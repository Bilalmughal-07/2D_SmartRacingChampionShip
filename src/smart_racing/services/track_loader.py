from __future__ import annotations

import json
from pathlib import Path

from smart_racing.model.graph import Edge, Track, Vertex, VertexType

TRACK_DIR = Path(__file__).resolve().parents[1] / "tracks"


def _edge(edges, edge_id, source, target, distance, difficulty=2, shortcut=False, directed=False):
    edges.append(
        Edge(
            edge_id,
            source,
            target,
            float(distance),
            float(distance) / 4.0,
            float(distance) / 12.0,
            max(1, min(5, difficulty)),
            is_shortcut=shortcut,
            directed=directed,
        )
    )
    return edge_id + 1


def _build_edges(specs):
    """Build an edge list from readable topology specifications."""
    edges = []
    edge_id = 0
    for source, target, distance, difficulty, shortcut, directed in specs:
        edge_id = _edge(edges, edge_id, source, target, distance, difficulty, shortcut, directed)
    return edges


def _make_vertices(points):
    return [
        Vertex(i, float(x), float(y), VertexType.INTERSECTION) for i, (x, y) in enumerate(points)
    ]


def _finalize(index, name, theme, vertices, edges, checkpoints, finish, description):
    vertices[0].type = VertexType.START
    vertices[finish].type = VertexType.FINISH
    for order, vertex_id in enumerate(checkpoints, 1):
        vertices[vertex_id].type = VertexType.CHECKPOINT
        vertices[vertex_id].checkpoint_order = order
    return Track(
        f"circuit_{index:02d}",
        name,
        vertices,
        edges,
        0,
        finish,
        checkpoints,
        laps=2,
        time_limit=600,
        seed=index,
        description=description,
        theme=theme,
    )


def _emerald_loop() -> Track:
    points = [
        (400, 90), (560, 120), (680, 200), (720, 330), (680, 480), (560, 570),
        (400, 610), (240, 570), (120, 480), (80, 330), (120, 190), (240, 120),
        (400, 250), (400, 450), (255, 350), (545, 350), (265, 160), (535, 500),
        (620, 255), (180, 410), (400, 350), (255, 350),
    ]
    vertices = _make_vertices(points)
    for vertex_id, vertex_type in [
        (16, VertexType.FUEL_STATION),
        (17, VertexType.FUEL_STATION),
        (18, VertexType.NITRO_PICKUP),
        (19, VertexType.NITRO_PICKUP),
        (20, VertexType.DEAD_END),
    ]:
        vertices[vertex_id].type = vertex_type
    edges = _build_edges(
        [
            (0, 1, 12, 2, False, False), (1, 2, 11, 2, False, False),
            (2, 3, 11, 2, False, False), (3, 4, 10, 2, False, False),
            (4, 5, 10, 2, False, False), (5, 6, 11, 2, False, False),
            (6, 7, 11, 2, False, False), (7, 8, 10, 2, False, False),
            (8, 9, 10, 2, False, False), (9, 10, 10, 2, False, False),
            (10, 11, 10, 2, False, False), (11, 0, 9, 1, False, False),
            (1, 12, 7, 3, True, False), (12, 2, 7, 3, True, False),
            (5, 13, 7, 4, True, False), (13, 6, 7, 4, True, False),
            (2, 15, 8, 2, False, False), (15, 3, 8, 2, False, False),
            (7, 14, 8, 2, False, False), (14, 8, 8, 2, False, False),
            (12, 21, 8, 2, False, False), (21, 13, 8, 2, False, False),
            (15, 21, 9, 3, False, False), (21, 20, 7, 2, False, False),
            (10, 16, 4, 1, False, False), (16, 11, 4, 1, False, False),
            (5, 17, 4, 2, False, False), (17, 6, 4, 2, False, False),
            (2, 18, 3, 2, False, False), (18, 3, 3, 2, False, False),
            (8, 19, 3, 2, False, False), (19, 9, 3, 2, False, False),
        ]
    )
    return _finalize(
        1,
        "Circuit 1 — Emerald Loop",
        "emerald",
        vertices,
        edges,
        list(range(1, 11)),
        11,
        "Green oval raceway with embedded pit lanes, inner corner cuts, reachable nitro lines, and a marshal dead-end branch.",
    )


