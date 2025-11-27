"""Utilities for managing run-on-startup integration (Windows and macOS)."""

from __future__ import annotations

import os
import platform
import plistlib
import sys
from pathlib import Path

if os.name == "nt":  # pragma: no cover - Windows-only module
    import winreg
else:  # pragma: no cover - Windows-only module
    winreg = None  # type: ignore[assignment]


class StartupManager:
    """Helper to create/remove the HKCU Run entry for the launcher."""

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "WatchdogdLauncher"

    def __init__(self, value_name: str | None = None) -> None:
        self.value_name = value_name or self.VALUE_NAME

    # ------------------------------------------------------------------
    # Platform helpers
    # ------------------------------------------------------------------
    @staticmethod
    def is_supported() -> bool:
        """Return True when run-on-startup integration is available."""
        return os.name == "nt" or platform.system() == "Darwin"

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def is_enabled(self) -> bool:
        """Check whether the startup entry currently exists."""
        if not self.is_supported():
            return False

        if os.name == "nt":
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_READ
                ) as key:
                    winreg.QueryValueEx(key, self.value_name)
                    return True
            except OSError:
                return False
        elif platform.system() == "Darwin":
            plist_path = self._get_macos_plist_path()
            return plist_path.exists()
        
        return False

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------
    def enable(self) -> None:
        """Create/update the startup entry for this app."""
        if not self.is_supported():
            raise OSError("Run on startup is only supported on Windows and macOS.")

        if os.name == "nt":
            command = self._build_command()
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY) as key:
                winreg.SetValueEx(key, self.value_name, 0, winreg.REG_SZ, command)
        elif platform.system() == "Darwin":
            self._create_macos_launch_agent()

    def disable(self) -> None:
        """Remove the startup entry if it exists."""
        if not self.is_supported():
            return

        if os.name == "nt":
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.DeleteValue(key, self.value_name)
            except FileNotFoundError:
                pass
        elif platform.system() == "Darwin":
            plist_path = self._get_macos_plist_path()
            try:
                plist_path.unlink()
            except FileNotFoundError:
                pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_command(self) -> str:
        """Return the command string that launches this app."""
        executable = Path(sys.executable).resolve()
        if getattr(sys, "frozen", False):
            # PyInstaller build – executable already wraps the app.
            return f'"{executable}"'

        script_path = Path(sys.argv[0]).resolve()
        if script_path.suffix.lower() in {".py", ".pyw"}:
            return f'"{executable}" "{script_path}"'

        return f'"{script_path}"'

    def _get_macos_plist_path(self) -> Path:
        """Return the path to the LaunchAgent plist file on macOS."""
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        return launch_agents_dir / "com.watchdogd-launcher.plist"

    def _create_macos_launch_agent(self) -> None:
        """Create a LaunchAgent plist file for macOS."""
        plist_path = self._get_macos_plist_path()
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        executable = Path(sys.executable).resolve()
        if getattr(sys, "frozen", False):
            # PyInstaller build - use the app bundle or executable
            program_args = [str(executable)]
        else:
            # Running from source
            script_path = Path(sys.argv[0]).resolve()
            program_args = [str(executable), str(script_path)]

        plist_data = {
            "Label": "com.watchdogd-launcher",
            "ProgramArguments": program_args,
            "RunAtLoad": True,
            "KeepAlive": False,
        }

        with open(plist_path, "wb") as f:
            plistlib.dump(plist_data, f)

