"""
ProjectItem: sidebar entry for a project, with compact progress bar and title.
"""
from textual.app import ComposeResult
from textual.widgets import ListItem, Static

from lib.progress import SIDE_BAR_W, ProgressDisplay

class ProjectItem(ListItem):
    """Sidebar entry: compact progress bar + title, carries the project uuid."""

    def __init__(self, uuid, title, overview):
        super().__init__()
        self.uuid = uuid
        self.proj_title = title
        self._ratio = overview["ratio"]
        self._done = overview["done"]
        self._total = overview["total"]

    def compose(self) -> ComposeResult:
        yield Static(f"{self.proj_title} ({self._done}/{self._total})", classes="side-title")
        yield ProgressDisplay(self._ratio, "", SIDE_BAR_W)
