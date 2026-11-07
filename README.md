# MacroFlow — Automation Studio v0.3.1 (UI Redesign)

Windows desktop automation with an editable step sequence, recording and local scenarios. This update rebuilds the **real desktop UI**, not a static mockup. Based on MacroFlow's previously supplied **v0.2.2** source branch.

## UI 3.1

- Custom **frameless** window: dark title bar with working minimize, maximize/restore, close, drag and Windows edge resize.
- A unified design system across **five screens**: scenarios, macro editor, recording, tools and settings.
- All important icons are SVG vector graphics (rendered by QtSvg), not emoji/font glyphs.
- Interactive states: hover, pressed, selected, checked, disabled; orange highlights remain visible on every screen.
- Branded graphite/orange sidebar, separated navigation tiles and quick actions.
- Macro editor: steps as cards with vector pictograms, drag-and-drop ordering, list/compact view, context menu, delays and action inspector.
- Editor toolbar: save, undo, redo, copy step, delete step. Undo history is maintained for the active scenario (up to 60 changes in memory).
- Repeat settings: once / N cycles / indefinitely; pauses between steps and cycles in milliseconds.
- Resizable execution panel: start/pause F6, record F7, stop F8, step F9; collapsible timestamped log.
- Scenario context menu, import and export `.mflow`, templates and tool shortcuts.
- Application icon: graphite background + orange M.

## Which functions are actually available?

The original execution engine is preserved. **Working actions:** click, double click, ASCII text input, press key, delay. Recording collects mouse clicks and selected service keys. Scenario repeat and `.mflow` interchange are working in the original codebase.

**Not implemented yet:** OCR, UI Automation element selection, smart window lookup, counterparty search in 1C, Cyrillic text typing, automatic *installation* of updates (only checking for updates is implemented). The interface does not pretend those actions already work.

## Run on Windows

Use Python **3.12** (recommended for the release workflow):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe main.py
```

You can also run `python main.py` if your selected Python has the necessary packages.

## Install into an existing local repository

1. Stop MacroFlow. Back up the repository directory and `%APPDATA%\MacroFlow\scenarios.json`.
2. Extract the ZIP **contents** into the repository directory beside `main.py`, merging `macroflow/`, `assets/`, `tests/`, `installer/` and `.github/`.
3. Run the tests and application directly with Python; verify the interface, scenario lists, hotkeys, record/stop and a harmless test macro.
4. Publish from PowerShell after confirming locally:

```powershell
git add .
git commit -m "MacroFlow v0.3.1 — vector UI redesign"
git push origin main
git tag v0.3.1
git push origin v0.3.1
```

The tag initiates the GitHub Actions Windows installer build; successful builds publish the release. **Do not push the tag before testing.** The archive contains no `.git` metadata and does not change user scenarios in `%APPDATA%`.

> If your installed source already contains unpublished functionality from a later v0.3.0 branch, do not overwrite it without reviewing the diff. This redesign is based on the last supplied source, which was v0.2.x. The screenshot marked v0.3.0 was used as the visual reference, not as actual source code.

## Data / safety

Before performing high-volume operations in 1C, test a script on a non-production database and verify results step by step. Mouse targets still use screen coordinates. F8 attempts to stop execution; PyAutoGUI also has a mouse-to-corner failsafe. Never store login details or passwords in shared macro files.

## Tests

Local static compilation and store/exchange tests can run on any Python installation. Qt GUI and execution-engine tests require PySide6 and are run by GitHub Actions on Windows using the offscreen Qt backend. This package was not GUI-render-tested in the authoring container because PySide6 was unavailable there.

### One-command UI upgrade (PowerShell)

Instead of manually copying folders, extract this ZIP anywhere and run **from inside the extracted folder**:

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY-TO-PROJECT.ps1 -ProjectPath "D:\GitHub\MacroFlow-v0.1.0-source-fixed\MacroFlow"
```

This verifies the target directory, backs up current UI files and (if present) `scenarios.json` under `_backups`, and copies the new source while leaving `.git` untouched. `_backups/` is excluded from Git. After that, run the tests and `python main.py` in your project folder. If your local version contains newer business logic than v0.2.2, inspect the replacement source before applying.
