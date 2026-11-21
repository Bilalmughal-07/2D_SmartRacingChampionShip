# Track Explorer Button and State Audit

This audit covers the functional-overhaul branch. Each control is wired to a real callback or is an intentional state guard; no decorative control is presented as an enabled action.

| Control | Real action | State/guard | Evidence |
|---|---|---|---|
| BACK | Returns to the recorded menu, circuit selection, or dashboard | Uses `session.explorer_return` | `go_menu()` + route roundtrip tests |
| Previous / Next circuit | Loads the adjacent authoritative circuit | Locked during championship mode; clears route/resource decisions | `switch_circuit()` and frontend test |
| RESET VIEW | Resets zoom, pan, and panel scroll | Preserves route/session plan | `reset_view()` |
| ALGORITHM LAB | Opens the shared Lab with Explorer context | Restores algorithm, preset, mode, and endpoints on return | `open_lab()` + context persistence test |
| FREE EXPLORATION | Enables arbitrary source/destination study | A free route cannot start a race | `set_explorer_mode()` / `start_race()` guard |
| FULL RACE PLAN | Enables START → CP1…CP10 → FINISH planning | Source and destination are fixed to official endpoints | checkpoint modal and route validation |
| BFS / DFS / Dijkstra / A* | Selects the real algorithm family | Marks the current route stale | `set_algorithm()` and route counters |
| Balanced / Speed / Economy / Safety | Selects weighted objective preset | Disabled logically for BFS/DFS with explanatory status | `set_preset()` |
| SOURCE / DESTINATION | Arms click selection in Free Exploration | Guarded in Full Race Plan | `set_selection_mode()` and map click handler |
| VIEW CHECKPOINT SEQUENCE | Shows mandatory ordered targets | Full-plan information only | checkpoint modal screenshot |
| CALCULATE ROUTE | Runs the shared RoutePlanner on the current graph copy | Reports invalid/unreachable/stale state | route tests and Explorer frame |
| COMPARE ROUTES | Computes distinct candidates from the same graph/objective | Deduplicates identical paths | comparison modal screenshot |
| PLAN RESOURCES | Runs fuel feasibility plus Nitro DP/Greedy planning | Does not silently alter race rules | resource modal screenshot |
| ROUTE STATUS | Explains current route state | Distinguishes no route, stale, invalid, feasible, infeasible | `show_route_status()` |
| ROAD EVENT PREVIEW | Opens road selection and event actions | Events apply to Explorer graph copy only | event modal screenshot |
| CLOSE / REOPEN / RESTRICT ROAD | Mutates the selected edge status | Every mutation invalidates the prior route | `apply_event()` and blocked-edge test |
| UNDO LAST / RESET EVENTS | Restores prior or canonical edge statuses | Rebuilds route validity state | event history methods |
| RECALCULATE | Replans after a road event | Uses the modified graph revision | `recalculate_from_event_modal()` |
| REVIEW / START RACE | Validates the current plan and opens review | Free mode, stale route, invalid graph, wrong endpoint, and infeasible fuel are rejected | `start_race()` |
| ACCEPT PLAN | Stores the reviewed resource decision | Required before race confirmation when resources are not yet accepted | resource modal screenshot |
| EDIT PLAN | Closes confirmation without starting | Preserves Explorer state | start confirmation screenshot |
| CONFIRM & START RACE | Transfers circuit, path, edge IDs, metrics, and resource plan | Opens the shared Arcade Racing view only after validation | route handoff test |

## Visual evidence

- Base states: `docs/screenshots/arcade_explorer_overhaul_1280.png`, `arcade_explorer_overhaul_1600.png`, `arcade_explorer_overhaul_1920.png`.
- Modal states: `arcade_explorer_compare_1280.png`, `arcade_explorer_resources_1280.png`, `arcade_explorer_events_1280.png`, and `arcade_explorer_start_confirm_1280.png`.
