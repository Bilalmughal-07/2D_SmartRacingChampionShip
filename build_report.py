# This script intentionally keeps report prose as long text literals.
# ruff: noqa: E501
from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "pdf" / "Smart_Racing_Technical_Report.pdf"


def read_rows(name):
    path = ROOT / "experiments" / "data" / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(
        2 * cm, 1.1 * cm, "Smart Racing Championship | Design and Analysis of Algorithms"
    )
    canvas.drawRightString(19 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.restoreState()


def table(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15395b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b8c5d1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4f8")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#15395b"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubCenter",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#4f6475"),
        )
    )
    styles["Heading1"].textColor = colors.HexColor("#15395b")
    styles["Heading2"].textColor = colors.HexColor("#1a5c86")
    body = styles["BodyText"]
    story = []
    story += [
        Spacer(1, 4 * cm),
        Paragraph("SMART RACING CHAMPIONSHIP", styles["TitleCenter"]),
        Paragraph("The Algorithmic Racing Challenge", styles["SubCenter"]),
        Spacer(1, 0.7 * cm),
        Paragraph("Technical Report", styles["TitleCenter"]),
        Paragraph("Design and Analysis of Algorithms", styles["SubCenter"]),
        Spacer(1, 2 * cm),
        Paragraph("Group members: ________________________________", styles["SubCenter"]),
        Paragraph("Registration numbers: __________________________", styles["SubCenter"]),
        Paragraph("Section: __________", styles["SubCenter"]),
        PageBreak(),
    ]
    story += [
        Paragraph("1. Introduction and Problem Statement", styles["Heading1"]),
        Paragraph(
            "Smart Racing Championship is a deterministic 2D top-down racing game designed to demonstrate algorithmic problem solving in a changing road network. Circuits are represented as sparse graphs containing intersections, ordered checkpoints, fuel stations, nitro pickups, shortcuts, obstacles, and dynamic road events. The main engineering goal is not graphical realism; it is the correct modelling, implementation, integration, measurement, and explanation of algorithms used during gameplay.",
            body,
        ),
        Spacer(1, 8),
        Paragraph(
            "The system supports route exploration, weighted route optimization, resource planning, event processing, deterministic opponents, championship ranking, visualization, and reproducible experiments. No machine learning or reinforcement learning is used.",
            body,
        ),
        Paragraph("2. System Architecture and Game Flow", styles["Heading1"]),
        Paragraph(
            "The code is separated into model, algorithm, service, and UI layers. The race engine owns a live graph snapshot and shares it with the route planner, ensuring that closures and restrictions immediately affect gameplay. The Algorithm Lab calls the same services as gameplay rather than using detached demonstrations.",
            body,
        ),
        Spacer(1, 6),
        table(
            [
                ["Layer", "Responsibilities"],
                [
                    "Model",
                    "Graph, track, edge, vertex, event, racer, result, and championship records",
                ],
                [
                    "Algorithms",
                    "BFS, DFS, Dijkstra, A*, DP, Greedy, Backtracking, Kruskal, heaps, sorting",
                ],
                [
                    "Services",
                    "Validation, cost model, route planning, event scheduling, race simulation, scoring",
                ],
                ["UI", "Five screens for menu, explorer, race, lab, and dashboard"],
            ],
            [3.3 * cm, 13.0 * cm],
        ),
        PageBreak(),
    ]
    story += [
        Paragraph("3. Data Models, Assumptions, and Rules", styles["Heading1"]),
        Paragraph(
            "Each circuit is G=(V,E) with adjacency lists. Vertex records store coordinates, type, checkpoint order, and service availability. Edge records store distance, base time, fuel cost, difficulty, status, shortcut flag, direction, and independent temporary effects. The validator checks checkpoint count/order, shortcuts, cycles, dead ends, reachability, and numeric invariants before a track is playable.",
            body,
        ),
        Paragraph(
            "Route cost is a non-negative normalized scalar combining distance, effective time, fuel, difficulty, and obstacle penalty. Balanced, Speed, Economy, and Safety presets use different documented weights. The same cost is displayed to the player and optimized by Dijkstra/A*.",
            body,
        ),
        Paragraph(
            "The implementation freezes 100 fuel units, a 40-unit station purchase cap, a 3-second positive-purchase stop, three nitro charges, two laps, and a 600-second race limit. Event ordering is (triggerTime, priority, insertionSequence). Finished ties use racer ID; unfinished racers are ranked by completed laps, checkpoints, elapsed time, and racer ID.",
            body,
        ),
        Paragraph("4. Algorithm Design and Integration", styles["Heading1"]),
        table(
            [
                ["Algorithm", "Functional role", "Complexity"],
                ["BFS", "Reachability and minimum-edge route", "O(V+E)"],
                [
                    "DFS",
                    "Traversal, cycle, components, dead ends, bounded alternatives",
                    "O(V+E) traversal",
                ],
                ["Dijkstra", "Optimal weighted route with non-negative cost", "O((V+E) log V)"],
                ["A*", "Heuristic-guided optimal route", "Worst case comparable to Dijkstra"],
                ["DP", "0/1 pickup and refuelling planning", "Pseudo-polynomial"],
                ["Greedy", "Benefit/cost pickup heuristic", "O(m log m)"],
                ["Backtracking", "Constraint-based placement", "Exponential worst case"],
                ["Kruskal", "Undirected MST backbone", "O(E log E)"],
                ["Heap", "Race events and top-k retrieval", "O(log n) update/extract"],
                ["Merge/Quick/Heap Sort", "Championship rankings", "See algorithm documentation"],
            ],
            [3.5 * cm, 9.5 * cm, 3.3 * cm],
        ),
        PageBreak(),
    ]
    story += [
        Paragraph("5. Gameplay Integration", styles["Heading1"]),
        Paragraph(
            "During planning, BFS and DFS explore graph structure; Dijkstra and A* plan checkpoint-aware route legs; DP and Greedy recommend pickup/refuelling decisions. During racing, the event heap applies closures and temporary restrictions, the graph is updated in place, and each affected racer recalculates from its current state. Opponents follow fixed strategies and share fuel, checkpoint, route, and recovery rules with the player.",
            body,
        ),
        Paragraph(
            "The championship dashboard aggregates race results and applies one total comparator to Merge Sort, Quick Sort, Heap Sort, and heap-based top-k retrieval. The complete rankings must match exactly across methods.",
            body,
        ),
        Paragraph("6. Testing Strategy", styles["Heading1"]),
        Paragraph(
            "Automated tests cover empty/singleton/disconnected/cyclic/branching/dead-end graphs; source-equals-target and unreachable routing; blocked and zero-weight edges; fuel and capacity limits; unavailable stations; zero-cost items; event ties, cancellations, expirations, and overlapping effects; duplicate-heavy sorting; and complete deterministic races.",
            body,
        ),
        Paragraph(
            "A deterministic replay test runs the same track twice and compares finish order and times. Each race uses a fresh deep-copied graph so service state and collected pickups cannot leak between races.",
            body,
        ),
        Paragraph("7. Experimental Studies", styles["Heading1"]),
        Paragraph(
            "The experiment runner uses two warm-up calls and five timed repetitions, excludes rendering and file I/O from timed sections, stores raw CSV data, and generates charts. The seed and environment metadata are written with the measurements.",
            body,
        ),
    ]
    for title, filename in [
        ("Experiment 1 - BFS and DFS", "experiment_1_bfs_dfs.csv"),
        ("Experiment 2 - Dijkstra and A*", "experiment_2_dijkstra_astar.csv"),
        ("Experiment 3 - DP and Greedy", "experiment_3_dp_greedy.csv"),
        ("Experiment 4 - Event Heap", "experiment_4_event_heap.csv"),
        ("Experiment 5 - Sorting and Top-k", "experiment_5_sorting_topk.csv"),
    ]:
        rows = read_rows(filename)
        summary = (
            f"{len(rows)} measured rows are available in experiments/data/{filename}."
            if rows
            else "Run run_experiments.py to populate this study's raw measurements."
        )
        story += [Paragraph(title, styles["Heading2"]), Paragraph(summary, body)]
    story += [
        PageBreak(),
        Paragraph("8. Limitations, Advanced Challenges, and Future Work", styles["Heading1"]),
        Paragraph(
            "The current build uses procedurally drawn graphics and deterministic JSON circuits rather than an asset-heavy production game. The live Pygame UI is intentionally compact so the algorithm state remains readable. The scalar route cost is useful for a single optimizer but cannot represent every Pareto-optimal trade-off between time, fuel, safety, and obstacles; changing weights can change the selected route.",
            body,
        ),
        Paragraph(
            "The implementation includes the MST/backtracking generation foundations and live top-k analytics. Future work could add richer track generation controls, a full visual step-by-step animation for every algorithm, sound/assets, and a multi-objective Pareto-front planner.",
            body,
        ),
        Paragraph("9. Conclusion", styles["Heading1"]),
        Paragraph(
            "Smart Racing Championship integrates the required algorithm families into a functioning, testable, and reproducible racing system. The project demonstrates graph modelling, shortest-path optimality, heuristic search, pseudo-polynomial resource planning, deterministic priority queues, constrained generation, sorting, top-k retrieval, complexity analysis, and empirical comparison in one coherent application.",
            body,
        ),
        Paragraph(
            "References and acknowledgements: Python standard library, pygame-ce, matplotlib, pytest, and the supplied Smart Racing Championship project specification.",
            body,
        ),
    ]
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Smart Racing Technical Report",
        author="Smart Racing Championship",
    )
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(OUTPUT)


if __name__ == "__main__":
    build()
