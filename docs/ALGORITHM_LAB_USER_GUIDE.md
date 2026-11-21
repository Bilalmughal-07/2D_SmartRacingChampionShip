# Algorithm Lab User Guide

The Algorithm Lab is the educational analysis screen in the Arcade client. It runs the same pure algorithm implementations used by Track Explorer, resource planning, event scheduling, track generation, and the championship dashboard.

## Navigation

- Open `Algorithm Lab` from the main menu.
- Use the five category buttons to switch between Graph & Routing, Optimization, Track Design, Events & Heaps, and Sorting.
- Select a circuit with the circuit button in the top-right. This changes the lab dataset only; it does not change the active championship circuit or race plan.
- Use `SOURCE`, `TARGET`, and `EXAMPLE INPUT` to change graph inputs.
- Press `BACK` or `Esc` to return to the screen that opened the lab.

## Playback

`PREV` and `NEXT` move through recorded operations. `RUN` animates the trace and becomes `PAUSE` while it is running. `RESET` returns to step zero. The speed button cycles through 0.5×, 1×, 2×, and 4×. The timeline is clickable and seeks directly to a recorded step. Arrow keys move between steps, `Space` toggles playback, and `Enter` toggles playback.

The lower strip switches between `STEP EXPLANATION` and `PSEUDOCODE`. The inspector reports the current data structure, counters, result, and asymptotic complexity. `HELP` explains the selected algorithm's purpose and gameplay role.

## Visualizations and algorithms

| Category | Algorithms | Live visualization |
|---|---|---|
| Graph & Routing | BFS, DFS, Dijkstra, A* | Circuit vertices/edges, frontier state, visited vertices, route path, and weighted cost |
| Optimization | 0/1 Knapsack DP, Refuelling DP, Greedy | DP capacity table, resource states, benefit/cost bars, and feasibility information |
| Track Design | Backtracking, Kruskal MST | Placement decisions, pruning, candidate edges, accepted MST edges, and cycle rejection |
| Events & Heaps | Event Min-Heap | Binary heap tree, heap array, deterministic event key, insertion, and extraction |
| Sorting | Merge Sort, Quick Sort, Heap Sort | Championship racer bars, comparator order, partition/merge/extraction operations |

The assignment defines 12 algorithm families. Refuelling DP is shown as an additional resource-planning extension because the project requirements explicitly require fuel feasibility and refuelling-stop planning.

## Analysis actions

- `COMPARE` runs a fresh comparison using the appropriate production algorithms for the current category.
- `EXPERIMENT` performs five fresh executions and reports mean, minimum, and maximum time in milliseconds.
- `EXPORT` writes the selected algorithm, inputs, trace, result, comparison, and experiment data to `data/arcade_lab_export.json`.

Results are calculated from the current repository implementation. The UI does not use illustrative placeholder paths, fabricated counters, or disconnected demo graphs.

## Manual comparison workspace

The Compare screen lets you choose Algorithm 1 and Algorithm 2 independently. Supported pair categories are:

- Graph Traversal: BFS and DFS.
- Weighted Routing: Dijkstra and A*.
- Resource Optimization: 0/1 Knapsack DP and Greedy.
- Championship Sorting: any two of Merge Sort, Quick Sort, and Heap Sort.

The screen rejects missing, duplicate, and incompatible selections. Both sides receive isolated copies of the same circuit graph or dataset, with the same source, destination, cost strategy, event scenario, graph revision, comparator, and tie-breaking rules. Reverse ordering is valid and remains visible left-to-right.

After `RUN COMPARISON`, use the synchronized playback controls to advance both traces. If one trace finishes earlier, its completed state remains visible while the other continues. The results area reports only metrics relevant to the selected category and generates a conclusion from the measured outputs. `EXPORT` writes the full comparison, input fingerprint, trace data, counters, timing method, and conclusion to `data/arcade_lab_comparison.json`.
