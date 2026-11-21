# SMART RACING CHAMPIONSHIP — OVERNIGHT CODEX MASTER EXECUTION PROMPT

> **Paste everything from “START OF CODEX PROMPT” onward into Codex.**
>
> **Repository:** https://github.com/Bilalmughal-07/2D_SmartRacingChampionShip.git
>
> **Stack:** Python 3.12, Arcade (not Pygame for new UI), `arcade.gui`, pytest, JSON, Matplotlib/Pandas, Git/GitHub CLI.
>
> **Reality check:** A prompt cannot grant GitHub permissions, waive required confirmations, defeat branch protection, or guarantee uninterrupted overnight execution. Start the agent in an environment with the permissions and authentication you explicitly authorize. If a mandatory approval is required, do not bypass it; continue independent work, record the blocker, and request the approval. Never claim a PR is merged when it is not.

---

# START OF CODEX PROMPT

You are an autonomous senior Python/Arcade game engineer, DAA algorithm engineer, UI/UX designer, QA engineer, release engineer, and GitHub workflow maintainer. Execute a **multi-phase, production-quality implementation and verification** of **Smart Racing Championship**, a 2D top-down university Design and Analysis of Algorithms racing game. Do actual repository work, not just provide plans. Work iteratively until the authorized time/session budget ends, and leave an actionable checkpoint if interrupted.

## 0. Source of truth, environment and operating boundaries

1. Read **Project.pdf** in the repository/workspace first; if unavailable, locate it in provided files or clearly record that it is missing. **Do not pretend to have read it.** Read the existing README, requirements, implementation guide, code, tests, assets, and git history. Requirements in the PDF take priority over this prompt where they conflict. Separate PDF mandates from design recommendations and bonus extensions.
2. Confirm `git remote -v` points to `https://github.com/Bilalmughal-07/2D_SmartRacingChampionShip.git`. Check whether the GitHub remote is empty, contains a default branch, or has divergent history. **Never force-push, reset, delete work, or overwrite a remote history.** Preserve all existing code and data; migrate carefully.
3. Verify Python, Arcade version, `gh --version`, `gh auth status`, `git status`, current branch, remotes, network connectivity, and whether `gh` can create PRs. Do not print authentication secrets or tokens. Use a supported Arcade API for the installed version; do not blindly copy older Arcade examples.
4. Ask for/obtain **all legitimate tool, filesystem, shell, network and GitHub permissions upfront through the execution environment's supported approval flow**. Prefer authorized non-interactive commands and preconfigured authentication. **Do not circumvent security prompts, approval gates, branch protection, required reviews, or GitHub policies.** If a tool asks for mandatory human confirmation, pause that action, continue work that does not require it, and provide a concise blocker list. Never claim you can self-approve your own required reviewer approval.
5. Maintain `docs/OVERNIGHT_PROGRESS.md` after every significant work unit: timestamp, phase, changes, tests, screenshots, commit SHA, PR URL/status, blockers, next action. Maintain `docs/REQUIREMENTS_TRACEABILITY.md` mapping every PDF requirement to code, tests, and evidence. Do not mark anything VERIFIED without evidence.
6. Work from the actual codebase. Do not create duplicate algorithm implementations, dummy dashboards, nonfunctional buttons, placeholder racing physics, fabricated benchmark results, or screenshot claims. Keep the algorithms independent of the Arcade UI.
7. Prioritize **correctness and complete integration** over unnecessary decoration. Never introduce ML or reinforcement learning.

## 1. GitHub lifecycle — mandatory for EVERY phase

**Goal:** one isolated feature branch and one professional PR per phase, including Phase 1 if it needs migration/repair, then Phase 2 onward. No unreviewed direct commits to the default branch. Ensure a working default branch before starting; if the remote is empty, initialize it only with authorized access and without overwriting existing remote content. Determine the real default branch; do not assume `main` if different.

For each phase:

1. Update the local default branch using a safe fast-forward (`git pull --ff-only` where appropriate). Confirm clean working tree; commit or safely preserve unrelated local changes before switching branches.
2. Create `feat/phase-01-main-menu`, `feat/phase-02-track-explorer`, `feat/phase-03-racing-engine`, `feat/phase-04-algorithm-lab`, `feat/phase-05-championship`, `feat/phase-06-experiments-qa`, `feat/phase-07-release` as applicable. If a phase is already implemented, audit and improve it rather than overwriting it; open a PR for actual necessary work only.
3. Make focused conventional commits, e.g. `feat(explorer): add checkpoint-aware route planning`, `fix(racing): prevent illegal blocked-edge traversal`, `test(algorithms): verify A* and Dijkstra optimal costs`, `docs(phase-02): document route cost normalization`. Include meaningful bodies for nontrivial commits. Never commit secrets, virtual environments, build artifacts, caches, huge recordings, or unlicensed assets.
4. Run relevant tests, lint/type checks where configured, headless or GUI smoke tests, and a screenshot-based visual review. Include results and limitations in the PR description.
5. Push the feature branch using `git push -u origin <branch>` with already-authorized credentials. Use GitHub CLI to create a PR, e.g. `gh pr create --base <default> --head <branch> --title "feat: Phase 2 — interactive track explorer and routing" --body-file <PR-body-file>`. Use the actual branch names and current repository state.
6. PR description must contain **Summary**, **PDF requirements covered**, **Design decisions**, **Screenshots/evidence**, **Tests and exact commands/results**, **Known limitations**, **Risk/rollback**, and **Checklist**. Include linked issues if present.
7. Wait for/check CI via `gh pr checks <PR-number> --watch` where feasible. Fix failures in the same branch and push additional commits. Review the diff for correctness and security.
8. If repository rules **explicitly allow self-merge** and the user has already authorized autonomous merging, merge the PR with `gh pr merge <PR-number> --squash --delete-branch` after checks pass. If approvals or branch protection require another person, **do not bypass**: leave PR open and continue independent next-phase work on a branch based on the latest verified integration state, clearly recording dependency and merge blockers. **Do not close an unmerged PR as a substitute for merging.** GitHub typically marks a successfully merged PR as *closed/merged* automatically. Verify the PR state with `gh pr view` and branch/default-branch status. Do not run `gh pr close` on a valid PR simply to make it appear completed.
9. Once merged, fast-forward the default branch and verify integrated tests. Clean up local branches only after confirming their commits are safely merged. Maintain a release/merge ledger in `docs/OVERNIGHT_PROGRESS.md`.
10. If remote authentication, repository initialization, PR creation, CI, or merge requires approval, **never stall the whole job**: complete local commits and tests, preserve branches, document exact blocked commands, and proceed with work not dependent on the blocked operation. Do not claim the GitHub action succeeded unless it actually did.

**GitHub CI:** add `.github/workflows/ci.yml` with Python setup, pinned/compatible dependency installation, lint/static checks if configured, unit tests, graph validation, and safe headless tests. GUI rendering tests may require an appropriate display server (e.g. Xvfb); report when not supported. Protect against accidental infinite CI loops and flaky frame-timing tests.

## 2. Shared product requirements and architecture

Implement a playable, polished, understandable **2D top-down racing game** with **PLAN → RACE → REVIEW**. At least **three distinct playable circuits**, **10 mandatory ordered checkpoints per circuit**, **two shortcuts per circuit**, branching intersections, alternatives, at least one cycle and dead end, fuel stations, nitro pickups, varying road difficulty, obstacles and road closures. **One human player plus at least three deterministic AI racers.** Five fully functional primary GUI screens: Main Menu, Track Explorer/Route Planner, Racing Screen, Algorithm Lab, Championship Dashboard. Twelve mandatory algorithm families, five benchmark studies, and three advanced challenges as bonus unless PDF/instructor requires them.

Architecture: pure Python graph and algorithm modules; immutable/validated circuit definitions with explicit dynamic edge status; race simulation with deterministic fixed-timestep updates; resource rules shared between planner and race engine; event min-heap; championship scoring; Arcade rendering and input; Arcade Views with shared `GameSession`; JSON assets/config; test suite; experiment runners. Avoid global state and tightly coupled UI/algorithm code.

Build clear UX states: loading, empty, success, failure, unreachable route, insufficient fuel, race paused, DNF, race finished, championship finished. Every button and keyboard shortcut must have a meaningful response, visible focus, Back/Escape behavior, and safe state transitions.

### Suggested directories (adapt to repository)

`core/`, `algorithms/`, `tracks/`, `game/`, `ui/views/`, `ui/components/`, `rendering/`, `assets/backgrounds/`, `assets/cars/`, `assets/roads/`, `assets/icons/`, `tests/`, `experiments/`, `docs/`, `.github/workflows/`.

## 3. Phase 1 — audit/finalize Arcade Main Menu

If Phase 1 already exists, test and repair it; otherwise implement it. Full-screen cinematic **racing battle** background: four competing sports cars on a nighttime track, blue/cyan highlights, amber sparks, no embedded text. Use only original or properly licensed assets; implement an attractive fallback if artwork is missing. Add dark overlay for readability.

Title centered top: **SMART RACING / CHAMPIONSHIP**; subtitle **THE ALGORITHMIC RACING CHALLENGE**. All seven buttons in one vertically centered column under title, approximately 360px wide at 1600×900: **START CHAMPIONSHIP**, **QUICK RACE**, **TRACK EXPLORER**, **ALGORITHM LAB**, **HOW TO PLAY**, **SETTINGS**, **EXIT GAME**. Responsive layouts at 1280×720, 1600×900, 1920×1080. Theme navy `#0B1220`, slate `#18263B`, cyan `#38BDF8`, emerald `#2DD4A0`, amber `#FBBF24`, coral `#F87171`, white `#F1F5F9`.

