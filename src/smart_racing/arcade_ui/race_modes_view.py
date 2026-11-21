from __future__ import annotations

import textwrap

import arcade

from smart_racing.arcade_ui.app import (
    AMBER,
    CORAL,
    CYAN,
    EMERALD,
    MUTED,
    NAVY,
    PURPLE,
    WHITE,
    ArcadeView,
    _text,
)
from smart_racing.model.graph import EdgeStatus, VertexType


class _TrackPreviewMixin:
    def draw_track_preview(self, track, left: float, bottom: float, width: float, height: float) -> None:
        self.draw_panel(left, bottom, width, height, 248)
        graph = track.graph()
        vertices = list(graph.vertices.values())
        xmin, xmax = min(v.x for v in vertices), max(v.x for v in vertices)
        ymin, ymax = min(v.y for v in vertices), max(v.y for v in vertices)
        scale = min((width - 54) / max(1, xmax - xmin), (height - 72) / max(1, ymax - ymin))

        def point(vertex):
            return (
                left + width / 2 + (vertex.x - (xmin + xmax) / 2) * scale,
                bottom + height / 2 + (vertex.y - (ymin + ymax) / 2) * scale,
            )

        for edge in graph.edges.values():
            a, b = point(graph.vertices[edge.from_id]), point(graph.vertices[edge.to_id])
            color = CORAL if edge.status == EdgeStatus.BLOCKED else PURPLE if edge.is_shortcut else (91, 116, 142)
            arcade.draw_line(*a, *b, color, 6 if edge.is_shortcut else 4)
        for vertex in vertices:
            start = graph.vertices.get(track.start_id)
            finish = graph.vertices.get(track.finish_id)
            if (
                vertex.id == track.finish_id
                and vertex.id != track.start_id
                and start is not None
                and finish is not None
                and (start.x, start.y) == (finish.x, finish.y)
            ):
                continue
            x, y = point(vertex)
            if vertex.type == VertexType.START:
                color, label = EMERALD, "S"
            elif vertex.type == VertexType.FINISH:
                color, label = CORAL, "F"
            elif vertex.checkpoint_order:
                color, label = AMBER, str(vertex.checkpoint_order)
            elif vertex.type == VertexType.FUEL_STATION:
                color, label = CYAN, "F"
            elif vertex.type == VertexType.NITRO_PICKUP:
                color, label = PURPLE, "N"
            else:
                color, label = (138, 158, 181), str(vertex.id)
            arcade.draw_circle_filled(x, y, 8 if vertex.checkpoint_order else 6, color)
            if vertex.id == track.start_id and finish is not None and (vertex.x, vertex.y) == (finish.x, finish.y):
                arcade.draw_circle_outline(x, y, 8 if vertex.checkpoint_order else 6, CORAL, 2)
                label = "S/F"
            _text(label, x, y - 4, 8, NAVY, anchor_x="center", bold=True)


