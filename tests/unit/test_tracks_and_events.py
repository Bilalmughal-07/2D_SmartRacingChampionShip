from smart_racing.model.events import Event, EventType
from smart_racing.services.event_scheduler import EventScheduler
from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.route_planner import RoutePlanner
from smart_racing.services.track_loader import load_tracks
from smart_racing.services.track_validator import TrackValidator


def test_three_tracks_validate():
    tracks = load_tracks()
    assert len(tracks) == 3
    assert all(TrackValidator().validate(track).valid for track in tracks)
    assert [track.theme for track in tracks] == ["emerald", "canyon", "metro"]
    assert len({(len(track.vertices), len(track.edges)) for track in tracks}) == 3


def test_event_order_cancellation_and_expiration():
    scheduler = EventScheduler()
    scheduler.schedule(Event(1, EventType.ROAD_BLOCKAGE, 5, 2, 1))
    scheduler.schedule(Event(2, EventType.OIL_SPILL, 5, 1, 2))
    scheduler.schedule(Event(3, EventType.FUEL_STATION, 5, 1, 3))
    scheduler.cancel(3)
    assert [e.event_id for e in scheduler.pop_due(5)] == [2, 1]


def test_each_circuit_uses_one_physical_start_finish_timing_line():
    for track in load_tracks():
        graph = track.graph()
        start = graph.vertices[track.start_id]
        finish = graph.vertices[track.finish_id]
        assert (start.x, start.y) == (finish.x, finish.y)


def test_transferred_player_route_restarts_at_shared_start_finish_for_second_lap():
    for track in load_tracks():
        report = RoutePlanner(track, "balanced").plan_route(
            track.start_id,
            track.finish_id,
            "dijkstra",
            checkpoint_aware=True,
        )
        assert report is not None
        engine = RaceEngine(
            track,
            route_config={
                "player_path": report["path"],
                "preset": "balanced",
                "strategy": "balanced",
                "checkpoint_aware": True,
            },
            events_enabled=False,
        )
        results = engine.run()
        player = next(racer for racer in engine.racers if racer.is_human)
        player_result = next(result for result in results if result.racer_id == player.id)
        assert player.lap == engine.config.laps
        assert player.current_vertex == track.finish_id
        assert player_result.finish_time is not None
        assert not player_result.dnf
        assert player_result.completed_checkpoints == engine.config.laps * len(track.checkpoint_ids) + len(track.checkpoint_ids)
