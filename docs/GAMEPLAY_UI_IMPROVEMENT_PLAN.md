# Gameplay and UI Improvement Plan

## Audit summary

The existing project already has the required graph, routing algorithms, event heap, fixed-step race engine, checkpoints, fuel/nitro state, three validated tracks, five screens, experiments, tests, and release packaging. The authoritative state boundary is sound: `RaceEngine` owns the live graph snapshot and racer state, while `GameApp` renders that state.

The main deficiencies are presentation and player interaction:

- The racing view renders graph edges, vertices, and colored circles instead of roads, cars, gates, and an environment.
- Racer positions are shown only at the last reached vertex; the engine has edge progress but the UI does not interpolate it.
- The player currently receives keyboard hints but throttle, braking, junction choice, and manual refuelling are not part of the simulation contract.
- The race layout gives the sidebar more visual weight than the track and has no camera, minimap, speedometer, or resource gauges.
- Checkpoints, services, nitro, closures, oil, and speed restrictions are present in state but lack clear world-space visual treatment.
- The explorer and lab share the map renderer but do not yet share the richer road/environment language of the race view.
- UI smoke coverage exists, but gameplay regression needs explicit checks for interpolation, input effects, resource requests, and responsive 1280x720 rendering.

## Design and architecture decisions

1. Keep graph topology, edge cost, event status, route planning, checkpoint ordering, fuel rules, and scoring in models/services.
2. Add a small input contract to `RaceEngine` for throttle, brake, junction exit cycling, manual route confirmation, refuelling, and nitro. The engine remains authoritative; the renderer only dispatches input and draws state.
3. Derive every car world position from `current_vertex`, `current_path`, and `edge_progress`. No renderer-created path or shortcut may affect simulation.
4. Use straight, wide, layered road geometry because the live movement model traverses straight graph edges. Rounded endpoints, shoulders, dashed centerlines, junction patches, barriers, signs, gates, and themed scenery improve readability without inventing connections.
5. Add a presentation-only camera that follows the player and a separate full-track minimap transform.
6. Render procedural car sprites and world markers with Pygame primitives; do not add unavailable external assets.
7. Keep the five-screen navigation contract and existing DAA algorithm implementations intact.

## Implementation priorities

### P0 — Gameplay contract

- Add player throttle/brake state and deterministic speed modifiers.
- Add valid outgoing-road selection at intersections and route confirmation.
- Add manual refuel request with station eligibility checks.
- Add public race-pose helpers or stable UI derivation for interpolation.

Acceptance: the player can accelerate, brake, choose a valid outgoing edge, confirm it, request a station refuel, activate nitro, and never select a blocked/nonexistent edge.

### P0 — Racing presentation

- Replace thin graph lines with layered asphalt roads, shoulders, lane markings, shortcut styling, closures, restrictions, and junction blends.
- Add themed grass/canyon/metro terrain, procedural scenery, checkpoint gates, service stations, nitro pickups, and event signs.
- Add four oriented car sprites with controlled overlap offsets and nitro/brake/refuel effects.
- Add camera follow, world transforms, minimap, top HUD, compact standings, event feed, speedometer, fuel, nitro, lap, and checkpoint panels.

Acceptance: roads read as roads, cars read as cars, all cars remain aligned to their graph edge, the track is the visual focus, and no critical clipping occurs at 1440x900 or 1280x720.

### P1 — Other screens

- Reuse the road/environment renderer in menu and explorer.
- Make Algorithm Lab step playback visibly highlight the current expanded/relaxed graph item.
- Improve dashboard standings, race history, and champion emphasis without changing scoring.

Acceptance: every screen remains navigable by keyboard and mouse and the same design tokens are used throughout.

### P1 — QA and evidence

- Add deterministic tests for player controls, edge interpolation, blocked-exit rejection, refuel requests, nitro expiry, event state, and responsive layouts.
- Render real application screens at 1440x900 and 1280x720 using the existing Pygame smoke harness.
- Run validation, unit/integration tests, experiments, report generation, executable launch, and clean archive inspection.
- Update traceability, progress, status, and the defect log.

## Affected modules

| Area | Modules |
|---|---|
| Simulation input | `model/race.py`, `services/race_engine.py` |
| Rendering and controls | `ui/screens.py` |
| Verification | `tests/integration/test_race.py`, `tests/integration/test_ui_smoke.py`, new gameplay/UI tests |
| Evidence | `tools/visual_smoke.py`, `docs/screenshots/` |
| Release records | `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/PROGRESS.md`, `docs/status.md` |

## Acceptance test matrix

- Three tracks validate and have distinct themes/topologies.
- Four racers complete deterministic races or are correctly ranked as DNF.
- A race replay produces the same results twice.
- Player throttle changes travel time; braking slows travel; nitro expires at the configured duration.
- Junction input accepts only open graph neighbors and route confirmation uses the selected edge.
- Refuelling changes fuel only at an active fuel station and applies the configured stop time.
- Checkpoints advance only in required order; laps and finish state remain authoritative.
- Road events mutate the live graph used by route planning and are visible in the renderer.
- All five screens draw at 1440x900 and 1280x720 without exceptions or critical clipping.
- Experiments, report generation, executable build/launch, and submission ZIP inspection remain green.

## Defect log

| ID | Defect | Resolution |
|---|---|---|
| UI-001 | Racing view exposed graph internals instead of a playable track | Addressed by layered road/environment renderer and camera HUD work |
| GAME-001 | Player keyboard commands did not affect simulation movement or route choice | Addressed by the engine input contract |
| QA-001 | Visual smoke covered one target size only | Addressed by dual-size screenshot smoke |

