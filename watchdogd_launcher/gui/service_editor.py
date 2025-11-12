"""Service editor dialog for adding/editing service configurations"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any

from ..service_definitions import ServiceStrategyFactory
from .theme import COLORS


class ServiceEditorDialog:
    """Dialog for adding/editing service configurations"""
    
    def __init__(self, parent, service_config: Optional[Dict[str, Any]] = None, title: str = "Service Configuration"):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("650x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLORS["background"])
        
        self.service_config = service_config or {}
        self.is_new = service_config is None
        
        self._create_widgets()
        self._load_values()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container with scrollbar
        canvas = tk.Canvas(
            self.dialog,
            bg=COLORS["surface"],
            highlightthickness=0,
            borderwidth=0
        )
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Surface.TFrame")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind mouse wheel to canvas and all child widgets
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store canvas reference for cleanup
        self.canvas = canvas
        
        main_frame = ttk.Frame(scrollable_frame, padding="20", style="Surface.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Service Name
        ttk.Label(main_frame, text="Service Name:", font=('', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=60).grid(row=row, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)
        row += 1
        
        # Service Type
        ttk.Label(main_frame, text="Service Type:", font=('', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        self.type_var = tk.StringVar()
        type_display = ServiceStrategyFactory.get_type_display_names()
        type_values = list(type_display.values())
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, 
                                   values=type_values,
                                   state='readonly', width=57)
        self.type_combo.grid(row=row, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)
        self.type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)
        row += 1
        
        # Workspace
        ttk.Label(main_frame, text="Workspace Directory:", font=('', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        self.workspace_label = ttk.Label(
            main_frame,
            text="(Required for NPM scripts)",
            font=('', 8, 'italic'),
            foreground=COLORS["muted_text"]
        )
        self.workspace_label.grid(row=row, column=0, sticky=tk.W)
        row += 1
        workspace_frame = ttk.Frame(main_frame, style="Surface.TFrame")
        workspace_frame.grid(row=row, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)
        self.workspace_var = tk.StringVar()
        self.workspace_entry = ttk.Entry(workspace_frame, textvariable=self.workspace_var)
        self.workspace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(workspace_frame, text="Browse...", command=self._browse_workspace, width=12).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Command/Executable
        ttk.Label(main_frame, text="Command / Executable:", font=('', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        self.command_label = ttk.Label(
            main_frame,
            text="(For executables: .exe path, For NPM: command like 'pnpm dev')",
            font=('', 8, 'italic'),
            foreground=COLORS["muted_text"]
        )
        self.command_label.grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        command_frame = ttk.Frame(main_frame, style="Surface.TFrame")
        command_frame.grid(row=row, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(command_frame, textvariable=self.command_var)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_command_btn = ttk.Button(command_frame, text="Browse...", command=self._browse_command, width=12)
        self.browse_command_btn.pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Arguments
        ttk.Label(main_frame, text="Arguments:", font=('', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        ttk.Label(
            main_frame,
            text="(Space-separated, e.g., --host --port 3000)",
            font=('', 8, 'italic'),
            foreground=COLORS["muted_text"]
        ).grid(row=row, column=0, sticky=tk.W)
        row += 1
        self.args_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.args_var, width=60).grid(row=row, column=0, columnspan=2, pady=(0, 15), sticky=tk.EW)
        row += 1
        
        # Options section
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)
        row += 1
        
        ttk.Label(main_frame, text="Options:", font=('', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Checkboxes
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Enable this service", variable=self.enabled_var).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        self.auto_restart_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Auto-restart on crash", variable=self.auto_restart_var).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        self.track_children_var = tk.BooleanVar(value=False)
        track_check = ttk.Checkbutton(main_frame, text="Track child processes (for browsers/editors)", variable=self.track_children_var)
        track_check.grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        self.use_unique_profile_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame,
            text="Launch with isolated browser profile (--user-data-dir)",
            variable=self.use_unique_profile_var
        ).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        profile_dir_frame = ttk.Frame(main_frame, style="Surface.TFrame")
        profile_dir_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=5)
        self.profile_dir_var = tk.StringVar()
        ttk.Label(profile_dir_frame, text="Profile storage dir (optional):").pack(side=tk.LEFT, padx=(0, 5))
        profile_entry = ttk.Entry(profile_dir_frame, textvariable=self.profile_dir_var)
        profile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(profile_dir_frame, text="Browse...", command=self._browse_profile_dir, width=12).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        ttk.Label(
            main_frame,
            text="(Leave blank to use %USERPROFILE%/.watchdogd_launcher/profiles/<service-name>)",
            font=('', 8, 'italic'),
            foreground=COLORS["muted_text"]
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=(20, 0))
        row += 1
        
        # Startup Delay
        delay_frame = ttk.Frame(main_frame, style="Surface.TFrame")
        delay_frame.grid(row=row, column=0, sticky=tk.W, pady=10)
        ttk.Label(delay_frame, text="Startup Delay:").pack(side=tk.LEFT, padx=(0, 5))
        self.delay_var = tk.IntVar(value=0)
        ttk.Spinbox(delay_frame, from_=0, to=60, textvariable=self.delay_var, width=8).pack(side=tk.LEFT)
        ttk.Label(delay_frame, text="seconds").pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Minimum Uptime for Crash
        uptime_frame = ttk.Frame(main_frame, style="Surface.TFrame")
        uptime_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(uptime_frame, text="Minimum Uptime for Crash:").pack(side=tk.LEFT, padx=(0, 5))
        self.min_uptime_var = tk.IntVar(value=0)
        ttk.Spinbox(uptime_frame, from_=0, to=300, textvariable=self.min_uptime_var, width=8).pack(side=tk.LEFT)
        ttk.Label(uptime_frame, text="seconds").pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Help text for min uptime
        help_label = ttk.Label(
            main_frame,
            text="(Set to 0 for browsers/editors that redirect to existing instances)",
            font=('', 8, 'italic'),
            foreground=COLORS["muted_text"]
        )
        help_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=(20, 0))
        row += 1
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        
        # Buttons at bottom
        button_frame = ttk.Frame(self.dialog, style="Surface.TFrame")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=20)
        
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save", command=self._on_ok).pack(side=tk.RIGHT)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _load_values(self):
        """Load values from existing config"""
        if self.service_config:
            self.name_var.set(self.service_config.get('name', ''))
            
            # Set service type (convert internal name to display name)
            service_type = self.service_config.get('type', 'executable')
            type_display = ServiceStrategyFactory.get_type_display_names()
            display_name = type_display.get(service_type, 'Executable (.exe)')
            self.type_var.set(display_name)
            
            self.workspace_var.set(self.service_config.get('workspace', ''))
            self.command_var.set(self.service_config.get('command', ''))
            args = self.service_config.get('args', [])
            self.args_var.set(' '.join(args) if isinstance(args, list) else '')
            self.enabled_var.set(self.service_config.get('enabled', True))
            self.auto_restart_var.set(self.service_config.get('auto_restart', True))
            self.delay_var.set(self.service_config.get('startup_delay', 0))
            self.min_uptime_var.set(self.service_config.get('min_uptime_for_crash', 0))
            self.track_children_var.set(self.service_config.get('track_child_processes', False))
            self.use_unique_profile_var.set(self.service_config.get('use_unique_profile', True))
            self.profile_dir_var.set(self.service_config.get('profile_base_dir', ''))
        else:
            self.type_var.set('Executable (.exe)')
            self.use_unique_profile_var.set(True)
        
        self._on_type_changed()
    
    def _on_type_changed(self, event=None):
        """Handle service type change"""
        display_value = self.type_var.get()
        type_display = ServiceStrategyFactory.get_type_display_names()
        
        # Reverse lookup to get internal type name
        internal_type = None
        for key, value in type_display.items():
            if value == display_value:
                internal_type = key
                break
        
        # Show/hide workspace based on type
        if internal_type == 'npm_script':
            self.workspace_label.config(text="(Required for NPM scripts)")
        elif internal_type == 'powershell_script':
            self.workspace_label.config(text="(Optional, defaults to script directory)")
        else:
            self.workspace_label.config(text="(Not used for executables)")
        
        # Update command label
        if internal_type == 'npm_script':
            self.command_label.config(text="(Command like 'pnpm dev' or 'npm start')")
            self.browse_command_btn.config(state=tk.DISABLED)
        elif internal_type == 'powershell_script':
            self.command_label.config(text="(Path to .ps1 script file)")
            self.browse_command_btn.config(state=tk.NORMAL)
        else:
            self.command_label.config(text="(Path to .exe executable file)")
            self.browse_command_btn.config(state=tk.NORMAL)
    
    def _browse_workspace(self):
        """Browse for workspace directory"""
        directory = filedialog.askdirectory(title="Select Workspace Directory")
        if directory:
            self.workspace_var.set(directory)
    
    def _browse_profile_dir(self):
        """Browse for isolated profile storage directory"""
        directory = filedialog.askdirectory(title="Select Profile Storage Directory")
        if directory:
            self.profile_dir_var.set(directory)
    
    def _browse_command(self):
        """Browse for executable or script"""
        display_value = self.type_var.get()
        type_display = ServiceStrategyFactory.get_type_display_names()
        
        internal_type = None
        for key, value in type_display.items():
            if value == display_value:
                internal_type = key
                break
        
        if internal_type == 'executable':
            file_path = filedialog.askopenfilename(
                title="Select Executable",
                filetypes=[("Executables", "*.exe"), ("All files", "*.*")]
            )
        elif internal_type == 'powershell_script':
            file_path = filedialog.askopenfilename(
                title="Select PowerShell Script",
                filetypes=[("PowerShell Scripts", "*.ps1"), ("All files", "*.*")]
            )
        else:
            return
        
        if file_path:
            self.command_var.set(file_path)
    
    def _on_ok(self):
        """Validate and save configuration"""
        if not self.name_var.get().strip():
            messagebox.showerror("Validation Error", "Service name is required", parent=self.dialog)
            return
        
        if not self.type_var.get():
            messagebox.showerror("Validation Error", "Service type is required", parent=self.dialog)
            return
        
        if not self.command_var.get().strip():
            messagebox.showerror("Validation Error", "Command is required", parent=self.dialog)
            return
        
        # Get internal type name from display name
        display_value = self.type_var.get()
        type_display = ServiceStrategyFactory.get_type_display_names()
        internal_type = None
        for key, value in type_display.items():
            if value == display_value:
                internal_type = key
                break
        
        if internal_type is None:
            messagebox.showerror("Error", "Invalid service type", parent=self.dialog)
            return
        
        # Build result configuration
        args_text = self.args_var.get().strip()
        args_list = args_text.split() if args_text else []
        
        self.result = {
            'name': self.name_var.get().strip(),
            'type': internal_type,
            'enabled': self.enabled_var.get(),
            'auto_restart': self.auto_restart_var.get(),
            'workspace': self.workspace_var.get().strip(),
            'command': self.command_var.get().strip(),
            'args': args_list,
            'startup_delay': self.delay_var.get(),
            'min_uptime_for_crash': self.min_uptime_var.get(),
            'track_child_processes': self.track_children_var.get(),
            'use_unique_profile': self.use_unique_profile_var.get(),
            'profile_base_dir': self.profile_dir_var.get().strip(),
            'environment': self.service_config.get('environment', {})
        }
        
        # Unbind mouse wheel to prevent memory leaks
        self.canvas.unbind_all("<MouseWheel>")
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Cancel and close dialog"""
        self.result = None
        # Unbind mouse wheel to prevent memory leaks
        self.canvas.unbind_all("<MouseWheel>")
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result

