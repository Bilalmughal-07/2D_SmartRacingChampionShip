from __future__ import annotations

import math
from dataclasses import dataclass, fields

from smart_racing.algorithms.astar import astar
from smart_racing.algorithms.bfs import bfs
from smart_racing.algorithms.common import Counters
from smart_racing.algorithms.dfs import dfs
from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.algorithms.dynamic_programming import knapsack_01, refuel_dp
from smart_racing.algorithms.greedy import greedy_knapsack
from smart_racing.model.graph import Track


@dataclass(frozen=True)
class CostPreset:
    name: str
    distance: float
    time: float
    fuel: float
    difficulty: float
    obstacle: float


ALGORITHM_COMPLEXITY = {
    "BFS": "O(V + E) — minimum edge count, not weighted cost",
    "DFS": "O(V + E) — traversal/path discovery, not weighted cost",
    "Dijkstra": "O((V + E) log V) — optimal for non-negative weights",
    "A*": "O((V + E) log V) worst case — admissible weighted search",
}


class CostModel:
    PRESETS = {
        "balanced": CostPreset("Balanced", 0.25, 0.25, 0.2, 0.2, 0.1),
        "speed": CostPreset("Speed", 0.15, 0.55, 0.1, 0.1, 0.1),
        "economy": CostPreset("Economy", 0.15, 0.15, 0.55, 0.1, 0.05),
        "safety": CostPreset("Safety", 0.15, 0.15, 0.1, 0.4, 0.2),
    }

    def __init__(self, preset: str = "balanced"):
        self.set_preset(preset)
        self.references = {
            "distance": 10.0,
            "time": 10.0,
            "fuel": 10.0,
            "difficulty": 5.0,
            "obstacle": 5.0,
        }

    def set_preset(self, preset: str) -> None:
        if preset not in self.PRESETS:
            raise ValueError(f"unknown preset {preset}")
        self.preset = preset

    def cost(self, edge) -> float:
        p = self.PRESETS[self.preset]
        values = {
            "distance": edge.distance / self.references["distance"],
            "time": edge.effective_time() / self.references["time"],
            "fuel": edge.effective_fuel() / self.references["fuel"],
            "difficulty": edge.effective_difficulty() / self.references["difficulty"],
            "obstacle": (
                edge.obstacle_penalty
                + sum(float(x.get("obstacle_penalty", 0)) for x in edge.effects.values())
            )
            / self.references["obstacle"],
        }
        return sum(
            weight * values[name]
            for name, weight in (
                ("distance", p.distance),
                ("time", p.time),
                ("fuel", p.fuel),
                ("difficulty", p.difficulty),
                ("obstacle", p.obstacle),
            )
        )


