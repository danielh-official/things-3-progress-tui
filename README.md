# Things 3 Progress TUI

![screenshot](https://github.com/danielh-official/things-3-progress-tui/blob/main/screenshot.png)

Are you:

- Technical & Terminal-Savvy?
- On Mac?
- A fan and user of Things 3 by Cultured Code?
- Want progress bars for not only your Things projects, but each heading within each project?

Then this TUI is for you!

## Install

Install from PyPI:

```bash
pip install things-3-progress-tui
things-progress
```

> [!NOTE]
> This app is macOS-only and requires Things 3 to be installed.

## Developing

To get started, clone and run the app in your terminal emulator of choice (I recommend [Ghostty](https://github.com/ghostty-org/ghostty)):

```bash
.venv/bin/textual run --dev app.py
```

For live reloading, you can use `ptw` (pytest-watch) to watch for changes and run the app:

```bash
ptw --runner "textual run --dev app.py"
```
