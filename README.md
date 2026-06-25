# Things 3 Progress TUI

![screenshot](https://raw.githubusercontent.com/danielh-official/things-3-progress-tui/refs/heads/main/screenshot.png)

Are you:

- Technical & Terminal-Savvy?
- On Mac?
- A fan and user of Things 3 by Cultured Code?
- Want progress bars for not only your Things projects, but each heading within each project?

Then this TUI is for you!

## Install

**Note**: This app is macOS-only and requires Things 3 to be installed.

Install from PyPI:

```bash
pip install things-3-progress-tui
```

or Homebrew:

```bash
brew install danielh-official/tap/things-3-progress-tui
```

## How To Use

Activate in Terminal with:

```bash
things-progress
```

## Developing

To get started, clone and run the app in your terminal emulator of choice (I recommend [Ghostty](https://github.com/ghostty-org/ghostty)):

```bash
.venv/bin/textual run --dev app.py
```

For live reloading, you can use `ptw` (pytest-watch) to watch for changes and run the app:

```bash
ptw --runner "textual run --dev app.py"
```