Navigation: Championship → resume/new → scheduled circuit → Explorer; Quick Race → circuit select → Explorer; Track Explorer → standalone exploration; Algorithm Lab → lab; How to Play and Settings → working modals; Exit → confirmation. Support keyboard and mouse, focus, hover, Enter, Escape, safe persistence, and back navigation. Verify every button actually works. Commit, push, PR, checks, merge/close per §1.

## 4. Phase 2 — Track Explorer, readable circuits and full planning

**This phase is critical.** Make all three circuits instantly understandable to a first-time user. Do not present tangled lines, overlapping junctions, fused roads, isolated pickups, or text that covers intersections. The world should look like a top-down **racing road network** rather than an abstract graph, while still displaying the true graph accurately.

### 4.1 Three distinct, fully playable circuit designs

- **Circuit A — Emerald Loop** (forest, approachable): broad loop, obvious main road, two clearly marked alternate shortcuts, spaced checkpoints, readable service branch and one clearly marked dead end.
- **Circuit B — Canyon Switchbacks** (desert, strategic): distinct winding switchbacks and alternate upper/lower roads; carefully spaced intersections; difficult/short route versus safer/longer route.
- **Circuit C — Metro Grid** (urban, complex): clean city-block road grid, visible one-way arrows where used, multiple junction choices, two shortcuts, legible lanes and obstacle/restriction areas.
- These are **recommended names/themes**. Retain valid existing IDs and track naming if present; do not falsely claim the PDF requires these names.

For **each** circuit, validate at least 10 ordered checkpoints, ≥2 shortcuts, ≥1 cycle, ≥1 dead end, alternative paths, fuel and nitro opportunities, valid start/finish and lap transition, fuel-feasible full checkpoint sequence, and valid routes after representative closures. At least one circuit must yield genuinely different optimal routes under different weighted presets. Do not just color two roads differently while retaining identical route cost/geometry.

**Geometry/readability rules:** use a documented world coordinate system and node/edge geometry. Provide generous spacing between parallel roads, intersections and checkpoint icons; ensure road widths do not visually merge unrelated edges. Avoid accidental crossings that look like intersections: use bridges/overpasses with unmistakable styling if graph edges cross without connecting, or reroute the geometry to eliminate crossings. Every real intersection must have a visible junction and graph vertex. Keep mandatory checkpoint labels offset from roads, with leader lines where needed; apply collision-aware label placement and zoom-aware labels. Mark dead ends with a visible termination and label, not an unexplained line. Clearly distinguish main road, shortcut, blocked edge, restricted edge, service road and non-traversable scenery. Provide legend, tooltip, map focus, reset and fit-to-track. Fuel and nitro locations must lie on traversable graph vertices/edges and be reachable from valid routes. Validate both **graph topology and screen-space geometry** at supported resolutions and zoom levels. Keep user-facing maps visually clear in screenshots.

### 4.2 Track Explorer UX

Large map (~70% width), right planning panel (~30%), top circuit/mode toolbar, bottom legend/status. Pan/zoom, hover/click vertices/edges, choose start/destination for exploration, show ordered checkpoints, route highlight, arrows, obstacles, dynamic road status, tooltips, and clear color contrast. Previous/next circuit enabled only where mode permits; Championship follows fixed order. Back, Reset View, Fit Map, Calculate Route, Compare Routes, Resource Planner, Algorithm Lab, Start Race must work.

### 4.3 Algorithms and routing

BFS reachability and minimum **edge-count** path; DFS traversal, cycle detection, connected/reachable regions, dead-end analysis and **bounded** alternative simple paths (all-path enumeration can be exponential); Dijkstra minimum nonnegative weighted scalar cost; A* optimal using admissible/consistent lower-bound heuristic or safe `h=0`. Verify A* and Dijkstra return equal optimal costs under identical objective. Support blocked/unreachable/zero-weight/equal-cost/source=target/directed cases. Count visited/expanded nodes, examined/relaxed edges, heap operations, runtime excluding rendering.

For race planning, enforce **START → CP1 → CP2 → ... → CP10 → FINISH/LAP BOUNDARY** in order, including safe behavior when a shortest leg passes a later checkpoint prematurely. Use a checkpoint-progress-aware state-space or another demonstrably correct method; do not accidentally accept invalid progress. Plan/replan from current vertex and checkpoint progress after closures. Show **exact** weighted cost optimized; normalize distance/time/fuel/difficulty/obstacle terms and document nonnegative weights. Presets Balanced/Speed/Economy/Safety apply to weighted routing, not BFS/DFS. Show alternative route comparison with real distance, time, fuel, risk, shortcut use, route cost, and feasibility. Route summary must match actual edge list.

### 4.4 Resource planning and transfer

Implement real 0/1 knapsack DP or documented refuelling DP; Greedy benefit/cost comparison with at least the PDF counterexample and two original counterexamples; reconstruct chosen pickups. Match race fuel and nitro rules, capacities, station accessibility, stop time, and consumption. Show feasible/infeasible with reasons. Transfer selected circuit, algorithm/preset, route, resource plan, and mode into shared `GameSession`. Start Race only when a valid mode and plan exist; provide meaningful recovery options otherwise. If Phase 3 is incomplete, use a clearly labeled temporary destination only until Phase 3 is built.

**Phase 2 exit gate:** three readable validated circuits; true route overlays; all four algorithms; checkpoint correctness; preset comparisons; resource planning; working navigation; tests and screenshots at three resolutions; GitHub PR lifecycle complete/blocked status recorded.

## 5. Phase 3 — complete playable Racing Screen and meaningful human decisions

Build a **real 2D top-down race**, not a static graph with moving dots. Use professional asphalt roads and markings, edge-aligned car sprites with heading/rotation, road shoulders, scenery, barriers, road restrictions, readable junctions, animation and HUD. The car must follow the graph's legal roads; smooth motion interpolates along edge geometry, while the graph remains authoritative. Avoid teleportation, clipping through scenery, crossing disconnected roads, or cars appearing off-track.

### 5.1 Camera system and minimap

- **Follow Camera:** smooth player-car tracking, adjustable zoom, bounded to circuit, motion smoothing.
- **Tactical/Overhead Camera:** zoomed-out view of nearby junctions and route decisions.
- **Full Circuit View:** fit entire circuit to viewport for strategic awareness; preserve UI legibility.
- **Optional Free Camera:** pan/zoom while paused or exploring, then return to follow mode.
- Camera switching via on-screen buttons and documented keyboard shortcuts; show current mode and reset behavior. Camera transforms must correctly handle world/screen coordinates, sprites, hit-testing, and labels.
- **Bottom-left minimap:** always-visible compact representation of the **entire current circuit**; show all four racer positions with distinct icons/colors and legend, player facing/position, start/finish, checkpoints, selected route, and closures. Avoid minimap covering important controls. Update at a stable interval and keep positions consistent with world state. Add enlarge/toggle option if space permits. Verify it shows all vehicles even when main camera follows only one.

### 5.2 Meaningful player control and decisions

The PDF requires a **human-controlled racer**. Implement a documented, enjoyable hybrid approach: car automatically follows valid graph edges while the player makes actual consequential choices. Provide **accelerate/sprint**, **brake/coast** or speed-control within balanced rules, **nitro activation**, **route choice at junctions**, **shortcut accept/avoid**, **reroute**, **fuel station stop/refuel**, **camera switching**, **pause**, and a clear decision prompt when an upcoming fork or closure matters. If manual steering is added, preserve edge legality and checkpoint logic. Do not fake controls that have no effect. Show immediate HUD feedback, countdowns, costs and consequences. Keep the player capable of winning or losing based on decisions, not purely passive watching. Define sprint separately from nitro (speed, duration, cooldown, fuel trade-off) and document it; ensure it does not break resource balance or determinism. For nitro use suggested PDF defaults unless documented otherwise: max 3 charges, 1.5× speed for 4s, 2× fuel consumption while active; full starting fuel, difficulty-adjusted edge fuel, stations up to 40 fuel per stop with time cost.

### 5.3 Race rules and AI

One player + three deterministic AI racers, all subject to the same road, fuel, nitro, checkpoint and event rules. Suggested 2 or 3 laps, ≥10 checkpoints **in strict order per lap**. A shortcut counts only when legal/open and does not skip mandatory checkpoints. No traversal without sufficient fuel; provide legal stop, refuel, recovery or DNF. AI1 fixed route with documented detour; AI2 shortcut preference with fallback; AI3 shortest-distance route and dynamic replanning. Deterministic policies for station selection, event response, ties and time limit. Show racer ranking, laps, next checkpoint, fuel, nitro, speed, race time, events, and notifications without clutter.

### 5.4 Dynamic events

Implement custom min-heap ordering `(triggerTime, priority, insertionSequence)` with documented priorities and events: road blockages, shortcut open/close, oil spill, speed restriction, station availability, nitro booster. Process simultaneous events in deterministic order, manage overlap and expiration, cancel safely, validate targets, and reroute **without restarting the race**. A car on a newly blocked edge must follow a documented safe transition rule; no disappearing cars or silent freezes. Add a concise live event feed and visual road warnings.

