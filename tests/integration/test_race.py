from smart_racing.services.race_engine import RaceEngine
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
