"""
Watchdog launcher package for automating macOS application startup.
"""

from .config_loader import AppConfig, load_app_config  # noqa: F401
from .core import AppDefinition, AppStatus, WatchdogController  # noqa: F401
