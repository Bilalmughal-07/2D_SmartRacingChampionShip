# Progress Record

## Current status

Status: `COMPLETE` for the expanded gameplay/UI and release gates in the current environment; the original assignment core and final Arcade game path are verified.

## Arcade Phase 1 (2026-11-21)

- Added an isolated Python 3.12+ Arcade 3.3.3 front end without Pygame imports in the new UI package.
- Added a generated original `assets/backgrounds/racing_battle.png` hero image with a dark readability overlay and responsive centered title/menu composition.
- Added `run_arcade.py`, JSON-backed `GameSession`, responsive seven-button navigation, keyboard focus, modal How-to-Play/Settings/Exit/Championship flows, real settings sliders/toggles, quick-race circuit selection, and shared Explorer/Lab/Racing destinations.
- Verified actual Arcade smoke frames at 1280x720, 1600x900, and 1920x1080, plus settings, instructions, circuit selection, Explorer, Racing, Algorithm Lab, and Dashboard states. Fixed title overlap, modal draw order, missing Track field name, clipped labels, and smoke-window shutdown ordering.

## Arcade Phase 2 — Track Explorer and Route Planner (2026-11-21)

- Replaced the temporary Explorer bridge with an interactive authoritative graph explorer using the same `Track`, `Graph`, `RoutePlanner`, DP/Greedy resource modules, and validation services as the race system.
- Added circuit switching, championship lock behavior, click-selected source/destination markers, checkpoint-aware routing, BFS/DFS/Dijkstra/A* controls, weighted cost presets, complexity/counter reporting, exact distance/time/fuel/risk metrics, fuel feasibility and refuelling stops, nitro DP/Greedy status, and four-preset comparison.
- Added map zoom, pan, hover inspection, directional arrows, shortcut/status overlays, environmental circuit styling, a complete legend, wrapped planning text, and an interactive road-event split-screen workspace that reroutes on the Explorer-only graph overlay.
- Added route configuration persistence and handoff into the Racing destination, with race start blocked unless the circuit validates, all checkpoints are enabled, the source is the official start, and the resource plan is feasible.
- Added Phase 2 regression coverage for every algorithm on every circuit, A*/Dijkstra weighted-cost agreement, source-equals-destination handling, route persistence/handoff, stale-route clearing during quick-circuit switching, and the UI A* service-key alias.
- Inspected actual Explorer smoke frames after implementation and fixes at requested logical 1280x720, 1600x900, and 1920x1080 sizes. Windows display scaling stores the captures at 1600x900, 2000x1125, and 2400x1350 physical pixels respectively; the responsive layout was inspected at each logical target. Modal captures cover comparison, resources, road events, and start confirmation.

## Verified in this session

- Read the implementation guide and audited the repository.
- Redesigned all three authoritative tracks as recognizable oval, canyon-switchback, and urban street-circuit topologies.
- Fuel and nitro nodes are now embedded in two-sided service/racing road segments instead of dangling remote markers.
- All tracks pass validation with 10 checkpoints and 2 shortcut corridors (4 shortcut edges) each; their vertex/edge signatures differ.
- Track validation now enforces resource reachability, non-dead-end service nodes, complete-lap return, and fuel feasibility.
- Race engine now uses `GameConfig.fixed_timestep = 1/60` and caches a route during edge traversal.
- Race engine now accepts deterministic player throttle, brake, junction-exit, refuel, and nitro requests without allowing invalid graph edges.
- Track Explorer now supports selectable start/destination vertices, checkpoint-aware planning, weighted route arrows, map zoom/pan/hover, wrapped descriptions, algorithm complexity/counters, exact physical metrics, fuel DP, nitro DP/Greedy recommendations, four-preset comparison, and live closure rerouting.
- Existing algorithm, race, event, sorting, UI, championship, player-control, nitro, route-planner, track-validation, AI fuel, Explorer integration, geometry, comparison-card, road-event-preview, NEXT ROAD, and Arcade session tests are green (47 passed).
- Pygame visual smoke renders all five screens at 1440x900 and 1280x720 plus one Explorer screenshot for each redesigned circuit; the racing screen now shows layered roads, procedural cars, themed scenery, gates, services, pickups, camera follow, minimap, gauges, standings, and event state.
- All three circuits complete full deterministic races and a full championship after the redesign.
- Experiments and technical report were regenerated after the gameplay/UI changes.
- PyInstaller onedir build launches successfully from a clean copied extraction.

