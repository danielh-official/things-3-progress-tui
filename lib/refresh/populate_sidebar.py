"""
Populate the sidebar ListView with project items.
"""
from typing import TYPE_CHECKING, Any
from textual.widgets import ListView
from lib.project import ProjectItem

if TYPE_CHECKING:
    from app import ThingsApp

def populate_sidebar(app: "ThingsApp", items: list[tuple[str, str, dict[str, Any]]]) -> None:
    """Populate the sidebar ListView with the given project items."""
    lv = app.query_one("#sidebar", ListView)
    lv.clear()
    for uuid, title, ov in items:
        lv.append(ProjectItem(uuid, title, ov["ratio"], ov["done"], ov["total"]))
