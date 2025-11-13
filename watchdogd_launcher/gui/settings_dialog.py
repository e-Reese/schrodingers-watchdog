"""Settings dialog for managing application settings and services (PyQt)."""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from PyQt6 import QtCore, QtGui, QtWidgets

from ..config_manager import ConfigManager
from .service_editor import ServiceEditorDialog


class SettingsDialog(QtWidgets.QDialog):
    """Dialog for managing services and application settings."""

    def __init__(self, parent: QtWidgets.QWidget, config_manager: ConfigManager):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Manage Services")
        self.resize(960, 620)
        self.setModal(True)

        self.services: List[Dict[str, Any]] = copy.deepcopy(
            self.config_manager.get_services()
        )
        self.modified = False

        self._build_ui()
        self._refresh_service_list()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Service Configuration Manager")
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        content_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(content_layout, stretch=1)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Service Name", "Type", "Enabled", "Command"])
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree.itemDoubleClicked.connect(lambda *_: self._edit_service())
        content_layout.addWidget(self.tree, stretch=1)

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(6)
        content_layout.addLayout(button_layout)

        self._add_button(button_layout, "Add Service", self._add_service)
        self._add_button(button_layout, "Edit Service", self._edit_service)
        self._add_button(button_layout, "Duplicate", self._duplicate_service)
        self._add_button(button_layout, "Remove Service", self._remove_service)

        button_layout.addWidget(self._separator())

        self._add_button(button_layout, "Move Up", self._move_up)
        self._add_button(button_layout, "Move Down", self._move_down)

        button_layout.addWidget(self._separator())

        self._add_button(button_layout, "Toggle Enabled", self._toggle_enabled)
        button_layout.addStretch(1)

        action_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(action_layout)
        action_layout.addStretch(1)

        save_button = QtWidgets.QPushButton("Save Changes")
        save_button.clicked.connect(self._save_changes)
        action_layout.addWidget(save_button)

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self._handle_close)
        action_layout.addWidget(close_button)

    def _add_button(self, layout: QtWidgets.QVBoxLayout, text: str, slot) -> None:
        button = QtWidgets.QPushButton(text)
        button.clicked.connect(slot)
        button.setMinimumWidth(140)
        layout.addWidget(button)

    def _separator(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        return frame

    # ------------------------------------------------------------------
    def _refresh_service_list(self) -> None:
        current_index = self._get_selected_index()
        self.tree.clear()

        for service in self.services:
            enabled_text = "Yes" if service.get("enabled", True) else "No"
            values = [
                service.get("name", ""),
                service.get("type", ""),
                enabled_text,
                service.get("command", ""),
            ]
            item = QtWidgets.QTreeWidgetItem(values)
            self.tree.addTopLevelItem(item)

        if 0 <= current_index < self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(current_index))

    def _get_selected_index(self) -> int:
        item = self.tree.currentItem()
        if not item:
            return -1
        return self.tree.indexOfTopLevelItem(item)

    # ------------------------------------------------------------------
    def _add_service(self) -> None:
        editor = ServiceEditorDialog(self, title="Add New Service")
        if editor.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.services.append(editor.result)  # type: ignore[arg-type]
            self.modified = True
            self._refresh_service_list()

    def _edit_service(self) -> None:
        index = self._get_selected_index()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a service to edit.")
            return
        editor = ServiceEditorDialog(self, service_config=self.services[index], title="Edit Service")
        if editor.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.services[index] = editor.result  # type: ignore[assignment]
            self.modified = True
            self._refresh_service_list()

    def _duplicate_service(self) -> None:
        index = self._get_selected_index()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a service to duplicate.")
            return
        duplicate = copy.deepcopy(self.services[index])
        duplicate["name"] = f"{duplicate.get('name', 'Service')} (Copy)"
        self.services.insert(index + 1, duplicate)
        self.modified = True
        self._refresh_service_list()

    def _remove_service(self) -> None:
        index = self._get_selected_index()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a service to remove.")
            return
        service_name = self.services[index].get("name", "Unknown")
        result = QtWidgets.QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove '{service_name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            del self.services[index]
            self.modified = True
            self._refresh_service_list()

    def _move_up(self) -> None:
        index = self._get_selected_index()
        if index <= 0:
            return
        self.services[index - 1], self.services[index] = self.services[index], self.services[index - 1]
        self.modified = True
        self._refresh_service_list()
        self.tree.setCurrentItem(self.tree.topLevelItem(index - 1))

    def _move_down(self) -> None:
        index = self._get_selected_index()
        if index < 0 or index >= len(self.services) - 1:
            return
        self.services[index + 1], self.services[index] = self.services[index], self.services[index + 1]
        self.modified = True
        self._refresh_service_list()
        self.tree.setCurrentItem(self.tree.topLevelItem(index + 1))

    def _toggle_enabled(self) -> None:
        index = self._get_selected_index()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a service.")
            return
        current = self.services[index].get("enabled", True)
        self.services[index]["enabled"] = not current
        self.modified = True
        self._refresh_service_list()
        self.tree.setCurrentItem(self.tree.topLevelItem(index))

    def _save_changes(self) -> None:
        self.config_manager.config["services"] = copy.deepcopy(self.services)
        if self.config_manager.save():
            QtWidgets.QMessageBox.information(self, "Success", "Services saved successfully.")
            self.modified = False
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to save services.")

    def _handle_close(self) -> None:
        if self.modified:
            result = QtWidgets.QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if result == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self._save_changes()
                if self.modified:  # Save failed
                    return
        self.accept()

