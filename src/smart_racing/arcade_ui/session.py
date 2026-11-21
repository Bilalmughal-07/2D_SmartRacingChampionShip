from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from smart_racing.model.race import ChampionshipEntry, RaceResult
from smart_racing.services.scoring import record_results

DEFAULT_SETTINGS = {
    "fullscreen": False,
    "width": 1600,
    "height": 900,
    "music_volume": 0.65,
    "sfx_volume": 0.8,
    "effects": True,
}


def _json_default(value: Any):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Cannot persist {type(value).__name__}")


@dataclass
class GameSession:
    """Small authoritative state object shared by the Arcade views."""

    tracks: list[Any]
    settings_path: Path
    state_path: Path
    selected_track_id: str = "circuit_01"
    mode: str = "quick"
    championship_in_progress: bool = False
    championship_index: int = 0
    championship_points: dict[str, int] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    route_plan: dict[str, Any] | None = None
    selected_algorithm: str = "Dijkstra"
    championship_status: str = "NOT_STARTED"
    completed_races: list[str] = field(default_factory=list)
    race_history: list[dict[str, Any]] = field(default_factory=list)
    championship_entries: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_results: list[dict[str, Any]] = field(default_factory=list)
    explorer_mode: str = "full_race"
    explorer_return: str = "menu"
    explorer_context: dict[str, Any] = field(default_factory=dict)
    quick_race_config: dict[str, Any] = field(default_factory=dict)
    race_sequence: int = 0

    @classmethod
    def create(cls, tracks: list[Any], root: Path | None = None) -> "GameSession":
        base = root or Path(__file__).resolve().parents[3]
        session = cls(
            tracks=tracks,
            settings_path=base / "data" / "arcade_settings.json",
            state_path=base / "data" / "arcade_session.json",
        )
        session.load()
        return session

    def load(self) -> None:
        self.settings = dict(DEFAULT_SETTINGS)
        if self.settings_path.exists():
            try:
                stored = json.loads(self.settings_path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    self.settings.update({key: stored[key] for key in DEFAULT_SETTINGS if key in stored})
            except (OSError, ValueError, TypeError):
                self.settings = dict(DEFAULT_SETTINGS)
        if self.state_path.exists():
            try:
                stored = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    self.selected_track_id = str(stored.get("selected_track_id", self.selected_track_id))
                    self.mode = str(stored.get("mode", self.mode))
                    self.championship_in_progress = bool(stored.get("championship_in_progress", False))
                    self.championship_index = int(stored.get("championship_index", 0))
                    self.championship_points = {
                        str(key): int(value)
                        for key, value in dict(stored.get("championship_points", {})).items()
                    }
                    stored_plan = stored.get("route_plan")
                    self.route_plan = dict(stored_plan) if isinstance(stored_plan, dict) else None
                    self.selected_algorithm = str(stored.get("selected_algorithm", "Dijkstra"))
                    self.championship_status = str(stored.get("championship_status", "NOT_STARTED"))
                    self.completed_races = [str(item) for item in stored.get("completed_races", [])]
                    self.race_history = [dict(item) for item in stored.get("race_history", []) if isinstance(item, dict)]
                    self.championship_entries = {
                        str(key): dict(value)
                        for key, value in dict(stored.get("championship_entries", {})).items()
                        if isinstance(value, dict)
                    }
                    self.last_results = [dict(item) for item in stored.get("last_results", []) if isinstance(item, dict)]
                    self.explorer_mode = str(stored.get("explorer_mode", self.explorer_mode))
                    self.explorer_return = str(stored.get("explorer_return", self.explorer_return))
                    self.explorer_context = dict(stored.get("explorer_context", {}))
                    self.quick_race_config = dict(stored.get("quick_race_config", {}))
                    self.race_sequence = int(stored.get("race_sequence", 0))
            except (OSError, ValueError, TypeError):
                self.championship_in_progress = False

        if not any(track.id == self.selected_track_id for track in self.tracks):
            self.selected_track_id = self.tracks[0].id

    @property
    def selected_track(self) -> Any:
        return next(track for track in self.tracks if track.id == self.selected_track_id)

    @property
    def has_saved_championship(self) -> bool:
        return self.championship_in_progress and self.championship_index < len(self.tracks)

    def save_settings(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.settings, indent=2) + "\n", encoding="utf-8")

    def save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "selected_track_id": self.selected_track_id,
            "mode": self.mode,
            "championship_in_progress": self.championship_in_progress,
            "championship_index": self.championship_index,
            "championship_points": self.championship_points,
            "selected_algorithm": self.selected_algorithm,
            "route_plan": self.route_plan,
            "championship_status": self.championship_status,
            "completed_races": self.completed_races,
            "race_history": self.race_history,
            "championship_entries": self.championship_entries,
            "last_results": self.last_results,
            "explorer_mode": self.explorer_mode,
            "explorer_return": self.explorer_return,
            "explorer_context": self.explorer_context,
        }
        payload.update(
            {
                "quick_race_config": self.quick_race_config,
                "race_sequence": self.race_sequence,
            }
        )
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, default=_json_default) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def start_new_championship(self) -> None:
        self.mode = "championship"
        self.championship_in_progress = True
        self.championship_index = 0
        self.championship_points = {"Player": 0, "Navigator": 0, "Shortcut": 0, "Distance": 0}
        self.championship_status = "ACTIVE"
        self.completed_races = []
        self.race_history = []
        self.last_results = []
        self.championship_entries = {
            str(index): ChampionshipEntry(index, name).__dict__.copy()
            for index, name in enumerate(("Player", "Navigator", "Shortcut", "Distance"), 1)
        }
        self.selected_track_id = self.tracks[0].id
        self.route_plan = None
        self.explorer_mode = "full_race"
        self.explorer_return = "menu"
        self.explorer_context = {}
        self.quick_race_config = {}
        self.save_state()

    def continue_championship(self) -> None:
        self.mode = "championship"
        if not self.has_saved_championship:
            self.start_new_championship()
        else:
            self.selected_track_id = self.tracks[self.championship_index].id
            self.championship_status = "ACTIVE"
            self.explorer_mode = "full_race"
            self.explorer_return = "dashboard"
            self.explorer_context = {}
            self.save_state()

    def configure_quick_race(self, track_id: str, **settings: Any) -> dict[str, Any]:
        """Persist the standalone race setup and return its immutable launch config."""
        self.select_quick_race(track_id)
        self.race_sequence += 1
        config = {
            "laps": 2,
            "ai_difficulty": "Normal",
            "events_enabled": True,
            "routing": "Balanced",
            "race_mode": "quick",
            **settings,
        }
        config["race_id"] = f"quick-{track_id}-{self.race_sequence}"
        self.quick_race_config = config
        # A setup selection is not a route plan. Track Explorer must create and
        # validate the route before a Racing View can be opened.
        self.route_plan = None
        self.explorer_mode = "full_race"
        self.explorer_context = {
            "track_id": track_id,
            "preset": str(config.get("routing", "Balanced")).lower(),
            "explorer_mode": "full_race",
        }
        self.explorer_return = "quick_setup"
        self.save_state()
        return dict(config)

    def prepare_championship_race(self) -> dict[str, Any]:
        if not self.has_saved_championship:
            raise ValueError("No championship round is available")
        self.mode = "championship"
        self.selected_track_id = self.tracks[self.championship_index].id
        self.race_sequence += 1
        config = {
            "laps": int(self.selected_track.laps),
            "ai_difficulty": "Normal",
            "events_enabled": True,
            "routing": "Balanced",
            "race_mode": "championship",
            "round_index": self.championship_index,
            "race_id": f"championship-{self.championship_index + 1}-{self.race_sequence}",
        }
        self.quick_race_config = config
        # Each championship round gets a fresh planning session on its own
        # circuit. The route is populated only by Track Explorer confirmation.
        self.route_plan = None
        self.explorer_mode = "full_race"
        self.explorer_context = {
            "track_id": self.selected_track_id,
            "preset": "balanced",
            "explorer_mode": "full_race",
        }
        self.explorer_return = "dashboard"
        self.save_state()
        return dict(config)

    def select_quick_race(self, track_id: str) -> None:
        if not any(track.id == track_id for track in self.tracks):
            raise ValueError(f"Unknown circuit: {track_id}")
        self.mode = "quick"
        self.selected_track_id = track_id
        self.route_plan = None
        self.explorer_mode = "full_race"
        self.explorer_return = "circuit_selection"
        self.explorer_context = {}
        self.save_state()

    def set_route_plan(self, route_plan: dict[str, Any]) -> None:
        self.route_plan = dict(route_plan)
        self.selected_algorithm = str(route_plan.get("algorithm", self.selected_algorithm))
        self.selected_track_id = str(route_plan.get("track_id", self.selected_track_id))
        self.save_state()

    def record_race_results(self, track_id: str, results: list[RaceResult]) -> bool:
        """Persist one race exactly once and update championship standings when applicable."""
        race_id = str(results[0].race_id) if results else track_id
        if race_id in self.completed_races:
            return False
        self.last_results = [result.__dict__.copy() for result in results]
        mode = "championship" if self.mode == "championship" else "quick"
        self.race_history.append(
            {
                "track_id": track_id,
                "race_id": race_id,
                "mode": mode,
                "round_index": self.championship_index if mode == "championship" else None,
                "results": self.last_results,
            }
        )
        if self.mode == "championship":
            entries = {
                int(key): ChampionshipEntry(**value)
                for key, value in self.championship_entries.items()
            }
            if not entries:
                entries = {
                    index: ChampionshipEntry(index, name)
                    for index, name in enumerate(("Player", "Navigator", "Shortcut", "Distance"), 1)
                }
            record_results(entries, results)
            self.championship_entries = {str(key): value.__dict__.copy() for key, value in entries.items()}
            self.championship_points = {entry.name: entry.total_points for entry in entries.values()}
            self.completed_races.append(race_id)
            self.championship_index = min(self.championship_index + 1, len(self.tracks))
            self.championship_status = "COMPLETED" if self.championship_index >= len(self.tracks) else "AWAITING_NEXT_RACE"
            if self.championship_index < len(self.tracks):
                self.selected_track_id = self.tracks[self.championship_index].id
        self.route_plan = None
        self.save_state()
        return True

    def close(self) -> None:
        self.save_settings()
        self.save_state()