### 5.5 Race completion and user flow

Racing Screen → race results → Championship Dashboard / Next Race / Replay / Main Menu. Finish by valid ordered checkpoints and lap boundary; rank finishers by time then racer ID, time-limited unfinished racers by documented progress comparator; handle DNF clearly. Test complete races, shortcut decisions, fuel shortage, sprint/nitro, closures, camera modes, minimap positions, and all navigation.

**Phase 3 exit gate:** a genuinely playable race with meaningful decisions, accurate vehicle movement, all AI, dynamic events, camera modes, always-readable bottom-left minimap tracking all cars, polished HUD, and full integration tests. Commit/push/PR/checks/merge/verify.

## 6. Phase 4 — fully professional Algorithm Lab (mandatory, not a stub)

Create a complete educational **Algorithm Lab** with a polished, beginner-friendly layout and working features for **all twelve mandatory algorithm families**. The Lab must call the **same underlying algorithm code** used by gameplay; no separate hardcoded demo algorithms. Support actual circuit graphs and appropriate sample datasets.

### 6.1 Lab navigation and usability

Left sidebar algorithm catalog grouped by **Graph Exploration**, **Route Optimization**, **Resource Optimization**, **Track Construction**, **Scheduling/Heaps**, **Championship Sorting**. Center large interactive visualization. Right panel: pseudocode/step explanation, active variables, operation counters, complexity, assumptions and current result. Bottom toolbar: **Load Dataset, Reset, Previous Step (if snapshots supported), Next Step, Play/Pause, Speed Slider, Run to End, Compare, Export Results, Back**. Clear state transitions, descriptive tooltips, accessible contrast, responsive layouts, no clipping. Show visual legend and what each color means. Allow example data and user-selectable circuit/vertices, with validation and reset. Provide optional beginner/expert information density.

### 6.2 Every algorithm must be demonstrable

1. **BFS:** queue, current vertex, visited frontier, parent tree, reachability and minimum-edge path.
2. **DFS:** recursion/stack, discovery/finish, cycle detection, components/reachable regions, dead ends, bounded alternative paths.
3. **Dijkstra:** priority queue, distances, relaxations, visited/settled nodes, final optimal path.
4. **A*:** `g`, `h`, `f`, open/closed sets, expansions, heuristic admissibility and optimal path comparison with Dijkstra.
5. **Dynamic Programming (0/1 Knapsack/refuelling):** state table, transitions, budget, optimal benefit, reconstructed choices.
6. **Greedy:** benefit/cost ranking, selected items, budget and counterexample comparing with DP (PDF example: budget 10, A 6/30, B 5/24, C 5/24 → Greedy 30 vs DP 48); two original counterexamples.
7. **Backtracking:** placement/generation decision tree, constraints, pruning, rejection reasons, valid solution.
8. **Prim OR Kruskal:** undirected MST backbone, chosen edges, running weight, why extra edges are needed for cycles/shortcuts.
9. **Custom Min-Heap/Priority Queue:** insertion, sift-up/down, extraction, event order `(time, priority, sequence)`, cancellation/expiration; optionally top-k heap view.
10. **Merge Sort:** partitions/merges, comparisons, stable ranking behavior.
11. **Quick Sort:** pivot, partition, comparisons, documented worst case.
12. **Heap Sort:** heap construction, swaps/extractions, comparisons.

For all: show correct **input**, step narration, visual state, **actual measured operation counters**, output, theoretical time/space complexity, limitations, and how it is used in gameplay. Provide at least one normal case and one edge case per algorithm; allow reset and reproducible runs. For graph algorithms, distinguish weighted vs unweighted claims; for sorting use the **same championship comparator** across all methods. Avoid calling a data structure an independent algorithm without explaining its supporting role.

### 6.3 Lab-to-game integration and QA

Launch Lab from Main Menu and Track Explorer; preserve return context. Offer a **Use Current Circuit** action. Step playback should not mutate the live race unexpectedly; use snapshots/read-only inputs where appropriate. Export counters/data to CSV/JSON for experiments. Unit-test each trace against the real algorithm output. Visual-test every algorithm at three resolutions. All buttons must work. Commit/push/PR/checks/merge/verify.

## 7. Phase 5 — complete Championship Dashboard and progression

Championship across all three circuits in predefined order. After each race show positions, valid finishing times, fastest laps, points, event/resource statistics, Next Race/Replay/Menu. Award position points **25, 18, 15, 12, 10, 8, 6, 4, 2, 1** for ranks 1–10; document unfinished/DNF points policy. Maintain cumulative scores, wins, sum of finishing positions, best fastest lap, racer ID. Tie-break **points descending → wins descending → sum positions ascending → best fastest lap ascending → racer ID ascending**. Use one total comparator for **Merge Sort, Quick Sort, Heap Sort, top-k**; verify exact agreement.

Make the Dashboard attractive and clear: standings table with readable columns, top-three podium, race-by-race history, points changes, sorting method selector, top-k selector, comparison/counters panel, current championship progress, final champion screen and clear navigation. The player's choices during race must affect results through actual simulation. Persist championship safely and allow resume/new confirmation. Do not award points twice on repeated navigation. Verify standings after each race and champion after last. Commit/push/PR/checks/merge/verify.

## 8. Phase 6 — five experiments, advanced challenges, QA and accessibility

### 8.1 All five required experiments (real measurements)

1. **BFS vs DFS:** vary vertices/edges and sparse/dense graphs; runtime, visited nodes, examined edges, correctness.
2. **Dijkstra vs A*:** vary graph sizes/circuits; runtime, expansions, relaxations, heap operations, optimal cost equality.
3. **DP vs Greedy:** vary items/budget; benefit, choices, runtime, DP states; PDF counterexample + two original failures; brute-force verification on small instances.
4. **Event min-heap:** varying event count, insert/extract time, operations, equal-time ordering, cancellation, expiration.
5. **Merge/Quick/Heap Sort and top-k:** varying `n`, `k`, random/sorted/reverse/duplicates; runtime, comparisons, output equality, final racer-ID tie case.

Use repeated runs (recommended ≥5 after warm-up), `time.perf_counter_ns()`, identical inputs/conditions, no rendering or I/O inside timed algorithm sections, raw CSVs, summary statistics, reproducible seeds, charts, environment details, methods, limitations and interpretation. Never fabricate metrics. Provide a one-command reproducible experiment runner.

### 8.2 Advanced challenges (bonus, after mandatory correctness)

- MST + backtracking automatic circuit generation, with rejected invalid example and validator proof.
- Multi-objective preset trade-offs; demonstrate genuine differing routes and limitations of scalarization.
- Live top-k heap analytics vs full sorting, with correctness and performance comparison.

### 8.3 Deep self-testing

Use **pytest** for pure logic/integration, deterministic replay tests for races/events, property-based tests if available, and Arcade GUI tests through an actual display or Xvfb where supported. **Playwright is intended for browser/web interfaces; do not claim it can directly operate an ordinary Arcade desktop window.** For desktop GUI, use supported desktop automation (e.g. PyAutoGUI with a working display) and/or deterministic input-injection and screenshot capture. If the repository has a separate browser dashboard, Playwright may test that web portion. Use whichever tools are actually installed and appropriate. Record exact commands, environment and results.

Test: 3 complete championships; multiple seeds and event schedules; all screens; all buttons; keyboard/mouse navigation; all four cars on minimap; all camera modes; route legality; checkpoint order; fuel/nitro; unreachable routes; dead ends; blocked roads; overlapping events; pause/resume; DNF; sorting ties; 1280×720/1600×900/1920×1080; missing assets; save/load; restart; package smoke test. For each failure: **reproduce → diagnose → fix → rerun targeted tests → rerun regression suite → inspect actual screenshots**. Never claim a screenshot was reviewed if it was not captured and inspected.

Create a test evidence index under `docs/QA_EVIDENCE.md`; avoid committing large binary recordings. Add an accessibility pass: keyboard-only navigation, focus, readable labels, color + icon distinction, no tiny map labels, tooltips, sufficient contrast and safe modal behavior. Commit/push/PR/checks/merge/verify.

## 9. Phase 7 — final polish, report, build, release and repository audit

Complete README with install/run instructions, controls, screen flow, architecture, circuit legend, algorithm catalog, experiments, known limitations, acknowledgments/licenses, and troubleshooting. Produce a complete technical report PDF matching **Project.pdf** sections (title; introduction; architecture; graph/data/normalization/rules; algorithm pseudocode/correctness/complexity; gameplay integration; testing; five experiments/charts; limitations/advanced challenges; conclusion/references). Include actual data, not invented results. Package a runnable executable using PyInstaller with assets, test on available OS, and record portability limits. Prepare submission ZIP with source, executable, assets, report, raw results and instructions, named according to **actual registration numbers and section supplied by the user**; never invent them.

Run final full suite and a complete manual/automated game walkthrough from Main Menu → Track Explorer → Race → Results → Next Circuit → Final Champion, plus all Algorithm Lab algorithms. Verify all three circuits' graph and geometry validators. Confirm every mandatory requirement has evidence in traceability matrix. Verify GitHub PR history, final default branch, CI status, README screenshots and release assets. Create final Phase 7 PR, merge only if authorized and allowed, verify merged/closed state.

## 10. Priority, iteration and overnight resilience

Work sequentially: **Phase 1 audit → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7**. Within each phase, use small testable commits. Do not leave a phase as “complete” if critical functionality is fake or broken. If time runs short, prioritize mandatory requirements and document bonus gaps rather than sacrificing correctness.

