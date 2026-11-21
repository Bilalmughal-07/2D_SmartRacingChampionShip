# Verification Matrix

The project uses deterministic tests plus real Arcade/Pygame smoke captures. A feature is marked verified only after the implementation, automated test, and relevant screenshot or command evidence are available.

| Area | Automated evidence | Visual/command evidence | Current target |
|---|---|---|---|
| Circuit topology | `tests/unit/test_track_validation.py`, `run_validation.py` | Three circuit validation reports | Pass |
| Ordered route planning | `tests/unit/test_route_planner.py` | Explorer route overlay captures | Pass |
| Closures and rerouting | `tests/integration/test_ui_smoke.py`, race tests | Explorer blocked-edge capture | Pass |
| Fuel and nitro | `tests/unit/test_route_planner.py`, `tests/integration/test_race.py` | Racing HUD capture | Pass |
| Main Menu | `tests/unit/test_arcade_frontend.py` | Arcade 1280/1600/1920 captures | Pass |
| Track Explorer | route/session, geometry, comparison-card, road-event, NEXT ROAD, and Explorer integration tests | `arcade_explorer_overhaul_1280.png`, `_1600.png`, `_1920.png`, `arcade_explorer_events_1280.png`, `arcade_explorer_events_next_1280.png`, `_1440.png`, `_1600.png`, responsive comparison/resources/start-confirmation captures | Pass |
| Racing Screen | race replay/control/sprint tests; exact transferred-path and all-circuits/both-modes planned-route test | `planned_race_roads_1280.png`, `arcade_race_quick_modes_1280.png` | Pass |
| Algorithm Lab | catalog/session tests, comparison-selection tests, trace-hook tests, algorithm unit suite, direct 13-entry × 3-circuit and four-category comparison audit | `algorithm_lab_1280.png`, `algorithm_lab_1600.png`, `algorithm_lab_1920.png`, graph/DP/heap/sorting captures, `algorithm_comparison_weighted_1280.png` | Pass |
| Championship Dashboard | scoring/championship tests | `arcade_dashboard_1280.png` | Pass |
| Quick Race setup/results | route-gate, configuration, no-point-mutation, and all-circuits planned-path tests | `quick_setup_route_gate_1280.png`, `quick_results_centered_1280.png`, `quick_results_centered_1600.png` | Pass |
| Championship lifecycle | route-gated round persistence, duplicate-safe scoring, and three-round simulation | `championship_dashboard_route_flow_1280.png`, `championship_results_1280.png` | Pass |
| Release path | build scripts and clean extraction smoke | report, executable, ZIP manifest | Re-run after final edits |

## Required smoke commands

```powershell
python -m pytest -q
python -m ruff check .
python run_validation.py
python run_game.py --headless --track circuit_01
python run_championship.py
python run_experiments.py
python build_report.py
python run_arcade.py --smoke --screen menu --width 1280 --height 720 --output docs/screenshots/arcade_menu_1280.png
python run_arcade.py --smoke --screen explorer --width 1280 --height 720 --output docs/screenshots/arcade_explorer_1280.png
python run_arcade.py --smoke --screen race --width 1280 --height 720 --output docs/screenshots/arcade_race_1280.png
python run_arcade.py --smoke --screen lab --width 1280 --height 720 --output docs/screenshots/arcade_lab_1280.png
python run_arcade.py --smoke --screen dashboard --width 1280 --height 720 --output docs/screenshots/arcade_dashboard_1280.png
python run_arcade.py --smoke --screen quick_setup --width 1280 --height 720 --output docs/screenshots/quick_setup_1280.png
python run_arcade.py --smoke --screen championship_results --width 1280 --height 720 --output docs/screenshots/championship_results_1280.png
```

The Arcade smoke backend may report a higher physical framebuffer on Windows display scaling; the logical window size remains the requested size and the image is inspected at the actual captured dimensions.
