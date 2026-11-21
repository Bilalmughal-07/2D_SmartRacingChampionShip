from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig:
    fixed_timestep: float = 1.0 / 60.0
    window_width: int = 1440
    window_height: int = 900
    target_fps: int = 60
    max_fuel: float = 100.0
    fuel_purchase_cap: float = 40.0
    fuel_station_stop_time: float = 3.0
    max_nitro: int = 3
    nitro_speed_multiplier: float = 1.5
    nitro_duration: float = 4.0
    nitro_fuel_multiplier: float = 2.0
    sprint_speed_multiplier: float = 1.18
    sprint_duration: float = 2.0
    sprint_cooldown: float = 6.0
    sprint_fuel_multiplier: float = 1.2
    laps: int = 2
    race_time_limit: float = 600.0
    checkpoint_count: int = 10
    initial_fuel: float = 100.0
    initial_nitro: int = 3


DEFAULT_CONFIG = GameConfig()
