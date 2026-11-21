from __future__ import annotations

import csv
import json
import random
import statistics
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, "src")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from smart_racing.algorithms.astar import astar
from smart_racing.algorithms.bfs import bfs
from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.algorithms.dynamic_programming import knapsack_01
from smart_racing.algorithms.greedy import greedy_knapsack
from smart_racing.algorithms.sorting import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.model.events import Event, EventType
from smart_racing.model.graph import Edge, Graph, Vertex
from smart_racing.services.event_scheduler import EventScheduler
from smart_racing.services.track_loader import load_tracks

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "experiments" / "data"
CHARTS = ROOT / "experiments" / "charts"
DATA.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)
RNG = random.Random(20261113)


def timed(fn, repeat=5):
    samples = []
    value = None
    for _ in range(2):
        fn()
    for _ in range(repeat):
        start = perf_counter()
        value = fn()
        samples.append((perf_counter() - start) * 1000)
    return value, statistics.mean(samples), statistics.median(samples), statistics.pstdev(samples)


def write_csv(path, rows):
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def graph_fixture(n):
    vertices = [Vertex(i, float(i), float(i % 7)) for i in range(n)]
    edges = [Edge(i, i, i + 1, 1, 1, 1) for i in range(n - 1)]
    extra_id = n
    for _ in range(max(1, n // 3)):
        a = RNG.randrange(0, n - 1)
        b = RNG.randrange(a + 1, n)
        edges.append(Edge(extra_id, a, b, max(1, b - a), 1, 1))
        extra_id += 1
    return Graph(vertices, edges)


def experiment_1():
    rows = []
    for n in [20, 40, 80, 160, 320]:
        graph = graph_fixture(n)
        for name, fn in [
            ("BFS", lambda: bfs(graph, 0, n - 1)),
            (
                "DFS",
                lambda: __import__("smart_racing.algorithms.dfs", fromlist=["dfs"]).dfs(
                    graph, 0, n - 1
                ),
            ),
        ]:
            result, mean, median, sd = timed(fn)
            rows.append(
                {
                    "experiment": 1,
                    "algorithm": name,
                    "vertices": n,
                    "edges": len(graph.edges),
                    "mean_ms": mean,
                    "median_ms": median,
                    "stdev_ms": sd,
                    "visited": result.counters.visited_vertices,
                    "examined_edges": result.counters.examined_edges,
                }
            )
    write_csv(DATA / "experiment_1_bfs_dfs.csv", rows)
    return rows


def experiment_2():
    rows = []
    for track in load_tracks():
        graph = track.graph()

        def model(edge):
            return edge.distance

        for name, fn in [
            ("Dijkstra", lambda: dijkstra(graph, track.start_id, track.finish_id, model)),
            ("A*", lambda: astar(graph, track.start_id, track.finish_id, model, lambda a, b: 0)),
        ]:
            result, mean, median, sd = timed(fn)
            rows.append(
                {
                    "experiment": 2,
                    "track": track.id,
                    "algorithm": name,
                    "vertices": len(graph.vertices),
                    "edges": len(graph.edges),
                    "mean_ms": mean,
                    "median_ms": median,
                    "stdev_ms": sd,
                    "expanded": result.counters.expanded_vertices,
                    "relaxed": result.counters.relaxed_edges,
                    "heap_operations": result.counters.heap_operations,
                    "path_cost": result.cost,
                }
            )
    write_csv(DATA / "experiment_2_dijkstra_astar.csv", rows)
    return rows


def experiment_3():
    rows = []
    for count in [10, 20, 40, 80]:
        items = [
            {"id": i, "cost": RNG.randint(1, 20), "benefit": RNG.randint(1, 50)}
            for i in range(count)
        ]
        budget = 50
        for name, fn in [
            ("DP", lambda: knapsack_01(items, budget)),
            ("Greedy", lambda: greedy_knapsack(items, budget)),
        ]:
            result, mean, median, sd = timed(fn)
            rows.append(
                {
                    "experiment": 3,
                    "algorithm": name,
                    "items": count,
                    "budget": budget,
                    "mean_ms": mean,
                    "median_ms": median,
                    "stdev_ms": sd,
                    "benefit": result.value,
                    "selected": len(result.selected),
                    "states": result.states,
                }
            )
    write_csv(DATA / "experiment_3_dp_greedy.csv", rows)
    return rows


def experiment_4():
    rows = []
    for count in [50, 100, 250, 500, 1000]:

        def run():
            scheduler = EventScheduler()
            for i in range(count):
                scheduler.schedule(Event(i, EventType.ROAD_BLOCKAGE, float(i % 20), i % 6, i))
            return scheduler.pop_due(1000), scheduler.heap_operations

        result, mean, median, sd = timed(run)
        rows.append(
            {
                "experiment": 4,
                "events": count,
                "mean_ms": mean,
                "median_ms": median,
                "stdev_ms": sd,
                "heap_operations": result[1],
            }
        )
    write_csv(DATA / "experiment_4_event_heap.csv", rows)
    return rows


def experiment_5():
    rows = []
    for n in [50, 100, 250, 500]:
        values = [
            {
                "racer_id": i,
                "total_points": RNG.randrange(100),
                "wins": RNG.randrange(5),
                "sum_of_finish_positions": RNG.randrange(50),
                "best_fastest_lap": RNG.random() * 100,
            }
            for i in range(n)
        ]

        def key(value):
            return (
                -value["total_points"],
                -value["wins"],
                value["sum_of_finish_positions"],
                value["best_fastest_lap"],
                value["racer_id"],
            )

        for name, fn in [
            ("Merge", lambda: merge_sort(values, key)),
            ("Quick", lambda: quick_sort(values, key)),
            ("Heap", lambda: heap_sort(values, key)),
            ("TopK", lambda: top_k(values, min(10, n), key)),
        ]:
            _, mean, median, sd = timed(fn)
            rows.append(
                {
                    "experiment": 5,
                    "algorithm": name,
                    "n": n,
                    "k": min(10, n),
                    "mean_ms": mean,
                    "median_ms": median,
                    "stdev_ms": sd,
                }
            )
    write_csv(DATA / "experiment_5_sorting_topk.csv", rows)
    return rows


def chart(rows, x, title, filename):
    plt.figure(figsize=(7, 4))
    names = sorted({row.get("algorithm", "run") for row in rows})
    for name in names:
        subset = [r for r in rows if r.get("algorithm", "run") == name]
        plt.plot([r[x] for r in subset], [r["mean_ms"] for r in subset], marker="o", label=name)
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel("mean time (ms)")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS / filename, dpi=140)
    plt.close()


def main():
    all_rows = [experiment_1(), experiment_2(), experiment_3(), experiment_4(), experiment_5()]
    chart(all_rows[0], "vertices", "Experiment 1: BFS vs DFS", "experiment_1.png")
    chart(all_rows[1], "vertices", "Experiment 2: Dijkstra vs A*", "experiment_2.png")
    chart(all_rows[2], "items", "Experiment 3: DP vs Greedy", "experiment_3.png")
    chart(all_rows[3], "events", "Experiment 4: Event heap", "experiment_4.png")
    chart(all_rows[4], "n", "Experiment 5: Sorting and top-k", "experiment_5.png")
    (DATA / "experiment_metadata.json").write_text(
        json.dumps(
            {"seed": 20261113, "repetitions": 5, "warmup": 2, "python": sys.version}, indent=2
        ),
        encoding="utf-8",
    )
    print("Experiments complete. Raw data: experiments/data; charts: experiments/charts")


if __name__ == "__main__":
    main()
