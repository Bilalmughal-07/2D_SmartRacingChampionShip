"""Interactive Algorithm Lab backed by the production algorithm library."""

from __future__ import annotations

import json
import math
from time import perf_counter

import arcade

from smart_racing.algorithms.astar import astar
from smart_racing.algorithms.backtracking import place_services_backtracking
from smart_racing.algorithms.bfs import bfs
from smart_racing.algorithms.common import AlgorithmResult, TraceCollector
from smart_racing.algorithms.dfs import dfs
from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.algorithms.dynamic_programming import knapsack_01
from smart_racing.algorithms.greedy import greedy_knapsack
from smart_racing.algorithms.mst import kruskal_mst
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
from smart_racing.model.events import Event, EventType
from smart_racing.services.event_scheduler import EventScheduler
from smart_racing.services.route_planner import RoutePlanner

CATEGORY_ORDER = ("Graph & Routing", "Optimization", "Track Design", "Events & Heaps", "Sorting")

CATALOG = (
    ("BFS", "Breadth-first reachability and minimum edge-count path", "O(V + E)", "Explorer reachability", "Graph & Routing"),
    ("DFS", "Depth-first traversal, cycles, components and dead ends", "O(V + E)", "Explorer topology", "Graph & Routing"),
    ("Dijkstra", "Exact weighted routing with non-negative costs", "O((V + E) log V)", "Race route planner", "Graph & Routing"),
    ("A*", "Heuristic-guided exact weighted routing", "O((V + E) log V) worst case", "Race route planner", "Graph & Routing"),
    ("0/1 Knapsack DP", "Optimal finite pickup selection under a budget", "O(mB)", "Nitro recommendation", "Optimization"),
    ("Refuelling DP", "Minimum stop-time fuel feasibility planning", "O(mC²)", "Fuel planner", "Optimization"),
    ("Greedy", "Benefit-to-cost pickup heuristic", "O(m log m)", "Nitro comparison", "Optimization"),
    ("Backtracking", "Constraint-based service placement", "Exponential worst case", "Track generation", "Track Design"),
    ("Kruskal MST", "Connected undirected road backbone", "O(E log E)", "Track generation", "Track Design"),
    ("Event Min-Heap", "Deterministic event priority ordering", "O(log n) push/pop", "Race event scheduler", "Events & Heaps"),
    ("Merge Sort", "Stable championship ranking", "O(n log n)", "Dashboard ranking", "Sorting"),
    ("Quick Sort", "Pivot-based ranking alternative", "O(n log n) average", "Dashboard comparison", "Sorting"),
    ("Heap Sort", "In-place priority-based ranking", "O(n log n)", "Dashboard comparison", "Sorting"),
)

PSEUDOCODE = {
    "BFS": ["queue ← [source]", "mark source visited", "while queue not empty:", "  v ← dequeue", "  discover each unvisited neighbor"],
    "DFS": ["push source", "while stack not empty:", "  inspect next edge", "  push unvisited neighbor", "  backtrack when exhausted"],
    "Dijkstra": ["distance[source] ← 0", "push (0, source)", "while queue not empty:", "  extract smallest tentative distance", "  relax every legal edge"],
    "A*": ["g[source] ← 0", "f(v) ← g(v) + h(v)", "while open set not empty:", "  extract smallest f score", "  update scores and parents"],
    "0/1 Knapsack DP": ["dp[0][budget] ← 0", "for each item and capacity:", "  choose max(skip, take)", "store the state decision", "trace selected items backward"],
    "Refuelling DP": ["initialize starting fuel state", "for each route leg:", "  try every legal purchase", "  reject states below demand", "keep minimum stop time"],
    "Greedy": ["sort by benefit / cost", "take zero-cost positive items", "accept the next item when it fits", "update remaining capacity", "report heuristic status"],
    "Backtracking": ["choose a candidate", "reject constraint violations", "place candidate", "recurse", "undo on failure"],
    "Kruskal MST": ["sort undirected edges", "find component roots", "union if no cycle", "record accepted edge", "stop after V − 1 edges"],
    "Event Min-Heap": ["insert by (time, priority, sequence)", "sift up after insert", "peek minimum", "extract due events", "sift down after removal"],
    "Merge Sort": ["split into halves", "sort both halves", "compare front records", "append smaller record", "merge sorted halves"],
    "Quick Sort": ["choose pivot", "partition around pivot", "recurse left", "recurse right", "return in-place order"],
    "Heap Sort": ["heapify records", "extract minimum", "append sorted prefix", "repeat until empty", "return ranking"],
}


