from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlacementResult:
    placements: list[int]
    valid: bool
    explored_states: int
    pruned_states: int
    reason: str = ""


def place_services_backtracking(
    vertices: list[int], checkpoint_ids: set[int], required: int = 2, min_gap: int = 2
) -> PlacementResult:
    placements: list[int] = []
    explored = 0
    pruned = 0

    def search(index: int) -> bool:
        nonlocal explored, pruned
        explored += 1
        if len(placements) == required:
            return True
        if len(vertices) - index < required - len(placements):
            pruned += 1
            return False
        for pos in range(index, len(vertices)):
            candidate = vertices[pos]
            if candidate in checkpoint_ids or any(
                abs(pos - vertices.index(p)) < min_gap for p in placements
            ):
                pruned += 1
                continue
            placements.append(candidate)
            if search(pos + 1):
                return True
            placements.pop()
        return False

    valid = search(0)
    return PlacementResult(
        placements.copy(), valid, explored, pruned, "no feasible placement" if not valid else ""
    )
