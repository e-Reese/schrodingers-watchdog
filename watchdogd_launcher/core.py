from __future__ import annotations

import enum
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal


class AppStatus(enum.Enum):
    """Possible runtime states for a managed application."""

    UNKNOWN = "Unknown"
    RUNNING = "Running"
    STOPPED = "Stopped"
    STARTING = "Starting"
    STOPPING = "Stopping"
    ERROR = "Error"


@dataclass(slots=True)
class AppDefinition:
    """Configuration for one managed macOS application."""

    name: str
    launch_target: str
    process_match: str
    auto_start: bool = True
    args: List[str] = field(default_factory=list)

    def build_launch_command(self) -> List[str]:
        """
        Build the `open` command used to launch the target.

        Supported launch targets:
        - Absolute or relative path to an .app bundle
        - High level application name resolvable by `open -a`
        - Bundle identifiers prefixed with `bundle:`
        """
        cmd = ["open"]

        if self.launch_target.startswith("bundle:"):
            bundle_id = self.launch_target.split(":", 1)[1]
            cmd.extend(["-b", bundle_id])
        else:
            path = Path(self.launch_target).expanduser()
            cmd.extend(["-a", str(path)])

        if self.args:
            cmd.append("--args")
            cmd.extend(self.args)

        return cmd

    def describe(self) -> str:
        """Return a short human readable description."""
        args = " ".join(shlex.quote(arg) for arg in self.args)
        base = f"{self.name} -> {self.launch_target}"
        return f"{base} {args}".strip()


class WatchdogController(QObject):
    """
    Coordinates process monitoring and lifecycle management.
    """

    status_changed = pyqtSignal(str, AppStatus)
    log_event = pyqtSignal(str)

    def __init__(self, apps: Iterable[AppDefinition], poll_interval: float = 5.0) -> None:
        super().__init__()
        self.apps: Dict[str, AppDefinition] = {app.name: app for app in apps}
        self.status: Dict[str, AppStatus] = {name: AppStatus.UNKNOWN for name in self.apps}
        self.poll_interval = poll_interval

    def _log(self, message: str) -> None:
        self.log_event.emit(message)

    def _update_status(self, name: str, status: AppStatus) -> None:
        if self.status.get(name) == status:
            return
        self.status[name] = status
        self.status_changed.emit(name, status)

    def _lookup_app(self, name: str) -> Optional[AppDefinition]:
        return self.apps.get(name)

    def iter_apps(self) -> Iterable[AppDefinition]:
        return self.apps.values()

    def get_status(self, name: str) -> AppStatus:
        return self.status.get(name, AppStatus.UNKNOWN)

    def start_autorun_apps(self) -> None:
        for app in self.apps.values():
            if not app.auto_start:
                continue
            self.start_app(app.name)

    def start_app(self, name: str) -> bool:
        app = self._lookup_app(name)
        if not app:
            self._log(f"Unknown app: {name}")
            return False

        command = app.build_launch_command()
        try:
            subprocess.Popen(command)
            self._log(f"Launching {app.describe()}")
            self._update_status(name, AppStatus.STARTING)
            return True
        except OSError as exc:
            self._log(f"Failed to launch {name}: {exc}")
            self._update_status(name, AppStatus.ERROR)
            return False

    def stop_app(self, name: str) -> bool:
        app = self._lookup_app(name)
        if not app:
            self._log(f"Unknown app: {name}")
            return False

        self._update_status(name, AppStatus.STOPPING)
        script = f'tell application "{app.process_match}" to quit'

        script_result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )

        if script_result.returncode == 0:
            self._log(f"Requested {name} to quit via AppleScript")
            return True

        # Fall back to pkill if AppleScript fails
        kill_result = subprocess.run(
            ["pkill", "-f", app.process_match],
            capture_output=True,
            text=True,
            check=False,
        )

        if kill_result.returncode == 0:
            self._log(f"Force quitting {name} via pkill")
            return True

        self._log(f"Unable to stop {name}: {script_result.stderr or kill_result.stderr}")
        self._update_status(name, AppStatus.ERROR)
        return False

    def refresh_status(self) -> None:
        for name, app in self.apps.items():
            status = self._detect_status(app)
            self._update_status(name, status)

    def _detect_status(self, app: AppDefinition) -> AppStatus:
        try:
            result = subprocess.run(
                ["pgrep", "-if", app.process_match],
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            self._log(f"pgrep unavailable when checking {app.name}: {exc}")
            return AppStatus.ERROR

        return AppStatus.RUNNING if result.returncode == 0 else AppStatus.STOPPED
