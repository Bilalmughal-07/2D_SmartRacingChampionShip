from __future__ import annotations

import json
import sys

sys.path.insert(0, "src")

from smart_racing.services.track_loader import load_tracks
from smart_racing.services.track_validator import TrackValidator


def main():
    output = []
    for track in load_tracks():
        report = TrackValidator().validate(track)
        output.append(
            {
                "id": track.id,
                "name": track.name,
                "valid": report.valid,
                "errors": report.errors,
                "warnings": report.warnings,
                "vertices": len(track.vertices),
                "edges": len(track.edges),
                "checkpoints": len(track.checkpoint_ids),
                "shortcuts": sum(e.is_shortcut for e in track.edges),
            }
        )
    print(json.dumps(output, indent=2))
    if not all(item["valid"] for item in output):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
