# Experimental Studies

`run_experiments.py` performs five warmed-up timing repetitions on deterministic inputs and writes raw CSV data under `experiments/data/` and charts under `experiments/charts/`.

1. BFS/DFS: graph size, sparse/extra edges, runtime, visited vertices, examined edges.
2. Dijkstra/A*: circuit graphs, runtime, expanded vertices, relaxed edges, heap operations, final cost.
3. DP/Greedy: item count and budget, runtime, benefit, selected items, DP state count, plus small-instance correctness checks in tests.
4. Event heap: event count, insertion/extraction timing, heap operations, deterministic ordering/cancellation coverage.
5. Sorting/top-k: input size, runtime for Merge/Quick/Heap Sort and size-k heap retrieval.

Rendering and file I/O are outside timed functions. The experiment metadata stores the seed, warm-up count, repetition count, and Python version.
