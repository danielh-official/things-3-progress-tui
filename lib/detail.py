"""
Updates the detail view of the application with project data.
"""
from typing import TYPE_CHECKING, Dict, List

from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Rule, Static

from lib.progress import render_bar, ProgressDisplay
from lib.pin import pin_label

if TYPE_CHECKING:
    from app import ThingsApp

def show_detail(
    app: "ThingsApp",
    uuid: str,
    title: str,
    buckets: List[Dict[str, int]],
    overall: Dict[str, int],
) -> None:
    """Update the detail view with the project data."""
    app.current_uuid = uuid
    app.current_title = title
    app.query_one("#msg", Static).update("")
    results = app.query_one("#results", VerticalScroll)
    results.remove_children()
    results.mount(
        Static(
            render_bar(overall["ratio"], f"{title} ({overall['done']}/{overall['total']})"),
            classes="project-bar",
        )
    )
    results.mount(Rule())
    for b in buckets:
        results.mount(
            ProgressDisplay(b["ratio"], f"{b['title']} {b['done']}/{b['total']}")
                .add_class("section-bar")
        )
    pinned = any(f["uuid"] == uuid for f in app.pinned)
    results.mount(
        Horizontal(
            Button(pin_label(pinned), classes="pin-toggle"),
            Button("↗ Open in Things 3", classes="open-things", variant="primary"),
            classes="actions",
        )
    )
