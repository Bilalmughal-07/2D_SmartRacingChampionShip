from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    ROAD_BLOCKAGE = "road_blockage"
    ROAD_REOPEN = "road_reopen"
    SHORTCUT_TOGGLE = "shortcut_toggle"
    OIL_SPILL = "oil_spill"
    SPEED_RESTRICTION = "speed_restriction"
    FUEL_STATION = "fuel_station"
    NITRO_BOOSTER = "nitro_booster"
    EFFECT_EXPIRE = "effect_expire"


@dataclass
class Event:
    event_id: int
    type: EventType
    trigger_time: float
    priority: int
    insertion_sequence: int
    target_id: int | None = None
    duration: float = 0.0
    payload: dict | None = None
    cancelled: bool = False
    effect_id: str | None = None

    def key(self) -> tuple[float, int, int]:
        return (self.trigger_time, self.priority, self.insertion_sequence)
