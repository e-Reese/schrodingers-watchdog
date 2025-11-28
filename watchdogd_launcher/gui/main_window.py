from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config_loader import AppConfig
from ..core import AppDefinition, AppStatus, WatchdogController


STATUS_COLORS = {
    AppStatus.RUNNING: QColor(46, 125, 50),  # green
    AppStatus.STOPPED: QColor(211, 47, 47),  # red
    AppStatus.STARTING: QColor(255, 179, 0),  # amber
    AppStatus.STOPPING: QColor(255, 179, 0),
    AppStatus.UNKNOWN: QColor(120, 120, 120),
    AppStatus.ERROR: QColor(198, 40, 40),
}


class MainWindow(QMainWindow):
    def __init__(self, controller: WatchdogController, config: AppConfig) -> None:
        super().__init__()
        self.controller = controller
        self.config = config
        self.setWindowTitle("Watchdogd Launcher")
        self.resize(900, 500)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Application", "Status", "Auto Start", "Target"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.log_view = QTextEdit(self)
        self.log_view.setReadOnly(True)

        self.start_button = QPushButton("Start Selected")
        self.stop_button = QPushButton("Stop Selected")
        self.refresh_button = QPushButton("Refresh Status")

        self.start_button.clicked.connect(self._start_selected)
        self.stop_button.clicked.connect(self._stop_selected)
        self.refresh_button.clicked.connect(self.controller.refresh_status)

        button_row = QHBoxLayout()
        button_row.addWidget(QLabel("Actions:"))
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.refresh_button)
        button_row.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(button_row)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("Activity Log:"))
        layout.addWidget(self.log_view)

        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.controller.status_changed.connect(self._handle_status_change)
        self.controller.log_event.connect(self._append_log)

        self._populate_table()
        self._setup_timer()

        # Run initial status refresh and auto starts.
        self.controller.refresh_status()
        self.controller.start_autorun_apps()

    def _setup_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.setInterval(int(self.config.poll_interval * 1000))
        self.timer.timeout.connect(self.controller.refresh_status)
        self.timer.start()

    def _populate_table(self) -> None:
        apps = list(self.controller.iter_apps())
        self.table.setRowCount(len(apps))
        for row, app in enumerate(apps):
            self._render_row(row, app, self.controller.get_status(app.name))

    def _render_row(self, row: int, app: AppDefinition, status: AppStatus) -> None:
        name_item = QTableWidgetItem(app.name)
        name_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 0, name_item)

        status_item = QTableWidgetItem(status.value)
        status_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self._apply_status_color(status_item, status)
        self.table.setItem(row, 1, status_item)

        auto_item = QTableWidgetItem("Yes" if app.auto_start else "No")
        auto_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        auto_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 2, auto_item)

        target_item = QTableWidgetItem(app.launch_target)
        target_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 3, target_item)

    def _apply_status_color(self, item: QTableWidgetItem, status: AppStatus) -> None:
        color = STATUS_COLORS.get(status)
        if color:
            item.setForeground(color)

    def _append_log(self, message: str) -> None:
        self.log_view.append(message)

    def _handle_status_change(self, name: str, status: AppStatus) -> None:
        row = self._find_row(name)
        if row is None:
            return
        status_item = self.table.item(row, 1)
        if not status_item:
            status_item = QTableWidgetItem()
            status_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 1, status_item)
        status_item.setText(status.value)
        self._apply_status_color(status_item, status)

    def _selected_names(self) -> List[str]:
        rows = {index.row() for index in self.table.selectionModel().selectedRows()}
        names = []
        for row in rows:
            item = self.table.item(row, 0)
            if item:
                names.append(item.text())
        return names

    def _start_selected(self) -> None:
        for name in self._selected_names():
            self.controller.start_app(name)

    def _stop_selected(self) -> None:
        for name in self._selected_names():
            self.controller.stop_app(name)

    def _find_row(self, app_name: str) -> Optional[int]:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == app_name:
                return row
        return None
