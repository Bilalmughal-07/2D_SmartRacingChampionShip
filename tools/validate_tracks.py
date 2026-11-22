from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from smart_racing.services.track_loader import load_tracks
from smart_racing.services.track_validator import TrackValidator

if __name__ == "__main__":
    reports = [TrackValidator().validate(track) for track in load_tracks()]
    for report in reports:
        print("VALID" if report.valid else "INVALID", report.errors)
    raise SystemExit(0 if all(report.valid for report in reports) else 1)
