from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass

from smart_racing.algorithms.common import TraceCollector
from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.model.graph import EdgeStatus, VertexType
from smart_racing.model.race import ChampionshipEntry
from smart_racing.services.route_planner import CostModel, RoutePlanner
from smart_racing.services.scoring import rank_entries, record_results


class ScreenName:
    MENU = "Main Menu"
    EXPLORER = "Track Explorer / Route Planner"
    RACE = "Racing Screen"
    LAB = "Algorithm Lab / Visualization"
    DASHBOARD = "Championship Dashboard"


@dataclass(frozen=True)
class Theme:
    background: tuple[int, int, int]
    terrain: tuple[int, int, int]
    terrain_alt: tuple[int, int, int]
    panel: tuple[int, int, int]
    road: tuple[int, int, int]
    shoulder: tuple[int, int, int]
    lane: tuple[int, int, int]
    accent: tuple[int, int, int]
    danger: tuple[int, int, int]
    service: tuple[int, int, int]


THEMES = {
    "emerald": Theme((8, 25, 29), (33, 91, 64), (44, 116, 76), (18, 45, 48), (58, 67, 74), (112, 127, 124), (224, 231, 222), (52, 211, 153), (248, 113, 113), (56, 189, 248)),
    "canyon": Theme((37, 24, 25), (159, 103, 54), (184, 127, 66), (68, 43, 42), (70, 65, 64), (170, 138, 108), (245, 223, 172), (251, 191, 36), (248, 113, 113), (251, 146, 60)),
    "metro": Theme((13, 18, 38), (36, 48, 72), (46, 61, 88), (28, 36, 67), (52, 60, 76), (115, 126, 148), (222, 232, 240), (56, 189, 248), (248, 113, 113), (167, 139, 250)),
}

CAR_COLORS = {1: (56, 189, 248), 2: (248, 113, 113), 3: (52, 211, 153), 4: (167, 139, 250)}


def draw_text(surface, font, text, position, color=(235, 240, 250)):
    surface.blit(font.render(str(text), True, color), position)


def _clamp(value, low, high):
    return max(low, min(high, value))


