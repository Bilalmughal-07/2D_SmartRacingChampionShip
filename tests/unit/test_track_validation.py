from smart_racing.model.graph import VertexType
from smart_racing.services.route_planner import RoutePlanner
from smart_racing.services.track_loader import load_tracks
from smart_racing.services.track_validator import TrackValidator


def test_redesigned_tracks_have_reachable_two_sided_resource_vertices():
    for track in load_tracks():
        graph = track.graph()
        resources = [
            vertex
            for vertex in track.vertices
            if vertex.type in (VertexType.FUEL_STATION, VertexType.NITRO_PICKUP)
        ]
        assert resources
        for vertex in resources:
            incident = [
                edge
                for edge in track.edges
                if edge.from_id == vertex.id or edge.to_id == vertex.id
            ]
            assert len(incident) >= 2
            assert TrackValidator._reachable(graph, track.start_id, vertex.id)
            assert TrackValidator._reachable(graph, vertex.id, track.finish_id)


def test_redesigned_tracks_support_ordered_complete_lap_and_next_lap_transition():
    for track in load_tracks():
        planner = RoutePlanner(track)
        first_lap = planner.plan_checkpoints(track.start_id, include_resources=True)
        next_lap = planner.plan_route(
            track.finish_id,
            track.checkpoint_ids[0],
            algorithm="dijkstra",
            checkpoint_aware=False,
        )
        assert first_lap is not None
        assert first_lap["targets"] == [*track.checkpoint_ids, track.finish_id]
        assert first_lap["resources"]["fuel_feasible"]
        assert next_lap is not None
        assert next_lap["metrics"]["valid"]
        assert next_lap["resources"]["fuel_feasible"]


def test_validator_rejects_a_resource_that_is_only_a_dead_end():
    track = load_tracks()[0]
    station = next(vertex for vertex in track.vertices if vertex.type == VertexType.FUEL_STATION)
    incident = [edge for edge in track.edges if edge.from_id == station.id or edge.to_id == station.id]
    track.edges.remove(incident[0])
    report = TrackValidator().validate(track)
    assert not report.valid
    assert any("resource vertex" in error for error in report.errors)
