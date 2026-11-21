from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from smart_racing.model.race import ChampionshipEntry
from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.scoring import rank_entries, record_results, top_k_entries
from smart_racing.services.track_loader import load_tracks
from smart_racing.services.track_validator import TrackValidator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="experiments/data/championship_results.json")
    args = parser.parse_args()
    tracks = load_tracks()
    if not all(TrackValidator().validate(track).valid for track in tracks):
        raise SystemExit("track validation failed")
    entries = {
        i: ChampionshipEntry(i, name)
        for i, name in enumerate(["Player", "Navigator", "Shortcut", "Distance"], 1)
    }
    races = []
    for track in tracks:
        engine = RaceEngine(track)
        results = engine.run()
        record_results(entries, results)
        races.append(
            {
                "track": track.id,
                "results": [result.__dict__ for result in results],
                "events": engine.state.event_log,
            }
        )
    ranking = rank_entries(list(entries.values()))
    payload = {
        "races": races,
        "standings": [entry.__dict__ for entry in ranking],
        "top_3": [entry.__dict__ for entry in top_k_entries(ranking, 3)],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
