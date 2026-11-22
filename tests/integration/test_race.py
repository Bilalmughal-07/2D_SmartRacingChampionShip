from dataclasses import replace

from smart_racing.config import DEFAULT_CONFIG
from smart_racing.model.graph import EdgeStatus
from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.route_planner import RoutePlanner
from smart_racing.services.track_loader import load_tracks


def test_complete_race_and_deterministic_replay():
    track = load_tracks()[0]
    first = RaceEngine(track).run()
    second = RaceEngine(track).run()
    assert [(x.racer_id, x.finish_position, x.finish_time) for x in first] == [
        (x.racer_id, x.finish_position, x.finish_time) for x in second
    ]
    assert all(x.finish_position >= 1 for x in first)


def test_all_redesigned_tracks_keep_ai_racers_fuel_feasible():
    for track in load_tracks():
        results = RaceEngine(track).run()
        assert len(results) == 4
        assert all(not result.dnf for result in results)


def test_live_closure_updates_shared_route_graph():
    engine = RaceEngine(load_tracks()[0])
    before = engine.graph.edges[3].status
    engine.tick(12.5)
    assert before.value == "Open"
    assert any("road_blockage" in event for event in engine.state.event_log)


def test_player_controls_change_edge_progress_and_only_select_open_neighbors():
    track = load_tracks()[0]
    slow = RaceEngine(track)
    slow.set_player_input(0.0, 1.0)
    slow.tick()
    slow_progress = slow.racers[0].edge_progress

    fast = RaceEngine(track)
    fast.set_player_input(1.0, 0.0)
    fast.tick()
    fast_progress = fast.racers[0].edge_progress

    assert fast_progress > slow_progress
    options = fast.available_player_exits()
    assert options
    assert fast.cycle_player_exit(1) in options
    assert fast.confirm_player_exit()


def test_manual_nitro_expires_and_is_reported_in_snapshot():
    engine = RaceEngine(load_tracks()[0])
    assert engine.activate_nitro(1)
    engine.tick()
    assert engine.racers[0].active_nitro
    for _ in range(300):
        engine.tick()
    assert not engine.racers[0].active_nitro
    assert engine.snapshot().racers[0]["active_nitro"] is False


def test_player_sprint_has_duration_and_cooldown():
    engine = RaceEngine(load_tracks()[0])
    assert engine.activate_sprint(1)
    assert engine.racers[0].sprint_active
    for _ in range(int(engine.config.sprint_duration / engine.config.fixed_timestep) + 2):
        engine.tick()
    assert not engine.racers[0].sprint_active
    assert engine.racers[0].sprint_cooldown > 0
    assert not engine.activate_sprint(1)


def test_arcade_route_handoff_accepts_unset_preset_for_unweighted_algorithms():
    engine = RaceEngine(load_tracks()[0], route_config={"algorithm": "BFS", "preset": None})
    engine.tick()
    assert engine.racers[0].current_path


def test_all_ai_policies_finish_all_circuits_without_event_or_shortcut_oscillation():
    for track in load_tracks():
        results = RaceEngine(track, events_enabled=False).run()
        assert all(result.finish_time is not None and not result.dnf for result in results)
        shortcut = next(result for result in results if result.racer_id == 3)
        assert shortcut.finish_time < 200


def test_player_recalculates_when_the_transferred_route_edge_is_closed():
    track = load_tracks()[0]
    report = RoutePlanner(track).plan_route(
        track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True
    )
    engine = RaceEngine(
        track,
        route_config={
            "player_path": report["path"],
            "checkpoint_aware": True,
            "race_laps": 1,
        },
        events_enabled=False,
    )
    first_edge = report["metrics"]["edge_ids"][0]
    engine.graph.set_edge_status(first_edge, EdgeStatus.BLOCKED)
    engine.tick()
    assert engine.player_deviated
    assert "blocked" in engine.player_reroute_reason
    assert not engine.racers[0].dnf


def test_shortcut_driver_never_immediately_reverses_an_edge():
    track = load_tracks()[0]
    engine = RaceEngine(track, events_enabled=False)
    racer = next(item for item in engine.racers if item.id == 3)
    racer.current_vertex = 12
    racer.last_edge_from = 1
    racer.last_edge_to = 12
    plan = engine._choose_plan(racer)
    assert plan["path"][1] != 1


def test_free_exploration_plan_can_launch_one_lap_race_to_selected_destination():
    track = load_tracks()[0]
    source, destination = 11, 5
    report = RoutePlanner(track).plan_route(source, destination, "dijkstra", checkpoint_aware=False)
    engine = RaceEngine(
        track,
        config=replace(DEFAULT_CONFIG, laps=1),
        route_config={
            "source": source,
            "destination": destination,
            "player_path": report["path"],
            "checkpoint_aware": False,
            "race_laps": 1,
        },
        events_enabled=False,
    )
    result = next(item for item in engine.run() if item.racer_id == 1)
    assert result.finish_time is not None
    assert not result.dnf


def test_player_exit_selection_survives_arrival_at_next_junction_on_all_circuits():
    for track in load_tracks():
        planned = RoutePlanner(track).plan_route(
            track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True
        )["path"]
        engine = RaceEngine(
            track,
            route_config={"player_path": planned},
            events_enabled=False,
        )
        engine.tick()
        player = engine._player()
        decision_vertex = player.current_path[1]
        assert player.current_vertex in engine.available_player_exits()
        planned_next = planned[2]
        selected = None
        for _ in range(len(engine.available_player_exits()) + 2):
            selected = engine.cycle_player_exit(1)
            if selected != planned_next:
                break
        assert selected is not None
        assert engine.confirm_player_exit()
        for _ in range(500):
            engine.tick()
            if player.current_vertex == decision_vertex:
                break
        assert player.current_vertex == decision_vertex
        assert player.selected_exit == selected
        assert player.selected_exit_vertex == decision_vertex
        assert player.exit_confirmed
        engine.tick()
        assert player.current_path[:2] == [decision_vertex, selected]
        assert engine.player_deviated or selected == planned_next
