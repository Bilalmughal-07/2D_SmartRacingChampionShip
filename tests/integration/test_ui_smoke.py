import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from smart_racing.services.track_loader import load_tracks
from smart_racing.ui.screens import GameApp, ScreenName


def test_all_screens_draw_and_menu_buttons_navigate():
    pygame.init()
    surface = pygame.display.set_mode((1440, 900))
    app = GameApp(load_tracks())
    font = pygame.font.SysFont("segoeui", 18)
    small = pygame.font.SysFont("segoeui", 15)
    large = pygame.font.SysFont("segoeui", 32, bold=True)
    for screen_name in (
        ScreenName.MENU,
        ScreenName.EXPLORER,
        ScreenName.RACE,
        ScreenName.LAB,
        ScreenName.DASHBOARD,
    ):
        app.screen_name = screen_name
        surface.fill((11, 18, 32))
        app._draw(surface, font, large, small, pygame)
    app.screen_name = ScreenName.MENU
    app._draw(surface, font, large, small, pygame)
    app._handle_click((100, 325))
    assert app.screen_name == ScreenName.EXPLORER
    pygame.quit()


def test_explorer_route_configuration_transfers_to_race_engine():
    app = GameApp(load_tracks())
    app.explorer_algorithm = "A*"
    app.explorer_preset = "speed"
    app._calculate_route()
    app._start_from_explorer()
    assert app.screen_name == ScreenName.RACE
    assert app.engine.track is app.track
    assert app.engine.route_config["algorithm"] == "A*"
    assert app.engine.route_config["preset"] == "speed"
    assert app.engine.route_config["source"] == app.explorer_start_id
    assert app.engine.route_config["destination"] == app.explorer_destination_id


def test_explorer_closure_recalculates_route_on_live_graph():
    app = GameApp(load_tracks())
    app._calculate_route()
    closed_edge = app.explorer_result["metrics"]["edge_ids"][0]
    app._toggle_explorer_closure()
    assert app.explorer_graph.edges[closed_edge].status.value == "Blocked"
    assert closed_edge not in app.explorer_result["metrics"]["edge_ids"]