Use this loop repeatedly:

**INSPECT → PLAN → IMPLEMENT → RUN → CAPTURE → INSPECT VISUALLY → TEST → FIX → REGRESSION TEST → COMMIT → PUSH → PR → CHECK → MERGE (if authorized) → VERIFY → NEXT PHASE.**

At session start, write `docs/OVERNIGHT_PROGRESS.md` and a task ledger; update it after each completed unit and before any risky operation. If the environment has execution time limits, save progress and exact resume commands frequently. Do not assume you can run indefinitely or continue after the agent session ends. If blocked on approvals, preserve state and continue other independent tasks; clearly flag what cannot proceed. Do not use `--force`, `--no-verify`, security-bypass flags, unauthorized tokens, or destructive repository operations to suppress confirmation. Never self-approve required reviews.

**Final response after the actual work:** concise status table per phase (done/partial/blocked), key features, tests with counts, screenshots inspected, commit SHAs, PR URLs and actual states (open/merged/blocked), final branch status, artifact paths, known issues, and exact next actions. Do not fabricate results or claim overnight work was completed if it was not.



---

# 11. EXECUTION PLAYBOOK — EXACTLY HOW TO WORK, NOT JUST WHAT TO BUILD

This section is an **operational specification**, not a substitute for Project.pdf. The PDF's explicit requirements remain authoritative; the interface design, suggested architecture, example names, automation choices, and extra usability features here are implementation recommendations. Do not turn suggestions into false assignment requirements.

## 11.1 Before changing a single line of source

**Actions:**

1. Inspect the entire working directory with `pwd`, `find`/`rg --files`, `git status --short --branch`, `git log --oneline -10`, `git remote -v`, and inspect `pyproject.toml`, `requirements*.txt`, existing `main.py`, tests, assets and game modules. Avoid dumping secrets or large files.
2. Open Project.pdf from the actual workspace and build a requirement inventory with PDF section/page, mandatory/bonus status, owner module, test ID, UI evidence, and status. If it is missing, stop claiming PDF compliance; use the present requirements provisionally and flag the missing source.
3. Identify the current working version, whether Pygame remains, whether Arcade is installed, what is already working, and which modules are pure Python. Run the baseline tests **before** migration and record failures without attributing them to new code.
4. Confirm `gh auth status`, repository visibility/access, branch protections and CI. Determine whether remote has commits and whether `origin` is correct. Check that push, PR creation and merge rights are actually available. Do not repeatedly prompt for the same missing authorization; use the authorized flow and keep working locally if blocked.
5. Establish a reproducible environment. Prefer `python -m venv .venv` where available, pinned/compatible requirements or a lockfile, `.gitignore`, a documented entry point, and `python -m pytest`. Do not install untrusted packages without evaluating necessity. Keep Python 3.12 as preferred; if incompatible with an installed dependency, document the verified supported version instead of silently changing the project.
6. Capture baseline screenshots of existing screens if a display is available. Record screen resolution, OS, Arcade version, and whether visual verification was possible. Do not confuse image assets with actual game screenshots.
7. Write `docs/IMPLEMENTATION_PLAN.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/OVERNIGHT_PROGRESS.md`, and `docs/TEST_MATRIX.md` with real starting statuses. Use checkboxes only when evidence exists.

**Expected output:** a clear inventory of reusable code, known defects, missing assets, tests, permissions, project requirements and an ordered implementation plan. Do not jump into cosmetic changes before understanding the graph/race engine.

## 11.2 Repeatable engineering loop for every feature

For every feature or bug, use this precise sequence:

1. **Define behavior**: write the user story, input, expected state transition, success result, invalid-input result and test cases.
2. **Define data contract**: identify authoritative records and invariants; avoid new duplicate state.
3. **Implement logic first**: add pure Python behavior and unit tests; prefer deterministic APIs and explicit result objects.
4. **Connect the Arcade view**: map user actions to the logic, display actual results, and provide feedback for errors.
5. **Exercise edge cases**: unreachable graph, empty list, blocked edge, missing asset, repeated button activation, back navigation, pause, save/load.
6. **Inspect visual output**: launch the actual app, capture screenshots and review readable text, geometry, focus, overlap and contrast.
7. **Run regression tests**: verify earlier phases, not only the new view.
8. **Commit**: make a scoped conventional commit with tests and documentation, then update progress and traceability.
9. **PR/merge**: push, open a meaningful PR, check CI and merge only when allowed; verify actual GitHub state.

**Definition of DONE:** implementation exists, user can reach it, controls respond, output comes from real logic, edge cases are handled, tests pass, visuals are inspected, state survives navigation where required, documentation matches reality, and GitHub status is recorded. A feature with only a screenshot, button or placeholder is NOT done.

## 11.3 Overnight time-budget and interruption handling

- Keep a small `NEXT_ACTION` section in `docs/OVERNIGHT_PROGRESS.md` with branch, last good commit, commands to run, pending PR, active bug, and precise next file to edit.
- Work in bounded milestones; commit tested slices frequently. Do not wait until the end to commit or write test evidence.
- Prefer non-interactive commands only when explicitly authorized: `python -m pytest -q`, `git -c core.pager=cat status`, `gh --version`, `gh pr view --json state,mergeable`, etc. Use documented CLI flags; never guess approval-bypass options.
- Do not spawn uncontrolled background jobs or promise to work after the agent/session stops. If a task requires a real approval, document it and switch to another independent feature.
- If CI is slow, monitor with bounded waits and perform other work; do not treat an uncompleted check as passed.
- If code migration causes regression, fix or safely revert **your own** isolated change, preserving unrelated user work. Never reset or force-push unknown work.
- Never make a silent destructive action, leak credentials, fabricate completion or substitute a fake GUI for a required one.

# 12. USER JOURNEYS — EVERY BUTTON, SCREEN, DECISION AND EXPECTED RESULT

Implement these end-to-end journeys and add automated or recorded tests for each. Use one `GameSession` containing mode, championship ID, current circuit, route preset, selected route, checkpoint progress, race state, results, navigation return target and persistent preferences. Give each view explicit `on_show_view`/`on_hide_view` lifecycle management compatible with installed Arcade version; never register duplicate handlers or lose session references.

## 12.1 First-time launch → Main Menu

**User sees:** readable cinematic racing battle background, title, seven centered buttons, keyboard focus, subtle motion, version/help information. Background never obscures text; missing artwork displays a tasteful fallback, not a crash.

**User does:** click Start Championship, Quick Race, Track Explorer, Algorithm Lab, How to Play, Settings or Exit. **Expected:** correct action, no dead button, one activation per click, clear Back/Escape, no unexpected state loss. Modal input is isolated; clicking behind a modal does nothing.

## 12.2 Start Championship → plan → race → results → next circuit

**User sees:** New/Continue choice if a save exists, championship race order and progress, first scheduled circuit, named AI competitors and mode indicator. **User does:** start new or resume; inspect circuit, compare routes, choose preset, plan fuel/nitro, choose a feasible plan and start. **Expected:** session mode=`championship`, scheduled circuit locked to proper order, player and three deterministic AI created, Race View receives real graph and resources, results award points exactly once, dashboard displays updated standings and Next Race. Repeat for all three circuits; final race declares champion. Cancel/New must not silently delete saved progress.

## 12.3 Quick Race → circuit choice → plan → race → results

**User sees:** three circuit cards with actual thumbnails/preview, difficulty, checkpoint count, shortcut count, environment and an explanation of what makes each track distinct. **User does:** select circuit, plan route, race. **Expected:** no championship points changed, quick-race results remain available for review, Replay/Choose Circuit/Menu work. Any route saved for one circuit must not accidentally be reused for another.

## 12.4 Standalone Track Explorer → algorithms → return

**User sees:** interactive graph map, clear legend, actual node/edge attributes, selectable start/destination, checkpoint order, algorithm selector and metrics. **User does:** pan, zoom, inspect roads, run BFS/DFS/Dijkstra/A*, compare routes, view resource recommendations, open Algorithm Lab, return. **Expected:** algorithm results correspond exactly to visible edges, mode stays `explore`, opening Lab preserves the circuit/selection, and Back returns to the previous view. Starting a race requires choosing a valid mode and circuit; never silently award points.

## 12.5 Algorithm Lab → learn → compare → export

**User sees:** categorized algorithm catalog, explanatory one-sentence purpose, sample input/current circuit selector, visualization, pseudocode, operations, complexity, play/step controls and result. **User does:** select any required algorithm, load input, Next/Previous/Play/Pause/Reset, change speed, compare with a related algorithm, export. **Expected:** all steps are reproducible, no fake animation unrelated to algorithm state, exported counters agree with run, invalid inputs explain the problem, and return navigation works. Lab runs do not mutate a live race.

## 12.6 Race player decision flow

**User sees:** follow camera on player car, next mandatory checkpoint, upcoming junction choices, road status, speed, sprint, fuel, nitro, lap, position, elapsed time, AI status and full-track minimap at bottom-left. **User does:** accelerate/sprint, coast/brake, choose a fork, accept/avoid shortcut, activate nitro, stop/refuel, reroute, switch camera, pause/resume. **Expected:** each action changes simulated state meaningfully, displays consequences, respects legal graph edges, and can improve or worsen race performance. If a choice is invalid (blocked edge, insufficient fuel, skipped checkpoint), disable it or explain why, and offer valid alternatives. AI and player use the same core rules.

