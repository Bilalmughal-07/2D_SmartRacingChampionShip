# Verification Matrix

The project uses deterministic tests plus real Arcade/Pygame smoke captures. A feature is marked verified only after the implementation, automated test, and relevant screenshot or command evidence are available.

| Area | Automated evidence | Visual/command evidence | Current target |
|---|---|---|---|
| Circuit topology | `tests/unit/test_track_validation.py`, `run_validation.py` | Three circuit validation reports | Pass |
| Ordered route planning | `tests/unit/test_route_planner.py` | Explorer route overlay captures | Pass |
| Closures and rerouting | `tests/integration/test_ui_smoke.py`, race tests | Explorer blocked-edge capture | Pass |
| Fuel and nitro | `tests/unit/test_route_planner.py`, `tests/integration/test_race.py` | Racing HUD capture | Pass |
| Main Menu | `tests/unit/test_arcade_frontend.py` | Arcade 1280/1600/1920 captures | Pass |
| Track Explorer | route/session tests | `arcade_explorer_1280.png` and circuit captures | Pass |
| Racing Screen | race replay/control/sprint tests | `arcade_race_1280.png` | Pass |
| Algorithm Lab | catalog/session tests and algorithm unit suite | `arcade_lab_1280.png` | Pass |
| Championship Dashboard | scoring/championship tests | `arcade_dashboard_1280.png` | Pass |
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
```

The Arcade smoke backend may report a higher physical framebuffer on Windows display scaling; the logical window size remains the requested size and the image is inspected at the actual captured dimensions.
