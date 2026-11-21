from __future__ import annotations

import random
import textwrap
from copy import deepcopy
from pathlib import Path
from typing import Callable

import arcade
from arcade.gui import UIFlatButton, UIManager, UISlider

from smart_racing.arcade_ui.session import GameSession
from smart_racing.arcade_ui.theme import (
    AMBER,
    CORAL,
    CYAN,
    EMERALD,
    MUTED,
    NAVY,
    PANEL_DARK,
    PURPLE,
    WHITE,
    button_style,
    rgba,
)
from smart_racing.model.graph import EdgeStatus, VertexType
from smart_racing.services.route_planner import ALGORITHM_COMPLEXITY, RoutePlanner
from smart_racing.services.track_validator import TrackValidator


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _text(text: str, x: float, y: float, size: float, color=WHITE, **kwargs) -> None:
    arcade.draw_text(text, x, y, color, font_size=size, font_name=("Aptos Display", "Arial"), **kwargs)


def _ensure_phase_views() -> None:
    """Load the focused Phase 3-5 views after the shared shell is defined."""
    global ArcadeRacingView, AlgorithmLabView, ChampionshipDashboardView
    from smart_racing.arcade_ui.dashboard_view import ChampionshipDashboardView as _Dashboard
    from smart_racing.arcade_ui.lab_view import AlgorithmLabView as _Lab
    from smart_racing.arcade_ui.race_view import ArcadeRacingView as _Race

    ArcadeRacingView, AlgorithmLabView, ChampionshipDashboardView = _Race, _Lab, _Dashboard


class ArcadeApp(arcade.Window):
    """Arcade application shell for Phase 1, backed by the existing services."""

    def __init__(
        self,
        tracks,
        smoke_path: str | None = None,
        size: tuple[int, int] | None = None,
        initial_modal: str | None = None,
        initial_screen: str = "menu",
    ):
        _ensure_phase_views()
        session = GameSession.create(tracks)
        window_width, window_height = size or (
            int(session.settings["width"]),
            int(session.settings["height"]),
        )
        super().__init__(
            width=window_width,
            height=window_height,
            title="Smart Racing Championship — Arcade",
            fullscreen=bool(session.settings["fullscreen"]),
            resizable=True,
            vsync=True,
            center_window=True,
        )
        self.session = session
        self.smoke_path = Path(smoke_path) if smoke_path else None
        self.smoke_captured = False
        if initial_screen == "explorer":
            self.show_view(TrackExplorerView(self, session))
        elif initial_screen == "lab":
            self.show_view(AlgorithmLabView(self, session))
        elif initial_screen == "race":
            self.show_view(ArcadeRacingView(self, session))
        elif initial_screen == "dashboard":
            self.show_view(ChampionshipDashboardView(self, session))
        elif initial_screen == "circuits":
            self.show_view(CircuitSelectionView(self, session))
        else:
            self.show_view(MainMenuView(self, session, self.smoke_path, initial_modal))

    def on_close(self):
        self.session.close()
        super().on_close()


class ArcadeView(arcade.View):
    def __init__(self, window: ArcadeApp, session: GameSession):
        super().__init__(window)
        self.app = window
        self.session = session
        self.ui = UIManager(window)
        self.buttons: list[tuple[UIFlatButton, tuple[float, float, float, float], Callable[[], None]]] = []
        self.focus_index = 0

    def on_show_view(self):
        self.ui.enable()
        self.rebuild_ui()

    def on_hide_view(self):
        self.ui.disable()

    def clear_ui(self) -> None:
        self.ui.clear()
        self.buttons.clear()
        self.focus_index = 0

    def add_button(
        self,
        label: str,
        x: float,
        y: float,
        width: float,
        height: float,
        callback: Callable[[], None],
        fill=NAVY,
        text=WHITE,
        border=None,
    ) -> UIFlatButton:
        button = UIFlatButton(
            text=label,
            x=x,
            y=y,
            width=width,
            height=height,
            style=button_style(fill, text, border),
        )
        button.on_click = lambda _event: callback()
        self.ui.add(button)
        self.buttons.append((button, (x, y, width, height), callback))
        return button

    def focus_move(self, delta: int) -> None:
        if self.buttons:
            self.focus_index = (self.focus_index + delta) % len(self.buttons)

    def activate_focus(self) -> None:
        if self.buttons:
            self.buttons[self.focus_index][2]()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        for index, (_, rect, _) in enumerate(self.buttons):
            left, bottom, width, height = rect
            if left <= x <= left + width and bottom <= y <= bottom + height:
                self.focus_index = index
                break

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.UP, arcade.key.LEFT):
            self.focus_move(-1)
        elif symbol in (arcade.key.DOWN, arcade.key.RIGHT):
            self.focus_move(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN, arcade.key.SPACE):
            self.activate_focus()
        elif symbol == arcade.key.ESCAPE:
            self.go_menu()

    def go_menu(self) -> None:
        self.app.show_view(MainMenuView(self.app, self.session))

    def draw_focus(self) -> None:
        if not self.buttons:
            return
        _, (x, y, width, height), _ = self.buttons[self.focus_index]
        arcade.draw_lbwh_rectangle_outline(x - 5, y - 5, width + 10, height + 10, CYAN, 2)

    def capture_smoke(self) -> None:
        if self.app.smoke_path and not self.app.smoke_captured:
            self.app.smoke_path.parent.mkdir(parents=True, exist_ok=True)
            arcade.get_image().save(self.app.smoke_path)
            self.app.smoke_captured = True
            arcade.schedule_once(lambda _delta: self.app.close(), 0.05)

    def draw_panel(self, x: float, y: float, width: float, height: float, alpha: int = 230) -> None:
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, rgba(PANEL_DARK, alpha))
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, rgba((54, 85, 112)), 1)

    def rebuild_ui(self) -> None:
        raise NotImplementedError


