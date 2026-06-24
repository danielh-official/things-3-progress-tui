# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

There is no system `python` on this machine — use the venv interpreter directly.

```bash
.venv/bin/python app.py        # launch the TUI
.venv/bin/python test_data.py  # run the self-check (no Things/Textual needed)
.venv/bin/textual run --dev app.py   # live CSS hot-reload (needs textual-dev)
```

`textual run app.py` also launches the TUI. Dependencies (`requirements.txt`): `textual`, `things.py`, `textual-dev` (`rich` comes in via `textual`).

## Testing

Tests live in `test_data.py` (`test()`) and run via `python test_data.py`. Plain `assert`s, no framework — it imports only the pure layers (`lib/data.py`, `lib/progress.py`), so it runs without Textual or a Things database. When adding non-trivial logic, extend `test()` rather than introducing a test framework.

For UI behavior, drive the app headless with Textual's `run_test()` / `Pilot`. Stub `app.fetch_project` / `app.fetch_by_uuid` (they're imported into the `app` namespace) and point `lib.storage.STORE` at a tmp file to avoid touching the real DB or `pinned.json`. Note: thread workers need a few `await pilot.pause()` + `asyncio.sleep` cycles to land, and `pilot.press("enter")` on a programmatically-set `Input` can be flaky — calling the worker method directly (e.g. `app.do_search("x")`) is more reliable in tests.

## Architecture

`app.py` + `app.tcss` live at the repo root; the modules it depends on are the `lib/` package:

- **`lib/data.py`** — Things data layer: `group_todos` buckets to-dos by heading and computes ratios; `_progress_for` / `fetch_project` / `fetch_by_uuid` pull from Things; `things_url`.
- **`lib/progress.py`** — pure horizontal bar renderer: `render_bar` + `BAR_W` / `SIDE_BAR_W` widths.
- **`lib/storage.py`** — `pinned.json` persistence (the file lives in `lib/`, beside `storage.py`): `load_pinned` / `save_pinned`.
- **`app.py`** — Textual UI only: `ThingsApp`, `ProgressDisplay` (Static wrapping `render_bar`), `ProjectItem`. Imports `lib.*` explicitly.
- **`test_data.py`** — self-check over `lib/data.py` + `lib/progress.py`.

Keep the pure/UI boundary: anything that doesn't need Textual goes in `lib/` so it stays testable headless. `app.py` is the only module that imports `textual`.

Key facts that aren't obvious from reading one module:

- **Data source.** Reads the Things 3 SQLite DB through the `things.py` library, *not* AppleScript — AppleScript's dictionary has no heading class, so to-dos can't be grouped by heading. `things.todos(...)` defaults to `status='incomplete'`; pass `status=None` to include completed/canceled, otherwise `done` counts are always 0.
- **Heading buckets.** `NO_HEADING = "Root"` is the bucket for to-dos with no heading; it's forced first and dropped only if empty when other headings exist. `canceled` to-dos are excluded from totals; `completed` count as done.
- **Progress bar.** `render_bar(ratio, label, width)` returns Rich `Text` (optional dim label line + filled/empty bar + percent). `BAR_W` is the detail width, `SIDE_BAR_W` the compact sidebar width. Wrapped by the `ProgressDisplay` Static widget in `app.py`.
- **Persistence.** Pinned projects are stored as `lib/pinned.json` (beside `storage.py`), a list of `{"uuid","title"}`. Search and pin are separate actions: searching only shows a project; the detail view's toggle button pins/unpins it. `refresh_sidebar` re-fetches live titles from Things and rewrites `pinned.json` when a title changed.
- **Threading.** DB fetches run in `@work(thread=True, exclusive=True)` workers (grouped `sidebar`/`search`/`detail`); they update the UI via `self.call_from_thread(...)`.
- **macOS only.** Things 3 is macOS/iOS. The "Open in Things 3" button shells out to `open things:///show?id=<uuid>` (Things URL scheme via `things_url`).

## Textual gotchas (learned here)

- **Never reuse a fixed `id` on a widget that gets remounted.** The detail view (`_show_detail`) calls `results.remove_children()` then mounts fresh widgets on every search/select/refresh. `remove_children()` is async and isn't awaited, so a rapid re-render can mount the new widget before the old one is gone → `DuplicateIds`. Use a `class` and match on it (e.g. `has_class("open-things")`) instead of an `id`.
- **Quit.** `ctrl+q` is bound to `quit` with `priority=True` so it fires even when the `Input` is focused. `ctrl+c` is left to Textual's default, which shows a "Press ctrl+q to quit" toast (`action_help_quit` scans for a binding whose action is literally `"quit"`).
- **`cmd+r` and similar can't reach a terminal TUI** — refresh is a button, not a keybinding.