## 12.7 Road event → safe reroute

**User sees:** event notification and changed road marking; affected road turns red/blocked, restriction has distinct symbol. **User does:** inspect suggested detour, choose alternative if available, wait/recover if policy allows. **Expected:** event heap applies all same-time events first, affected racers reroute from current legal state, no teleport or disappearing car, no traversal of blocked edges, active effects expire independently, results remain deterministic.

## 12.8 Race completion, DNF and replay

**User sees:** results only when valid finish condition or time limit occurs, finishing positions, times, checkpoint/lap completion, points if Championship, and transparent DNF explanation. **User does:** view details, next race, replay or menu. **Expected:** finish order is correct, a skipped checkpoint cannot complete a lap, replay resets race-specific state, standings cannot be double-awarded, and Save/Continue recovers correctly.

# 13. TRACK DESIGN BIBLE — BUILD THREE LEGIBLE, VALID CIRCUITS

## 13.1 Graph correctness versus visual readability

**Graph source of truth:** vertices and edges are real race traversals. Rendering is a projection of this topology, not a separate hand-drawn decorative route. Every line the player perceives as a drivable road must have corresponding legal graph edges; every junction that permits turning must be represented by a graph vertex. Nonconnecting overpasses must be visibly separated or avoided.

**Rendering approach:** maintain separate `world_position`, optional `road_polyline`, road class, draw layer and hit-test geometry. Keep logical graph IDs stable even if art positions are adjusted. Draw shoulders/borders beneath asphalt, then lane/center markings, then icons, then route highlights and labels. Avoid map art that conceals the graph. Draw intersection patches only where edges actually meet at a shared vertex. Draw dead ends as capped roads with turn-back signs; draw closed edges with barricades rather than simply deleting them.

**Layout constraints:** define road width in world units; enforce a geometry-validation margin between nonincident road segments and between checkpoint icons. The margin should exceed combined visible road half-widths plus label clearance at default zoom. Reject unintended segment intersections or route them via explicit bridges. Test pairwise line-segment distance/intersection in geometry utilities; sample curves into line segments for validation. Check actual screen-space labels at each supported resolution; hide secondary labels on far zoom and reveal them on hover/zoom. Do not solve overlap by making roads too thin to read.

**Usability:** checkpoint icons numbered CP1...CP10 must be distinguishable without relying on color alone; start/finish visibly unique; fuel ⛽ and nitro ⚡ markers with tooltips and reachability; shortcut edges dashed/colored and marked S1/S2; difficulty shown via tooltip or road border rather than chaotic text. Provide a fixed legend and a toggleable graph-debug overlay with vertex/edge IDs for viva demonstrations. Tooltips must show direction, length, time, fuel, difficulty, status and whether shortcut. Make the default zoom fit the whole route and keep the right panel from covering critical nodes.

## 13.2 Circuit A: Emerald Loop — beginner, broad forest loop

**Visual goal:** a single dominant broad loop with a recognizable start/finish, clear clockwise progression, well-spaced checkpoint markers and two visually obvious alternate connectors. Do not cram CP1–CP10 around one bend. Use green forest scenery outside roads, not on top of them.

**Suggested topology:** main loop through ordered CP1..CP10, several junction vertices, two optional shortcuts that reconnect later without invalidly skipping mandatory checkpoints, one short side road ending at a clearly signed dead end, at least one accessible fuel station and nitro pickup on real branch/route vertices. Include an alternative safe route with different time/fuel trade-off. Distinguish short difficult vs long safe path. Make at least one closure recoverable by alternate path. Validate checkpoint order in both directions if edges are bidirectional.

**Expected user experience:** the player can trace the lap visually from Start to CP1...CP10 and back, see where choices happen, and understand why a shortcut is legal or not.

## 13.3 Circuit B: Canyon Switchbacks — intermediate, strategic choices

**Visual goal:** large zig-zag switchbacks, separated parallel road levels and two distinct alternate connectors. Do not allow parallel switchback segments to merge visually. Use desert/canyon scenery and cliffs beyond road boundaries; any overpass must have an explicit visual cue.

**Suggested topology:** a longer gentle route versus shorter steep/difficult route, two shortcuts with different fuel/time penalties, a signed dead-end lookout spur, fuel service at a strategic fork and a reachable nitro pickup. Create meaningful Speed versus Safety/Economy route differences. Ensure road geometry has sufficient clearance even when camera zooms out.

**Expected user experience:** user can compare a dangerous short route with a longer safe route, anticipate fuel cost and choose a strategy before racing.

## 13.4 Circuit C: Metro Grid — advanced, urban intersections

**Visual goal:** an uncluttered city-block grid with distinct orthogonal roads, traffic-like one-way indicators where applicable, intersections represented by real nodes, two shortcut alleys and one visible cul-de-sac. Buildings must not block the road layer or icons.

**Suggested topology:** multiple alternate paths, one-way restrictions only where graph validates, fuel/nitro at reachable junctions, dynamic closures that force meaningful detours, and enough checkpoint spacing to avoid ambiguous order. Distinguish a nonconnecting bridge from a genuine intersection. Use consistent visual road width and clear intersection turning cues.

**Expected user experience:** player can read junction choices quickly and understands which roads are open, blocked, one-way, shortcuts or dead ends.

## 13.5 Circuit generator, validator and route sanity tests

- Provide a deterministic hand-authored baseline for all three circuits; optional procedural generation must not replace the requirement to ship three validated playable maps.
- Validate node IDs, edge IDs, endpoint existence, nonnegative costs, difficulty range 1–5, checkpoint uniqueness/order, shortcut count, cycle, dead end, reachable services, lap boundary and full multi-lap feasibility.
- A checkpoint must be visited **in sequence**; a shortcut that physically bypasses CPk may be traversable but cannot magically award CPk. Explain whether a shortcut is strategically legal in current checkpoint state.
- Verify every displayed route references actual edge IDs in traversal order and that each edge's direction/status is legal. If the graph changes, invalidate stale routes or replan.
- Run automated checks that detect unintended geometric crossings, segments closer than road-clearance threshold, labels colliding at default zoom, icons placed outside roads and unrenderable paths. Allow explicitly annotated intentional overpasses with separate z-layer and clear styling.
- Export `docs/CIRCUIT_SPECIFICATIONS.md` including for each map: topology summary, screenshots, vertex/edge counts, checkpoints, shortcut IDs, fuel/nitro IDs, dead end, cycle witness, feasible route, preset differences, geometry validation and recovery scenarios.

# 14. ALGORITHM ENGINEERING CONTRACTS — EXPLAIN AND IMPLEMENT EACH ONE

All algorithms must be authored in pure Python, deterministic for fixed inputs, independently testable and shared between gameplay and Algorithm Lab. A visual step trace is an **instrumented view of the same implementation**, not a separate fake algorithm. Standardize a `Result` with input metadata, output, validity, metrics and optional steps; traces may be yielded lazily to avoid excessive memory. Prefer immutable snapshots for Lab playback.

## 14.1 BFS — why, how, expected output

**Purpose:** determine reachability and minimum number of edges in an unweighted graph; used to explain whether checkpoints/services can be reached, not to claim fastest or shortest-distance travel. **How:** FIFO queue, `visited`, `parent`, adjacency iteration respecting directedness and blocked roads. Mark visited when enqueued; reconstruct parent path if reachable. **Show:** frontier queue, visited order, highlighted tree, edge-count path, unreachable warning, counters for visited vertices and examined edges. **Tests:** empty/single vertex, cycles, disconnected graph, equal-hop alternatives, directed edges and the PDF's one-edge-vs-three-edge weighted counterexample. **Complexity:** O(V+E) time, O(V) auxiliary space.

## 14.2 DFS — why, how, expected output

**Purpose:** graph traversal, cycle discovery, connected components or directed reachability regions, dead-end identification, and bounded alternate simple paths. **How:** explicit stack or recursion with visited/discovery state; handle directed cycles with appropriate recursion-state/three-color logic, undirected cycles with parent logic; do not equate arbitrary low-degree vertex with the PDF's dead-end definition. For alternative paths, use visited-on-current-path backtracking and strict route-count/path-length limits. **Show:** active stack, discovery/finish sequence, cycle witness, dead-end reason, route variants. **Tests:** cycles, branching, directed, disconnected, dead end and bounded enumeration. **Complexity:** one traversal O(V+E); enumerating simple paths can be exponential.

## 14.3 Dijkstra — why, how, expected output

**Purpose:** find minimum cost route under nonnegative edge weights. **How:** binary min-heap keyed by `(cost, stable_tiebreaker, vertex/state)`, best-known distances, stale-entry skipping or documented decrease-key, parent reconstruction; ignore blocked roads and account for restrictions. The edge cost is exactly the documented normalized scalar objective. **Show:** settled nodes, heap, relaxations, cost table, final path, actual total distance/time/fuel and scalar cost. **Tests:** zero-cost edges, equal paths, unreachable, source=target, directed edges, blocked/restricted edges, reroute. **Complexity:** O((V+E) log V) for appropriate heap implementation; distinguish from the custom race-event heap requirement.

## 14.4 A* — why, how, expected output

