"""Dark theme helpers for the PyQt-based Watchdogd Launcher UI."""

from __future__ import annotations

from PyQt6 import QtGui, QtWidgets


PALETTE_COLORS = {
    "background": "#111217",
    "surface": "#181b22",
    "surface_alt": "#1f232b",
    "text": "#f4f4f6",
    "text_muted": "#a0a7b5",
    "border": "#2d3038",
    "accent": "#4e8af7",
    "accent_dark": "#3c6cd0",
    "accent_light": "#6ba2ff",
}


STYLE_SHEET = f"""
QWidget {{
    background-color: {PALETTE_COLORS["background"]};
    color: {PALETTE_COLORS["text"]};
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 10.5pt;
}}

#titleLabel {{
    font-size: 20pt;
    letter-spacing: 0.5px;
    color: {PALETTE_COLORS["text"]};
}}

QGroupBox {{
    border: 1px solid {PALETTE_COLORS["border"]};
    border-radius: 10px;
    margin-top: 18px;
    padding: 18px;
    background-color: {PALETTE_COLORS["surface"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 24px;
    padding: 0 6px;
    color: {PALETTE_COLORS["text_muted"]};
    background-color: {PALETTE_COLORS["background"]};
}}

QPushButton {{
    background-color: {PALETTE_COLORS["surface_alt"]};
    border: 1px solid {PALETTE_COLORS["border"]};
    border-radius: 6px;
    padding: 8px 18px;
    color: {PALETTE_COLORS["text"]};
}}

QPushButton:hover {{
    background-color: {PALETTE_COLORS["accent"]};
    border-color: {PALETTE_COLORS["accent"]};
}}

QPushButton:pressed {{
    background-color: {PALETTE_COLORS["accent_dark"]};
}}

QPushButton:disabled {{
    color: {PALETTE_COLORS["text_muted"]};
    border-color: {PALETTE_COLORS["border"]};
    background-color: {PALETTE_COLORS["surface"]};
}}

QCheckBox, QRadioButton {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {PALETTE_COLORS["border"]};
    background-color: {PALETTE_COLORS["surface_alt"]};
}}

QCheckBox::indicator:checked {{
    background-color: {PALETTE_COLORS["accent"]};
    border-color: {PALETTE_COLORS["accent"]};
}}

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {PALETTE_COLORS["surface_alt"]};
    border: 1px solid {PALETTE_COLORS["border"]};
    border-radius: 6px;
    padding: 6px 10px;
}}

QPlainTextEdit {{
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 10pt;
}}

QTreeWidget {{
    background-color: {PALETTE_COLORS["surface_alt"]};
    border: 1px solid {PALETTE_COLORS["border"]};
    border-radius: 8px;
    padding: 4px;
}}

QTreeWidget::item:selected {{
    background-color: {PALETTE_COLORS["accent"]};
    color: #0c0d12;
}}

QHeaderView::section {{
    background-color: {PALETTE_COLORS["surface"]};
    border: 0;
    padding: 6px;
    color: {PALETTE_COLORS["text_muted"]};
}}

QScrollBar:vertical {{
    background: {PALETTE_COLORS["background"]};
    width: 12px;
    margin: 4px 0 4px 0;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background: {PALETTE_COLORS["surface_alt"]};
    min-height: 20px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background: {PALETTE_COLORS["accent"]};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    background: transparent;
}}

QMenuBar {{
    background-color: {PALETTE_COLORS["surface"]};
    color: {PALETTE_COLORS["text"]};
}}

QMenuBar::item:selected {{
    background: {PALETTE_COLORS["accent_dark"]};
}}

QMenu {{
    background-color: {PALETTE_COLORS["surface"]};
    color: {PALETTE_COLORS["text"]};
    border: 1px solid {PALETTE_COLORS["border"]};
}}

QMenu::item:selected {{
    background-color: {PALETTE_COLORS["accent"]};
    color: #0c0d12;
}}
"""


def apply_dark_theme(app: QtWidgets.QApplication) -> None:
    """Apply a dark palette and stylesheet to the QApplication."""
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(PALETTE_COLORS["background"]))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(PALETTE_COLORS["text"]))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(PALETTE_COLORS["surface_alt"]))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(PALETTE_COLORS["surface"]))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(PALETTE_COLORS["surface"]))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(PALETTE_COLORS["text"]))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(PALETTE_COLORS["text"]))
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(PALETTE_COLORS["surface"]))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(PALETTE_COLORS["text"]))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(PALETTE_COLORS["accent"]))
    palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(PALETTE_COLORS["accent_light"]))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#0c0d12"))

    app.setPalette(palette)
    app.setStyleSheet(STYLE_SHEET)