class MainMenuView(ArcadeView):
    MENU_ITEMS = (
        ("START CHAMPIONSHIP", "championship"),
        ("QUICK RACE", "quick"),
        ("TRACK EXPLORER", "explorer"),
        ("ALGORITHM LAB", "lab"),
        ("HOW TO PLAY", "instructions"),
        ("SETTINGS", "settings"),
        ("EXIT GAME", "exit"),
    )

    def __init__(
        self,
        window: ArcadeApp,
        session: GameSession,
        smoke_path: Path | None = None,
        initial_modal: str | None = None,
    ):
        self.smoke_path = smoke_path
        self.smoke_captured = False
        self.modal: str | None = initial_modal
        self.modal_focus = 0
        self.particles = [(random.random(), random.random(), random.uniform(15, 42)) for _ in range(28)]
        self.background = None
        background_path = _root() / "assets" / "backgrounds" / "racing_battle.png"
        if background_path.exists():
            self.background = arcade.load_texture(str(background_path))
        super().__init__(window, session)

    def rebuild_ui(self) -> None:
        self.clear_ui()
        if self.modal:
            self.build_modal()
            return
        width, height = self.window.width, self.window.height
        button_width = min(380, max(300, int(width * 0.35)))
        button_height = max(42, min(52, int(height * 0.058)))
        gap = max(7, int(button_height * 0.18))
        total = len(self.MENU_ITEMS) * button_height + (len(self.MENU_ITEMS) - 1) * gap
        x = (width - button_width) / 2
        y = max(34, int(height * 0.06)) + total - button_height
        for label, action in self.MENU_ITEMS:
            fill, text, border = NAVY, WHITE, (83, 112, 139)
            if action == "championship":
                fill, text, border = CYAN, NAVY, CYAN
            elif action == "quick":
                fill, text, border = EMERALD, NAVY, EMERALD
            elif action == "exit":
                fill, text, border = (84, 27, 39), WHITE, CORAL
            self.add_button(label, x, y, button_width, button_height, lambda action=action: self.activate(action), fill, text, border)
            y -= button_height + gap

    def activate(self, action: str) -> None:
        if action == "championship":
            if self.session.has_saved_championship:
                self.open_modal("championship")
            else:
                self.session.start_new_championship()
                self.show_explorer()
        elif action == "quick":
            self.window.show_view(CircuitSelectionView(self.app, self.session))
        elif action == "explorer":
            self.session.mode = "quick"
            self.session.save_state()
            self.show_explorer()
        elif action == "lab":
            self.window.show_view(AlgorithmLabView(self.app, self.session))
        elif action in {"instructions", "settings", "exit"}:
            self.open_modal(action)

    def show_explorer(self) -> None:
        self.window.show_view(TrackExplorerView(self.app, self.session))

    def open_modal(self, modal: str) -> None:
        self.modal = modal
        self.modal_focus = 0
        self.rebuild_ui()

    def close_modal(self) -> None:
        self.modal = None
        self.rebuild_ui()

    def build_modal(self) -> None:
        width, height = self.window.width, self.window.height
        panel_width = min(720, int(width * 0.82))
        panel_height = min(480, int(height * 0.70))
        left = (width - panel_width) / 2
        bottom = (height - panel_height) / 2
        button_width = min(190, (panel_width - 70) / 3)
        button_height = 44
        if self.modal == "championship":
            labels = [("CONTINUE", self.session.continue_championship, CYAN), ("NEW", self.session.start_new_championship, EMERALD), ("CANCEL", self.close_modal, NAVY)]
            y = bottom + 42
            for index, (label, callback, fill) in enumerate(labels):
                callback = self._then(callback, self.show_explorer) if label != "CANCEL" else callback
                self.add_button(label, left + 24 + index * (button_width + 10), y, button_width, button_height, callback, fill, NAVY if fill != NAVY else WHITE, CYAN if fill == NAVY else fill)
        elif self.modal == "instructions":
            self.add_button("CLOSE", left + 24, bottom + 28, 170, button_height, self.close_modal, CYAN, NAVY, CYAN)
        elif self.modal == "settings":
            mode_label = "FULLSCREEN" if self.session.settings["fullscreen"] else "WINDOWED"
            effects_label = "EFFECTS: ON" if self.session.settings["effects"] else "EFFECTS: OFF"
            self.add_button(mode_label, left + 24, bottom + 100, 190, button_height, self.toggle_fullscreen, NAVY, WHITE, CYAN)
            self.add_button(effects_label, left + 230, bottom + 100, 170, button_height, self.toggle_effects, NAVY, WHITE, CYAN)
            self.add_button("SAVE & CLOSE", left + 24, bottom + 28, 170, button_height, self.close_settings, CYAN, NAVY, CYAN)
            slider_width = min(270, panel_width - 80)
            music = UISlider(
                value=float(self.session.settings["music_volume"]) * 100,
                min_value=0,
                max_value=100,
                x=left + 250,
                y=bottom + panel_height - 165,
                width=slider_width,
                height=24,
            )
            music.on_change = lambda event: self.set_volume("music_volume", event.value)
            sfx = UISlider(
                value=float(self.session.settings["sfx_volume"]) * 100,
                min_value=0,
                max_value=100,
                x=left + 250,
                y=bottom + panel_height - 215,
                width=slider_width,
                height=24,
            )
            sfx.on_change = lambda event: self.set_volume("sfx_volume", event.value)
            self.ui.add(music)
            self.ui.add(sfx)
        elif self.modal == "exit":
            self.add_button("CANCEL", left + 24, bottom + 34, 170, button_height, self.close_modal, NAVY, WHITE, CYAN)
            self.add_button("EXIT GAME", left + 214, bottom + 34, 170, button_height, self.exit_game, (84, 27, 39), WHITE, CORAL)

    @staticmethod
    def _then(first: Callable[[], None], second: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            first()
            second()

        return run

    def toggle_fullscreen(self) -> None:
        value = not bool(self.session.settings["fullscreen"])
        self.session.settings["fullscreen"] = value
        self.session.save_settings()
        self.window.set_fullscreen(value)
        self.rebuild_ui()

    def toggle_effects(self) -> None:
        self.session.settings["effects"] = not bool(self.session.settings["effects"])
        self.session.save_settings()
        self.rebuild_ui()

    def set_volume(self, key: str, value: float) -> None:
        self.session.settings[key] = round(_clamp(float(value) / 100.0, 0.0, 1.0), 2)
        self.session.save_settings()

    def close_settings(self) -> None:
        self.session.save_settings()
        self.close_modal()

    def exit_game(self) -> None:
        self.session.close()
        self.window.close()

    def on_key_press(self, symbol: int, modifiers: int):
        if self.modal:
            if symbol == arcade.key.ESCAPE:
                self.close_modal()
            elif symbol in (arcade.key.UP, arcade.key.LEFT):
                if self.buttons:
                    self.focus_index = (self.focus_index - 1) % len(self.buttons)
            elif symbol in (arcade.key.DOWN, arcade.key.RIGHT):
                if self.buttons:
                    self.focus_index = (self.focus_index + 1) % len(self.buttons)
            elif symbol in (arcade.key.ENTER, arcade.key.RETURN, arcade.key.SPACE):
                self.activate_focus()
            return
        super().on_key_press(symbol, modifiers)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_update(self, delta_time: float):
        if self.session.settings.get("effects", True):
            self.particles = [((x + speed * delta_time / max(self.window.width, 1)) % 1.0, y, speed) for x, y, speed in self.particles]

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        if self.background:
            arcade.draw_texture_rect(self.background, arcade.LBWH(0, 0, width, height))
            arcade.draw_lbwh_rectangle_filled(0, 0, width, height, (6, 13, 27, 158))
            arcade.draw_lbwh_rectangle_filled(width * 0.24, 0, width * 0.52, height, (5, 12, 25, 95))
        else:
            arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
            self.draw_fallback_background(width, height)
        for x_ratio, y_ratio, length in self.particles:
            x = x_ratio * width
            y = y_ratio * height
            arcade.draw_line(x, y, x + length, y + 1, (56, 189, 248, 75), 1)

        title_size = max(38, min(72, int(width * 0.046)))
        _text("SMART RACING", width / 2, height * 0.865, title_size, WHITE, anchor_x="center", anchor_y="center", bold=True)
        _text("CHAMPIONSHIP", width / 2, height * 0.775, int(title_size * 0.68), CYAN, anchor_x="center", anchor_y="center", bold=True)
        _text("THE ALGORITHMIC RACING CHALLENGE", width / 2, height * 0.708, max(14, int(title_size * 0.24)), MUTED, anchor_x="center", anchor_y="center")
        if self.modal:
            self.draw_modal_content()
        self.ui.draw()
        self.draw_focus()
        if not self.modal:
            _text("PHASE 1  /  ARCADE FRONT-END MIGRATION", width / 2, 18, 11, MUTED, anchor_x="center")
        self.capture_smoke()

    def draw_fallback_background(self, width: int, height: int) -> None:
        for index in range(10):
            y = height * (0.2 + index * 0.055)
            arcade.draw_line(0, y, width, y - 80, (18, 42, 64), 2)
        for x in range(0, int(width), 130):
            arcade.draw_line(x, 0, x + 320, height, (19, 52, 73), 1)
        arcade.draw_line(0, height * 0.26, width, height * 0.18, (56, 189, 248), 8)
        arcade.draw_line(0, height * 0.26, width, height * 0.18, (23, 33, 47), 4)

    def draw_modal_content(self) -> None:
        width, height = self.window.width, self.window.height
        panel_width = min(720, int(width * 0.82))
        panel_height = min(480, int(height * 0.70))
        left = (width - panel_width) / 2
        bottom = (height - panel_height) / 2
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, (3, 9, 18, 185))
        self.draw_panel(left, bottom, panel_width, panel_height, 248)
        titles = {
            "championship": "CHAMPIONSHIP SESSION",
            "instructions": "HOW TO PLAY",
            "settings": "SETTINGS",
            "exit": "EXIT GAME",
        }
        _text(titles[self.modal], left + 28, bottom + panel_height - 48, 25, WHITE, bold=True)
        if self.modal == "championship":
            _text("A saved championship was found. Continue your standings or start a new season.", left + 28, bottom + panel_height - 90, 15, MUTED)
            _text(f"Next circuit: {self.session.selected_track.name}", left + 28, bottom + panel_height - 124, 15, CYAN)
        elif self.modal == "instructions":
            lines = (
                "OBJECTIVE  Plan legal routes, clear ordered checkpoints, and finish each lap first.",
                "MODES  Championship preserves points across 3 circuits; Quick Race is standalone.",
                "ROUTES  Explorer compares algorithms, shortcuts, fuel, and nitro choices.",
                "RACE  Fuel, nitro, road events, and deterministic AI shape each race.",
                "SCORING  Points persist across races; standings use deterministic tie-breaks.",
                "CONTROLS  Arrow keys navigate; Enter activates; Escape closes or returns.",
            )
            for index, line in enumerate(lines):
                _text(line, left + 28, bottom + panel_height - 94 - index * 35, 14, MUTED, width=panel_width - 56)
        elif self.modal == "settings":
            _text(f"Window mode: {'Fullscreen' if self.session.settings['fullscreen'] else 'Windowed'}", left + 28, bottom + panel_height - 82, 15, MUTED)
            _text(f"Effects: {'Enabled' if self.session.settings['effects'] else 'Disabled'}", left + 28, bottom + panel_height - 116, 15, MUTED)
            _text(f"Music volume: {int(self.session.settings['music_volume'] * 100)}%", left + 28, bottom + panel_height - 176, 14, MUTED)
            _text(f"SFX volume: {int(self.session.settings['sfx_volume'] * 100)}%", left + 28, bottom + panel_height - 226, 14, MUTED)
            _text("Values persist to JSON and are ready for the audio-backed migration stage.", left + 28, bottom + panel_height - 270, 14, AMBER)
        else:
            _text("Are you sure you want to exit Smart Racing Championship?", left + 28, bottom + panel_height - 94, 16, MUTED)