def _canyon_switchbacks() -> Track:
    points = [
        (100, 600), (180, 520), (300, 560), (420, 490), (540, 540), (680, 450),
        (560, 370), (680, 290), (520, 240), (640, 150), (470, 100), (360, 220),
        (250, 300), (430, 320), (300, 430), (100, 430),
    ]
    points.extend(
        [
            (480, 515), (620, 410), (600, 265), (555, 175), (330, 75), (260, 420),
            (520, 330), (210, 460), (570, 120), (150, 330), (610, 360), (340, 600),
            (365, 360), (760, 300),
        ]
    )
    vertices = _make_vertices(points)
    for vertex_id, vertex_type in [
        (16, VertexType.FUEL_STATION), (17, VertexType.NITRO_PICKUP),
        (18, VertexType.FUEL_STATION), (19, VertexType.NITRO_PICKUP),
        (20, VertexType.DEAD_END), (23, VertexType.FUEL_STATION),
        (24, VertexType.NITRO_PICKUP), (27, VertexType.FUEL_STATION),
        (28, VertexType.NITRO_PICKUP), (29, VertexType.DEAD_END),
    ]:
        vertices[vertex_id].type = vertex_type
    edges = _build_edges(
        [
            (0, 1, 11, 3, False, False), (1, 2, 13, 3, False, False),
            (2, 3, 14, 3, False, False), (3, 4, 14, 4, False, False),
            (4, 5, 16, 4, False, False), (5, 6, 15, 4, False, False),
            (6, 7, 15, 4, False, False), (7, 8, 16, 4, False, False),
            (8, 9, 15, 4, False, False), (9, 10, 16, 4, False, False),
            (10, 11, 15, 3, False, False), (11, 12, 12, 3, False, False),
            (12, 13, 13, 3, False, False), (13, 14, 13, 3, False, False),
            (14, 15, 14, 3, False, False), (15, 0, 12, 3, False, False),
            (3, 21, 9, 5, True, False), (21, 4, 9, 5, True, False),
            (6, 22, 9, 5, True, False), (22, 7, 9, 5, True, False),
            (1, 12, 19, 3, False, False), (2, 21, 13, 3, False, False),
            (4, 22, 11, 4, False, False), (7, 26, 10, 3, False, False),
            (26, 10, 12, 3, False, False), (11, 25, 10, 2, False, False),
            (25, 15, 10, 2, False, False), (13, 24, 5, 3, False, False),
            (24, 14, 5, 3, False, False), (11, 20, 8, 3, False, False),
            (26, 29, 8, 4, False, False),
            (3, 16, 5, 2, False, False), (16, 4, 5, 2, False, False),
            (5, 17, 5, 3, False, False), (17, 6, 5, 3, False, False),
            (7, 18, 5, 2, False, False), (18, 8, 5, 2, False, False),
            (9, 19, 4, 3, False, False), (19, 10, 4, 3, False, False),
            (14, 23, 4, 2, False, False), (23, 15, 4, 2, False, False),
            (0, 27, 5, 2, False, False), (27, 1, 5, 2, False, False),
            (10, 28, 7, 3, False, False), (28, 11, 7, 3, False, False),
        ]
    )
    return _finalize(
        2,
        "Circuit 2 — Canyon Switchbacks",
        "canyon",
        vertices,
        edges,
        list(range(1, 11)),
        15,
        "Amber canyon switchbacks with embedded service lanes, risky corner cuts, reachable pickups, and marshal dead ends.",
    )


