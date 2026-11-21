from __future__ import annotations

from smart_racing.arcade_ui.app import MainMenuView, TrackExplorerView
from smart_racing.arcade_ui.lab_view import CATALOG
from smart_racing.arcade_ui.session import DEFAULT_SETTINGS, GameSession
from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.track_loader import load_tracks


def test_arcade_menu_has_required_centered_navigation_order():
    assert [label for label, _ in MainMenuView.MENU_ITEMS] == [
        "START CHAMPIONSHIP",
        "QUICK RACE",
        "TRACK EXPLORER",
        "ALGORITHM LAB",
        "HOW TO PLAY",
        "SETTINGS",
        "EXIT GAME",
    ]


def test_arcade_frontend_has_no_pygame_imports():
    from pathlib import Path

    root = Path(__file__).parents[2] / "src" / "smart_racing" / "arcade_ui"
    assert not any(
        line.strip().startswith(("import pygame", "from pygame"))
        for path in root.glob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def test_game_session_persists_mode_selection_and_settings(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    assert session.settings["width"] == DEFAULT_SETTINGS["width"]
    session.select_quick_race("circuit_03")
    session.settings["music_volume"] = 0.25
    session.save_settings()

    loaded = GameSession.create(tracks, root=tmp_path)
    assert loaded.selected_track_id == "circuit_03"
    assert loaded.mode == "quick"
    assert loaded.settings["music_volume"] == 0.25


def test_game_session_starts_and_continues_championship_in_order(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    session.start_new_championship()
    assert session.has_saved_championship
    assert session.selected_track_id == tracks[0].id
    session.championship_index = 1
    session.save_state()

    loaded = GameSession.create(tracks, root=tmp_path)
    loaded.continue_championship()
    assert loaded.mode == "championship"
    assert loaded.selected_track_id == tracks[1].id


def test_route_configuration_transfers_from_explorer_to_race_session(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    route_plan = {
        "track_id": "circuit_02",
        "algorithm": "A*",
        "preset": "safety",
        "source": 0,
        "destination": 15,
        "checkpoint_aware": True,
        "path": [0, 1, 2],
        "edge_ids": [0, 1],
        "metrics": {"distance": 12.0, "weighted_cost": 4.5},
        "fuel_feasible": True,
        "required_refuelling_stops": [],
    }
    session.set_route_plan(route_plan)
    loaded = GameSession.create(tracks, root=tmp_path)
    assert loaded.selected_track_id == "circuit_02"
    assert loaded.selected_algorithm == "A*"
    assert loaded.route_plan == route_plan


def test_quick_circuit_switch_clears_stale_route_configuration(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    session.set_route_plan({"track_id": "circuit_01", "algorithm": "Dijkstra"})
    session.select_quick_race("circuit_03")
    assert session.selected_track_id == "circuit_03"
    assert session.route_plan is None


def test_explorer_maps_display_algorithm_labels_to_service_keys():
    view = object.__new__(TrackExplorerView)
    view.algorithm = "A*"
    assert view.planner_algorithm == "astar"
    view.algorithm = "Dijkstra"
    assert view.planner_algorithm == "dijkstra"


def test_arcade_phase_views_expose_all_required_algorithm_families():
    assert len(CATALOG) == 12
    assert [name for name, *_ in CATALOG] == [
        "BFS",
        "DFS",
        "Dijkstra",
        "A*",
        "0/1 Knapsack DP",
        "Refuelling DP",
        "Greedy",
        "Backtracking",
        "Kruskal MST",
        "Event Min-Heap",
        "Merge Sort",
        "Quick/Heap Sort",
    ]


def test_session_records_championship_races_once_and_advances_order(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    session.start_new_championship()
    results = RaceEngine(tracks[0]).run()

    assert session.record_race_results(tracks[0].id, results)
    assert not session.record_race_results(tracks[0].id, results)
    assert session.championship_index == 1
    assert session.championship_status == "AWAITING_NEXT_RACE"
    assert session.selected_track_id == tracks[1].id
    assert len(session.race_history) == 1
    assert session.championship_points["Player"] >= 0
