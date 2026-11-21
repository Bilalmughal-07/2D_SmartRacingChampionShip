from __future__ import annotations

import heapq
import math
from itertools import count

from smart_racing.algorithms.common import AlgorithmResult, Timer
from smart_racing.model.graph import Graph


def dijkstra(
    graph: Graph, start: int, target: int | None = None, edge_cost=None, trace=None
) -> AlgorithmResult:
    if edge_cost is None:

        def edge_cost(edge):
            return float(edge.distance)

    result = AlgorithmResult()
    with Timer() as timer:
        distances = {v: math.inf for v in graph.vertices}
        parent: dict[int, tuple[int, int] | None] = {start: None}
        distances[start] = 0.0
        sequence = count()
        heap: list[tuple[float, int, int]] = [(0.0, start, next(sequence))]
        while heap:
            distance, node, _ = heapq.heappop(heap)
            result.counters.heap_operations += 1
            if distance != distances[node]:
                continue
            result.counters.expanded_vertices += 1
            if trace:
                trace.emit("extract_min", {"vertex": node, "distance": distance}, result.counters)
            if target is not None and node == target:
                break
            for neighbor, edge in graph.neighbors(node):
                result.counters.examined_edges += 1
                weight = float(edge_cost(edge))
                if weight < 0:
                    raise ValueError("Dijkstra requires non-negative edge costs")
                candidate = distance + weight
                previous = parent.get(neighbor)
                previous_id = previous[0] if isinstance(previous, tuple) else 10**9
                if candidate < distances[neighbor] or (
                    candidate == distances[neighbor] and node < previous_id
                ):
                    distances[neighbor] = candidate
                    parent[neighbor] = (node, edge.id)
                    result.counters.relaxed_edges += 1
                    heapq.heappush(heap, (candidate, neighbor, next(sequence)))
                    result.counters.heap_operations += 1
                    if trace:
                        trace.emit(
                            "relax",
                            {"from": node, "to": neighbor, "distance": candidate},
                            result.counters,
                        )
        path: list[int] = []
        edges: list[int] = []
        if target is not None and math.isfinite(distances.get(target, math.inf)):
            cur = target
            path.append(cur)
            while parent.get(cur) is not None:
                previous, edge_id = parent[cur]  # type: ignore[misc]
                edges.append(edge_id)
                path.append(previous)
                cur = previous
            path.reverse()
            edges.reverse()
        result.path = path
        result.cost = None if target is None or not path else distances[target]
        result.value = distances
        result.details = {"reachable": bool(path), "edge_ids": edges}
    result.elapsed_ms = timer.elapsed_ms
    return result
