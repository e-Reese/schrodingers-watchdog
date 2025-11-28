## Schrodinger's Watchdog

PyQt-based watchdog UI that automates starting and supervising long-lived macOS applications. Designed to streamline preparing production machines by ensuring required apps launch (and stay running) with minimal interaction.

### Features
- JSON-driven application list with launch target, auto-start flag, and optional arguments.
- PyQt UI that displays current status, activity logs, and manual start/stop controls.
- Periodic health checks via `pgrep` plus graceful shutdown via AppleScript fallbacks.

### Requirements
- macOS with Python 3.11+ (earlier versions likely work but are untested).
- PyQt6 installed (`pip install PyQt6`).

### Configuration
Edit `config/apps.json` to add the bundle you want to manage:

```json
{
  "poll_interval_seconds": 10,
  "applications": [
    {
      "name": "OBS Studio",
      "launch_target": "/Applications/OBS.app",
      "process_match": "OBS",
      "auto_start": true,
      "args": ["--multi"]
    }
  ]
}
```

- `launch_target`: absolute path to the `.app` bundle or any value accepted by `open -a`. For bundle identifiers, prefix with `bundle:` (e.g., `"bundle:com.apple.Safari"`).
- `process_match`: substring passed to `pgrep -if` when determining whether the app is running.
- `auto_start`: start automatically when the UI launches.
- `args`: optional list appended after `open --args`.

### Running

```bash
pip install PyQt6
python -m watchdogd_launcher.main --config config/apps.json
```

The UI will present the managed app list, start auto-run entries, and monitor them at the configured interval. Use the buttons to manually start/stop any entry as needed.
