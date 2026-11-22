from __future__ import annotations

import arcade

NAVY = (11, 18, 32)
PANEL = (24, 38, 59)
PANEL_DARK = (12, 22, 38)
CYAN = (56, 189, 248)
EMERALD = (45, 212, 160)
AMBER = (251, 191, 36)
CORAL = (248, 113, 113)
WHITE = (241, 245, 249)
MUTED = (169, 184, 204)
PURPLE = (167, 139, 250)


def rgba(color: tuple[int, int, int], alpha: int = 255) -> tuple[int, int, int, int]:
    return (*color, alpha)


def button_style(
    fill: tuple[int, int, int],
    text: tuple[int, int, int] = NAVY,
    border: tuple[int, int, int] | None = None,
    font_size: int = 15,
) -> dict:
    """Return the versioned Arcade 3.x UIFlatButton style map."""

    outline = border or fill
    return {
        "normal": arcade.gui.UIFlatButton.UIStyle(
            font_size=font_size,
            font_name=("Aptos Display", "Arial"),
            font_color=rgba(text),
            bg=rgba(fill),
            border=rgba(outline),
            border_width=1,
        ),
        "hover": arcade.gui.UIFlatButton.UIStyle(
            font_size=font_size,
            font_name=("Aptos Display", "Arial"),
            font_color=rgba(WHITE),
            bg=rgba(fill if fill != NAVY else (28, 57, 83)),
            border=rgba(CYAN),
            border_width=2,
        ),
        "press": arcade.gui.UIFlatButton.UIStyle(
            font_size=font_size,
            font_name=("Aptos Display", "Arial"),
            font_color=rgba(NAVY),
            bg=rgba(WHITE),
            border=rgba(CYAN),
            border_width=2,
        ),
        "disabled": arcade.gui.UIFlatButton.UIStyle(
            font_size=font_size,
            font_name=("Aptos Display", "Arial"),
            font_color=rgba(MUTED),
            bg=rgba((42, 54, 70)),
            border=rgba((66, 82, 101)),
            border_width=1,
        ),
    }
