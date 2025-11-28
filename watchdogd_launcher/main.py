from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from .config_loader import load_app_config
from .core import WatchdogController
from .gui.main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch and monitor macOS applications via a PyQt watchdog.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to the JSON config that defines managed applications.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_app_config(path=args.config)
    qt_app = QApplication(sys.argv)

    controller = WatchdogController(config.apps, poll_interval=config.poll_interval)
    window = MainWindow(controller, config)
    window.show()

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
