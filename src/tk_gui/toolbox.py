import tkinter as tk
from tkinter import ttk


class Toolbox(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selected_tool = tk.StringVar(value="select")
        self.tool_callback = None
        
        # Create a label for the toolbox
        label = ttk.Label(self, text="Tools", font=("Helvetica", 12, "bold"))
        label.pack(pady=5)
        
        # Define tools
        self.tools = [
            {"id": "select", "name": "Select", "icon": "↖"},
            {"id": "add_pinned_support", "name": "Add Pinned Support", "icon": "△"},
            {"id": "add_roller_support", "name": "Add Roller Support", "icon": "○"},
            {"id": "add_fixed_support", "name": "Add Fixed Support", "icon": "■"},
            {"id": "add_point_load", "name": "Add Point Load", "icon": "↓"},
            {"id": "add_distributed_load", "name": "Add Distributed Load", "icon": "⇓"},
            {"id": "delete", "name": "Delete", "icon": "✕"}
        ]
        
        # Create buttons for each tool
        self.tool_buttons = {}
        for tool in self.tools:
            # Using default parameter in lambda to capture the current value of tool['id']
            button = ttk.Button(
                self, 
                text=f"{tool['icon']} {tool['name']}",
                command=lambda t=tool['id']: self.select_tool(t)
            )
            button.pack(fill=tk.X, padx=5, pady=2)
            self.tool_buttons[tool['id']] = button
            
        # Highlight the initially selected tool
        self._update_button_states()

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