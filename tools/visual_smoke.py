from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from smart_racing.services.track_loader import load_tracks
from smart_racing.ui.screens import GameApp, ScreenName


def main():
    output = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    screens = [
        (ScreenName.MENU, "01_main_menu.png"),
        (ScreenName.EXPLORER, "02_track_explorer.png"),
        (ScreenName.RACE, "03_racing_screen.png"),
        (ScreenName.LAB, "04_algorithm_lab.png"),
        (ScreenName.DASHBOARD, "05_championship_dashboard.png"),
    ]
    pygame.init()
    for size, suffix in (((1440, 900), ""), ((1280, 720), "_1280x720")):
        surface = pygame.display.set_mode(size)
        app = GameApp(load_tracks())
        font = pygame.font.SysFont("segoeui", 18)
        large = pygame.font.SysFont("segoeui", 32, bold=True)
        small = pygame.font.SysFont("segoeui", 15)
        for screen_name, filename in screens:
            app.screen_name = screen_name
            surface.fill((11, 18, 32))
            app._draw(surface, font, large, small, pygame)
            target = output / f"{Path(filename).stem}{suffix}{Path(filename).suffix}"
            pygame.image.save(surface, target)
    comparison_app = GameApp(load_tracks())
    comparison_app._change_track(2)
    comparison_app.screen_name = ScreenName.EXPLORER
    comparison_app._calculate_route()
    comparison_app._compare_routes()
    surface = pygame.display.set_mode((1440, 900))
    comparison_app._draw(surface, font, large, small, pygame)
    pygame.image.save(surface, output / "06_track_explorer_comparison.png")
    for index in range(3):
        explorer_app = GameApp(load_tracks())
        explorer_app._change_track(index)
        explorer_app.screen_name = ScreenName.EXPLORER
        explorer_app._calculate_route()
        explorer_surface = pygame.display.set_mode((1440, 900))
        explorer_app._draw(explorer_surface, font, large, small, pygame)
        pygame.image.save(explorer_surface, output / f"07_track_explorer_circuit_{index + 1}.png")
    pygame.quit()
    print(f"Rendered {len(screens) * 2 + 4} real application states at 1440x900 and 1280x720 to {output}")


if __name__ == "__main__":
    main()
