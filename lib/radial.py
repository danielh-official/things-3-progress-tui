"""ASCII circular progress ring renderer (pure, no Textual)."""
from __future__ import annotations

import math

from rich.text import Text

# Grid geometry. Cells are ~2:1 (tall), so x is scaled to keep the ring round.
W, H = 21, 11            # full detail ring
SIDE_W, SIDE_H = 13, 7   # compact sidebar ring
_OUTER, _INNER = 1.0, 0.62  # normalized ring band


def ring_cell(col, row, progress, w=W, h=H):
    """Return 'filled' | 'empty' | None (None = not part of the ring band)."""
    cx, cy = (w - 1) / 2, (h - 1) / 2
    nx = (col - cx) / cx * 0.5  # halve x to correct char aspect ratio
    ny = (row - cy) / cy
    dist = math.hypot(nx, ny)
    if not (_INNER <= dist <= _OUTER):
        return None
    angle = math.atan2(nx, -ny) % (2 * math.pi)  # 0 at top, clockwise
    frac = angle / (2 * math.pi)
    return "filled" if frac < progress else "empty"


def render_radial(progress, label, w=W, h=H):
    """Build a Rich renderable (Text) of the ring with centered % and label."""
    pct = f"{round(progress * 100)}%"
    text = Text()
    mid = h // 2
    for row in range(h):
        # Center two rows hold the percentage and the label.
        if row == mid:
            text.append(pct.center(w) + "\n", style="bold")
            continue
        if row == mid + 1 and label:
            text.append(label[:w].center(w) + "\n", style="dim")
            continue
        for col in range(w):
            state = ring_cell(col, row, progress, w, h)
            if state == "filled":
                text.append("●", style="green")
            elif state == "empty":
                text.append("·", style="grey37")
            else:
                text.append(" ")
        text.append("\n")
    return text
