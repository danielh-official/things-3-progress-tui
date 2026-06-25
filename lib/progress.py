"""Horizontal progress bar renderer (pure, no Textual)."""
from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

BAR_W = 36       # detail / overall bar width in cells
SIDE_BAR_W = 18  # compact sidebar bar


def render_bar(ratio, label="", width=BAR_W):
    """Rich Text: optional dim label line, then a filled/empty bar + percent."""
    filled = round(ratio * width)
    text = Text()
    if label:
        text.append(label + "\n", style="dim")
    text.append("█" * filled, style="green")
    text.append("░" * (width - filled), style="grey37")
    text.append(f" {round(ratio * 100)}%", style="bold")
    return text

class ProgressDisplay(Static):
    """A horizontal progress bar with optional label."""
    DEFAULT_CSS = "ProgressDisplay { width: auto; height: auto; }"

    def __init__(self, ratio=0.0, label="", width=BAR_W):
        super().__init__()
        self._ratio, self._label, self._width = ratio, label, width

    def render(self):
        return render_bar(self._ratio, self._label, self._width)
