"""Utilities for managing Windows run-on-startup integration."""

from __future__ import annotations

import os
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
        return os.name == "nt"

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def is_enabled(self) -> bool:
        """Check whether the registry entry currently exists."""
        if not self.is_supported():
            return False

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, self.value_name)
                return True
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------
    def enable(self) -> None:
        """Create/update the Run entry for this app."""
        if not self.is_supported():
            raise OSError("Run on startup is only supported on Windows.")

        command = self._build_command()
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY) as key:
            winreg.SetValueEx(key, self.value_name, 0, winreg.REG_SZ, command)

    def disable(self) -> None:
        """Remove the Run entry if it exists."""
        if not self.is_supported():
            return

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, self.value_name)
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

