# Requirements Traceability Matrix

Source priority: the supplied `Project.pdf` is authoritative; the implementation guide adds proposed architecture and UI guidance. Status is only `VERIFIED` when the listed command or inspection has succeeded.

| Requirement | Source | Implementation | GUI entry | Verification | Status | Evidence |
|---|---|---|---|---|---|---|
| 3 playable circuits | PDF 4.1 | `services/track_loader.py`, `tracks/*.json` | Track Explorer | `python run_validation.py` | VERIFIED | 3 valid reports |
| 10 ordered checkpoints/circuit | PDF 4.1 | `Track.checkpoint_ids`, validator | Explorer/Racing | validator + race tests | VERIFIED | 10 each |
| 2 shortcuts/circuit | PDF 4.1 | Edge `is_shortcut` | Map overlay | validator | VERIFIED | 4 shortcut edges forming 2 corridors each |
| Cycle and dead end | PDF 4.1, 5.1 | distinct track graph structures | Explorer | validator/DFS | VERIFIED | all circuits; named dead-end vertices |
| 1 human + 3 deterministic AI | PDF 1, 4.4 | `RaceEngine`, `RacerStrategy` | Racing Screen | replay test/championship | VERIFIED | 4 racers |
| Main Menu | PDF 2.1 | `ui/screens.py`, `arcade_ui/app.py` | Main Menu | Pygame smoke + Arcade smoke | VERIFIED | Pygame core plus Phase 1 Arcade menu |
| Arcade Phase 1 menu | Phase 1 prompt | `arcade_ui/app.py`, `arcade_ui/session.py`, `run_arcade.py` | Arcade Main Menu | `python run_arcade.py --smoke` at 1280/1600/1920; modal/destination smoke | VERIFIED | centered seven-button menu, JSON state/settings, dialogs, focus navigation, migration bridges |
| Arcade Phase 2 Track Explorer | Phase 2 prompt + Track Explorer improvement prompt | `arcade_ui/app.py`, `route_planner.py`, `track_validator.py`, `geometry_validator.py` | Main Menu -> Track Explorer | Explorer smoke frames at requested logical 1280/1600/1920 sizes, modal smoke, route/resource/transfer tests, live closure check | VERIFIED | explicit Free Exploration/Full Race Plan modes, endpoint/checkpoint markers, arrows, zoom/pan/hover/inspection, wrapped scrollable panel, graph-vs-route validation, real counters/complexity, weighted metrics, resource planner, comparison, road-event reroute, start confirmation |
| Track Explorer | PDF 2.1 | `RoutePlanner`, interactive graph/route renderer | Main Menu -> Explorer | Pygame smoke + route/UI tests | VERIFIED | endpoint selection, arrows, metrics, comparison |
| Racing Screen | PDF 2.1 | `RaceEngine` + `arcade_ui/race_view.py` layered road/car/camera renderer | Explorer -> Start Race | race/control/sprint tests + Arcade smoke | VERIFIED | fixed-step playable race with player decisions |
| Algorithm Lab | PDF 2.1, design guide 14 | `arcade_ui/lab_view.py` plus the 12 pure algorithm families | Main Menu -> Algorithm Lab | catalog regression, algorithm suite, Arcade smoke | VERIFIED | real step/run/reset/compare/export view |
| Championship Dashboard | PDF 2.1 | scoring/ranking services | key `5` | comparator tests | VERIFIED | standings output |
| Adjacency-list graph | PDF 3.1 | `Graph._adj` | Explorer | graph unit tests | VERIFIED | O(V+E) storage |
| Dynamic edge/service state | PDF 3.1 | `Graph.set_edge_status/effects` | Race event feed | event/reroute tests | VERIFIED | shared live graph |
| Normalized non-negative cost | PDF 3.3 | `CostModel` | Explorer preset comparison | route tests | VERIFIED | 4 presets |
| Fuel rules | PDF 4.3 | race engine and rules doc | Racing HUD | race/resource tests | VERIFIED | fuel consumption |
| Nitro rules | PDF 4.3 | `Racer` nitro fields, engine activation | Racing HUD | resource/control tests | VERIFIED | manual/AI activation and expiry |
| Reachable service topology | PDF 3.1/4.1/4.3 | generated track graphs + `TrackValidator` resource checks | Explorer/Racing | `test_track_validation.py` + validator | VERIFIED | every fuel/nitro vertex has incident roads, start reachability, finish reachability |
| Complete-lap/fuel feasibility | PDF 4.2/4.3 | validator ordered-lap and `RoutePlanner.resource_plan` checks | Explorer/Racing | `test_track_validation.py` + full races | VERIFIED | start → 10 checkpoints → finish → next checkpoint is feasible on all 3 tracks |
| Player driving controls | Improvement prompt 7 | `RaceEngine` input contract + `GameApp` key loop | Racing Screen | player-control integration test | VERIFIED | throttle, brake, route selection, refuel, nitro |
| Deterministic AI policies | PDF 4.4 | `RaceEngine._choose_plan` | Racing Screen | deterministic replay | IMPLEMENTED | 3 strategy types |
| Event min-heap ordering | PDF 4.5 | `EventScheduler` | event log | event tests | VERIFIED | tuple key |
| Overlap/cancel/expiry | PDF 4.5 | independent effects/lazy cancellation | event log | event tests | VERIFIED | regression coverage |
| Championship points/ties | PDF 4.6 | `scoring.py` | Dashboard | sorting tests | VERIFIED | shared comparator |
| BFS/DFS | PDF 5.1 | `algorithms/bfs.py`, `dfs.py` | Explorer/Lab | unit tests | VERIFIED | counters |
| Dijkstra/A* | PDF 5.2 | `dijkstra.py`, `astar.py` | Explorer/Lab/race | optimal-cost tests | VERIFIED | counters |
| Checkpoint-aware route planning | PDF 5.2 | `RoutePlanner.plan_route/plan_checkpoints` | Explorer | checkpoint target/order tests | VERIFIED | ten ordered targets |
| DP/Greedy | PDF 5.3 | resource modules | Explorer/Lab | counterexample tests | VERIFIED | supplied case |
| Explorer resource planning | PDF 5.3 | `RoutePlanner.resource_plan` | Explorer | fuel/nitro route tests | VERIFIED | refuel DP + nitro DP/Greedy |
| Backtracking | PDF 5.4 | placement service | generator foundation | unit test | VERIFIED | pruning counters |
| Kruskal MST | PDF 5.4 | `mst.py` | Lab/generator foundation | unit test | VERIFIED | union-find |
| Heap/PQ | PDF 5.4/5.5 | scheduler + heap | events/top-k | event/sorting tests | VERIFIED | operations |
| Merge/Quick/Heap Sort | PDF 5.5 | `sorting.py` | Dashboard/Lab | common comparator test | VERIFIED | exact agreement |
| Five experiments | PDF 7 | `run_experiments.py` | exported data/charts | command run | VERIFIED | 5 CSV + charts |
| Automatic generation bonus | PDF 8.1 | generator foundations | not exposed as control | validator foundations | IMPLEMENTED | MST/backtracking |
| Multi-objective bonus | PDF 8.2 | cost presets | Explorer | preset comparison | VERIFIED | four presets |
| Live top-k bonus | PDF 8.3 | heap `nsmallest` top-k | Dashboard service | top-k test | VERIFIED | comparator equality |
| Responsive UI evidence | Improvement prompt 8/19, Phase 1 prompt | `tools/visual_smoke.py`, `docs/screenshots/` | all screens | real Pygame render plus Arcade smoke at 1280x720, 1600x900, 1920x1080 | VERIFIED | Pygame screenshots; latest Arcade menu, settings, instructions, circuit selection, Explorer, Racing, Lab, and Dashboard frames inspected |
| Required tests | PDF 9.1 | `tests/` | n/a | `python -m pytest -q` | VERIFIED | 42 passed |
| Technical report | PDF 9.2 | `build_report.py` | n/a | PDF render inspection | VERIFIED | 5-page report |
| Submission package | PDF 9.3 | `build_submission.ps1` | n/a | archive manifest/open | VERIFIED | ZIP generated |
| Explorer route configuration handoff | Improvement task | `GameSession.route_plan` → Racing destination | Explorer -> Racing | `test_route_configuration_transfers_from_explorer_to_race_session` + direct view smoke | VERIFIED | circuit, algorithm, preset, endpoints, path, edge IDs, metrics, fuel plan |
| Live Explorer closure reroute | Improvement task | explorer live graph + route recalculation | Explorer | blocked-edge integration test | VERIFIED | closed route edge excluded |
| Explorer geometry safety | Track Explorer improvement prompt | `services/geometry_validator.py`, authoritative circuit JSON | Explorer map load | `python -m pytest -q`, `run_validation.py` | VERIFIED | duplicate coordinates and zero-length geometry fail validation; non-connected crossings are surfaced as warnings; all three circuits pass |
| Explorer button/state audit | Track Explorer improvement prompt | `TrackExplorerView` callbacks and `GameSession.explorer_*` context | Explorer controls/modals | `docs/TRACK_EXPLORER_BUTTON_AUDIT.md` plus modal screenshots | VERIFIED | every visible control has a callback, stale-route invalidation, or documented intentional guard |

## Known scope notes

- `pygame-ce` remains available for the original five-screen baseline and regression smoke; the final user-facing client is the Arcade application using `arcade==3.3.3`.
- The Arcade menu, Explorer, Racing, Algorithm Lab, and Dashboard use the same authoritative track repository, graph, route planner, resource services, race engine, and scoring state. The earlier bridge classes remain unused compatibility code, not the active destinations.
- The final ZIP still requires actual registration numbers, section, and group names before submission.
