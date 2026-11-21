from smart_racing.services.route_planner import RoutePlanner
from smart_racing.services.track_loader import load_tracks


def test_checkpoint_aware_route_visits_all_required_targets_and_reports_resources():
    for track in load_tracks():
        planner = RoutePlanner(track, "balanced")
        report = planner.plan_route(track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True)
        assert report is not None
        assert report["targets"] == [*track.checkpoint_ids, track.finish_id]
        assert report["metrics"]["valid"]
        assert report["cost"] == report["weighted_cost"]
        assert report["resources"]["fuel_feasible"]
        assert report["resources"]["fuel"].details["destination_fuel"] >= 0


def test_bfs_and_dfs_are_available_but_do_not_claim_weighted_optimization():
    track = load_tracks()[0]
    planner = RoutePlanner(track, "balanced")
    for algorithm in ("bfs", "dfs"):
        report = planner.plan_route(track.start_id, track.finish_id, algorithm, checkpoint_aware=True)
        assert report is not None
        assert report["path"]
        assert report["cost"] is None
        assert report["weighted_cost"] >= 0


def test_blocked_route_edge_is_excluded_by_recalculation():
    track = load_tracks()[0]
    planner = RoutePlanner(track, "balanced")
    first = planner.plan_route(track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True)
    assert first is not None
    edge_id = first["metrics"]["edge_ids"][0]
    planner.graph.set_edge_status(edge_id, "Blocked")
    second = planner.plan_route(track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True)
    assert second is not None
    assert edge_id not in second["metrics"]["edge_ids"]
    assert second["metrics"]["valid"]


def test_four_preset_comparison_uses_checkpoint_aware_weighted_reports():
    track = load_tracks()[1]
    planner = RoutePlanner(track, "balanced")
    comparison = planner.compare_presets(track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True)
    assert set(comparison) == {"balanced", "speed", "economy", "safety"}
    assert all(report["checkpoint_aware"] for report in comparison.values())
    assert all(report["cost"] == report["weighted_cost"] for report in comparison.values())


def test_all_supported_algorithms_visit_ordered_checkpoints_on_every_circuit():
    for track in load_tracks():
        for algorithm in ("bfs", "dfs", "dijkstra", "astar"):
            report = RoutePlanner(track, "balanced").plan_route(
                track.start_id, track.finish_id, algorithm, checkpoint_aware=True
            )
            assert report is not None
            assert report["targets"] == [*track.checkpoint_ids, track.finish_id]
            assert report["metrics"]["valid"]
            assert all(target in report["path"] for target in report["targets"])


def test_astar_matches_dijkstra_weighted_cost_for_each_circuit():
    for track in load_tracks():
        dijkstra = RoutePlanner(track, "balanced").plan_route(
            track.start_id, track.finish_id, "dijkstra", checkpoint_aware=True
        )
        astar = RoutePlanner(track, "balanced").plan_route(
            track.start_id, track.finish_id, "astar", checkpoint_aware=True
        )
        assert dijkstra is not None and astar is not None
        assert astar["weighted_cost"] == dijkstra["weighted_cost"]


def test_source_equals_destination_is_a_valid_single_vertex_route():
    track = load_tracks()[0]
    report = RoutePlanner(track, "balanced").plan_route(
        track.start_id, track.start_id, "dijkstra", checkpoint_aware=False
    )
    assert report is not None
    assert report["path"] == [track.start_id]
    assert report["metrics"]["valid"]
