from __future__ import annotations

import heapq
import math
from itertools import count

from smart_racing.algorithms.common import AlgorithmResult, Timer
from smart_racing.model.graph import Graph


def astar(
    graph: Graph, start: int, target: int, edge_cost=None, heuristic=None, trace=None
) -> AlgorithmResult:
    if edge_cost is None:

        def edge_cost(edge):
            return float(edge.distance)

    if heuristic is None:

        def heuristic(a, b):
            return 0.0

    result = AlgorithmResult()
    with Timer() as timer:
        g_score = {v: math.inf for v in graph.vertices}
        g_score[start] = 0.0
        parent: dict[int, tuple[int, int] | None] = {start: None}
        sequence = count()
        heap: list[tuple[float, float, int, int]] = [
            (heuristic(start, target), 0.0, start, next(sequence))
        ]
        while heap:
            _f, current_g, node, _ = heapq.heappop(heap)
            result.counters.heap_operations += 1
            if current_g != g_score[node]:
                continue
            result.counters.expanded_vertices += 1
            if trace:
                trace.emit("expand", {"vertex": node, "g": current_g}, result.counters)
            if node == target:
                break
            for neighbor, edge in graph.neighbors(node):
                result.counters.examined_edges += 1
                weight = float(edge_cost(edge))
                if weight < 0:
                    raise ValueError("A* requires non-negative edge costs")
                candidate = current_g + weight
                previous = parent.get(neighbor)
                previous_id = previous[0] if isinstance(previous, tuple) else 10**9
                if candidate < g_score[neighbor] or (
                    candidate == g_score[neighbor] and node < previous_id
                ):
                    g_score[neighbor] = candidate
                    parent[neighbor] = (node, edge.id)
                    heapq.heappush(
                        heap,
                        (
                            candidate + heuristic(neighbor, target),
                            candidate,
                            neighbor,
                            next(sequence),
                        ),
                    )
                    result.counters.relaxed_edges += 1
                    result.counters.heap_operations += 1
                    if trace:
                        trace.emit(
                            "relax", {"from": node, "to": neighbor, "g": candidate}, result.counters
                        )
        path: list[int] = []
        edges: list[int] = []
        if math.isfinite(g_score.get(target, math.inf)):
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
        result.cost = None if not path else g_score[target]
        result.value = g_score
        result.details = {
            "reachable": bool(path),
            "edge_ids": edges,
            "heuristic": "admissible caller-supplied",
        }
    result.elapsed_ms = timer.elapsed_ms
    return result