def _metro_grid() -> Track:
    points = [
        (100, 100), (260, 100), (420, 100), (580, 100), (700, 210), (700, 360),
        (700, 510), (580, 620), (420, 660), (260, 620), (100, 510), (100, 300),
        (260, 260), (420, 260), (580, 260), (580, 440), (760, 360), (260, 690),
        (340, 260), (640, 570), (420, 360), (260, 440), (580, 520), (100, 260),
    ]
    vertices = _make_vertices(points)
    for vertex_id, vertex_type in [
        (16, VertexType.FUEL_STATION),
        (17, VertexType.FUEL_STATION),
        (18, VertexType.NITRO_PICKUP),
        (19, VertexType.NITRO_PICKUP),
        (20, VertexType.DEAD_END),
    ]:
        vertices[vertex_id].type = vertex_type
    edges = _build_edges(
        [
            (0, 1, 12, 1, False, False), (1, 2, 12, 1, False, False),
            (2, 3, 12, 1, False, False), (3, 4, 10, 2, False, False),
            (4, 5, 10, 2, False, False), (5, 6, 10, 2, False, False),
            (6, 7, 12, 2, False, False), (7, 8, 12, 2, False, False),
            (8, 9, 12, 2, False, False), (9, 10, 12, 2, False, False),
            (10, 11, 10, 1, False, False), (11, 0, 10, 1, False, False),
            (1, 12, 7, 3, True, True), (12, 2, 7, 3, True, True),
            (6, 19, 8, 4, True, True), (19, 7, 8, 4, True, True),
            (2, 13, 8, 2, False, False), (13, 3, 8, 2, False, False),
            (3, 14, 8, 2, False, False), (14, 4, 8, 2, False, False),
            (5, 15, 8, 2, False, False), (15, 6, 8, 2, False, False),
            (7, 22, 8, 2, False, False), (22, 8, 8, 2, False, False),
            (8, 21, 8, 2, False, False), (21, 9, 8, 2, False, False),
            (9, 23, 8, 2, False, False), (23, 10, 8, 2, False, False),
            (10, 23, 7, 2, False, False), (23, 11, 7, 2, False, False),
            (12, 13, 7, 2, False, False), (13, 14, 7, 2, False, False),
            (12, 21, 8, 2, False, False), (21, 15, 8, 2, False, False),
            (14, 15, 8, 2, False, False), (13, 20, 7, 2, False, False),
            (5, 16, 4, 1, False, False), (16, 6, 4, 1, False, False),
            (8, 17, 4, 2, False, False), (17, 9, 4, 2, False, False),
            (12, 18, 4, 2, False, False), (18, 13, 4, 2, False, False),
        ]
    )
    checkpoints = list(range(1, 11))
    return _finalize(
        3,
        "Circuit 3 — Metro Grid",
        "metro",
        vertices,
        edges,
        checkpoints,
        15,
        "Dense urban street circuit with embedded pit lanes, directed block shortcuts, reachable nitro corridors, and closure-sensitive routing.",
    )


def _make_track(index: int) -> Track:
    return {1: _emerald_loop, 2: _canyon_switchbacks, 3: _metro_grid}[index]()


def generate_default_tracks(directory: str | Path = TRACK_DIR) -> list[Track]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    tracks = [_make_track(i) for i in (1, 2, 3)]
    for track in tracks:
        payload = {
            "id": track.id,
            "name": track.name,
            "start_id": track.start_id,
            "finish_id": track.finish_id,
            "checkpoint_ids": track.checkpoint_ids,
            "laps": track.laps,
            "time_limit": track.time_limit,
            "seed": track.seed,
            "description": track.description,
            "theme": track.theme,
            "vertices": [{**v.__dict__, "type": v.type.value} for v in track.vertices],
            "edges": [{**e.__dict__, "status": e.status.value} for e in track.edges],
        }
        (directory / f"{track.id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return tracks


def load_tracks(directory: str | Path = TRACK_DIR) -> list[Track]:
    directory = Path(directory)
    files = sorted(directory.glob("circuit_*.json"))
    if not files:
        return generate_default_tracks(directory)
    return [Track.from_json(path) for path in files]
