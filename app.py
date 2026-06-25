"""Things 3 project progress TUI.
"""
from __future__ import annotations

import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, ListView, Static

from lib.refresh.action_refresh import action_refresh
from lib.data import things_url
from lib.open_project import open_project
from lib.pin import pin_label
from lib.refresh.refresh_sidebar import refresh_sidebar
from lib.search import do_search
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
        self.pinned = load_pinned()  # [{"uuid","title"}]
        self.current_uuid: str | None = None
        self.current_title: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("⟳ Refresh all", id="refresh", variant="primary")
        yield Input(placeholder="Project name… (Enter to search)", id="search")
        yield Static("", id="msg")
        with Horizontal(id="body"):
            yield ListView(id="sidebar")
            yield VerticalScroll(id="results")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the sidebar with pinned projects on startup."""
        refresh_sidebar(self)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle sidebar selection: open the project detail view for the selected project."""
        if isinstance(event.item, ProjectItem):
            open_project(self, event.item.uuid)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission: fetch the project by name and show its detail view."""
        name = event.value.strip()
        if name:
            self.query_one("#msg", Static).update("Searching…")
            do_search(self, name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for refresh, open in Things, and pin/unpin actions."""
        if event.button.id == "refresh":
            action_refresh(self)
            return
        if not self.current_uuid:
            return
        if event.button.has_class("open-things"):
            subprocess.run(["open", things_url(self.current_uuid)], check=False)
        elif event.button.has_class("pin-toggle"):
            pinned = any(f["uuid"] == self.current_uuid for f in self.pinned)
            if pinned:
                self.pinned = [f for f in self.pinned if f["uuid"] != self.current_uuid]
            else:
                self.pinned.append({"uuid": self.current_uuid, "title": self.current_title})
            save_pinned(self.pinned)
            refresh_sidebar(self)
            event.button.label = pin_label(not pinned)

    def _show_error(self, msg: str) -> None:
        self.query_one("#msg", Static).update(msg)


if __name__ == "__main__":
    ThingsApp().run()
