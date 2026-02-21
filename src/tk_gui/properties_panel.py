import tkinter as tk
from tkinter import ttk


class PropertiesPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.item_data = None
        self.config_data = None
        self.property_widgets = {}
        
        # Create a label for the panel
        label = ttk.Label(self, text="Properties", font=("Helvetica", 12, "bold"))
        label.pack(pady=5)
        
        # Create a canvas and scrollbar for the properties
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind canvas resizing
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        """Handle canvas resize events."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def show_properties(self, item_data, config_data):
        """Display properties for the selected item."""
        self.item_data = item_data
        self.config_data = config_data
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.property_widgets = {}
        
        if not item_data:
            # Show a message when no item is selected
            label = ttk.Label(self.scrollable_frame, text="No item selected")
            label.pack(pady=20)
            return
            
        # Show item type
        item_type = item_data.get("type", "Unknown")
        type_label = ttk.Label(self.scrollable_frame, text=f"Type: {item_type}", font=("Helvetica", 10, "bold"))
        type_label.pack(pady=5)
        
        # Show specific properties based on item type
        data = item_data.get("data", {})
        if data:
            # Create property editors for each field in the data
            for key, value in data.items():
                self._create_property_editor(key, value)
        else:
            # If no specific data, show generic properties
            for key, value in item_data.items():
                # Skip internal properties
                if key not in ["type", "color", "index", "subindex"]:
                    self._create_property_editor(key, value)
                    
        # Add a save button
        save_btn = ttk.Button(self.scrollable_frame, text="Apply Changes", command=self._apply_changes)
        save_btn.pack(pady=10)

    def _create_property_editor(self, key, value):
        """Create an editor widget for a property."""
        # Skip internal properties
        if key in ["index", "subindex"]:
            return
            
        # Create a frame for this property
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Create label
        label = ttk.Label(frame, text=f"{key}:", width=15, anchor="w")
        label.pack(side=tk.LEFT)
        
        # Create editor based on value type and key
        if isinstance(value, bool):
            # Checkbox for boolean values
            var = tk.BooleanVar(value=value)
            editor = ttk.Checkbutton(frame, variable=var)
        elif key == "type":
            # For type properties, use a readonly combobox
            var = tk.StringVar(value=str(value))
            editor = ttk.Combobox(frame, textvariable=var, state="readonly", 
                                values=["pinned", "roller", "fixed", "point", "distributed"])
            editor.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        elif isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
            # Spinbox for numeric values (including string representations of numbers)
            try:
                numeric_value = float(value)
                var = tk.DoubleVar(value=numeric_value)
                editor = ttk.Spinbox(frame, textvariable=var, from_=-1000000, to=1000000, increment=0.1)
            except ValueError:
                # Fallback to entry for non-numeric strings
                var = tk.StringVar(value=str(value))
                editor = ttk.Entry(frame, textvariable=var)
        else:
            # Entry for string values
            var = tk.StringVar(value=str(value))
            editor = ttk.Entry(frame, textvariable=var)
            
        editor.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Store reference to the variable
        self.property_widgets[key] = var

    def _apply_changes(self):
        """Apply changes to the item data."""
        if not self.item_data or not self.config_data:
            return
            
        # Get item information
        item_type = self.item_data.get("type", "")
        index = self.item_data.get("index", -1)
        data = self.item_data.get("data", {})
        
        # Validate index
        if index < 0:
            return
            
        # Update item data with new values
        updated_values = {}
        for key, var in self.property_widgets.items():
            if isinstance(var, tk.BooleanVar):
                new_value = var.get()
            elif isinstance(var, tk.DoubleVar):
                # Try to preserve the original type
                original_value = data.get(key) if data else self.item_data.get(key)
                if isinstance(original_value, int):
                    new_value = int(var.get())
                else:
                    new_value = var.get()
            else:
                # For string values, try to convert to appropriate type
                str_value = var.get()
                # Try to convert to number if possible
                if str_value.replace('.', '', 1).isdigit():
                    new_value = float(str_value) if '.' in str_value else int(str_value)
                else:
                    new_value = str_value
                    
            updated_values[key] = new_value
        
        # Update the configuration data
        if item_type == "support" and index < len(self.config_data.get("supports", [])):
            support = self.config_data["supports"][index]
            for key, value in updated_values.items():
                support[key] = value
        elif item_type == "load" and index < len(self.config_data.get("loads", [])):
            load = self.config_data["loads"][index]
            for key, value in updated_values.items():
                load[key] = value
                
        # Notify parent of changes and redraw canvas
        if hasattr(self.master.master, 'beam_canvas'):
            self.master.master.beam_canvas.set_config(self.master.master.current_config)
            self.master.master.status_var.set("Changes applied successfully")

    def get_property(self, key):
        """Get the current value of a property."""
        if key in self.property_widgets:
            var = self.property_widgets[key]
            if isinstance(var, tk.BooleanVar):
                return var.get()
            elif isinstance(var, tk.DoubleVar):
                return var.get()
            else:
                return var.get()
        return None