class GameApp:
    """Pygame presentation layer around the authoritative graph/race services."""

    def __init__(self, tracks):
        self.tracks = tracks
        self.track_index = 0
        self.screen_name = ScreenName.MENU
        self.origin = "menu"
        self.engine = None
        self.entries: dict[int, ChampionshipEntry] = {}
        self.modal: str | None = None
        self.should_quit = False
        self.sound_enabled = True
        self.paused = False
        self.button_rects = []
        self.explorer_algorithm = "Dijkstra"
        self.explorer_preset = "balanced"
        self.explorer_result = None
        self.explorer_comparison = None
        self.explorer_graph = copy.deepcopy(self.track.graph())
        self.explorer_start_id = self.track.start_id
        self.explorer_destination_id = self.track.finish_id
        self.explorer_select_mode = "start"
        self.explorer_checkpoint_aware = True
        self.explorer_zoom = 1.0
        self.explorer_pan = (0.0, 0.0)
        self.explorer_panel_scroll = 0
        self.explorer_hover_vertex: int | None = None
        self.explorer_map_rect = None
        self.explorer_drag_anchor = None
        self._active_explorer_transform = False
        self._last_mouse_position = (0, 0)
        self.explorer_route_config = None
        self.explorer_invalidated = False
        self.lab_step = 0
        self.pressed_keys: set[int] = set()
        self.show_minimap = True
        self.show_route = True
        self.camera_center = (400.0, 350.0)
        self.camera_zoom = 1.0
        self._sprite_cache = {}
        self._scenery_cache = {}

    @property
    def track(self):
        return self.tracks[self.track_index]

    def run(self):
        try:
            import pygame
        except ImportError as exc:
            raise RuntimeError("Install pygame-ce from requirements.txt to run the graphical app") from exc
        pygame.init()
        screen = pygame.display.set_mode((1440, 900), pygame.RESIZABLE)
        pygame.display.set_caption("Smart Racing Championship")
        font = pygame.font.SysFont("segoeui", 18)
        small = pygame.font.SysFont("segoeui", 15)
        large = pygame.font.SysFont("segoeui", 32, bold=True)
        clock = pygame.time.Clock()
        accumulator = 0.0
        running = True
        while running and not self.should_quit:
            frame_dt = min(clock.tick(60) / 1000.0, 0.1)
            accumulator += frame_dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.explorer_drag_anchor = event.pos if self.screen_name == ScreenName.EXPLORER else None
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                    self.explorer_drag_anchor = None
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_motion(event.pos)
                elif event.type == pygame.MOUSEWHEEL:
                    self._handle_wheel(event.y)
                elif event.type == pygame.KEYDOWN:
                    self.pressed_keys.add(event.key)
                    if event.key == pygame.K_ESCAPE and self.modal:
                        self.modal = None
                    else:
                        self._handle_key(event.key, pygame)
                elif event.type == pygame.KEYUP:
                    self.pressed_keys.discard(event.key)
            while accumulator >= 1 / 60:
                if self.screen_name == ScreenName.RACE and self.engine and not self.paused:
                    self._apply_player_controls(pygame)
                    self.engine.tick()
                accumulator -= 1 / 60
            self._draw(screen, font, large, small, pygame)
            pygame.display.flip()
        pygame.quit()

    def _apply_player_controls(self, pygame):
        if not self.engine:
            return
        accelerate = pygame.K_w in self.pressed_keys or pygame.K_UP in self.pressed_keys
        brake = pygame.K_s in self.pressed_keys or pygame.K_DOWN in self.pressed_keys
        self.engine.set_player_input(1.0 if accelerate else 0.72, 1.0 if brake else 0.0)

    def _handle_key(self, key, pygame):
        if key == pygame.K_1:
            self.screen_name = ScreenName.MENU
        elif key == pygame.K_2:
            self.origin = "menu"
            self.screen_name = ScreenName.EXPLORER
        elif key == pygame.K_3:
            self._start_race()
            self.screen_name = ScreenName.RACE
        elif key == pygame.K_4:
            self.screen_name = ScreenName.LAB
        elif key == pygame.K_5:
            self.screen_name = ScreenName.DASHBOARD
        elif key == pygame.K_RETURN and self.screen_name == ScreenName.MENU:
            self.origin = "quick"
            self.screen_name = ScreenName.EXPLORER
            self._calculate_route()
        elif self.screen_name == ScreenName.RACE and self.engine:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.paused = not self.paused
            elif key == pygame.K_SPACE:
                self.engine.activate_nitro(1)
            elif key in (pygame.K_a, pygame.K_LEFT):
                self.engine.cycle_player_exit(-1)
            elif key in (pygame.K_d, pygame.K_RIGHT):
                self.engine.cycle_player_exit(1)
            elif key == pygame.K_RETURN:
                self.engine.confirm_player_exit()
            elif key == pygame.K_r:
                self.engine.request_refuel()
            elif key == pygame.K_m:
                self.show_minimap = not self.show_minimap
            elif key == pygame.K_TAB:
                self.show_route = not self.show_route
        elif self.screen_name == ScreenName.LAB:
            if key == pygame.K_RIGHT:
                self.lab_step += 1
            elif key == pygame.K_LEFT:
                self.lab_step = max(0, self.lab_step - 1)
        elif self.screen_name == ScreenName.EXPLORER:
            if key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                self._zoom_explorer(1.15)
            elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self._zoom_explorer(1 / 1.15)
            elif key == pygame.K_0:
                self._reset_explorer_view()
            elif key == pygame.K_LEFT:
                self.explorer_pan = (self.explorer_pan[0] - 30, self.explorer_pan[1])
            elif key == pygame.K_RIGHT:
                self.explorer_pan = (self.explorer_pan[0] + 30, self.explorer_pan[1])
            elif key == pygame.K_UP:
                self.explorer_pan = (self.explorer_pan[0], self.explorer_pan[1] - 30)
            elif key == pygame.K_DOWN:
                self.explorer_pan = (self.explorer_pan[0], self.explorer_pan[1] + 30)

    def _handle_click(self, position):
        for rect, callback in reversed(self.button_rects):
            if rect.collidepoint(position):
                callback()
                return
        if self.screen_name == ScreenName.EXPLORER and self.explorer_map_rect:
            vertex_id = self._nearest_explorer_vertex(position)
            if vertex_id is not None:
                if self.explorer_select_mode == "destination":
                    self.explorer_destination_id = vertex_id
                else:
                    self.explorer_start_id = vertex_id
                self.explorer_invalidated = False
                self._calculate_route()

    def _handle_motion(self, position):
        self._last_mouse_position = position
        if self.explorer_drag_anchor and self.screen_name == ScreenName.EXPLORER:
            dx = position[0] - self.explorer_drag_anchor[0]
            dy = position[1] - self.explorer_drag_anchor[1]
            self.explorer_pan = (self.explorer_pan[0] - dx / max(self._explorer_base_zoom(), 0.1), self.explorer_pan[1] - dy / max(self._explorer_base_zoom(), 0.1))
            self.explorer_drag_anchor = position
        elif self.screen_name == ScreenName.EXPLORER:
            self.explorer_hover_vertex = self._nearest_explorer_vertex(position)

    def _handle_wheel(self, direction):
        if self.screen_name == ScreenName.EXPLORER:
            if getattr(self, "explorer_side_rect", None) and self.explorer_side_rect.collidepoint(self._last_mouse_position):
                self.explorer_panel_scroll = _clamp(getattr(self, "explorer_panel_scroll", 0) - direction * 24, 0, 160)
            else:
                self._zoom_explorer(1.12 if direction > 0 else 1 / 1.12)

    def _zoom_explorer(self, factor):
        self.explorer_zoom = _clamp(self.explorer_zoom * factor, 0.70, 2.25)

    def _reset_explorer_view(self):
        self.explorer_zoom = 1.0
        self.explorer_pan = (0.0, 0.0)
        self.explorer_panel_scroll = 0

    def _register_button(self, pygame, label, rect, callback, kind="secondary"):
        self.button_rects.append((rect, callback))
        colors = {"primary": ((56, 189, 248), (8, 18, 30)), "success": ((52, 211, 153), (7, 35, 29)), "warning": ((251, 191, 36), (45, 30, 8)), "secondary": ((35, 51, 76), (235, 240, 250))}
        fill, text_color = colors[kind]
        pygame.draw.rect(self._surface, fill, rect, border_radius=10)
        pygame.draw.rect(self._surface, (125, 155, 180), rect, 1, border_radius=10)
        label_surface = self._font.render(label, True, text_color)
        self._surface.blit(label_surface, label_surface.get_rect(center=rect.center))

    def _start_race(self, route_config=None):
        from smart_racing.services.race_engine import RaceEngine
        self.engine = RaceEngine(self.track, route_config=route_config)
        self.paused = False
        self.camera_center = self._world_center()

    def _run_championship(self):
        from smart_racing.services.race_engine import RaceEngine
        self.entries = {i: ChampionshipEntry(i, name) for i, name in enumerate(("Player", "Navigator", "Shortcut", "Distance"), 1)}
        for track in self.tracks:
            record_results(self.entries, RaceEngine(track).run())

    def _cycle_algorithm(self):
        values = ["BFS", "DFS", "Dijkstra", "A*"]
        self.explorer_algorithm = values[(values.index(self.explorer_algorithm) + 1) % len(values)]

    def _cycle_preset(self):
        if self.explorer_algorithm in {"BFS", "DFS"}:
            return
        values = list(CostModel.PRESETS)
        self.explorer_preset = values[(values.index(self.explorer_preset) + 1) % len(values)]

    def _calculate_route(self):
        planner = RoutePlanner(self.track, self.explorer_preset)
        planner.graph = self.explorer_graph
        algorithm = {"A*": "astar", "Dijkstra": "dijkstra", "BFS": "bfs", "DFS": "dfs"}[self.explorer_algorithm]
        self.explorer_result = planner.plan_route(
            self.explorer_start_id,
            algorithm=algorithm,
            destination=self.explorer_destination_id,
            checkpoint_aware=self.explorer_checkpoint_aware,
        )
        if self.explorer_result:
            self.explorer_result["resources"] = planner.resource_plan(
                self.explorer_result["path"],
                starting_fuel=100.0,
                capacity=100.0,
                purchase_cap=40.0,
                stop_time=3.0,
                max_nitro=3,
            )
            self.explorer_result["start"] = self.explorer_start_id
            self.explorer_result["destination"] = self.explorer_destination_id
            self.explorer_result["complexity"] = {
                "BFS": "O(V + E) — minimum edge count only",
                "DFS": "O(V + E) — traversal/path discovery only",
                "Dijkstra": "O((V + E) log V) — exact non-negative weighted optimum",
                "A*": "O((V + E) log V) worst case — exact with admissible heuristic",
            }.get(self.explorer_algorithm, "")
            self.explorer_invalidated = not self.explorer_result["metrics"]["valid"]
        else:
            self.explorer_invalidated = True
        self.explorer_route_config = {
            "algorithm": self.explorer_algorithm,
            "preset": self.explorer_preset,
            "source": self.explorer_start_id,
            "destination": self.explorer_destination_id,
            "checkpoint_aware": self.explorer_checkpoint_aware,
            "blocked_edges": [edge.id for edge in self.explorer_graph.edges.values() if edge.status == EdgeStatus.BLOCKED],
        }

    def _compare_routes(self):
        planner = RoutePlanner(self.track, "balanced")
        planner.graph = self.explorer_graph
        self.explorer_comparison = planner.compare_presets(
            self.explorer_start_id,
            self.explorer_destination_id,
            algorithm="dijkstra",
            checkpoint_aware=self.explorer_checkpoint_aware,
        )

    def _toggle_explorer_closure(self):
        edge_ids = self.explorer_result.get("metrics", {}).get("edge_ids", []) if self.explorer_result else []
        if not edge_ids:
            return
        edge_id = edge_ids[0]
        edge = self.explorer_graph.edges[edge_id]
        edge.status = EdgeStatus.OPEN if edge.status == EdgeStatus.BLOCKED else EdgeStatus.BLOCKED
        self._calculate_route()
        self.explorer_invalidated = not bool(self.explorer_result and self.explorer_result.get("path"))

    def _draw(self, screen, font, large, small, pygame):
        self._surface = screen
        self._font = font
        self._small = small
        self.button_rects = []
        screen.fill((7, 12, 24))
        self._draw_header(screen, large, font, pygame)
        if self.screen_name == ScreenName.MENU:
            self._draw_menu(screen, font, pygame)
        elif self.screen_name == ScreenName.EXPLORER:
            self._draw_explorer(screen, font, pygame)
        elif self.screen_name == ScreenName.RACE:
            self._draw_race(screen, font, pygame)
        elif self.screen_name == ScreenName.LAB:
            self._draw_lab(screen, font, pygame)
        else:
            self._draw_dashboard(screen, font, pygame)
        if self.modal:
            self._draw_modal(screen, font, pygame)

    def _draw_header(self, screen, large, font, pygame):
        width = screen.get_width()
        pygame.draw.rect(screen, (14, 25, 45), pygame.Rect(0, 0, width, 84))
        pygame.draw.line(screen, (36, 189, 248), (0, 83), (width, 83), 2)
        draw_text(screen, large, "SMART RACING CHAMPIONSHIP", (28, 15), (56, 189, 248))
        draw_text(screen, font, self.screen_name.upper(), (30, 53), (179, 196, 216))
        if width >= 1120:
            draw_text(screen, self._small if hasattr(self, "_small") else font, "1 MENU   2 EXPLORER   3 RACE   4 LAB   5 DASHBOARD", (width - 452, 34), (179, 196, 216))

    def _draw_menu(self, screen, font, pygame):
        width, height = screen.get_size()
        draw_text(screen, font, "THE ALGORITHMIC RACING CHALLENGE", (52, 130), (148, 163, 184))
        draw_text(screen, self._small, "Plan the route. Read the graph. Win the championship.", (52, 158), (203, 213, 225))
        buttons = [("START CHAMPIONSHIP", 225, lambda: self._open_explorer("championship"), "primary"), ("QUICK RACE", 287, lambda: self._open_explorer("quick"), "success"), ("ALGORITHM LAB", 349, lambda: setattr(self, "screen_name", ScreenName.LAB), "secondary"), ("HOW TO PLAY", 411, lambda: setattr(self, "modal", "instructions"), "secondary"), ("SETTINGS", 473, lambda: setattr(self, "modal", "settings"), "secondary"), ("EXIT", 535, lambda: setattr(self, "modal", "exit"), "warning")]
        for label, y, callback, kind in buttons:
            self._register_button(pygame, label, pygame.Rect(52, y, 340, 48), callback, kind)
        left = min(470, width // 3)
        map_rect = pygame.Rect(left, 126, width - left - 44, min(610, height - 150))
        self._draw_map_panel(screen, pygame, self.track, map_rect)
        theme = THEMES[self.track.theme]
        draw_text(screen, font, "FEATURED CIRCUIT", (map_rect.left + 24, map_rect.top + 22), (203, 213, 225))
        draw_text(screen, font, self.track.name, (map_rect.left + 24, map_rect.top + 52), theme.accent)
        draw_text(screen, self._small, "3 circuits  •  10 ordered gates  •  live road events", (map_rect.left + 24, map_rect.top + 82), (203, 213, 225))
        draw_text(screen, self._small, "Press 3 for a race or Enter for the route planner", (52, 620), (148, 163, 184))

    def _open_explorer(self, origin):
        self.origin = origin
        self.screen_name = ScreenName.EXPLORER
        self._calculate_route()

    def _draw_explorer(self, screen, font, pygame):
        width, height = screen.get_size()
        compact = height < 780
        if self.explorer_result is None and not self.explorer_invalidated:
            self._calculate_route()
        side_width = min(500, max(410, int(width * 0.36)))
        map_rect = pygame.Rect(24, 108, width - side_width - 36, height - 126)
        side = pygame.Rect(width - side_width - 12, 108, side_width, height - 126)
        self.explorer_map_rect = map_rect
        self.explorer_side_rect = side
        self._draw_map_panel(screen, pygame, self.track, map_rect)
        theme = THEMES[self.track.theme]
        self._panel(screen, pygame, side, theme.panel)
        draw_text(screen, font, self.track.name, (side.left + 24, side.top + 22), theme.accent)
        self._wrap_text(screen, self._small, self.track.description, pygame.Rect(side.left + 24, side.top + 52, side.width - 48, 40), (203, 213, 225))
        self._register_button(pygame, "< CIRCUIT", pygame.Rect(side.left + 24, side.top + 96, 128, 36), lambda: self._change_track(-1))
        self._register_button(pygame, "CIRCUIT >", pygame.Rect(side.left + 162, side.top + 96, 128, 36), lambda: self._change_track(1))
        start_kind = "primary" if self.explorer_select_mode == "start" else "secondary"
        destination_kind = "primary" if self.explorer_select_mode == "destination" else "secondary"
        self._register_button(pygame, f"START NODE  {self.explorer_start_id}", pygame.Rect(side.left + 24, side.top + 144, 190, 36), lambda: setattr(self, "explorer_select_mode", "start"), start_kind)
        self._register_button(pygame, f"DESTINATION  {self.explorer_destination_id}", pygame.Rect(side.left + 224, side.top + 144, side.width - 248, 36), lambda: setattr(self, "explorer_select_mode", "destination"), destination_kind)
        self._register_button(pygame, self.explorer_algorithm, pygame.Rect(side.left + 24, side.top + 190, 174, 36), self._cycle_algorithm, "primary")
        weighted = self.explorer_algorithm not in {"BFS", "DFS"}
        self._register_button(pygame, self.explorer_preset.upper() if weighted else "N/A FOR BFS/DFS", pygame.Rect(side.left + 208, side.top + 190, side.width - 232, 36), self._cycle_preset if weighted else lambda: None, "secondary" if weighted else "disabled")
        self._register_button(pygame, "CALCULATE ROUTE", pygame.Rect(side.left + 24, side.top + 236, 178, 38), self._calculate_route, "success")
        self._register_button(pygame, "COMPARE 4 PRESETS", pygame.Rect(side.left + 214, side.top + 236, side.width - 238, 38), self._compare_routes)
        self._register_button(pygame, "CLOSE EDGE", pygame.Rect(side.left + 24, side.top + 282, 130, 34), self._toggle_explorer_closure, "warning")
        self._register_button(pygame, "−", pygame.Rect(side.left + 164, side.top + 282, 42, 34), lambda: self._zoom_explorer(1 / 1.15))
        self._register_button(pygame, "RESET VIEW", pygame.Rect(side.left + 212, side.top + 282, 112, 34), self._reset_explorer_view)
        self._register_button(pygame, "+", pygame.Rect(side.left + 332, side.top + 282, 42, 34), lambda: self._zoom_explorer(1.15))
        self._register_button(pygame, "CHECKPOINTS ON" if self.explorer_checkpoint_aware else "CHECKPOINTS OFF", pygame.Rect(side.left + 24, side.top + 326, 190, 34), self._toggle_checkpoint_mode, "success" if self.explorer_checkpoint_aware else "warning")
        bottom_y = side.bottom - 54
        self._register_button(pygame, "START RACE", pygame.Rect(side.left + 24, bottom_y, 174, 40), self._start_from_explorer, "primary")
        self._register_button(pygame, "ALGORITHM LAB", pygame.Rect(side.left + 210, bottom_y, side.width - 234, 40), lambda: setattr(self, "screen_name", ScreenName.LAB))
        previous_clip = screen.get_clip()
        content_top = side.top + 360
        screen.set_clip(pygame.Rect(side.left + 8, content_top, side.width - 16, max(40, side.bottom - 60 - content_top)))
        y = side.top + 374 - getattr(self, "explorer_panel_scroll", 0)
        draw_text(screen, font, "ROUTE EVIDENCE", (side.left + 24, y), (248, 250, 252))
        y += 28
        if self.explorer_invalidated:
            draw_text(screen, self._small, "ROUTE INVALIDATED — recalculate after closure", (side.left + 24, y), (248, 113, 113))
            y += 22
        if self.explorer_result:
            result = self.explorer_result
            metrics = result["metrics"]
            counters = result["counters"]
            resources = result.get("resources", {})
            status = "VALID / CHECKPOINT-SAFE" if metrics["valid"] else "NO LEGAL ROUTE"
            draw_text(screen, self._small, f"{self.explorer_algorithm}  •  {status}", (side.left + 24, y), (52, 211, 153) if metrics["valid"] else (248, 113, 113))
            y += 21
            if compact:
                draw_text(screen, self._small, f"O((V+E) log V)  |  expanded {counters.expanded_vertices}  heap {counters.heap_operations}", (side.left + 24, y), (148, 163, 184))
                y += 21
                weighted_label = f"Cost {result['cost']:.4f}" if weighted and result["cost"] is not None else "BFS/DFS: weighted cost not optimized"
                draw_text(screen, self._small, f"{weighted_label}  |  {result['elapsed_ms']:.2f} ms", (side.left + 24, y), (56, 189, 248) if weighted else (251, 191, 36))
                y += 21
                draw_text(screen, self._small, f"D {metrics['distance']:.0f}  T {metrics['travel_time']:.1f}s  F {metrics['fuel']:.1f}  Risk {metrics['risk']:.1f}", (side.left + 24, y), (203, 213, 225))
                y += 21
                fuel_ok = resources.get("fuel_feasible", False)
                stops = resources.get("required_refuelling_stops", [])
                draw_text(screen, self._small, f"Fuel {'FEASIBLE' if fuel_ok else 'INFEASIBLE'}  |  refuel stops {len(stops)}  |  nitro DP/Greedy {len(resources.get('nitro', {}).get('dp').selected) if resources.get('nitro', {}).get('dp') else 0}/{len(resources.get('nitro', {}).get('greedy').selected) if resources.get('nitro', {}).get('greedy') else 0}", (side.left + 24, y), (52, 211, 153) if fuel_ok else (248, 113, 113))
            else:
                draw_text(screen, self._small, f"Complexity: {result.get('complexity', '')}", (side.left + 24, y), (148, 163, 184))
                y += 21
                draw_text(screen, self._small, f"Expanded {counters.expanded_vertices}  Relaxed {counters.relaxed_edges}  Heap {counters.heap_operations}  {result['elapsed_ms']:.3f} ms", (side.left + 24, y), (203, 213, 225))
                y += 23
                if weighted:
                    draw_text(screen, self._small, f"Optimized weighted cost: {result['cost']:.4f}", (side.left + 24, y), (56, 189, 248))
                else:
                    draw_text(screen, self._small, "Weighted cost: not optimized by BFS/DFS", (side.left + 24, y), (251, 191, 36))
                y += 21
                draw_text(screen, self._small, f"Distance {metrics['distance']:.1f}  Time {metrics['travel_time']:.1f}s  Fuel {metrics['fuel']:.1f}  Risk {metrics['risk']:.1f}", (side.left + 24, y), (203, 213, 225))
                y += 22
                fuel_ok = resources.get("fuel_feasible", False)
                stops = resources.get("required_refuelling_stops", [])
                stop_label = "none" if not stops else ",".join(f"{stop['vertex_id']}+{stop['buy']:.0f}" for stop in stops[:3])
                draw_text(screen, self._small, f"Fuel feasibility: {'FEASIBLE' if fuel_ok else 'INFEASIBLE'}  Stops: {stop_label}", (side.left + 24, y), (52, 211, 153) if fuel_ok else (248, 113, 113))
                y += 21
                nitro = resources.get("nitro", {})
                dp = nitro.get("dp")
                greedy = nitro.get("greedy")
                draw_text(screen, self._small, f"Nitro DP: {len(dp.selected) if dp else 0}  Greedy: {len(greedy.selected) if greedy else 0}  (pickup budget 3)", (side.left + 24, y), (203, 213, 225))
                y += 24
                if not self.explorer_comparison:
                    draw_text(screen, self._small, "Reachable route: " + " → ".join(map(str, result["targets"][:6])) + (" …" if len(result["targets"]) > 6 else ""), (side.left + 24, y), (148, 163, 184))
                    y += 24
        if compact:
            draw_text(screen, self._small, "LEGEND  cyan route | green ends | amber gates | red", (side.left + 24, side.bottom - 84), (148, 163, 184))
        if self.explorer_comparison and not compact:
            draw_text(screen, self._small, "FOUR-PRESET CHECKPOINT-AWARE COMPARISON", (side.left + 24, y), (248, 250, 252))
            y += 21
            for preset, result in self.explorer_comparison.items():
                metrics = result["metrics"]
                draw_text(screen, self._small, f"{preset.title():8} cost {result['cost']:.3f}  dist {metrics['distance']:.0f}  time {metrics['travel_time']:.0f}s", (side.left + 24, y), (203, 213, 225))
                y += 19
        if self.explorer_comparison and not compact:
            draw_text(screen, self._small, "LEGEND  cyan route  •  green endpoints  •  amber gates  •  red closure", (side.left + 24, side.bottom - 84), (148, 163, 184))
        elif not compact:
            self._draw_explorer_legend(screen, pygame, side, y)
        screen.set_clip(previous_clip)
        if self.explorer_hover_vertex is not None:
            self._draw_hover_card(screen, pygame, map_rect, self.explorer_hover_vertex)

    def _change_track(self, delta):
        self.track_index = (self.track_index + delta) % len(self.tracks)
        self.explorer_graph = copy.deepcopy(self.track.graph())
        self.explorer_start_id = self.track.start_id
        self.explorer_destination_id = self.track.finish_id
        self.explorer_select_mode = "start"
        self._reset_explorer_view()
        self.explorer_result = None
        self._calculate_route()

    def _start_from_explorer(self):
        if not self.explorer_route_config:
            self._calculate_route()
        self._start_race(self.explorer_route_config)
        self.screen_name = ScreenName.RACE

    def _toggle_checkpoint_mode(self):
        self.explorer_checkpoint_aware = not self.explorer_checkpoint_aware
        self._calculate_route()

    def _draw_explorer_legend(self, screen, pygame, side, y):
        if y > side.bottom - 118:
            y = side.bottom - 118
        draw_text(screen, self._small, "LEGEND", (side.left + 24, y), (248, 250, 252))
        entries = [("selected route", (56, 189, 248)), ("start / destination", (52, 211, 153)), ("blocked / restricted", (248, 113, 113)), ("checkpoint / service", (251, 191, 36))]
        for index, (label, color) in enumerate(entries):
            column = index % 2
            row = index // 2
            x = side.left + 24 + column * 190
            yy = y + 22 + row * 20
            pygame.draw.circle(screen, color, (x + 6, yy + 7), 5)
            draw_text(screen, self._small, label, (x + 16, yy), (203, 213, 225))

    def _draw_hover_card(self, screen, pygame, map_rect, vertex_id):
        vertex = self.explorer_graph.vertices[vertex_id]
        width = 220
        x, y = self._world_to_screen(vertex.x, vertex.y, map_rect, camera=False)
        x = _clamp(x + 14, map_rect.left + 8, map_rect.right - width - 8)
        y = _clamp(y - 50, map_rect.top + 8, map_rect.bottom - 82)
        card = pygame.Rect(int(x), int(y), width, 74)
        pygame.draw.rect(screen, (8, 16, 28), card, border_radius=8)
        pygame.draw.rect(screen, (56, 189, 248), card, 1, border_radius=8)
        draw_text(screen, self._small, f"VERTEX {vertex.id}  {vertex.type.value}", (card.left + 10, card.top + 9), (248, 250, 252))
        detail = f"checkpoint {vertex.checkpoint_order}" if vertex.checkpoint_order else "service available" if vertex.type in (VertexType.FUEL_STATION, VertexType.NITRO_PICKUP) else "intersection / road node"
        draw_text(screen, self._small, detail, (card.left + 10, card.top + 31), (203, 213, 225))
        draw_text(screen, self._small, f"x {vertex.x:.0f}  y {vertex.y:.0f}", (card.left + 10, card.top + 52), (148, 163, 184))

    def _nearest_explorer_vertex(self, position):
        if not self.explorer_map_rect or not self.explorer_map_rect.collidepoint(position):
            return None
        self._active_explorer_transform = True
        try:
            nearest, nearest_distance = None, 18.0
            for vertex in self.explorer_graph.vertices.values():
                point = self._world_to_screen(vertex.x, vertex.y, self.explorer_map_rect, camera=False)
                distance = math.hypot(point[0] - position[0], point[1] - position[1])
                if distance < nearest_distance:
                    nearest, nearest_distance = vertex.id, distance
            return nearest
        finally:
            self._active_explorer_transform = False

    def _explorer_base_zoom(self):
        if not self.explorer_map_rect:
            return 1.0
        xmin, xmax, ymin, ymax = self._world_bounds()
        return min(self.explorer_map_rect.width / max(1.0, xmax - xmin), self.explorer_map_rect.height / max(1.0, ymax - ymin)) * 0.88

    def _draw_race(self, screen, font, pygame):
        if not self.engine:
            self._start_race()
        width, height = screen.get_size()
        side_width = min(390, max(330, int(width * 0.29)))
        world_rect = pygame.Rect(20, 102, width - side_width - 32, height - 116)
        side = pygame.Rect(width - side_width - 12, 102, side_width, height - 116)
        self._update_camera(world_rect)
        self._draw_track_world(screen, pygame, self.track, world_rect, self.engine.graph, camera=True, show_details=True)
        self._draw_cars(screen, pygame, world_rect)
        if self.show_minimap:
            self._draw_minimap(screen, pygame, world_rect)
        self._draw_race_top_hud(screen, font, pygame, world_rect)
        self._draw_race_side_panel(screen, font, pygame, side)

    def _draw_race_top_hud(self, screen, font, pygame, world_rect):
        engine = self.engine
        player = next(r for r in engine.racers if r.is_human)
        ranking = self._rank_live_racers()
        position = next(i for i, r in enumerate(ranking, 1) if r.id == player.id)
        theme = THEMES[self.track.theme]
        hud = pygame.Rect(world_rect.left + 14, world_rect.top + 14, min(world_rect.width - 28, 800), 64)
        pygame.draw.rect(screen, (8, 16, 28), hud, border_radius=12)
        pygame.draw.rect(screen, (97, 120, 145), hud, 1, border_radius=12)
        cells = [("LAP", f"{min(player.lap + 1, self.track.laps)}/{self.track.laps}"), ("POSITION", f"{position}/4"), ("NEXT GATE", f"{min(player.next_checkpoint + 1, len(self.track.checkpoint_ids))}/10"), ("TIME", f"{engine.state.elapsed:05.1f}s"), ("CIRCUIT", self.track.name.split("—")[-1].strip())]
        x = hud.left + 18
        for label, value in cells:
            draw_text(screen, self._small, label, (x, hud.top + 10), (148, 163, 184))
            draw_text(screen, font, value, (x, hud.top + 30), theme.accent if label != "POSITION" else (248, 250, 252))
            x += 124 if label != "CIRCUIT" else 150

    def _draw_race_side_panel(self, screen, font, pygame, rect):
        engine = self.engine
        theme = THEMES[self.track.theme]
        compact = rect.height < 640
        self._panel(screen, pygame, rect, theme.panel)
        self._register_button(pygame, "RESUME" if self.paused else "PAUSE", pygame.Rect(rect.left + 18, rect.top + 18, 112, 38), lambda: setattr(self, "paused", not self.paused), "warning")
        self._register_button(pygame, "MENU", pygame.Rect(rect.right - 124, rect.top + 18, 106, 38), lambda: setattr(self, "screen_name", ScreenName.MENU))
        player = next(r for r in engine.racers if r.is_human)
        y = rect.top + 80
        self._draw_meter(screen, pygame, rect.left + 20, y, rect.width - 40, "FUEL", player.fuel / engine.config.max_fuel, theme.service, f"{player.fuel:04.1f} / {engine.config.max_fuel:.0f}")
        y += 60
        nitro_ratio = player.nitro_remaining / engine.config.nitro_duration if player.active_nitro else 0.0
        self._draw_meter(screen, pygame, rect.left + 20, y, rect.width - 40, "NITRO BOOST" if player.active_nitro else "NITRO CHARGES", nitro_ratio if player.active_nitro else player.nitro_charges / engine.config.max_nitro, (167, 139, 250), f"{player.nitro_charges}  {'ACTIVE ' + str(round(player.nitro_remaining, 1)) + 's' if player.active_nitro else 'charges'}")
        y += 70
        self._draw_speedometer(screen, pygame, rect.left + rect.width // 2, y + 60, player)
        y += 118 if compact else 140
        draw_text(screen, font, "STANDINGS", (rect.left + 20, y), (248, 250, 252))
        y += 28
        for index, racer in enumerate(self._rank_live_racers(), 1):
            color = CAR_COLORS[racer.id]
            pygame.draw.circle(screen, color, (rect.left + 28, y + 9), 6)
            state = "FIN" if racer.finished else "DNF" if racer.dnf else f"G{min(racer.next_checkpoint + 1, 10)}"
            draw_text(screen, self._small, f"{index}  {racer.name}", (rect.left + 42, y), color)
            draw_text(screen, self._small, f"L{min(racer.lap + 1, self.track.laps)}/{self.track.laps}  {state}", (rect.right - 124, y), (203, 213, 225))
            y += 20 if compact else 24
        y += 8
        draw_text(screen, font, "DRIVING", (rect.left + 20, y), (248, 250, 252))
        y += 28
        draw_text(screen, self._small, f"PLAN  {engine.route_config['algorithm']} / {engine.route_config['preset'].title()}", (rect.left + 20, y), theme.accent)
        y += 22
        options = engine.available_player_exits()
        selected = player.selected_exit if player.selected_exit in options else (options[0] if options else None)
        selection_state = "CONFIRMED" if player.exit_confirmed else "SELECTED"
        draw_text(screen, self._small, f"Next road: {selected:02}  {selection_state if player.selected_exit else 'AUTO'}" if selected is not None else "Next road: automatic route", (rect.left + 20, y), theme.accent if selected is not None else (203, 213, 225))
        y += 22
        for hint in ("W / ↑ accelerate    S / ↓ brake", "A / D choose road   Enter confirm", "Space nitro   R refuel   M minimap"):
            draw_text(screen, self._small, hint, (rect.left + 20, y), (148, 163, 184))
            y += 20
        if not compact:
            y += 12
            draw_text(screen, font, "EVENT FEED", (rect.left + 20, y), (248, 250, 252))
            y += 26
            for event in engine.state.event_log[-4:]:
                draw_text(screen, self._small, event.replace("target=", "edge ")[:38], (rect.left + 20, y), (203, 213, 225))
                y += 20
        elif engine.state.event_log:
            draw_text(screen, self._small, "LATEST  " + engine.state.event_log[-1].replace("target=", "edge ")[:34], (rect.left + 20, rect.bottom - 20), (203, 213, 225))
        if engine.state.finished:
            draw_text(screen, font, "RACE COMPLETE", (rect.left + 20, rect.bottom - 46), theme.accent)

    def _draw_lab(self, screen, font, pygame):
        width, height = screen.get_size()
        side_width = min(470, max(390, int(width * 0.34)))
        map_rect = pygame.Rect(24, 108, width - side_width - 36, height - 126)
        side = pygame.Rect(width - side_width - 12, 108, side_width, height - 126)
        self._draw_map_panel(screen, pygame, self.track, map_rect)
        planner = RoutePlanner(self.track, self.explorer_preset)
        trace = TraceCollector()
        result = dijkstra(planner.graph, self.track.start_id, self.track.finish_id, edge_cost=planner.cost_model.cost, trace=trace)
        self._panel(screen, pygame, side, THEMES[self.track.theme].panel)
        draw_text(screen, font, "SHARED ALGORITHM LAB", (side.left + 24, side.top + 22), (56, 189, 248))
        draw_text(screen, self._small, "The lab executes the same graph services used by routing.", (side.left + 24, side.top + 54), (203, 213, 225))
        self._register_button(pygame, "< BACK", pygame.Rect(side.left + 24, side.top + 94, 130, 40), lambda: setattr(self, "screen_name", ScreenName.EXPLORER))
        self._register_button(pygame, "NEXT STEP", pygame.Rect(side.left + 168, side.top + 94, 140, 40), lambda: setattr(self, "lab_step", self.lab_step + 1), "primary")
        y = side.top + 166
        for label in ("Algorithm: Dijkstra", f"Path: {result.path}", f"Cost: {result.cost}", f"Expanded vertices: {result.counters.expanded_vertices}", f"Relaxed edges: {result.counters.relaxed_edges}", f"Heap operations: {result.counters.heap_operations}", f"Trace step: {min(self.lab_step, len(trace.steps))}/{len(trace.steps)}"):
            draw_text(screen, self._small, label, (side.left + 24, y), (203, 213, 225))
            y += 28
        draw_text(screen, font, "PSEUDOCODE", (side.left + 24, y + 12), (248, 250, 252))
        for line in ("push(source)", "extract minimum", "relax outgoing edges", "repeat until target"):
            y += 32
            draw_text(screen, self._small, line, (side.left + 42, y), (148, 163, 184))
        if trace.steps:
            step = trace.steps[min(self.lab_step, len(trace.steps) - 1)]
            draw_text(screen, self._small, f"CURRENT  {step.operation}  {step.state}", (side.left + 24, side.bottom - 48), (56, 189, 248))

    def _draw_dashboard(self, screen, font, pygame):
        width, height = screen.get_size()
        rect = pygame.Rect(24, 108, width - 48, height - 126)
        self._panel(screen, pygame, rect, (18, 29, 52))
        draw_text(screen, font, "CHAMPIONSHIP STANDINGS", (rect.left + 28, rect.top + 26), (56, 189, 248))
        self._register_button(pygame, "RUN FULL SEASON", pygame.Rect(rect.left + 28, rect.top + 70, 210, 42), self._run_championship, "primary")
        self._register_button(pygame, "ALGORITHM LAB", pygame.Rect(rect.left + 252, rect.top + 70, 170, 42), lambda: setattr(self, "screen_name", ScreenName.LAB))
        self._register_button(pygame, "MENU", pygame.Rect(rect.left + 436, rect.top + 70, 120, 42), lambda: setattr(self, "screen_name", ScreenName.MENU))
        if not self.entries:
            draw_text(screen, font, "Run Full Season to calculate official standings.", (rect.left + 28, rect.top + 170), (203, 213, 225))
            return
        ranking = rank_entries(list(self.entries.values()))
        headers = [(rect.left + 36, "POS"), (rect.left + 118, "RACER"), (rect.left + 390, "POINTS"), (rect.left + 500, "WINS"), (rect.left + 610, "SUM POS"), (rect.left + 740, "BEST LAP")]
        for x, label in headers:
            draw_text(screen, self._small, label, (x, rect.top + 164), (148, 163, 184))
        y = rect.top + 208
        for position, entry in enumerate(ranking, 1):
            row = pygame.Rect(rect.left + 20, y - 8, min(rect.width - 40, 850), 38)
            pygame.draw.rect(screen, (24, 42, 67) if position == 1 else (22, 35, 57), row, border_radius=8)
            color = CAR_COLORS.get(entry.racer_id, (248, 250, 252))
            draw_text(screen, font, str(position), (rect.left + 36, y), color)
            draw_text(screen, font, entry.name, (rect.left + 118, y), (248, 250, 252))
            draw_text(screen, font, entry.total_points, (rect.left + 390, y), (52, 211, 153))
            draw_text(screen, font, entry.wins, (rect.left + 500, y), (248, 250, 252))
            draw_text(screen, font, entry.sum_of_finish_positions, (rect.left + 610, y), (248, 250, 252))
            draw_text(screen, font, f"{entry.best_fastest_lap:.2f}" if entry.best_fastest_lap is not None else "-", (rect.left + 740, y), (248, 250, 252))
            y += 50
        draw_text(screen, self._small, "Shared comparator: points → wins → finish-position sum → fastest lap", (rect.left + 28, rect.bottom - 42), (148, 163, 184))

    def _panel(self, screen, pygame, rect, color):
        pygame.draw.rect(screen, color, rect, border_radius=14)
        pygame.draw.rect(screen, (77, 103, 134), rect, 1, border_radius=14)

    def _draw_meter(self, screen, pygame, x, y, width, label, ratio, color, value):
        draw_text(screen, self._small, label, (x, y), (148, 163, 184))
        draw_text(screen, self._small, value, (x + width - self._small.size(value)[0], y), (235, 240, 250))
        track = pygame.Rect(x, y + 23, width, 12)
        pygame.draw.rect(screen, (9, 16, 29), track, border_radius=6)
        pygame.draw.rect(screen, color, pygame.Rect(x, y + 23, int(width * _clamp(ratio, 0.0, 1.0)), 12), border_radius=6)

    def _draw_speedometer(self, screen, pygame, cx, cy, racer):
        speed = self._racer_speed(racer)
        radius = 54
        pygame.draw.circle(screen, (8, 16, 29), (cx, cy), radius)
        pygame.draw.circle(screen, (92, 117, 145), (cx, cy), radius, 2)
        pygame.draw.arc(screen, (56, 189, 248), (cx - radius + 8, cy - radius + 8, (radius - 8) * 2, (radius - 8) * 2), math.radians(210), math.radians(510), 5)
        angle = math.radians(210 + 300 * _clamp(speed / 8.0, 0.0, 1.0))
        end = (cx + int(math.cos(angle) * 39), cy - int(math.sin(angle) * 39))
        pygame.draw.line(screen, (248, 113, 113), (cx, cy), end, 3)
        pygame.draw.circle(screen, (248, 250, 252), (cx, cy), 5)
        label = self._small.render(f"{speed:.1f}", True, (248, 250, 252))
        screen.blit(label, label.get_rect(center=(cx, cy + 24)))
        draw_text(screen, self._small, "SPEED", (cx - 24, cy - 75), (148, 163, 184))

    def _draw_map_panel(self, screen, pygame, track, rect, graph=None):
        self._draw_track_world(screen, pygame, track, rect, graph or track.graph(), camera=False, show_details=True)

    def _draw_track_world(self, screen, pygame, track, rect, graph, camera=False, show_details=True):
        theme = THEMES[track.theme]
        self._active_explorer_transform = bool(self.screen_name == ScreenName.EXPLORER and self.explorer_map_rect == rect)
        pygame.draw.rect(screen, theme.terrain, rect, border_radius=14)
        self._draw_scenery(screen, pygame, track, rect, camera)
        self._draw_roads(screen, pygame, track, rect, graph, camera)
        if self._active_explorer_transform and self.explorer_result and self.explorer_result.get("path"):
            self._draw_route_overlay(screen, pygame, rect, graph, self.explorer_result["path"])
        self._draw_services_and_checkpoints(screen, pygame, track, rect, graph, camera, show_details)
        if self._active_explorer_transform:
            self._draw_plan_markers(screen, pygame, rect, graph)
        pygame.draw.rect(screen, (94, 120, 144), rect, 1, border_radius=14)
        self._active_explorer_transform = False

    def _draw_route_overlay(self, screen, pygame, rect, graph, path):
        for source_id, target_id in zip(path, path[1:]):
            source, target = graph.vertices[source_id], graph.vertices[target_id]
            a = self._world_to_screen(source.x, source.y, rect, camera=False)
            b = self._world_to_screen(target.x, target.y, rect, camera=False)
            pygame.draw.line(screen, (5, 35, 52), a, b, 12)
            pygame.draw.line(screen, (56, 189, 248), a, b, 7)
            self._draw_arrow(screen, pygame, a, b, (235, 248, 255))

    def _draw_plan_markers(self, screen, pygame, rect, graph):
        for vertex_id, label, color in ((self.explorer_start_id, "PLAN START", (52, 211, 153)), (self.explorer_destination_id, "PLAN DEST", (248, 250, 252))):
            vertex = graph.vertices.get(vertex_id)
            if vertex is None:
                continue
            point = self._world_to_screen(vertex.x, vertex.y, rect, camera=False)
            pygame.draw.circle(screen, color, point, 18, 3)
            pygame.draw.circle(screen, (7, 12, 24), point, 5)
            draw_text(screen, self._small, label, (point[0] - 30, point[1] - 34), color)

    def _draw_scenery(self, screen, pygame, track, rect, camera):
        theme = THEMES[track.theme]
        if track.id not in self._scenery_cache:
            rng = random.Random(track.seed * 1009)
            self._scenery_cache[track.id] = [(rng.uniform(50, 750), rng.uniform(65, 655), rng.randint(0, 2)) for _ in range(52)]
        for x, y, _ in self._scenery_cache[track.id]:
            px, py = self._world_to_screen(x, y, rect, camera)
            if not rect.collidepoint(px, py):
                continue
            if track.theme == "emerald":
                pygame.draw.circle(screen, (18, 62, 42), (px, py + 5), 12)
                pygame.draw.circle(screen, (24, 107, 63), (px - 4, py - 3), 10)
                pygame.draw.circle(screen, (36, 139, 79), (px + 4, py - 5), 8)
            elif track.theme == "canyon":
                pygame.draw.polygon(screen, (116, 71, 48), [(px - 12, py + 8), (px - 6, py - 9), (px + 8, py - 13), (px + 14, py + 9)])
                pygame.draw.line(screen, (210, 143, 75), (px - 6, py - 5), (px + 8, py - 8), 2)
            else:
                block = pygame.Rect(px - 12, py - 9, 24, 18)
                pygame.draw.rect(screen, (21, 31, 55), block)
                pygame.draw.rect(screen, (76, 95, 129), block, 1)
                pygame.draw.line(screen, (64, 89, 130), (px - 8, py - 3), (px + 8, py - 3), 2)
                pygame.draw.line(screen, (64, 89, 130), (px - 8, py + 3), (px + 8, py + 3), 2)
        if track.theme == "metro":
            for x in range(80, 760, 85):
                px, py = self._world_to_screen(x, 68, rect, camera)
                if rect.collidepoint(px, py):
                    pygame.draw.line(screen, (91, 106, 135), (px, py), (px, py + 12), 2)
                    pygame.draw.circle(screen, (248, 250, 252), (px, py), 2)
        pygame.draw.rect(screen, theme.terrain_alt, rect, 2, border_radius=14)

    def _draw_roads(self, screen, pygame, track, rect, graph, camera):
        theme = THEMES[track.theme]
        compact = rect.width < 300
        for edge in graph.edges.values():
            source, target = graph.vertices[edge.from_id], graph.vertices[edge.to_id]
            a, b = self._world_to_screen(source.x, source.y, rect, camera), self._world_to_screen(target.x, target.y, rect, camera)
            status = edge.status
            shoulder = (248, 113, 113) if status == EdgeStatus.BLOCKED else theme.shoulder
            road = (72, 49, 51) if status == EdgeStatus.BLOCKED else theme.road
            width = 7 if compact else (28 if edge.is_shortcut else 24)
            pygame.draw.line(screen, shoulder, a, b, width + (3 if compact else 9))
            pygame.draw.line(screen, road, a, b, width)
            pygame.draw.circle(screen, road, a, max(2, width // 2))
            pygame.draw.circle(screen, road, b, max(2, width // 2))
            if edge.is_shortcut and status != EdgeStatus.BLOCKED and not compact:
                pygame.draw.line(screen, (196, 181, 253), a, b, 3)
            if not compact:
                self._draw_lane_marks(screen, pygame, a, b, theme.lane if status != EdgeStatus.BLOCKED else (150, 55, 65))
            if edge.directed and status != EdgeStatus.BLOCKED and not compact:
                self._draw_arrow(screen, pygame, a, b, theme.accent)
            if edge.effects and not compact:
                midpoint = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
                if any("time_multiplier" in values for values in edge.effects.values()):
                    pygame.draw.ellipse(screen, (22, 22, 28), (midpoint[0] - 20, midpoint[1] - 8, 40, 16))
                    draw_text(screen, self._small, "OIL", (midpoint[0] - 12, midpoint[1] - 8), (248, 250, 252))
                if any("speed_cap" in values for values in edge.effects.values()):
                    pygame.draw.circle(screen, (251, 191, 36), midpoint, 13, 3)
                    draw_text(screen, self._small, "!", (midpoint[0] - 3, midpoint[1] - 8), (251, 191, 36))
            if status == EdgeStatus.BLOCKED and not compact:
                self._draw_barrier(screen, pygame, a, b)

    def _draw_lane_marks(self, screen, pygame, a, b, color):
        dx, dy = b[0] - a[0], b[1] - a[1]
        distance = math.hypot(dx, dy)
        if distance < 20:
            return
        ux, uy = dx / distance, dy / distance
        for start in range(10, int(distance) - 8, 28):
            p1 = (int(a[0] + ux * start), int(a[1] + uy * start))
            p2 = (int(a[0] + ux * min(start + 13, distance - 6)), int(a[1] + uy * min(start + 13, distance - 6)))
            pygame.draw.line(screen, color, p1, p2, 2)

    def _draw_arrow(self, screen, pygame, a, b, color):
        mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        points = [(mx + int(math.cos(angle) * 9), my + int(math.sin(angle) * 9)), (mx + int(math.cos(angle + 2.5) * 7), my + int(math.sin(angle + 2.5) * 7)), (mx + int(math.cos(angle - 2.5) * 7), my + int(math.sin(angle - 2.5) * 7))]
        pygame.draw.polygon(screen, color, points)

    def _draw_barrier(self, screen, pygame, a, b):
        mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        p1, p2 = (int(mx - nx * 16), int(my - ny * 16)), (int(mx + nx * 16), int(my + ny * 16))
        pygame.draw.line(screen, (248, 113, 113), p1, p2, 6)
        pygame.draw.line(screen, (251, 191, 36), (p1[0] + 4, p1[1] + 4), (p2[0] + 4, p2[1] + 4), 3)

    def _draw_services_and_checkpoints(self, screen, pygame, track, rect, graph, camera, show_details):
        for vertex in graph.vertices.values():
            px, py = self._world_to_screen(vertex.x, vertex.y, rect, camera)
            if not rect.collidepoint(px, py):
                continue
            if vertex.checkpoint_order:
                self._draw_checkpoint_gate(screen, pygame, graph, vertex, (px, py), rect, camera)
            elif vertex.type == VertexType.FUEL_STATION:
                pygame.draw.circle(screen, (56, 189, 248), (px, py), 16)
                pygame.draw.rect(screen, (235, 248, 255), (px - 5, py - 10, 10, 20), border_radius=2)
                pygame.draw.rect(screen, (56, 189, 248), (px - 2, py - 6, 4, 12))
                if show_details:
                    draw_text(screen, self._small, "FUEL", (px - 18, py + 19), (235, 248, 255))
            elif vertex.type == VertexType.NITRO_PICKUP and vertex.active:
                pulse = 14 + int(3 * math.sin((self.engine.state.elapsed if self.engine else 0) * 5 + vertex.id))
                pygame.draw.circle(screen, (167, 139, 250), (px, py), pulse, 3)
                pygame.draw.polygon(screen, (233, 213, 255), [(px, py - 10), (px - 6, py + 3), (px, py + 1), (px - 3, py + 11), (px + 8, py - 4), (px + 1, py - 3)])
                if show_details:
                    draw_text(screen, self._small, "NITRO", (px - 20, py + 19), (233, 213, 255))
            elif vertex.type == VertexType.DEAD_END:
                pygame.draw.circle(screen, (248, 113, 113), (px, py), 10, 2)
            elif vertex.type == VertexType.START:
                pygame.draw.circle(screen, (52, 211, 153), (px, py), 12, 3)
                draw_text(screen, self._small, "START", (px - 22, py + 16), (52, 211, 153))
            elif vertex.type == VertexType.FINISH:
                pygame.draw.circle(screen, (248, 113, 113), (px, py), 12, 3)
                draw_text(screen, self._small, "FINISH", (px - 24, py + 16), (248, 113, 113))
            else:
                pygame.draw.circle(screen, (157, 173, 190), (px, py), 4)

    def _draw_checkpoint_gate(self, screen, pygame, graph, vertex, point, rect, camera):
        px, py = point
        neighbors = graph.neighbors(vertex.id, include_blocked=True)
        if neighbors:
            other = graph.vertices[neighbors[0][0]]
            dx, dy = other.x - vertex.x, other.y - vertex.y
            length = max(1.0, math.hypot(dx, dy))
            nx, ny = -dy / length, dx / length
        else:
            nx, ny = 0, 1
        size = 20 if rect.width > 600 else 14
        left, right = (int(px - nx * size), int(py - ny * size)), (int(px + nx * size), int(py + ny * size))
        color = (251, 191, 36)
        if self.engine and any(r.is_human and r.next_checkpoint == vertex.checkpoint_order - 1 for r in self.engine.racers):
            color = (248, 250, 252)
        pygame.draw.line(screen, color, left, right, 5)
        pygame.draw.line(screen, color, (left[0], left[1] - 10), (left[0], left[1] + 10), 3)
        pygame.draw.line(screen, color, (right[0], right[1] - 10), (right[0], right[1] + 10), 3)
        pygame.draw.circle(screen, (25, 31, 44), (px, py), 11)
        draw_text(screen, self._small, vertex.checkpoint_order, (px - 4, py - 8), color)

    def _draw_cars(self, screen, pygame, rect):
        for racer in self.engine.racers:
            x, y, angle = self._racer_pose(racer)
            sx, sy = self._world_to_screen(x, y, rect, camera=True)
            normal = (racer.id - 2.5) * 5
            sx += int(-math.sin(angle) * normal)
            sy += int(math.cos(angle) * normal)
            if not rect.collidepoint(sx, sy):
                continue
            if racer.active_nitro:
                pygame.draw.circle(screen, (167, 139, 250), (sx, sy), 24, 3)
                pygame.draw.circle(screen, (56, 189, 248), (sx, sy), 30, 1)
            sprite = self._car_sprite(pygame, CAR_COLORS[racer.id], angle, racer.active_nitro, racer.brake > 0.1)
            screen.blit(sprite, sprite.get_rect(center=(sx, sy)))
            draw_text(screen, self._small, racer.name, (sx - 28, sy + 22), CAR_COLORS[racer.id])
            if racer.waiting > 0:
                draw_text(screen, self._small, "SERVICE", (sx - 26, sy - 32), (251, 191, 36))

    def _car_sprite(self, pygame, color, angle, nitro, braking):
        key = (color, round(angle / math.radians(5)), nitro, braking)
        if key in self._sprite_cache:
            return self._sprite_cache[key]
        base = pygame.Surface((58, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(base, (4, 10, 18, 130), (5, 10, 48, 24))
        body = [(9, 20), (16, 8), (39, 6), (51, 15), (54, 20), (51, 25), (39, 34), (16, 32)]
        pygame.draw.polygon(base, color, body)
        pygame.draw.line(base, (235, 248, 255), (17, 10), (40, 8), 2)
        pygame.draw.polygon(base, (25, 42, 63), [(21, 11), (37, 10), (45, 17), (17, 17)])
        pygame.draw.polygon(base, (25, 42, 63), [(17, 23), (45, 23), (37, 30), (21, 29)])
        for wx, wy in ((14, 3), (40, 3), (14, 29), (40, 29)):
            pygame.draw.rect(base, (15, 20, 30), (wx, wy, 8, 6), border_radius=2)
        pygame.draw.circle(base, (248, 250, 252), (50, 20), 3)
        if braking:
            pygame.draw.circle(base, (248, 60, 70), (10, 15), 3)
            pygame.draw.circle(base, (248, 60, 70), (10, 25), 3)
        if nitro:
            pygame.draw.polygon(base, (167, 139, 250), [(3, 15), (-4, 20), (3, 25)])
        result = pygame.transform.rotozoom(base, -math.degrees(angle), 1.0)
        self._sprite_cache[key] = result
        return result

    def _draw_minimap(self, screen, pygame, world_rect):
        mini = pygame.Rect(world_rect.left + 16, world_rect.bottom - 146, 220, 128)
        pygame.draw.rect(screen, (7, 14, 25), mini, border_radius=10)
        pygame.draw.rect(screen, (125, 155, 180), mini, 1, border_radius=10)
        self._draw_roads(screen, pygame, self.track, mini, self.engine.graph, camera=False)
        for racer in self.engine.racers:
            x, y, _ = self._racer_pose(racer)
            px, py = self._world_to_screen(x, y, mini, camera=False)
            pygame.draw.circle(screen, CAR_COLORS[racer.id], (px, py), 4)
        draw_text(screen, self._small, "MINIMAP", (mini.left + 10, mini.top + 8), (248, 250, 252))

    def _racer_pose(self, racer):
        graph = self.engine.graph
        vertex = graph.vertices[racer.current_vertex]
        if racer.current_path and len(racer.current_path) > racer.current_edge_index + 1:
            target = graph.vertices[racer.current_path[racer.current_edge_index + 1]]
            progress = _clamp(racer.edge_progress, 0.0, 1.0)
            return (vertex.x + (target.x - vertex.x) * progress, vertex.y + (target.y - vertex.y) * progress, math.atan2(target.y - vertex.y, target.x - vertex.x))
        options = graph.neighbors(vertex.id, include_blocked=True)
        if options:
            target = graph.vertices[options[0][0]]
            return vertex.x, vertex.y, math.atan2(target.y - vertex.y, target.x - vertex.x)
        return vertex.x, vertex.y, 0.0

    def _racer_speed(self, racer):
        if not racer.current_path or len(racer.current_path) <= racer.current_edge_index + 1:
            return 0.0
        edge = self.engine.graph.edge_between(racer.current_vertex, racer.current_path[racer.current_edge_index + 1])
        if edge is None:
            return 0.0
        multiplier = self.engine.config.nitro_speed_multiplier if racer.active_nitro else 1.0
        control = 0.55 + 0.65 * racer.throttle - 0.45 * racer.brake if racer.is_human else 1.0
        return edge.distance / max(edge.effective_time(), 1e-9) * multiplier * max(0.25, control)

    def _rank_live_racers(self):
        return sorted(self.engine.racers, key=lambda racer: (not racer.finished, racer.lap * -1, racer.next_checkpoint * -1, racer.edge_progress * -1, racer.total_time, racer.id))

    def _world_bounds(self):
        xs = [vertex.x for vertex in self.track.vertices]
        ys = [vertex.y for vertex in self.track.vertices]
        return min(xs) - 40, max(xs) + 40, min(ys) - 40, max(ys) + 40

    def _world_center(self):
        xmin, xmax, ymin, ymax = self._world_bounds()
        return (xmin + xmax) / 2, (ymin + ymax) / 2

    def _update_camera(self, rect):
        player = next((racer for racer in self.engine.racers if racer.is_human), None)
        if player is None:
            return
        x, y, _ = self._racer_pose(player)
        self.camera_center = (self.camera_center[0] * 0.88 + x * 0.12, self.camera_center[1] * 0.88 + y * 0.12)
        xmin, xmax, ymin, ymax = self._world_bounds()
        self.camera_zoom = _clamp(min(rect.width / max(1.0, xmax - xmin), rect.height / max(1.0, ymax - ymin)) * 0.90, 0.62, 1.35)

    def _world_to_screen(self, x, y, rect, camera):
        xmin, xmax, ymin, ymax = self._world_bounds()
        if camera:
            cx, cy = self.camera_center
            zoom = self.camera_zoom
        elif self._active_explorer_transform:
            zoom = self._explorer_base_zoom() * self.explorer_zoom
            world_center = ((xmin + xmax) / 2, (ymin + ymax) / 2)
            cx = world_center[0] + self.explorer_pan[0]
            cy = world_center[1] + self.explorer_pan[1]
        else:
            zoom = min(rect.width / max(1.0, xmax - xmin), rect.height / max(1.0, ymax - ymin)) * 0.88
            cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        return int(rect.centerx + (x - cx) * zoom), int(rect.centery + (y - cy) * zoom)

    def _wrap_text(self, screen, font, text, rect, color):
        words, line, y = str(text).split(), "", rect.top
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] > rect.width and line:
                draw_text(screen, font, line, (rect.left, y), color)
                y += font.get_linesize()
                line = word
            else:
                line = candidate
        if line:
            draw_text(screen, font, line, (rect.left, y), color)

    def _draw_modal(self, screen, font, pygame):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        width, height = screen.get_size()
        rect = pygame.Rect(width // 2 - 320, height // 2 - 165, 640, 330)
        self._panel(screen, pygame, rect, (22, 34, 57))
        title = {"instructions": "HOW TO PLAY", "settings": "SETTINGS", "exit": "EXIT GAME"}.get(self.modal, "NOTICE")
        draw_text(screen, font, title, (rect.left + 34, rect.top + 30), (248, 250, 252))
        if self.modal == "instructions":
            lines = ["W / Up accelerates; S / Down brakes.", "A / D selects a valid outgoing road; Enter confirms it.", "Space activates nitro; R refuels when parked at a fuel station.", "P pauses; M toggles minimap; Tab toggles route overlays."]
        elif self.modal == "settings":
            lines = [f"Sound: {'ON' if self.sound_enabled else 'OFF'}", "Simulation timestep: 1/60 second", "Window supports 1440×900 and 1280×720 layouts."]
        else:
            lines = ["Close the game now?"]
        for index, line in enumerate(lines):
            draw_text(screen, self._small, line, (rect.left + 34, rect.top + 92 + index * 30), (203, 213, 225))
        self._register_button(pygame, "CLOSE", pygame.Rect(rect.left + 34, rect.bottom - 62, 170, 42), lambda: setattr(self, "modal", None))
        if self.modal == "settings":
            self._register_button(pygame, "TOGGLE SOUND", pygame.Rect(rect.left + 220, rect.bottom - 62, 180, 42), self._toggle_sound)
        elif self.modal == "exit":
            self._register_button(pygame, "EXIT", pygame.Rect(rect.left + 220, rect.bottom - 62, 170, 42), self._exit_requested, "warning")

    def _toggle_sound(self):
        self.sound_enabled = not self.sound_enabled

    def _exit_requested(self):
        self.should_quit = True