class CircuitSelectionView(ArcadeView):
    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, height = self.window.width, self.window.height
        card_width = min(430, int(width * 0.28))
        gap = max(18, int(width * 0.025))
        start_x = (width - (3 * card_width + 2 * gap)) / 2
        y = height * 0.22
        for index, track in enumerate(self.session.tracks):
            x = start_x + index * (card_width + gap)
            self.add_button(
                f"SELECT CIRCUIT {index + 1}",
                x + 24,
                y,
                card_width - 48,
                48,
                lambda track_id=track.id: self.choose(track_id),
                (20, 52, 75),
                WHITE,
                CYAN,
            )
        self.add_button("BACK TO MAIN MENU", (width - 220) / 2, 46, 220, 44, self.go_menu, NAVY, WHITE, CYAN)

    def choose(self, track_id: str) -> None:
        self.session.select_quick_race(track_id)
        self.window.show_view(TrackExplorerView(self.app, self.session))

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        _text("QUICK RACE", width / 2, height - 95, 44, WHITE, anchor_x="center", bold=True)
        _text("SELECT A CIRCUIT", width / 2, height - 137, 16, CYAN, anchor_x="center")
        card_width = min(430, int(width * 0.28))
        gap = max(18, int(width * 0.025))
        start_x = (width - (3 * card_width + 2 * gap)) / 2
        y = height * 0.22
        for index, track in enumerate(self.session.tracks):
            x = start_x + index * (card_width + gap)
            self.draw_panel(x, y, card_width, height * 0.45)
            _text(f"0{index + 1}", x + 22, y + height * 0.36, 28, CYAN, bold=True)
            _text(track.name.split("—")[-1].strip(), x + 22, y + height * 0.30, 20, WHITE, bold=True)
            _text(f"{len(track.vertices)} vertices  /  {len(track.edges)} roads", x + 22, y + height * 0.24, 13, MUTED)
            _text("10 ordered checkpoints", x + 22, y + height * 0.19, 13, EMERALD)
            _text("Route planning required before race", x + 22, y + height * 0.14, 12, MUTED)
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()


