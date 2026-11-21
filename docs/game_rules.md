# Frozen Game Rules and Assumptions

These values are frozen for the implementation and experiments.

- 3 circuits, 2 laps per circuit, 10 mandatory ordered checkpoints per circuit.
- 1 human racer and 3 deterministic computer opponents.
- Maximum fuel: 100 units; initial fuel: 100.
- Fuel per edge: `fuelCost * (1 + 0.1 * (difficulty - 1))`.
- Fuel station purchase cap: 40 units; positive purchase stop time: 3 seconds.
- Maximum nitro: 3 charges; nitro gives 1.5x speed for the affected edge and doubles its fuel use.
- Race time limit: 600 seconds. Unfinished racers receive no finish-position points.
- Unfinished ranking: completed laps descending, checkpoints completed descending, elapsed time ascending, racer ID ascending.
- Finished ties: lower racer ID wins.
- Event heap key: `(triggerTime, priority, insertionSequence)` ascending.
- Recovery: recalculate immediately. If no route exists, wait for a scheduled reopen; if no reopen exists and the race cannot finish, mark DNF rather than freezing.
- No bonus points are used.
- All randomness is seeded and saved in experiment metadata.

## Cost normalization

The scalar route cost is:

```text
cost = wd*(distance/10) + wt*(effective_time/10)
     + wf*(effective_fuel/10) + wr*(difficulty/5)
     + wo*(obstacle_penalty/5)
```

All weights are non-negative. The four presets are Balanced, Speed, Economy, and Safety. The same `CostModel` is used by the Route Planner, race engine, and Algorithm Lab.

## Opponent strategies

1. Navigator: fixed planner route, deterministic reroute, first eligible station below 25% fuel.
2. Shortcut: uses an open shortcut when legal and falls back to a normal route if it closes.
3. Distance: chooses the available route with the minimum distance and selects the nearest reachable station below 25% fuel.

## DP fuel discretization

The refuelling DP uses one-unit discrete fuel states. This keeps the tank capacity at 101 states and makes the state-space size explicit. The live engine uses floating-point fuel for travel, while the planner rounds its input to integer planning units and performs a final feasibility check before applying a plan.
