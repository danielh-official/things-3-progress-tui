"""
It is used to update the user interface with the latest data from Things.
"""
from typing import TYPE_CHECKING

from lib.open_project import open_project
from lib.refresh import refresh_sidebar

if TYPE_CHECKING:
    from app import ThingsApp

def action_refresh(app: "ThingsApp") -> None:
    """Re-fetch sidebar items and the open detail view from Things."""
    refresh_sidebar(app)
    if app.current_uuid:
        open_project(app, app.current_uuid)