## Arcade Phase 3–5 — Final playable client (2026-11-21)

- Replaced the Arcade race, lab, and dashboard bridge destinations with real views backed by `RaceEngine`, the shared algorithm modules, `GameSession`, and scoring services.
- Racing now has fixed-step updates, legal graph-edge movement, player speed/brake/fork/refuel/nitro/sprint decisions, camera modes, minimap, closures, live event feed, race results, and session persistence.
- Algorithm Lab exposes all 12 required algorithm families with real execution, traces or result summaries, step/run/reset/compare/export controls, complexity, and gameplay usage labels.
- Championship Dashboard loads persistent standings without hidden preview races, supports Merge/Quick/Heap ranking, Top-3/Top-4 views, next-round continuation, podium, reset confirmation, and shared scoring data.
- Added CI workflow, release-oriented `.gitignore`, verification matrix, sprint/race handoff regression, 12-family catalog regression, and duplicate-safe championship persistence regression.
- Rechecked actual Arcade captures after fixing header navigation collisions and dashboard footer overlap. Latest captures: `arcade_race_1280.png`, `arcade_lab_1280.png`, and `arcade_dashboard_1280.png`.
- Phase checkpoint verification: 39 tests passed; Ruff and compile checks passed; all three circuits validated; championship replay, five experiments, and technical report regenerated successfully. The later Algorithm Lab overhaul raised the current suite to 47 tests.

## Algorithm Lab overhaul (2026-11-21)

- Rebuilt `arcade_ui/lab_view.py` as a responsive, production-backed learning workspace with five category tabs: Graph & Routing, Optimization, Track Design, Events & Heaps, and Sorting.
- Added real trace playback for BFS, DFS, Dijkstra, A*, 0/1 Knapsack DP, Refuelling DP, Greedy, Backtracking, Kruskal MST, Event Min-Heap, Merge Sort, Quick Sort, and Heap Sort. Refuelling DP is retained as the resource-planning extension to the 12 assignment families.
- Added per-algorithm visualizations: live circuit graph, DP table, greedy benefit bars, binary heap tree/array, and championship ranking bars; every view exposes current state, counters, complexity, pseudocode, step explanation, and gameplay role.
- Added responsive circuit/source/target/example controls, Previous/Next, Run/Pause, Reset, speed cycling, timeline seeking, compare, experiment, JSON export, help, keyboard navigation, and Back context restoration.
- Added optional trace hooks to DFS, Backtracking, Kruskal MST, and Merge/Quick/Heap Sort while preserving their existing pure APIs and results.
- Visual evidence inspected: `algorithm_lab_1280.png`, `algorithm_lab_1600.png`, `algorithm_lab_1920.png`, plus graph/DP/heap/sorting category captures. Logical 1280×720, 1600×900, and 1920×1080 layouts remain readable under Windows display scaling.
- Verification after the overhaul: 47 tests passed, Ruff passed, all algorithm/circuit combinations executed without errors, and playback/compare/experiment controls completed successfully.

## Manual two-algorithm comparison (2026-11-21)