**Purpose:** optimal heuristic-guided weighted routing. **How:** maintain g-score, admissible h, f=g+h, priority queue, parents; use proven lower-bound heuristic from Euclidean geometry and minimum cost per distance only when graph edge lengths/normalization justify it, else h=0. Document consistent versus inconsistent heuristic and reopening strategy. **Show:** open/closed, g/h/f, expansions, final path, optimal cost comparison with Dijkstra. **Tests:** compare with Dijkstra on many graphs and presets, including zero-cost edges, source=target, unreachable, equal cost and blocked roads. **Do not claim** A* always expands fewer vertices.

## 14.5 Ordered checkpoint route solver

**Purpose:** plan legal racing laps, not simply a direct source-to-finish path. **How:** model state as `(vertex, next_checkpoint_index[, lap])` or use carefully verified legs with explicit progress updates and invalid-order prevention. A graph walk can pass a later checkpoint before an earlier one; this must not incorrectly advance progress or declare success. Use shared `advance_checkpoint(state, entered_vertex)` in planner and race engine. After CP10, require valid finish/lap-boundary crossing; only then increment lap/reset next checkpoint. **Show:** ordered route, upcoming CP, progress, invalid shortcut warnings and a legal alternate. **Tests:** skip CP, revisit earlier CP, pass CP out of order, two laps, closure mid-leg, disconnected CP, finish too early.

## 14.6 DP / 0-1 knapsack — why, how, expected output

**Purpose:** optimize a finite set of optional pickup decisions under a documented integer detour budget. **How:** use `dp[i][b]`, explicit base cases, include/exclude recurrence, deterministic reconstruction and an item-used-once constraint. Define benefit units and cost units; never conflate time/fuel/nitro without a documented scalarization. Handle zero-cost items correctly. **Show:** table cells, current transition, selected pickups, optimal benefit, remaining budget, states evaluated. **Tests:** PDF A(6,30), B(5,24), C(5,24), budget 10 => optimum B+C=48 versus ratio-greedy A=30; two original counterexamples, brute-force small sets, zero-cost items, infeasible items. **Complexity:** O(mB) time/space with full table, pseudo-polynomial in B.

## 14.7 Optional refuelling DP — why, how, expected output

**Purpose:** decide station stops on a fixed route with discrete fuel states. **How:** use `dp[stop_index][fuel]` with starting fuel, tank cap, segment consumption, station availability, purchase bound up to 40 units per stop and positive-purchase fixed stop time. For every feasible purchase and next segment, update minimum additional stop time; reconstruct stops. Document fuel discretization and rounding safety. **Show:** feasible plan, refuel quantities, time penalty, tank trajectory, no-route/no-fuel explanation. **Tests:** insufficient fuel, station unavailable, full tank, fractional consumption scaling, infeasible final leg. **Complexity:** straightforward O(mC²) when enumerating purchases.

## 14.8 Greedy — why, how, expected output

**Purpose:** fast, explainable pickup heuristic and a teaching comparison against DP. **How:** take positive-benefit zero-cost items first; sort remaining by decreasing benefit/cost with deterministic ID tie-break; take item if it fits. **Show:** sorted ratios, accepted/rejected items, remaining budget, total benefit and optimality gap to DP. **Tests:** PDF counterexample plus two independently designed counterexamples, deterministic ties, empty and zero-cost inputs. **Never label** ratio-greedy optimal for 0/1 knapsack.

## 14.9 Backtracking — why, how, expected output

**Purpose:** satisfy placement/track constraints in advanced generation or a constraint-placement demonstration. **How:** enumerate candidate assignments, check partial constraints, prune invalid branches, backtrack and return valid configuration or bounded failure. Show invalid candidate rejection with reason. **Show:** decision tree, current choice, constraint result, pruning counter, valid track or unsatisfied constraint explanation. **Tests:** satisfiable, unsatisfiable, deterministic candidate order, invalid placement and valid generated circuit. **Complexity:** exponential worst case; explain pruning without claiming it changes worst-case class.

## 14.10 MST — why, how, expected output

**Purpose:** generate an undirected connected road backbone before adding loops/shortcuts. **How:** choose and implement **Prim OR Kruskal**, with actual edge weights, stable ties and proper connectedness checks. Kruskal uses sorted edges + union-find; Prim uses visited frontier + heap. Add extra edges after MST to introduce cycles and alternative routes, then validate directed reachability if one-way roads are added. **Show:** selected edges, running weight, rejected cycle edges, total MST weight, added non-MST edges. **Tests:** connected/disconnected graphs, duplicate weights, single vertex, known optimal MST. **Complexity:** Kruskal O(E log E) or Prim O(E log V) depending implementation.

## 14.11 Custom min-heap — why, how, expected output

**Purpose:** deterministic race-event scheduling and optional top-k retrieval. **How:** implement array-based binary heap with sift-up/down, push, peek, pop, comparator on `(trigger_time, priority, insertion_sequence)` and lazy cancellation. Keep separate event ID registry; never assume Python's built-in `heapq` alone fulfills the requirement for a custom heap implementation. **Show:** tree/array state, swaps, next event, pop order, cancelled entries, heap size and operation counts. **Tests:** simultaneous events, equal priorities, insertion sequence, cancellations, empty heap, expiry and stress comparisons against a sorted oracle. **Complexity:** push/pop O(log n), peek O(1).

## 14.12 Merge Sort, Quick Sort, Heap Sort — why, how, expected output

**Purpose:** championship ranking and performance comparison. **How:** use the exact same total comparator for all three; never compare preformatted strings. Merge Sort: split and stable merge, O(n log n), O(n) extra space. Quick Sort: document pivot/partition, average O(n log n), worst O(n²), use deterministic pivot/tie handling and a strategy for duplicates. Heap Sort: heapify/extract O(n log n), document in-place behavior and instability. **Show:** array/record cards, compare/swap/merge actions, current partition/heap, comparison counters, final identical leaderboard. **Tests:** empty, singleton, random, sorted, reverse, duplicates, all tie-breakers, final racer ID, stable ordering where applicable. **Top-k:** use heap with same comparator and verify first k equals full ranking.

# 15. RACING ENGINE IMPLEMENTATION DETAILS — SIMULATION, INPUT, CAMERAS, MINIMAP

## 15.1 Simulation and interpolation

Use fixed simulation time step (for example 1/60s or 1/30s) with accumulated real-time delta and a capped catch-up policy. Rendering may interpolate between simulation states for smooth animation. Record a deterministic seed/event schedule and stable ordering of updates. Separate simulation elapsed time from wall-clock/render FPS; pause must freeze simulation and timers consistently. The graph is authoritative: car state should include edge ID, edge progress (0..1), previous/current vertex, heading, velocity/speed modifier, lap and checkpoint progress. Draw the sprite at the road-polyline interpolated position; orient along tangent. Do not jump across disconnected nodes, allow edge progress outside bounds, or start an edge without fuel/legality checks.

At a junction, only offer outgoing edges allowed by direction/status and checkpoint policy. When an event closes an edge before entry, recalculate choices. For closure while a car is already on an edge, define a deterministic safety rule (e.g. complete current edge if explicitly permitted, or stop at safe boundary and wait); apply it consistently and document. Never teleport a car to a graph node without a defined recovery mechanic.

## 15.2 Player input contract and meaningful decisions

Provide an on-screen controls legend and remappable/default keyboard bindings. Suggested defaults (verify conflicts): W/Up accelerate, S/Down brake/coast, Shift sprint, Space nitro, A/D or Left/Right choose upcoming fork, R request reroute, F refuel when at station, C cycle camera, M expand minimap, P/Escape pause/back, Enter confirm a highlighted choice. The hybrid movement model should be explicitly explained in How to Play: cars stay on graph roads, the user controls speed/resource/route decisions. Do not imply free steering if it is not implemented.

**Sprint:** define speed multiplier, maximum duration, cooldown and fuel/heat cost; sprint is **not** a replacement for PDF nitro. Display cooldown and prevent repeated key press from restarting it. Ensure AI fairness rules and difficulty balancing are documented; if sprint is player-only, explain why and verify racing remains coherent. **Nitro:** one charge per activation, up to three, suggested 1.5× speed for four simulation seconds, 2× fuel consumption while active; prevent activation with no charges and avoid negative fuel. Fuel consumption should be applied consistently over partial edges if nitro begins/ends mid-edge. **Refuel:** only at active reachable station, up to 40 units per stop, cap tank at 100, apply stop time once for positive purchase, allow cancel before confirmation. **Route decisions:** show distance/time/fuel/risk and whether the choice skips a checkpoint; no unreasoned "best" labels.

**Feedback:** show speed changes, fuel cost, nitro remaining, sprint timer, upcoming checkpoint, available exits and why unavailable options are disabled. Pause panel should include Resume, Restart (with confirmation), Controls, Settings, Main Menu (with confirmation when progress would be lost).

## 15.3 AI contract

- AI1 **Navigator**: fixed baseline route, deterministic fallback detour, refuel at first eligible station below 25% fuel.
- AI2 **Shortcut Specialist**: prefer designated legal shortcuts, fall back to main route if closed/invalid, refuel at first eligible station below 25% fuel.
- AI3 **Distance Optimizer**: shortest-distance legal checkpoint-aware route and dynamic reroute; select nearest reachable on-route station when below 25% fuel.
- All AI must obey fuel, nitro, speed, checkpoint, lap and event rules. If AI uses nitro/sprint, give it documented deterministic activation conditions and the same physics/resource effects as the player. If a car cannot proceed, apply shared recovery/DNF policy; do not make AI immune to blocked roads.
- Add tests with fixed seed and schedule verifying byte-for-byte or structurally equal finish orders, routes and event logs across repeated runs.

