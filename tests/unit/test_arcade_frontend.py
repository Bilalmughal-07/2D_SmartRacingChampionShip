from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

from smart_racing.arcade_ui.app import MainMenuView, TrackExplorerView
from smart_racing.arcade_ui.comparison_view import (
    comparison_algorithms,
    validate_comparison_selection,
)
from smart_racing.arcade_ui.lab_view import CATALOG
from smart_racing.arcade_ui.session import DEFAULT_SETTINGS, GameSession
from smart_racing.config import DEFAULT_CONFIG
from smart_racing.model.graph import EdgeStatus
from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.route_planner import RoutePlanner
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
    assert session.explorer_mode == "full_race"
    assert session.explorer_return == "circuit_selection"


def test_explorer_context_round_trips_for_algorithm_lab_return(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    session.explorer_mode = "free"
    session.explorer_return = "explorer"
    session.explorer_context = {"track_id": "circuit_02", "algorithm": "A*", "source": 11, "destination": 13}
    session.save_state()
    loaded = GameSession.create(tracks, root=tmp_path)
    assert loaded.explorer_mode == "free"
    assert loaded.explorer_return == "explorer"
    assert loaded.explorer_context["algorithm"] == "A*"


def test_explorer_maps_display_algorithm_labels_to_service_keys():
    view = object.__new__(TrackExplorerView)
    view.algorithm = "A*"
    assert view.planner_algorithm == "astar"
    view.algorithm = "Dijkstra"
    assert view.planner_algorithm == "dijkstra"


def test_explorer_comparison_keeps_all_four_weighted_preset_cards():
    tracks = load_tracks()
    track = tracks[0]
    view = object.__new__(TrackExplorerView)
    view.session = SimpleNamespace(tracks=tracks, selected_algorithm="Dijkstra")
    view.track_index = 0
    view.algorithm = "Dijkstra"
    view.preset = "balanced"
    view.comparison_selected_preset = "balanced"
    view.explorer_mode = "full_race"
    view.source_id = track.start_id
    view.destination_id = track.finish_id
    view.graph = deepcopy(track.graph())
    view.route_result = RoutePlanner(track, "balanced").plan_route(
        track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True
    )
    view.route_revision = 0
    view.graph_revision = 0
    view.route_state = "PLAN_FEASIBLE"
    view.comparison = {}
    view.comparison_candidates = []
    view.modal = None
    view.status_message = ""
    view.status_color = None
    view.rebuild_ui = lambda: None

    view.compare_routes()

    assert [label for label, _report in view.comparison_candidates] == [
        "Balanced Route",
        "Speed Route",
        "Economy Route",
        "Safety Route",
    ]
    assert [report["preset"] for _label, report in view.comparison_candidates] == [
        "balanced",
        "speed",
        "economy",
        "safety",
    ]
    assert all(report["metrics"]["valid"] for _label, report in view.comparison_candidates)

    view.close_modal = lambda: None
    view.select_comparison(2)
    assert view.preset == "economy"
    assert view.route_result["preset"] == "economy"


def test_explorer_road_event_preview_does_not_record_noop_status_change():
    track = load_tracks()[0]
    view = object.__new__(TrackExplorerView)
    view.graph = deepcopy(track.graph())
    view.event_edge_id = 0
    view.event_history = []
    view.graph_revision = 1
    view.status_message = ""
    view.status_color = None
    view._mark_route_stale = lambda _message: None
    view.rebuild_ui = lambda: None

    view.apply_event(EdgeStatus.OPEN)

    assert view.graph.edges[0].status == EdgeStatus.OPEN
    assert view.event_history == []
    assert view.graph_revision == 1


def test_explorer_road_event_restriction_changes_cost_and_undo_restores():
    track = load_tracks()[0]
    view = object.__new__(TrackExplorerView)
    view.graph = deepcopy(track.graph())
    view.event_edge_id = 0
    view.event_history = []
    view.graph_revision = 1
    view.status_message = ""
    view.status_color = None
    view._mark_route_stale = lambda _message: None
    view.rebuild_ui = lambda: None

    edge = view.graph.edges[0]
    original_time = edge.effective_time()
    original_difficulty = edge.effective_difficulty()
    view.apply_event(EdgeStatus.RESTRICTED)

    assert edge.status == EdgeStatus.RESTRICTED
    assert edge.effective_time() > original_time
    assert edge.effective_difficulty() > original_difficulty
    assert view.event_history == [(0, EdgeStatus.OPEN, None)]

    view.undo_event()

    assert edge.status == EdgeStatus.OPEN
    assert "explorer_restriction" not in edge.effects
    assert edge.effective_time() == original_time
    assert edge.effective_difficulty() == original_difficulty
    assert view.event_history == []


def test_explorer_close_event_preview_restores_canonical_graph_and_route():
    track = load_tracks()[0]
    original_graph = deepcopy(track.graph())
    view = object.__new__(TrackExplorerView)
    view.graph = deepcopy(original_graph)
    view.graph.edges[0].status = EdgeStatus.BLOCKED
    view.event_original_graph = original_graph
    expected_route = {"path": [track.start_id, track.finish_id]}
    view.event_original_route = expected_route
    view.event_original_route_state = "ROUTE_READY"
    view.event_original_resource_accepted = True
    view.event_history = [(0, EdgeStatus.OPEN, None)]
    view.event_edge_id = 0
    view.event_candidate_ids = [0]
    view.event_candidate_index = 0
    view.graph_revision = 3
    view.route_result = {"path": [track.start_id]}
    view.event_after_route = {"path": [track.finish_id]}
    view.resource_accepted = False
    view.route_revision = 2
    view.route_state = "ROUTE_STALE"
    view.modal = "events"
    view.status_message = ""
    view.status_color = None
    view.rebuild_ui = lambda: None

    view.close_event_preview()

    assert view.modal is None
    assert view.graph.edges[0].status == original_graph.edges[0].status
    assert view.route_result == expected_route
    assert view.resource_accepted is True
    assert view.event_history == []


def test_explorer_next_road_cycles_all_circuit_edges_in_id_order_with_wraparound():
    for track in load_tracks():
        view = object.__new__(TrackExplorerView)
        view.graph = deepcopy(track.graph())
        view.event_edge_id = min(view.graph.edges)
        view.event_candidate_ids = [view.event_edge_id]
        view.event_candidate_index = 0
        view.status_message = ""
        view.status_color = None
        view.zoom = 1.8
        view.pan = [23.0, -17.0]
        view.event_history = []
        view.graph_revision = 7
        view.route_result = {"path": [track.start_id, track.finish_id]}
        view.rebuild_ui = lambda: None
        original_statuses = {edge_id: edge.status for edge_id, edge in view.graph.edges.items()}

        road_ids = sorted(view.graph.edges)
        for expected_edge_id in road_ids[1:] + road_ids[:1]:
            view.cycle_event_edge()
            assert view.event_edge_id == expected_edge_id
            assert view.event_candidate_ids == [expected_edge_id]
            assert view.event_candidate_index == 0

        assert {edge_id: edge.status for edge_id, edge in view.graph.edges.items()} == original_statuses
        assert view.event_history == []
        assert view.graph_revision == 7
        assert view.route_result == {"path": [track.start_id, track.finish_id]}
        assert view.zoom == 1.8
        assert view.pan == [23.0, -17.0]


def test_arcade_phase_views_expose_all_required_algorithm_families():
    assert len(CATALOG) == 13
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
        "Quick Sort",
        "Heap Sort",
    ]


