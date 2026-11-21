from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class Counters:
    visited_vertices: int = 0
    examined_edges: int = 0
    expanded_vertices: int = 0
    relaxed_edges: int = 0
    heap_operations: int = 0
    comparisons: int = 0
    states: int = 0
    pruned_states: int = 0


@dataclass
class AlgorithmResult:
    value: Any = None
    path: list[int] = field(default_factory=list)
    cost: float | None = None
    counters: Counters = field(default_factory=Counters)
    elapsed_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlgorithmTraceStep:
    operation: str
    state: dict[str, Any]
    counters: dict[str, int]


class TraceCollector:
    def __init__(self, max_steps: int = 5000):
        self.max_steps = max_steps
        self.steps: list[AlgorithmTraceStep] = []

    def emit(self, operation: str, state: dict[str, Any], counters: Counters) -> None:
        if len(self.steps) < self.max_steps:
            self.steps.append(AlgorithmTraceStep(operation, dict(state), counters.__dict__.copy()))


class Timer:
    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = (perf_counter() - self.start) * 1000
