from __future__ import annotations

from collections import deque

from smart_racing.algorithms.common import AlgorithmResult, Timer
from smart_racing.model.graph import Graph


def bfs(graph: Graph, start: int, target: int | None = None, trace=None) -> AlgorithmResult:
    result = AlgorithmResult()
    with Timer() as timer:
        queue = deque([start])
        visited = {start}
        parent: dict[int, int | None] = {start: None}
        order: list[int] = []
        while queue:
            current = queue.popleft()
            if trace:
                trace.emit("dequeue", {"current": current, "queue": list(queue)}, result.counters)
            order.append(current)
            result.counters.visited_vertices += 1
            if target is not None and current == target:
                break
            for neighbor, _edge in graph.neighbors(current):
                result.counters.examined_edges += 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
                    if trace:
                        trace.emit(
                            "discover", {"current": current, "neighbor": neighbor}, result.counters
                        )
        path: list[int] = []
        if target is not None and target in visited:
            cursor: int | None = target
            while cursor is not None:
                path.append(cursor)
                cursor = parent[cursor]
            path.reverse()
        result.path = path
        result.value = order
        result.details = {
            "reachable": target is None or target in visited,
            "edge_count": max(0, len(path) - 1),
        }
    result.elapsed_ms = timer.elapsed_ms
    return result
