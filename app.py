"""Things 3 project progress TUI.

Type a project name -> fetch its headings + to-dos from the Things DB (via
things.py) -> show a circular progress radial for the project and one per heading.

AppleScript can't do this: its dictionary has no heading class, so to-dos can't
be grouped by heading. We read the Things SQLite DB through things.py instead.

Run `python app.py` to launch the TUI (`textual run app.py` also works).
Run `python app.py test` for the self-checks (no Things/Textual needed).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

# Pinned projects persist here, next to the script. List of {"uuid", "title"}.
_STORE = Path(__file__).parent / "pinned.json"


def load_pinned():
    try:
        return json.loads(_STORE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_pinned(items):
    _STORE.write_text(json.dumps(items, indent=2))

# ---------------------------------------------------------------------------
# Data layer (pure where possible)
# ---------------------------------------------------------------------------

NO_HEADING = "Root"  # bucket for to-dos with no heading


def group_todos(todos, headings=None):
    """Bucket to-dos by heading title and compute completion ratios.

    Pure function: takes lists of things.py-style dicts, returns
    (heading_buckets, overall). A bucket is {title, done, total, ratio}.
    `status == 'completed'` counts as done; `'canceled'` is excluded from total.
    Empty headings (passed in `headings`) appear with total 0.
    """
    buckets = {}  # title -> {"done": int, "total": int}
    order = []  # preserve first-seen order; "No heading" forced first

    def bucket(title):
        if title not in buckets:
            buckets[title] = {"done": 0, "total": 0}
            order.append(title)
        return buckets[title]

    bucket(NO_HEADING)  # always exists, shown first
    for h in headings or []:
        bucket(h.get("title") or h.get("heading_title") or NO_HEADING)

    for t in todos:
        if t.get("status") == "canceled":
            continue
        b = bucket(t.get("heading_title") or NO_HEADING)
        b["total"] += 1
        if t.get("status") == "completed":
            b["done"] += 1

    # Drop the "No heading" bucket if it ended up empty and other headings exist.
    if buckets[NO_HEADING]["total"] == 0 and len(order) > 1:
        order.remove(NO_HEADING)
        del buckets[NO_HEADING]

    out = []
    done_sum = total_sum = 0
    for title in order:
        d, tot = buckets[title]["done"], buckets[title]["total"]
        done_sum += d
        total_sum += tot
        out.append({"title": title, "done": d, "total": tot, "ratio": _ratio(d, tot)})

    overall = {"done": done_sum, "total": total_sum, "ratio": _ratio(done_sum, total_sum)}
    return out, overall


def _ratio(done, total):
    return done / total if total else 0.0


def _progress_for(uuid):
    """Grouped progress for a project uuid -> (buckets, overall)."""
    import things  # imported here so the self-check runs without Things installed

    todos = things.todos(project=uuid, status=None)  # status=None -> include completed/canceled
    try:
        headings = things.tasks(type="heading", project=uuid)
    except Exception:
        headings = []
    return group_todos(todos, headings)


def fetch_project(name):
    """Look up a project by name in Things and return its grouped progress.

    Returns (uuid, title, heading_buckets, overall). Raises ValueError with a
    friendly message if not found / DB unreadable.
    """
    import things

    name_l = name.strip().lower()
    matches = [p for p in things.projects() if p.get("title", "").lower() == name_l]
    if not matches:
        # fall back to substring match for convenience
        matches = [p for p in things.projects() if name_l in p.get("title", "").lower()]
    if not matches:
        raise ValueError(f"No project matching {name!r}.")

    proj = matches[0]
    buckets, overall = _progress_for(proj["uuid"])
    return proj["uuid"], proj["title"], buckets, overall


def fetch_by_uuid(uuid):
    """Grouped progress for a known project uuid -> (title, buckets, overall)."""
    import things

    proj = things.get(uuid)
    if not proj:
        raise ValueError(f"Project {uuid!r} not found in Things.")
    buckets, overall = _progress_for(uuid)
    return proj.get("title", uuid), buckets, overall


def things_url(uuid):
    """Things 3 URL scheme link that opens the project in the app."""
    return f"things:///show?id={uuid}"


# ---------------------------------------------------------------------------
# Radial widget
# ---------------------------------------------------------------------------

# Grid geometry. Cells are ~2:1 (tall), so x is scaled to keep the ring round.
_W, _H = 21, 11
_CX, _CY = (_W - 1) / 2, (_H - 1) / 2
_OUTER, _INNER = 1.0, 0.62  # normalized ring band


def _ring_cell(col, row, progress, w=_W, h=_H):
    """Return 'filled' | 'empty' | None (None = not part of the ring band)."""
    cx, cy = (w - 1) / 2, (h - 1) / 2
    nx = (col - cx) / cx * 0.5  # halve x to correct char aspect ratio
    ny = (row - cy) / cy
    dist = math.hypot(nx, ny)
    if not (_INNER <= dist <= _OUTER):
        return None
    angle = math.atan2(nx, -ny) % (2 * math.pi)  # 0 at top, clockwise
    frac = angle / (2 * math.pi)
    return "filled" if frac < progress else "empty"


def _render_radial(progress, label, w=_W, h=_H):
    """Build a Rich renderable (Text) of the ring with centered % and label."""
    from rich.text import Text

    pct = f"{round(progress * 100)}%"
    text = Text()
    mid = h // 2
    for row in range(h):
        # Center two rows hold the percentage and the label.
        if row == mid:
            text.append(pct.center(w) + "\n", style="bold")
            continue
        if row == mid + 1 and label:
            text.append(label[:w].center(w) + "\n", style="dim")
            continue
        for col in range(w):
            state = _ring_cell(col, row, progress, w, h)
            if state == "filled":
                text.append("●", style="green")
            elif state == "empty":
                text.append("·", style="grey37")
            else:
                text.append(" ")
        text.append("\n")
    return text


try:  # Textual is optional for the self-check
    import subprocess

    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, VerticalScroll
    from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Button
    from textual import work

    _SIDE_W, _SIDE_H = 13, 7  # compact radial for the sidebar

    class RadialProgress(Static):
        DEFAULT_CSS = "RadialProgress { width: auto; height: auto; content-align: center middle; }"

        def __init__(self, progress=0.0, label="", w=_W, h=_H):
            super().__init__()
            self._progress, self._label, self._w, self._h = progress, label, w, h

        def render(self):
            return _render_radial(self._progress, self._label, self._w, self._h)

    class ProjectItem(ListItem):
        """Sidebar entry: compact radial + title, carries the project uuid."""

        def __init__(self, uuid, title, ratio, done, total):
            super().__init__()
            self.uuid = uuid
            self.proj_title = title
            self._ratio, self._done, self._total = ratio, done, total

        def compose(self) -> ComposeResult:
            yield RadialProgress(self._ratio, "", _SIDE_W, _SIDE_H)
            yield Static(f"{self.proj_title}\n{self._done}/{self._total}", classes="side-title")

    class ThingsApp(App):
        # ctrl+q quits (priority so it fires even with the Input focused). ctrl+c
        # keeps Textual's default toast pointing here ("Press ctrl+q to quit").
        BINDINGS = [Binding("ctrl+q", "quit", "Quit", priority=True)]
        CSS = """
        #body { height: 1fr; }
        #sidebar { width: 36; border-right: solid $panel; }
        ProjectItem { height: auto; padding: 1 0; }
        .side-title { text-align: center; }
        #refresh { width: 100%; }
        #results { padding: 1 2; }
        #msg { color: $warning; padding: 0 2; }
        .project-radial { width: 100%; height: auto; align: center middle; }
        .section-radial { width: 100%; height: auto; align: center middle; }
        .pin-toggle { margin: 1 2 0 2; }
        .open-things { margin: 1 2; }
        """
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
                    _render_radial(overall["ratio"], f"{title} ({overall['done']}/{overall['total']})"),
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

except ImportError:  # Textual not installed -> only the data layer is usable
    RadialProgress = None
    ThingsApp = None


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def _selfcheck():
    todos = [
        {"status": "completed", "heading_title": "Design"},
        {"status": "incomplete", "heading_title": "Design"},
        {"status": "canceled", "heading_title": "Design"},  # excluded from total
        {"status": "completed", "heading_title": None},  # -> "No heading"
        {"status": "completed", "heading_title": "Ship"},
    ]
    headings = [{"title": "Empty"}]  # heading with no todos
    buckets, overall = group_todos(todos, headings)
    by = {b["title"]: b for b in buckets}

    assert by["Design"]["done"] == 1 and by["Design"]["total"] == 2, by["Design"]
    assert by["Design"]["ratio"] == 0.5
    assert by[NO_HEADING]["done"] == 1 and by[NO_HEADING]["total"] == 1
    assert by["Ship"]["ratio"] == 1.0
    assert by["Empty"]["total"] == 0 and by["Empty"]["ratio"] == 0.0
    # overall: done = Design1 + None1 + Ship1 = 3; total = 2+1+1 = 4
    assert overall["done"] == 3 and overall["total"] == 4, overall
    assert overall["ratio"] == 0.75

    # canceled-only / empty project -> ratio 0, no crash
    _, ov2 = group_todos([{"status": "canceled", "heading_title": None}], [])
    assert ov2 == {"done": 0, "total": 0, "ratio": 0.0}, ov2

    # Radial fill extremes.
    full = [_ring_cell(c, r, 1.0) for r in range(_H) for c in range(_W)]
    none = [_ring_cell(c, r, 0.0) for r in range(_H) for c in range(_W)]
    ring = [x for x in full if x is not None]
    assert ring and all(x == "filled" for x in ring), "progress=1.0 must fill ring"
    ring0 = [x for x in none if x is not None]
    assert ring0 and all(x == "empty" for x in ring0), "progress=0.0 must empty ring"

    # Compact (sidebar) radial geometry still forms a ring and fills fully.
    cw, ch = 13, 7
    comp = [_ring_cell(c, r, 1.0, cw, ch) for r in range(ch) for c in range(cw)]
    cring = [x for x in comp if x is not None]
    assert cring and all(x == "filled" for x in cring), "compact ring must fill"

    assert things_url("ABC123") == "things:///show?id=ABC123"

    print("self-check OK")


if __name__ == "__main__":
    import sys

    if "test" in sys.argv[1:]:
        _selfcheck()
    elif ThingsApp is None:
        sys.exit("Textual not installed. Run: pip install -r requirements.txt")
    else:
        ThingsApp().run()
