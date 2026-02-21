import tkinter as tk
from tkinter import ttk


class ImprovedPropertiesPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Properties.TFrame')
        self.item_data = None
        self.config_data = None
        self.property_widgets = {}
        self.main_window = None  # Reference to main window for callbacks
        
        # Create a label for the panel
        label = ttk.Label(self, text="Properties", font=("Helvetica", 12, "bold"))
        label.pack(pady=10)
        
        # Create a canvas and scrollbar for the properties
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg='#f0f0f0')
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
        
        # Bind mousewheel to scroll
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

    def set_main_window(self, main_window):
        """Set reference to main window for callbacks."""
        self.main_window = main_window

    def _on_canvas_configure(self, event):
        """Handle canvas resize events."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

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
            label = ttk.Label(self.scrollable_frame, text="No item selected", 
                             font=("Helvetica", 10))
            label.pack(pady=20)
            return
            
        # Show item type with better formatting
        item_type = item_data.get("type", "Unknown")
        type_frame = ttk.LabelFrame(self.scrollable_frame, text="Item Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        type_label = ttk.Label(type_frame, text=item_type.title(), 
                              font=("Helvetica", 12, "bold"))
        type_label.pack()
        
        # Show specific properties based on item type
        data = item_data.get("data", {})
        if data:
            # Create property editors for each field in the data
            self._create_properties_section("Properties", data, item_type)
        else:
            # If no specific data, show generic properties
            generic_props = {k: v for k, v in item_data.items() 
                           if k not in ["type", "color", "index", "subindex"]}
            if generic_props:
                self._create_properties_section("Properties", generic_props, item_type)
                
        # Add a save button
        save_btn = ttk.Button(self.scrollable_frame, text="Apply Changes", 
                             command=self._apply_changes, style='Primary.TButton')
        save_btn.pack(pady=15, padx=10, fill=tk.X)

    def _create_properties_section(self, section_name, properties, item_type):
        """Create a section for properties."""
        section_frame = ttk.LabelFrame(self.scrollable_frame, text=section_name, padding=10)
        section_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for key, value in properties.items():
            # Skip internal properties
            if key in ["index", "subindex"]:
                continue
            # Special handling for point loads to add direction control
            if item_type == "load" and key == "magnitude" and properties.get("type") == "point":
                self._create_point_load_properties(section_frame, properties)
            else:
                self._create_property_editor(section_frame, key, value)

    def _create_point_load_properties(self, parent, properties):
        """Create special properties for point loads including direction control."""
        magnitude = properties.get("magnitude", 0)
        
        # Create magnitude editor
        mag_frame = ttk.Frame(parent)
        mag_frame.pack(fill=tk.X, pady=3)
        
        mag_label = ttk.Label(mag_frame, text="Magnitude:", width=15, anchor="w")
        mag_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Use absolute value for the spinbox
        try:
            mag_value = abs(float(magnitude))
            var = tk.DoubleVar(value=mag_value)
            editor = ttk.Spinbox(mag_frame, textvariable=var, from_=0, to=1000000, 
                               increment=100, width=20)
            editor.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            # Bind to update canvas when changed
            var.trace_add("write", lambda *args: self._on_point_load_magnitude_changed())
            self.property_widgets["magnitude"] = var
        except ValueError:
            # Fallback to entry for non-numeric values
            var = tk.StringVar(value=str(abs(magnitude)))
            editor = ttk.Entry(mag_frame, textvariable=var, width=20)
            editor.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            # Bind to update canvas when changed
            var.trace_add("write", lambda *args: self._on_point_load_magnitude_changed())
            self.property_widgets["magnitude"] = var
        
        # Create direction editor
        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill=tk.X, pady=3)
        
        dir_label = ttk.Label(dir_frame, text="Direction:", width=15, anchor="w")
        dir_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Determine current direction
        current_dir = "Down" if float(magnitude) < 0 else "Up"
        dir_var = tk.StringVar(value=current_dir)
        dir_editor = ttk.Combobox(dir_frame, textvariable=dir_var, state="readonly",
                                values=["Up", "Down"], width=20)
        dir_editor.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        # Bind to update canvas when changed
        dir_var.trace_add("write", lambda *args: self._on_point_load_direction_changed())
        self.property_widgets["direction"] = dir_var

    def _create_property_editor(self, parent, key, value):
        """Create an editor widget for a property."""
        # Create a frame for this property
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=3)
        
        # Create label with better formatting
        label = ttk.Label(frame, text=f"{key.replace('_', ' ').title()}:", 
                         width=15, anchor="w")
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create editor based on value type and key
        if isinstance(value, bool):
            # Checkbox for boolean values
            var = tk.BooleanVar(value=value)
            editor = ttk.Checkbutton(frame, variable=var)
            # Bind to update canvas when changed
            var.trace_add("write", lambda *args, k=key: self._on_property_changed(k))
        elif key == "type":
            # For type properties, use a readonly combobox
            var = tk.StringVar(value=str(value))
            editor = ttk.Combobox(frame, textvariable=var, state="readonly", 
                                values=["pinned", "roller", "fixed", "point", "distributed"],
                                width=20)
            # Bind to update canvas when changed
            var.trace_add("write", lambda *args, k=key: self._on_property_changed(k))
        elif isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
            # Spinbox for numeric values (including string representations of numbers)
            try:
                numeric_value = float(value)
                var = tk.DoubleVar(value=numeric_value)
                editor = ttk.Spinbox(frame, textvariable=var, from_=-1000000, to=1000000, 
                                   increment=0.1, width=20)
                # Bind to update canvas when changed
                var.trace_add("write", lambda *args, k=key: self._on_property_changed(k))
            except ValueError:
                # Fallback to entry for non-numeric strings
                var = tk.StringVar(value=str(value))
                editor = ttk.Entry(frame, textvariable=var, width=20)
                # Bind to update canvas when changed
                var.trace_add("write", lambda *args, k=key: self._on_property_changed(k))
        else:
            # Entry for string values
            var = tk.StringVar(value=str(value))
            editor = ttk.Entry(frame, textvariable=var, width=20)
            # Bind to update canvas when changed
            var.trace_add("write", lambda *args, k=key: self._on_property_changed(k))
            
        editor.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Store reference to the variable
        self.property_widgets[key] = var

    def _on_point_load_magnitude_changed(self):
        """Callback when point load magnitude changes."""
        self._apply_point_load_changes()

    def _on_point_load_direction_changed(self):
        """Callback when point load direction changes."""
        self._apply_point_load_changes()

    def _apply_point_load_changes(self):
        """Apply changes to point load properties."""
        if not self.item_data or not self.config_data:
            return
            
        # Get item information
        item_type = self.item_data.get("type", "")
        index = self.item_data.get("index", -1)
        
        # Validate index and type
        if index < 0 or item_type != "load":
            return
            
        # Get magnitude and direction values
        magnitude_var = self.property_widgets.get("magnitude")
        direction_var = self.property_widgets.get("direction")
        
        if not magnitude_var or not direction_var:
            return
            
        try:
            # Get magnitude value
            if isinstance(magnitude_var, tk.DoubleVar):
                magnitude = magnitude_var.get()
            else:
                magnitude = float(magnitude_var.get())
                
            # Get direction value
            direction = direction_var.get()
            
            # Apply direction (negative for down, positive for up)
            if direction == "Down":
                magnitude = -abs(magnitude)
            else:
                magnitude = abs(magnitude)
                
            # Update the configuration data
            if index < len(self.config_data.get("loads", [])):
                load = self.config_data["loads"][index]
                load["magnitude"] = magnitude
                
                # Notify parent of changes and redraw canvas
                if self.main_window and hasattr(self.main_window, 'beam_canvas'):
                    self.main_window.beam_canvas.set_config(self.main_window.current_config)
                    self.main_window.status_var.set("Point load updated")
        except ValueError:
            # Handle conversion errors
            pass

    def _on_property_changed(self, key):
        """Callback when a property value changes."""
        # Apply changes immediately for the specific property that changed
        self._apply_single_change(key)

    def _apply_single_change(self, changed_key):
        """Apply a single property change to the item data and update canvas."""
        if not self.item_data or not self.config_data:
            return
            
        # Get item information
        item_type = self.item_data.get("type", "")
        index = self.item_data.get("index", -1)
        data = self.item_data.get("data", {})
        
        # Validate index
        if index < 0:
            return
            
        # Get the changed value
        var = self.property_widgets.get(changed_key)
        if not var:
            return
            
        if isinstance(var, tk.BooleanVar):
            new_value = var.get()
        elif isinstance(var, tk.DoubleVar):
            # Try to preserve the original type
            original_value = data.get(changed_key) if data else self.item_data.get(changed_key)
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
        
        # Update the configuration data
        if item_type == "support" and index < len(self.config_data.get("supports", [])):
            support = self.config_data["supports"][index]
            support[changed_key] = new_value
        elif item_type == "load" and index < len(self.config_data.get("loads", [])):
            load = self.config_data["loads"][index]
            load[changed_key] = new_value
                
        # Notify parent of changes and redraw canvas
        if self.main_window and hasattr(self.main_window, 'beam_canvas'):
            self.main_window.beam_canvas.set_config(self.main_window.current_config)
            self.main_window.status_var.set(f"Updated {changed_key}")

    def _apply_changes(self):
        """Apply all changes to the item data."""
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
            # Skip special properties handled separately
            if key in ["direction"]:
                continue
                
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
        if self.main_window and hasattr(self.main_window, 'beam_canvas'):
            self.main_window.beam_canvas.set_config(self.main_window.current_config)
            self.main_window.status_var.set("Changes applied successfully")

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