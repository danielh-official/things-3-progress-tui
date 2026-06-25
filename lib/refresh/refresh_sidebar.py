"""
This module contains functions to refresh the sidebar and populate it with project items.
"""
from typing import TYPE_CHECKING

from textual import work

from lib.data import fetch_by_uuid
from lib.refresh.populate_sidebar import populate_sidebar
from lib.storage import save_pinned

if TYPE_CHECKING:
    from app import ThingsApp

@work(thread=True, exclusive=True, group="sidebar")
def refresh_sidebar(app: "ThingsApp") -> None:
    """Re-fetch pinned projects from Things and update the sidebar."""
    items = []
    changed = False
    for f in app.pinned:
        title, _, overall = fetch_by_uuid(f["uuid"])  # live title from Things
        if title != f["title"]:  # title renamed in Things -> persist it
            f["title"] = title
            changed = True
        items.append((f["uuid"], title, overall))
    if changed:
        save_pinned(app.pinned)
    app.call_from_thread(populate_sidebar, app, items)
