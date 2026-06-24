"""Local persistence of pinned projects (pinned.json, beside this file)."""
from __future__ import annotations

import json
from pathlib import Path

STORE = Path(__file__).parent / "pinned.json"  # list of {"uuid", "title"}


def load_pinned():
    try:
        return json.loads(STORE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_pinned(items):
    STORE.write_text(json.dumps(items, indent=2))
