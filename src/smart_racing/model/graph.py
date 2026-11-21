from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class VertexType(str, Enum):
    START = "Start"
    FINISH = "Finish"
    CHECKPOINT = "Checkpoint"
    INTERSECTION = "Intersection"
    FUEL_STATION = "FuelStation"
    NITRO_PICKUP = "NitroPickup"
    DEAD_END = "DeadEnd"


class EdgeStatus(str, Enum):
    OPEN = "Open"
    BLOCKED = "Blocked"
    RESTRICTED = "Restricted"


@dataclass
class Vertex:
    id: int
    x: float
    y: float
    type: VertexType = VertexType.INTERSECTION
    checkpoint_order: int | None = None
    active: bool = True


@dataclass
class Edge:
    id: int
    from_id: int
    to_id: int
    distance: float
    base_time: float
    fuel_cost: float
    difficulty: int = 1
    status: EdgeStatus = EdgeStatus.OPEN
    is_shortcut: bool = False
    directed: bool = False
    obstacle_penalty: float = 0.0
    effects: dict[str, dict] = field(default_factory=dict)

    def effective_difficulty(self) -> int:
        penalty = max(
            (float(v.get("difficulty_penalty", 0)) for v in self.effects.values()), default=0.0
        )
        return min(5, max(1, int(math.ceil(self.difficulty + penalty))))

    def effective_time(self) -> float:
        time = self.base_time
        multipliers = [float(v.get("time_multiplier", 1.0)) for v in self.effects.values()]
        if multipliers:
            time *= max(multipliers)
        caps = [float(v["speed_cap"]) for v in self.effects.values() if "speed_cap" in v]
        if caps:
            time = max(time, self.distance / min(caps))
        return time

    def effective_fuel(self) -> float:
        return self.fuel_cost * (1.0 + 0.1 * (self.effective_difficulty() - 1))

    def traversable(self) -> bool:
        return self.status != EdgeStatus.BLOCKED


class Graph:
    def __init__(self, vertices: Iterable[Vertex] = (), edges: Iterable[Edge] = ()) -> None:
        self.vertices: dict[int, Vertex] = {v.id: v for v in vertices}
        self.edges: dict[int, Edge] = {e.id: e for e in edges}
        self._adj: dict[int, list[tuple[int, int]]] = {v: [] for v in self.vertices}
        for edge in self.edges.values():
            self._add_edge_ref(edge.from_id, edge.to_id, edge.id)
            if not edge.directed:
                self._add_edge_ref(edge.to_id, edge.from_id, edge.id)

    def _add_edge_ref(self, source: int, target: int, edge_id: int) -> None:
        if source not in self._adj:
            raise ValueError(f"edge {edge_id} references missing source vertex {source}")
        if target not in self.vertices:
            raise ValueError(f"edge {edge_id} references missing target vertex {target}")
        self._adj[source].append((target, edge_id))
        self._adj[source].sort(key=lambda pair: (pair[0], pair[1]))

    def neighbors(self, vertex_id: int, *, include_blocked: bool = False) -> list[tuple[int, Edge]]:
        result = []
        for target, edge_id in self._adj.get(vertex_id, []):
            edge = self.edges[edge_id]
            if include_blocked or edge.traversable():
                result.append((target, edge))
        return result

    def set_edge_status(self, edge_id: int, status: EdgeStatus) -> None:
        self.edges[edge_id].status = (
            status if isinstance(status, EdgeStatus) else EdgeStatus(status)
        )

    def add_effect(self, edge_id: int, effect_id: str, values: dict) -> None:
        self.edges[edge_id].effects[effect_id] = dict(values)

    def remove_effect(self, edge_id: int, effect_id: str) -> None:
        self.edges[edge_id].effects.pop(effect_id, None)

    def activate_vertex(self, vertex_id: int, active: bool) -> None:
        self.vertices[vertex_id].active = active

    def edge_between(self, source: int, target: int) -> Edge | None:
        for candidate, edge in self.neighbors(source, include_blocked=True):
            if candidate == target:
                return edge
        return None


@dataclass
class Track:
    id: str
    name: str
    vertices: list[Vertex]
    edges: list[Edge]
    start_id: int
    finish_id: int
    checkpoint_ids: list[int]
    laps: int = 2
    time_limit: float = 600.0
    seed: int = 1
    description: str = ""
    theme: str = "emerald"

    def graph(self) -> Graph:
        return Graph(self.vertices, self.edges)

    def to_json(self, path: str | Path) -> None:
        payload = asdict(self)
        payload["vertices"] = [asdict(v) | {"type": v.type.value} for v in self.vertices]
        payload["edges"] = [asdict(e) | {"status": e.status.value} for e in self.edges]
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "Track":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        payload["vertices"] = [
            Vertex(**{**v, "type": VertexType(v["type"])}) for v in payload["vertices"]
        ]
        payload["edges"] = [
            Edge(**{**e, "status": EdgeStatus(e["status"])}) for e in payload["edges"]
        ]
        return cls(**payload)
