from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass

from smart_racing.algorithms.dijkstra import dijkstra
from smart_racing.config import DEFAULT_CONFIG, GameConfig
from smart_racing.model.events import Event, EventType
from smart_racing.model.graph import EdgeStatus, Track, VertexType
from smart_racing.model.race import Racer, RaceResult, RacerStrategy, RaceState
from smart_racing.services.event_scheduler import EventScheduler
from smart_racing.services.route_planner import RoutePlanner
from smart_racing.services.scoring import points_for_position


@dataclass
class RaceSnapshot:
    elapsed: float
    racers: list[dict]
    events: list[str]
    finished: bool


class RaceEngine:
    def __init__(
        self,
        track: Track,
        config: GameConfig = DEFAULT_CONFIG,
        racers: list[Racer] | None = None,
        route_config: dict | None = None,
        *,
        events_enabled: bool = True,
        ai_difficulty: str = "Normal",
    ):
        self.track = track
        self.config = config
        self.events_enabled = bool(events_enabled)
        self.ai_difficulty = str(ai_difficulty or "Normal").title()
        self.ai_multiplier = {"Easy": 0.88, "Normal": 1.0, "Hard": 1.10}.get(
            self.ai_difficulty, 1.0
        )
        self.route_config = {
            "algorithm": "Dijkstra",
            "preset": "balanced",
            "source": track.start_id,
            "destination": track.finish_id,
            "checkpoint_aware": True,
        }
        if route_config:
            self.route_config.update(route_config)
        self.route_algorithm = str(self.route_config.get("algorithm") or "Dijkstra").lower()
        if self.route_algorithm == "a*":
            self.route_algorithm = "astar"
        self.strategy_preset = str(
            self.route_config.get("strategy") or self.route_config.get("preset") or "balanced"
        ).lower()
        self.checkpoint_aware = bool(self.route_config.get("checkpoint_aware", True))
        self.race_start_vertex = int(self.route_config.get("source", track.start_id))
        self.race_destination = int(self.route_config.get("destination", track.finish_id))
        self.player_route = [
            int(vertex_id) for vertex_id in self.route_config.get("player_path", [])
        ]
        self.original_player_route = list(self.player_route)
        self.player_deviated = False
        self.player_reroute_reason = ""
        # Each race owns a graph snapshot; services and pickup availability must
        # not leak into the next replay or championship race.
        self.graph = copy.deepcopy(track.graph())
        for edge_id in self.route_config.get("blocked_edges", []):
            if edge_id in self.graph.edges:
                self.graph.set_edge_status(edge_id, EdgeStatus.BLOCKED)
        self.planner = RoutePlanner(track, str(self.route_config.get("preset") or "balanced"))
        # Gameplay and the planner must share the same live graph so event mutations
        # are visible to every route calculation and to the Algorithm Lab snapshot.
        self.planner.graph = self.graph
        self.scheduler = EventScheduler()
        self.state = RaceState(str(self.route_config.get("race_id") or track.id))
        self.racers = racers or [
            Racer(
                1,
                "Player",
                True,
                RacerStrategy.HUMAN,
                self.race_start_vertex,
                config.initial_fuel,
                config.initial_nitro,
            ),
            Racer(
                2,
                "Navigator",
                False,
                RacerStrategy.FIXED_ROUTE,
                self.race_start_vertex,
                config.initial_fuel,
                config.initial_nitro,
            ),
            Racer(
                3,
                "Shortcut",
                False,
                RacerStrategy.SHORTCUT,
                self.race_start_vertex,
                config.initial_fuel,
                config.initial_nitro,
            ),
            Racer(
                4,
                "Distance",
                False,
                RacerStrategy.MIN_DISTANCE,
                self.race_start_vertex,
                config.initial_fuel,
                config.initial_nitro,
            ),
        ]
        self._next_event_id = 1
        self.ai_routes: dict[int, list[int]] = {}
        for racer in self.racers:
            if not racer.is_human:
                plan = self._standard_plan(self.race_start_vertex, 0, "balanced")
                if plan and plan.get("path"):
                    self.ai_routes[racer.id] = list(plan["path"])
        if self.events_enabled:
            self._schedule_default_events()

    def _schedule_default_events(self):
        # Event targets and later trigger times vary by circuit/race ID, but
        # the seeded generator keeps replay decisions deterministic.
        seed = self.track.seed * 1009 + sum(ord(char) for char in str(self.state.race_id))
        rng = random.Random(seed)
        edge_ids = sorted(self.graph.edges)
        targets = rng.sample(edge_ids, min(4, len(edge_ids)))
        events = [
            (12.0, 1, EventType.ROAD_BLOCKAGE, targets[0], 12.0, {}),
            (25.0 + rng.randint(0, 4), 2, EventType.SHORTCUT_TOGGLE, targets[1], 20.0, {}),
            (38.0 + rng.randint(0, 5), 3, EventType.OIL_SPILL, targets[2], 20.0, {"difficulty_penalty": 2, "time_multiplier": 1.5, "obstacle_penalty": 2}),
            (55.0 + rng.randint(0, 6), 4, EventType.SPEED_RESTRICTION, targets[3], 15.0, {"speed_cap": 2.5}),
        ]
        for trigger, priority, kind, target, duration, payload in events:
            self.schedule_event(kind, trigger, priority, target, duration, payload)

    def _route_targets(self, checkpoint_index: int = 0) -> list[int]:
        if not self.checkpoint_aware:
            return [self.race_destination]
        remaining = self.track.checkpoint_ids[max(0, checkpoint_index):]
        if self.race_destination in remaining:
            return remaining[: remaining.index(self.race_destination) + 1]
        return [*remaining, self.race_destination]

    def _standard_plan(self, source: int, checkpoint_index: int, preset: str, algorithm: str = "dijkstra"):
        saved = self.planner.cost_model.preset
        self.planner.cost_model.set_preset(preset if preset in self.planner.cost_model.PRESETS else "balanced")
        try:
            if self.checkpoint_aware:
                return self.planner.plan_checkpoints(
                    source,
                    checkpoint_index,
                    algorithm=algorithm,
                    destination=self.race_destination,
                    include_resources=False,
                )
            return self.planner.plan_route(
                source,
                self.race_destination,
                algorithm=algorithm,
                checkpoint_aware=False,
            )
        finally:
            self.planner.cost_model.set_preset(saved)

    def _shortest_distance_plan(self, source: int, checkpoint_index: int):
        current = source
        path: list[int] = []
        for target in self._route_targets(checkpoint_index):
            result = dijkstra(self.graph, current, target, edge_cost=lambda edge: edge.distance)
            if not result.path:
                return None
            path.extend(result.path if not path else result.path[1:])
            current = target
        if not path:
            return None
        return {
            "path": path,
            "metrics": self.planner.path_metrics(path),
            "algorithm": "dijkstra",
            "preset": "distance",
            "checkpoint_aware": self.checkpoint_aware,
        }

    @staticmethod
    def _with_current_prefix(current: int, result: dict | None) -> dict | None:
        if not result or not result.get("path"):
            return None
        path = list(result["path"])
        if path[0] != current:
            path.insert(0, current)
        return {**result, "path": path}

    def schedule_event(
        self, event_type, trigger_time, priority, target_id=None, duration=0.0, payload=None
    ):
        event = Event(
            self._next_event_id,
            event_type,
            trigger_time,
            priority,
            self.scheduler.sequence,
            target_id,
            duration,
            payload or {},
        )
        self._next_event_id += 1
        self.scheduler.schedule(event)
        return event.event_id

    def _apply_event(self, event: Event) -> None:
        target = event.target_id
        if target is None:
            return
        label = f"t={self.state.elapsed:.1f}: {event.type.value} target={target}"
        self.state.event_log.append(label)
        if event.type == EventType.ROAD_BLOCKAGE and target in self.graph.edges:
            self.graph.set_edge_status(target, EdgeStatus.BLOCKED)
            self._schedule_expiry(event, EventType.ROAD_REOPEN)
        elif event.type == EventType.ROAD_REOPEN and target in self.graph.edges:
            self.graph.set_edge_status(target, EdgeStatus.OPEN)
        elif event.type == EventType.SHORTCUT_TOGGLE and target in self.graph.edges:
            edge = self.graph.edges[target]
            edge.status = EdgeStatus.BLOCKED if edge.status == EdgeStatus.OPEN else EdgeStatus.OPEN
            if event.duration:
                self._schedule_expiry(event, EventType.SHORTCUT_TOGGLE)
        elif (
            event.type in (EventType.OIL_SPILL, EventType.SPEED_RESTRICTION)
            and target in self.graph.edges
        ):
            effect_id = event.effect_id or f"event-{event.event_id}"
            event.effect_id = effect_id
            self.graph.add_effect(target, effect_id, event.payload or {})
            self._schedule_expiry(event, EventType.EFFECT_EXPIRE)
        elif (
            event.type == EventType.EFFECT_EXPIRE and target in self.graph.edges and event.effect_id
        ):
            self.graph.remove_effect(target, event.effect_id)

    def _schedule_expiry(self, original: Event, expiry_type: EventType):
        if original.duration <= 0:
            return
        expiry = Event(
            self._next_event_id,
            expiry_type,
            original.trigger_time + original.duration,
            original.priority,
            self.scheduler.sequence,
            original.target_id,
            0,
            original.payload,
            effect_id=original.effect_id,
        )
        self._next_event_id += 1
        self.scheduler.schedule(expiry)

    def _consume_vertex_actions(self, racer: Racer):
        vertex = self.graph.vertices[racer.current_vertex]
        if (
            vertex.type == VertexType.FUEL_STATION
            and vertex.active
            and (racer.manual_refuel or racer.fuel < self.config.max_fuel * 0.25)
        ):
            purchase = min(self.config.fuel_purchase_cap, self.config.max_fuel - racer.fuel)
            if purchase > 0:
                racer.fuel += purchase
                racer.waiting += self.config.fuel_station_stop_time
                racer.decision_log.append(f"refuel+{purchase:.1f}")
            racer.manual_refuel = False
        if (
            vertex.type == VertexType.NITRO_PICKUP
            and vertex.active
            and racer.nitro_charges < self.config.max_nitro
        ):
            racer.nitro_charges += 1
            vertex.active = False
            racer.decision_log.append("nitro_pickup")
        if (
            self.checkpoint_aware
            and
            racer.next_checkpoint < len(self.track.checkpoint_ids)
            and racer.current_vertex == self.track.checkpoint_ids[racer.next_checkpoint]
        ):
            racer.next_checkpoint += 1
            racer.decision_log.append(f"checkpoint_{racer.next_checkpoint}")
        reached_destination = racer.current_vertex == (
            self.track.finish_id if self.checkpoint_aware else self.race_destination
        )
        checkpoints_complete = not self.checkpoint_aware or racer.next_checkpoint == len(self.track.checkpoint_ids)
        if reached_destination and checkpoints_complete:
            lap_time = racer.total_time - racer.lap_started_at
            racer.fastest_lap = (
                lap_time if racer.fastest_lap is None else min(racer.fastest_lap, lap_time)
            )
            racer.lap += 1
            racer.lap_started_at = racer.total_time
            if racer.lap >= self.config.laps:
                racer.finished = True
            else:
                # The finish line is the same physical position as the start
                # line. Keep the finish vertex as the authoritative lap
                # boundary, then place every racer back on the start vertex so
                # the transferred player route can be replayed from index 0 on
                # the next lap. Leaving the racer at ``finish_id`` makes an
                # exact player path appear to have no next road and causes the
                # player to wait indefinitely while AI racers re-plan.
                racer.current_vertex = self.race_start_vertex
                racer.next_checkpoint = 0
                racer.current_path = []
                racer.current_edge_index = 0
                racer.planned_route_index = 0

    def _fuel_detour_plan(self, racer: Racer) -> dict | None:
        if racer.fuel >= self.config.max_fuel * 0.25:
            return None
        current_vertex = self.graph.vertices.get(racer.current_vertex)
        if current_vertex and current_vertex.type == VertexType.FUEL_STATION:
            return None
        stations = [
            vertex.id
            for vertex in self.graph.vertices.values()
            if vertex.type == VertexType.FUEL_STATION and vertex.active
        ]
        candidates = []
        for station_id in stations:
            result = dijkstra(self.graph, racer.current_vertex, station_id, edge_cost=lambda edge: edge.distance)
            if result.path:
                candidates.append((len(result.path), result.cost, station_id, result.path))
        if not candidates:
            return None
        if racer.strategy_type == RacerStrategy.FIXED_ROUTE:
            route = self.ai_routes.get(racer.id, [])
            ordered = {vertex_id: index for index, vertex_id in enumerate(route)}
            candidates.sort(key=lambda item: (ordered.get(item[2], 10_000), item[0], item[2]))
        else:
            candidates.sort(key=lambda item: (item[1], item[2]))
        path = candidates[0][3]
        return {"path": path, "fuel_detour": True}

    def _recalculate_player_route(self, racer: Racer, reason: str) -> dict | None:
        result = self._standard_plan(racer.current_vertex, racer.next_checkpoint, self.strategy_preset, self.route_algorithm)
        if not result or len(result.get("path", [])) < 2:
            return None
        self.player_route = list(result["path"])
        self.player_deviated = True
        self.player_reroute_reason = reason
        racer.planned_route_index = 0
        # Do not call _planned_player_plan here: that method intentionally
        # calls back into this function when it sees a blocked edge.  Returning
        # the segment directly keeps a second simultaneous closure a safe wait
        # state instead of creating recursive replanning or a false DNF.
        plan = self._route_segment(racer, self.player_route)
        return plan if plan and not plan.get("planned_blocked") else None

    def _plan_player_exit(self, racer: Racer) -> dict | None:
        selected = racer.selected_exit
        if selected is None or racer.selected_exit_vertex != racer.current_vertex:
            return None
        edge = self.graph.edge_between(racer.current_vertex, selected)
        if edge is None or not edge.traversable():
            return None
        if self.player_route and racer.planned_route_index + 1 < len(self.player_route):
            expected = self.player_route[racer.planned_route_index + 1]
            if selected == expected:
                return self._planned_player_plan(racer)
        suffix = self._standard_plan(selected, racer.next_checkpoint, self.strategy_preset, self.route_algorithm)
        if not suffix or len(suffix.get("path", [])) < 1:
            return None
        path = [racer.current_vertex, *suffix["path"]]
        self.player_route = path
        self.player_deviated = True
        self.player_reroute_reason = "manual alternative road"
        racer.planned_route_index = 0
        return {"path": path[:2], "metrics": {"edge_ids": [edge.id]}, "planned": True, "rerouted": True}

    def _player_heading(self, racer: Racer) -> tuple[float, float]:
        if racer.current_path and racer.current_edge_index + 1 < len(racer.current_path):
            source = self.graph.vertices[racer.current_path[racer.current_edge_index]]
            target = self.graph.vertices[racer.current_path[racer.current_edge_index + 1]]
        elif racer.last_edge_from is not None and racer.last_edge_to is not None:
            source = self.graph.vertices[racer.last_edge_from]
            target = self.graph.vertices[racer.last_edge_to]
        elif self.player_route and racer.planned_route_index + 1 < len(self.player_route):
            source = self.graph.vertices[self.player_route[racer.planned_route_index]]
            target = self.graph.vertices[self.player_route[racer.planned_route_index + 1]]
        else:
            return 1.0, 0.0
        dx, dy = target.x - source.x, target.y - source.y
        length = max(1.0, math.hypot(dx, dy))
        return dx / length, dy / length

    def _decision_vertex(self, racer: Racer) -> int:
        """Return the junction where the player's next decision is made."""
        if racer.current_path and racer.edge_progress > 0 and racer.current_edge_index + 1 < len(racer.current_path):
            return racer.current_path[racer.current_edge_index + 1]
        return racer.current_vertex

    def _ordered_player_exits(self, racer: Racer, vertex_id: int | None = None) -> list[int]:
        vertex_id = racer.current_vertex if vertex_id is None else vertex_id
        hx, hy = self._player_heading(racer)
        options = []
        for target, edge in self.graph.neighbors(vertex_id):
            if not edge.traversable():
                continue
            vertex = self.graph.vertices[target]
            dx, dy = vertex.x - self.graph.vertices[vertex_id].x, vertex.y - self.graph.vertices[vertex_id].y
            length = max(1.0, math.hypot(dx, dy))
            cross = hx * (dy / length) - hy * (dx / length)
            dot = hx * (dx / length) + hy * (dy / length)
            options.append((math.atan2(cross, dot), target))
        return [target for _angle, target in sorted(options, key=lambda item: (item[0], item[1]))]

    def _choose_plan(self, racer: Racer):
        if (
            racer.strategy_type == RacerStrategy.HUMAN
            and racer.selected_exit is not None
            and racer.selected_exit_vertex == racer.current_vertex
            and racer.exit_confirmed
        ):
            selected_plan = self._plan_player_exit(racer)
            if selected_plan is not None:
                racer.selected_exit = None
                racer.selected_exit_vertex = None
                racer.exit_confirmed = False
                return selected_plan
        if racer.strategy_type == RacerStrategy.HUMAN and self.player_route:
            planned = self._planned_player_plan(racer)
            if planned is not None:
                return planned
            rerouted = self._recalculate_player_route(racer, "planned road unavailable")
            return rerouted or {"path": [racer.current_vertex]}

        detour = self._fuel_detour_plan(racer)
        if detour is not None:
            return detour
        if racer.strategy_type == RacerStrategy.FIXED_ROUTE:
            route = self.ai_routes.get(racer.id, [])
            planned = self._route_segment(racer, route)
            if planned is not None and not planned.get("planned_blocked"):
                return planned
            rerouted = self._standard_plan(racer.current_vertex, racer.next_checkpoint, "balanced")
            if rerouted and rerouted.get("path"):
                self.ai_routes[racer.id] = list(rerouted["path"])
                racer.planned_route_index = 0
                return self._route_segment(racer, self.ai_routes[racer.id]) or rerouted
            return {"path": [racer.current_vertex]}
        if racer.strategy_type == RacerStrategy.SHORTCUT:
            shortcut_candidates = []
            for target, edge in self.graph.neighbors(racer.current_vertex):
                if not edge.traversable() or not edge.is_shortcut:
                    continue
                # A shortcut is a route choice, not a U-turn.  Without this
                # guard an undirected shortcut can be selected again from its
                # far endpoint while the same checkpoint is still pending,
                # making the AI oscillate forever between two vertices.
                if racer.last_edge_from is not None and target == racer.last_edge_from:
                    continue
                suffix = self._standard_plan(target, racer.next_checkpoint, "speed")
                if suffix and suffix.get("path") and racer.current_vertex not in suffix["path"]:
                    shortcut_candidates.append((edge.id, target, suffix))
            if shortcut_candidates:
                _edge_id, target, suffix = sorted(shortcut_candidates)[0]
                racer.planned_route_index = 0
                return self._with_current_prefix(racer.current_vertex, suffix)
            result = self._standard_plan(racer.current_vertex, racer.next_checkpoint, "speed")
            return result or {"path": [racer.current_vertex]}
        if racer.strategy_type == RacerStrategy.MIN_DISTANCE:
            result = self._shortest_distance_plan(racer.current_vertex, racer.next_checkpoint)
            return result or {"path": [racer.current_vertex]}
        result = self._standard_plan(racer.current_vertex, racer.next_checkpoint, "balanced")
        return result or {"path": [racer.current_vertex]}

    def _route_segment(self, racer: Racer, route: list[int]) -> dict | None:
        if len(route) < 2:
            return None
        index = max(0, racer.planned_route_index)
        if index >= len(route) or route[index] != racer.current_vertex:
            matches = [position for position, vertex_id in enumerate(route[:-1]) if vertex_id == racer.current_vertex]
            if not matches:
                return None
            index = matches[0]
            racer.planned_route_index = index
        if index >= len(route) - 1:
            return None
        target = route[index + 1]
        edge = self.graph.edge_between(racer.current_vertex, target)
        if edge is None or not edge.traversable():
            return {"path": [racer.current_vertex, target], "planned_blocked": True}
        return {"path": [racer.current_vertex, target], "planned": True, "metrics": {"edge_ids": [edge.id]}}

    def _planned_player_plan(self, racer: Racer) -> dict | None:
        """Return the next exact player road from the Explorer handoff."""
        if len(self.player_route) < 2:
            return None
        plan = self._route_segment(racer, self.player_route)
        if plan and plan.get("planned_blocked"):
            return self._recalculate_player_route(racer, "road event blocked the active route")
        return plan

    def _advance_racer(self, racer: Racer, dt: float):
        if racer.finished or racer.dnf:
            return
        if racer.waiting > 0:
            racer.waiting = max(0.0, racer.waiting - dt)
            racer.total_time += dt
            return
        self._consume_vertex_actions(racer)
        if racer.finished:
            return
        if racer.waiting > 0:
            racer.waiting = max(0.0, racer.waiting - dt)
            racer.total_time += dt
            return
        plan = {}
        if racer.edge_progress > 0 and len(racer.current_path) > racer.current_edge_index + 1:
            next_vertex = racer.current_path[racer.current_edge_index + 1]
        else:
            plan = self._choose_plan(racer)
            if not plan or len(plan["path"]) < 2:
                racer.waiting += dt
                racer.decision_log.append("wait_no_route")
                if self.scheduler.next_time() is None and racer.waiting > 10:
                    racer.dnf = True
                return
            racer.current_path = plan["path"]
            racer.current_edge_index = 0
            racer.edge_progress = 0.0
            next_vertex = plan["path"][1]
        if plan.get("planned_blocked"):
            racer.dnf = True
            racer.decision_log.append("planned_route_blocked")
            return
        edge = self.graph.edge_between(racer.current_vertex, next_vertex)
        if edge is None or not edge.traversable():
            racer.current_path = []
            racer.decision_log.append("reroute_blocked")
            return
        if racer.edge_progress == 0.0:
            auto_nitro = (
                racer.nitro_charges > 0
                and racer.fuel > self.config.max_fuel * 0.35
                and (
                    (racer.strategy_type == RacerStrategy.FIXED_ROUTE and edge.distance >= 10 and edge.difficulty <= 3)
                    or (racer.strategy_type == RacerStrategy.SHORTCUT and edge.is_shortcut)
                    or (racer.strategy_type == RacerStrategy.MIN_DISTANCE and edge.effective_time() >= 10)
                )
            )
            if racer.manual_nitro or auto_nitro:
                racer.nitro_charges -= 1
                racer.nitro_uses += 1
                racer.active_nitro = True
                racer.manual_nitro = False
                racer.nitro_remaining = self.config.nitro_duration
                racer.decision_log.append("nitro_activate")
        speed_multiplier = self.config.nitro_speed_multiplier if racer.active_nitro else 1.0
        if racer.sprint_active:
            racer.sprint_remaining = max(0.0, racer.sprint_remaining - dt)
            if racer.sprint_remaining <= 0:
                racer.sprint_active = False
                racer.sprint_cooldown = self.config.sprint_cooldown
        else:
            racer.sprint_cooldown = max(0.0, racer.sprint_cooldown - dt)
        if racer.sprint_active:
            speed_multiplier *= self.config.sprint_speed_multiplier
        if racer.strategy_type == RacerStrategy.HUMAN:
            control_multiplier = max(0.25, 0.55 + (0.65 * racer.throttle) - (0.45 * racer.brake))
        else:
            control_multiplier = self.ai_multiplier
        if racer.active_nitro:
            racer.nitro_remaining = max(0.0, racer.nitro_remaining - dt)
            if racer.nitro_remaining <= 0:
                racer.active_nitro = False
        nitro_active = racer.active_nitro
        if nitro_active:
            racer.nitro_remaining = max(0.0, racer.nitro_remaining)
        travel_time = edge.effective_time() / max(speed_multiplier * control_multiplier, 0.1)
        fuel_multiplier = self.config.nitro_fuel_multiplier if nitro_active else 1.0
        if racer.sprint_active:
            fuel_multiplier *= self.config.sprint_fuel_multiplier
        fuel = edge.effective_fuel() * fuel_multiplier
        if racer.fuel + 1e-9 < fuel:
            racer.waiting += dt
            racer.decision_log.append("wait_low_fuel")
            if (
                racer.waiting > 5
                and self.graph.vertices[racer.current_vertex].type != VertexType.FUEL_STATION
            ):
                racer.dnf = True
            return
        progress = min(1.0, dt / max(travel_time, 1e-9))
        racer.fuel -= fuel * progress
        racer.fuel_used += fuel * progress
        racer.total_time += dt
        racer.edge_progress += progress
        if racer.edge_progress >= 1.0 - 1e-9:
            source_vertex = racer.current_vertex
            racer.fuel = max(0.0, racer.fuel)
            racer.current_vertex = next_vertex
            racer.current_edge_index = 0
            racer.current_path = []
            racer.edge_progress = 0.0
            if racer.selected_exit_vertex != racer.current_vertex:
                racer.selected_exit = None
                racer.selected_exit_vertex = None
                racer.exit_confirmed = False
            racer.last_edge_from = source_vertex
            racer.last_edge_to = next_vertex
            racer.decision_log.append(f"move_{edge.id}")
            active_route = self.player_route if racer.is_human else self.ai_routes.get(racer.id, [])
            if active_route:
                for position in range(racer.planned_route_index, len(active_route) - 1):
                    if active_route[position] == source_vertex and active_route[position + 1] == next_vertex:
                        racer.planned_route_index = position + 1
                        break
            self._consume_vertex_actions(racer)

    def _player(self) -> Racer | None:
        return next((racer for racer in self.racers if racer.is_human), None)

    def set_player_input(self, throttle: float, brake: float = 0.0) -> None:
        """Update presentation-independent player controls for the next fixed step."""
        racer = self._player()
        if racer is None:
            return
        racer.throttle = max(0.0, min(1.0, float(throttle)))
        racer.brake = max(0.0, min(1.0, float(brake)))

    def available_player_exits(self) -> list[int]:
        racer = self._player()
        if racer is None or racer.finished or racer.dnf:
            return []
        return self._ordered_player_exits(racer, self._decision_vertex(racer))

    def cycle_player_exit(self, direction: int) -> int | None:
        """Select a valid outgoing graph neighbor; selection never mutates topology."""
        racer = self._player()
        decision_vertex = self._decision_vertex(racer) if racer is not None else None
        options = (
            self._ordered_player_exits(racer, decision_vertex)
            if racer is not None and decision_vertex is not None
            else []
        )
        if racer is None or not options:
            return None
        if racer.selected_exit_vertex != decision_vertex or racer.selected_exit not in options:
            heading = self._player_heading(racer)
            signed = []
            current = self.graph.vertices[decision_vertex]
            for target in options:
                vertex = self.graph.vertices[target]
                angle = math.atan2(
                    heading[0] * (vertex.y - current.y) - heading[1] * (vertex.x - current.x),
                    heading[0] * (vertex.x - current.x) + heading[1] * (vertex.y - current.y),
                )
                signed.append((angle, target))
            left = [item for item in signed if item[0] < -0.05]
            right = [item for item in signed if item[0] > 0.05]
            if direction < 0 and left:
                index = options.index(max(left, key=lambda item: item[0])[1])
            elif direction > 0 and right:
                index = options.index(min(right, key=lambda item: item[0])[1])
            else:
                index = 0 if direction >= 0 else len(options) - 1
        else:
            index = (options.index(racer.selected_exit) + (1 if direction >= 0 else -1)) % len(options)
        racer.selected_exit = options[index]
        racer.selected_exit_vertex = decision_vertex
        racer.exit_confirmed = False
        racer.decision_log.append(f"select_exit_{racer.selected_exit}")
        return racer.selected_exit

    def confirm_player_exit(self) -> bool:
        racer = self._player()
        decision_vertex = self._decision_vertex(racer) if racer is not None else None
        options = (
            self._ordered_player_exits(racer, decision_vertex)
            if racer is not None and decision_vertex is not None
            else []
        )
        if (
            racer is None
            or racer.selected_exit_vertex != decision_vertex
            or racer.selected_exit not in options
        ):
            return False
        racer.exit_confirmed = True
        racer.decision_log.append(f"confirm_exit_{racer.selected_exit}")
        return True

    def request_refuel(self) -> bool:
        racer = self._player()
        if racer is None:
            return False
        vertex = self.graph.vertices[racer.current_vertex]
        if vertex.type != VertexType.FUEL_STATION or not vertex.active or racer.waiting > 0:
            return False
        racer.manual_refuel = True
        racer.decision_log.append("manual_refuel_requested")
        return True

    def activate_nitro(self, racer_id: int = 1) -> bool:
        racer = next((item for item in self.racers if item.id == racer_id), None)
        if racer is None or racer.nitro_charges <= 0 or racer.active_nitro:
            return False
        racer.manual_nitro = True
        return True

    def activate_sprint(self, racer_id: int = 1) -> bool:
        racer = next((item for item in self.racers if item.id == racer_id), None)
        if racer is None or racer.sprint_active or racer.sprint_cooldown > 0:
            return False
        racer.sprint_active = True
        racer.sprint_remaining = self.config.sprint_duration
        racer.decision_log.append("sprint_activate")
        return True

    def tick(self, dt: float | None = None) -> RaceSnapshot:
        if self.state.finished:
            return self.snapshot()
        dt = self.config.fixed_timestep if dt is None else dt
        self.state.elapsed += dt
        for event in self.scheduler.pop_due(self.state.elapsed):
            self._apply_event(event)
        for racer in self.racers:
            self._advance_racer(racer, dt)
        active = [r for r in self.racers if not r.finished and not r.dnf]
        if not active or self.state.elapsed >= self.config.race_time_limit:
            self.state.finished = True
        return self.snapshot()

    def run(self, max_ticks: int = 50000) -> list[RaceResult]:
        ticks = 0
        while not self.state.finished and ticks < max_ticks:
            self.tick()
            ticks += 1
        if ticks >= max_ticks:
            self.state.finished = True
        ranked = sorted(
            self.racers,
            key=lambda r: (not r.finished, r.lap * -1, r.next_checkpoint * -1, r.total_time, r.id),
        )
        results = []
        for position, racer in enumerate(ranked, 1):
            results.append(
                RaceResult(
                    self.state.race_id,
                    racer.id,
                    position,
                    racer.total_time if racer.finished else None,
                    racer.fastest_lap,
                    points_awarded=points_for_position(position) if racer.finished else 0,
                    dnf=racer.dnf,
                    fuel_used=round(racer.fuel_used, 3),
                    nitro_used=racer.nitro_uses,
                    completed_checkpoints=(racer.lap * len(self.track.checkpoint_ids)) + racer.next_checkpoint,
                    event_count=len(self.state.event_log),
                    mode=str(self.route_config.get("race_mode") or ""),
                    round_index=self.route_config.get("round_index"),
                )
            )
        return results

    def snapshot(self) -> RaceSnapshot:
        return RaceSnapshot(
            self.state.elapsed,
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "vertex": r.current_vertex,
                    "fuel": round(r.fuel, 2),
                    "nitro": r.nitro_charges,
                    "lap": r.lap,
                    "checkpoint": r.next_checkpoint,
                    "finished": r.finished,
                    "dnf": r.dnf,
                    "progress": round(r.edge_progress, 4),
                    "active_nitro": r.active_nitro,
                    "nitro_remaining": round(r.nitro_remaining, 2),
                    "sprint_active": r.sprint_active,
                    "sprint_remaining": round(r.sprint_remaining, 2),
                    "sprint_cooldown": round(r.sprint_cooldown, 2),
                    "waiting": round(r.waiting, 2),
                    "selected_exit": r.selected_exit,
                    "selected_exit_vertex": r.selected_exit_vertex,
                    "exit_confirmed": r.exit_confirmed,
                }
                for r in self.racers
            ],
            self.state.event_log[-8:],
            self.state.finished,
        )
