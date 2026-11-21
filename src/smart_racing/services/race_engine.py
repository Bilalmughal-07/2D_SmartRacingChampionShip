from __future__ import annotations

import copy
from dataclasses import dataclass

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
        self.player_route = [
            int(vertex_id) for vertex_id in self.route_config.get("player_path", [])
        ]
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
                track.start_id,
                config.initial_fuel,
                config.initial_nitro,
            ),
            Racer(
                2,
                "Navigator",
                False,
                RacerStrategy.FIXED_ROUTE,
                track.start_id,
                config.initial_fuel,
                config.initial_nitro,
            ),
            Racer(
                3,
                "Shortcut",
                False,
                RacerStrategy.SHORTCUT,
                track.start_id,
                config.initial_fuel,
                config.initial_nitro,
            ),
            Racer(
                4,
                "Distance",
                False,
                RacerStrategy.MIN_DISTANCE,
                track.start_id,
                config.initial_fuel,
                config.initial_nitro,
            ),
        ]
        self._next_event_id = 1
        if self.events_enabled:
            self._schedule_default_events()

    def _schedule_default_events(self):
        events = [
            (12.0, 1, EventType.ROAD_BLOCKAGE, 3, 12.0, {}),
            (25.0, 2, EventType.SHORTCUT_TOGGLE, 10, 20.0, {}),
            (
                38.0,
                3,
                EventType.OIL_SPILL,
                5,
                20.0,
                {"difficulty_penalty": 2, "time_multiplier": 1.5, "obstacle_penalty": 2},
            ),
            (55.0, 4, EventType.SPEED_RESTRICTION, 7, 15.0, {"speed_cap": 2.5}),
        ]
        for trigger, priority, kind, target, duration, payload in events:
            self.schedule_event(kind, trigger, priority, target, duration, payload)

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
            racer.next_checkpoint < len(self.track.checkpoint_ids)
            and racer.current_vertex == self.track.checkpoint_ids[racer.next_checkpoint]
        ):
            racer.next_checkpoint += 1
            racer.decision_log.append(f"checkpoint_{racer.next_checkpoint}")
        if racer.current_vertex == self.track.finish_id and racer.next_checkpoint == len(
            self.track.checkpoint_ids
        ):
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
                racer.current_vertex = self.track.start_id
                racer.next_checkpoint = 0
                racer.current_path = []
                racer.current_edge_index = 0
                racer.planned_route_index = 0

    def _choose_plan(self, racer: Racer):
        if racer.strategy_type == RacerStrategy.HUMAN and self.player_route:
            planned = self._planned_player_plan(racer)
            if planned is not None:
                return planned
            return {"path": [racer.current_vertex]}
        if (
            racer.strategy_type == RacerStrategy.HUMAN
            and racer.selected_exit is not None
            and racer.exit_confirmed
        ):
            selected = racer.selected_exit
            edge = self.graph.edge_between(racer.current_vertex, selected)
            if edge is not None and edge.traversable():
                suffix = self.planner.plan_checkpoints(
                    selected, racer.next_checkpoint, algorithm=self.route_algorithm, include_resources=False
                )
                if suffix and suffix["path"]:
                    return {**suffix, "path": [racer.current_vertex, *suffix["path"]]}
        if racer.strategy_type == RacerStrategy.MIN_DISTANCE:
            saved = self.planner.cost_model.preset
            self.planner.cost_model.set_preset(
                "balanced" if self.strategy_preset == "balanced" else self.strategy_preset
            )
            result = self.planner.plan_checkpoints(
                racer.current_vertex, racer.next_checkpoint, algorithm=self.route_algorithm, include_resources=False
            )
            self.planner.cost_model.set_preset(saved)
            return result
        return self.planner.plan_checkpoints(
            racer.current_vertex, racer.next_checkpoint, algorithm=self.route_algorithm, include_resources=False
        )

    def _planned_player_plan(self, racer: Racer) -> dict | None:
        """Return the next exact player road from the Explorer handoff."""
        if len(self.player_route) < 2:
            return None
        index = max(0, racer.planned_route_index)
        if index >= len(self.player_route) or self.player_route[index] != racer.current_vertex:
            matches = [
                position
                for position, vertex_id in enumerate(self.player_route[:-1])
                if vertex_id == racer.current_vertex and position >= index
            ]
            if not matches:
                matches = [
                    position
                    for position, vertex_id in enumerate(self.player_route[:-1])
                    if vertex_id == racer.current_vertex
                ]
            if not matches:
                return None
            index = matches[0]
            racer.planned_route_index = index
        if index >= len(self.player_route) - 1:
            return None
        target = self.player_route[index + 1]
        edge = self.graph.edge_between(racer.current_vertex, target)
        if edge is None or not edge.traversable():
            return {"path": [racer.current_vertex, target], "planned_blocked": True}
        return {
            "path": [racer.current_vertex, target],
            "metrics": {"edge_ids": [edge.id]},
            "planned": True,
        }

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
                and racer.strategy_type in (RacerStrategy.SHORTCUT, RacerStrategy.MIN_DISTANCE)
                and int(racer.total_time) % 17 == 0
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
            racer.selected_exit = None
            racer.exit_confirmed = False
            racer.decision_log.append(f"move_{edge.id}")
            if racer.is_human and self.player_route:
                for position in range(racer.planned_route_index, len(self.player_route) - 1):
                    if self.player_route[position] == source_vertex and self.player_route[position + 1] == next_vertex:
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
        if self.player_route:
            planned = self._planned_player_plan(racer)
            if planned and not planned.get("planned_blocked"):
                return [planned["path"][1]]
            return []
        return [target for target, edge in self.graph.neighbors(racer.current_vertex) if edge.traversable()]

    def cycle_player_exit(self, direction: int) -> int | None:
        """Select a valid outgoing graph neighbor; selection never mutates topology."""
        racer = self._player()
        options = self.available_player_exits()
        if racer is None or not options:
            return None
        if racer.selected_exit not in options:
            index = 0 if direction >= 0 else len(options) - 1
        else:
            index = (options.index(racer.selected_exit) + (1 if direction >= 0 else -1)) % len(options)
        racer.selected_exit = options[index]
        racer.exit_confirmed = False
        racer.decision_log.append(f"select_exit_{racer.selected_exit}")
        return racer.selected_exit

    def confirm_player_exit(self) -> bool:
        racer = self._player()
        if racer is None or racer.selected_exit not in self.available_player_exits():
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
                    "exit_confirmed": r.exit_confirmed,
                }
                for r in self.racers
            ],
            self.state.event_log[-8:],
            self.state.finished,
        )