class TrackExplorerBridgeView(ArcadeView):
    def __init__(self, window: ArcadeApp, session: GameSession):
        self.route = None
        super().__init__(window, session)
        self.calculate_route()

    def calculate_route(self) -> None:
        planner = RoutePlanner(self.session.selected_track, "balanced")
        self.route = planner.plan_route(
            self.session.selected_track.start_id,
            algorithm="dijkstra",
            destination=self.session.selected_track.finish_id,
            checkpoint_aware=True,
        )

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width = self.window.width
        self.add_button("CONTINUE TO RACE", width - 300, 48, 250, 46, self.open_race, CYAN, NAVY, CYAN)
        self.add_button("BACK TO MAIN MENU", 48, 48, 210, 46, self.go_menu, NAVY, WHITE, CYAN)
        if self.session.mode == "quick":
            self.add_button("CHANGE CIRCUIT", 280, 48, 190, 46, lambda: self.window.show_view(CircuitSelectionView(self.app, self.session)), NAVY, WHITE, CYAN)

    def open_race(self) -> None:
        self.window.show_view(RacingBridgeView(self.app, self.session, self.route))

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        _text("TRACK EXPLORER", 54, height - 80, 40, WHITE, bold=True)
        _text("ARCADE MIGRATION BRIDGE", 56, height - 111, 14, AMBER, bold=True)
        track = self.session.selected_track
        _text(track.name, 56, height - 160, 26, CYAN, bold=True)
        _text(f"Mode: {self.session.mode.upper()}   |   All route data comes from the authoritative graph", 56, height - 188, 14, MUTED)
        map_rect = (48, 130, width * 0.57, height - 350)
        self.draw_panel(*map_rect, 235)
        self.draw_graph_map(track, map_rect)
        info_x = map_rect[0] + map_rect[2] + 34
        info_w = width - info_x - 48
        info_y = height - 220
        self.draw_panel(info_x, 130, info_w, height - 350, 235)
        _text("PLANNING STATUS", info_x + 22, info_y, 18, WHITE, bold=True)
        _text("Checkpoint-aware Dijkstra", info_x + 22, info_y - 40, 14, CYAN)
        _text(f"Checkpoints: {len(track.checkpoint_ids)} mandatory, ordered", info_x + 22, info_y - 70, 13, MUTED)
        _text(f"Roads: {len(track.edges)} directed/undirected edges", info_x + 22, info_y - 96, 13, MUTED)
        if self.route and self.route.get("metrics"):
            metrics = self.route["metrics"]
            _text("ROUTE READY", info_x + 22, info_y - 145, 16, EMERALD, bold=True)
            _text(f"Weighted cost: {metrics.get('weighted_cost', 0):.2f}", info_x + 22, info_y - 175, 13, WHITE)
            _text(f"Distance: {metrics.get('distance', 0):.1f}   Time: {metrics.get('travel_time', 0):.1f}s", info_x + 22, info_y - 201, 13, WHITE)
            _text(f"Path vertices: {len(self.route.get('path', []))}", info_x + 22, info_y - 227, 13, MUTED)
        else:
            _text("No valid route found", info_x + 22, info_y - 145, 16, CORAL)
        _text("Temporary Arcade destination; return path is functional.", info_x + 22, 154, 12, AMBER)
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()

    def draw_graph_map(self, track, rect) -> None:
        left, bottom, width, height = rect
        graph = track.graph()
        xs = [vertex.x for vertex in graph.vertices.values()]
        ys = [vertex.y for vertex in graph.vertices.values()]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)

        def point(vertex):
            px = left + 24 + (vertex.x - xmin) / max(1, xmax - xmin) * (width - 48)
            py = bottom + 24 + (vertex.y - ymin) / max(1, ymax - ymin) * (height - 48)
            return px, py

        route_edges = set(zip(self.route.get("path", []), self.route.get("path", [])[1:])) if self.route else set()
        for edge in graph.edges.values():
            source, target = graph.vertices[edge.from_id], graph.vertices[edge.to_id]
            a, b = point(source), point(target)
            color = (97, 116, 137) if edge.status == EdgeStatus.OPEN else CORAL
            arcade.draw_line(*a, *b, color, 5 if not edge.is_shortcut else 3)
            if (edge.from_id, edge.to_id) in route_edges:
                arcade.draw_line(*a, *b, CYAN, 9)
                arcade.draw_line(*a, *b, WHITE, 3)
            if edge.directed:
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                arcade.draw_circle_filled(mx, my, 3, AMBER)
        for vertex in graph.vertices.values():
            px, py = point(vertex)
            color = MUTED
            radius = 5
            if vertex.type == VertexType.START:
                color, radius = EMERALD, 10
            elif vertex.type == VertexType.FINISH:
                color, radius = CORAL, 10
            elif vertex.checkpoint_order:
                color, radius = AMBER, 8
            elif vertex.type == VertexType.FUEL_STATION:
                color, radius = CYAN, 8
            elif vertex.type == VertexType.NITRO_PICKUP:
                color, radius = PURPLE, 8
            arcade.draw_circle_filled(px, py, radius, color)
            if vertex.checkpoint_order or vertex.type in {VertexType.START, VertexType.FINISH}:
                _text(str(vertex.checkpoint_order or ("S" if vertex.type == VertexType.START else "F")), px, py - 4, 9, NAVY, anchor_x="center")


