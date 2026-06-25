"""Local persistence of pinned projects in a user-writable data directory."""
from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "things-3-progress-tui"
APP_AUTHOR = "danielh-official"
LEGACY_STORE = Path(__file__).parent / "pinned.json"
STORE = Path(user_data_dir(APP_NAME, APP_AUTHOR)) / "pinned.json"


def load_pinned():
    """Load the list of pinned projects from the local JSON file."""
    try:
        return json.loads(STORE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        # Backward-compatibility for old installs that stored data in-package.
        try:
            return json.loads(LEGACY_STORE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return []


def save_pinned(items):
    """Save the list of pinned projects to the local JSON file."""
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(items, indent=2))
