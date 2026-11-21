from __future__ import annotations

from dataclasses import dataclass

from smart_racing.model.graph import EdgeStatus, Track, VertexType
from smart_racing.services.route_planner import RoutePlanner


@dataclass
class ValidationReport:
    valid: bool
    errors: list[str]
    warnings: list[str]


class TrackValidator:
    def validate(self, track: Track) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        vertex_ids = {v.id for v in track.vertices}
        edge_ids = {e.id for e in track.edges}
        if len(vertex_ids) != len(track.vertices):
            errors.append("duplicate vertex ID")
        if len(edge_ids) != len(track.edges):
            errors.append("duplicate edge ID")
        if track.start_id not in vertex_ids:
            errors.append("missing start vertex")
        if track.finish_id not in vertex_ids:
            errors.append("missing finish vertex")
        if len(track.checkpoint_ids) < 10:
            errors.append("fewer than 10 mandatory checkpoints")
        if len(set(track.checkpoint_ids)) != len(track.checkpoint_ids):
            errors.append("duplicate checkpoint IDs")
        if any(cp not in vertex_ids for cp in track.checkpoint_ids):
            errors.append("checkpoint references missing vertex")
        if sum(e.is_shortcut for e in track.edges) < 2:
            errors.append("fewer than 2 shortcuts")
        for edge in track.edges:
            if edge.from_id not in vertex_ids or edge.to_id not in vertex_ids:
                errors.append(f"edge {edge.id} has dangling endpoint")
            if edge.distance < 0 or edge.base_time < 0 or edge.fuel_cost < 0:
                errors.append(f"edge {edge.id} has negative value")
            if edge.difficulty not in range(1, 6):
                errors.append(f"edge {edge.id} has invalid difficulty")
        graph = track.graph()
        for cp in track.checkpoint_ids:
            if not self._reachable(graph, track.start_id, cp):
                errors.append(f"checkpoint {cp} unreachable from start")
        has_cycle = False
        visited, stack = set(), set()

        def cycle(v):
            nonlocal has_cycle
            visited.add(v)
            stack.add(v)
            for nxt, _ in graph.neighbors(v):
                if nxt not in visited and cycle(nxt):
                    return True
                if nxt in stack:
                    return True
            stack.remove(v)
            return False

        for v in graph.vertices:
            if v not in visited and cycle(v):
                has_cycle = True
                break
        if not has_cycle:
            errors.append("no cycle detected")
        dead_ends = [v.id for v in track.vertices if v.type == VertexType.DEAD_END]
        if not dead_ends:
            errors.append("no designated dead end")
        if len({e.from_id for e in track.edges} | {e.to_id for e in track.edges}) < len(
            track.vertices
        ):
            warnings.append("isolated vertex")
        if not self._ordered_route_exists(track):
            errors.append("ordered checkpoint route to finish does not exist")
        if not self._complete_lap_exists(track):
            errors.append("complete lap return from finish to the first checkpoint does not exist")
        self._validate_resources(track, errors)
        self._validate_fuel_plan(track, errors)
        return ValidationReport(not errors, errors, warnings)

    @staticmethod
    def _reachable(graph, source, target):
        todo = [source]
        seen = {source}
        while todo:
            v = todo.pop()
            if v == target:
                return True
            for nxt, edge in graph.neighbors(v):
                if edge.status != EdgeStatus.BLOCKED and nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return False

    def _ordered_route_exists(self, track):
        current = track.start_id
        for target in [*track.checkpoint_ids, track.finish_id]:
            if not self._reachable(track.graph(), current, target):
                return False
            current = target
        return True

    def _complete_lap_exists(self, track):
        graph = track.graph()
        current = track.start_id
        for target in [*track.checkpoint_ids, track.finish_id]:
            if not self._reachable(graph, current, target):
                return False
            current = target
        return bool(track.checkpoint_ids) and self._reachable(graph, track.finish_id, track.checkpoint_ids[0])

    def _validate_resources(self, track, errors):
        graph = track.graph()
        resources = [
            vertex for vertex in track.vertices
            if vertex.type in (VertexType.FUEL_STATION, VertexType.NITRO_PICKUP)
        ]
        if not any(vertex.type == VertexType.FUEL_STATION for vertex in resources):
            errors.append("no fuel station defined")
        if not any(vertex.type == VertexType.NITRO_PICKUP for vertex in resources):
            errors.append("no nitro pickup defined")
        for vertex in resources:
            degree = sum(
                1 for edge in track.edges if edge.from_id == vertex.id or edge.to_id == vertex.id
            )
            if degree < 2:
                errors.append(f"resource vertex {vertex.id} is a dead-end or isolated service node")
            if not self._reachable(graph, track.start_id, vertex.id):
                errors.append(f"resource vertex {vertex.id} unreachable from start")
            if not self._reachable(graph, vertex.id, track.finish_id):
                errors.append(f"resource vertex {vertex.id} cannot reach finish")

    def _validate_fuel_plan(self, track, errors):
        planner = RoutePlanner(track)
        ordered = planner.plan_checkpoints(track.start_id, include_resources=True)
        if not ordered or not ordered.get("resources", {}).get("fuel_feasible", False):
            errors.append("ordered route has no feasible fuel plan")
        if track.checkpoint_ids:
            return_leg = planner.plan_route(
                track.finish_id,
                track.checkpoint_ids[0],
                algorithm="dijkstra",
                checkpoint_aware=False,
            )
            if not return_leg or not return_leg.get("resources", {}).get("fuel_feasible", False):
                errors.append("finish-to-first-checkpoint lap transition has no feasible fuel plan")