class QuickRaceSetupView(_TrackPreviewMixin, ArcadeView):
    """Standalone Quick Race setup; every control changes the next real engine run."""

    def __init__(self, window, session):
        self.track_index = next(
            (index for index, track in enumerate(session.tracks) if track.id == session.selected_track_id), 0
        )
        saved = dict(session.quick_race_config or {}) if session.mode == "quick" else {}
        self.laps = int(saved.get("laps", 2)) if int(saved.get("laps", 2)) in (1, 2, 3, 5) else 2
        self.ai_difficulty = str(saved.get("ai_difficulty", "Normal"))
        self.events_enabled = bool(saved.get("events_enabled", True))
        self.routing = str(saved.get("routing", "Balanced"))
        self.help_open = False
        self.status = "Configure a standalone race. Quick Race never changes championship points."
        super().__init__(window, session)

    @property
    def track(self):
        return self.session.tracks[self.track_index]

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, height = self.window.width, self.window.height
        nav_y = height - 56
        self.add_button("BACK", 18, nav_y, 92, 38, self.go_menu, NAVY, WHITE, CYAN)
        self.add_button("HOW TO PLAY", 118, nav_y, 132, 38, self.toggle_help, NAVY, WHITE, CYAN)
        self.add_button("< CIRCUIT", 28, 88, 126, 38, lambda: self.change_track(-1), NAVY, WHITE, CYAN)
        self.add_button("CIRCUIT >", 164, 88, 126, 38, lambda: self.change_track(1), NAVY, WHITE, CYAN)
        self.add_button("PLAN ROUTE", width - 286, 88, 258, 44, self.start_race, EMERALD, NAVY, EMERALD)
        panel_left = max(520, width * 0.48)
        panel_width = width - panel_left - 26
        option_y = 315 if height <= 760 else max(330, int(height * 0.38))
        self.add_button(f"LAPS  {self.laps}", panel_left + 18, option_y, panel_width - 36, 38, self.cycle_laps, NAVY, WHITE, CYAN)
        self.add_button(f"AI  {self.ai_difficulty.upper()}", panel_left + 18, option_y - 50, panel_width - 36, 38, self.cycle_ai, NAVY, WHITE, CYAN)
        self.add_button(f"ROAD EVENTS  {'ON' if self.events_enabled else 'OFF'}", panel_left + 18, option_y - 100, panel_width - 36, 38, self.toggle_events, AMBER if self.events_enabled else NAVY, NAVY if self.events_enabled else WHITE, AMBER)
        self.add_button(f"ROUTING  {self.routing.upper()}", panel_left + 18, option_y - 150, panel_width - 36, 38, self.cycle_routing, NAVY, WHITE, PURPLE)

    def change_track(self, direction: int) -> None:
        self.track_index = (self.track_index + direction) % len(self.session.tracks)
        self.session.selected_track_id = self.track.id
        self.session.save_state()
        self.rebuild_ui()

    def cycle_laps(self) -> None:
        self.laps = (1, 2, 3, 5)[((1, 2, 3, 5).index(self.laps) + 1) % 4]
        self.rebuild_ui()

    def cycle_ai(self) -> None:
        choices = ("Easy", "Normal", "Hard")
        self.ai_difficulty = choices[(choices.index(self.ai_difficulty) + 1) % len(choices)]
        self.rebuild_ui()

    def toggle_events(self) -> None:
        self.events_enabled = not self.events_enabled
        self.rebuild_ui()

    def cycle_routing(self) -> None:
        choices = ("Balanced", "Speed", "Economy", "Safety")
        self.routing = choices[(choices.index(self.routing) + 1) % len(choices)]
        self.rebuild_ui()

    def toggle_help(self) -> None:
        self.help_open = not self.help_open
        self.rebuild_ui()

    def start_race(self) -> None:
        self.session.configure_quick_race(
            self.track.id,
            laps=self.laps,
            ai_difficulty=self.ai_difficulty,
            events_enabled=self.events_enabled,
            routing=self.routing,
        )
        self.session.explorer_return = "quick_setup"
        self.session.save_state()
        from smart_racing.arcade_ui.app import TrackExplorerView

        self.app.show_view(TrackExplorerView(self.app, self.session))

    def draw_content(self) -> None:
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        arcade.draw_line(0, height - 74, width, height - 74, EMERALD, 2)
        _text("QUICK RACE", 280, height - 31, 25, WHITE, bold=True)
        _text("STANDALONE SETUP  ·  REAL RACE ENGINE  ·  NO CHAMPIONSHIP POINTS", 280, height - 56, 11, EMERALD)
        map_left, map_bottom, map_width, map_height = 26, 150, max(460, width * 0.43), height - 290
        self.draw_track_preview(self.track, map_left, map_bottom, map_width, map_height)
        _text(self.track.name, map_left + 20, map_bottom + map_height - 30, 20, WHITE, bold=True)
        for line_index, line in enumerate(textwrap.wrap(self.track.description, width=66)[:2]):
            _text(line, map_left + 20, map_bottom + 38 - line_index * 16, 10, MUTED)
        panel_left = max(520, width * 0.48)
        panel_width = width - panel_left - 26
        panel_bottom = 150
        panel_height = height - 290
        self.draw_panel(panel_left, panel_bottom, panel_width, panel_height, 248)
        _text("RACE CONFIGURATION", panel_left + 18, panel_bottom + panel_height - 34, 18, WHITE, bold=True)
        _text(f"{self.track.name}  ·  {len(self.track.vertices)} vertices  ·  {len(self.track.edges)} roads", panel_left + 18, panel_bottom + panel_height - 60, 11, MUTED)
        values = (
            ("MANDATORY CHECKPOINTS", "10 in order"),
            ("SHORTCUTS", str(sum(edge.is_shortcut for edge in self.track.edges))),
            ("RESOURCES", "Fuel stations + nitro pickups"),
            ("RACE MODEL", "Fixed-step deterministic simulation"),
        )
        for index, (label, value) in enumerate(values):
            y = panel_bottom + panel_height - 104 - index * 28
            _text(label, panel_left + 18, y, 10, MUTED, bold=True)
            _text(value, panel_left + 225, y, 11, CYAN)
        if self.help_open:
            arcade.draw_lbwh_rectangle_filled(panel_left + 12, panel_bottom + 12, panel_width - 24, 116, (7, 18, 31, 245))
            _text("HOW TO PLAY", panel_left + 24, panel_bottom + 102, 13, AMBER, bold=True)
            _text("Use W/Up to accelerate, A/D to select a junction, Enter to confirm.", panel_left + 24, panel_bottom + 78, 11, WHITE, width=panel_width - 48)
            _text("Space activates nitro, Shift activates sprint, R requests a station refuel.", panel_left + 24, panel_bottom + 52, 11, WHITE, width=panel_width - 48)
            _text("Fuel, checkpoints, road events, AI and the final ranking come from the live engine.", panel_left + 24, panel_bottom + 26, 11, MUTED, width=panel_width - 48)
        _text(self.status, 28, 112, 11, MUTED, width=width - 56)

    def on_draw(self):
        self.clear()
        self.draw_content()
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()


