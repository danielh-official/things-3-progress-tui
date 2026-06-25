"""
Populate the sidebar ListView with project items.
"""
from typing import TYPE_CHECKING, Any, Dict, List, Tuple
from textual.widgets import ListView
from lib.project import ProjectItem

if TYPE_CHECKING:
    from app import ThingsApp

def populate_sidebar(app: "ThingsApp", items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
    """Populate the sidebar ListView with the given project items."""
    lv = app.query_one("#sidebar", ListView)
    lv.clear()
    for uuid, title, ov in items:
        lv.append(ProjectItem(uuid, title, ov["ratio"], ov["done"], ov["total"]))