class AlgorithmLabView(ArcadeView):
    """Responsive step-through visualizer for all required algorithm families."""

    SPEEDS = (0.5, 1.0, 2.0, 4.0)

    def __init__(self, window, session):
        selected_name = session.selected_algorithm
        self.selected = next((i for i, item in enumerate(CATALOG) if item[0] == selected_name), 0)
        self.category = CATALOG[self.selected][4]
        self.lab_track_index = next((i for i, track in enumerate(session.tracks) if track.id == session.selected_track_id), 0)
        self.source_id = session.selected_track.start_id
        self.target_id = session.selected_track.finish_id
        self.preset = "balanced"
        self.steps: list[dict] = []
        self.step_index = 0
        self.result = None
        self.status = "Choose an algorithm, then run or step through the real implementation."
        self.error: str | None = None
        self.dataset = "current circuit"
        self.playing = False
        self.playback_speed = 1.0
        self._playback_elapsed = 0.0
        self.detail_tab = "explanation"
        self.comparison: dict | None = None
        self.experiment: dict | None = None
        self.help_open = False
        self.timeline_rect = (0.0, 0.0, 1.0, 1.0)
        self.center_rect = (0.0, 0.0, 1.0, 1.0)
        self.right_rect = (0.0, 0.0, 1.0, 1.0)
        super().__init__(window, session)
        self.execute(reset=True)

    @property
    def algorithm_name(self) -> str:
        return CATALOG[self.selected][0]

    @property
    def track(self):
        return self.session.tracks[self.lab_track_index]

    @property
    def category_algorithms(self):
        return [(i, item) for i, item in enumerate(CATALOG) if item[4] == self.category]

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, height = self.window.width, self.window.height
        self.center_rect = (250, 108, max(390, width - 602), max(390, height - 236))
        self.right_rect = (width - 338, 108, 322, max(390, height - 236))
        left, bottom, center_width, center_height = self.center_rect
        nav_y = height - 84
        self.add_button("BACK", 18, nav_y, 92, 38, self.go_back, NAVY, WHITE, CYAN)
        self.add_button(f"CIRCUIT: {self.track.id[-2:]}", width - 170, nav_y, 150, 38, self.cycle_circuit, NAVY, WHITE, CYAN)
        category_y = height - 108
        category_width = max(100, (width - 36) / len(CATEGORY_ORDER))
        for i, category in enumerate(CATEGORY_ORDER):
            active = category == self.category
            self.add_button(category, 18 + i * category_width, category_y, category_width - 6, 32, lambda category=category: self.select_category(category), CYAN if active else (24, 43, 65), NAVY if active else WHITE, CYAN, font_size=12)
        panel_top = bottom + center_height
        alg_y = panel_top - 108
        for offset, (index, item) in enumerate(self.category_algorithms):
            active = index == self.selected
            self.add_button(item[0], 28, alg_y - offset * 38, 202, 30, lambda index=index: self.select_algorithm(index), CYAN if active else (27, 48, 72), NAVY if active else WHITE, CYAN, font_size=12)
        self.add_button(f"SOURCE  V{self.source_id}", 28, bottom + 100, 202, 28, self.cycle_source, NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"TARGET  V{self.target_id}", 28, bottom + 66, 202, 28, self.cycle_target, NAVY, WHITE, CYAN, font_size=11)
        self.add_button("EXAMPLE INPUT", 28, bottom + 32, 202, 28, self.load_example, NAVY, WHITE, AMBER, font_size=11)
        playback_y = bottom + 17
        self.add_button("PREV", left + 16, playback_y, 64, 32, self.previous_step, NAVY, WHITE, CYAN, font_size=11)
        self.add_button("NEXT", left + 86, playback_y, 64, 32, self.next_step, NAVY, WHITE, CYAN, font_size=11)
        self.add_button("PAUSE" if self.playing else "RUN", left + 156, playback_y, 78, 32, self.toggle_playback, CORAL if self.playing else EMERALD, NAVY, CYAN, font_size=11)
        self.add_button("RESET", left + 240, playback_y, 70, 32, lambda: self.execute(reset=True), NAVY, WHITE, CYAN, font_size=11)
        self.add_button(f"{self.playback_speed:g}×", left + 316, playback_y, 58, 32, self.cycle_speed, NAVY, WHITE, CYAN, font_size=11)
        footer_x = left + 16
        cursor = footer_x
        for label, callback, button_width in (("PSEUDOCODE", self.show_pseudocode, 112), ("EXPLANATION", self.show_explanation, 112), ("COMPARE", self.compare, 90), ("EXPERIMENT", self.run_experiment, 106), ("EXPORT", self.export_result, 75), ("HELP", self.toggle_help, 62)):
            self.add_button(label, cursor, 20, button_width, 30, callback, NAVY, WHITE, CYAN, font_size=10)
            cursor += button_width + 6
        self.timeline_rect = (left + 18, bottom + 116, center_width - 36, 14)

    def go_back(self) -> None:
        from smart_racing.arcade_ui.app import MainMenuView, TrackExplorerView
        self.playing = False
        if self.session.explorer_return == "explorer":
            self.app.show_view(TrackExplorerView(self.app, self.session))
        elif self.session.explorer_return == "dashboard":
            from smart_racing.arcade_ui.dashboard_view import ChampionshipDashboardView
            self.app.show_view(ChampionshipDashboardView(self.app, self.session))
        else:
            self.app.show_view(MainMenuView(self.app, self.session))

    def select_category(self, category: str) -> None:
        self.category = category
        matching = self.category_algorithms
        if matching:
            self.selected = matching[0][0]
        self.execute(reset=True)
        self.rebuild_ui()

    def select_algorithm(self, index: int) -> None:
        self.selected = index
        self.category = CATALOG[index][4]
        self.session.selected_algorithm = CATALOG[index][0]
        self.session.save_state()
        self.execute(reset=True)
        self.rebuild_ui()

    def cycle_circuit(self) -> None:
        self.lab_track_index = (self.lab_track_index + 1) % len(self.session.tracks)
        self.source_id, self.target_id = self.track.start_id, self.track.finish_id
        self.dataset = self.track.id
        self.execute(reset=True)
        self.status = f"Loaded {self.track.name} for the Lab only; game session and race plan were preserved."
        self.rebuild_ui()

    def cycle_source(self) -> None:
        ids = sorted(self.track.graph().vertices)
        self.source_id = ids[(ids.index(self.source_id) + 1) % len(ids)]
        self.execute(reset=True)
        self.rebuild_ui()

    def cycle_target(self) -> None:
        ids = sorted(self.track.graph().vertices)
        self.target_id = ids[(ids.index(self.target_id) + 1) % len(ids)]
        self.execute(reset=True)
        self.rebuild_ui()

    def load_example(self) -> None:
        self.source_id, self.target_id = self.track.start_id, self.track.finish_id
        self.preset, self.dataset = "balanced", "current circuit"
        self.execute(reset=True)
        self.status = f"Loaded the validated {self.algorithm_name} example on {self.track.name}."
        self.rebuild_ui()

    def show_pseudocode(self) -> None:
        self.detail_tab, self.help_open = "pseudocode", False

    def show_explanation(self) -> None:
        self.detail_tab, self.help_open = "explanation", False

    def toggle_help(self) -> None:
        self.help_open = not self.help_open

    def cycle_speed(self) -> None:
        self.playback_speed = self.SPEEDS[(self.SPEEDS.index(self.playback_speed) + 1) % len(self.SPEEDS)]
        self.status = f"Playback speed set to {self.playback_speed:g}×; recorded execution steps are unchanged."
        self.rebuild_ui()

    def toggle_playback(self) -> None:
        if not self.steps:
            self.error = "This algorithm produced no trace steps."
            self.status = "Run could not start because the trace is empty."
            return
        if self.step_index >= len(self.steps):
            self.step_index = 0
        self.playing = not self.playing
        self.status = "Playback running." if self.playing else "Playback paused at the current recorded step."
        self.rebuild_ui()

    def next_step(self) -> None:
        self.playing = False
        self.step_index = min(len(self.steps), self.step_index + 1)
        self.status = self._step_status()
        self.rebuild_ui()

    def previous_step(self) -> None:
        self.playing = False
        self.step_index = max(0, self.step_index - 1)
        self.status = f"Restored recorded step {self.step_index}/{len(self.steps)}."
        self.rebuild_ui()

    def seek_step(self, index: int) -> None:
        self.playing = False
        self.step_index = max(0, min(len(self.steps), index))
        self.status = self._step_status()
        self.rebuild_ui()

    def _step_status(self) -> str:
        if not self.step_index:
            return "Trace reset. Press RUN or NEXT to begin."
        step = self.steps[self.step_index - 1]
        return f"Step {self.step_index}/{len(self.steps)}: {step.get('operation', 'state')} — {step.get('explanation', '')}"

    def execute(self, reset: bool = False) -> None:
        if reset:
            self.step_index, self.playing = 0, False
        self.error, self.comparison = None, None
        try:
            self.result, self.steps = self._run_algorithm()
            self.status = f"{self.algorithm_name} ready: {len(self.steps)} recorded operations."
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            self.result, self.steps = None, []
            self.error = f"{type(exc).__name__}: {exc}"
            self.status = "Execution error — correct the input or choose EXAMPLE INPUT."

    def _run_algorithm(self):
        name, graph = self.algorithm_name, self.track.graph()
        if name in {"BFS", "DFS", "Dijkstra", "A*"}:
            return self._run_graph_algorithm(name, graph)
        if name in {"0/1 Knapsack DP", "Greedy"}:
            return self._run_pickup_algorithm(name)
        if name == "Refuelling DP":
            planner = RoutePlanner(self.track, self.preset)
            report = planner.plan_route(self.source_id, self.target_id, "dijkstra", checkpoint_aware=False)
            if not report:
                return None, [{"operation": "unreachable", "state": {}, "counters": {}, "explanation": "No legal route reaches the selected destination."}]
            fuel = report.get("resources", {}).get("fuel")
            steps = [{"operation": "fuel_state", "state": {"leg": i + 1, "demand": demand, "path": report.get("path", [])}, "counters": {"states": getattr(fuel, "states", 0)}, "explanation": "The refuelling DP evaluates legal purchases before this route leg."} for i, demand in enumerate(self._route_demands(report.get("path", [])))]
            return fuel, steps or [{"operation": "complete", "state": {}, "counters": {}, "explanation": "The selected route requires no additional fuel states."}]
        if name == "Backtracking":
            trace = TraceCollector()
            result = place_services_backtracking(list(graph.vertices), set(self.track.checkpoint_ids), required=2, trace=trace)
            return result, self._trace_steps(trace, "Backtracking tests a placement and undoes it when constraints fail.")
        if name == "Kruskal MST":
            trace = TraceCollector()
            edges = [(e.from_id, e.to_id, e.distance) for e in self.track.edges if not e.directed]
            result = kruskal_mst(list(graph.vertices), edges, trace=trace)
            return result, self._trace_steps(trace, "Kruskal accepts an edge only when its two components are different.")
        if name == "Event Min-Heap":
            return self._run_event_heap()
        return self._run_sort(name)

    def _run_graph_algorithm(self, name, graph):
        trace = TraceCollector()
        if name == "BFS":
            result = bfs(graph, self.source_id, self.target_id, trace=trace)
        elif name == "DFS":
            result = dfs(graph, self.source_id, self.target_id, trace=trace)
        else:
            planner = RoutePlanner(self.track, self.preset)
            if name == "Dijkstra":
                result = dijkstra(graph, self.source_id, self.target_id, edge_cost=planner.cost_model.cost, trace=trace)
            else:
                def heuristic(a, b):
                    va, vb = graph.vertices[a], graph.vertices[b]
                    straight = math.hypot(va.x - vb.x, va.y - vb.y)
                    ratio = min((planner.cost_model.cost(e) / max(e.distance, 1e-9) for e in graph.edges.values()), default=0.0)
                    return straight * ratio
                result = astar(graph, self.source_id, self.target_id, edge_cost=planner.cost_model.cost, heuristic=heuristic, trace=trace)
        steps = self._trace_steps(trace, self._graph_explanation(name))
        if result.path:
            steps.append({"operation": "complete", "state": {"path": result.path, "cost": result.cost}, "counters": result.counters.__dict__.copy(), "explanation": f"Final route contains {len(result.path) - 1} road legs."})
        return result, steps

    def _run_pickup_algorithm(self, name):
        items = self._knapsack_items()
        if name == "0/1 Knapsack DP":
            result = knapsack_01(items, 10)
            table = result.details.get("table", []) if result.details else []
            steps = [{"operation": "dp_cell", "state": {"row": row, "budget": budget, "value": value}, "counters": {"states": row * 11 + budget + 1}, "explanation": "DP compares excluding this item with taking it when capacity allows."} for row, values in enumerate(table) for budget, value in enumerate(values)]
            return result, steps
        result = greedy_knapsack(items, 10)
        selected = {item["id"] for item in result.selected}
        ordered = sorted(items, key=lambda item: (-item["benefit"] / item["cost"], item["id"]))
        return result, [{"operation": "consider", "state": {"item": item, "accepted": item["id"] in selected, "remaining": result.details.get("remaining_budget", 0)}, "counters": {"states": i + 1}, "explanation": "Greedy accepts the next highest benefit-to-cost item when it fits."} for i, item in enumerate(ordered)]

    def _run_event_heap(self):
        scheduler = EventScheduler()
        events = ((1, EventType.NITRO_BOOSTER, 40.0, 6), (2, EventType.ROAD_BLOCKAGE, 40.0, 1), (3, EventType.OIL_SPILL, 40.0, 3), (4, EventType.SPEED_RESTRICTION, 45.0, 4), (5, EventType.FUEL_STATION, 52.0, 5), (6, EventType.SHORTCUT_TOGGLE, 40.0, 2))
        steps = []
        for event_id, event_type, trigger_time, priority in events:
            scheduler.schedule(
                Event(
                    event_id=event_id,
                    type=event_type,
                    trigger_time=trigger_time,
                    priority=priority,
                    insertion_sequence=event_id,
                    target_id=0,
                    payload={"target": 0},
                )
            )
            steps.append({"operation": "insert", "state": {"event": event_id, "type": event_type.value, "heap": [item[1] for item in scheduler.heap]}, "counters": {"heap_operations": scheduler.heap_operations}, "explanation": "The event is placed by trigger time, priority, and insertion sequence."})
        ordered = scheduler.pop_due(40.0)
        for event in ordered:
            steps.append({"operation": "extract_min", "state": {"event": event.event_id, "type": event.type.value, "heap": [item[1] for item in scheduler.heap]}, "counters": {"heap_operations": scheduler.heap_operations}, "explanation": "The minimum event is extracted; priority breaks equal-time ties."})
        return {"ordered_event_ids": [event.event_id for event in ordered], "heap_operations": scheduler.heap_operations, "remaining": [item[1] for item in scheduler.heap]}, steps

    def _run_sort(self, name):
        records, trace = self._sample_records(), []

        def callback(operation, state):
            trace.append((operation, state))
        if name == "Merge Sort":
            result = merge_sort(records, key=self._ranking_key, trace=callback)
        elif name == "Quick Sort":
            result = quick_sort(records, key=self._ranking_key, trace=callback)
        else:
            result = heap_sort(records, key=self._ranking_key, trace=callback)
        steps = [{"operation": operation, "state": state, "counters": {"comparisons": i + 1}, "explanation": self._sort_explanation(operation)} for i, (operation, state) in enumerate(trace)]
        steps.append({"operation": "complete", "state": {"ranking": result}, "counters": {"comparisons": len(trace)}, "explanation": "The final ranking uses the authoritative championship comparator."})
        return result, steps

    @staticmethod
    def _trace_steps(trace, explanation):
        return [{"operation": step.operation, "state": step.state, "counters": step.counters, "explanation": explanation} for step in trace.steps]

    @staticmethod
    def _graph_explanation(name):
        return {"BFS": "BFS explores the oldest queued frontier first and minimizes edge count, not weighted cost.", "DFS": "DFS follows one branch deeply, then backtracks; a parent edge is not a false undirected cycle.", "Dijkstra": "Dijkstra extracts the smallest tentative weighted cost and relaxes legal roads.", "A*": "A* orders the open set by g + h; the heuristic is a lower-bound distance ratio."}[name]

    @staticmethod
    def _sort_explanation(operation):
        return {"split": "The input is divided into smaller subarrays.", "compare": "The shared ranking comparator decides which record comes first.", "merge": "Sorted subarrays are merged into a stable result.", "pivot": "The last record is the documented partition pivot.", "swap": "Records move around the pivot.", "extract": "The smallest decorated record is extracted from the heap."}.get(operation, "The production sorting implementation recorded this operation.")

    def _route_demands(self, path):
        graph = self.track.graph()
        return [max(0, math.ceil(graph.edge_between(a, b).effective_fuel() * 10)) for a, b in zip(path, path[1:]) if graph.edge_between(a, b)]

    @staticmethod
    def _knapsack_items():
        return [{"id": 1, "name": "A", "cost": 6, "benefit": 30}, {"id": 2, "name": "B", "cost": 5, "benefit": 24}, {"id": 3, "name": "C", "cost": 5, "benefit": 24}]

    @staticmethod
    def _sample_records():
        return [{"racer_id": 1, "name": "Player", "total_points": 54, "wins": 2, "sum_of_finish_positions": 5, "best_fastest_lap": 21.3}, {"racer_id": 2, "name": "Navigator", "total_points": 54, "wins": 2, "sum_of_finish_positions": 6, "best_fastest_lap": 20.9}, {"racer_id": 3, "name": "Shortcut", "total_points": 45, "wins": 1, "sum_of_finish_positions": 7, "best_fastest_lap": 22.1}, {"racer_id": 4, "name": "Distance", "total_points": 36, "wins": 0, "sum_of_finish_positions": 9, "best_fastest_lap": None}]

    @staticmethod
    def _ranking_key(item):
        return (-item["total_points"], -item["wins"], item["sum_of_finish_positions"], item["best_fastest_lap"] if item["best_fastest_lap"] is not None else float("inf"), item["racer_id"])

    def compare(self):
        from smart_racing.arcade_ui.comparison_view import AlgorithmComparisonView

        self.playing = False
        self.app.show_view(AlgorithmComparisonView(self.app, self.session, self.algorithm_name))

    def run_experiment(self):
        samples = []
        for _ in range(5):
            started = perf_counter()
            self._run_algorithm()
            samples.append((perf_counter() - started) * 1000)
        self.experiment = {"algorithm": self.algorithm_name, "circuit": self.track.id, "runs": 5, "mean_ms": sum(samples) / len(samples), "min_ms": min(samples), "max_ms": max(samples)}
        self.status = f"Experiment complete: 5 fresh runs, mean {self.experiment['mean_ms']:.3f} ms."
        self.rebuild_ui()

    def export_result(self):
        path = _root() / "data" / "arcade_lab_export.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"algorithm": self.algorithm_name, "category": self.category, "circuit": self.track.id, "source": self.source_id, "target": self.target_id, "preset": self.preset, "step": self.step_index, "steps": self.steps, "result": self._jsonable(self.result), "comparison": self._jsonable(self.comparison), "experiment": self.experiment}
        path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        self.status = f"Exported actual trace, result, comparison, and experiment data to {path.name}."
        self.rebuild_ui()

    def _draw_header(self, width, height):
        _text("ALGORITHM LAB", 160, height - 28, 24, WHITE, bold=True)
        _text(f"SMART RACING CHAMPIONSHIP  ·  {self.category.upper()}", 160, height - 52, 11, MUTED)
        _text(self.algorithm_name, width / 2, height - 34, 15, CYAN, anchor_x="center", bold=True)
        _text(self.track.name, width - 180, height - 34, 12, WHITE, anchor_x="center")
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)

    def _draw_left_panel(self):
        left, bottom, width, height = 18, 108, 220, max(390, self.window.height - 236)
        self.draw_panel(left, bottom, width, height, 246)
        _text("ALGORITHMS", left + 12, bottom + height - 28, 12, WHITE, bold=True)
        _text(self.category.upper(), left + 12, bottom + height - 46, 9, CYAN)
        _text("INPUTS", left + 12, bottom + 174, 10, MUTED, bold=True)
        for index, line in enumerate((f"Circuit: {self.track.id}", f"Source: V{self.source_id}", f"Target: V{self.target_id}", f"Preset: {self.preset.title()}")):
            _text(line, left + 12, bottom + 154 - index * 18, 10, WHITE)
        if self.error:
            _text(self.error, left + 12, bottom + 18, 9, CORAL, width=width - 24)

    def _example_label(self):
        return {"0/1 Knapsack DP": "Capacity 10 · A/B/C counterexample", "Greedy": "Same capacity-10 pickup set", "Event Min-Heap": "Six events at deterministic priorities"}.get(self.algorithm_name, "Validated circuit graph")

    def _draw_center(self):
        left, bottom, width, height = self.center_rect
        self.draw_panel(left, bottom, width, height, 244)
        _text("LIVE EXECUTION VISUALIZATION", left + 16, bottom + height - 28, 14, WHITE, bold=True)
        _text(f"{self.algorithm_name}  ·  STEP {self.step_index:02d}/{len(self.steps):02d}", left + width - 16, bottom + height - 28, 10, CYAN, anchor_x="right")
        if self.comparison is not None:
            self._draw_comparison(left + 12, bottom + 44, width - 24, height - 84)
        elif self.help_open:
            self._draw_help(left + 16, bottom + 54, width - 32, height - 108)
        elif self.algorithm_name in {"BFS", "DFS", "Dijkstra", "A*", "Refuelling DP", "Backtracking", "Kruskal MST"}:
            self._draw_graph_visual(left + 12, bottom + 58, width - 24, height - 108)
        elif self.algorithm_name == "0/1 Knapsack DP":
            self._draw_dp_visual(left + 16, bottom + 86, width - 32, height - 140)
        elif self.algorithm_name == "Greedy":
            self._draw_greedy_visual(left + 16, bottom + 86, width - 32, height - 140)
        elif self.algorithm_name == "Event Min-Heap":
            self._draw_heap_visual(left + 16, bottom + 86, width - 32, height - 140)
        else:
            self._draw_sort_visual(left + 16, bottom + 86, width - 32, height - 140)
        self._draw_detail_strip(left + 16, bottom + 48, width - 32, 72)
        timeline_left, timeline_bottom, timeline_width, _ = self.timeline_rect
        arcade.draw_lbwh_rectangle_filled(timeline_left, timeline_bottom, timeline_width, 8, (48, 65, 84))
        progress = self.step_index / max(1, len(self.steps))
        arcade.draw_lbwh_rectangle_filled(timeline_left, timeline_bottom, timeline_width * progress, 8, CYAN)
        arcade.draw_circle_filled(timeline_left + timeline_width * progress, timeline_bottom + 4, 7, WHITE)
        _text("Timeline · click to seek", timeline_left, timeline_bottom + 16, 9, MUTED)

    def _draw_graph_visual(self, left, bottom, width, height):
        graph = self.track.graph()
        xs, ys = [v.x for v in graph.vertices.values()], [v.y for v in graph.vertices.values()]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        scale = min((width - 50) / max(1, xmax - xmin), (height - 45) / max(1, ymax - ymin))
        def point(vertex):
            return left + width / 2 + (vertex.x - (xmin + xmax) / 2) * scale, bottom + height / 2 + (vertex.y - (ymin + ymax) / 2) * scale
        active_vertex = self._current_state().get("vertex", self._current_state().get("current", self._current_state().get("to")))
        result_path = self._result_path() if self.step_index >= len(self.steps) else []
        visited = self._visited_vertices()
        placements = set(self._current_state().get("placements", []))
        accepted_edges = {
            tuple(step.get("state", {}).get("edge", ()))
            for step in self.steps[: self.step_index]
            if step.get("operation") == "accept"
        }
        for edge in graph.edges.values():
            source, target = graph.vertices[edge.from_id], graph.vertices[edge.to_id]
            edge_pair = (edge.from_id, edge.to_id)
            reverse_pair = (edge.to_id, edge.from_id)
            if edge.status.value == "Blocked":
                color = CORAL
            elif self.algorithm_name == "Kruskal MST" and (edge_pair in accepted_edges or reverse_pair in accepted_edges):
                color = EMERALD
            elif edge.from_id in result_path and edge.to_id in result_path:
                color = CYAN
            else:
                color = (67, 83, 105)
            arcade.draw_line(*point(source), *point(target), color, 5 if edge.is_shortcut else 3)
        for source_id, target_id in zip(result_path, result_path[1:]):
            arcade.draw_line(*point(graph.vertices[source_id]), *point(graph.vertices[target_id]), EMERALD, 7)
        for vertex in graph.vertices.values():
            px, py = point(vertex)
            if vertex.id == active_vertex:
                arcade.draw_circle_outline(px, py, 12, AMBER, 3)
            color = (
                EMERALD
                if vertex.id == self.source_id
                else CORAL
                if vertex.id == self.target_id
                else (165, 112, 255)
                if vertex.id in placements
                else AMBER
                if vertex.checkpoint_order
                else EMERALD
                if vertex.id in visited
                else MUTED
            )
            arcade.draw_circle_filled(px, py, 8 if vertex.checkpoint_order else 6, color)
            _text(f"CP{vertex.checkpoint_order}" if vertex.checkpoint_order else f"V{vertex.id}", px, py + 10, 8, WHITE, anchor_x="center")
        _text(f"V{self.source_id} → V{self.target_id} · visited {len(visited)} · route legs {max(0, len(result_path) - 1)}", left + 4, bottom + 4, 9, MUTED)

    def _draw_dp_visual(self, left, bottom, width, height):
        table = (self.result.details or {}).get("table", []) if self.result else []
        if not table:
            _text("DP table unavailable for this input.", left, bottom + height / 2, 12, CORAL)
            return
        cell_w, cell_h = min(42, (width - 50) / len(table[0])), min(28, (height - 38) / len(table))
        _text("CAPACITY / BUDGET", left, bottom + height - 16, 10, CYAN, bold=True)
        items = self._knapsack_items()
        for row, values in enumerate(table):
            _text("0" if row == 0 else items[row - 1]["name"], left, bottom + height - 38 - row * cell_h, 9, WHITE)
            for col, value in enumerate(values):
                x, y = left + 34 + col * cell_w, bottom + height - 48 - row * cell_h
                active = self._current_state().get("row") == row and self._current_state().get("budget") == col
                arcade.draw_lbwh_rectangle_filled(x, y, cell_w - 2, cell_h - 2, AMBER if active else (29, 53, 78))
                _text(f"{value:g}", x + (cell_w - 2) / 2, y + 7, 8, NAVY if active else WHITE, anchor_x="center")
        _text("The supplied counterexample selects B + C = 48, while value/cost Greedy selects A = 30.", left, bottom + 4, 9, MUTED)

    def _draw_greedy_visual(self, left, bottom, width, height):
        items = sorted(self._knapsack_items(), key=lambda value: -value["benefit"] / value["cost"])
        selected = {item["id"] for item in getattr(self.result, "selected", [])}
        maximum = max(item["benefit"] for item in items)
        for index, item in enumerate(items):
            y = bottom + height - 70 - index * 62
            bar = (width - 150) * item["benefit"] / maximum
            color = EMERALD if item["id"] in selected and index < self.step_index else AMBER if index == max(0, self.step_index - 1) else (48, 73, 96)
            arcade.draw_lbwh_rectangle_filled(left + 62, y, bar, 26, color)
            _text(f"{item['name']} cost {item['cost']} / value {item['benefit']}", left, y + 7, 10, WHITE)
        _text("Greedy ranks benefit ÷ cost. It is a feasible heuristic, not an optimality guarantee.", left, bottom + 4, 9, MUTED)

    def _draw_heap_visual(self, left, bottom, width, height):
        heap = self._current_state().get("heap", [])
        if self.step_index and not heap and isinstance(self.result, dict):
            heap = self.result.get("remaining", [])
        _text("BINARY HEAP", left, bottom + height - 18, 11, CYAN, bold=True)
        for index, event_id in enumerate(heap[:10]):
            level = int(math.log2(index + 1)) if index else 0
            slot, nodes = index - (2**level - 1), 2**level
            x, y = left + width / 2 + (slot - (nodes - 1) / 2) * min(70, width / max(2, nodes + 1)), bottom + height - 58 - level * 55
            arcade.draw_circle_filled(x, y, 17, AMBER if index == 0 else (48, 73, 96))
            _text(f"E{event_id}", x, y - 5, 9, NAVY if index == 0 else WHITE, anchor_x="center")
        _text("Event array: " + str(heap), left, bottom + 18, 9, MUTED, width=width)
        _text("Ordering: trigger time → priority → insertion sequence.", left, bottom + 4, 9, WHITE)

    def _draw_sort_visual(self, left, bottom, width, height):
        state = self._current_state()
        records = state.get("values")
        if records is None:
            records = self._result_value() if self.step_index else self._sample_records()
        if not isinstance(records, list):
            records = self._sample_records()
        if not records:
            return
        maximum, bar_w = max(record["total_points"] for record in records), max(22, (width - 30) / len(records) - 10)
        for index, record in enumerate(records):
            bar_h = (height - 80) * record["total_points"] / maximum
            x = left + 14 + index * (bar_w + 10)
            arcade.draw_lbwh_rectangle_filled(x, bottom + 36, bar_w, bar_h, CYAN if index < self.step_index else (49, 83, 111))
            _text(record["name"], x + bar_w / 2, bottom + 20, 9, WHITE, anchor_x="center")
            _text(str(record["total_points"]), x + bar_w / 2, bottom + 42 + bar_h, 9, AMBER, anchor_x="center")
        _text("Bars show points; ranking uses wins, finish sum, fastest lap, then racer ID.", left, bottom + 4, 9, MUTED)

    def _draw_detail_strip(self, left, bottom, width, height):
        arcade.draw_lbwh_rectangle_filled(left, bottom, width, height, (19, 37, 58))
        title = "PSEUDOCODE" if self.detail_tab == "pseudocode" else "STEP EXPLANATION"
        _text(title, left + 10, bottom + height - 20, 10, CYAN, bold=True)
        if self.detail_tab == "pseudocode":
            lines, current = PSEUDOCODE[self.algorithm_name], self.step_index % len(PSEUDOCODE[self.algorithm_name])
            for index, line in enumerate(lines[:3]):
                _text(("▶ " if index == current else "  ") + line, left + 10, bottom + height - 38 - index * 14, 9, AMBER if index == current else WHITE)
        else:
            current = self.steps[self.step_index - 1] if self.step_index else None
            explanation = current.get("explanation", "Press RUN or NEXT STEP to observe the first operation.") if current else "Press RUN or NEXT STEP to observe the first operation."
            _text(explanation, left + 10, bottom + height - 42, 10, WHITE, width=width - 20)

    def _draw_comparison(self, left, bottom, width, height):
        _text(self.comparison.get("title", "Comparison"), left, bottom + height - 20, 16, WHITE, bold=True)
        same = self.comparison.get("same")
        _text(f"Same result: {'YES' if same else 'NO'}  ·  {self.comparison.get('metric', '')}", left, bottom + height - 42, 11, EMERALD if same else AMBER)
        cards = [("A", self.comparison.get("left")), ("B", self.comparison.get("right")), ("C", self.comparison.get("third"))]
        visible = [card for card in cards if card[1] is not None]
        card_width = (width - 12 * (len(visible) - 1)) / max(1, len(visible))
        for index, (label, value) in enumerate(visible):
            x = left + index * (card_width + 12)
            arcade.draw_lbwh_rectangle_filled(x, bottom + 40, card_width, height - 110, (29, 53, 78))
            _text(label, x + 12, bottom + height - 76, 13, CYAN, bold=True)
            for line_index, line in enumerate(self._summary_lines(value)[:8]):
                _text(line, x + 12, bottom + height - 100 - line_index * 20, 10, WHITE, width=card_width - 24)

    def _draw_help(self, left, bottom, width, height):
        _text(f"HOW TO READ {self.algorithm_name}", left, bottom + height - 22, 16, WHITE, bold=True)
        lines = (CATALOG[self.selected][1], f"Game role: {CATALOG[self.selected][3]}", "NEXT advances one recorded operation; RUN animates it; the timeline seeks.", "The inspector shows data structures and counters from the same execution.")
        for index, line in enumerate(lines):
            _text(line, left, bottom + height - 58 - index * 28, 11, WHITE if index == 0 else MUTED, width=width)

    def _draw_inspector(self):
        left, bottom, width, height = self.right_rect
        self.draw_panel(left, bottom, width, height, 246)
        _text("LIVE INSPECTOR", left + 14, bottom + height - 28, 15, WHITE, bold=True)
        _text(self.algorithm_name, left + 14, bottom + height - 50, 11, CYAN)
        _text("DATA STRUCTURE", left + 14, bottom + height - 84, 10, MUTED, bold=True)
        for index, line in enumerate(self._structure_lines(self._current_state())[:6]):
            _text(line, left + 14, bottom + height - 105 - index * 18, 10, WHITE, width=width - 28)
        _text("COUNTERS", left + 14, bottom + 240, 10, MUTED, bold=True)
        counters = self._current_counters()
        for index, line in enumerate((f"Visited: {counters.get('visited_vertices', 0)}", f"Expanded: {counters.get('expanded_vertices', 0)}", f"Relaxed/examined: {counters.get('relaxed_edges', 0)}/{counters.get('examined_edges', 0)}", f"Heap ops: {counters.get('heap_operations', 0)}", f"States/comparisons: {counters.get('states', 0)}/{counters.get('comparisons', 0)}")):
            _text(line, left + 14, bottom + 218 - index * 18, 10, WHITE)
        _text("COMPLEXITY", left + 14, bottom + 118, 10, MUTED, bold=True)
        _text(CATALOG[self.selected][2], left + 14, bottom + 98, 10, AMBER, width=width - 28)
        _text("RESULT", left + 14, bottom + 62, 10, MUTED, bold=True)
        for index, line in enumerate(self._summary_lines(self.result)[:3]):
            _text(line, left + 14, bottom + 44 - index * 15, 9, EMERALD if index == 0 else WHITE, width=width - 28)

    def _structure_lines(self, state):
        if self.algorithm_name == "BFS":
            return [f"Queue: {state.get('queue', [])}", f"Current: V{state.get('current', '—')}", f"Path edges: {max(0, len(self._result_path()) - 1)}"]
        if self.algorithm_name == "DFS":
            return [f"Stack: {state.get('stack', [])}", f"Current: V{state.get('vertex', '—')}", f"Cycles: {len(self._result_details().get('cycle_edges', []))}"]
        if self.algorithm_name in {"Dijkstra", "A*"}:
            return [f"Current: V{state.get('vertex', state.get('to', '—'))}", f"Score: {state.get('distance', state.get('g', '—'))}", f"Cost model: {self.preset.title()}", f"Path cost: {self._result_cost()}"]
        if self.algorithm_name == "Event Min-Heap":
            return [f"Heap array: {state.get('heap', [])}", f"Event: E{state.get('event', '—')}", "Key: time, priority, sequence"]
        if self.algorithm_name in {"Merge Sort", "Quick Sort", "Heap Sort"}:
            return [f"Records: {len(state.get('values', self._result_value() if isinstance(self._result_value(), list) else []))}", "Comparator: championship total order"]
        return [f"State: {self._display(state)}", "Input remains available in the left panel."]

    def _current_state(self):
        return self.steps[self.step_index - 1].get("state", {}) if self.step_index and self.step_index <= len(self.steps) else {}

    def _current_counters(self):
        if self.step_index and self.step_index <= len(self.steps):
            return self.steps[self.step_index - 1].get("counters", {})
        return getattr(getattr(self.result, "counters", None), "__dict__", {})

    def _result_path(self):
        return list(getattr(self.result, "path", []) or (self.result.get("path", []) if isinstance(self.result, dict) else []))

    def _result_details(self):
        return getattr(self.result, "details", {}) or {}

    def _result_cost(self):
        return getattr(self.result, "cost", None)

    def _result_value(self):
        return getattr(self.result, "value", self.result)

    def _visited_vertices(self):
        values = set()
        for step in self.steps[: self.step_index]:
            state = step.get("state", {})
            values.update(state[key] for key in ("vertex", "current", "to") if key in state)
        return values

    def _summary_lines(self, value):
        if value is None:
            return ["No result"]
        if isinstance(value, AlgorithmResult):
            return [f"path: {value.path}", f"cost: {value.cost}", f"time: {value.elapsed_ms:.3f} ms"]
        if hasattr(value, "value") and hasattr(value, "selected"):
            return [f"value: {value.value:g}" if isinstance(value.value, (int, float)) else f"value: {value.value}", f"selected: {len(value.selected)}", f"states: {value.states}"]
        if isinstance(value, dict):
            return [f"{key}: {self._display(item)}" for key, item in list(value.items())[:3]]
        if isinstance(value, list):
            return [f"ranking: {[item.get('name', item.get('racer_id')) for item in value]}"]
        return [self._display(value)]

    @staticmethod
    def _display(value):
        text = str(value)
        return text if len(text) <= 68 else text[:65] + "…"

    @staticmethod
    def _jsonable(value):
        if hasattr(value, "__dict__"):
            return {key: AlgorithmLabView._jsonable(item) for key, item in value.__dict__.items()}
        if isinstance(value, dict):
            return {str(key): AlgorithmLabView._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [AlgorithmLabView._jsonable(item) for item in value]
        return value

    def on_update(self, delta_time: float):
        if self.playing and self.steps:
            self._playback_elapsed += delta_time
            if self._playback_elapsed >= 0.75 / self.playback_speed:
                self._playback_elapsed = 0.0
                self.step_index = min(len(self.steps), self.step_index + 1)
                self.status = self._step_status()
                if self.step_index >= len(self.steps):
                    self.playing = False
                    self.status = f"{self.algorithm_name} playback completed."
                    self.rebuild_ui()

    def _step_status(self):
        if not self.step_index:
            return "Trace reset. Press RUN or NEXT to begin."
        step = self.steps[self.step_index - 1]
        return f"Step {self.step_index}/{len(self.steps)}: {step.get('operation', 'state')} — {step.get('explanation', '')}"

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            left, bottom, width, height = self.timeline_rect
            if left <= x <= left + width and bottom - 8 <= y <= bottom + height + 8:
                self.seek_step(round((x - left) / max(1, width) * len(self.steps)))

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            if self.help_open or self.comparison is not None:
                self.help_open, self.comparison = False, None
                self.rebuild_ui()
            else:
                self.go_back()
        elif symbol in (arcade.key.RIGHT, arcade.key.SPACE):
            self.next_step()
        elif symbol == arcade.key.LEFT:
            self.previous_step()
        elif symbol == arcade.key.ENTER:
            self.toggle_playback()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        self._draw_header(width, height)
        self._draw_left_panel()
        self._draw_center()
        self._draw_inspector()
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()
