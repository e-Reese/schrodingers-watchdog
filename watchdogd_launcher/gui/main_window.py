"""Main window for Watchdogd Launcher (PyQt implementation)."""

from __future__ import annotations

import threading
import time
import webbrowser
from typing import Dict

from PyQt6 import QtCore, QtGui, QtWidgets

from ..config_manager import ConfigManager
from ..service_manager import ServiceManager
from ..utils.logger import Logger
from ..utils.process_utils import kill_processes_by_name
from .settings_dialog import SettingsDialog


class LogEmitter(QtCore.QObject):
    """Thread-safe bridge for log messages coming from background threads."""

    message = QtCore.pyqtSignal(str)


class MainWindow(QtWidgets.QMainWindow):
    """Main GUI window for Watchdogd Launcher using PyQt widgets."""

    STATUS_RUNNING_COLOR = QtGui.QColor("#7ad77a")
    STATUS_ERROR_COLOR = QtGui.QColor("#ff6b6b")
    STATUS_STOPPED_COLOR = QtGui.QColor("#b1b1b1")

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle("Watchdogd Development Environment Launcher")
        self.resize(980, 760)

        self.services: Dict[str, ServiceManager] = {}
        self.status_items: Dict[str, QtWidgets.QTreeWidgetItem] = {}
        self.all_running = False

        self.log_emitter = LogEmitter(self)
        self.log_emitter.message.connect(self._log_to_gui)

        self.logger = Logger(
            log_dir=config_manager.get_log_dir(),
            callback=self.log_emitter.message.emit,
        )

        self._create_menu()
        self._build_ui()

        self.logger.info("Watchdogd Launcher initialized. Ready to start services.")

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_menu(self) -> None:
        """Create the application menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        manage_action = QtGui.QAction("Manage Services...", self)
        manage_action.triggered.connect(self._open_service_manager)
        file_menu.addAction(manage_action)
        file_menu.addSeparator()
        exit_action = QtGui.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Help")
        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        """Construct the main layout."""
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(12)

        title_label = QtWidgets.QLabel("Watchdogd Development Environment")
        title_label.setObjectName("titleLabel")
        title_font = QtGui.QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Control buttons
        control_box = QtWidgets.QGroupBox("Controls")
        control_layout = QtWidgets.QHBoxLayout(control_box)
        control_layout.setSpacing(10)
        layout.addWidget(control_box)

        self.start_button = QtWidgets.QPushButton("Start All Services")
        self.start_button.clicked.connect(self.start_all)
        control_layout.addWidget(self.start_button)

        self.stop_button = QtWidgets.QPushButton("Stop All Services")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_all)
        control_layout.addWidget(self.stop_button)

        open_browser_button = QtWidgets.QPushButton("Open Browser")
        open_browser_button.clicked.connect(self.open_browser)
        control_layout.addWidget(open_browser_button)

        manage_button = QtWidgets.QPushButton("Manage Services")
        manage_button.clicked.connect(self._open_service_manager)
        control_layout.addWidget(manage_button)

        control_layout.addStretch()

        self.auto_open_checkbox = QtWidgets.QCheckBox("Auto-open browser on start")
        self.auto_open_checkbox.setChecked(
            self.config_manager.get_app_setting("auto_open_browser", False)
        )
        self.auto_open_checkbox.stateChanged.connect(self._toggle_auto_open_browser)
        control_layout.addWidget(self.auto_open_checkbox)

        # Status area
        status_group = QtWidgets.QGroupBox("Service Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)
        layout.addWidget(status_group)

        self.status_tree = QtWidgets.QTreeWidget()
        self.status_tree.setColumnCount(2)
        self.status_tree.setHeaderLabels(["Service", "Status"])
        self.status_tree.setAlternatingRowColors(True)
        self.status_tree.setRootIsDecorated(False)
        self.status_tree.header().setStretchLastSection(True)
        self.status_tree.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.status_tree.header().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        status_layout.addWidget(self.status_tree)

        # Log section
        log_group = QtWidgets.QGroupBox("Activity Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        layout.addWidget(log_group, stretch=1)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        log_layout.addWidget(self.log_view, stretch=1)

        clear_button = QtWidgets.QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self._refresh_status_display()

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    @QtCore.pyqtSlot(str)
    def _log_to_gui(self, message: str) -> None:
        """Append a log message to the log view."""
        self.log_view.appendPlainText(message)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    def clear_log(self) -> None:
        """Clear the log widget."""
        self.log_view.clear()

    # ------------------------------------------------------------------
    # Status management
    # ------------------------------------------------------------------
    def _refresh_status_display(self) -> None:
        """Populate the status tree from configuration."""
        self.status_tree.clear()
        self.status_items.clear()

        services = self.config_manager.get_services()
        if not services:
            empty_item = QtWidgets.QTreeWidgetItem(
                ["No services configured", "Use 'Manage Services' to add services"]
            )
            empty_item.setFirstColumnSpanned(True)
            font = empty_item.font(0)
            font.setItalic(True)
            empty_item.setFont(0, font)
            empty_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#888888")))
            self.status_tree.addTopLevelItem(empty_item)
            return

        for service_config in services:
            service_name = service_config.get("name", "Unnamed Service")
            enabled = service_config.get("enabled", True)
            status_text = "Disabled" if not enabled else "Stopped"
            status_item = QtWidgets.QTreeWidgetItem([service_name, status_text])
            status_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, service_name)
            status_item.setForeground(
                1, QtGui.QBrush(self.STATUS_STOPPED_COLOR)
            )
            self.status_tree.addTopLevelItem(status_item)
            self.status_items[service_name] = status_item

    def update_status(self, service_name: str, status: str, color: QtGui.QColor) -> None:
        """Update the status text and color for a service."""
        item = self.status_items.get(service_name)
        if not item:
            return
        item.setText(1, status)
        item.setForeground(1, QtGui.QBrush(color))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _toggle_auto_open_browser(self) -> None:
        new_value = self.auto_open_checkbox.isChecked()
        self.config_manager.set_app_setting("auto_open_browser", new_value)
        status = "enabled" if new_value else "disabled"
        self.logger.info(f"Auto-open browser {status}")

    def start_all(self) -> None:
        if self.all_running:
            QtWidgets.QMessageBox.information(
                self, "Already Running", "Services are already running."
            )
            return

        services = self.config_manager.get_services()
        enabled_services = [s for s in services if s.get("enabled", True)]
        if not enabled_services:
            QtWidgets.QMessageBox.warning(
                self,
                "No Services",
                "No enabled services configured. Use 'Manage Services' to add services.",
            )
            return

        self.logger.info("=== Starting all enabled services ===")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.all_running = True

        self._cleanup_existing_processes()

        crash_log_path = self.config_manager.get_crash_log_file()
        for service_config in enabled_services:
            service_name = service_config.get("name", "Unknown")
            try:
                manager = ServiceManager(
                    service_config,
                    self.logger.log,
                    crash_log_path,
                )
                self.services[service_name] = manager
                manager.start()
                self.update_status(service_name, "Running", self.STATUS_RUNNING_COLOR)
            except ValueError as exc:
                self.logger.error(f"Failed to start {service_name}: {exc}")
                self.update_status(service_name, "Error", self.STATUS_ERROR_COLOR)

        if self.auto_open_checkbox.isChecked():
            delay = self.config_manager.get_app_setting("browser_delay", 8)
            threading.Thread(
                target=self._delayed_browser_open, args=(delay,), daemon=True
            ).start()

    def stop_all(self) -> None:
        if not self.all_running:
            return
        self.logger.info("=== Stopping all services ===")
        self.stop_button.setEnabled(False)
        for name, service in self.services.items():
            service.stop()
            self.update_status(name, "Stopped", self.STATUS_STOPPED_COLOR)
            self.logger.info(f"[{name}] Service stopped")
        self.services.clear()
        self.all_running = False
        self.start_button.setEnabled(True)
        self.logger.info("=== All services stopped ===")

    def open_browser(self) -> None:
        url = self.config_manager.get_app_setting("frontend_url", "http://localhost:3000/")
        try:
            webbrowser.open(url)
            self.logger.info(f"Opening browser: {url}")
        except Exception as exc:
            self.logger.error(f"Failed to open browser: {exc}")
            QtWidgets.QMessageBox.critical(
                self, "Browser Error", f"Failed to open browser:\n{exc}"
            )

    def _delayed_browser_open(self, delay: int) -> None:
        time.sleep(delay)
        self.open_browser()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _cleanup_existing_processes(self) -> None:
        self.logger.info("Cleaning up existing processes...")
        processes_to_kill = ["Watchdogd.exe", "node.exe", "pnpm.exe"]
        killed = kill_processes_by_name(processes_to_kill)
        if killed > 0:
            self.logger.info(f"Killed {killed} existing process(es)")
            time.sleep(2)
        self.logger.info("Cleanup complete")

    def _open_service_manager(self) -> None:
        if self.all_running:
            result = QtWidgets.QMessageBox.question(
                self,
                "Services Running",
                "Services are currently running. "
                "You should stop them before making changes. Continue anyway?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
            )
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        dialog = SettingsDialog(self, self.config_manager)
        dialog.exec()
        self._refresh_status_display()

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About Watchdogd Launcher",
            (
                "Watchdogd Development Environment Launcher\n"
                "Version 2.0.0\n\n"
                "A dynamic service management tool with automatic restart capabilities.\n\n"
                "Features:\n"
                "- Configurable services\n"
                "- Auto-restart on crash\n"
                "- Crash logging\n"
                "- Multiple service types (Executable, NPM, PowerShell)"
            ),
        )

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        if self.all_running:
            result = QtWidgets.QMessageBox.question(
                self,
                "Services Running",
                "Services are still running. Stop them and exit?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
            )
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.stop_all()
        event.accept()

