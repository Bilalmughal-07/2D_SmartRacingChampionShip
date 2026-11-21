from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "src")

from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.track_loader import load_tracks
from smart_racing.services.track_validator import TrackValidator


def main():
    parser = argparse.ArgumentParser(description="Smart Racing Championship")
    parser.add_argument("--headless", action="store_true", help="run a deterministic smoke race")
    parser.add_argument("--track", default="circuit_01")
    args = parser.parse_args()
    tracks = load_tracks()
    track = next(t for t in tracks if t.id == args.track)
    report = TrackValidator().validate(track)
    if not report.valid:
        raise SystemExit("Invalid track: " + "; ".join(report.errors))
    if args.headless:
        results = RaceEngine(track).run()
        print(json.dumps({"track": track.id, "results": [r.__dict__ for r in results]}, indent=2))
        return
    from smart_racing.app import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
