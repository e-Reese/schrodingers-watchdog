"""Settings dialog for managing application settings and services"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any

from .service_editor import ServiceEditorDialog
from ..config_manager import ConfigManager
from .theme import COLORS


class SettingsDialog:
    """Dialog for managing services and application settings"""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Services")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=COLORS["background"])
        
        self.services = self.config_manager.get_services().copy()
        self.modified = False
        
        self._create_widgets()
        self._refresh_service_list()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Title
        title_frame = ttk.Frame(self.dialog, padding="10", style="Surface.TFrame")
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="Service Configuration Manager", font=('', 12, 'bold')).pack()
        
        # Main content area
        content_frame = ttk.Frame(self.dialog, padding="10", style="Surface.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Service list
        list_frame = ttk.LabelFrame(content_frame, text="Services", padding="10", style="Surface.TLabelframe")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Treeview for services
        columns = ('name', 'type', 'enabled', 'command')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('name', text='Service Name')
        self.tree.heading('type', text='Type')
        self.tree.heading('enabled', text='Enabled')
        self.tree.heading('command', text='Command')
        
        self.tree.column('name', width=200)
        self.tree.column('type', width=120)
        self.tree.column('enabled', width=70)
        self.tree.column('command', width=350)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable mouse wheel scrolling for the tree
        def _on_mousewheel(event):
            self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.tree.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Bind double-click to edit
        self.tree.bind('<Double-Button-1>', lambda e: self._edit_service())
        
        # Button panel
        button_panel = ttk.Frame(content_frame, style="Surface.TFrame")
        button_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(button_panel, text="Add Service", command=self._add_service, width=15).pack(pady=5)
        ttk.Button(button_panel, text="Edit Service", command=self._edit_service, width=15).pack(pady=5)
        ttk.Button(button_panel, text="Duplicate", command=self._duplicate_service, width=15).pack(pady=5)
        ttk.Button(button_panel, text="Remove Service", command=self._remove_service, width=15).pack(pady=5)
        
        ttk.Separator(button_panel, orient='horizontal').pack(fill=tk.X, pady=15)
        
        ttk.Button(button_panel, text="Move Up", command=self._move_up, width=15).pack(pady=5)
        ttk.Button(button_panel, text="Move Down", command=self._move_down, width=15).pack(pady=5)
        
        ttk.Separator(button_panel, orient='horizontal').pack(fill=tk.X, pady=15)
        
        ttk.Button(button_panel, text="Toggle Enabled", command=self._toggle_enabled, width=15).pack(pady=5)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(self.dialog, padding="10", style="Surface.TFrame")
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="Close", command=self._on_close).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_frame, text="Save Changes", command=self._save_changes).pack(side=tk.RIGHT)
    
    def _refresh_service_list(self):
        """Refresh the service list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add services
        for service in self.services:
            enabled_text = "Yes" if service.get('enabled', True) else "No"
            self.tree.insert('', tk.END, values=(
                service.get('name', ''),
                service.get('type', ''),
                enabled_text,
                service.get('command', '')
            ))
    
    def _get_selected_index(self) -> int:
        """Get the index of the selected service"""
        selection = self.tree.selection()
        if not selection:
            return -1
        item = selection[0]
        return self.tree.index(item)
    
    def _add_service(self):
        """Add a new service"""
        editor = ServiceEditorDialog(self.dialog, title="Add New Service")
        result = editor.show()
        
        if result:
            self.services.append(result)
            self._refresh_service_list()
            self.modified = True
    
    def _edit_service(self):
        """Edit the selected service"""
        index = self._get_selected_index()
        if index < 0:
            messagebox.showwarning("No Selection", "Please select a service to edit", parent=self.dialog)
            return
        
        editor = ServiceEditorDialog(self.dialog, self.services[index], title="Edit Service")
        result = editor.show()
        
        if result:
            self.services[index] = result
            self._refresh_service_list()
            self.modified = True
    
    def _duplicate_service(self):
        """Duplicate the selected service"""
        index = self._get_selected_index()
        if index < 0:
            messagebox.showwarning("No Selection", "Please select a service to duplicate", parent=self.dialog)
            return
        
        # Create a copy with " (Copy)" appended to the name
        duplicate = self.services[index].copy()
        duplicate['name'] = duplicate['name'] + " (Copy)"
        
        self.services.insert(index + 1, duplicate)
        self._refresh_service_list()
        self.modified = True
    
    def _remove_service(self):
        """Remove the selected service"""
        index = self._get_selected_index()
        if index < 0:
            messagebox.showwarning("No Selection", "Please select a service to remove", parent=self.dialog)
            return
        
        service_name = self.services[index].get('name', 'Unknown')
        if messagebox.askyesno("Confirm Removal", 
                               f"Are you sure you want to remove '{service_name}'?",
                               parent=self.dialog):
            del self.services[index]
            self._refresh_service_list()
            self.modified = True
    
    def _move_up(self):
        """Move the selected service up in the list"""
        index = self._get_selected_index()
        if index <= 0:
            return
        
        self.services[index], self.services[index - 1] = self.services[index - 1], self.services[index]
        self._refresh_service_list()
        
        # Re-select the moved item
        self.tree.selection_set(self.tree.get_children()[index - 1])
        self.modified = True
    
    def _move_down(self):
        """Move the selected service down in the list"""
        index = self._get_selected_index()
        if index < 0 or index >= len(self.services) - 1:
            return
        
        self.services[index], self.services[index + 1] = self.services[index + 1], self.services[index]
        self._refresh_service_list()
        
        # Re-select the moved item
        self.tree.selection_set(self.tree.get_children()[index + 1])
        self.modified = True
    
    def _toggle_enabled(self):
        """Toggle the enabled status of the selected service"""
        index = self._get_selected_index()
        if index < 0:
            messagebox.showwarning("No Selection", "Please select a service", parent=self.dialog)
            return
        
        current = self.services[index].get('enabled', True)
        self.services[index]['enabled'] = not current
        self._refresh_service_list()
        
        # Re-select the item
        self.tree.selection_set(self.tree.get_children()[index])
        self.modified = True
    
    def _save_changes(self):
        """Save changes to configuration"""
        # Update config manager with new services list
        self.config_manager.config['services'] = self.services
        if self.config_manager.save():
            messagebox.showinfo("Success", "Services saved successfully", parent=self.dialog)
            self.modified = False
        else:
            messagebox.showerror("Error", "Failed to save services", parent=self.dialog)
    
    def _on_close(self):
        """Handle close event"""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                parent=self.dialog
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes
                self._save_changes()
        
        # Unbind mouse wheel to prevent memory leaks
        self.tree.unbind_all("<MouseWheel>")
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog"""
        self.dialog.wait_window()

