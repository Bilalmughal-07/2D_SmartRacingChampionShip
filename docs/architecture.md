# Architecture and State Ownership

## Layers

1. **Models:** vertices, edges, graph, track, racer, event, results, championship entries.
2. **Algorithms:** pure Python, no Pygame imports, deterministic tie-breaking, counters.
3. **Services:** route cost/planning, validation, event scheduler, race engine, scoring, analytics.
4. **Presentation:** compact Pygame screen manager and map/HUD renderers.

## Authoritative state

`RaceEngine` owns `RaceState`, racer state, scheduler, and a deep-copied live graph. The planner points at that exact graph object, so events mutate the state that route calculations read. The UI renders snapshots and dispatches controls; it does not implement routing, checkpoint, fuel, or scoring rules.

## Determinism

- Track generation is seed-indexed and exported to JSON.
- Neighbours, heaps, path ties, event order, and rankings use stable IDs.
- `GameConfig.fixed_timestep` is `1/60` second.
- A new race deep-copies the base track graph, preventing pickup/service state leakage.
- Headless race replay produces equal finish order and times.

## Data flow

```text
JSON Track -> Validator -> Graph snapshot -> RoutePlanner / RaceEngine
                                               -> fixed-step snapshots -> Pygame UI
Events -> EventScheduler -> live graph effects -> reroute
Results -> Scoring comparator -> sort/top-k -> dashboard/CSV/report
```
