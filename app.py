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
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Static

from data import fetch_by_uuid, fetch_project, things_url
from radial import H, SIDE_H, SIDE_W, W, render_radial
from storage import load_pinned, save_pinned


class RadialProgress(Static):
    DEFAULT_CSS = "RadialProgress { width: auto; height: auto; content-align: center middle; }"

    def __init__(self, progress=0.0, label="", w=W, h=H):
        super().__init__()
        self._progress, self._label, self._w, self._h = progress, label, w, h

    def render(self):
        return render_radial(self._progress, self._label, self._w, self._h)


class ProjectItem(ListItem):
    """Sidebar entry: compact radial + title, carries the project uuid."""

    def __init__(self, uuid, title, ratio, done, total):
        super().__init__()
        self.uuid = uuid
        self.proj_title = title
        self._ratio, self._done, self._total = ratio, done, total

    def compose(self) -> ComposeResult:
        yield RadialProgress(self._ratio, "", SIDE_W, SIDE_H)
        yield Static(f"{self.proj_title}\n{self._done}/{self._total}", classes="side-title")


class ThingsApp(App):
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
        self.refresh_sidebar()

    def action_refresh(self) -> None:
        """Re-fetch sidebar radials and the open detail view from Things."""
        self.refresh_sidebar()
        if self._current_uuid:
            self.open_project(self._current_uuid)

    # -- sidebar -------------------------------------------------------
    @work(thread=True, exclusive=True, group="sidebar")
    def refresh_sidebar(self) -> None:
        items = []
        changed = False
        for f in self._pinned:
            try:
                title, _, overall = fetch_by_uuid(f["uuid"])  # live title from Things
            except Exception:  # noqa: BLE001 - skip projects that vanished
                continue
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
        if isinstance(event.item, ProjectItem):
            self.open_project(event.item.uuid)

    # -- search --------------------------------------------------------
    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if name:
            self.query_one("#msg", Static).update("Searching…")
            self.do_search(name)

    @work(thread=True, exclusive=True, group="search")
    def do_search(self, name: str) -> None:
        try:
            uuid, title, buckets, overall = fetch_project(name)
        except Exception as e:  # noqa: BLE001 - surface fetch error to UI
            self.call_from_thread(self._show_error, str(e))
            return
        self.call_from_thread(self._show_detail, uuid, title, buckets, overall)

    # -- detail --------------------------------------------------------
    @work(thread=True, exclusive=True, group="detail")
    def open_project(self, uuid: str) -> None:
        try:
            title, buckets, overall = fetch_by_uuid(uuid)
        except Exception as e:  # noqa: BLE001
            self.call_from_thread(self._show_error, str(e))
            return
        self.call_from_thread(self._show_detail, uuid, title, buckets, overall)

    def _show_detail(self, uuid, title, buckets, overall) -> None:
        self._current_uuid = uuid
        self._current_title = title
        self.query_one("#msg", Static).update("")
        results = self.query_one("#results", VerticalScroll)
        results.remove_children()
        results.mount(
            Static(
                render_radial(overall["ratio"], f"{title} ({overall['done']}/{overall['total']})"),
                classes="project-radial",
            )
        )
        for b in buckets:
            results.mount(
                RadialProgress(b["ratio"], f"{b['title']} {b['done']}/{b['total']}").add_class("section-radial")
            )
        pinned = any(f["uuid"] == uuid for f in self._pinned)
        results.mount(Button(self._pin_label(pinned), classes="pin-toggle"))
        results.mount(Button("↗ Open in Things 3", classes="open-things", variant="primary"))

    @staticmethod
    def _pin_label(pinned: bool) -> str:
        return "★ Unpin" if pinned else "☆ Pin to sidebar"

    def on_button_pressed(self, event: Button.Pressed) -> None:
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
