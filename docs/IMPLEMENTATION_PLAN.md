# Implementation Plan and Milestones

The build follows the guide's vertical-slice order.

1. **Foundation:** package layout, typed models, JSON tracks, configuration, scripts.
2. **Algorithms:** pure BFS/DFS/Dijkstra/A*/DP/Greedy/Backtracking/Kruskal/heap/sorts with counters and tests.
3. **Validated circuits:** three distinct topologies, services, checkpoints, shortcuts, cycles, dead ends, and validator.
4. **Race engine:** fixed `1/60` simulation timestep, legal edge traversal, ordered checkpoints, laps, fuel/nitro, recovery, AI.
5. **Dynamic events:** deterministic heap ordering, closures, restrictions, overlap, expiry, cancellation, reroute.
6. **Screens:** Main Menu, Explorer, Racing, Algorithm Lab, Dashboard; one authoritative race state.
7. **Championship:** official points, comparator, sorting alternatives, top-k, championship output.
8. **Experiments:** five headless studies, raw CSV, charts, metadata.
9. **QA/release:** tests, lint, compile, visual smoke, report, clean ZIP and manifest.

## Current exit gates

- Foundation: passed.
- Algorithms: passed.
- Circuit validation: passed for all three circuits.
- Headless race/championship: passed.
- Five-screen render smoke: passed.
- Experiments/report/package: passed in previous release audit; rerun after topology/timestep changes before final packaging.
