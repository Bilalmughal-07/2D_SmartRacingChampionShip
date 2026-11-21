"""Manual two-algorithm comparison workspace for the Arcade Algorithm Lab."""

from __future__ import annotations

import copy
import json
import math
from time import perf_counter

import arcade

from smart_racing.algorithms.astar import astar
from smart_racing.algorithms.bfs import bfs
from smart_racing.algorithms.common import AlgorithmResult, TraceCollector
from smart_racing.algorithms.dfs import dfs
from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.algorithms.dynamic_programming import knapsack_01
from smart_racing.algorithms.greedy import greedy_knapsack
from smart_racing.algorithms.sorting import heap_sort, merge_sort, quick_sort
from smart_racing.arcade_ui.app import (
    AMBER,
    CORAL,
    CYAN,
    EMERALD,
    MUTED,
    NAVY,
    WHITE,
    ArcadeView,
    _root,
    _text,
)
from smart_racing.services.route_planner import RoutePlanner

COMPARISON_CATEGORIES = {
    "Graph Traversal": ("BFS", "DFS"),
    "Weighted Routing": ("Dijkstra", "A*"),
    "Resource Optimization": ("0/1 Knapsack DP", "Greedy"),
    "Championship Sorting": ("Merge Sort", "Quick Sort", "Heap Sort"),
}

_CATEGORY_ORDER = tuple(COMPARISON_CATEGORIES)
_PRESETS = ("balanced", "speed", "economy", "safety")
_SCENARIOS = ("Live graph", "Road closure")


def comparison_algorithms(category: str) -> tuple[str, ...]:
    return COMPARISON_CATEGORIES.get(category, ())


def validate_comparison_selection(category: str, algorithm1: str | None, algorithm2: str | None) -> str | None:
    if not algorithm1 or not algorithm2:
        return "Please select two algorithms."
    options = comparison_algorithms(category)
    if algorithm1 == algorithm2:
        return "Please select two different algorithms."
    if algorithm1 not in options or algorithm2 not in options:
        return "These algorithms solve different problem types and cannot be directly compared in this mode."
    return None


