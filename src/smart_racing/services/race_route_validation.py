from __future__ import annotations

from typing import Any

from smart_racing.model.graph import EdgeStatus, Graph, Track


def validate_planned_route(
    track: Track,
    graph: Graph,
    route_result: dict[str, Any] | None,
    *,
    route_revision: int,
    graph_revision: int,
    source_id: int,
    destination_id: int,
    resource_accepted: bool,
    checkpoint_aware: bool = True,
) -> dict[str, Any]:
    """Validate the exact route that will be transferred to the race engine."""
    errors: list[str] = []
    if route_result is None:
        errors.append("Calculate a route before starting the race.")
        return {"valid": False, "errors": errors}
    if route_revision != graph_revision:
        errors.append("The route is stale because the road graph changed; recalculate it.")
    metrics = route_result.get("metrics", {})
    if not metrics.get("valid"):
        errors.append("The planned route is not valid under the current road graph.")
    path = list(route_result.get("path", []))
    if len(path) < 2:
        errors.append("The planned route must contain at least one road.")
    if checkpoint_aware and source_id != track.start_id:
        errors.append("The route source must be the circuit start vertex.")
    if checkpoint_aware and destination_id != track.finish_id:
        errors.append("The route destination must be the circuit finish vertex.")
    if path and path[0] != source_id:
        errors.append("The planned route does not begin at the selected source.")
    if path and path[-1] != destination_id:
        errors.append("The planned route does not end at the selected destination.")

    for source, target in zip(path, path[1:]):
        edge = graph.edge_between(source, target)
        if edge is None:
            errors.append(f"Road connection {source} → {target} is missing.")
            continue
        if edge.status == EdgeStatus.BLOCKED or not edge.traversable():
            errors.append(f"Road E{edge.id} is blocked on the planned route.")

    if checkpoint_aware:
        checkpoint_cursor = 0
        for vertex_id in path:
            if checkpoint_cursor < len(track.checkpoint_ids) and vertex_id == track.checkpoint_ids[checkpoint_cursor]:
                checkpoint_cursor += 1
        if checkpoint_cursor != len(track.checkpoint_ids):
            errors.append(
                f"The route visits {checkpoint_cursor}/{len(track.checkpoint_ids)} mandatory checkpoints in order."
            )

    resources = route_result.get("resources", {}) or {}
    if not resources.get("fuel_feasible", False):
        errors.append("Fuel feasibility failed for the planned route.")
    if not resource_accepted:
        errors.append("Accept the calculated fuel/nitro resource plan before racing.")

    return {
        "valid": not errors,
        "errors": errors,
        "path": path,
        "edge_ids": list(metrics.get("edge_ids", [])),
        "resources": resources,
    }
