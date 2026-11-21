from smart_racing.services.geometry_validator import validate_geometry
from smart_racing.services.track_loader import load_tracks


def test_all_authoritative_circuits_have_valid_geometry():
    reports = {track.id: validate_geometry(track) for track in load_tracks()}
    assert set(reports) == {"circuit_01", "circuit_02", "circuit_03"}
    assert all(report.valid for report in reports.values())
    assert all(not report.errors for report in reports.values())


def test_geometry_report_warns_about_unconnected_crossings_without_failing_topology():
    reports = {track.id: validate_geometry(track) for track in load_tracks()}
    assert any(reports[track_id].warnings for track_id in reports)
