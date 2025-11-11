"""Logging utilities for Watchdogd Launcher"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Callable


class Logger:
    """Simple logger that writes to file and optionally calls a callback"""
    
    def __init__(self, log_dir: Path, callback: Optional[Callable] = None):
        self.log_dir = log_dir
        self.callback = callback
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Call callback if provided (for GUI display)
        if self.callback:
            try:
                self.callback(log_message)
            except Exception as e:
                print(f"Error in log callback: {e}")
        
        # Write to daily log file
        try:
            log_file = self.log_dir / f"launcher_{datetime.now().strftime('%Y-%m-%d')}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def info(self, message: str):
        """Log an info message"""
        self.log(message, "INFO")
    
    def warning(self, message: str):
        """Log a warning message"""
        self.log(message, "WARNING")
    
    def error(self, message: str):
        """Log an error message"""
        self.log(message, "ERROR")
    
    def debug(self, message: str):
        """Log a debug message"""
        self.log(message, "DEBUG")

