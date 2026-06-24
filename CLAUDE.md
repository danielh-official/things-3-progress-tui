# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

There is no system `python` on this machine — use the venv interpreter directly.

```bash
.venv/bin/python app.py        # launch the TUI
.venv/bin/python test_data.py  # run the self-check (no Things/Textual needed)
.venv/bin/textual run --dev app.py   # live CSS hot-reload (needs textual-dev)
```

`textual run app.py` also launches the TUI. Dependencies (`requirements.txt`): `textual`, `things.py`.

## Testing

Tests live in `test_data.py` (`test()`) and run via `python test_data.py`. Plain `assert`s, no framework — it imports only the pure layers (`data.py`, `radial.py`), so it runs without Textual or a Things database. When adding non-trivial logic, extend `test()` rather than introducing a test framework.

For UI behavior, drive the app headless with Textual's `run_test()` / `Pilot` (stub `fetch_project`/`fetch_by_uuid` and point `app._STORE` at a tmp file to avoid touching the real DB or `pinned.json`).

## Architecture

Flat modules, separated by concern so the pure layers import without Textual:

- **`data.py`** — Things data layer: `group_todos` buckets to-dos by heading and computes ratios; `_progress_for` / `fetch_project` / `fetch_by_uuid` pull from Things; `things_url`.
- **`radial.py`** — pure ASCII ring renderer: `ring_cell` / `render_radial` + geometry constants.
- **`storage.py`** — `pinned.json` persistence: `load_pinned` / `save_pinned`.
- **`app.py`** — Textual UI only: `ThingsApp`, `RadialProgress`, `ProjectItem`. Imports the three above explicitly.
- **`test_data.py`** — self-check over `data.py` + `radial.py`.

Keep the pure/UI boundary: anything that doesn't need Textual goes in `data`/`radial`/`storage` so it stays testable headless. `app.py` is the only module that imports `textual`.

Key facts that aren't obvious from reading one module:

- **Data source.** Reads the Things 3 SQLite DB through the `things.py` library, *not* AppleScript — AppleScript's dictionary has no heading class, so to-dos can't be grouped by heading. `things.todos(...)` defaults to `status='incomplete'`; pass `status=None` to include completed/canceled, otherwise `done` counts are always 0.
- **Heading buckets.** `NO_HEADING = "Root"` is the bucket for to-dos with no heading; it's forced first and dropped only if empty when other headings exist. `canceled` to-dos are excluded from totals; `completed` count as done.
- **Radial widget.** `ring_cell`/`render_radial` take `w,h` so the same renderer draws the full detail ring (`W,H = 21,11`) and the compact sidebar ring (`SIDE_W,SIDE_H = 13,7`). The x-axis is halved to correct for ~2:1 terminal cell aspect.
- **Persistence.** Pinned projects are stored as `pinned.json` beside `storage.py`, a list of `{"uuid","title"}`. Search and pin are separate actions: searching only shows a project; the detail view's toggle button pins/unpins it. `refresh_sidebar` re-fetches live titles from Things and rewrites `pinned.json` when a title changed.
- **Threading.** DB fetches run in `@work(thread=True, exclusive=True)` workers (grouped `sidebar`/`search`/`detail`); they update the UI via `self.call_from_thread(...)`.
- **macOS only.** Things 3 is macOS/iOS. The "Open in Things 3" button shells out to `open things:///show?id=<uuid>` (Things URL scheme via `things_url`).

## Textual gotchas (learned here)

- **Never reuse a fixed `id` on a widget that gets remounted.** `remove_children()` is async and isn't awaited, so a rapid re-render can mount the new widget before the old one is gone → `DuplicateIds`. Use a `class` and match on it instead. This bit us on the headings grid and the Things/pin buttons.
- **Quit.** `ctrl+q` is bound to `quit` with `priority=True` so it fires even when the `Input` is focused. `ctrl+c` is left to Textual's default, which shows a "Press ctrl+q to quit" toast (`action_help_quit` scans for a binding whose action is literally `"quit"`).
- **`cmd+r` and similar can't reach a terminal TUI** — refresh is a button, not a keybinding.
