# Danrode Commander 0.1.0

Full GUI rewrite of Danrode Commander (formerly DCMDS) using **PySide6**.
This is a GUI redesign only — every backend command, plugin, and config
format from the original terminal version remains compatible.

## Design

Minimal, glassmorphism, dark-mode, Apple/Windows-11 inspired. The main
window shows exactly four things:

1. Title — "Danrode Commander"
2. Status — "Ready"
3. One large **All Commands** button (opens a searchable command palette)
4. A command input bar at the bottom

No sidebar, no ribbon, no toolbar.

## Running

```bash
pip install -r requirements.txt
python main.py
```

## Architecture

```
DanrodeCommander/
  main.py                 # tiny entry point
  core/
    command_manager.py    # central dispatcher + app state
    config.py              # config.json compatibility
    history.py             # history.log compatibility
    logger.py               # in-memory + file logger
    plugin_manager.py       # legacy plugin loader
    dpa_engine.py            # .dpa XOR+Base64 encryption engine
    result.py                # CommandResult data contract
  gui/
    main_window.py         # top-level window (title/status/button/input)
    command_dialog.py       # "All Commands" search palette
    command_input.py         # bottom input, history, autocomplete
    status_bar.py             # bottom status strip
    output_panel.py            # renders CommandResult objects
    confirm_dialog.py          # confirmation for destructive actions
    glass_panel.py               # reusable rounded/shadowed panel
    animations.py                 # fade / scale helpers
    theme.py                       # QSS + color tokens
  commands/
    filesystem.py    wifi/tasks -> system_info.py
    power.py          dpa_cmd.py   camera_cmd.py   calc_cmd.py
  plugins/            # legacy-compatible plugin drop folder
  themes/             # dark.json (active), light.json (reserved)
  config/             # config.json (auto-created on first run)
  history/            # history.log + dcmds.log (auto-created)
  tests/
```

## Compatibility notes

- `config.json` keys (`safe_mode`, `theme`, `history_enabled`,
  `history_max`, `history_path`, `dpa_key`) are unchanged.
- `history.log` remains a plain newline-separated command log.
- `.dpa` file format (`#DPA-XOR2` / `#DPA-PLAIN` headers, XOR+Base64 body)
  is byte-for-byte compatible with the original DCMDS encoder/decoder.
- Plugins keep the exact same API: a `.py` file in `plugins/` exposing
  `register(register_command)`.

## Not part of 0.1.0

File Explorer, Plugin Store, Theme Editor, Package Manager, AI Assistant,
and Terminal Tabs are intentionally out of scope. The architecture (small
files, clear core/gui/commands separation) is built so these can be added
later without a GUI rewrite.
