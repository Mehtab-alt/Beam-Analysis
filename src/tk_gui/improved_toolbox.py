import tkinter as tk
from tkinter import ttk


class ImprovedToolbox(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Toolbox.TFrame')
        self.parent = parent
        self.selected_tool = tk.StringVar(value="select")
        self.tool_callback = None
        
        # Create a label for the toolbox
        label = ttk.Label(self, text="Tools", font=("Helvetica", 12, "bold"))
        label.pack(pady=10)
        
        # Define tools with better icons and grouping
        self.tool_categories = [
            {
                "name": "Selection",
                "tools": [
                    {"id": "select", "name": "Select", "icon": "↖"},
                ]
            },
            {
                "name": "Supports",
                "tools": [
                    {"id": "add_pinned_support", "name": "Add Pinned Support", "icon": "△"},
                    {"id": "add_roller_support", "name": "Add Roller Support", "icon": "○"},
                    {"id": "add_fixed_support", "name": "Add Fixed Support", "icon": "■"},
                ]
            },
            {
                "name": "Loads",
                "tools": [
                    {"id": "add_point_load", "name": "Add Point Load", "icon": "↓"},
                    {"id": "add_distributed_load", "name": "Add Distributed Load", "icon": "⇓"},
                ]
            },
            {
                "name": "Actions",
                "tools": [
                    {"id": "delete", "name": "Delete", "icon": "✕"},
                ]
            }
        ]
        
        # Create buttons for each tool
        self.tool_buttons = {}
        for category in self.tool_categories:
            # Create category label
            if category["name"]:
                cat_label = ttk.Label(self, text=category["name"], font=("Helvetica", 10, "bold"))
                cat_label.pack(pady=(10, 2), padx=5, anchor="w")
            
            # Create buttons for tools in this category
            for tool in category["tools"]:
                # Using default parameter in lambda to capture the current value of tool['id']
                button = ttk.Button(
                    self, 
                    text=f" {tool['icon']} {tool['name']}",
                    command=lambda t=tool['id']: self.select_tool(t),
                    style='ToolButton.TButton'
                )
                button.pack(fill=tk.X, padx=10, pady=2)
                self.tool_buttons[tool['id']] = button
                
                # Add tooltip
                self._create_tooltip(button, tool['name'])
            
        # Highlight the initially selected tool
        self._update_button_states()

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            widget.tooltip = tk.Toplevel()
            widget.tooltip.wm_overrideredirect(True)
            widget.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(widget.tooltip, text=text, 
                             background="#ffffe0", relief="solid", borderwidth=1,
                             font=("Helvetica", 8))
            label.pack()

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def set_tool_callback(self, callback):
        """Set the callback function to be called when a tool is selected."""
        self.tool_callback = callback

    def select_tool(self, tool_id):
        """Select a tool and update the UI."""
        self.selected_tool.set(tool_id)
        self._update_button_states()
        
        # Notify parent of tool selection
        if self.tool_callback:
            self.tool_callback(tool_id)

    def _update_button_states(self):
        """Update the visual state of tool buttons."""
        for tool_id, button in self.tool_buttons.items():
            if tool_id == self.selected_tool.get():
                # Highlight selected button with pressed state
                button.state(['pressed'])
            else:
                # Reset button appearance
                button.state(['!pressed'])

    def get_selected_tool(self):
        """Get the currently selected tool."""
        return self.selected_tool.get()

    def set_tool(self, tool_id):
        """Set the selected tool programmatically."""
        if tool_id in self.tool_buttons:
            self.select_tool(tool_id)