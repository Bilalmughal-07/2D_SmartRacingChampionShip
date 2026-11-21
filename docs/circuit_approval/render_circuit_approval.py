"""Render standalone circuit proposals for approval.

This module deliberately does not import the game or write active track JSON files.
It produces visual design artefacts only, so the circuits can be reviewed before
integration into Smart Racing Championship.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

OUT = Path(__file__).resolve().parent

BG = "#061523"
PANEL = "#0b2131"
TEXT = "#f1f7ff"
MUTED = "#a8bfd2"
ROAD = "#eaf4ff"
SHORTCUT = "#cf7bff"
CHECKPOINT = "#ffd524"
START = "#22d982"
FUEL = "#19b9f1"
NITRO = "#e83e88"
JUNCTION = "#cad8e5"


DESIGNS = {
    "emerald_loop": {
        "title": "Circuit 1 — Emerald Loop",
        "subtitle": "Readable outer loop with safe inner connectors and service spurs",
        "accent": "#19e58e",
        "difficulty": "EASY / ONBOARDING",
        "notes": [
            "10 ordered checkpoints",
            "2 visible shortcuts",
            "Loop + alternative inner route",
            "Fuel stations embedded in the live loop",
        ],
        "positions": {
            "S": (-5.3, 2.8), "1": (-3.4, 4.1), "2": (-0.5, 4.2),
            "3": (2.5, 4.0), "4": (4.8, 2.3), "5": (4.8, -0.7),
            "6": (2.5, -2.8), "7": (-0.5, -3.0), "8": (-3.4, -2.7),
            "9": (-5.0, -0.6), "10": (-5.1, 1.2), "J1": (-2.5, 2.1),
            "J2": (0.4, 2.0), "J3": (-1.2, -0.2), "J4": (1.7, -0.3),
            "F1": (-5.1, 0.3), "F2": (4.8, 0.8), "N1": (-2.3, -1.45),
            "N2": (1.45, 3.0),
        },
        "normal": [
            ("S", "1"), ("1", "2"), ("2", "3"), ("3", "4"), ("4", "F2"),
            ("F2", "5"), ("5", "6"), ("6", "7"), ("7", "8"), ("8", "9"),
            ("9", "F1"), ("F1", "10"),
            ("10", "S"), ("1", "J1"), ("J1", "J3"), ("J3", "J4"),
            ("J4", "5"), ("J2", "J4"), ("J1", "J2"), ("8", "N1"),
            ("N1", "J3"),
        ],
        "shortcuts": [("S", "J1"), ("J2", "N2"), ("N2", "3")],
        "resources": {"F1": ("fuel", "10"), "F2": ("fuel", "5"),
                      "N1": ("nitro", "8"), "N2": ("nitro", "3")},
    },
    "canyon_switchbacks": {
        "title": "Circuit 2 — Canyon Switchbacks",
        "subtitle": "Serpentine ridge route with high-payoff, high-risk crossover shortcuts",
        "accent": "#ffb51d",
        "difficulty": "MEDIUM / STRATEGY",
        "notes": [
            "10 ordered checkpoints",
            "2 visible shortcuts",
            "Long switchbacks create trade-offs",
            "Four refuel opportunities",
        ],
        "positions": {
            "S": (-5.2, 2.8), "1": (-3.7, 4.0), "2": (-0.8, 4.2),
            "3": (2.4, 3.8), "4": (4.8, 2.0), "5": (4.3, -0.7),
            "6": (1.8, -2.6), "7": (-1.0, -2.5), "8": (-3.7, -1.5),
            "9": (-5.0, 0.1), "10": (-5.2, 1.5), "J1": (-3.0, 2.0),
            "J2": (-0.4, 2.4), "J3": (0.0, 0.0), "J4": (2.3, 1.0),
            "J5": (0.9, -0.2), "F1": (-2.25, 4.1), "F2": (4.55, 0.65),
            "F3": (0.4, -3.3), "F4": (-5.1, 0.8), "N1": (-2.35, -2.0),
            "N2": (2.2, 2.2),
        },
        "normal": [
            ("S", "10"), ("10", "F4"), ("F4", "9"), ("9", "8"), ("8", "N1"),
            ("N1", "7"), ("7", "F3"), ("F3", "6"), ("6", "5"), ("5", "F2"),
            ("F2", "4"), ("4", "3"), ("3", "2"), ("2", "F1"), ("F1", "1"),
            ("1", "S"), ("10", "J1"), ("J1", "J2"), ("J2", "3"),
            ("J1", "J3"), ("J3", "J4"), ("J4", "5"), ("J3", "J5"),
            ("J5", "7"), ("4", "J4"),
        ],
        "shortcuts": [("S", "J1"), ("J2", "N2"), ("N2", "4")],
        "resources": {"F1": ("fuel", "2"), "F2": ("fuel", "5"),
                      "F3": ("fuel", "7"), "F4": ("fuel", "10"),
                      "N1": ("nitro", "8"), "N2": ("nitro", "4")},
    },
    "metro_grid": {
        "title": "Circuit 3 — Metro Grid",
        "subtitle": "Dense urban grid with intersections, directed corridors, and diagonal escapes",
        "accent": "#b57cff",
        "difficulty": "HARD / TECHNICAL",
        "notes": [
            "10 ordered checkpoints",
            "2 visible one-way shortcuts",
            "Grid intersections and diagonals",
            "Best for closure rerouting",
        ],
        "positions": {
            "S": (-4.7, 3.8), "1": (-1.9, 3.8), "2": (0.9, 3.8),
            "3": (3.7, 3.8), "4": (3.7, 1.3), "5": (3.7, -1.3),
            "6": (0.9, -1.3), "7": (-1.9, -1.3), "8": (-1.9, -3.8),
            "9": (0.9, -3.8), "10": (3.7, -3.8), "J1": (-4.7, 1.3),
            "J2": (-1.9, 1.3), "J3": (0.9, 1.3), "J4": (-4.7, -1.3),
            "F1": (-4.7, 0.0), "F2": (2.3, -3.8), "N1": (-1.9, 0.0),
            "N2": (0.9, -2.55),
        },
        "normal": [
            ("S", "1"), ("1", "2"), ("2", "3"), ("3", "4"), ("4", "5"),
            ("5", "6"), ("6", "7"), ("7", "8"), ("8", "9"), ("9", "10"),
            ("10", "8"), ("S", "J1"), ("J1", "J2"), ("J2", "J3"),
            ("J3", "6"), ("J1", "F1"), ("F1", "J4"), ("J4", "10"),
            ("1", "J2"), ("2", "J3"), ("7", "N1"), ("N1", "J2"),
            ("8", "J4"),
            ("9", "F2"), ("F2", "10"),
        ],
        "shortcuts": [("S", "J2"), ("7", "N2"), ("N2", "10")],
        "resources": {"F1": ("fuel", "J1"), "F2": ("fuel", "9"),
                      "N1": ("nitro", "7"), "N2": ("nitro", "10")},
    },
}


def _draw_edge(ax, positions, a, b, *, shortcut=False):
    x1, y1 = positions[a]
    x2, y2 = positions[b]
    ax.plot(
        [x1, x2], [y1, y2],
        color=SHORTCUT if shortcut else ROAD,
        linewidth=3.0 if shortcut else 2.2,
        linestyle=(0, (8, 5)) if shortcut else "-",
        alpha=0.98,
        zorder=1,
    )
    if shortcut:
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops={"arrowstyle": "-|>", "color": SHORTCUT, "lw": 1.4},
            zorder=2,
        )


def _draw_marker(ax, label, xy, color, shape="circle", size=0.34):
    x, y = xy
    if shape == "square":
        patch = Rectangle((x - size, y - size), 2 * size, 2 * size,
                          facecolor=color, edgecolor=TEXT, linewidth=1.6, zorder=5)
        ax.add_patch(patch)
    else:
        patch = Circle((x, y), size, facecolor=color, edgecolor=TEXT, linewidth=1.6, zorder=5)
        ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center", color="#071522",
            fontsize=10, fontweight="bold", zorder=6)


def draw_design(key: str, path: Path) -> None:
    design = DESIGNS[key]
    fig = plt.figure(figsize=(16, 10), facecolor=BG)
    gs = fig.add_gridspec(1, 2, width_ratios=[2.15, 0.85], wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    panel = fig.add_subplot(gs[0, 1])
    ax.set_facecolor(BG)
    panel.set_facecolor(PANEL)

    pos = design["positions"]
    for edge in design["normal"]:
        _draw_edge(ax, pos, *edge)
    for edge in design["shortcuts"]:
        _draw_edge(ax, pos, *edge, shortcut=True)
    for name, (x, y) in pos.items():
        if name == "S":
            _draw_marker(ax, "S/F", (x, y), START, size=0.38)
        elif name.startswith("F"):
            _draw_marker(ax, name, (x, y), FUEL, shape="square", size=0.30)
        elif name.startswith("N"):
            _draw_marker(ax, name, (x, y), NITRO, shape="square", size=0.30)
        elif name.startswith("J"):
            _draw_marker(ax, name, (x, y), JUNCTION, size=0.30)
        else:
            _draw_marker(ax, name, (x, y), CHECKPOINT, size=0.30)

    ax.set_xlim(-6.3, 5.8)
    ax.set_ylim(-4.8, 5.0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(-6.2, 5.0, design["title"], color=TEXT, fontsize=24, fontweight="bold", va="top")
    ax.text(-6.2, 4.56, design["subtitle"], color=MUTED, fontsize=12, va="top")
    ax.text(-6.2, -4.58, "White = normal road   •   Purple dashed = shortcut   •   Cyan/Pink markers are road vertices",
            color=MUTED, fontsize=10, va="bottom")

    panel.axis("off")
    panel.add_patch(FancyBboxPatch((0.05, 0.82), 0.90, 0.10, boxstyle="round,pad=0.02",
                                   facecolor=design["accent"], edgecolor=design["accent"], alpha=0.18))
    panel.text(0.10, 0.87, design["difficulty"], color=design["accent"], fontsize=12,
               fontweight="bold", va="center")
    panel.text(0.08, 0.75, "APPROVAL CHECKLIST", color=TEXT, fontsize=14, fontweight="bold")
    y = 0.69
    for note in design["notes"]:
        panel.text(0.10, y, "✓", color=design["accent"], fontsize=15, fontweight="bold", va="center")
        panel.text(0.18, y, note, color=TEXT, fontsize=11, va="center")
        y -= 0.075
    panel.text(0.08, 0.32, "LEGEND", color=TEXT, fontsize=14, fontweight="bold")
    legend = [(START, "S", "Start / finish"), (CHECKPOINT, "1–10", "Ordered checkpoints"),
              (JUNCTION, "J", "Intersection"), (FUEL, "F", "Fuel station"), (NITRO, "N", "Nitro pickup")]
    y = 0.26
    for color, label, description in legend:
        panel.add_patch(Circle((0.14, y), 0.025, transform=panel.transAxes, facecolor=color,
                               edgecolor=TEXT, linewidth=0.8))
        panel.text(0.14, y, label, transform=panel.transAxes, ha="center", va="center",
                   color="#071522", fontsize=7, fontweight="bold")
        panel.text(0.21, y, description, transform=panel.transAxes, color=MUTED, fontsize=10,
                   va="center")
        y -= 0.055
    panel.add_line(Line2D([0.08, 0.25], [0.02, 0.02], transform=panel.transAxes, color=SHORTCUT,
                          linestyle=(0, (6, 4)), linewidth=2.5))
    panel.text(0.30, 0.02, "shortcut", transform=panel.transAxes, color=MUTED, fontsize=10, va="center")

    fig.savefig(path, dpi=160, facecolor=BG, bbox_inches="tight")
    plt.close(fig)


def draw_board(path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(24, 10), facecolor=BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.12, wspace=0.04)
    for ax, (key, design) in zip(axes, DESIGNS.items()):
        ax.set_facecolor(BG)
        pos = design["positions"]
        for edge in design["normal"]:
            _draw_edge(ax, pos, *edge)
        for edge in design["shortcuts"]:
            _draw_edge(ax, pos, *edge, shortcut=True)
        for name, (x, y) in pos.items():
            if name == "S":
                _draw_marker(ax, "S/F", (x, y), START, size=0.34)
            elif name.startswith("F"):
                _draw_marker(ax, name, (x, y), FUEL, shape="square", size=0.27)
            elif name.startswith("N"):
                _draw_marker(ax, name, (x, y), NITRO, shape="square", size=0.27)
            elif name.startswith("J"):
                _draw_marker(ax, name, (x, y), JUNCTION, size=0.27)
            else:
                _draw_marker(ax, name, (x, y), CHECKPOINT, size=0.27)
        ax.set_xlim(-6.1, 5.5)
        ax.set_ylim(-4.6, 4.8)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(design["title"], color=design["accent"], fontsize=17, fontweight="bold", pad=10)
        ax.text(0.5, -0.06, design["difficulty"], transform=ax.transAxes, ha="center", color=MUTED, fontsize=10)
    fig.suptitle("SMART RACING CHAMPIONSHIP — Circuit Design Approval Board",
                 color=TEXT, fontsize=27, fontweight="bold", y=0.95)
    fig.text(0.5, 0.90, "Standalone proposals — not integrated into the project yet",
             ha="center", color=MUTED, fontsize=13)
    fig.text(0.5, 0.045, "White roads = normal routes   •   Purple dashed roads = shortcuts   •   Yellow = checkpoints   •   Cyan = fuel vertices   •   Pink = nitro vertices",
             ha="center", color=MUTED, fontsize=11)
    fig.savefig(path, dpi=160, facecolor=BG, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for key in DESIGNS:
        draw_design(key, OUT / f"{key}_practical_v2.png")
    draw_board(OUT / "circuit_design_approval_board_practical_v2.png")
    print(f"Rendered {len(DESIGNS) + 1} approval PNGs in {OUT}")
