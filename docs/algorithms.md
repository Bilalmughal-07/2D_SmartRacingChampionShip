# Algorithm Design and Integration

| Algorithm | Gameplay/Lab role | Complexity |
|---|---|---|
| BFS | Reachability and minimum-edge path in Track Explorer | `O(V+E)` time, `O(V)` space |
| DFS | Traversal, cycle/component/dead-end analysis, bounded alternatives | `O(V+E)` traversal; bounded path enumeration can be exponential |
| Dijkstra | Weighted route optimization with non-negative scalar costs | `O((V+E) log V)` |
| A* | Heuristic-guided weighted route optimization | Worst case comparable to Dijkstra |
| Dynamic programming | 0/1 pickup knapsack and discrete refuelling plan | `O(mB)` knapsack; refuelling `O(mC^2)` straightforward |
| Greedy | Benefit/cost pickup heuristic | `O(m log m)` |
| Backtracking | Constraint-based service/obstacle placement | Exponential worst case with pruning |
| Kruskal | Undirected MST backbone for track generation | `O(E log E)` |
| Min-heap | Event scheduling and top-k retrieval | `O(log n)` update/extract |
| Merge Sort | Primary championship ranking | `O(n log n)` |
| Quick Sort | Alternative ranking | Average `O(n log n)`, worst `O(n^2)` |
| Heap Sort | Third ranking method | `O(n log n)` |

The Algorithm Lab calls the same service implementations as gameplay. Dijkstra and A* return counters for expanded vertices, relaxed edges, heap operations, final path cost, and elapsed time. The A* implementation uses a caller-supplied admissible heuristic; the route planner supplies a straight-line lower bound multiplied by the minimum observed cost-per-distance ratio, or zero when no positive lower bound is valid.

All championship methods use the same total order: higher points, higher wins, lower sum of finishing positions, lower best fastest-lap time, then lower racer ID.
