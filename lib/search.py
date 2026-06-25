"""Search for a project by name and show its detail view."""
from typing import TYPE_CHECKING

from textual import work

from lib.data import fetch_project
from lib.detail import show_detail

if TYPE_CHECKING:
    from app import ThingsApp

@work(thread=True, exclusive=True, group="search")
def do_search(app: "ThingsApp", name: str) -> None:
    """Fetch the project by name and show its detail view."""
    uuid, title, buckets, overall = fetch_project(name)
    app.call_from_thread(show_detail, app, uuid, title, buckets, overall)
