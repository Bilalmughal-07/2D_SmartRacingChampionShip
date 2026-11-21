from __future__ import annotations

from smart_racing.services.track_loader import load_tracks


def main():
    from smart_racing.ui.screens import GameApp

    GameApp(load_tracks()).run()
