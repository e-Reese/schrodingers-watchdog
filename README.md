# Watchdogd Development Environment Launcher v2.0
Automate live-install bootstraps, keep development environments ready, or standardize enterprise terminals with a repeatable service stack. This GUI orchestrates services, monitors health, and automatically restarts crashed services.

## Features
- Add/edit/remove services at runtime
- Support executable, npm/pnpm, and PowerShell targets
- Auto-restart with crash logging
- Startup ordering and delays
- JSON configuration stored per user
- Optional browser auto-launch

## Install & Run
```bash
pip install -r requirements.txt
python watchdogd-launcher.py
```
## Build (PyInstaller)
```bash
pyinstaller watchdogd-launcher.spec
```
Executable output: `dist/Watchdogd-Launcher`.
## Configuration
- User config: `%USERPROFILE%\.watchdogd_launcher\config.json`
- Logs: `%USERPROFILE%\.watchdogd_launcher\logs\`
- Example config and notes: `config/`

## Managing Services
Use **Manage Services** to add, edit, duplicate, reorder, toggle, and save services. Each service supports command, workspace, args, startup delay, restart policy, custom environment variables (`${VAR_NAME}` syntax), and optional browser profile isolation.

## Structure
```
watchdogd_launcher/
├── main.py
├── config_manager.py
├── service_manager.py
├── service_definitions.py
├── gui/
│   ├── main_window.py
│   ├── settings_dialog.py
│   └── service_editor.py
└── utils/
    ├── logger.py
    └── process_utils.py
```
## License
GPL-2.0-only