class TrackExplorerView(ArcadeView):
    """Authoritative graph explorer and checkpoint-aware route planner."""

    ALGORITHMS = ("BFS", "DFS", "Dijkstra", "A*")
    PRESETS = ("balanced", "speed", "economy", "safety")

    def __init__(self, window: ArcadeApp, session: GameSession):
        self.track_index = next(
            (index for index, track in enumerate(session.tracks) if track.id == session.selected_track_id),
            0,
        )
        self.algorithm = session.selected_algorithm if session.selected_algorithm in self.ALGORITHMS else "Dijkstra"
        self.preset = "balanced"
        self.checkpoint_aware = True
        self.selection_mode = "source"
        self.source_id = 0
        self.destination_id = 0
        self.selected_vertex_id: int | None = None
        self.hover_vertex_id: int | None = None
        self.hover_edge_id: int | None = None
        self.route_result: dict | None = None
        self.comparison: dict[str, dict] = {}
        self.graph = None
        self.validation = None
        self.status_message = "Select a source or destination vertex, then calculate a route."
        self.status_color = MUTED
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.panel_scroll = 0
        self.drag_anchor: tuple[float, float] | None = None
        self.dragged = False
        self._last_mouse_position = (0.0, 0.0)
        self.map_rect = (0, 0, 1, 1)
        self.side_rect = (0, 0, 1, 1)
        super().__init__(window, session)
        self.load_track(reset_route=True)
        if self.validation.valid:
            self.calculate_route()

    @property
    def track(self):
        return self.session.tracks[self.track_index]

    def load_track(self, reset_route: bool = True) -> None:
        # Explorer events are session-local overlays.  Deep-copying prevents a
        # temporary closure in the planning screen from mutating the race
        # engine's authoritative track definition.
        self.graph = deepcopy(self.track.graph())
        self.validation = TrackValidator().validate(self.track)
        self.source_id = self.track.start_id
        self.destination_id = self.track.finish_id
        self.selected_vertex_id = self.source_id
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.panel_scroll = 0
        if reset_route:
            self.route_result = None
            self.comparison = {}
        if self.validation.valid:
            self.status_message = "Circuit validated. Select vertices or calculate the default lap plan."
            self.status_color = EMERALD
        else:
            self.status_message = "Validation error: " + self.validation.errors[0]
            self.status_color = CORAL

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, height = self.window.width, self.window.height
        self.map_rect = (18, 70, int(width * 0.68) - 30, max(250, height - 138))
        side_left = int(width * 0.70)
        self.side_rect = (side_left, 70, width - side_left - 18, max(250, height - 138))
        nav_y = height - 56
        self.add_button("BACK", 18, nav_y, 92, 38, self.go_menu, NAVY, WHITE, CYAN)
        self.add_button("‹", 122, nav_y, 38, 38, lambda: self.switch_circuit(-1), NAVY, WHITE, CYAN)
        self.add_button("›", 166, nav_y, 38, 38, lambda: self.switch_circuit(1), NAVY, WHITE, CYAN)
        self.add_button("RESET VIEW", 214, nav_y, 126, 38, self.reset_view, NAVY, WHITE, CYAN)
        self.add_button("ALGORITHM LAB", 350, nav_y, 160, 38, self.open_lab, NAVY, WHITE, CYAN)

        left, bottom, width, height = self.side_rect
        algorithm_y = bottom + height - 100
        button_width = max(58, (width - 48) / 4)
        for index, algorithm in enumerate(self.ALGORITHMS):
            fill = CYAN if algorithm == self.algorithm else NAVY
            text = NAVY if algorithm == self.algorithm else WHITE
            self.add_button(
                algorithm,
                left + 12 + index * button_width,
                algorithm_y,
                button_width - 4,
                34,
                lambda algorithm=algorithm: self.set_algorithm(algorithm),
                fill,
                text,
                CYAN,
            )
        preset_y = algorithm_y - 45
        preset_width = max(58, (width - 48) / 4)
        for index, preset in enumerate(self.PRESETS):
            applicable = self.algorithm in {"Dijkstra", "A*"}
            fill = CYAN if applicable and preset == self.preset else PANEL_DARK
            text = NAVY if applicable and preset == self.preset else (MUTED if not applicable else WHITE)
            self.add_button(
                preset.title(),
                left + 12 + index * preset_width,
                preset_y,
                preset_width - 4,
                32,
                lambda preset=preset: self.set_preset(preset),
                fill,
                text,
                (83, 112, 139),
            )
        select_y = preset_y - 47
        self.add_button("SOURCE", left + 12, select_y, (width - 30) / 2, 34, lambda: self.set_selection_mode("source"), EMERALD if self.selection_mode == "source" else NAVY, NAVY if self.selection_mode == "source" else WHITE, EMERALD)
        self.add_button("DESTINATION", left + 18 + (width - 30) / 2, select_y, (width - 30) / 2, 34, lambda: self.set_selection_mode("destination"), EMERALD if self.selection_mode == "destination" else NAVY, NAVY if self.selection_mode == "destination" else WHITE, EMERALD)
        action_y = select_y - 49
        self.add_button("CALCULATE ROUTE", left + 12, action_y, width - 24, 38, self.calculate_route, CYAN, NAVY, CYAN)
        compare_y = action_y - 47
        self.add_button("COMPARE ROUTES", left + 12, compare_y, (width - 30) / 2, 34, self.compare_routes, NAVY, WHITE, CYAN)
        self.add_button("PLAN RESOURCES", left + 18 + (width - 30) / 2, compare_y, (width - 30) / 2, 34, self.plan_resources, NAVY, WHITE, CYAN)
        toggle_y = compare_y - 47
        self.add_button("CHECKPOINT MODE: ON" if self.checkpoint_aware else "CHECKPOINT MODE: OFF", left + 12, toggle_y, width - 24, 32, self.toggle_checkpoint_mode, NAVY, WHITE, AMBER)
        event_y = toggle_y - 44
        self.add_button("TOGGLE ROAD EVENT", left + 12, event_y, width - 24, 32, self.toggle_closure, NAVY, WHITE, CORAL)
        start_y = bottom + 12
        self.add_button("START RACE", left + 12, start_y, width - 24, 40, self.start_race, EMERALD, NAVY, EMERALD)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def go_menu(self) -> None:
        self.app.show_view(MainMenuView(self.app, self.session))

    def open_lab(self) -> None:
        self.session.selected_algorithm = self.algorithm
        self.session.save_state()
        self.app.show_view(AlgorithmLabView(self.app, self.session))

    def reset_view(self) -> None:
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.panel_scroll = 0
        self.status_message = "Map view reset; route/session state preserved."
        self.status_color = CYAN

    def switch_circuit(self, delta: int) -> None:
        if self.session.mode == "championship":
            self.status_message = "Championship order locks circuit switching for the scheduled race."
            self.status_color = AMBER
            return
        self.track_index = (self.track_index + delta) % len(self.session.tracks)
        self.session.selected_track_id = self.session.tracks[self.track_index].id
        self.session.save_state()
        self.load_track()
        self.rebuild_ui()

    def set_algorithm(self, algorithm: str) -> None:
        self.algorithm = algorithm
        self.session.selected_algorithm = algorithm
        self.route_result = None
        self.comparison = {}
        self.status_message = f"{algorithm} selected. {ALGORITHM_COMPLEXITY[algorithm]}"
        self.status_color = CYAN
        self.rebuild_ui()

    @property
    def planner_algorithm(self) -> str:
        return "astar" if self.algorithm == "A*" else self.algorithm.lower()

    def set_preset(self, preset: str) -> None:
        if self.algorithm not in {"Dijkstra", "A*"}:
            self.status_message = "Weighted presets are not applicable to BFS or DFS."
            self.status_color = AMBER
            return
        self.preset = preset
        self.route_result = None
        self.comparison = {}
        self.status_message = f"{preset.title()} preset selected; calculate to recompute the weighted route."
        self.status_color = CYAN
        self.rebuild_ui()

    def set_selection_mode(self, mode: str) -> None:
        self.selection_mode = mode
        self.status_message = f"Click a vertex on the map to choose the {mode}."
        self.status_color = CYAN
        self.rebuild_ui()

    def toggle_checkpoint_mode(self) -> None:
        self.checkpoint_aware = not self.checkpoint_aware
        self.route_result = None
        self.comparison = {}
        self.status_message = "Checkpoint-aware routing is " + ("enabled." if self.checkpoint_aware else "disabled; race start will be rejected.")
        self.status_color = AMBER if not self.checkpoint_aware else CYAN
        self.rebuild_ui()

    def calculate_route(self) -> None:
        if not self.validation.valid:
            self.route_result = None
            self.status_message = "Cannot calculate: " + self.validation.errors[0]
            self.status_color = CORAL
            return
        preset = self.preset if self.algorithm in {"Dijkstra", "A*"} else "balanced"
        planner = RoutePlanner(self.track, preset)
        planner.graph = self.graph
        try:
            result = planner.plan_route(
                self.source_id,
                self.destination_id,
                algorithm=self.planner_algorithm,
                checkpoint_aware=self.checkpoint_aware,
            )
        except (KeyError, ValueError) as exc:
            result = None
            self.status_message = f"Route error: {exc}"
            self.status_color = CORAL
        self.route_result = result
        if result is None or not result.get("metrics", {}).get("valid"):
            self.status_message = "Destination is unreachable under the current directed/open-road graph."
            self.status_color = CORAL
            self.comparison = {}
            return
        self.status_message = "Route calculated from the authoritative graph."
        self.status_color = EMERALD
        self.comparison = {}
        self.rebuild_ui()

    def plan_resources(self) -> None:
        self.calculate_route()
        if self.route_result:
            resources = self.route_result.get("resources", {})
            stops = len(resources.get("required_refuelling_stops", []))
            nitro_ready = bool(resources.get("nitro", {}).get("dp"))
            self.status_message = f"Resource plan ready: fuel {'feasible' if resources.get('fuel_feasible') else 'infeasible'}, {stops} refuel stop(s), nitro {'available' if nitro_ready else 'unavailable'}."
            self.status_color = EMERALD if resources.get("fuel_feasible") else CORAL
            self.rebuild_ui()

    def compare_routes(self) -> None:
        if self.route_result is None:
            self.calculate_route()
        if self.route_result is None:
            return
        planner = RoutePlanner(self.track, self.preset if self.algorithm in {"Dijkstra", "A*"} else "balanced")
        planner.graph = self.graph
        if self.algorithm in {"Dijkstra", "A*"}:
            self.comparison = planner.compare_presets(
                self.source_id,
                self.destination_id,
                self.planner_algorithm,
                checkpoint_aware=self.checkpoint_aware,
            )
        else:
            weighted = planner.plan_route(
                self.source_id,
                self.destination_id,
                algorithm="dijkstra",
                checkpoint_aware=self.checkpoint_aware,
            )
            self.comparison = {"selected": self.route_result, "Dijkstra balanced": weighted}
        self.status_message = f"Compared {len([item for item in self.comparison.values() if item])} valid route candidates."
        self.status_color = CYAN

    def start_race(self) -> None:
        if not self.validation.valid:
            self.status_message = "Race blocked: circuit validation failed."
            self.status_color = CORAL
            return
        if not self.checkpoint_aware:
            self.status_message = "Race blocked: enable checkpoint-aware routing first."
            self.status_color = CORAL
            return
        if self.source_id != self.track.start_id:
            self.status_message = "Race blocked: source must be the circuit start vertex."
            self.status_color = CORAL
            return
        if self.route_result is None:
            self.calculate_route()
        if not self.route_result or not self.route_result.get("resources", {}).get("fuel_feasible", False):
            self.status_message = "Race blocked: route has no feasible fuel plan."
            self.status_color = CORAL
            return
        metrics = self.route_result["metrics"]
        resources = self.route_result.get("resources", {})
        self.session.set_route_plan(
            {
                "track_id": self.track.id,
                "algorithm": self.algorithm,
                "preset": self.preset if self.algorithm in {"Dijkstra", "A*"} else None,
                "source": self.source_id,
                "destination": self.destination_id,
                "checkpoint_aware": self.checkpoint_aware,
                "path": list(self.route_result["path"]),
                "edge_ids": list(metrics.get("edge_ids", [])),
                "metrics": {key: value for key, value in metrics.items() if isinstance(value, (bool, int, float, str))},
                "fuel_feasible": bool(resources.get("fuel_feasible", False)),
                "required_refuelling_stops": resources.get("required_refuelling_stops", []),
            }
        )
        self.app.show_view(ArcadeRacingView(self.app, self.session))

    def toggle_closure(self) -> None:
        edge_ids = self.route_result.get("metrics", {}).get("edge_ids", []) if self.route_result else []
        edge_id = edge_ids[0] if edge_ids else next(iter(self.graph.edges), None)
        if edge_id is None:
            return
        edge = self.graph.edges[edge_id]
        edge.status = EdgeStatus.OPEN if edge.status == EdgeStatus.BLOCKED else EdgeStatus.BLOCKED
        self.status_message = f"Road {edge_id} is now {edge.status.value}; routes must be recalculated."
        self.status_color = CORAL if edge.status == EdgeStatus.BLOCKED else AMBER
        self.calculate_route()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.go_menu()
        elif symbol == arcade.key.S:
            self.set_selection_mode("source")
        elif symbol == arcade.key.D:
            self.set_selection_mode("destination")
        elif symbol in (arcade.key.PLUS, arcade.key.NUM_ADD, arcade.key.EQUAL):
            self.zoom = min(2.5, self.zoom * 1.12)
        elif symbol in (arcade.key.MINUS, arcade.key.NUM_SUBTRACT):
            self.zoom = max(0.55, self.zoom / 1.12)
        elif symbol == arcade.key.KEY_0:
            self.reset_view()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        super().on_mouse_motion(x, y, dx, dy)
        self._last_mouse_position = (x, y)
        if self.drag_anchor is None:
            self.hover_vertex_id = self.nearest_vertex(x, y)
            self.hover_edge_id = None if self.hover_vertex_id is not None else self.nearest_edge(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        if self.map_contains(x, y):
            vertex_id = self.nearest_vertex(x, y)
            if vertex_id is not None:
                self.selected_vertex_id = vertex_id
                if self.selection_mode == "source":
                    self.source_id = vertex_id
                else:
                    self.destination_id = vertex_id
                self.status_message = f"{self.selection_mode.title()} set to vertex {vertex_id}; calculate to update the route."
                self.status_color = CYAN
                return
            self.drag_anchor = (x, y)
            self.dragged = False

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int):
        if self.drag_anchor is not None:
            self.pan[0] += dx
            self.pan[1] += dy
            self.dragged = True

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.drag_anchor = None

    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        if self.side_rect[0] <= x <= self.side_rect[0] + self.side_rect[2]:
            self.panel_scroll = _clamp(self.panel_scroll - scroll_y * 26, 0, 260)
        elif self.map_contains(x, y):
            self.zoom = _clamp(self.zoom * (1.12 if scroll_y > 0 else 1 / 1.12), 0.55, 2.5)

    def map_contains(self, x: float, y: float) -> bool:
        left, bottom, width, height = self.map_rect
        return left <= x <= left + width and bottom <= y <= bottom + height

    def map_transform(self):
        vertices = list(self.graph.vertices.values())
        xs = [vertex.x for vertex in vertices]
        ys = [vertex.y for vertex in vertices]
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        left, bottom, width, height = self.map_rect
        base = min((width - 62) / max(1.0, xmax - xmin), (height - 62) / max(1.0, ymax - ymin))
        return xmin, xmax, ymin, ymax, base

    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        xmin, xmax, ymin, ymax, base = self.map_transform()
        left, bottom, width, height = self.map_rect
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        scale = base * self.zoom
        return left + width / 2 + (x - cx) * scale + self.pan[0], bottom + height / 2 + (y - cy) * scale + self.pan[1]

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        xmin, xmax, ymin, ymax, base = self.map_transform()
        left, bottom, width, height = self.map_rect
        scale = base * self.zoom
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        return cx + (x - left - width / 2 - self.pan[0]) / scale, cy + (y - bottom - height / 2 - self.pan[1]) / scale

    def nearest_vertex(self, x: float, y: float) -> int | None:
        if not self.map_contains(x, y):
            return None
        candidates = []
        for vertex in self.graph.vertices.values():
            px, py = self.world_to_screen(vertex.x, vertex.y)
            distance = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
            if distance <= 17:
                candidates.append((distance, vertex.id))
        return min(candidates)[1] if candidates else None

    def nearest_edge(self, x: float, y: float) -> int | None:
        if not self.map_contains(x, y):
            return None
        best = (12.0, None)
        for edge in self.graph.edges.values():
            source = self.graph.vertices[edge.from_id]
            target = self.graph.vertices[edge.to_id]
            ax, ay = self.world_to_screen(source.x, source.y)
            bx, by = self.world_to_screen(target.x, target.y)
            dx, dy = bx - ax, by - ay
            length_sq = dx * dx + dy * dy or 1
            t = _clamp(((x - ax) * dx + (y - ay) * dy) / length_sq, 0, 1)
            px, py = ax + t * dx, ay + t * dy
            distance = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
            if distance < best[0]:
                best = (distance, edge.id)
        return best[1]

    def graph_summary(self) -> tuple[int, int, int, int]:
        reachable = set()
        todo = [self.source_id]
        while todo:
            current = todo.pop()
            if current in reachable:
                continue
            reachable.add(current)
            todo.extend(target for target, _ in self.graph.neighbors(current))
        dead_ends = sum(1 for vertex in self.graph.vertices.values() if vertex.type == VertexType.DEAD_END)
        cycle = False
        visited, stack = set(), set()

        def visit(vertex_id: int) -> bool:
            nonlocal cycle
            visited.add(vertex_id)
            stack.add(vertex_id)
            for target, _ in self.graph.neighbors(vertex_id):
                if target not in visited and visit(target):
                    return True
                if target in stack:
                    return True
            stack.remove(vertex_id)
            return False

        for vertex_id in self.graph.vertices:
            if vertex_id not in visited and visit(vertex_id):
                cycle = True
                break
        alternatives = len({tuple(report.get("path", [])) for report in self.comparison.values() if report and report.get("path")})
        return len(reachable), dead_ends, int(cycle), alternatives

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)
        title_center = max(650, width * 0.50)
        _text("TRACK EXPLORER", title_center, height - 39, 24, WHITE, anchor_x="center", anchor_y="center", bold=True)
        _text(self.track.name, title_center, height - 61, 11, CYAN, anchor_x="center", anchor_y="center")
        _text(f"MODE  {self.session.mode.upper()}", width - 24, height - 38, 12, MUTED, anchor_x="right", anchor_y="center")
        self.draw_map()
        self.draw_side_panel()
        self.draw_legend()
        self.ui.draw()
        self.draw_focus()
        self.draw_tooltip()
        self.capture_smoke()

    def draw_map(self) -> None:
        left, bottom, width, height = self.map_rect
        self.draw_panel(left, bottom, width, height, 245)
        theme_color = {"emerald": (27, 80, 58), "canyon": (113, 70, 39), "metro": (32, 45, 78)}.get(self.track.theme, (30, 45, 60))
        arcade.draw_lbwh_rectangle_filled(left + 1, bottom + 1, width - 2, height - 2, (*theme_color, 105))
        self.draw_environment()
        for edge in self.graph.edges.values():
            if self.route_result and edge.id in self.route_result.get("metrics", {}).get("edge_ids", []):
                continue
            source, target = self.graph.vertices[edge.from_id], self.graph.vertices[edge.to_id]
            a, b = self.world_to_screen(source.x, source.y), self.world_to_screen(target.x, target.y)
            if edge.status == EdgeStatus.BLOCKED:
                road, border = (67, 28, 38), CORAL
            elif edge.status == EdgeStatus.RESTRICTED:
                road, border = (84, 68, 31), AMBER
            else:
                road, border = (66, 76, 91), (120, 137, 154)
            arcade.draw_line(*a, *b, border, 14 if edge.is_shortcut else 16)
            arcade.draw_line(*a, *b, road, 9 if edge.is_shortcut else 11)
            if edge.is_shortcut and edge.status != EdgeStatus.BLOCKED:
                arcade.draw_line(*a, *b, PURPLE, 3)
            if edge.directed:
                self.draw_arrow(a, b, AMBER if edge.status != EdgeStatus.BLOCKED else CORAL)
            if edge.status == EdgeStatus.BLOCKED:
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                arcade.draw_line(mx - 9, my - 9, mx + 9, my + 9, CORAL, 3)
                arcade.draw_line(mx - 9, my + 9, mx + 9, my - 9, CORAL, 3)
        comparison_paths = []
        colors = [AMBER, PURPLE, (244, 114, 182), (134, 239, 172)]
        for index, report in enumerate(self.comparison.values()):
            if report and report.get("path"):
                comparison_paths.append((report["path"], colors[index % len(colors)]))
        for path, color in comparison_paths:
            self.draw_path(path, color, 4, False)
        if self.route_result and self.route_result.get("path"):
            self.draw_path(self.route_result["path"], CYAN, 10, True)
        for vertex in self.graph.vertices.values():
            self.draw_vertex(vertex)

    def draw_environment(self) -> None:
        left, bottom, width, height = self.map_rect
        if self.track.theme == "emerald":
            for index in range(18):
                x = left + 16 + (index * 83) % max(30, int(width - 25))
                y = bottom + 18 + (index * 47) % max(30, int(height - 25))
                arcade.draw_circle_filled(x, y, 9, (22, 95, 57, 90))
                arcade.draw_circle_filled(x + 5, y + 7, 6, (44, 135, 76, 80))
        elif self.track.theme == "canyon":
            for index in range(12):
                x = left + 20 + (index * 111) % max(40, int(width - 35))
                y = bottom + 20 + (index * 63) % max(40, int(height - 35))
                arcade.draw_triangle_filled(x - 15, y - 10, x, y + 15, x + 15, y - 10, (137, 83, 43, 75))
        else:
            for index in range(15):
                x = left + 20 + (index * 97) % max(40, int(width - 35))
                y = bottom + 20 + (index * 53) % max(40, int(height - 35))
                arcade.draw_lbwh_rectangle_filled(x - 8, y - 8, 16, 16, (36, 57, 95, 90))

    def draw_path(self, path: list[int], color, line_width: int, selected: bool) -> None:
        for source_id, target_id in zip(path, path[1:]):
            source, target = self.graph.vertices.get(source_id), self.graph.vertices.get(target_id)
            if source is None or target is None:
                continue
            a, b = self.world_to_screen(source.x, source.y), self.world_to_screen(target.x, target.y)
            if selected:
                arcade.draw_line(*a, *b, (4, 21, 34), line_width + 8)
            arcade.draw_line(*a, *b, color, line_width)
            self.draw_arrow(a, b, WHITE if selected else color)

    @staticmethod
    def draw_arrow(a, b, color) -> None:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        points = [(mx + ux * 9, my + uy * 9), (mx - ux * 5 + px * 5, my - uy * 5 + py * 5), (mx - ux * 5 - px * 5, my - uy * 5 - py * 5)]
        arcade.draw_polygon_filled(points, color)

    def draw_vertex(self, vertex) -> None:
        px, py = self.world_to_screen(vertex.x, vertex.y)
        if vertex.id == self.source_id:
            arcade.draw_circle_outline(px, py, 18, EMERALD, 3)
        if vertex.id == self.destination_id:
            arcade.draw_circle_outline(px, py, 22, WHITE, 3)
        color, radius = MUTED, 5
        if vertex.type == VertexType.START:
            color, radius = EMERALD, 11
        elif vertex.type == VertexType.FINISH:
            color, radius = CORAL, 11
        elif vertex.checkpoint_order:
            color, radius = AMBER, 9
        elif vertex.type == VertexType.FUEL_STATION:
            color, radius = CYAN, 9
        elif vertex.type == VertexType.NITRO_PICKUP:
            color, radius = PURPLE, 9
        elif vertex.type == VertexType.DEAD_END:
            color, radius = CORAL, 7
        arcade.draw_circle_filled(px, py, radius, color)
        if vertex.checkpoint_order:
            label = f"CP{vertex.checkpoint_order}"
        elif vertex.type == VertexType.START:
            label = "S"
        elif vertex.type == VertexType.FINISH:
            label = "F"
        elif vertex.type == VertexType.FUEL_STATION:
            label = "FUEL"
        elif vertex.type == VertexType.NITRO_PICKUP:
            label = "N"
        else:
            label = str(vertex.id)
        _text(label, px, py + radius + 4, 10 if len(label) < 4 else 8, WHITE, anchor_x="center", anchor_y="bottom", bold=True)

    def draw_side_panel(self) -> None:
        left, bottom, width, height = self.side_rect
        self.draw_panel(left, bottom, width, height, 245)
        _text("ROUTE PLANNER", left + 14, bottom + height - 28, 17, WHITE, bold=True)
        _text("Click the map to select vertices", left + 14, bottom + height - 48, 11, MUTED)
        body_top = bottom + height - 410 - self.panel_scroll
        reachable, dead_ends, cycle, alternatives = self.graph_summary()
        lines = [
            ("VALIDATION", self.status_color, True),
            ("Graph valid" if self.validation.valid else "Graph invalid", EMERALD if self.validation.valid else CORAL, False),
            (f"Reachable vertices: {reachable}/{len(self.graph.vertices)}", MUTED, False),
            (f"Cycle: {'yes' if cycle else 'no'}   Dead ends: {dead_ends}", MUTED, False),
            (f"Alternative candidates: {alternatives}", MUTED, False),
            (f"Source: {self.source_id}   Destination: {self.destination_id}", WHITE, False),
            (self.status_message, self.status_color, False),
        ]
        wrapped_lines = []
        max_chars = max(18, int((width - 28) / 8.5))
        for line, color, heading in lines:
            parts = textwrap.wrap(line, width=max_chars, break_long_words=False) or [""]
            wrapped_lines.extend((part, color, heading) for part in parts)
        for index, (line, color, heading) in enumerate(wrapped_lines):
            y = body_top - index * 20
            if bottom + 62 < y < bottom + height - 285:
                _text(line, left + 14, y, 12 if not heading else 13, color, bold=heading)
        if self.route_result:
            metrics = self.route_result.get("metrics", {})
            counters = self.route_result.get("counters")
            route_lines = [
                ("ROUTE METRICS", WHITE, True),
                (f"Algorithm: {self.algorithm}", WHITE, False),
                (f"Complexity: {self.route_result.get('complexity', 'n/a')}", MUTED, False),
                (f"Distance: {metrics.get('distance', 0):.1f}", WHITE, False),
                (f"Travel time: {metrics.get('travel_time', 0):.1f}s", WHITE, False),
                (f"Fuel demand: {metrics.get('fuel', 0):.1f}", WHITE, False),
                (f"Weighted cost: {metrics.get('weighted_cost', 0):.3f}", CYAN, False),
                (f"Risk/difficulty: {metrics.get('risk', 0):.1f}", MUTED, False),
                (f"Visited: {getattr(counters, 'visited_vertices', 0)}  Expanded: {getattr(counters, 'expanded_vertices', 0)}", MUTED, False),
                (f"Edges examined: {getattr(counters, 'examined_edges', 0)}  Relaxed: {getattr(counters, 'relaxed_edges', 0)}", MUTED, False),
                (f"Heap operations: {getattr(counters, 'heap_operations', 0)}", MUTED, False),
                (f"Compute time: {self.route_result.get('elapsed_ms', 0):.2f}ms", MUTED, False),
            ]
            if self.algorithm in {"BFS", "DFS"}:
                route_lines.insert(3, ("BFS/DFS finds a feasible route; it does not optimize weighted cost.", AMBER, False))
            resource = self.route_result.get("resources", {})
            route_lines.extend([
                ("RESOURCE PLAN", WHITE, True),
                (f"Fuel feasible: {'YES' if resource.get('fuel_feasible') else 'NO'}", EMERALD if resource.get("fuel_feasible") else CORAL, False),
                (f"Refuel stops: {len(resource.get('required_refuelling_stops', []))}", MUTED, False),
                (f"Nitro DP/Greedy: {'ready' if resource.get('nitro', {}).get('dp') else 'none'}", PURPLE, False),
            ])
            route_wrapped = []
            for line, color, heading in route_lines:
                parts = textwrap.wrap(line, width=max_chars, break_long_words=False) or [""]
                route_wrapped.extend((part, color, heading) for part in parts)
            route_start = len(wrapped_lines)
            for index, (line, color, heading) in enumerate(route_wrapped, start=route_start + 1):
                y = body_top - index * 20
                if bottom + 62 < y < bottom + height - 285:
                    _text(line, left + 14, y, 12 if not heading else 13, color, bold=heading)
        if self.comparison:
            compare_y = bottom + 52
            _text("COMPARISON", left + 14, compare_y + 16, 12, WHITE, bold=True)
            labels = list(self.comparison.items())[:4]
            for index, (label, report) in enumerate(labels):
                if report is None:
                    continue
                metrics = report.get("metrics", {})
                _text(f"{label}: {metrics.get('distance', 0):.0f}m / {metrics.get('weighted_cost', 0):.2f}", left + 14, compare_y - index * 17, 10, CYAN if report is self.route_result else MUTED, width=width - 28)

    def draw_legend(self) -> None:
        _, _, map_width, _ = self.map_rect
        items = [("CP", AMBER), ("FUEL", CYAN), ("NITRO", PURPLE), ("SHORTCUT", PURPLE), ("BLOCKED", CORAL), ("ROUTE", CYAN)]
        x, y = 26, 22
        for label, color in items:
            arcade.draw_circle_filled(x, y + 3, 5, color)
            _text(label, x + 10, y, 10, MUTED)
            x += 75 if label != "SHORTCUT" else 92
        _text("Wheel: zoom/panel scroll   Drag: pan   S/D: select source/destination", map_width - 8, y, 10, MUTED, anchor_x="right")

    def draw_tooltip(self) -> None:
        vertex_id = self.hover_vertex_id
        edge_id = self.hover_edge_id
        if vertex_id is None and edge_id is None:
            return
        x, y = self._last_mouse_position if hasattr(self, "_last_mouse_position") else (self.map_rect[0] + 20, self.map_rect[1] + 20)
        if vertex_id is not None:
            vertex = self.graph.vertices[vertex_id]
            text = f"V{vertex.id}  {vertex.type.value}"
            if vertex.checkpoint_order:
                text += f"  CP{vertex.checkpoint_order}"
        else:
            edge = self.graph.edges[edge_id]
            text = f"Road {edge.id}: {edge.from_id} → {edge.to_id}  {edge.status.value}  {edge.distance:.1f}m"
        width = min(300, max(180, len(text) * 7))
        x = _clamp(x + 14, self.map_rect[0] + 4, self.map_rect[0] + self.map_rect[2] - width - 4)
        y = _clamp(y - 34, self.map_rect[1] + 4, self.map_rect[1] + self.map_rect[3] - 30)
        arcade.draw_lbwh_rectangle_filled(x, y, width, 26, (8, 17, 29, 245))
        arcade.draw_lbwh_rectangle_outline(x, y, width, 26, CYAN, 1)
        _text(text, x + 8, y + 8, 10, WHITE)


