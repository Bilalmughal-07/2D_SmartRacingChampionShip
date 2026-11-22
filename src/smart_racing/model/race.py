from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RacerStrategy(str, Enum):
    HUMAN = "human"
    FIXED_ROUTE = "fixed_route"
    SHORTCUT = "shortcut"
    MIN_DISTANCE = "min_distance"


@dataclass
class Racer:
    id: int
    name: str
    is_human: bool
    strategy_type: RacerStrategy
    current_vertex: int
    fuel: float = 100.0
    nitro_charges: int = 3
    lap: int = 0
    next_checkpoint: int = 0
    total_time: float = 0.0
    edge_progress: float = 0.0
    manual_nitro: bool = False
    active_nitro: bool = False
    nitro_remaining: float = 0.0
    current_path: list[int] = field(default_factory=list)
    current_edge_index: int = 0
    finished: bool = False
    dnf: bool = False
    waiting: float = 0.0
    fastest_lap: float | None = None
    lap_started_at: float = 0.0
    decision_log: list[str] = field(default_factory=list)
    throttle: float = 1.0
    brake: float = 0.0
    manual_refuel: bool = False
    sprint_active: bool = False
    sprint_remaining: float = 0.0
    sprint_cooldown: float = 0.0
    selected_exit: int | None = None
    selected_exit_vertex: int | None = None
    exit_confirmed: bool = False
    fuel_used: float = 0.0
    nitro_uses: int = 0
    planned_route_index: int = 0
    last_edge_from: int | None = None
    last_edge_to: int | None = None


@dataclass
class RaceResult:
    race_id: str
    racer_id: int
    finish_position: int
    finish_time: float | None
    fastest_lap: float | None
    bonus_points: int = 0
    points_awarded: int = 0
    dnf: bool = False
    fuel_used: float = 0.0
    nitro_used: int = 0
    completed_checkpoints: int = 0
    event_count: int = 0
    mode: str = ""
    round_index: int | None = None


@dataclass
class ChampionshipEntry:
    racer_id: int
    name: str
    total_points: int = 0
    wins: int = 0
    sum_of_finish_positions: int = 0
    best_fastest_lap: float | None = None


@dataclass
class RaceState:
    race_id: str
    elapsed: float = 0.0
    finished: bool = False
    event_log: list[str] = field(default_factory=list)
