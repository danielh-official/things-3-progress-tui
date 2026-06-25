"""Things 3 project progress TUI.

Type a project name -> fetch its headings + to-dos from the Things DB (via
things.py) -> show a circular progress radial for the project and one per heading.

Run `python app.py` to launch (`textual run app.py` also works).
Pure logic lives in data.py / radial.py; tests in test_data.py.
"""
from __future__ import annotations

import subprocess

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, ListView, Rule, Static

from lib.data import fetch_by_uuid, fetch_project, things_url
from lib.progress import render_bar, ProgressDisplay
from lib.storage import load_pinned, save_pinned
from lib.project import ProjectItem


class ThingsApp(App):
    """Textual TUI for Things 3 project progress."""
    # ctrl+q quits (priority so it fires even with the Input focused). ctrl+c
    # keeps Textual's default toast pointing here ("Press ctrl+q to quit").
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", priority=True)]
    CSS_PATH = "app.tcss"  # external for live hot-reload: textual run --dev app.py
    TITLE = "Things Project Progress"

    def __init__(self):
        super().__init__()
        self._pinned = load_pinned()  # [{"uuid","title"}]
        self._current_uuid = None
        self._current_title = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("⟳ Refresh all", id="refresh")
        yield Input(placeholder="Project name… (Enter to search)", id="search")
        yield Static("", id="msg")
        with Horizontal(id="body"):
            yield ListView(id="sidebar")
            yield VerticalScroll(id="results")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the sidebar with pinned projects on startup."""
        self.refresh_sidebar()

    def action_refresh(self) -> None:
        """Re-fetch sidebar radials and the open detail view from Things."""
        self.refresh_sidebar()
        if self._current_uuid:
            self.open_project(self._current_uuid)

    # -- sidebar -------------------------------------------------------
    @work(thread=True, exclusive=True, group="sidebar")
    def refresh_sidebar(self) -> None:
        """Re-fetch pinned projects from Things and update the sidebar."""
        items = []
        changed = False
        for f in self._pinned:
            title, _, overall = fetch_by_uuid(f["uuid"])  # live title from Things
            if title != f["title"]:  # title renamed in Things -> persist it
                f["title"] = title
                changed = True
            items.append((f["uuid"], title, overall))
        if changed:
            save_pinned(self._pinned)
        self.call_from_thread(self._populate_sidebar, items)

    def _populate_sidebar(self, items) -> None:
        lv = self.query_one("#sidebar", ListView)
        lv.clear()
        for uuid, title, ov in items:
            lv.append(ProjectItem(uuid, title, ov["ratio"], ov["done"], ov["total"]))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle sidebar selection: open the project detail view for the selected project."""
        if isinstance(event.item, ProjectItem):
            self.open_project(event.item.uuid)

    # -- search --------------------------------------------------------
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission: fetch the project by name and show its detail view."""
        name = event.value.strip()
        if name:
            self.query_one("#msg", Static).update("Searching…")
            self.do_search(name)

    @work(thread=True, exclusive=True, group="search")
    def do_search(self, name: str) -> None:
        """Fetch the project by name and show its detail view."""
        uuid, title, buckets, overall = fetch_project(name)
        self.call_from_thread(self._show_detail, uuid, title, buckets, overall)

    # -- detail --------------------------------------------------------
    @work(thread=True, exclusive=True, group="detail")
    def open_project(self, uuid: str) -> None:
        """Fetch the project by UUID and show its detail view."""
        title, buckets, overall = fetch_by_uuid(uuid)
        self.call_from_thread(self._show_detail, uuid, title, buckets, overall)

    def _show_detail(self, uuid, title, buckets, overall) -> None:
        """Update the detail view with the project data."""
        self._current_uuid = uuid
        self._current_title = title
        self.query_one("#msg", Static).update("")
        results = self.query_one("#results", VerticalScroll)
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
        pinned = any(f["uuid"] == uuid for f in self._pinned)
        results.mount(
            Horizontal(
                Button(self._pin_label(pinned), classes="pin-toggle"),
                Button("↗ Open in Things 3", classes="open-things", variant="primary"),
                classes="actions",
            )
        )

    @staticmethod
    def _pin_label(pinned: bool) -> str:
        """Return the label for the pin/unpin button based on whether the project is pinned."""
        return "★ Unpin" if pinned else "☆ Pin to sidebar"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for refresh, open in Things, and pin/unpin actions."""
        if event.button.id == "refresh":
            self.action_refresh()
            return
        if not self._current_uuid:
            return
        if event.button.has_class("open-things"):
            subprocess.run(["open", things_url(self._current_uuid)], check=False)
        elif event.button.has_class("pin-toggle"):
            pinned = any(f["uuid"] == self._current_uuid for f in self._pinned)
            if pinned:
                self._pinned = [f for f in self._pinned if f["uuid"] != self._current_uuid]
            else:
                self._pinned.append({"uuid": self._current_uuid, "title": self._current_title})
            save_pinned(self._pinned)
            self.refresh_sidebar()
            event.button.label = self._pin_label(not pinned)

    def _show_error(self, msg: str) -> None:
        self.query_one("#msg", Static).update(msg)


if __name__ == "__main__":
    ThingsApp().run()
