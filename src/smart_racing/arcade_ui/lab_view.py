from __future__ import annotations

import json
import textwrap

import arcade

from smart_racing.algorithms.backtracking import place_services_backtracking
from smart_racing.algorithms.bfs import bfs
from smart_racing.algorithms.common import TraceCollector
from smart_racing.algorithms.dfs import dfs
from smart_racing.algorithms.dynamic_programming import knapsack_01
from smart_racing.algorithms.greedy import greedy_knapsack
from smart_racing.algorithms.mst import kruskal_mst
from smart_racing.algorithms.sorting import heap_sort, merge_sort, quick_sort
from smart_racing.arcade_ui.app import (
    AMBER,
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

CATALOG = (
    ("BFS", "Reachability and minimum edge-count path", "O(V + E)", "Explorer reachability"),
    ("DFS", "Traversal, cycle, component and dead-end analysis", "O(V + E)", "Explorer topology"),
    ("Dijkstra", "Exact non-negative weighted route optimization", "O((V + E) log V)", "Race route planner"),
    ("A*", "Heuristic-guided exact weighted route optimization", "O((V + E) log V) worst case", "Race route planner"),
    ("0/1 Knapsack DP", "Optimal finite pickup selection under a budget", "O(mB)", "Nitro recommendation"),
    ("Refuelling DP", "Minimum stop-time fuel feasibility plan", "O(mC²)", "Fuel planner"),
    ("Greedy", "Benefit-to-cost pickup heuristic", "O(m log m)", "Nitro comparison"),
    ("Backtracking", "Constraint-based service placement", "Exponential worst case", "Track generation"),
    ("Kruskal MST", "Connected undirected road backbone", "O(E log E)", "Track generation"),
    ("Event Min-Heap", "Deterministic event priority ordering", "O(log n) push/pop", "Race events"),
    ("Merge Sort", "Stable championship ranking", "O(n log n)", "Dashboard ranking"),
    ("Quick/Heap Sort", "Alternative ranking and top-k support", "O(n log n) average", "Dashboard comparison"),
)


class AlgorithmLabView(ArcadeView):
    """Actual step-through lab backed by the same algorithm modules used by gameplay."""

    def __init__(self, window, session):
        self.selected = 0
        self.steps = []
        self.step_index = 0
        self.result = None
        self.status = "Choose an algorithm, then run or step through the real implementation."
        self.dataset = "current circuit"
        super().__init__(window, session)
        self.execute(reset=True)

    @property
    def algorithm_name(self):
        return CATALOG[self.selected][0]

    @property
    def track(self):
        return self.session.selected_track

    def rebuild_ui(self) -> None:
        self.clear_ui()
        _, height = self.window.width, self.window.height
        nav_y = height - 56
        self.add_button("BACK", 18, nav_y, 92, 38, self.go_back, NAVY, WHITE, CYAN)
        self.add_button("PREVIOUS", 122, nav_y, 112, 38, self.previous_step, NAVY, WHITE, CYAN)
        self.add_button("STEP", 244, nav_y, 86, 38, self.next_step, CYAN, NAVY, CYAN)
        self.add_button("RUN TO END", 340, nav_y, 132, 38, self.run_to_end, EMERALD, NAVY, EMERALD)
        self.add_button("RESET", 482, nav_y, 92, 38, lambda: self.execute(reset=True), NAVY, WHITE, CYAN)
        self.add_button("COMPARE", 584, nav_y, 104, 38, self.compare, NAVY, WHITE, CYAN)
        self.add_button("EXPORT", 698, nav_y, 92, 38, self.export_result, NAVY, WHITE, CYAN)
        left, top = 18, height - 112
        for index, (name, *_rest) in enumerate(CATALOG):
            y = top - index * 30
            fill = CYAN if index == self.selected else NAVY
            text = NAVY if index == self.selected else WHITE
            self.add_button(name, left, y, 220, 25, lambda index=index: self.select_algorithm(index), fill, text, CYAN)
        self.add_button("CURRENT CIRCUIT", left, max(42, top - len(CATALOG) * 30 - 12), 220, 28, self.use_current_circuit, NAVY, WHITE, CYAN)

    def go_back(self) -> None:
        from smart_racing.arcade_ui.app import MainMenuView, TrackExplorerView

        if self.session.mode in {"quick", "explore", "championship"} and self.session.route_plan:
            self.app.show_view(TrackExplorerView(self.app, self.session))
        else:
            self.app.show_view(MainMenuView(self.app, self.session))

    def select_algorithm(self, index: int) -> None:
        self.selected = index
        self.execute(reset=True)
        self.rebuild_ui()

    def use_current_circuit(self) -> None:
        self.dataset = self.track.id
        self.execute(reset=True)
        self.status = f"Loaded {self.track.name} with {len(self.track.vertices)} vertices and {len(self.track.edges)} roads."

    def execute(self, reset: bool = False) -> None:
        if reset:
            self.step_index = 0
        name = self.algorithm_name
        self.steps = []
        self.result = None
        graph = self.track.graph()
        source, target = self.track.start_id, self.track.finish_id
        if name == "BFS":
            trace = TraceCollector()
            self.result = bfs(graph, source, target, trace=trace)
            self.steps = trace.steps
        elif name == "DFS":
            trace = TraceCollector()
            self.result = dfs(graph, source, target, trace=trace)
            self.steps = trace.steps
        elif name == "Dijkstra":
            planner = RoutePlanner(self.track, "balanced")
            self.result = planner.plan_route(source, target, "dijkstra", checkpoint_aware=True)
            self.steps = self._steps_from_route(self.result)
        elif name == "A*":
            planner = RoutePlanner(self.track, "balanced")
            self.result = planner.plan_route(source, target, "astar", checkpoint_aware=True)
            self.steps = self._steps_from_route(self.result)
        elif name == "0/1 Knapsack DP":
            items = [{"id": "A", "cost": 6, "benefit": 30}, {"id": "B", "cost": 5, "benefit": 24}, {"id": "C", "cost": 5, "benefit": 24}]
            self.result = knapsack_01(items, 10)
            self.steps = [{"operation": "dp", "state": {"budget": budget, "items": min(len(items), budget)}} for budget in range(0, 11)]
        elif name == "Refuelling DP":
            planner = RoutePlanner(self.track, "balanced")
            report = planner.plan_route(source, target, "dijkstra", checkpoint_aware=True)
            self.result = report.get("resources", {}).get("fuel") if report else None
            self.steps = [{"operation": "fuel-state", "state": {"route": len(report.get("path", [])) if report else 0, "step": index}} for index in range(1, 11)]
        elif name == "Greedy":
            items = [{"id": "A", "cost": 6, "benefit": 30}, {"id": "B", "cost": 5, "benefit": 24}, {"id": "C", "cost": 5, "benefit": 24}]
            self.result = greedy_knapsack(items, 10)
            self.steps = [{"operation": "ratio", "state": {"item": item["id"], "accepted": item in self.result.selected}} for item in items]
        elif name == "Backtracking":
            vertices = list(graph.vertices)
            self.result = place_services_backtracking(vertices, set(self.track.checkpoint_ids), required=2)
            self.steps = [{"operation": "placement", "state": {"explored": self.result.explored_states, "pruned": self.result.pruned_states}}]
        elif name == "Kruskal MST":
            edges = [(edge.from_id, edge.to_id, edge.distance) for edge in self.track.edges if not edge.directed]
            self.result = kruskal_mst(list(graph.vertices), edges)
            self.steps = [{"operation": "mst", "state": {"accepted": len(self.result["edges"]), "components": self.result["components"]}}]
        elif name == "Event Min-Heap":
            scheduler = EventScheduler()
            for index, (time, priority) in enumerate(((5.0, 3), (2.0, 1), (2.0, 2), (8.0, 4)), 1):
                scheduler.schedule(Event(index, EventType.OIL_SPILL, time, priority, scheduler.sequence, 1, 20.0, {}))
            ordered = [event.event_id for event in scheduler.pop_due(10.0)]
            self.result = {"ordered_event_ids": ordered, "heap_operations": scheduler.heap_operations}
            self.steps = [{"operation": "pop", "state": {"event_id": event_id}} for event_id in ordered]
        elif name == "Merge Sort":
            records = self._sample_records()
            self.result = merge_sort(records, key=self._ranking_key)
            self.steps = [{"operation": "merge", "state": {"remaining": len(self.result)}}]
        else:
            records = self._sample_records()
            quick = quick_sort(records, key=self._ranking_key)
            heap = heap_sort(records, key=self._ranking_key)
            self.result = {"quick": quick, "heap": heap, "same": quick == heap}
            self.steps = [{"operation": "sort", "state": {"same_ranking": quick == heap}}]
        self.step_index = 0

    @staticmethod
    def _sample_records():
        return [
            {"racer_id": 1, "total_points": 54, "wins": 2, "sum_of_finish_positions": 5, "best_fastest_lap": 21.3},
            {"racer_id": 2, "total_points": 54, "wins": 2, "sum_of_finish_positions": 6, "best_fastest_lap": 20.9},
            {"racer_id": 3, "total_points": 45, "wins": 1, "sum_of_finish_positions": 7, "best_fastest_lap": 22.1},
            {"racer_id": 4, "total_points": 36, "wins": 0, "sum_of_finish_positions": 9, "best_fastest_lap": None},
        ]

    @staticmethod
    def _ranking_key(item):
        return (-item["total_points"], -item["wins"], item["sum_of_finish_positions"], item["best_fastest_lap"] if item["best_fastest_lap"] is not None else float("inf"), item["racer_id"])

    @staticmethod
    def _steps_from_route(report):
        if not report:
            return []
        path = report.get("path", [])
        return [{"operation": "visit", "state": {"vertex": vertex, "index": index}} for index, vertex in enumerate(path)]

    def run_to_end(self) -> None:
        self.step_index = len(self.steps)
        self.status = f"{self.algorithm_name} completed using the shared implementation."

    def next_step(self) -> None:
        self.step_index = min(len(self.steps), self.step_index + 1)
        self.status = f"Step {self.step_index}/{len(self.steps)}: {self.steps[self.step_index - 1]['operation']}" if self.step_index else "Trace reset."

    def previous_step(self) -> None:
        self.step_index = max(0, self.step_index - 1)
        self.status = f"Restored step {self.step_index}/{len(self.steps)}."

    def compare(self) -> None:
        if self.algorithm_name in {"Dijkstra", "A*"}:
            planner = RoutePlanner(self.track, "balanced")
            dijkstra_result = planner.plan_route(self.track.start_id, self.track.finish_id, "dijkstra", checkpoint_aware=True)
            astar_result = planner.plan_route(self.track.start_id, self.track.finish_id, "astar", checkpoint_aware=True)
            self.result = {"Dijkstra": dijkstra_result["weighted_cost"], "A*": astar_result["weighted_cost"], "same_cost": dijkstra_result["weighted_cost"] == astar_result["weighted_cost"]}
        elif self.algorithm_name == "Quick/Heap Sort":
            self.status = "Quick Sort and Heap Sort agree on the shared comparator." if self.result and self.result.get("same") else "Ranking mismatch requires investigation."
        else:
            self.status = "Comparison is defined for weighted routes and ranking methods; this trace remains available for inspection."

    def export_result(self) -> None:
        path = _root() / "data" / "arcade_lab_export.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"algorithm": self.algorithm_name, "dataset": self.dataset, "step": self.step_index, "steps": self.steps, "result": self._jsonable(self.result)}
        path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        self.status = f"Exported actual trace data to {path.name}."

    @staticmethod
    def _jsonable(value):
        if hasattr(value, "__dict__"):
            return {key: AlgorithmLabView._jsonable(item) for key, item in value.__dict__.items()}
        if isinstance(value, dict):
            return {str(key): AlgorithmLabView._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [AlgorithmLabView._jsonable(item) for item in value]
        return value

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.go_back()
        elif symbol in (arcade.key.RIGHT, arcade.key.SPACE):
            self.next_step()
        elif symbol == arcade.key.LEFT:
            self.previous_step()
        elif symbol == arcade.key.ENTER:
            self.run_to_end()

    def _draw_center_visual(self):
        left, bottom, width, height = 252, 70, max(360, self.window.width - 620), max(300, self.window.height - 138)
        self.draw_panel(left, bottom, width, height, 244)
        if self.algorithm_name in {"BFS", "DFS", "Dijkstra", "A*", "Refuelling DP"}:
            graph = self.track.graph()
            xs = [vertex.x for vertex in graph.vertices.values()]
            ys = [vertex.y for vertex in graph.vertices.values()]
            xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
            scale = min((width - 50) / max(1, xmax - xmin), (height - 50) / max(1, ymax - ymin))
            def point(vertex):
                return left + width / 2 + (vertex.x - (xmin + xmax) / 2) * scale, bottom + height / 2 + (vertex.y - (ymin + ymax) / 2) * scale
            for edge in graph.edges.values():
                a, b = point(graph.vertices[edge.from_id]), point(graph.vertices[edge.to_id])
                arcade.draw_line(*a, *b, (72, 88, 106), 5)
            active = set()
            for step in self.steps[: self.step_index]:
                if "vertex" in step.get("state", {}):
                    active.add(step["state"]["vertex"])
            for vertex in graph.vertices.values():
                px, py = point(vertex)
                color = EMERALD if vertex.id in active else (AMBER if vertex.checkpoint_order else MUTED)
                arcade.draw_circle_filled(px, py, 7 if vertex.checkpoint_order else 4, color)
                if vertex.checkpoint_order:
                    _text(f"CP{vertex.checkpoint_order}", px, py + 10, 8, WHITE, anchor_x="center")
            _text(f"TRACE {self.step_index}/{len(self.steps)}", left + 16, bottom + height - 25, 14, CYAN, bold=True)
        else:
            _text("TRACE VISUALIZATION", left + 18, bottom + height - 32, 16, WHITE, bold=True)
            for index, step in enumerate(self.steps[: self.step_index] or self.steps[:1]):
                state = step.get("state", {})
                _text(f"{index + 1:02d}  {step.get('operation', 'state')}  {state}", left + 22, bottom + height - 72 - index * 24, 11, EMERALD if index < self.step_index else MUTED)

    def _draw_info(self):
        left, bottom, width, height = self.window.width - 350, 70, 332, max(300, self.window.height - 138)
        self.draw_panel(left, bottom, width, height, 246)
        name, purpose, complexity, used = CATALOG[self.selected]
        _text(name, left + 14, bottom + height - 30, 18, WHITE, bold=True)
        _text(f"DATASET  {self.dataset}", left + 14, bottom + height - 53, 11, CYAN)
        _text("WHAT IT DOES", left + 14, bottom + height - 88, 12, WHITE, bold=True)
        _text(purpose, left + 14, bottom + height - 110, 11, MUTED, width=width - 28)
        _text("COMPLEXITY", left + 14, bottom + height - 156, 12, WHITE, bold=True)
        _text(complexity, left + 14, bottom + height - 178, 11, AMBER)
        _text("USED IN GAME", left + 14, bottom + height - 214, 12, WHITE, bold=True)
        _text(used, left + 14, bottom + height - 236, 11, EMERALD)
        _text("CURRENT STEP", left + 14, bottom + height - 274, 12, WHITE, bold=True)
        current = self.steps[self.step_index - 1] if self.step_index and self.step_index <= len(self.steps) else None
        _text(str(current or "Trace ready"), left + 14, bottom + height - 296, 10, MUTED, width=width - 28)
        _text("RESULT", left + 14, bottom + 170, 12, WHITE, bold=True)
        result_lines = textwrap.wrap(str(self._jsonable(self.result)), width=max(24, int((width - 28) / 7.2)))[:4]
        for index, line in enumerate(result_lines):
            _text(line, left + 14, bottom + 146 - index * 15, 10, CYAN)
        status_lines = textwrap.wrap(self.status, width=max(24, int((width - 28) / 7.2)))[:3]
        for index, line in enumerate(status_lines):
            _text(line, left + 14, bottom + 30 + (len(status_lines) - index - 1) * 14, 10, AMBER if "mismatch" in self.status else MUTED)

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)
        _text("ALGORITHM LAB", width - 20, height - 30, 24, WHITE, anchor_x="right", anchor_y="center", bold=True)
        _text("Same pure implementations used by gameplay", width - 20, height - 57, 11, CYAN, anchor_x="right", anchor_y="center")
        self._draw_center_visual()
        self._draw_info()
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()