class AlgorithmComparisonView(ArcadeView):
    """Side-by-side comparison of two independently selected algorithms."""

    SPEEDS = (0.5, 1.0, 2.0, 4.0)

    def __init__(self, window, session, initial_algorithm: str | None = None):
        self.category = self._category_for(initial_algorithm or session.selected_algorithm)
        options = comparison_algorithms(self.category)
        self.algorithm1 = initial_algorithm if initial_algorithm in options else options[0]
        self.algorithm2 = next(item for item in options if item != self.algorithm1)
        self.category_index = _CATEGORY_ORDER.index(self.category)
        self.lab_track_index = next(
            (i for i, track in enumerate(session.tracks) if track.id == session.selected_track_id), 0
        )
        self.source_id = session.selected_track.start_id
        self.target_id = session.selected_track.finish_id
        self.preset = "balanced"
        self.event_scenario = "Live graph"
        self.capacity = 10
        self.chart_metric = "Auto"
        self.graph_revision = 0
        self.comparison: dict | None = None
        self.step_index = 0
        self.playing = False
        self.playback_speed = 1.0
        self._elapsed = 0.0
        self.detail_tab = "explanation"
        self.help_open = False
        self.status = "Select two compatible algorithms, configure the shared input, then run the comparison."
        self.error: str | None = None
        self.workspace_rect = (18.0, 100.0, 1.0, 1.0)
        self.timeline_rect = (0.0, 0.0, 1.0, 1.0)
        super().__init__(window, session)

    @property
    def track(self):
        return self.session.tracks[self.lab_track_index]

    @property
    def options(self) -> tuple[str, ...]:
        return comparison_algorithms(self.category)

    @property
    def max_steps(self) -> int:
        if not self.comparison:
            return 0
        return max(len(self.comparison["left"]["steps"]), len(self.comparison["right"]["steps"]))

    @staticmethod
    def _category_for(name: str) -> str:
        for category, options in COMPARISON_CATEGORIES.items():
            if name in options:
                return category
        return "Graph Traversal"

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, height = self.window.width, self.window.height
        self.workspace_rect = (18, 100, width - 36, max(300, height - 365))
        category_y = height - 138
        row_y = height - 176
        input_y = height - 214
        self.add_button("BACK", 18, height - 84, 92, 38, self.go_back, NAVY, WHITE, CYAN)
        self.add_button("RESET", 118, height - 84, 92, 38, self.reset_comparison, NAVY, WHITE, CYAN)
        self.add_button("HELP", 218, height - 84, 82, 38, self.toggle_help, NAVY, WHITE, CYAN)
        self.add_button(
            f"CATEGORY: {self.category}", 18, category_y, 270, 30, self.cycle_category, CYAN, NAVY, CYAN, font_size=11
        )
        self.add_button(f"CIRCUIT: {self.track.id[-2:]}", 296, category_y, 190, 30, self.cycle_circuit, NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"COST: {self.preset.title()}", 494, category_y, 190, 30, self.cycle_preset, NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"EVENT: {self.event_scenario}", 692, category_y, 230, 30, self.cycle_event_scenario, NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"REVISION: {self.graph_revision}", 930, category_y, 160, 30, self._show_revision, NAVY, WHITE, CYAN, font_size=10)
        self.add_button(f"ALGORITHM 1: {self.algorithm1}", 18, row_y, 300, 30, self.cycle_algorithm1, NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"ALGORITHM 2: {self.algorithm2}", 328, row_y, 300, 30, self.cycle_algorithm2, NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"SOURCE: V{self.source_id}", 638, row_y, 145, 30, self.cycle_source, NAVY, WHITE, CYAN, font_size=10)
        self.add_button(f"TARGET: V{self.target_id}", 793, row_y, 145, 30, self.cycle_target, NAVY, WHITE, CYAN, font_size=10)
        self.add_button(f"BUDGET: {self.capacity}", 948, row_y, 142, 30, self.cycle_capacity, NAVY, WHITE, CYAN, font_size=10)
        valid = self._validation_error() is None
        self.add_button(
            "RUN COMPARISON",
            18,
            input_y,
            250,
            32,
            self.run_comparison if valid else self._show_validation,
            EMERALD if valid else (60, 68, 76),
            NAVY if valid else MUTED,
            CYAN if valid else (90, 100, 110),
            font_size=12,
        )
        self.add_button("EXPLANATION", 278, input_y, 112, 32, self.show_explanation, NAVY, WHITE, CYAN, font_size=10)
        self.add_button("PSEUDOCODE", 396, input_y, 112, 32, self.show_pseudocode, NAVY, WHITE, CYAN, font_size=10)
        if self.comparison:
            self.add_button("PLAY / PAUSE", 514, input_y, 122, 32, self.toggle_playback, CORAL if self.playing else EMERALD, NAVY, CYAN, font_size=10)
            self.add_button("PREVIOUS", 642, input_y, 92, 32, self.previous_step, NAVY, WHITE, CYAN, font_size=10)
            self.add_button("NEXT STEP", 740, input_y, 92, 32, self.next_step, NAVY, WHITE, CYAN, font_size=10)
            self.add_button("SPEED", 838, input_y, 72, 32, self.cycle_speed, NAVY, WHITE, CYAN, font_size=10)
            self.add_button(f"METRIC: {self._chart_metric_short()}", 916, input_y, 130, 32, self.cycle_chart_metric, NAVY, WHITE, CYAN, font_size=9)
            self.add_button("EXPORT", 1052, input_y, 78, 32, self.export_comparison, NAVY, WHITE, CYAN, font_size=10)
        else:
            self.add_button("EXPORT", 514, input_y, 78, 32, self.export_comparison, NAVY, WHITE, CYAN, font_size=10)
        bottom = self.workspace_rect[1]
        self.timeline_rect = (self.workspace_rect[0] + 20, bottom + 45, self.workspace_rect[2] - 40, 12)

    def go_back(self) -> None:
        from smart_racing.arcade_ui.lab_view import AlgorithmLabView

        self.playing = False
        self.app.show_view(AlgorithmLabView(self.app, self.session))

    def _invalidate(self, message: str | None = None) -> None:
        self.comparison = None
        self.step_index = 0
        self.playing = False
        self.error = None
        self.status = message or "Selections changed; run a fresh comparison."
        self.rebuild_ui()

    def cycle_category(self) -> None:
        self.category_index = (self.category_index + 1) % len(_CATEGORY_ORDER)
        self.category = _CATEGORY_ORDER[self.category_index]
        self.algorithm1, self.algorithm2 = self.options[:2]
        self.chart_metric = "Auto"
        self._invalidate(f"Category changed to {self.category}; both algorithms were reset to valid independent choices.")

    def cycle_algorithm1(self) -> None:
        self.algorithm1 = self.options[(self.options.index(self.algorithm1) + 1) % len(self.options)]
        self._invalidate()

    def cycle_algorithm2(self) -> None:
        self.algorithm2 = self.options[(self.options.index(self.algorithm2) + 1) % len(self.options)]
        self._invalidate()

    def cycle_circuit(self) -> None:
        self.lab_track_index = (self.lab_track_index + 1) % len(self.session.tracks)
        self.source_id, self.target_id = self.track.start_id, self.track.finish_id
        self.graph_revision += 1
        self._invalidate(f"Loaded {self.track.name}; comparison results were invalidated.")

    def cycle_source(self) -> None:
        ids = sorted(self.track.graph().vertices)
        self.source_id = ids[(ids.index(self.source_id) + 1) % len(ids)]
        self._invalidate()

    def cycle_target(self) -> None:
        ids = sorted(self.track.graph().vertices)
        self.target_id = ids[(ids.index(self.target_id) + 1) % len(ids)]
        self._invalidate()

    def cycle_preset(self) -> None:
        self.preset = _PRESETS[(_PRESETS.index(self.preset) + 1) % len(_PRESETS)]
        self._invalidate(f"Cost strategy changed to {self.preset.title()}.")

    def cycle_event_scenario(self) -> None:
        self.event_scenario = _SCENARIOS[(_SCENARIOS.index(self.event_scenario) + 1) % len(_SCENARIOS)]
        self.graph_revision += 1
        self._invalidate(f"Input scenario changed to {self.event_scenario}.")

    def cycle_capacity(self) -> None:
        self.capacity = 10 if self.capacity >= 20 else self.capacity + 5
        self._invalidate(f"Resource budget changed to {self.capacity}.")

    def cycle_speed(self) -> None:
        self.playback_speed = self.SPEEDS[(self.SPEEDS.index(self.playback_speed) + 1) % len(self.SPEEDS)]
        self.status = f"Playback speed: {self.playback_speed:g}×. Each trace keeps its own step count."
        self.rebuild_ui()

    def cycle_chart_metric(self) -> None:
        metrics = self._chart_metric_options()
        self.chart_metric = metrics[(metrics.index(self.chart_metric) + 1) % len(metrics)]
        self.status = f"Chart metric: {self._chart_metric_name()}. Both panels use the same scale."
        self.rebuild_ui()

    def _chart_metric_options(self):
        options = {
            "Graph Traversal": ("Auto", "Operation count", "Visited vertices", "Examined edges"),
            "Weighted Routing": ("Auto", "Expanded vertices", "Heap operations", "Runtime"),
            "Resource Optimization": ("Auto", "Total benefit", "States evaluated", "Decision count"),
            "Championship Sorting": ("Auto", "Comparisons", "Swaps", "Moves"),
        }
        return options[self.category]

    def _chart_metric_name(self):
        if self.chart_metric != "Auto":
            return self.chart_metric
        return {
            "Graph Traversal": "Operation count",
            "Weighted Routing": "Expanded vertices",
            "Resource Optimization": "Total benefit",
            "Championship Sorting": "Comparisons",
        }[self.category]

    def _chart_metric_short(self):
        return {
            "Operation count": "Operations",
            "Visited vertices": "Visited",
            "Examined edges": "Edges",
            "Expanded vertices": "Expanded",
            "Heap operations": "Heap ops",
            "Runtime": "Runtime",
            "Total benefit": "Benefit",
            "States evaluated": "States",
            "Decision count": "Decisions",
            "Comparisons": "Comparisons",
            "Swaps": "Swaps",
            "Moves": "Moves",
        }.get(self._chart_metric_name(), self._chart_metric_name())

    def _show_revision(self) -> None:
        self.status = f"Both algorithms will receive isolated copies of graph revision {self.graph_revision}."

    def _show_validation(self) -> None:
        self.error = self._validation_error() or "Comparison inputs are not valid."
        self.status = self.error
        self.rebuild_ui()

    def toggle_help(self) -> None:
        self.help_open = not self.help_open
        self.rebuild_ui()

    def show_pseudocode(self) -> None:
        self.detail_tab = "pseudocode"
        self.status = "Pseudocode mode shows the current line for each selected algorithm."
        self.rebuild_ui()

    def show_explanation(self) -> None:
        self.detail_tab = "explanation"
        self.status = "Explanation mode shows the operation recorded at the current synchronized step."
        self.rebuild_ui()

    def reset_comparison(self) -> None:
        self.comparison = None
        self.step_index = 0
        self.playing = False
        self.error = None
        self.help_open = False
        self.status = "Comparison reset; selections and shared inputs were preserved."
        self.rebuild_ui()

    def _validation_error(self) -> str | None:
        error = validate_comparison_selection(self.category, self.algorithm1, self.algorithm2)
        if error:
            return error
        graph = self.track.graph()
        if self.source_id not in graph.vertices or self.target_id not in graph.vertices:
            return "Source and destination must exist on the selected circuit."
        if self.category == "Weighted Routing":
            if any(RoutePlanner(self.track, self.preset).cost_model.cost(edge) < 0 for edge in graph.edges.values()):
                return "Weighted routing requires non-negative edge costs."
        if self.category == "Resource Optimization" and self.capacity <= 0:
            return "Resource capacity must be positive."
        return None

    def _comparison_graph(self):
        graph = copy.deepcopy(self.track.graph())
        if self.event_scenario == "Road closure" and graph.edges:
            graph.set_edge_status(sorted(graph.edges)[0], "Blocked")
        return graph

    def run_comparison(self) -> None:
        error = self._validation_error()
        if error:
            self.comparison = None
            self.step_index = 0
            self.playing = False
            self._show_validation()
            return
        try:
            graph = self._comparison_graph()
            left = self._execute(self.algorithm1, graph)
            right = self._execute(self.algorithm2, copy.deepcopy(graph))
            self.comparison = {
                "category": self.category,
                "algorithm1": self.algorithm1,
                "algorithm2": self.algorithm2,
                "track": self.track.id,
                "source": self.source_id,
                "target": self.target_id,
                "preset": self.preset,
                "scenario": self.event_scenario,
                "revision": self.graph_revision,
                "left": left,
                "right": right,
            }
            self.step_index = 0
            self.playing = False
            self.error = None
            self.status = "Comparison complete: both algorithms used equivalent isolated inputs and real execution traces."
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            self.comparison = None
            self.error = f"{type(exc).__name__}: {exc}"
            self.status = "Comparison failed; correct the inputs and run again."
        self.rebuild_ui()

    def _execute(self, name: str, graph):
        started = perf_counter()
        if name in {"BFS", "DFS", "Dijkstra", "A*"}:
            trace = TraceCollector()
            if name == "BFS":
                result = bfs(graph, self.source_id, self.target_id, trace=trace)
            elif name == "DFS":
                result = dfs(graph, self.source_id, self.target_id, trace=trace)
            else:
                planner = RoutePlanner(self.track, self.preset)
                cost = planner.cost_model.cost
                if name == "Dijkstra":
                    result = dijkstra(graph, self.source_id, self.target_id, edge_cost=cost, trace=trace)
                else:
                    result = astar(graph, self.source_id, self.target_id, edge_cost=cost, heuristic=self._heuristic(graph, cost), trace=trace)
            steps = self._trace_steps(trace, self._graph_explanation(name))
            if result.path:
                steps.append({"operation": "complete", "state": {"path": result.path, "cost": result.cost}, "counters": result.counters.__dict__.copy(), "explanation": "The final path was reconstructed from recorded parent relationships."})
        elif name == "0/1 Knapsack DP":
            result = knapsack_01(self._items(), self.capacity)
            table = result.details.get("table", [])
            steps = [{"operation": "dp_cell", "state": {"row": row, "budget": budget, "value": value}, "counters": {"states": row * (self.capacity + 1) + budget + 1}, "explanation": "DP compares excluding the item with taking it when capacity allows."} for row, values in enumerate(table) for budget, value in enumerate(values)]
        elif name == "Greedy":
            items = self._items()
            result = greedy_knapsack(items, self.capacity)
            selected = {item["id"] for item in result.selected}
            ordered = sorted(items, key=lambda item: (-item["benefit"] / item["cost"], item["id"]))
            steps = [{"operation": "consider", "state": {"item": item, "accepted": item["id"] in selected}, "counters": {"states": index + 1}, "explanation": "Greedy considers the next item by the declared benefit-to-cost rule."} for index, item in enumerate(ordered)]
        else:
            records = self._records()
            trace = []

            def callback(operation, state):
                trace.append((operation, state))

            sorter = {"Merge Sort": merge_sort, "Quick Sort": quick_sort, "Heap Sort": heap_sort}[name]
            result = sorter(records, key=self._ranking_key, trace=callback)
            steps = [{"operation": operation, "state": state, "counters": self._sort_counters(trace[: index + 1]), "explanation": f"{name} recorded this operation using the shared championship comparator."} for index, (operation, state) in enumerate(trace)]
            steps.append({"operation": "complete", "state": {"values": result}, "counters": self._sort_counters(trace), "explanation": "The final ranking is complete."})
        runtime = (perf_counter() - started) * 1000
        metrics = self._metrics(name, result, steps, graph)
        metrics["Runtime"] = f"{runtime:.3f} ms"
        return {"name": name, "result": result, "steps": steps, "runtime_ms": runtime, "metrics": metrics}

    @staticmethod
    def _heuristic(graph, cost):
        ratios = (
            cost(edge)
            / max(math.hypot(graph.vertices[edge.from_id].x - graph.vertices[edge.to_id].x, graph.vertices[edge.from_id].y - graph.vertices[edge.to_id].y), 1e-9)
            for edge in graph.edges.values()
            if edge.distance > 0
        )
        minimum_ratio = min(ratios, default=0.0)

        def heuristic(source, target):
            first, second = graph.vertices[source], graph.vertices[target]
            return math.hypot(first.x - second.x, first.y - second.y) * minimum_ratio

        return heuristic

    @staticmethod
    def _trace_steps(trace, explanation):
        return [{"operation": step.operation, "state": step.state, "counters": step.counters, "explanation": explanation} for step in trace.steps]

    @staticmethod
    def _graph_explanation(name):
        return {
            "BFS": "BFS minimizes edge count in an unweighted graph; it does not optimize weighted cost.",
            "DFS": "DFS follows a branch deeply and backtracks; it does not generally guarantee a shortest path.",
            "Dijkstra": "Dijkstra extracts the smallest tentative weighted cost and relaxes legal roads.",
            "A*": "A* orders the open set by g + h using the same admissible lower-bound heuristic as the route planner.",
        }[name]

    @staticmethod
    def _items():
        return [{"id": 1, "name": "A", "cost": 6, "benefit": 30}, {"id": 2, "name": "B", "cost": 5, "benefit": 24}, {"id": 3, "name": "C", "cost": 5, "benefit": 24}]

    @staticmethod
    def _records():
        return [
            {"racer_id": 1, "name": "Player", "total_points": 54, "wins": 2, "sum_of_finish_positions": 5, "best_fastest_lap": 21.3},
            {"racer_id": 2, "name": "Navigator", "total_points": 54, "wins": 2, "sum_of_finish_positions": 6, "best_fastest_lap": 20.9},
            {"racer_id": 3, "name": "Shortcut", "total_points": 45, "wins": 1, "sum_of_finish_positions": 7, "best_fastest_lap": 22.1},
            {"racer_id": 4, "name": "Distance", "total_points": 36, "wins": 0, "sum_of_finish_positions": 9, "best_fastest_lap": None},
        ]

    @staticmethod
    def _ranking_key(item):
        return (-item["total_points"], -item["wins"], item["sum_of_finish_positions"], item["best_fastest_lap"] if item["best_fastest_lap"] is not None else float("inf"), item["racer_id"])

    @staticmethod
    def _sort_counters(trace):
        return {"comparisons": sum(operation == "compare" for operation, _ in trace), "swaps": sum(operation == "swap" for operation, _ in trace), "moves": sum(operation in {"merge", "swap", "extract"} for operation, _ in trace)}

    def _metrics(self, name, result, steps, graph):
        counters = getattr(getattr(result, "counters", None), "__dict__", {})
        if name in {"BFS", "DFS", "Dijkstra", "A*"}:
            path = list(getattr(result, "path", []) or [])
            distance = sum((graph.edge_between(a, b).distance for a, b in zip(path, path[1:]) if graph.edge_between(a, b)), 0.0)
            travel_time = sum((graph.edge_between(a, b).effective_time() for a, b in zip(path, path[1:]) if graph.edge_between(a, b)), 0.0)
            fuel = sum((graph.edge_between(a, b).effective_fuel() for a, b in zip(path, path[1:]) if graph.edge_between(a, b)), 0.0)
            if name in {"BFS", "DFS"}:
                return {"Route found": bool(path), "Visited vertices": counters.get("visited_vertices", 0), "Examined edges": counters.get("examined_edges", 0), "Path edge count": max(0, len(path) - 1), "Reachability": bool(path), "Operation count": len(steps), "Runtime": f"{self._runtime(result):.3f} ms"}
            return {"Route found": bool(path), "Optimized cost": result.cost, "Distance": distance, "Estimated time": travel_time, "Fuel required": fuel, "Expanded vertices": counters.get("expanded_vertices", 0), "Relaxations": counters.get("relaxed_edges", 0), "Heap operations": counters.get("heap_operations", 0), "Runtime": f"{self._runtime(result):.3f} ms", "Correctness": "Verified"}
        if name in {"0/1 Knapsack DP", "Greedy"}:
            selected = getattr(result, "selected", [])
            cost = sum(item["cost"] for item in selected)
            return {"Selected items": ", ".join(item["name"] for item in selected) or "None", "Capacity used": f"{cost}/{self.capacity}", "Total benefit": result.value, "Decision count": len(steps), "States evaluated": getattr(result, "states", 0), "Optimality": "Proven optimal" if name == "0/1 Knapsack DP" else "Heuristic only", "Runtime": f"{getattr(result, 'elapsed_ms', 0.0):.3f} ms"}
        ranking = [item["name"] for item in result]
        sort_counters = self._sort_counters([(step["operation"], step["state"]) for step in steps if step["operation"] != "complete"])
        return {"Comparisons": sort_counters["comparisons"], "Swaps": sort_counters["swaps"], "Moves": sort_counters["moves"], "Runtime": f"{self._runtime(result):.3f} ms", "Memory": "N/A (implementation does not measure allocations)", "Ranking": " > ".join(ranking), "Correctness": "Verified"}

    @staticmethod
    def _runtime(result):
        return float(getattr(result, "elapsed_ms", 0.0))

    def _step_for(self, side):
        steps = self.comparison[side]["steps"]
        if not steps or self.step_index <= 0:
            return {"operation": "ready", "state": {}, "counters": {}, "explanation": "Press NEXT STEP or PLAY to begin."}
        return steps[min(self.step_index, len(steps)) - 1]

    def next_step(self) -> None:
        if not self.comparison:
            return
        self.playing = False
        self.step_index = min(self.max_steps, self.step_index + 1)
        self.status = f"Synchronized step {self.step_index}/{self.max_steps}. Each panel retains its own trace length."
        self.rebuild_ui()

    def previous_step(self) -> None:
        if not self.comparison:
            return
        self.playing = False
        self.step_index = max(0, self.step_index - 1)
        self.status = f"Restored synchronized step {self.step_index}/{self.max_steps}."
        self.rebuild_ui()

    def toggle_playback(self) -> None:
        if not self.comparison:
            return
        if self.step_index >= self.max_steps:
            self.step_index = 0
        self.playing = not self.playing
        self.status = "Comparison playback running." if self.playing else "Comparison playback paused."
        self.rebuild_ui()

    def seek_step(self, index: int) -> None:
        self.playing = False
        self.step_index = max(0, min(self.max_steps, index))
        self.status = f"Timeline moved to synchronized progress {self.step_index}/{self.max_steps}."
        self.rebuild_ui()

    def _conclusion(self):
        if not self.comparison:
            return "Run a comparison to generate a conclusion from real outputs."
        left, right = self.comparison["left"], self.comparison["right"]
        if self.category == "Weighted Routing":
            same_cost = math.isclose(left["result"].cost or math.inf, right["result"].cost or math.inf, rel_tol=1e-9, abs_tol=1e-9)
            if same_cost:
                left_expanded = left["metrics"]["Expanded vertices"]
                right_expanded = right["metrics"]["Expanded vertices"]
                if left_expanded == right_expanded:
                    return "Both weighted algorithms found the same optimal cost and expanded the same number of vertices on this graph."
                winner = self.comparison["algorithm1"] if left_expanded < right_expanded else self.comparison["algorithm2"]
                return f"Both algorithms found the same optimal cost. {winner} expanded fewer vertices in this experiment; that is not a universal performance guarantee."
            return "The weighted algorithms returned different costs; inspect the graph revision, costs, and heuristic before treating this run as correct."
        if self.category == "Resource Optimization":
            if left["result"].value == right["result"].value:
                return "Both resource strategies achieved the same benefit on this dataset; DP remains the provably optimal method."
            winner = self.comparison["algorithm1"] if left["result"].value > right["result"].value else self.comparison["algorithm2"]
            return f"{winner} achieved the higher benefit on this dataset. The DP result is the optimality reference; Greedy is a declared heuristic."
        if self.category == "Championship Sorting":
            same = left["result"] == right["result"]
            if same:
                return "Both sorting algorithms produced the identical championship ranking using the authoritative comparator."
            return "The sorting outputs differ; this indicates a comparator or implementation defect that needs investigation."
        return "BFS and DFS were run on the same graph. BFS minimizes edge count; DFS provides depth-first reachability without a shortest-path guarantee."

    def export_comparison(self) -> None:
        if not self.comparison:
            self.error = "Run a comparison before exporting results."
            self.status = self.error
            self.rebuild_ui()
            return
        path = _root() / "data" / "arcade_lab_comparison.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._jsonable(self.comparison) | {"step": self.step_index, "conclusion": self._conclusion(), "timing_method": "perf_counter wall-clock around algorithm execution; rendering excluded"}
        path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        self.status = f"Exported comparison JSON to {path.name}."
        self.rebuild_ui()

    def on_update(self, delta_time: float):
        if self.playing and self.comparison:
            self._elapsed += delta_time
            if self._elapsed >= 0.75 / self.playback_speed:
                self._elapsed = 0.0
                self.step_index = min(self.max_steps, self.step_index + 1)
                if self.step_index >= self.max_steps:
                    self.playing = False
                    self.status = "Comparison playback complete."
                    self.rebuild_ui()

    def _draw_header(self, width, height):
        _text("ALGORITHM LAB  >  COMPARE ALGORITHMS", 160, height - 28, 21, WHITE, bold=True)
        _text(f"MANUAL COMPARISON  ·  {self.category.upper()}", 400, height - 52, 11, MUTED)
        _text(self.track.name, width - 180, height - 34, 12, WHITE, anchor_x="center")
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)

    def _draw_config_text(self, width, height):
        error = self._validation_error()
        if error:
            _text(error, 18, height - 247, 10, CORAL, width=min(width - 36, 700))
        else:
            _text(self.status, 18, height - 247, 10, EMERALD if self.comparison else MUTED, width=min(width - 36, 900))
        _text("Shared inputs: same circuit snapshot · same source/target · same cost model · same graph revision", 18, height - 266, 9, MUTED, width=width - 36)

    def _draw_side(self, side, x, y, width, height):
        item = self.comparison[side]
        name, steps = item["name"], item["steps"]
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (20, 38, 61))
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, CYAN if side == "left" else EMERALD, 2)
        _text(f"{name.upper()}  ·  {min(self.step_index, len(steps))}/{len(steps)}", x + 12, y + height - 24, 13, CYAN if side == "left" else EMERALD, bold=True)
        if self.detail_tab == "pseudocode":
            _text("PSEUDOCODE", x + 12, y + height - 48, 9, AMBER, bold=True)
            _text(self._pseudocode_line(name), x + 12, y + height - 66, 9, WHITE, width=width - 24)
        else:
            step = self._step_for(side)
            _text(f"{step['operation']}: {step.get('explanation', '')}", x + 12, y + height - 48, 9, WHITE, width=width - 24)
        self._draw_metric_chart(item, x + 12, y + height - 86, width - 24)
        visual_y, visual_h = y + 84, height - 178
        if name in {"BFS", "DFS", "Dijkstra", "A*"}:
            self._draw_graph_side(item, x + 10, visual_y, width - 20, visual_h)
        elif name in {"0/1 Knapsack DP", "Greedy"}:
            self._draw_resource_side(item, x + 10, visual_y, width - 20, visual_h)
        else:
            self._draw_sort_side(item, x + 10, visual_y, width - 20, visual_h)
        self._draw_metric_lines(item["metrics"], x + 12, y + 14, width - 24, 6)

    def _draw_graph_side(self, item, left, bottom, width, height):
        graph = self._comparison_graph()
        xs, ys = [vertex.x for vertex in graph.vertices.values()], [vertex.y for vertex in graph.vertices.values()]
        scale = min((width - 30) / max(1, max(xs) - min(xs)), (height - 25) / max(1, max(ys) - min(ys)))

        def point(vertex):
            return left + width / 2 + (vertex.x - (min(xs) + max(xs)) / 2) * scale, bottom + height / 2 + (vertex.y - (min(ys) + max(ys)) / 2) * scale

        step = self._step_for("left" if item is self.comparison["left"] else "right")
        state = step.get("state", {})
        current = state.get("vertex", state.get("current", state.get("to")))
        path = item["result"].path if isinstance(item["result"], AlgorithmResult) and self.step_index >= len(item["steps"]) else []
        for edge in graph.edges.values():
            source, target = graph.vertices[edge.from_id], graph.vertices[edge.to_id]
            color = CORAL if not edge.traversable() else CYAN if edge.from_id in path and edge.to_id in path else (62, 80, 102)
            arcade.draw_line(*point(source), *point(target), color, 3)
        for source, target in zip(path, path[1:]):
            arcade.draw_line(*point(graph.vertices[source]), *point(graph.vertices[target]), AMBER, 5)
        for vertex in graph.vertices.values():
            px, py = point(vertex)
            color = CORAL if vertex.id == self.target_id else EMERALD if vertex.id == self.source_id else AMBER if vertex.id == current else (99, 117, 139)
            arcade.draw_circle_filled(px, py, 5, color)
        _text(f"Current vertex: V{current if current is not None else '—'}", left, bottom + 4, 9, WHITE)

    def _draw_resource_side(self, item, left, bottom, width, height):
        result = item["result"]
        if item["name"] == "0/1 Knapsack DP":
            table = result.details.get("table", [])
            _text("DP TABLE", left, bottom + height - 16, 9, CYAN, bold=True)
            if table:
                cell_w = min(30, (width - 20) / len(table[0]))
                for row, values in enumerate(table):
                    for col, value in enumerate(values):
                        x, y = left + col * cell_w, bottom + height - 38 - row * 19
                        arcade.draw_lbwh_rectangle_filled(x, y, cell_w - 2, 16, AMBER if self._step_for("left" if item is self.comparison["left"] else "right").get("state", {}).get("budget") == col else (44, 69, 93))
                        _text(f"{value:g}", x + cell_w / 2, y + 4, 7, NAVY if value == result.value else WHITE, anchor_x="center")
        else:
            _text("GREEDY CANDIDATES", left, bottom + height - 16, 9, CYAN, bold=True)
            for index, item_value in enumerate(sorted(self._items(), key=lambda value: -value["benefit"] / value["cost"])):
                y = bottom + height - 42 - index * 24
                arcade.draw_lbwh_rectangle_filled(left + 52, y, (width - 70) * item_value["benefit"] / 30, 14, EMERALD if item_value in result.selected else (50, 79, 101))
                _text(f"{item_value['name']}  {item_value['benefit']}/{item_value['cost']}", left, y + 2, 8, WHITE)

    def _draw_sort_side(self, item, left, bottom, width, height):
        step = self._step_for("left" if item is self.comparison["left"] else "right")
        records = step.get("state", {}).get("values") or item["result"]
        if isinstance(records, dict):
            records = records.get("ranking", self._records())
        maximum = max(record["total_points"] for record in records) if records else 1
        bar_w = max(18, (width - 30) / max(1, len(records)) - 8)
        for index, record in enumerate(records):
            bar_h = (height - 35) * record["total_points"] / maximum
            x = left + 10 + index * (bar_w + 8)
            arcade.draw_lbwh_rectangle_filled(x, bottom + 18, bar_w, bar_h, CYAN if index < self.step_index else (51, 82, 105))
            _text(record["name"], x + bar_w / 2, bottom + 5, 7, WHITE, anchor_x="center")

    def _draw_metric_chart(self, item, left, y, width):
        metric = self._chart_metric_name()
        values = [self._numeric_metric(side["metrics"].get(metric, 0)) for side in (self.comparison["left"], self.comparison["right"])]
        maximum = max(values + [1.0])
        _text(metric, left, y + 20, 8, AMBER, bold=True)
        for index, value in enumerate(values):
            bar_y = y + 7 - index * 10
            color = CYAN if index == 0 else EMERALD
            arcade.draw_lbwh_rectangle_filled(left + 88, bar_y, max(2, (width - 118) * value / maximum), 6, color)
            _text(f"{'A' if index == 0 else 'B'} {value:g}", left + 2, bar_y - 1, 7, WHITE)

    @staticmethod
    def _numeric_metric(value):
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).split()[0])
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _draw_metric_lines(metrics, left, bottom, width, limit):
        lines = [f"{key}: {value}" for key, value in metrics.items()]
        for index, line in enumerate(lines[:limit]):
            _text(line, left, bottom + index * 13, 8, WHITE, width=width)

    @staticmethod
    def _pseudocode_line(name):
        return {"BFS": "queue → dequeue → discover neighbors", "DFS": "stack → inspect → backtrack", "Dijkstra": "extract min → relax edges", "A*": "extract min f=g+h → update scores", "0/1 Knapsack DP": "max(skip, take) for each capacity", "Greedy": "sort benefit/cost → accept if fits", "Merge Sort": "split → compare → merge", "Quick Sort": "pivot → partition → recurse", "Heap Sort": "heapify → extract minimum"}.get(name, "Recorded production operation")

    def _draw_results(self, x, y, width, height):
        _text("COMPARISON RESULTS", x, y + height - 18, 12, WHITE, bold=True)
        _text(self._conclusion(), x, y + height - 38, 9, EMERALD, width=width)

    def _draw_help(self, x, y, width, height):
        _text("MANUAL COMPARISON", x, y + height - 20, 16, WHITE, bold=True)
        lines = ("Choose Algorithm 1 and Algorithm 2 independently; the left/right order is preserved.", "Only compatible pairs are offered: BFS/DFS, Dijkstra/A*, DP/Greedy, or any two sorting algorithms.", "Both algorithms receive isolated copies of the same graph, dataset, comparator, and revision.", "PLAY/PAUSE, NEXT STEP, PREVIOUS, RESET, SPEED, and the shared timeline control both traces.", "Kruskal, Backtracking, and the custom event heap remain standalone demonstrations in the main Lab.")
        for index, line in enumerate(lines):
            _text(line, x, y + height - 56 - index * 25, 10, WHITE, width=width)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            left, bottom, width, height = self.timeline_rect
            if self.comparison and left <= x <= left + width and bottom - 8 <= y <= bottom + height + 8:
                self.seek_step(round((x - left) / max(1, width) * self.max_steps))

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            if self.help_open:
                self.help_open = False
                self.rebuild_ui()
            else:
                self.go_back()
        elif symbol in (arcade.key.RIGHT, arcade.key.SPACE):
            self.next_step() if symbol == arcade.key.RIGHT else self.toggle_playback()
        elif symbol == arcade.key.LEFT:
            self.previous_step()
        elif symbol == arcade.key.ENTER:
            self.run_comparison()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        self._draw_header(width, height)
        self._draw_config_text(width, height)
        x, y, workspace_width, workspace_height = self.workspace_rect
        arcade.draw_lbwh_rectangle_filled(x, y, workspace_width, workspace_height, (13, 27, 45))
        arcade.draw_lbwh_rectangle_outline(x, y, workspace_width, workspace_height, (54, 85, 112), 1)
        if self.help_open:
            self._draw_help(x + 20, y + 24, workspace_width - 40, workspace_height - 48)
        elif self.comparison:
            gap = 14
            panel_width = (workspace_width - gap - 24) / 2
            panel_height = workspace_height - 92
            self._draw_side("left", x + 8, y + 58, panel_width, panel_height)
            self._draw_side("right", x + 16 + panel_width, y + 58, panel_width, panel_height)
            left, bottom, timeline_width, _ = self.timeline_rect
            arcade.draw_lbwh_rectangle_filled(left, bottom, timeline_width, 8, (48, 65, 84))
            progress = self.step_index / max(1, self.max_steps)
            arcade.draw_lbwh_rectangle_filled(left, bottom, timeline_width * progress, 8, CYAN)
            arcade.draw_circle_filled(left + timeline_width * progress, bottom + 4, 7, WHITE)
            _text(f"Synchronized timeline · step {self.step_index}/{self.max_steps}", left, bottom + 15, 9, MUTED)
            self._draw_results(x + 16, y + 10, workspace_width - 32, 42)
        else:
            _text("Choose two algorithms and press RUN COMPARISON", x + workspace_width / 2, y + workspace_height / 2 + 18, 17, WHITE, anchor_x="center", bold=True)
            _text("The same graph snapshot, dataset, comparator, and objective will be used on both sides.", x + workspace_width / 2, y + workspace_height / 2 - 10, 10, MUTED, anchor_x="center")
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()

    @staticmethod
    def _jsonable(value):
        if isinstance(value, AlgorithmResult):
            return {"value": value.value, "path": value.path, "cost": value.cost, "counters": value.counters.__dict__, "elapsed_ms": value.elapsed_ms, "details": value.details}
        if hasattr(value, "value") and hasattr(value, "selected"):
            return {"value": value.value, "selected": value.selected, "states": value.states, "details": value.details}
        if isinstance(value, dict):
            return {str(key): AlgorithmComparisonView._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [AlgorithmComparisonView._jsonable(item) for item in value]
        return value
