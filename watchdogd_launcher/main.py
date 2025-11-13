"""Main entry point for Watchdogd Launcher application (PyQt)."""

from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from .config_manager import ConfigManager
from .gui.main_window import MainWindow
from .gui.theme import apply_dark_theme


def main() -> None:
    """Start the PyQt application."""
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_theme(app)

    config_manager = ConfigManager()
    window = MainWindow(config_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