class RaceResultsView(ArcadeView):
    def __init__(self, window, session, *, championship: bool = False):
        self.championship = championship
        self.final = championship and session.championship_status == "COMPLETED"
        self.status = "Final championship standings" if self.final else "Race results saved to the authoritative session"
        super().__init__(window, session)

    @property
    def results(self):
        return list(self.session.last_results or [])

    @property
    def result_track(self):
        if self.session.race_history:
            track_id = self.session.race_history[-1].get("track_id")
            for track in self.session.tracks:
                if track.id == track_id:
                    return track
        return self.session.selected_track

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width = self.window.width
        button_y = 28
        if self.championship:
            actions = [
                ("MAIN MENU", self.go_menu, NAVY, WHITE, CYAN),
                ("VIEW STANDINGS", self.open_dashboard, CYAN, NAVY, CYAN),
            ]
            if not self.final:
                actions.append(("NEXT ROUND", self.next_round, EMERALD, NAVY, EMERALD))
        else:
            actions = [
                ("MAIN MENU", self.go_menu, NAVY, WHITE, CYAN),
                ("RETRY", self.retry, EMERALD, NAVY, EMERALD),
                ("CHANGE CIRCUIT", self.change_setup, CYAN, NAVY, CYAN),
            ]
        gap = 12
        total_width = sum(150 if label == "CHANGE CIRCUIT" else 136 for label, *_ in actions) + gap * (len(actions) - 1)
        cursor = (width - total_width) / 2
        for label, callback, fill, text, border in actions:
            button_width = 150 if label == "CHANGE CIRCUIT" else 136
            self.add_button(label, cursor, button_y, button_width, 40, callback, fill, text, border)
            cursor += button_width + gap

    def go_menu(self) -> None:
        from smart_racing.arcade_ui.app import MainMenuView

        self.app.show_view(MainMenuView(self.app, self.session))

    def open_dashboard(self) -> None:
        from smart_racing.arcade_ui.dashboard_view import ChampionshipDashboardView

        self.app.show_view(ChampionshipDashboardView(self.app, self.session))

    def next_round(self) -> None:
        if self.session.championship_status == "COMPLETED":
            self.final = True
            self.rebuild_ui()
            return
        self.session.prepare_championship_race()
        from smart_racing.arcade_ui.app import TrackExplorerView

        self.app.show_view(TrackExplorerView(self.app, self.session))

    def retry(self) -> None:
        from smart_racing.arcade_ui.race_modes_view import QuickRaceSetupView

        self.app.show_view(QuickRaceSetupView(self.app, self.session))

    def change_setup(self) -> None:
        from smart_racing.arcade_ui.race_modes_view import QuickRaceSetupView

        setup = QuickRaceSetupView(self.app, self.session)
        setup.track_index = (setup.track_index + 1) % len(self.session.tracks)
        setup.session.selected_track_id = setup.track.id
        setup.session.save_state()
        self.app.show_view(setup)

    def draw_content(self) -> None:
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)
        title = "CHAMPIONSHIP FINAL" if self.final else "CHAMPIONSHIP ROUND RESULTS" if self.championship else "QUICK RACE RESULTS"
        _text(title, width / 2, height - 31, 25, WHITE, anchor_x="center", bold=True)
        _text(self.status.upper(), width / 2, height - 56, 11, EMERALD if self.final else CYAN, anchor_x="center")
        panel_width = min(1140, width - 80)
        left, bottom = (width - panel_width) / 2, 96
        self.draw_panel(left, bottom, panel_width, height - 206, 248)
        _text(self.result_track.name, left + 22, height - 146, 18, CYAN, bold=True)
        columns = (left + 24, left + 82, left + 260, left + 370, left + 510, left + 620, left + 700)
        for label, x in zip(("POS", "RACER", "TIME", "FASTEST LAP", "FUEL USED", "NITRO", "STATUS"), columns):
            _text(label, x, height - 181, 11, MUTED, bold=True)
        if not self.results:
            _text("No completed race is recorded yet. Finish a live race to populate this report.", left + 22, height - 224, 13, MUTED)
        for index, result in enumerate(self.results):
            y = height - 218 - index * 46
            name = {1: "Player", 2: "Navigator", 3: "Shortcut", 4: "Distance"}.get(result.get("racer_id"), f"Racer {result.get('racer_id')}")
            time = "DNF" if result.get("dnf") else f"{float(result.get('finish_time') or 0):.1f}s"
            lap = "—" if result.get("fastest_lap") is None else f"{float(result['fastest_lap']):.1f}s"
            status = "DNF" if result.get("dnf") else (f"+{result.get('points_awarded', 0)} pts" if self.championship else "FINISHED")
            if name == "Player":
                arcade.draw_lbwh_rectangle_filled(left + 12, y - 10, panel_width - 24, 32, (21, 71, 85, 190))
            row_color = CYAN if name == "Player" else WHITE
            values = (
                str(result.get("finish_position", index + 1)),
                name,
                time,
                lap,
                f"{float(result.get('fuel_used', 0)):.1f}",
                str(result.get("nitro_used", 0)),
                status,
            )
            for value, x in zip(values, columns):
                _text(value, x, y, 12, row_color, bold=name == "Player")
        if self.championship:
            _text("CHAMPIONSHIP STANDINGS", left + 22, bottom + 94, 13, AMBER, bold=True)
            entries = sorted(self.session.championship_entries.values(), key=lambda item: (-int(item.get("total_points", 0)), int(item.get("racer_id", 99))))
            _text("   ".join(f"{index + 1}. {entry.get('name')} {entry.get('total_points', 0)} pts" for index, entry in enumerate(entries)), left + 22, bottom + 66, 12, WHITE)
            _text(f"Round {min(self.session.championship_index, len(self.session.tracks))} of {len(self.session.tracks)}", left + 22, bottom + 38, 11, MUTED)

    def on_draw(self):
        self.clear()
        self.draw_content()
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()


class QuickRaceResultsView(RaceResultsView):
    pass


class ChampionshipResultsView(RaceResultsView):
    pass