- Added `AlgorithmComparisonView`, opened by the main Lab `COMPARE` action, with independent Algorithm 1 and Algorithm 2 selectors. The left/right order is preserved and no comparison partner is substituted automatically.
- Supported pair categories are Graph Traversal (BFS/DFS), Weighted Routing (Dijkstra/A*), Resource Optimization (0/1 Knapsack DP/Greedy), and Championship Sorting (any two of Merge/Quick/Heap Sort). MST, Backtracking, and Event Min-Heap remain standalone demonstrations because a second production partner is not implemented for them.
- Added shared circuit/source/target/cost/event-revision/budget controls, validation for missing/same/incompatible selections, isolated graph snapshots, actual per-side traces, synchronized playback, independent trace lengths, step explanations, pseudocode, metrics, computed conclusions, and JSON export.
- Visual evidence inspected in `docs/screenshots/algorithm_comparison_weighted_1280.png`; the equal-weight side-by-side workspace is readable at the 1280×720 target and retains the dark racing telemetry theme.
- Comparison audit: all four categories executed, reverse sorting order produced the same ranking, invalid pairs were rejected, stale results were cleared, and playback/reset/export paths were exercised.

## Quick Race and Championship modes (2026-11-21)

- Added a standalone Quick Race setup with circuit switching, 1/2/3/5 lap selection, Easy/Normal/Hard deterministic AI, road-event toggle, and Balanced/Speed/Economy/Safety routing selection.
- Quick Race launches `ArcadeRacingView` with the saved setup and a unique race ID, records a dedicated results report with time, fastest lap, fuel used, nitro use, events, and status, and never mutates championship points.
- Reworked Championship Dashboard into a real persistent season state: not started, in progress, awaiting next round, and completed. It starts/continues/resets a three-round season, launches the next circuit, records each result exactly once, and opens round/final result views.
- Extended `RaceEngine` with configurable laps, event enable/disable, AI difficulty multipliers, race metadata, and resource telemetry while preserving the shared graph, checkpoint, event-heap, and scoring implementations.
- Added responsive Arcade smoke captures for Quick Race setup and Championship Dashboard at 1280x720 and 1600x900, inspected after fixing header and control-panel overlap. Quick Results also has a verified empty-state report for a fresh session.
- Verification after this phase: 50 tests passed, Ruff passed, compile checks passed, `run_validation.py` passed for all three circuits, three one-lap Quick Race engine smokes completed without DNF, and a three-round championship session completed with points and tie-break data persisted.

## Mandatory route gate and race presentation (2026-11-21)

- Quick Race now follows `Select Circuit → Track Explorer → Plan Route → Start Race → Race Results`; its setup action is `PLAN ROUTE`, and it cannot instantiate a live race before Explorer confirmation.
- Championship rounds now return to Track Explorer for every scheduled circuit. Each round requires a fresh route, ordered checkpoints, open-road connectivity, fuel feasibility, and accepted resource plan before the race can start.
- Added pure `race_route_validation.py` checks for route freshness, source/finish, graph connections, blocked roads, checkpoint order, fuel feasibility, and resource acceptance. Invalid plans stay in route planning with a clear error.
- The confirmed Explorer path is transferred as `player_path`, ordered checkpoints, selected algorithm, strategy, edge IDs, blocked-road state, metrics, and resource plan. Human movement follows those exact planned edges; AI route planning uses the selected strategy preset.
- Replaced thin Racing View graph strokes and triangle cars with layered asphalt shoulders, consistent road surfaces, dashed lane markings, shortcut markings, intersection pads, directed arrows, and stylized 2D racing cars while retaining the graph as the authoritative gameplay model.
- Reworked race results into a centered, padded report panel with aligned columns and centered bottom actions. Quick results expose Retry, Change Circuit, and Main Menu; championship results expose standings and next-round/final navigation without duplicate scoring.
- Visual evidence inspected: `quick_setup_route_gate_1280.png`, `route_planner_gate_1280.png`, `planned_race_roads_1280.png`, `quick_results_centered_1280.png`, and `championship_dashboard_route_flow_1280.png`.
- Verification after this phase: 55 tests passed, Ruff passed, all three circuits completed planned-path races in both Quick and Championship modes, and all validation reports remained valid.

## Shared start/finish lap boundary fix (2026-11-21)

