"""Main window for Watchdogd Launcher"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import webbrowser
from datetime import datetime
from typing import Dict, List

from ..config_manager import ConfigManager
from ..service_manager import ServiceManager
from ..utils.logger import Logger
from ..utils.process_utils import kill_processes_by_name
from .settings_dialog import SettingsDialog


class MainWindow:
    """Main GUI window for Watchdogd Launcher"""
    
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        self.root = root
        self.config_manager = config_manager
        self.root.title("Watchdogd Development Environment Launcher")
        self.root.geometry("950x750")
        
        # Service managers
        self.services: Dict[str, ServiceManager] = {}
        self.all_running = False
        
        # Logger
        self.logger = Logger(
            log_dir=config_manager.get_log_dir(),
            callback=self._log_to_gui
        )
        
        # Create GUI
        self._create_menu()
        self._create_gui()
        
        # Ensure log directory exists
        config_manager.get_log_dir().mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Watchdogd Launcher initialized. Ready to start services.")
        
        # Set close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Manage Services...", command=self._open_service_manager)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_gui(self):
        """Create the GUI layout"""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="Watchdogd Development Environment", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # Control buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Start All Services", 
            command=self.start_all,
            width=25
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop All Services", 
            command=self.stop_all,
            width=25,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.open_browser_button = ttk.Button(
            button_frame,
            text="Open Browser",
            command=self.open_browser,
            width=20
        )
        self.open_browser_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Manage Services",
            command=self._open_service_manager,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-open browser checkbox
        self.auto_open_var = tk.BooleanVar(value=self.config_manager.get_app_setting('auto_open_browser', False))
        self.auto_open_check = ttk.Checkbutton(
            button_frame,
            text="Auto-open browser on start",
            variable=self.auto_open_var,
            command=self._toggle_auto_open_browser
        )
        self.auto_open_check.pack(side=tk.LEFT, padx=15)
        
        # Status indicators
        status_frame = ttk.LabelFrame(self.root, text="Service Status", padding="10")
        status_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        
        # Create a frame with scrollbar for status
        status_canvas = tk.Canvas(status_frame, height=150)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=status_canvas.yview)
        self.status_container = ttk.Frame(status_canvas)
        
        self.status_container.bind(
            "<Configure>",
            lambda e: status_canvas.configure(scrollregion=status_canvas.bbox("all"))
        )
        
        status_canvas.create_window((0, 0), window=self.status_container, anchor="nw")
        status_canvas.configure(yscrollcommand=status_scrollbar.set)
        
        # Enable mouse wheel scrolling for status area
        def _on_status_mousewheel(event):
            status_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        status_canvas.bind("<MouseWheel>", _on_status_mousewheel)
        self.status_container.bind("<MouseWheel>", _on_status_mousewheel)
        
        status_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_labels: Dict[str, ttk.Label] = {}
        self._refresh_status_display()
        
        # Log output
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=20, 
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Clear log button
        clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_button.pack(pady=5)
    
    def _refresh_status_display(self):
        """Refresh the status display with current services"""
        # Clear existing status labels
        for widget in self.status_container.winfo_children():
            widget.destroy()
        self.status_labels.clear()
        
        # Get services from config
        services = self.config_manager.get_services()
        
        if not services:
            ttk.Label(
                self.status_container, 
                text="No services configured. Use 'Manage Services' to add services.",
                font=('', 9, 'italic'),
                foreground='gray'
            ).pack(pady=20)
            return
        
        for i, service_config in enumerate(services):
            service_name = service_config.get('name', f'Service {i+1}')
            enabled = service_config.get('enabled', True)
            
            row_frame = ttk.Frame(self.status_container)
            row_frame.pack(fill=tk.X, pady=2)
            
            label = ttk.Label(row_frame, text=f"{service_name}:", width=30, anchor=tk.W)
            label.pack(side=tk.LEFT, padx=5)
            
            status_text = "Disabled" if not enabled else "Stopped"
            status_color = "gray"
            
            status = ttk.Label(row_frame, text=status_text, foreground=status_color)
            status.pack(side=tk.LEFT)
            
            self.status_labels[service_name] = status
    
    def _log_to_gui(self, message: str):
        """Add a message to the GUI log"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
    
    def update_status(self, service_name: str, status: str, color: str):
        """Update the status indicator for a service"""
        if service_name in self.status_labels:
            self.status_labels[service_name].config(text=status, foreground=color)
    
    def _toggle_auto_open_browser(self):
        """Toggle the auto-open browser setting"""
        new_value = self.auto_open_var.get()
        self.config_manager.set_app_setting('auto_open_browser', new_value)
        status = "enabled" if new_value else "disabled"
        self.logger.info(f"Auto-open browser {status}")
    
    def start_all(self):
        """Start all enabled services"""
        if self.all_running:
            messagebox.showinfo("Already Running", "Services are already running")
            return
        
        services = self.config_manager.get_services()
        enabled_services = [s for s in services if s.get('enabled', True)]
        
        if not enabled_services:
            messagebox.showwarning("No Services", "No enabled services configured. Use 'Manage Services' to add services.")
            return
        
        self.logger.info("=== Starting all enabled services ===")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.all_running = True
        
        # Cleanup existing processes
        self._cleanup_existing_processes()
        
        # Initialize service managers
        crash_log_path = self.config_manager.get_crash_log_file()
        
        for service_config in enabled_services:
            service_name = service_config.get('name', 'Unknown')
            try:
                service_manager = ServiceManager(
                    service_config,
                    self.logger.log,
                    crash_log_path
                )
                self.services[service_name] = service_manager
                service_manager.start()
                self.update_status(service_name, "Running", "green")
            except ValueError as e:
                self.logger.error(f"Failed to start {service_name}: {e}")
                self.update_status(service_name, "Error", "red")
        
        # Open browser after delay if configured
        if self.auto_open_var.get():
            delay = self.config_manager.get_app_setting('browser_delay', 8)
            threading.Thread(target=self._delayed_browser_open, args=(delay,), daemon=True).start()
    
    def stop_all(self):
        """Stop all services"""
        if not self.all_running:
            return
        
        self.logger.info("=== Stopping all services ===")
        self.stop_button.config(state=tk.DISABLED)
        
        # Stop all services
        for name, service in self.services.items():
            service.stop()
            self.update_status(name, "Stopped", "gray")
            self.logger.info(f"[{name}] Service stopped")
        
        self.services.clear()
        self.all_running = False
        self.start_button.config(state=tk.NORMAL)
        
        self.logger.info("=== All services stopped ===")
    
    def open_browser(self):
        """Open the frontend URL in the default browser"""
        url = self.config_manager.get_app_setting('frontend_url', 'http://localhost:3000/')
        try:
            webbrowser.open(url)
            self.logger.info(f"Opening browser: {url}")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
            messagebox.showerror("Browser Error", f"Failed to open browser: {e}")
    
    def _delayed_browser_open(self, delay: int):
        """Open browser after services have had time to start"""
        time.sleep(delay)
        self.open_browser()
    
    def _cleanup_existing_processes(self):
        """Kill any existing processes that might conflict"""
        self.logger.info("Cleaning up existing processes...")
        
        processes_to_kill = ['Watchdogd.exe', 'node.exe', 'pnpm.exe']
        killed = kill_processes_by_name(processes_to_kill)
        
        if killed > 0:
            self.logger.info(f"Killed {killed} existing process(es)")
            time.sleep(2)
        
        self.logger.info("Cleanup complete")
    
    def _open_service_manager(self):
        """Open the service management dialog"""
        # If services are running, warn user
        if self.all_running:
            result = messagebox.askyesno(
                "Services Running",
                "Services are currently running. You should stop them before making changes. Continue anyway?",
                icon='warning'
            )
            if not result:
                return
        
        dialog = SettingsDialog(self.root, self.config_manager)
        dialog.show()
        
        # Refresh status display after dialog closes
        self._refresh_status_display()
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Watchdogd Launcher",
            "Watchdogd Development Environment Launcher\n"
            "Version 2.0.0\n\n"
            "A dynamic service management tool with automatic restart capabilities.\n\n"
            "Features:\n"
            "- Configurable services\n"
            "- Auto-restart on crash\n"
            "- Crash logging\n"
            "- Multiple service types (Executable, NPM, PowerShell)"
        )
    
    def on_closing(self):
        """Handle window close event"""
        if self.all_running:
            result = messagebox.askyesno(
                "Services Running",
                "Services are still running. Stop them and exit?"
            )
            if not result:
                return
            self.stop_all()
        
        self.root.destroy()

