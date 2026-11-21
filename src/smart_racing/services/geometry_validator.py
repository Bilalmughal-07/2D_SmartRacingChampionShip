"""Screen-space-friendly validation for authoritative circuit geometry."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from smart_racing.model.graph import Track


@dataclass
class GeometryReport:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _proper_crossing(a, b, c, d) -> bool:
    values = (_orientation(a, b, c), _orientation(a, b, d), _orientation(c, d, a), _orientation(c, d, b))
    return (values[0] > 1e-6) != (values[1] > 1e-6) and (values[2] > 1e-6) != (values[3] > 1e-6)


def validate_geometry(track: Track, *, minimum_label_spacing: float = 18.0) -> GeometryReport:
    """Check authoritative coordinates before the renderer draws them.

    Crossings between non-connected roads are warnings rather than topology errors:
    the Explorer renders them with an explicit bridge marker so the visual crossing
    cannot be mistaken for a graph junction.
    """
    errors: list[str] = []
    warnings: list[str] = []
    vertices = {vertex.id: vertex for vertex in track.vertices}
    points = list(vertices.values())
    for index, first in enumerate(points):
        for second in points[index + 1 :]:
            if math.hypot(first.x - second.x, first.y - second.y) < 1e-6:
                errors.append(f"duplicate coordinates at vertices {first.id} and {second.id}")
            if first.checkpoint_order and second.checkpoint_order and math.hypot(first.x - second.x, first.y - second.y) < minimum_label_spacing:
                warnings.append(f"checkpoint labels {first.checkpoint_order} and {second.checkpoint_order} are close")
    segments = []
    for edge in track.edges:
        source, target = vertices[edge.from_id], vertices[edge.to_id]
        length = math.hypot(source.x - target.x, source.y - target.y)
        if length < 1e-6 or edge.distance <= 0:
            errors.append(f"edge {edge.id} has zero geometry or distance")
        segments.append((edge, (source.x, source.y), (target.x, target.y)))
    for index, (first, a, b) in enumerate(segments):
        for second, c, d in segments[index + 1 :]:
            if {first.from_id, first.to_id} & {second.from_id, second.to_id}:
                continue
            if _proper_crossing(a, b, c, d):
                warnings.append(f"roads {first.id} and {second.id} cross without a graph junction")
    return GeometryReport(valid=not errors, errors=errors, warnings=sorted(set(warnings)))