class RoutePlanner:
    def __init__(self, track: Track, preset: str = "balanced"):
        self.track = track
        self.graph = track.graph()
        self.cost_model = CostModel(preset)

    def set_preset(self, preset: str) -> None:
        self.cost_model.set_preset(preset)

    def plan_leg(self, source: int, target: int, algorithm: str = "dijkstra"):
        cost = self.cost_model.cost
        normalized = algorithm.lower()
        if normalized == "bfs":
            return bfs(self.graph, source, target)
        if normalized == "dfs":
            return dfs(self.graph, source, target)
        if normalized == "dijkstra":
            return dijkstra(self.graph, source, target, edge_cost=cost)
        if normalized == "astar":

            def heuristic(a, b):
                va, vb = self.graph.vertices[a], self.graph.vertices[b]
                straight = math.hypot(va.x - vb.x, va.y - vb.y)
                min_ratio = min(
                    (
                        cost(edge)
                        / max(
                            math.hypot(
                                self.graph.vertices[edge.from_id].x
                                - self.graph.vertices[edge.to_id].x,
                                self.graph.vertices[edge.from_id].y
                                - self.graph.vertices[edge.to_id].y,
                            ),
                            1e-9,
                        )
                        for edge in self.graph.edges.values()
                        if edge.distance > 0
                    ),
                    default=0.0,
                )
                return straight * min_ratio

            return astar(self.graph, source, target, edge_cost=cost, heuristic=heuristic)
        raise ValueError("algorithm must be bfs, dfs, dijkstra or astar")

    def plan_checkpoints(
        self,
        source: int,
        checkpoint_index: int = 0,
        algorithm: str = "dijkstra",
        destination: int | None = None,
        include_resources: bool = True,
    ):
        destination = self.track.finish_id if destination is None else destination
        remaining = self.track.checkpoint_ids[max(0, checkpoint_index) :]
        if destination in remaining:
            targets = remaining[: remaining.index(destination) + 1]
        else:
            targets = remaining + [destination]
        current = source
        path = []
        legs = []
        for target in targets:
            result = self.plan_leg(current, target, algorithm)
            if not result.path:
                return None
            legs.append(result)
            if not path:
                path.extend(result.path)
            else:
                path.extend(result.path[1:])
            current = target
        weighted = algorithm.lower() in {"dijkstra", "astar"}
        metrics = self.path_metrics(path)
        return {
            "path": path,
            # Use the final path metric as the single source of truth. Summing
            # floating-point leg costs can differ by a few ulps from the same
            # route evaluated edge-by-edge in path_metrics().
            "cost": metrics["weighted_cost"] if weighted else None,
            "weighted_cost": metrics["weighted_cost"],
            "legs": legs,
            "preset": self.cost_model.preset,
            "algorithm": algorithm,
            "checkpoint_aware": True,
            "targets": targets,
            "metrics": metrics,
            "counters": self._sum_counters(legs),
            "elapsed_ms": sum(result.elapsed_ms for result in legs),
            "complexity": ALGORITHM_COMPLEXITY.get(algorithm.title(), ALGORITHM_COMPLEXITY.get(algorithm, "")),
            "resources": self.resource_plan(path) if include_resources else None,
        }

    def plan_route(
        self,
        source: int,
        destination: int,
        algorithm: str = "dijkstra",
        checkpoint_aware: bool = True,
    ) -> dict | None:
        if checkpoint_aware:
            return self.plan_checkpoints(source, algorithm=algorithm, destination=destination)
        result = self.plan_leg(source, destination, algorithm=algorithm)
        if not result.path:
            return None
        metrics = self.path_metrics(result.path)
        return {
            "path": result.path,
            "cost": result.cost,
            "weighted_cost": metrics["weighted_cost"],
            "legs": [result],
            "preset": self.cost_model.preset,
            "algorithm": algorithm,
            "checkpoint_aware": False,
            "targets": [destination],
            "metrics": metrics,
            "counters": result.counters,
            "elapsed_ms": result.elapsed_ms,
            "complexity": ALGORITHM_COMPLEXITY.get(algorithm.title(), ALGORITHM_COMPLEXITY.get(algorithm, "")),
            "resources": self.resource_plan(result.path),
        }

    def compare_presets(
        self,
        source: int | None = None,
        target: int | None = None,
        algorithm: str = "dijkstra",
        checkpoint_aware: bool = True,
    ) -> dict:
        source = self.track.start_id if source is None else source
        target = self.track.finish_id if target is None else target
        saved = self.cost_model.preset
        result = {}
        for preset in self.cost_model.PRESETS:
            self.cost_model.set_preset(preset)
            if checkpoint_aware:
                result[preset] = self.plan_checkpoints(source, algorithm=algorithm, destination=target)
            else:
                leg = self.plan_leg(source, target, algorithm=algorithm)
                result[preset] = {
                    "path": leg.path,
                    "cost": leg.cost,
                    "weighted_cost": self.path_metrics(leg.path)["weighted_cost"],
                    "metrics": self.path_metrics(leg.path),
                    "counters": leg.counters,
                    "elapsed_ms": leg.elapsed_ms,
                    "algorithm": algorithm,
                    "preset": preset,
                }
        self.cost_model.set_preset(saved)
        return result

    def path_metrics(self, path: list[int]) -> dict:
        distance = 0.0
        travel_time = 0.0
        fuel = 0.0
        risk = 0.0
        weighted_cost = 0.0
        valid = bool(path)
        edge_ids: list[int] = []
        for source, target in zip(path, path[1:]):
            edge = self.graph.edge_between(source, target)
            if edge is None or not edge.traversable():
                valid = False
                continue
            edge_ids.append(edge.id)
            distance += edge.distance
            travel_time += edge.effective_time()
            fuel += edge.effective_fuel()
            risk += float(edge.effective_difficulty()) + float(edge.obstacle_penalty)
            weighted_cost += self.cost_model.cost(edge)
        return {
            "valid": valid,
            "edge_ids": edge_ids,
            "distance": distance,
            "travel_time": travel_time,
            "fuel": fuel,
            "risk": risk,
            "weighted_cost": weighted_cost,
        }

    @staticmethod
    def _sum_counters(results) -> Counters:
        counters = Counters()
        for result in results:
            for field in fields(Counters):
                name = field.name
                setattr(counters, name, getattr(counters, name) + getattr(result.counters, name))
        return counters

    def resource_plan(
        self,
        path: list[int],
        starting_fuel: float = 100.0,
        capacity: float = 100.0,
        purchase_cap: float = 40.0,
        stop_time: float = 3.0,
        max_nitro: int = 3,
    ) -> dict:
        """Use the existing refuelling DP and knapsack/greedy modules on one route."""
        scale = 10
        demands: list[int] = []
        stops: list[dict] = []
        for source, target in zip(path, path[1:]):
            edge = self.graph.edge_between(source, target)
            if edge is None or not edge.traversable():
                return {"fuel_feasible": False, "fuel": None, "nitro": {"dp": None, "greedy": None}}
            demands.append(max(0, math.ceil(edge.effective_fuel() * scale)))
            vertex = self.graph.vertices[source]
            stops.append({"vertex_id": source, "available": vertex.type.value == "FuelStation" and vertex.active})
        fuel_result = refuel_dp(
            stops,
            demands,
            int(round(capacity * scale)),
            int(round(starting_fuel * scale)),
            purchase_cap=int(round(purchase_cap * scale)),
            stop_time=stop_time,
        )
        required_stops = [
            {"vertex_id": path[item["stop_index"]], "buy": item["buy"] / scale}
            for item in fuel_result.selected
            if item["buy"] > 0
        ]
        pickup_items = []
        for index, vertex_id in enumerate(path):
            vertex = self.graph.vertices[vertex_id]
            if vertex.type.value == "NitroPickup" and vertex.active:
                pickup_items.append({"id": vertex_id, "cost": 1, "benefit": max(1, 6 - index / max(1, len(path)))})
        budget = max_nitro
        nitro_dp = knapsack_01(pickup_items, budget) if pickup_items else None
        nitro_greedy = greedy_knapsack(pickup_items, budget) if pickup_items else None
        return {
            "fuel_feasible": fuel_result.feasible,
            "fuel": fuel_result,
            "required_refuelling_stops": required_stops,
            "fuel_scale": scale,
            "nitro": {
                "items": pickup_items,
                "budget": budget,
                "dp": nitro_dp,
                "greedy": nitro_greedy,
            },
        }