## 15.4 Camera modes

**Follow camera:** smoothly tracks player at usable zoom, with world bounds and readable upcoming junction. **Tactical camera:** shows next fork and surrounding alternate roads. **Full-track camera:** fits all road geometry into the available world viewport while keeping HUD separate. **Optional free camera:** paused inspection with controlled pan/zoom. Switching modes must not change simulation, route choices or physics. Correctly convert mouse coordinates from screen to world for hit testing; ensure HUD stays screen-fixed.

## 15.5 Minimap bottom-left — implementation contract

Reserve a bottom-left HUD rectangle with margin, dark translucent panel, visible border, optional expand button and fixed whole-circuit bounds. Use one world-to-minimap affine transform computed from circuit bounding box and aspect ratio; preserve proportions and avoid stretch. Draw **all** graph roads faintly, route bright, blocked segments red, start/finish, next checkpoint, four cars as distinguishable icons (not only colors), player highlight, AI legend and a main-camera viewport rectangle when practical. Update car markers every simulation frame or at a documented rate, with no stale cached coordinates. When camera changes, minimap still displays the entire circuit. If a car finishes/DNFs, retain a clear final marker/status rather than making it vanish. Test corners, overlaps, zoom levels, all four positions and circuit switching.

## 15.6 Event scheduler and overlapping effects

Implement priority table from PDF exactly: road blockage 1; shortcut open/close 2; oil spill 3 (~20s); speed restriction 4 (~15s); fuel station availability 5 (~30s); nitro booster 6 (~25s or until collected). Store event ID, target, start, duration, priority, sequence, cancelled and effect IDs. Apply same-time events in heap order before route recalculation. Track active effects independently; recompute effective speed/difficulty/status from all active effects rather than restoring an old snapshot on expiration. Handle duplicate closure/open commands, missing targets, expired pickups, cancellations and stale heap entries safely. Maintain concise event feed, map alerts and replay log. Use simulation time, not frame count, for expirations.

## 15.7 Finish and DNF contract

Complete a lap only after all checkpoints CP1..CP10 were visited in order and the racer crosses lap boundary. The final finish event must be idempotent. Race result records must include racer ID, finish status, time, position, fastest lap and relevant statistics. For finishers sort by finish time then racer ID. If race time limit is configured, sort unfinished by laps completed, checkpoints completed, elapsed time, racer ID per PDF, with documented points policy. DNF reasons must be visible: fuel exhausted, unrecoverable closure, time limit or other validated cause. Verify no race gets stuck indefinitely: provide timeout/recovery policy.

# 16. ALGORITHM LAB — SCREEN-BY-SCREEN PROFESSIONAL INTERACTION DESIGN

**Goal:** a nontechnical first-time user should understand *what the algorithm is solving*, *what each step means*, *why the result is correct*, *what it costs*, and *where the game uses it*.

**Layout:** left category sidebar with search and selected algorithm; center visualization (graph/array/DP grid/tree/heap) with legend and zoom; right explanation panel with "What it does", "Input", "Current step", "Pseudocode", "Variables", "Counters", "Complexity" and "Used in the game"; bottom playback bar. Keep controls reachable at 1280x720; scroll explanations, not the whole viewport. Use visual state colors consistently (unvisited, frontier, current, completed, rejected, final) plus text/icon indicators for accessibility.

**Common actions and expected results:**

| Action | Behavior | Required feedback |
|---|---|---|
| Choose algorithm | Load relevant sample or current circuit; reset old trace | Title, purpose, input constraints |
| Choose dataset | Validate graph/items/racers/event list | Dataset name and size |
| Start/Play | Advance steps at controlled speed | Highlighted state and step counter |
| Pause | Freeze trace only | Paused indicator |
| Next | Advance exactly one meaningful algorithm step | Updated narration and counters |
| Previous | Restore previous snapshot, if supported | Exact prior state, not reverse guessing |
| Reset | Return to initial trace state | Counters zeroed and original input restored |
| Run to End | Compute final result with bounded work | Correct output and elapsed compute time |
| Compare | Run two appropriate algorithms on identical input | Side-by-side correctness and counters |
| Export | Save actual results to CSV/JSON | Filename and location or clear error |
| Use Current Circuit | Load graph from selected game circuit | Circuit ID, graph stats and route context |
| Back | Return to invoking view | Previous mode and session preserved |

**Algorithm-specific visual patterns:** BFS queue with colored wavefront; DFS stack/tree and cycle witness; Dijkstra distance labels and relaxation arrows; A* g/h/f cards; DP editable item table and animated grid; Greedy sorted ratios and failure example; Backtracking branching choice tree and pruned nodes; MST candidate/accepted edges; event heap tree and array with sift animations; Merge Sort partition/merge bars; Quick Sort pivot/partition bars; Heap Sort heap tree and array. Render actual values, not arbitrary animation.

**Education quality:** show accurate complexity with assumptions, explain BFS edge count versus weighted distance, A* heuristic safety, DP pseudo-polynomial budget dependence, Greedy counterexamples, MST not creating cycles by itself, heap tie determinism, and sorting comparator ties. Provide a small "Try this" exercise per algorithm (e.g. block one edge, predict next vertex, alter budget) with a reveal result computed by the same code. This is an optional usability enhancement; do not sacrifice mandatory functionality for exercises.

**Expected deliverable:** all 12 families have functional demonstrations, step traces, tests, explanatory text, exports and links to the corresponding gameplay features. No catalog entry may be a "Coming soon" stub at Phase 4 exit.

# 17. CHAMPIONSHIP, SAVE DATA AND LEADERBOARD CONTRACTS

**Championship state machine:** `NOT_STARTED → ACTIVE → RACE_IN_PROGRESS → RACE_FINISHED → AWAITING_NEXT_RACE → COMPLETED`. Ensure transitions are explicit and idempotent. New Championship asks before replacing an active save; Continue resumes last safe checkpoint, not an undefined partial state. Quick Race never changes championship state.

**Points:** positions 1..10 award `[25,18,15,12,10,8,6,4,2,1]`; apply only once per unique race result ID. Define bonus points (if any) before testing; default to none unless the PDF or user demands otherwise. Tie order: points high, wins high, sum finishing positions low, best fastest lap low, racer ID low. Represent missing fastest lap/DNF with a documented sentinel that sorts consistently. All three sorting implementations and top-k use the identical comparator.

**UI:** podium top three, leaderboard table, current race card, points gained, wins, fastest lap, cumulative history and upcoming circuit; sort method selector, top-k selector, clear labels explaining ties, replay/next/menu controls. Highlight player row without hiding AI details. Results panel shows reasons for DNF and points policy. Final champion screen explains winner and tie-break if applicable.

**Persistence:** versioned JSON schema, atomic write (temporary file then replace), validation on load, graceful recovery from corrupted/older files, no secrets. Persist championship identity, race order, completed result IDs, scores, session preferences and replay seed; avoid serializing Arcade sprites/windows or raw Python object graphs. Add migration for prior save versions if applicable. Test kill/restart between races, duplicate award prevention and invalid saves.

# 18. AUTOMATED TESTING — EXACT CASES, TOOLS AND EXPECTED EVIDENCE

## 18.1 Testing pyramid

1. **Pure unit tests:** graph, validators, geometry, algorithms, costs, resources, event heap, comparator and persistence; fast and deterministic.
2. **Integration tests:** planner→session→race→results→dashboard, closures and rerouting, checkpoint/lap progression, multi-circuit championship and save/resume.
3. **UI interaction tests:** click/keyboard navigation, modal isolation, zoom/pan, algorithm playback, camera switching, minimap, screenshot checks at three resolutions.
4. **Packaging smoke test:** installed executable or documented Python entry point launches, loads assets and completes a minimal flow.
5. **Benchmark verification:** reproducible experiment runner, schema checks, nonempty CSV and charts, correct input sizes and no rendering in timed regions.

**Playwright caution:** Arcade is a desktop OpenGL app; Playwright does not automatically control its native window. Use Playwright only if an actual browser-based component exists. For native Arcade use input-injection, Arcade test hooks, Xvfb/virtual display when supported, or desktop automation tools such as PyAutoGUI if installed. Detect environment support and report limitations; never claim unsupported tools ran.

## 18.2 Mandatory test matrix

| Area | Scenario | Expected invariant |
|---|---|---|
| Graph | disconnected, directed, cycle, dead end, single node | no crash; correct reachability |
| Geometry | accidental crossings, road clearance, label collision | invalid layout flagged; legible screenshot |
| Circuits | three maps, 10+ CP, 2+ shortcuts | validators pass, route exists |
| BFS | one long edge vs three short edges | selects minimum hops, not weighted length |
| DFS | cycle/dead-end, path cap | correct detection, bounded search |
| Dijkstra | zero/equal costs, blocked edge | optimal legal cost |
| A* | multiple presets, heuristic bounds | cost equals Dijkstra when conditions hold |
| Checkpoints | skip CP, lap boundary early | no false checkpoint/lap credit |
| Resources | insufficient fuel, station cap, nitro mid-edge | never negative fuel; legal recovery/DNF |
| DP/Greedy | PDF budget-10 case, two new cases | DP=48 vs Greedy=30 in PDF case |
| Heap/events | equal time/priority, cancellation, overlap | `(time,priority,sequence)` order; no lost effects |
| AI | same inputs repeated | identical deterministic decisions/results |
| Sprint | cooldown, fuel cost, hold key | no unlimited activation |
| Cameras | follow/tactical/full, resize | correct transforms and UI |
| Minimap | all cars, every circuit, closures | world-to-map positions match |
| Ranking | points/wins/positions/lap/ID ties | all sorters and top-k identical |
| Persistence | restart, duplicate results, bad JSON | no double points; graceful failure |
| Navigation | every button/modal/back/escape | correct view, preserved state |
| GUI | 1280x720, 1600x900, 1920x1080 | no clipping/overlap; readable |
| End-to-end | three races, full championship | final champion and valid scores |

