from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from smart_racing.arcade_ui import ArcadeApp
from smart_racing.services.track_loader import load_tracks


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Racing Championship Arcade Phase 1")
    parser.add_argument("--smoke", action="store_true", help="render one menu frame and exit")
    parser.add_argument("--output", default="docs/screenshots/arcade_main_menu.png")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--modal", choices=("instructions", "settings", "exit"), default=None)
    parser.add_argument("--screen", choices=("menu", "circuits", "explorer", "lab", "race", "dashboard"), default="menu")
    args = parser.parse_args()
    size = (args.width, args.height) if args.width and args.height else None
    ArcadeApp(
        load_tracks(),
        smoke_path=args.output if args.smoke else None,
        size=size,
        initial_modal=args.modal,
        initial_screen=args.screen,
    ).run()


if __name__ == "__main__":
    main()