def test_manual_algorithm_comparison_selection_is_independent_and_validated():
    assert comparison_algorithms("Graph Traversal") == ("BFS", "DFS")
    assert comparison_algorithms("Weighted Routing") == ("Dijkstra", "A*")
    assert comparison_algorithms("Championship Sorting") == ("Merge Sort", "Quick Sort", "Heap Sort")
    assert validate_comparison_selection("Weighted Routing", "Dijkstra", "A*") is None
    assert validate_comparison_selection("Weighted Routing", "A*", "Dijkstra") is None
    assert validate_comparison_selection("Weighted Routing", "Dijkstra", "Dijkstra") == "Please select two different algorithms."
    assert validate_comparison_selection("Weighted Routing", "BFS", "Merge Sort") == "These algorithms solve different problem types and cannot be directly compared in this mode."
    assert validate_comparison_selection("Weighted Routing", None, "A*") == "Please select two algorithms."


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


def test_quick_race_setup_persists_config_without_championship_points(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    config = session.configure_quick_race(
        tracks[1].id,
        laps=1,
        ai_difficulty="Hard",
        events_enabled=False,
        routing="Speed",
    )
    engine = RaceEngine(
        tracks[1],
        config=replace(DEFAULT_CONFIG, laps=config["laps"]),
        route_config=session.route_plan,
        events_enabled=config["events_enabled"],
        ai_difficulty=config["ai_difficulty"],
    )
    results = engine.run()
    assert config["race_id"].startswith("quick-circuit_02-")
    assert engine.config.laps == 1
    assert not engine.state.event_log
    assert results[0].mode == "quick"
    assert session.record_race_results(tracks[1].id, results)
    assert session.championship_points == {}
    assert session.championship_index == 0


def test_championship_round_config_is_unique_and_uses_next_track(tmp_path):
    tracks = load_tracks()
    session = GameSession.create(tracks, root=tmp_path)
    session.start_new_championship()
    first = session.prepare_championship_race()
    assert first["race_mode"] == "championship"
    assert first["round_index"] == 0
    results = RaceEngine(tracks[0], route_config=session.route_plan).run()
    assert session.record_race_results(tracks[0].id, results)
    second = session.prepare_championship_race()
    assert second["round_index"] == 1
    assert second["race_id"] != first["race_id"]
    assert session.selected_track_id == tracks[1].id
