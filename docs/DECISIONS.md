# Engineering Decisions

| Decision | Reason | Trade-off |
|---|---|---|
| Python + pygame-ce | readable algorithms and lightweight 2D desktop UI | requires dependency install |
| Custom adjacency list | explicit assignment requirement and sparse graph efficiency | more code than NetworkX |
| Kruskal for MST | easy deterministic union-find integration | generator remains simpler than a full editor |
| JSON tracks | inspectable, deterministic, easy to package | no live authoring tool |
| Fixed `1/60` timestep | simulation independent from renderer FPS | more headless ticks |
| Per-race graph deep copy | prevents pickup/effect state leakage | small copy cost per race |
| No bonus points | removes ambiguity before benchmarks | no optional scoring layer |
| Wait then DNF recovery | deterministic and prevents silent freezes | cannot guarantee a finish after permanent disconnection |
| Pygame dummy smoke test | enables visual regression in headless environments | not a substitute for human playtest |
