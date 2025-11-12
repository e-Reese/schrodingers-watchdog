"""Dark theme helpers for the Watchdogd Launcher UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, font as tkfont

# Centralized palette so widgets stay consistent.
COLORS = {
    "background": "#1e1e1e",
    "surface": "#252526",
    "surface_alt": "#2d2d30",
    "text": "#f3f3f3",
    "muted_text": "#b1b1b1",
    "accent": "#42a5f5",
    "accent_hover": "#63b3ff",
    "border": "#3f3f46",
    "scroll_trough": "#1a1a1a",
}


def apply_dark_theme(root: tk.Tk) -> None:
    """Apply a dark color palette to Tk/ttk widgets."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        # Fall back gracefully if the theme is missing.
        pass

    root.configure(bg=COLORS["background"])
    root.tk_setPalette(
        background=COLORS["background"],
        foreground=COLORS["text"],
        activeBackground=COLORS["surface_alt"],
        activeForeground=COLORS["text"],
        highlightBackground=COLORS["border"],
        highlightColor=COLORS["accent"],
        insertBackground=COLORS["text"],
        selectBackground=COLORS["accent"],
        selectForeground=COLORS["background"],
    )

    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
    except tk.TclError:
        pass
    try:
        menu_font = tkfont.nametofont("TkMenuFont")
        menu_font.configure(family="Segoe UI", size=10)
    except tk.TclError:
        pass
    try:
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family="Segoe UI", size=10)
    except tk.TclError:
        pass
    root.option_add("*Menu.background", COLORS["surface"])
    root.option_add("*Menu.foreground", COLORS["text"])
    root.option_add("*Menu.activeBackground", COLORS["accent"])
    root.option_add("*Menu.activeForeground", COLORS["background"])

    # Base widgets
    style.configure(
        ".",
        background=COLORS["background"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["surface"],
        bordercolor=COLORS["border"],
        focuscolor=COLORS["accent"],
    )
    style.configure(
        "TFrame",
        background=COLORS["background"],
    )
    style.configure(
        "Surface.TFrame",
        background=COLORS["surface"],
    )
    style.configure(
        "TLabelframe",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=COLORS["surface"],
        foreground=COLORS["muted_text"],
    )
    style.configure(
        "Surface.TLabelframe",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        relief="solid",
    )
    style.configure(
        "Surface.TLabelframe.Label",
        background=COLORS["surface"],
        foreground=COLORS["muted_text"],
    )
    style.configure(
        "TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
    )
    style.configure(
        "TButton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        padding=(12, 6),
        borderwidth=0,
    )
    style.map(
        "TButton",
        background=[("active", COLORS["accent_hover"]), ("disabled", COLORS["surface_alt"])],
        foreground=[("disabled", COLORS["muted_text"])],
    )
    style.configure(
        "TCheckbutton",
        background=COLORS["background"],
        foreground=COLORS["text"],
    )
    style.configure(
        "TRadiobutton",
        background=COLORS["background"],
        foreground=COLORS["text"],
    )
    style.configure(
        "TEntry",
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        insertcolor=COLORS["text"],
        bordercolor=COLORS["border"],
    )
    style.configure(
        "TCombobox",
        fieldbackground=COLORS["surface"],
        background=COLORS["surface"],
        foreground=COLORS["text"],
        arrowcolor=COLORS["text"],
        bordercolor=COLORS["border"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["surface"])],
        selectbackground=[("readonly", COLORS["surface"])],
    )
    style.configure(
        "Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        rowheight=24,
        bordercolor=COLORS["border"],
        borderwidth=0,
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["accent"])],
        foreground=[("selected", COLORS["background"])],
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["surface_alt"],
        foreground=COLORS["text"],
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLORS["accent"])],
        foreground=[("active", COLORS["background"])],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["surface"],
        troughcolor=COLORS["scroll_trough"],
        bordercolor=COLORS["border"],
        arrowcolor=COLORS["text"],
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=COLORS["surface"],
        troughcolor=COLORS["scroll_trough"],
        bordercolor=COLORS["border"],
        arrowcolor=COLORS["text"],
    )


def apply_surface_background(widget: tk.Widget, *, use_alt: bool = False) -> None:
    """Give plain Tk widgets a dark surface background."""
    color = COLORS["surface_alt"] if use_alt else COLORS["surface"]
    supported = set(widget.keys())

    if "background" in supported:
        widget.configure(background=color)
    elif "bg" in supported:
        widget.configure(bg=color)

    if "foreground" in supported:
        widget.configure(foreground=COLORS["text"])
    elif "fg" in supported:
        widget.configure(fg=COLORS["text"])

    if "highlightbackground" in supported:
        widget.configure(highlightbackground=COLORS["border"])
    if "highlightcolor" in supported:
        widget.configure(highlightcolor=COLORS["border"])
    if "insertbackground" in supported:
        widget.configure(insertbackground=COLORS["text"])
    if "selectbackground" in supported:
        widget.configure(selectbackground=COLORS["accent"])
    if "selectforeground" in supported:
        widget.configure(selectforeground=COLORS["background"])
