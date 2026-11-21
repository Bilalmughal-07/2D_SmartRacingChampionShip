from __future__ import annotations

import arcade

from smart_racing.arcade_ui.app import (
    AMBER,
    CYAN,
    EMERALD,
    MUTED,
    NAVY,
    PURPLE,
    WHITE,
    ArcadeView,
    _text,
)
from smart_racing.model.race import ChampionshipEntry
from smart_racing.services.race_engine import RaceEngine
from smart_racing.services.scoring import rank_entries, record_results, top_k_entries


class ChampionshipDashboardView(ArcadeView):
    """Review screen for real race results, sorting methods and top-k standings."""

    def __init__(self, window, session):
        self.sort_method = "merge"
        self.top_k = 3
        self.entries: list[ChampionshipEntry] = []
        self.status = "Load standings or run the deterministic championship preview."
        super().__init__(window, session)
        self.load_entries()

    def load_entries(self) -> None:
        if self.session.championship_entries:
            self.entries = [ChampionshipEntry(**value) for value in self.session.championship_entries.values()]
            self.status = f"Loaded {len(self.entries)} persistent standings entries."
        else:
            self.run_preview()

    def run_preview(self) -> None:
        entries = {
            index: ChampionshipEntry(index, name)
            for index, name in enumerate(("Player", "Navigator", "Shortcut", "Distance"), 1)
        }
        for track in self.session.tracks:
            record_results(entries, RaceEngine(track).run())
        self.entries = list(entries.values())
        self.status = "Three-circuit deterministic championship review loaded."

    def rebuild_ui(self) -> None:
        self.clear_ui()
        _, height = self.window.width, self.window.height
        nav_y = height - 56
        self.add_button("BACK", 18, nav_y, 92, 38, self.go_menu, NAVY, WHITE, CYAN)
        self.add_button("MERGE SORT", 122, nav_y, 138, 38, lambda: self.set_sort("merge"), CYAN if self.sort_method == "merge" else NAVY, NAVY if self.sort_method == "merge" else WHITE, CYAN)
        self.add_button("QUICK SORT", 270, nav_y, 132, 38, lambda: self.set_sort("quick"), CYAN if self.sort_method == "quick" else NAVY, NAVY if self.sort_method == "quick" else WHITE, CYAN)
        self.add_button("HEAP SORT", 412, nav_y, 132, 38, lambda: self.set_sort("heap"), CYAN if self.sort_method == "heap" else NAVY, NAVY if self.sort_method == "heap" else WHITE, CYAN)
        self.add_button("TOP 3", 554, nav_y, 98, 38, lambda: self.set_top_k(3), PURPLE if self.top_k == 3 else NAVY, WHITE, PURPLE)
        self.add_button("TOP 4", 662, nav_y, 98, 38, lambda: self.set_top_k(4), PURPLE if self.top_k == 4 else NAVY, WHITE, PURPLE)
        self.add_button("RUN CHAMPIONSHIP", 24, 42, 220, 38, self.run_preview, EMERALD, NAVY, EMERALD)
        self.add_button("NEXT RACE", 256, 42, 140, 38, self.next_race, CYAN, NAVY, CYAN)

    def go_menu(self) -> None:
        from smart_racing.arcade_ui.app import MainMenuView

        self.app.show_view(MainMenuView(self.app, self.session))

    def set_sort(self, method: str) -> None:
        self.sort_method = method
        self.status = f"Ranking recomputed with {method.title()} Sort using the common comparator."
        self.rebuild_ui()

    def set_top_k(self, count: int) -> None:
        self.top_k = count
        self.status = f"Top-{count} view selected using the same ranking comparator."
        self.rebuild_ui()

    def next_race(self) -> None:
        if self.session.mode != "championship" or self.session.championship_status == "COMPLETED":
            self.status = "No championship race is waiting; start or continue a championship from the main menu."
            return
        if self.session.championship_index >= len(self.session.tracks):
            self.status = "Championship complete: final champion is shown below."
            return
        self.session.selected_track_id = self.session.tracks[self.session.championship_index].id
        self.session.route_plan = None
        self.session.explorer_mode = "full_race"
        self.session.explorer_return = "dashboard"
        self.session.explorer_context = {}
        self.session.save_state()
        from smart_racing.arcade_ui.app import TrackExplorerView

        self.app.show_view(TrackExplorerView(self.app, self.session))

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.go_menu()

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)
        _text("CHAMPIONSHIP DASHBOARD", width - 20, height - 30, 24, WHITE, anchor_x="right", anchor_y="center", bold=True)
        _text("PLAN  →  RACE  →  REVIEW", width - 20, height - 57, 11, CYAN, anchor_x="right", anchor_y="center")
        self.draw_content()
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()

    def draw_content(self):
        width, height = self.window.width, self.window.height
        ranked = rank_entries(self.entries, self.sort_method)
        leaders = top_k_entries(self.entries, self.top_k)
        left, bottom = 26, 90
        self.draw_panel(left, bottom, width * 0.38, height - 210, 246)
        self.draw_panel(width * 0.41, bottom, width * 0.56, height - 210, 246)
        _text("PODIUM", left + 22, height - 148, 18, WHITE, bold=True)
        if ranked:
            podium_x = [left + 80, left + 190, left + 300]
            podium_y = [height - 390, height - 330, height - 270]
            colors = [AMBER, (180, 194, 210), (180, 122, 67)]
            for index, entry in enumerate(ranked[:3]):
                x = podium_x[index]
                y = podium_y[index]
                arcade.draw_lbwh_rectangle_filled(x - 42, bottom + 90, 84, y - bottom - 90, (*colors[index], 150))
                arcade.draw_circle_filled(x, y, 24, colors[index])
                _text(str(index + 1), x, y - 7, 18, NAVY, anchor_x="center", bold=True)
                _text(entry.name, x, y - 42, 12, WHITE, anchor_x="center", bold=True)
                _text(f"{entry.total_points} pts", x, y - 60, 10, MUTED, anchor_x="center")
        _text("RANKING METHOD", left + 22, bottom + 60, 11, MUTED)
        _text(f"{self.sort_method.title()} Sort  |  comparator: points, wins, positions, lap, racer ID", left + 22, bottom + 40, 10, CYAN)
        _text("LEADERBOARD", width * 0.41 + 22, height - 148, 18, WHITE, bold=True)
        headers = "POS   RACER             POINTS   WINS   SUM POS   BEST LAP"
        _text(headers, width * 0.41 + 22, height - 184, 10, MUTED)
        for index, entry in enumerate(ranked):
            y = height - 218 - index * 40
            highlight = entry.name == "Player"
            if highlight:
                arcade.draw_lbwh_rectangle_filled(width * 0.41 + 10, y - 8, width * 0.56 - 20, 30, (21, 71, 85, 180))
            best = f"{entry.best_fastest_lap:.1f}s" if entry.best_fastest_lap is not None else "—"
            _text(f"{index + 1:02d}    {entry.name:<16} {entry.total_points:>4}     {entry.wins:>2}       {entry.sum_of_finish_positions:>2}       {best}", width * 0.41 + 22, y, 12, CYAN if highlight else WHITE, bold=highlight)
        _text(f"TOP-{self.top_k}", width * 0.41 + 22, bottom + 90, 12, PURPLE, bold=True)
        _text("  ".join(f"{index + 1}. {entry.name}" for index, entry in enumerate(leaders)), width * 0.41 + 22, bottom + 68, 12, WHITE)
        upcoming = self.session.selected_track.name if self.session.mode == "championship" and self.session.championship_index < len(self.session.tracks) else "Championship complete"
        _text(f"NEXT  {upcoming}", width * 0.41 + 22, bottom + 36, 11, EMERALD if upcoming != "Championship complete" else AMBER)
        _text(self.status, left + 22, 10, 10, MUTED, width=width - 52)
