from smart_racing.algorithms.astar import astar
from smart_racing.algorithms.backtracking import place_services_backtracking
from smart_racing.algorithms.bfs import bfs
from smart_racing.algorithms.common import TraceCollector
from smart_racing.algorithms.dfs import dfs
from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.algorithms.dynamic_programming import knapsack_01, refuel_dp
from smart_racing.algorithms.greedy import greedy_knapsack
from smart_racing.algorithms.mst import kruskal_mst
from smart_racing.algorithms.sorting import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.model.graph import Edge, Graph, Vertex


def sample_graph():
    return Graph(
        [Vertex(i, i, i) for i in range(5)],
        [
            Edge(1, 0, 1, 10, 1, 1),
            Edge(2, 1, 2, 1, 1, 1),
            Edge(3, 0, 2, 4, 1, 1),
            Edge(4, 2, 3, 2, 1, 1),
            Edge(5, 3, 4, 2, 1, 1),
        ],
    )


def test_bfs_minimum_edges_and_dfs_diagnostics():
    graph = sample_graph()
    assert bfs(graph, 0, 4).path == [0, 2, 3, 4]
    dfs_result = dfs(graph, 0, 4)
    assert dfs_result.details["reachable"]
    assert dfs_result.details["alternative_paths"]


def test_weighted_searches_agree():
    graph = sample_graph()
    d = dijkstra(graph, 0, 4)
    a = astar(graph, 0, 4, heuristic=lambda x, y: 0)
    assert d.cost == a.cost
    assert d.path == a.path


def test_algorithm_trace_is_optional_and_reusable():
    trace = TraceCollector()
    result = dijkstra(sample_graph(), 0, 4, trace=trace)
    assert result.path
    assert trace.steps
    assert trace.steps[0].operation == "extract_min"

    dfs_trace = TraceCollector()
    assert dfs(sample_graph(), 0, 4, trace=dfs_trace).path
    assert dfs_trace.steps


def test_blocked_edge_and_unreachable():
    graph = sample_graph()
    graph.set_edge_status(4, "Blocked")
    assert not dijkstra(graph, 0, 4).path


def test_dp_and_greedy_supplied_case():
    items = [
        {"id": 1, "name": "A", "cost": 6, "benefit": 30},
        {"id": 2, "name": "B", "cost": 5, "benefit": 24},
        {"id": 3, "name": "C", "cost": 5, "benefit": 24},
    ]
    assert greedy_knapsack(items, 10).value == 30
    result = knapsack_01(items, 10)
    assert result.value == 48
    assert {x["name"] for x in result.selected} == {"B", "C"}


def test_refuel_and_backtracking_and_mst():
    result = refuel_dp(
        [{"available": True}, {"available": True}], [40, 30], 100, 20, purchase_cap=40
    )
    assert result.feasible
    placement = place_services_backtracking(list(range(10)), {1, 2, 3}, 2)
    assert placement.valid
    mst = kruskal_mst([0, 1, 2], [(0, 1, 1), (1, 2, 2), (0, 2, 4)])
    assert mst["is_tree"] and mst["total_weight"] == 3

    placement_trace = TraceCollector()
    assert place_services_backtracking(list(range(10)), {1, 2, 3}, 2, trace=placement_trace).valid
    assert placement_trace.steps
    mst_trace = TraceCollector()
    kruskal_mst([0, 1, 2], [(0, 1, 1), (1, 2, 2), (0, 2, 4)], trace=mst_trace)
    assert {step.operation for step in mst_trace.steps} == {"accept", "reject_cycle"}


def test_all_sorts_and_top_k_match():
    values = [
        {
            "racer_id": i,
            "total_points": i % 3,
            "wins": i % 2,
            "sum_of_finish_positions": 10 - i,
            "best_fastest_lap": float(i),
        }
        for i in range(8)
    ]

    def key(value):
        return (
            -value["total_points"],
            -value["wins"],
            value["sum_of_finish_positions"],
            value["best_fastest_lap"],
            value["racer_id"],
        )

    expected = sorted(values, key=key)
    assert merge_sort(values, key=key) == expected
    assert quick_sort(values, key=key) == expected
    assert heap_sort(values, key=key) == expected
    assert top_k(values, 3, key=key) == expected[:3]

    for sorter in (merge_sort, quick_sort, heap_sort):
        trace = []
        assert sorter(values, key=key, trace=lambda operation, state: trace.append(operation)) == expected
        assert trace
