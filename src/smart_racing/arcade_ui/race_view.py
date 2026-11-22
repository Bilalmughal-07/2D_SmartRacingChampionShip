from __future__ import annotations

import math
import textwrap
from dataclasses import replace

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
    _clamp,
    _text,
)
from smart_racing.config import DEFAULT_CONFIG
from smart_racing.model.graph import EdgeStatus, VertexType
from smart_racing.services.race_engine import RaceEngine


class ArcadeRacingView(ArcadeView):
    """Playable Arcade race presentation backed by the authoritative RaceEngine."""

    def __init__(self, window, session, race_config: dict | None = None):
        self.track = session.selected_track
        self.race_config = dict(race_config or session.quick_race_config or {})
        self.route_config = dict(session.route_plan or {})
        for key in ("race_id", "race_mode", "round_index"):
            if key in self.race_config:
                self.route_config[key] = self.race_config[key]
        self.route_blocked = not bool(
            self.route_config.get("player_path")
            and self.route_config.get("fuel_feasible")
            and (self.route_config.get("checkpoint_aware") is not None)
        )
        laps = int(self.route_config.get("race_laps", self.race_config.get("laps", self.track.laps)))
        time_limit = float(self.race_config.get("time_limit", self.track.time_limit))
        config = replace(DEFAULT_CONFIG, laps=max(1, laps), race_time_limit=max(30.0, time_limit))
        self.engine = RaceEngine(
            self.track,
            config=config,
            route_config=self.route_config,
            events_enabled=bool(self.race_config.get("events_enabled", True)),
            ai_difficulty=str(self.race_config.get("ai_difficulty", "Normal")),
        )
        self.paused = self.route_blocked
        self.camera_mode = "FOLLOW"
        self.show_minimap = True
        self.show_route = True
        self.pressed: set[int] = set()
        self.accumulator = 0.0
        self.map_rect = (18, 70, 1, 1)
        self.side_rect = (0, 0, 1, 1)
        self.camera_center = self._world_center()
        self.camera_zoom = 1.35
        self.results = None
        self.results_recorded = False
        self._last_player_deviated = self.engine.player_deviated
        self.status_message = (
            "Racing blocked: return to Track Explorer and accept a valid route plan."
            if self.route_blocked
            else "Race ready on the selected planned route. Choose speed, fuel and nitro decisions."
        )
        super().__init__(window, session)

    def rebuild_ui(self) -> None:
        self.clear_ui()
        width, height = self.window.width, self.window.height
        nav_y = height - 56
        self.add_button("EXPLORER", 18, nav_y, 116, 38, self.open_explorer, NAVY, WHITE, CYAN)
        self.add_button("PAUSE" if not self.paused else "RESUME", 144, nav_y, 112, 38, self.toggle_pause, AMBER, NAVY, AMBER)
        self.add_button("CAMERA", 264, nav_y, 112, 38, self.cycle_camera, NAVY, WHITE, CYAN)
        self.add_button("MINIMAP", 384, nav_y, 112, 38, self.toggle_minimap, NAVY, WHITE, CYAN)
        self.add_button("DASHBOARD", 504, nav_y, 132, 38, self.open_dashboard, NAVY, WHITE, CYAN)
        self.map_rect = (18, 70, max(420, int(width * 0.70) - 30), max(260, height - 138))
        left = int(width * 0.72)
        self.side_rect = (left, 70, width - left - 18, max(260, height - 138))
        side_left, bottom, side_width, _ = self.side_rect
        self.add_button("REFUEL AT STATION", side_left + 12, bottom + 110, side_width - 24, 38, self.request_refuel, CYAN, NAVY, CYAN)
        self.add_button("NITRO BOOST", side_left + 12, bottom + 64, side_width - 24, 38, self.activate_nitro, PURPLE, WHITE, PURPLE)
        self.add_button("SPRINT", side_left + 12, bottom + 18, side_width - 24, 38, self.activate_sprint, EMERALD, NAVY, EMERALD)
        if self.results:
            self.add_button("VIEW RESULTS", side_left + 12, bottom + 156, side_width - 24, 38, self.open_dashboard, EMERALD, NAVY, EMERALD)

    def open_explorer(self) -> None:
        from smart_racing.arcade_ui.app import TrackExplorerView

        self.app.show_view(TrackExplorerView(self.app, self.session))

    def open_dashboard(self) -> None:
        if self.results and self.session.mode == "quick":
            from smart_racing.arcade_ui.race_modes_view import QuickRaceResultsView

            self.app.show_view(QuickRaceResultsView(self.app, self.session))
            return
        if self.results and self.session.mode == "championship":
            from smart_racing.arcade_ui.race_modes_view import ChampionshipResultsView

            self.app.show_view(ChampionshipResultsView(self.app, self.session, championship=True))
            return
        from smart_racing.arcade_ui.dashboard_view import ChampionshipDashboardView

        self.app.show_view(ChampionshipDashboardView(self.app, self.session))

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.status_message = "Race paused; simulation and event timers are frozen." if self.paused else "Race resumed."
        self.rebuild_ui()

    def cycle_camera(self) -> None:
        self.camera_mode = {"FOLLOW": "TACTICAL", "TACTICAL": "FULL", "FULL": "FOLLOW"}[self.camera_mode]
        self.status_message = f"Camera: {self.camera_mode}. Simulation state is unchanged."

    def toggle_minimap(self) -> None:
        self.show_minimap = not self.show_minimap

    def request_refuel(self) -> None:
        self.status_message = "Refuel requested." if self.engine.request_refuel() else "Refuel is only available while stopped at an active fuel station."

    def activate_nitro(self) -> None:
        self.status_message = "Nitro armed for the next legal edge." if self.engine.activate_nitro(1) else "Nitro unavailable: no charge or boost already active."

    def activate_sprint(self) -> None:
        self.status_message = "Sprint engaged for 2 seconds; cooldown follows." if self.engine.activate_sprint(1) else "Sprint is cooling down or already active."

    def choose_exit(self, direction: int) -> None:
        selected = self.engine.cycle_player_exit(direction)
        self.status_message = f"Selected outgoing road {selected}. Press Enter to confirm." if selected is not None else "No legal outgoing road is available."

    def confirm_exit(self) -> None:
        self.status_message = "Route exit confirmed." if self.engine.confirm_player_exit() else "Select an open outgoing road before confirming."

    def restart(self) -> None:
        self.engine = RaceEngine(
            self.track,
            config=self.engine.config,
            route_config=self.route_config,
            events_enabled=self.engine.events_enabled,
            ai_difficulty=self.engine.ai_difficulty,
        )
        self.results = None
        self.results_recorded = False
        self._last_player_deviated = self.engine.player_deviated
        self.paused = False
        self.status_message = "Race restarted from the saved route configuration."
        self.rebuild_ui()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.rebuild_ui()

    def on_update(self, delta_time: float):
        if self.route_blocked or self.paused or self.results:
            return
        player = self.engine._player()
        if player:
            accelerate = arcade.key.W in self.pressed or arcade.key.UP in self.pressed
            brake = arcade.key.S in self.pressed or arcade.key.DOWN in self.pressed
            self.engine.set_player_input(1.0 if accelerate else 0.72, 1.0 if brake else 0.0)
        self.accumulator = min(self.accumulator + min(delta_time, 0.1), 0.25)
        while self.accumulator >= self.engine.config.fixed_timestep and not self.results:
            self.engine.tick()
            self.accumulator -= self.engine.config.fixed_timestep
        if self.engine.player_deviated and not self._last_player_deviated:
            self.status_message = f"Live reroute active: {self.engine.player_reroute_reason}. White roads show the recalculated suffix."
            self._last_player_deviated = True
        if self.engine.state.finished:
            self.results = self.engine.run(max_ticks=1)
            self._record_results()
            if self.session.mode == "championship":
                from smart_racing.arcade_ui.race_modes_view import ChampionshipResultsView

                self.app.show_view(ChampionshipResultsView(self.app, self.session, championship=True))
            else:
                from smart_racing.arcade_ui.race_modes_view import QuickRaceResultsView

                self.app.show_view(QuickRaceResultsView(self.app, self.session))

    def _record_results(self) -> None:
        if self.results_recorded or not self.results:
            return
        self.session.record_race_results(self.track.id, self.results)
        self.results_recorded = True

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            if self.session.mode == "quick" and not self.results:
                from smart_racing.arcade_ui.race_modes_view import QuickRaceSetupView

                self.app.show_view(QuickRaceSetupView(self.app, self.session))
            else:
                self.open_explorer()
            return
        if symbol in (arcade.key.W, arcade.key.UP, arcade.key.S, arcade.key.DOWN):
            self.pressed.add(symbol)
        elif symbol in (arcade.key.P,):
            self.toggle_pause()
        elif symbol == arcade.key.C:
            self.cycle_camera()
        elif symbol == arcade.key.M:
            self.toggle_minimap()
        elif symbol == arcade.key.SPACE:
            self.activate_nitro()
        elif symbol == arcade.key.LSHIFT or symbol == arcade.key.RSHIFT:
            self.activate_sprint()
        elif symbol == arcade.key.R:
            self.request_refuel()
        elif symbol in (arcade.key.A, arcade.key.LEFT):
            self.choose_exit(-1)
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.choose_exit(1)
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            self.confirm_exit()
        elif symbol == arcade.key.TAB:
            self.show_route = not self.show_route
        elif symbol == arcade.key.F2:
            self.restart()

    def on_key_release(self, symbol: int, modifiers: int):
        self.pressed.discard(symbol)

    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        if self.map_contains(x, y):
            self.camera_zoom = _clamp(self.camera_zoom * (1.12 if scroll_y > 0 else 1 / 1.12), 0.65, 2.6)

    def map_contains(self, x: float, y: float) -> bool:
        left, bottom, width, height = self.map_rect
        return left <= x <= left + width and bottom <= y <= bottom + height

    def _world_center(self) -> tuple[float, float]:
        vertices = list(self.engine.graph.vertices.values())
        return ((min(v.x for v in vertices) + max(v.x for v in vertices)) / 2, (min(v.y for v in vertices) + max(v.y for v in vertices)) / 2)

    def _bbox(self):
        vertices = list(self.engine.graph.vertices.values())
        return min(v.x for v in vertices), max(v.x for v in vertices), min(v.y for v in vertices), max(v.y for v in vertices)

    def _player_position(self):
        player = self.engine._player()
        return self._racer_position(player) if player else self._world_center()

    def _racer_position(self, racer):
        if racer is None:
            return self._world_center()
        if racer.current_path and racer.edge_progress > 0 and racer.current_edge_index + 1 < len(racer.current_path):
            source = self.engine.graph.vertices[racer.current_path[racer.current_edge_index]]
            target = self.engine.graph.vertices[racer.current_path[racer.current_edge_index + 1]]
            t = _clamp(racer.edge_progress, 0.0, 1.0)
            return source.x + (target.x - source.x) * t, source.y + (target.y - source.y) * t
        vertex = self.engine.graph.vertices[racer.current_vertex]
        return vertex.x, vertex.y

    def _transform(self):
        left, bottom, width, height = self.map_rect
        xmin, xmax, ymin, ymax = self._bbox()
        base = min((width - 54) / max(1.0, xmax - xmin), (height - 54) / max(1.0, ymax - ymin))
        if self.camera_mode == "FULL":
            center = self._world_center()
            zoom = 1.0
        else:
            center = self._player_position() if self.camera_mode == "FOLLOW" else self._tactical_center()
            zoom = self.camera_zoom
        return left, bottom, width, height, center, base * zoom

    def _tactical_center(self):
        player = self.engine._player()
        if player and player.selected_exit in self.engine.graph.vertices:
            vertex = self.engine.graph.vertices[player.selected_exit]
            return vertex.x, vertex.y
        return self._player_position()

    def world_to_screen(self, x: float, y: float):
        left, bottom, width, height, center, scale = self._transform()
        return left + width / 2 + (x - center[0]) * scale, bottom + height / 2 + (y - center[1]) * scale

    def draw_world(self):
        left, bottom, width, height = self.map_rect
        self.draw_panel(left, bottom, width, height, 248)
        theme = {"emerald": (22, 78, 57), "canyon": (111, 69, 39), "metro": (30, 44, 78)}.get(self.track.theme, (30, 44, 60))
        arcade.draw_lbwh_rectangle_filled(left + 1, bottom + 1, width - 2, height - 2, (*theme, 255))
        for edge in self.engine.graph.edges.values():
            source = self.engine.graph.vertices[edge.from_id]
            target = self.engine.graph.vertices[edge.to_id]
            a, b = self.world_to_screen(source.x, source.y), self.world_to_screen(target.x, target.y)
            if edge.status == EdgeStatus.BLOCKED:
                shoulder, road, marking = (110, 38, 49), (66, 29, 40), CORAL
            elif edge.status == EdgeStatus.RESTRICTED:
                shoulder, road, marking = (115, 91, 42), (86, 69, 34), AMBER
            elif edge.is_shortcut:
                shoulder, road, marking = (76, 48, 105), (48, 45, 65), PURPLE
            else:
                shoulder, road, marking = (18, 29, 43), (58, 68, 79), (190, 198, 205)
            arcade.draw_line(*a, *b, shoulder, 32)
            arcade.draw_line(*a, *b, road, 25)
            self._lane_marking(a, b, marking, dashed=edge.is_shortcut or edge.status != EdgeStatus.OPEN)
            if edge.directed:
                self._arrow(a, b, AMBER if edge.status != EdgeStatus.BLOCKED else CORAL)
            if edge.status == EdgeStatus.BLOCKED:
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                arcade.draw_line(mx - 10, my - 10, mx + 10, my + 10, CORAL, 3)
                arcade.draw_line(mx - 10, my + 10, mx + 10, my - 10, CORAL, 3)
        for vertex in self.engine.graph.vertices.values():
            x, y = self.world_to_screen(vertex.x, vertex.y)
            arcade.draw_circle_filled(x, y, 16, (47, 57, 68))
        if self.show_route:
            original = self.engine.original_player_route
            live = self.engine.player_route if self.engine.player_deviated else original
            original_edges = set(zip(original, original[1:]))
            self._draw_route_lines(original, CYAN, 8, 29)
            if self.engine.player_deviated:
                for source_id, target_id in zip(live, live[1:]):
                    if (source_id, target_id) in original_edges:
                        continue
                    self._draw_route_lines([source_id, target_id], WHITE, 7, 27)
        for vertex in self.engine.graph.vertices.values():
            self._draw_vertex(vertex)
        for racer in self.engine.racers:
            self._draw_car(racer)

    @staticmethod
    def _arrow(a, b, color):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        arcade.draw_polygon_filled([(mx + ux * 9, my + uy * 9), (mx - ux * 5 + px * 5, my - uy * 5 + py * 5), (mx - ux * 5 - px * 5, my - uy * 5 - py * 5)], color)

    def _draw_route_lines(self, path, color, width, shadow_width):
        for source_id, target_id in zip(path, path[1:]):
            source = self.engine.graph.vertices.get(source_id)
            target = self.engine.graph.vertices.get(target_id)
            if source is None or target is None:
                continue
            a, b = self.world_to_screen(source.x, source.y), self.world_to_screen(target.x, target.y)
            arcade.draw_line(*a, *b, (3, 20, 30), shadow_width)
            arcade.draw_line(*a, *b, color, width)
            self._arrow(a, b, WHITE if color == CYAN else color)

    @staticmethod
    def _lane_marking(a, b, color, *, dashed: bool = False) -> None:
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        if dashed:
            dash, gap = 12.0, 9.0
            position = 7.0
            while position < length - 5:
                end = min(position + dash, length - 3)
                arcade.draw_line(
                    a[0] + ux * position,
                    a[1] + uy * position,
                    a[0] + ux * end,
                    a[1] + uy * end,
                    color,
                    2,
                )
                position += dash + gap
        else:
            arcade.draw_line(*a, *b, color, 2)

    def _draw_vertex(self, vertex):
        finish = self.engine.graph.vertices[self.track.finish_id]
        if vertex.id == self.track.finish_id and vertex.id != self.track.start_id:
            if vertex.x == self.engine.graph.vertices[self.track.start_id].x and vertex.y == self.engine.graph.vertices[self.track.start_id].y:
                return
        x, y = self.world_to_screen(vertex.x, vertex.y)
        start_finish = (
            vertex.id == self.track.start_id
            and finish.x == vertex.x
            and finish.y == vertex.y
        )
        if vertex.type == VertexType.START:
            color, radius, label = EMERALD, 11, "S/F" if start_finish else "S"
        elif vertex.type == VertexType.FINISH:
            color, radius, label = CORAL, 11, "F"
        elif vertex.checkpoint_order:
            color, radius, label = AMBER, 8, f"CP{vertex.checkpoint_order}"
        elif vertex.type == VertexType.FUEL_STATION:
            color, radius, label = CYAN, 9, "FUEL"
        elif vertex.type == VertexType.NITRO_PICKUP:
            color, radius, label = PURPLE, 9, "NITRO"
        elif vertex.type == VertexType.DEAD_END:
            color, radius, label = CORAL, 7, "DEAD END"
        else:
            color, radius, label = (155, 168, 183), 4, str(vertex.id)
        arcade.draw_circle_filled(x, y, radius, color)
        if start_finish:
            arcade.draw_circle_outline(x, y, radius, CORAL, 3)
        if vertex.id == self.engine._player().current_vertex if self.engine._player() else False:
            arcade.draw_circle_outline(x, y, radius + 7, WHITE, 2)
        arcade.draw_text(label, x, y + radius + 3, WHITE, font_size=9 if len(label) < 5 else 7, anchor_x="center", font_name=("Aptos Display", "Arial"), bold=True)

    def _draw_car(self, racer):
        x, y = self.world_to_screen(*self._racer_position(racer))
        color = {1: CYAN, 2: CORAL, 3: EMERALD, 4: PURPLE}.get(racer.id, WHITE)
        angle = 0.0
        if racer.current_path and racer.current_edge_index + 1 < len(racer.current_path):
            a = self.engine.graph.vertices[racer.current_path[racer.current_edge_index]]
            b = self.engine.graph.vertices[racer.current_path[racer.current_edge_index + 1]]
            angle = math.atan2(b.y - a.y, b.x - a.x)
        ux, uy, px, py = math.cos(angle), math.sin(angle), -math.sin(angle), math.cos(angle)

        def local(point):
            forward, lateral = point
            return x + ux * forward + px * lateral, y + uy * forward + py * lateral

        body = [local(point) for point in ((15, 0), (10, 6), (-9, 6), (-14, 4), (-14, -4), (-9, -6), (10, -6))]
        roof = [local(point) for point in ((7, 4), (2, 4), (-5, 3), (-5, -3), (2, -4), (7, -4))]
        arcade.draw_polygon_filled(body, color)
        arcade.draw_polygon_outline(body, WHITE if racer.is_human else (20, 28, 42), 2)
        arcade.draw_polygon_filled(roof, (34, 46, 63))
        arcade.draw_polygon_outline(roof, WHITE, 1)
        for wheel in ((7, 7), (7, -7), (-8, 7), (-8, -7)):
            arcade.draw_circle_filled(*local(wheel), 2.8, (9, 12, 18))
        arcade.draw_line(*local((-11, -7)), *local((-11, 7)), (9, 12, 18), 2)
        if racer.active_nitro or racer.sprint_active:
            arcade.draw_line(x - ux * 11, y - uy * 11, x - ux * 23, y - uy * 23, AMBER if racer.sprint_active else PURPLE, 4)
        _text(racer.name[0], x, y - 4, 9, NAVY, anchor_x="center", bold=True)

    def draw_minimap(self):
        if not self.show_minimap:
            return
        x, y, width, height = 34, 92, 238, 158
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (6, 14, 25, 232))
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, CYAN, 1)
        xmin, xmax, ymin, ymax = self._bbox()
        scale = min((width - 20) / max(1, xmax - xmin), (height - 30) / max(1, ymax - ymin))
        def point(wx, wy):
            return x + width / 2 + (wx - (xmin + xmax) / 2) * scale, y + height / 2 + (wy - (ymin + ymax) / 2) * scale
        for edge in self.engine.graph.edges.values():
            a = self.engine.graph.vertices[edge.from_id]
            b = self.engine.graph.vertices[edge.to_id]
            arcade.draw_line(*point(a.x, a.y), *point(b.x, b.y), CORAL if edge.status == EdgeStatus.BLOCKED else (77, 94, 113), 2)
        original = self.engine.original_player_route
        live = self.engine.player_route if self.engine.player_deviated else original
        original_edges = set(zip(original, original[1:]))
        for source_id, target_id in zip(original, original[1:]):
            source, target = self.engine.graph.vertices.get(source_id), self.engine.graph.vertices.get(target_id)
            if source and target:
                arcade.draw_line(*point(source.x, source.y), *point(target.x, target.y), CYAN, 4)
        if self.engine.player_deviated:
            for source_id, target_id in zip(live, live[1:]):
                if (source_id, target_id) in original_edges:
                    continue
                source, target = self.engine.graph.vertices.get(source_id), self.engine.graph.vertices.get(target_id)
                if source and target:
                    arcade.draw_line(*point(source.x, source.y), *point(target.x, target.y), WHITE, 3)
        for racer in self.engine.racers:
            px, py = point(*self._racer_position(racer))
            color = {1: CYAN, 2: CORAL, 3: EMERALD, 4: PURPLE}.get(racer.id, WHITE)
            arcade.draw_circle_filled(px, py, 5 if racer.is_human else 4, color)
        route_label = "REROUTE WHITE" if self.engine.player_deviated else "PLANNED BLUE"
        _text(f"MINIMAP  {route_label}", x + 8, y + height - 17, 9, WHITE)

    def draw_side_panel(self):
        left, bottom, width, height = self.side_rect
        self.draw_panel(left, bottom, width, height, 246)
        _text("RACING SCREEN", left + 14, bottom + height - 30, 18, WHITE, bold=True)
        _text(self.track.name, left + 14, bottom + height - 54, 12, CYAN)
        _text(f"CAMERA  {self.camera_mode}", left + 14, bottom + height - 80, 11, MUTED)
        player = self.engine._player()
        if player:
            lines = [
                f"LAP {min(player.lap + 1, self.engine.config.laps)}/{self.engine.config.laps}",
                f"CHECKPOINT {min(player.next_checkpoint + 1, len(self.track.checkpoint_ids))}/10",
                f"FUEL {player.fuel:05.1f} / 100",
                f"NITRO {player.nitro_charges}  {'ACTIVE' if player.active_nitro else ''}",
                f"SPRINT {'ACTIVE' if player.sprint_active else ('READY' if player.sprint_cooldown <= 0 else f'{player.sprint_cooldown:.1f}s')}" ,
                f"TIME {self.engine.state.elapsed:05.1f}s",
            ]
            for index, line in enumerate(lines):
                color = EMERALD if index in (0, 1) else WHITE
                _text(line, left + 14, bottom + height - 122 - index * 24, 13, color, bold=index < 2)
            selected = player.selected_exit
            options = self.engine.available_player_exits()
            _text(f"EXITS {options}  SELECTED {selected if selected is not None else 'AUTO'}", left + 14, bottom + height - 280, 10, AMBER if selected is not None else MUTED)
            _text(
                "ROUTE  REROUTED / WHITE" if self.engine.player_deviated else "ROUTE  PLANNED / BLUE",
                left + 14,
                bottom + height - 300,
                10,
                WHITE if self.engine.player_deviated else CYAN,
            )
        status_color = AMBER if "unavailable" in self.status_message or "only" in self.status_message else MUTED
        for index, line in enumerate(textwrap.wrap(self.status_message, width=42)[:2]):
            _text(line, left + 14, bottom + 202 - index * 16, 10, status_color)
        _text("W/UP speed   S/DOWN brake", left + 14, bottom + 172, 10, MUTED)
        _text("A/D fork   ENTER confirm   SPACE nitro", left + 14, bottom + 153, 10, MUTED)
        _text("SHIFT sprint   R refuel   C camera   P pause", left + 14, bottom + 134, 10, MUTED)
        _text("EVENT FEED", left + 14, bottom + 318, 12, WHITE, bold=True)
        for index, event in enumerate(self.engine.state.event_log[-4:]):
            _text(event.replace("target=", "edge ")[:36], left + 14, bottom + 294 - index * 18, 10, CORAL if "block" in event else MUTED)
        if self.results:
            arcade.draw_lbwh_rectangle_filled(left + 10, bottom + 225, width - 20, 105, (5, 18, 28, 240))
            _text("RACE FINISHED", left + width / 2, bottom + 304, 18, EMERALD, anchor_x="center", bold=True)
            for index, result in enumerate(self.results[:4]):
                _text(f"P{result.finish_position}  Racer {result.racer_id}  {'DNF' if result.dnf else f'{result.finish_time:.1f}s'}", left + 20, bottom + 278 - index * 19, 10, WHITE)

    def on_draw(self):
        self.clear()
        width, height = self.window.width, self.window.height
        arcade.draw_lbwh_rectangle_filled(0, 0, width, height, NAVY)
        arcade.draw_lbwh_rectangle_filled(0, height - 74, width, 74, (14, 27, 46))
        arcade.draw_line(0, height - 74, width, height - 74, CYAN, 2)
        _text("RACING SCREEN", width - 20, height - 30, 24, WHITE, anchor_x="right", anchor_y="center", bold=True)
        _text(f"{self.track.name}  |  {self.session.mode.upper()}", width - 20, height - 57, 11, CYAN, anchor_x="right", anchor_y="center")
        self.draw_world()
        self.draw_minimap()
        self.draw_side_panel()
        self.ui.draw()
        self.draw_focus()
        self.capture_smoke()
