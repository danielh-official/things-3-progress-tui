"""
ProjectItem: sidebar entry for a project, with compact progress bar and title.
"""
from typing import TYPE_CHECKING
from textual import work

from lib.data import fetch_by_uuid
from lib.detail import show_detail

if TYPE_CHECKING:
    from app import ThingsApp

@work(thread=True, exclusive=True, group="detail")
def open_project(app: "ThingsApp", uuid: str) -> None:
    """Fetch the project by UUID and show its detail view."""
    title, buckets, overall = fetch_by_uuid(uuid)
    app.call_from_thread(show_detail, app, uuid, title, buckets, overall)
