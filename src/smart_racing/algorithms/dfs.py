from __future__ import annotations

from smart_racing.algorithms.common import AlgorithmResult, Timer
from smart_racing.model.graph import Graph


def dfs(
    graph: Graph,
    start: int,
    target: int | None = None,
    max_paths: int = 20,
    max_path_length: int = 100,
    trace=None,
) -> AlgorithmResult:
    result = AlgorithmResult()
    with Timer() as timer:
        visited: set[int] = set()
        discovery: dict[int, int] = {}
        finish: dict[int, int] = {}
        parent: dict[int, int | None] = {start: None}
        cycle_edges: list[tuple[int, int]] = []
        dead_ends: list[int] = []
        order: list[int] = []
        clock = 0
        stack: list[tuple[int, int, list[tuple[int, int]]]] = [(start, 0, graph.neighbors(start))]
        visited.add(start)
        discovery[start] = clock
        clock += 1
        order.append(start)
        if trace:
            trace.emit("discover", {"vertex": start, "stack": [start]}, result.counters)
        while stack:
            node, index, neighbors = stack[-1]
            if index >= len(neighbors):
                stack.pop()
                finish[node] = clock
                clock += 1
                if len(neighbors) == 0:
                    dead_ends.append(node)
                    if trace:
                        trace.emit("dead_end", {"vertex": node, "stack": [item[0] for item in stack]}, result.counters)
                elif trace:
                    trace.emit("backtrack", {"vertex": node, "stack": [item[0] for item in stack]}, result.counters)
                continue
            neighbor, _edge = neighbors[index]
            stack[-1] = (node, index + 1, neighbors)
            result.counters.examined_edges += 1
            if trace:
                trace.emit("inspect_edge", {"from": node, "to": neighbor, "stack": [item[0] for item in stack]}, result.counters)
            if neighbor in visited:
                if neighbor not in finish and parent.get(node) != neighbor:
                    cycle_edges.append((node, neighbor))
                    if trace:
                        trace.emit("cycle", {"from": node, "to": neighbor}, result.counters)
                continue
            visited.add(neighbor)
            parent[neighbor] = node
            discovery[neighbor] = clock
            clock += 1
            order.append(neighbor)
            stack.append((neighbor, 0, graph.neighbors(neighbor)))
            if trace:
                trace.emit("discover", {"vertex": neighbor, "parent": node, "stack": [item[0] for item in stack]}, result.counters)
        result.counters.visited_vertices = len(visited)
        path: list[int] = []
        if target is not None and target in visited:
            cur: int | None = target
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            path.reverse()

        alternatives: list[list[int]] = []
        if target is not None:

            def walk(cur: int, current: list[int]) -> None:
                if len(alternatives) >= max_paths or len(current) > max_path_length:
                    return
                if cur == target:
                    alternatives.append(current.copy())
                    return
                for nxt, _edge in graph.neighbors(cur):
                    if nxt not in current:
                        walk(nxt, current + [nxt])

            walk(start, [start])
            alternatives = [p for p in alternatives if p != path]
        result.path = path
        result.value = order
        result.details = {
            "cycle_edges": cycle_edges,
            "dead_ends": dead_ends,
            "discovery": discovery,
            "finish": finish,
            "alternative_paths": alternatives,
            "reachable": target is None or target in visited,
        }
    result.elapsed_ms = timer.elapsed_ms
    return result