class RacingBridgeView(ArcadeView):
    def __init__(self, window: ArcadeApp, session: GameSession, route):
        self.route = route
        self.preview_results = None
        super().__init__(window, session)

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, _ = self.window.width, self.window.height
        self.add_button("RUN DETERMINISTIC PREVIEW", width / 2 - 150, 180, 300, 48, self.run_preview, CYAN, NAVY, CYAN)
        self.add_button("BACK TO TRACK EXPLORER", width / 2 - 150, 112, 300, 44, lambda: self.window.show_view(TrackExplorerView(self.app, self.session)), NAVY, WHITE, CYAN)
        self.add_button("BACK TO MAIN MENU", width / 2 - 150, 52, 300, 44, self.go_menu, NAVY, WHITE, CYAN)

    def run_preview(self) -> None:
        from smart_racing.services.race_engine import RaceEngine

        self.preview_results = RaceEngine(self.session.selected_track).run()
        self.rebuild_ui()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        _text("RACING SCREEN", width / 2, height - 100, 44, WHITE, anchor_x="center", bold=True)
        _text("ARCADE MIGRATION BRIDGE", width / 2, height - 136, 14, AMBER, anchor_x="center", bold=True)
        self.draw_panel(width * 0.18, 270, width * 0.64, 270)
        _text(self.session.selected_track.name, width / 2, 488, 25, CYAN, anchor_x="center", bold=True)
        _text(f"Mode: {self.session.mode.upper()}   |   Route configuration preserved", width / 2, 454, 15, MUTED, anchor_x="center")
        _text("The existing deterministic race engine remains authoritative while the Arcade racing view is migrated.", width / 2, 414, 14, MUTED, anchor_x="center")
        if self.preview_results:
            _text("PREVIEW COMPLETE", width / 2, 354, 18, EMERALD, anchor_x="center", bold=True)
            summary = "   ".join(f"P{result.finish_position}: {result.name}" for result in self.preview_results)
            _text(summary, width / 2, 322, 13, WHITE, anchor_x="center")
        else:
            _text("Use the deterministic preview to verify the shared race engine.", width / 2, 354, 14, WHITE, anchor_x="center")
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()


class AlgorithmLabBridgeView(ArcadeView):
    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, _ = self.window.width, self.window.height
        self.add_button("BACK TO MAIN MENU", width / 2 - 130, 52, 260, 46, self.go_menu, NAVY, WHITE, CYAN)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        _text("ALGORITHM LAB", width / 2, height - 105, 44, WHITE, anchor_x="center", bold=True)
        _text("ARCADE MIGRATION BRIDGE", width / 2, height - 140, 14, AMBER, anchor_x="center", bold=True)
        self.draw_panel(width * 0.18, 188, width * 0.64, 360)
        _text("Shared algorithm library detected", width / 2, 494, 22, EMERALD, anchor_x="center", bold=True)
        _text("BFS   DFS   Dijkstra   A*   DP   Greedy   Backtracking   Kruskal", width / 2, 445, 16, CYAN, anchor_x="center")
        _text("Step visualizer remains in the Pygame Lab until Arcade migration.", width / 2, 380, 15, MUTED, anchor_x="center")
        _text("This temporary destination is functional, explicit, and returns safely to the main menu.", width / 2, 332, 14, WHITE, anchor_x="center")
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()