- Updated the authoritative generator and JSON tracks so each circuit's finish vertex occupies the exact same world coordinate as its start vertex. The graph IDs remain distinct so the finish still acts as the lap boundary for ordered routing.
- Added an intentional timing-line exception to geometry validation for the colocated start/finish pair and its zero-length graph boundary edge; all unrelated duplicate coordinates and zero-length roads remain validation errors.
- Fixed `RaceEngine` to move every racer back to `start_id` after a completed non-final lap. The transferred Explorer `player_path` therefore restarts at route index 0 instead of waiting at `finish_id`.
- Added regression coverage for shared coordinates and two-lap transferred-route completion on all three circuits. The player now finishes with 30 completed checkpoint events and no DNF in the default two-lap race.
- Verification after this fix: 57 tests passed, Ruff passed, compile checks passed, `run_validation.py`, headless race, full championship simulation, and Arcade visual smoke all passed. Explorer, racing, and results screenshots were inspected after the fix.

## Next actions

1. Rebuild the final ZIP after replacing the placeholder registration numbers and section.
2. Fill actual group member names and registration numbers on the report title page.
3. Review and merge the stacked GitHub PRs in order if desired: core, Arcade, then QA/release.

## Free exploration, AI policies, and championship lap configuration (2026-11-22)

- Added two explicit route modes. Free Exploration accepts an arbitrary source and destination, computes the selected algorithm/strategy/resource plan, and launches a one-lap race on that exact route. Full Race Plan keeps one colocated physical start/finish timing line, requires all ten checkpoints in order, and uses the configured lap count.
- Added a persistent Championship Dashboard lap selector for 1/2/3/5 laps. The selected value is asked before a new season, applied to every round, persisted in the session file, and locked while an active season is in progress.
- Completed the four-racer policy split on the shared fixed-step engine: Navigator follows its deterministic main route/detour policy, Shortcut prefers legal shortcuts without immediate U-turn oscillation, Distance recomputes shortest-distance legal paths, and Player follows the transferred Explorer route until a confirmed A/D alternative or live event reroute.
- Added runtime route recovery for blocked planned roads, relative left/right exit selection, live planned-blue versus reroute-white route state, deterministic seeded road events, shared fuel/nitro/checkpoint rules, and resource-aware AI detours.
- Added optional procedural menu and championship themes controlled by separate Settings toggles and music volume; audio failures remain non-fatal in headless smoke runs.
- Verified actual 1280×720 Arcade settings, dashboard, Explorer, and Racing frames after the layout fix. The settings labels and volume rows no longer overlap the controls.
- Verification after this phase: 62 tests passed, Ruff passed, compile checks passed, all three circuits completed with four finishers with and without seeded events, `run_validation.py` passed, and free-route one-lap launch plus blocked-route recovery were covered by regression tests.

## Buffered intersection controls (2026-11-22)

- Fixed player A/D route selection so input made while approaching a junction targets the upcoming vertex instead of the previous vertex.
- Confirmed choices are now buffered through edge arrival, remain visible in the HUD, and are consumed only when the car reaches the selected junction. The selected road then becomes the first edge of the live route and triggers the blue/white reroute presentation when it differs from the plan.
- Added an all-circuit regression test for selection persistence and confirmed-road execution. Verification now totals 63 passing tests with Ruff still clean.

## Race route presentation and no-reverse junction choices (2026-11-22)

- Excluded the incoming road from the player's A/D exit list, including the first junction where the incoming vertex is inferred from the active edge. Enter can no longer select the road the car is currently travelling away from.
- Removed planned and rerouted path strokes from the large race map. Planned blue and recalculated white guidance now render only on the minimap, while the large view remains focused on asphalt, intersections, events, and cars.
- Inspected the updated 1280×720 Racing smoke frame and verified the large map has no route overlay while the minimap retains the guidance legend.

## External inputs still required

- Actual registration numbers, section, and group names.
- Optional human playtest feedback on controls and screen polish.