## 18.3 Screenshot and visual-review protocol

- Capture real Arcade window screenshots with consistent resolution and scene state. Store a small selected set under `docs/screenshots/` only if repository size policy permits; otherwise store external/local evidence with links and metadata.
- Required views: Main Menu; three Explorer maps fit-to-screen; zoomed intersections; each route algorithm overlay; route comparison; resource planner; race follow/tactical/full cameras; minimap showing four racers; blocked road/reroute; race results; championship dashboard; final champion; Lab overview and each algorithm category.
- For every screenshot, explicitly inspect: road crossings and accidental merging, readable CP labels, panel clipping, minimap coverage, button states, overlay accuracy, contrast, font scaling and alignment. Log pass/fail and fix failures before closing phase.
- Pixel-diff screenshots can flag regressions but do not replace visual reasoning; account for nondeterministic rendering/font/platform differences.

## 18.4 Test failure workflow

For each bug, write reproducible steps and expected vs actual behavior; add failing test where feasible; fix root cause rather than hiding UI symptom; rerun targeted test and full regression; recapture screenshot if visual; update issue/PR evidence. Do not silence exceptions, disable tests, use `pytest -k` as a substitute for full suite, or skip tests without recording why.

# 19. GITHUB OPERATIONS — COMMAND EXAMPLES AND PR/RELEASE QUALITY

**Repository:** `https://github.com/Bilalmughal-07/2D_SmartRacingChampionShip.git`.

**Before each phase:** ensure local working tree and branch history are understood. Verify correct remote with `git remote -v`; verify access with `gh auth status`; determine default branch using `gh repo view --json defaultBranchRef` when authenticated. Fetch safely. If repository is empty, initialize only with legitimate authorization and an intentional initial commit; if existing remote history differs, reconcile without force-pushing.

**Branch/commit example (adapt to real state):**

```bash
# These are examples; inspect state first and do not blindly run.
git switch <default-branch>
git pull --ff-only origin <default-branch>
git switch -c feat/phase-02-track-explorer
python -m pytest -q
git add <specific-files>
git commit -m "feat(explorer): implement checkpoint-aware routing and readable maps" \
  -m "Add three validated circuits, graph-linked rendering, route metrics and tests."
git push -u origin feat/phase-02-track-explorer
gh pr create --base <default-branch> --head feat/phase-02-track-explorer \
  --title "feat: Phase 2 — interactive track explorer and routing" \
  --body-file docs/pr/phase-02.md
```

**PR description format:** objective; PDF requirements with section references; screenshots; user journeys verified; test commands/results; algorithm correctness; circuit validator report; accessibility; known limitations; risk/rollback; changed modules; reviewer checklist. Use a conventional commit for each coherent slice (feature, fix, test, docs, refactor). Avoid one huge unexplained commit for all seven phases.

**Review/merge:** inspect `gh pr checks <number> --watch` and `gh pr view <number> --json state,mergeable,reviewDecision,statusCheckRollup`. If CI fails, fix and push. If self-merge is authorized and repository rules allow it, use `gh pr merge <number> --squash --delete-branch` and verify `MERGED` state. GitHub marks merged PRs closed automatically; **do not close an unmerged PR to simulate completion**. If human approval required, leave PR open, document blocker and work on a safely based dependent branch. Never bypass branch protection, fake a review or disable CI to make merging possible.

**After merge:** fetch/fast-forward default branch, run smoke tests, update `docs/OVERNIGHT_PROGRESS.md` with merge SHA and PR URL, and continue. If `gh` is unavailable, preserve local commits and create `docs/GITHUB_PENDING_ACTIONS.md` with exact commands/PR bodies for an authorized person. Do not claim GitHub work occurred when only local commands succeeded.

**Final repository quality:** README badges only for real workflows, `.gitignore` for `.venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `dist/`, `build/`, generated logs and temporary exports; `LICENSE` only when owner approves license; `CONTRIBUTING.md` optional; no credentials; small assets with license records; CI status visible; releases tagged only when tests and permissions permit.

# 20. REQUIRED OUTPUT ARTIFACTS AND EXPECTED CONTENT

At the end of each phase, produce and verify the following **real** outputs:

| Phase | Actual artifact | Acceptance evidence |
|---|---|---|
| 1 | Working Arcade Main Menu and navigation | screenshots, all-button test, keyboard/modal test |
| 2 | Three validated JSON circuits and Explorer | geometry report, algorithms, route comparisons, screenshots |
| 3 | Playable racing engine and HUD | full-race replay, all camera/minimap tests, fuel/event tests |
| 4 | Complete 12-family Algorithm Lab | trace-output agreement, playback tests, exports, screenshots |
| 5 | Championship Dashboard and save/resume | 3-race standings test, comparator equality, persistence tests |
| 6 | Five experiment runners and results | raw CSVs, charts, methods, reproducibility and QA report |
| 7 | README, technical report, executable, submission package | end-to-end smoke test, requirements traceability, release audit |

**Suggested files:**

```text
README.md
requirements.txt  (or pyproject.toml with reproducible lock strategy)
main.py
core/{game_session,navigation,track_validator,route_planner,resources,save_data}.py
algorithms/{bfs,dfs,dijkstra,astar,dp,greedy,backtracking,mst,event_heap,merge_sort,quick_sort,heap_sort}.py
game/{race_engine,racer,ai_controller,event_manager,championship}.py
rendering/{track_renderer,graph_overlay,car_renderer,camera_controller,minimap,effects}.py
ui/views/{main_menu,circuit_selection,track_explorer,racing_view,algorithm_lab,championship_dashboard}.py
ui/components/{buttons,dialogs,route_panel,resource_panel,hud,lab_controls}.py
tracks/{emerald_loop,canyon_switchbacks,metro_grid}.json
assets/{backgrounds,cars,roads,environments,icons,fonts}/
experiments/{run_all,experiment_1,experiment_2,experiment_3,experiment_4,experiment_5}.py
tests/{unit,integration,ui}/
docs/{IMPLEMENTATION_PLAN,REQUIREMENTS_TRACEABILITY,OVERNIGHT_PROGRESS,TEST_MATRIX,CIRCUIT_SPECIFICATIONS,QA_EVIDENCE,GITHUB_PENDING_ACTIONS}.md
.github/workflows/ci.yml
```

Adapt filenames to actual repository; never delete a working module solely to match the suggested tree. Do not commit generated `dist/` or `.venv/` unless a documented delivery process requires a separate release artifact.

**Technical report:** preserve the PDF's structure: title/course/team; introduction; architecture/flow; graph/data/cost normalization; algorithms with pseudocode/correctness/complexity; integration; testing; five experimental studies with actual measurements/charts; limitations/advanced challenges; conclusion/references. Do not invent team names, registration IDs, results or screenshots. Submission ZIP name must use actual group registration numbers/section provided by user.

# 21. FINAL AUDIT — DO NOT CLAIM COMPLETION UNTIL THESE QUESTIONS HAVE ANSWERS

1. Can a fresh user install and launch the Arcade app using README instructions?
2. Does every Main Menu button lead to a functional destination?
3. Are all three circuits graph-valid **and** visually unambiguous at standard resolutions?
4. Are every checkpoint, shortcut, dead end, intersection, fuel station and nitro pickup discoverable and correctly labeled?
5. Do BFS/DFS/Dijkstra/A* return correct results and share the Lab's implementations?
6. Are weighted presets mathematically documented, and do real route choices differ on at least one map?
7. Can the player meaningfully decide speed, sprint, nitro, fork, shortcut, refuel and reroute?
8. Are all four cars visibly on-road, and do all camera modes and bottom-left minimap show correct locations?
9. Are events ordered and expired deterministically, with safe rerouting and no overlapping-effect bug?
10. Can the player finish valid multi-lap races, see DNF reasons and progress across all three championship circuits?
11. Does the Algorithm Lab fully demonstrate all 12 required families with actual steps and counters?
12. Are championship standings, tie-breaks, Merge/Quick/Heap sorts and top-k identical and persistent?
13. Are all five experiments reproducible with real raw data, charts and correctness checks?
14. Were GUI screenshots actually captured and reviewed, not merely generated as assets?
15. Do pytest, integration tests, packaging smoke test and supported UI automation pass?
16. Does each phase have a real commit and PR URL/status, or an explicit permission blocker with saved local work?
17. Are all mandatory PDF requirements mapped to implementation, tests and evidence?
18. Are the final README, technical report, build and submission materials complete without fabricated personal details?

**Final deliverable report:** one concise table with Phase, Status, Commit SHA, PR URL, PR State, Tests, Screenshots, Remaining Issues. Add precise commands for any pending approval, PR merge, build or submission. Do not state "all done" unless the actual code, tests and GitHub state support that statement.

# END OF CODEX PROMPT
