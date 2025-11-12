"""Main entry point for Watchdogd Launcher application"""

import tkinter as tk
import sys
from pathlib import Path

from .config_manager import ConfigManager
from .gui.main_window import MainWindow
from .gui.theme import apply_dark_theme


def main():
    """Main entry point"""
    # Create root window
    root = tk.Tk()
    apply_dark_theme(root)
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    
    # Create main window
    app = MainWindow(root, config_manager)
    
    # Run the application
    root.mainloop()


if __name__ == '__main__':
    main()

