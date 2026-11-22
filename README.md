# Smart Racing Championship

Smart Racing Championship is a deterministic 2D top-down racing game for Design and Analysis of Algorithms. The game uses graph routing, dynamic programming, greedy planning, backtracking, an MST backbone, heaps, and three sorting algorithms as real gameplay services.

## Requirements

- Python 3.12+.
- `pygame-ce` for the graphical game.
- `arcade` for the final user-facing application and all five screens.
- `matplotlib` for experiment charts.
- `pytest` and `ruff` for development checks.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

If PowerShell blocks activation, run the commands with the Python executable inside `.venv` directly.

## Run

Validate all circuits:

```powershell
python run_validation.py
```

Run a deterministic headless race:

```powershell
python run_game.py --headless --track circuit_01
```

Launch the graphical application:

```powershell
python run_game.py
```

Launch the final Arcade application:

```powershell
python run_arcade.py
```

The Arcade application provides the complete PLAN → RACE → REVIEW flow. It uses
the shared authoritative track repository, graph, route planner, resource
modules, race engine, algorithm lab, and championship scoring state. The Explorer
supports interactive endpoint selection, checkpoint-aware routing, route
comparison, resource planning, map inspection, and road-event rerouting. Racing
supports fixed-step graph movement, speed/brake/fork decisions, fuel, nitro,
sprint, closures, camera/minimap controls, and persistent results.

Build a Windows executable after installing development requirements:

```powershell
.\build_executable.ps1
```

The executable is created under `dist\SmartRacingChampionship\`.
The Arcade Phase 1 executable is created under `dist\SmartRacingChampionshipArcade\`.

Controls: `1` Main Menu, `2` Track Explorer, `3` Racing Screen, `4` Algorithm Lab, `5` Dashboard, `Enter` starts a quick race, and `Esc` returns to the menu.

Run the championship:

```powershell
python run_championship.py
```

Run all five experiments and regenerate raw data/charts:

```powershell
python run_experiments.py
```

Run tests:

```powershell
python -m pytest
```

## Project rules

The fixed rules are documented in [`docs/game_rules.md`](docs/game_rules.md). The three JSON circuits are deterministic and validated at startup. Opponents use fixed strategies; there is no machine learning or reinforcement learning.

## Submission

Run `build_submission.ps1` after replacing the registration-number and section placeholders. It runs validation, tests, a headless smoke race, builds a clean staging directory, writes a manifest, and creates the final ZIP.

## Layout

- `src/smart_racing/algorithms`: algorithm implementations and counters.
- `src/smart_racing/model`: graph, race, and event records.
- `src/smart_racing/services`: route planning, event scheduling, racing, scoring, and validation.
- `src/smart_racing/ui`: optional Pygame UI with the five required areas.
- `tests`: unit and integration tests.
- `experiments`: headless measurement scripts, raw CSV/JSON, and charts.
- `docs`: architecture, rules, algorithm notes, test plan, experiments, and demo script.
