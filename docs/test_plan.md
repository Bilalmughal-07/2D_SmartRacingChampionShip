# Test Plan and Evidence

## Commands

```powershell
python -m pytest
python -m ruff check --ignore E501 src tests run_*.py build_report.py
python -m compileall -q src run_*.py build_report.py
python run_validation.py
python run_championship.py
python run_experiments.py
```

## Coverage matrix

- Graph: single, disconnected, cyclic, branching, dead-end, directed/undirected.
- Routing: source=target, unreachable, blocked, equal-cost, zero-weight, live changes.
- Resources: insufficient/exact/full fuel, unavailable station, capacity, zero-cost pickup, infeasible plan.
- Events: simultaneous, priority/sequence ties, cancellation, expiration, missing target, overlapping effects.
- Sorting: empty/singleton-compatible paths, random, sorted, reverse, duplicate-heavy, final ID tie.
- Integration: complete race, replay, multiple laps, ordered checkpoints, road blockage, championship standings.
- Visual: all five Pygame baseline screens rendered on a dummy display at 1100x720 and the final Arcade menu, Explorer, Racing, Lab, and Dashboard captured and inspected at the supported logical sizes.

## Regression history

- Track JSON type/status double-conversion fixed in loader.
- Race graph state leakage fixed with deep-copy per race.
- Fixed-timestep closure test updated to advance simulation seconds explicitly.
- Route planning cached while an edge is mid-traversal, reducing repeated searches.
- Distinct topology generation added for all three circuits.
- Final Arcade views replaced bridge destinations; title bars, navigation, and dashboard footer were visually rechecked after layout fixes.
- Final regression count: 39 passed.
