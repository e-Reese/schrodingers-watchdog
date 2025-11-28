"""Service editor dialog for adding/editing service configurations (PyQt)."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from ..service_definitions import ServiceStrategyFactory


class ServiceEditorDialog(QtWidgets.QDialog):
    """Dialog for creating or editing a single service configuration."""

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        service_config: Optional[Dict[str, Any]] = None,
        title: str = "Service Configuration",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 680)
        self.setModal(True)

        self.service_config = service_config or {}
        self.result: Optional[Dict[str, Any]] = None
        self.type_display = ServiceStrategyFactory.get_type_display_names()
        self.display_to_type = {v: k for k, v in self.type_display.items()}

        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, stretch=1)

        container = QtWidgets.QWidget()
        scroll.setWidget(container)
        self.form_layout = QtWidgets.QFormLayout(container)
        self.form_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.form_layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.form_layout.setHorizontalSpacing(18)
        self.form_layout.setVerticalSpacing(14)

        # Service name
        self.name_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self._bold_label("Service Name:"), self.name_edit)

        # Type
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(self.type_display.values())
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.form_layout.addRow(self._bold_label("Service Type:"), self.type_combo)

        # Workspace
        self.workspace_hint = self._hint_label("(Required for NPM scripts)")
        self.workspace_edit, workspace_btn = self._browse_row(
            self._browse_workspace, placeholder="Path to workspace directory"
        )
        workspace_layout = QtWidgets.QVBoxLayout()
        workspace_layout.addLayout(self._row_layout(self.workspace_edit, workspace_btn))
        workspace_layout.addWidget(self.workspace_hint)
        self.form_layout.addRow(self._bold_label("Workspace Directory:"), workspace_layout)

        # Command
        if os.name == 'nt':
            cmd_hint = "(For executables: .exe path, For NPM: command like 'pnpm dev')"
        else:
            cmd_hint = "(For executables: path to executable, For NPM: command like 'pnpm dev')"
        self.command_hint = self._hint_label(cmd_hint)
        self.command_edit, self.command_browse_btn = self._browse_row(
            self._browse_command, placeholder="Command or path"
        )
        command_layout = QtWidgets.QVBoxLayout()
        command_layout.addLayout(
            self._row_layout(self.command_edit, self.command_browse_btn)
        )
        command_layout.addWidget(self.command_hint)
        self.form_layout.addRow(self._bold_label("Command / Executable:"), command_layout)

        # Arguments
        self.args_edit = QtWidgets.QLineEdit()
        args_layout = QtWidgets.QVBoxLayout()
        args_layout.addWidget(self.args_edit)
        args_layout.addWidget(
            self._hint_label("(Space-separated, e.g., --host --port 3000)")
        )
        self.form_layout.addRow(self._bold_label("Arguments:"), args_layout)

        # Options
        options_box = QtWidgets.QGroupBox("Options")
        options_layout = QtWidgets.QVBoxLayout(options_box)
        options_layout.setSpacing(6)

        self.enabled_checkbox = QtWidgets.QCheckBox("Enable this service")
        self.auto_restart_checkbox = QtWidgets.QCheckBox("Auto-restart on crash")
        self.track_children_checkbox = QtWidgets.QCheckBox(
            "Track child processes (for browsers/editors)"
        )
        self.unique_profile_checkbox = QtWidgets.QCheckBox(
            "Launch with isolated browser profile (--user-data-dir)"
        )
        options_layout.addWidget(self.enabled_checkbox)
        options_layout.addWidget(self.auto_restart_checkbox)
        options_layout.addWidget(self.track_children_checkbox)
        options_layout.addWidget(self.unique_profile_checkbox)
        self.form_layout.addRow(options_box)

        # Profile directory
        self.profile_dir_edit, profile_btn = self._browse_row(
            self._browse_profile_dir, placeholder="Optional profile storage directory"
        )
        profile_layout = QtWidgets.QVBoxLayout()
        profile_layout.addLayout(self._row_layout(self.profile_dir_edit, profile_btn))
        if os.name == 'nt':
            profile_hint = "(Leave blank to use %USERPROFILE%/.watchdogd_launcher/profiles/<service-name>)"
        else:
            profile_hint = "(Leave blank to use ~/.watchdogd_launcher/profiles/<service-name>)"
        profile_layout.addWidget(self._hint_label(profile_hint))
        self.form_layout.addRow(self._bold_label("Profile Storage Directory:"), profile_layout)

        # Startup delay
        self.delay_spin = QtWidgets.QSpinBox()
        self.delay_spin.setRange(0, 600)
        self.delay_spin.setSuffix(" seconds")
        self.form_layout.addRow(self._bold_label("Startup Delay:"), self.delay_spin)

        # Min uptime
        self.min_uptime_spin = QtWidgets.QSpinBox()
        self.min_uptime_spin.setRange(0, 3600)
        min_uptime_layout = QtWidgets.QVBoxLayout()
        min_uptime_layout.addWidget(self.min_uptime_spin)
        min_uptime_layout.addWidget(
            self._hint_label("(Set to 0 for browsers/editors that redirect to existing instances)")
        )
        self.form_layout.addRow(self._bold_label("Minimum Uptime for Crash:"), min_uptime_layout)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _bold_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def _hint_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("color: #888888; font-style: italic;")
        label.setWordWrap(True)
        return label

    def _row_layout(
        self, widget: QtWidgets.QWidget, button: QtWidgets.QWidget
    ) -> QtWidgets.QHBoxLayout:
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(button)
        return layout

    def _browse_row(
        self, callback, *, placeholder: str = ""
    ) -> tuple[QtWidgets.QLineEdit, QtWidgets.QPushButton]:
        edit = QtWidgets.QLineEdit()
        edit.setPlaceholderText(placeholder)
        button = QtWidgets.QPushButton("Browse...")
        button.clicked.connect(callback)
        return edit, button

    # ------------------------------------------------------------------
    def _load_values(self) -> None:
        config = self.service_config
        self.name_edit.setText(config.get("name", ""))
        service_type = config.get("type", "executable")
        display_name = self.type_display.get(service_type, "Executable")
        index = self.type_combo.findText(display_name)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.workspace_edit.setText(config.get("workspace", ""))
        self.command_edit.setText(config.get("command", ""))

        args = config.get("args", [])
        if isinstance(args, list):
            self.args_edit.setText(" ".join(args))
        else:
            self.args_edit.setText(str(args))

        self.enabled_checkbox.setChecked(config.get("enabled", True))
        self.auto_restart_checkbox.setChecked(config.get("auto_restart", True))
        self.track_children_checkbox.setChecked(config.get("track_child_processes", False))
        self.unique_profile_checkbox.setChecked(config.get("use_unique_profile", True))
        self.profile_dir_edit.setText(config.get("profile_base_dir", ""))
        self.delay_spin.setValue(config.get("startup_delay", 0))
        self.min_uptime_spin.setValue(config.get("min_uptime_for_crash", 0))

        self._on_type_changed(self.type_combo.currentText())

    # ------------------------------------------------------------------
    def _on_type_changed(self, display_value: str) -> None:
        internal_type = self.display_to_type.get(display_value, "executable")
        if internal_type == "npm_script":
            self.workspace_hint.setText("(Required for NPM scripts)")
            self.command_hint.setText("(Command like 'pnpm dev' or 'npm start')")
            self.command_browse_btn.setEnabled(False)
        elif internal_type == "powershell_script":
            self.workspace_hint.setText("(Optional, defaults to script directory)")
            self.command_hint.setText("(Path to .ps1 script file)")
            self.command_browse_btn.setEnabled(True)
        elif internal_type == "shell_script":
            self.workspace_hint.setText("(Optional, defaults to script directory)")
            self.command_hint.setText("(Path to .sh script file)")
            self.command_browse_btn.setEnabled(True)
        else:  # executable
            self.workspace_hint.setText("(Not used for executables)")
            if os.name == 'nt':
                self.command_hint.setText("(Path to .exe executable file)")
            else:
                self.command_hint.setText("(Path to .app bundle, executable inside .app, or Unix executable)")
            self.command_browse_btn.setEnabled(True)

    # ------------------------------------------------------------------
    def _browse_workspace(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Workspace Directory"
        )
        if directory:
            self.workspace_edit.setText(directory)

    def _browse_profile_dir(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Profile Storage Directory"
        )
        if directory:
            self.profile_dir_edit.setText(directory)

    def _browse_command(self) -> None:
        display_value = self.type_combo.currentText()
        internal_type = self.display_to_type.get(display_value, "executable")

        if internal_type == "executable":
            if os.name == 'nt':
                file_filter = "Executables (*.exe);;All Files (*.*)"
            else:
                # On Unix systems, allow all files (executables don't have extensions)
                file_filter = "All Files (*)"
        elif internal_type == "powershell_script":
            file_filter = "PowerShell Scripts (*.ps1);;All Files (*.*)"
        elif internal_type == "shell_script":
            file_filter = "Shell Scripts (*.sh);;All Files (*.*)"
        else:
            file_filter = "All Files (*.*)"

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Command",
            filter=file_filter,
        )
        if file_path:
            self.command_edit.setText(file_path)

    # ------------------------------------------------------------------
    def accept(self) -> None:  # type: ignore[override]
        data = self._build_result()
        if data is None:
            return
        self.result = data
        super().accept()

    def _build_result(self) -> Optional[Dict[str, Any]]:
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Service name is required.")
            return None

        display_value = self.type_combo.currentText()
        internal_type = self.display_to_type.get(display_value)
        if not internal_type:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Service type is required.")
            return None

        command = self.command_edit.text().strip()
        if not command:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Command is required.")
            return None

        args_text = self.args_edit.text().strip()
        args_list = args_text.split() if args_text else []

        return {
            "name": name,
            "type": internal_type,
            "enabled": self.enabled_checkbox.isChecked(),
            "auto_restart": self.auto_restart_checkbox.isChecked(),
            "workspace": self.workspace_edit.text().strip(),
            "command": command,
            "args": args_list,
            "startup_delay": self.delay_spin.value(),
            "min_uptime_for_crash": self.min_uptime_spin.value(),
            "track_child_processes": self.track_children_checkbox.isChecked(),
            "use_unique_profile": self.unique_profile_checkbox.isChecked(),
            "profile_base_dir": self.profile_dir_edit.text().strip(),
            "environment": self.service_config.get("environment", {}),
        }
