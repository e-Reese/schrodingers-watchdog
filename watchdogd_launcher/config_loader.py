from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .core import AppDefinition

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "apps.json"


@dataclass(slots=True)
class AppConfig:
    apps: List[AppDefinition]
    poll_interval: float = 5.0


def _default_payload() -> dict:
    return {
        "poll_interval_seconds": 5,
        "applications": [
            {
                "name": "TextEdit",
                "launch_target": "/System/Applications/TextEdit.app",
                "process_match": "TextEdit",
                "auto_start": True,
                "args": [],
            }
        ],
    }


def ensure_default_config(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_default_payload(), indent=2))


def _parse_app(entry: dict) -> AppDefinition:
    return AppDefinition(
        name=entry["name"],
        launch_target=entry["launch_target"],
        process_match=entry.get("process_match") or entry["name"],
        auto_start=bool(entry.get("auto_start", True)),
        args=list(entry.get("args", [])),
    )


def load_app_config(path: str | Path | None = None, ensure_default: bool = True) -> AppConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if ensure_default:
        ensure_default_config(config_path)

    data = json.loads(config_path.read_text())
    apps_payload: Sequence[dict] = data.get("applications", [])
    apps: Iterable[AppDefinition] = (_parse_app(entry) for entry in apps_payload)
    poll_interval = float(data.get("poll_interval_seconds", 5))
    return AppConfig(apps=list(apps), poll_interval=poll_interval)
