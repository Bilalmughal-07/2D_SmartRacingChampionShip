from smart_racing.model.events import Event, EventType
from smart_racing.services.event_scheduler import EventScheduler
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
