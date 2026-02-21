import tkinter as tk
from tkinter import Canvas
import logging


class ImprovedBeamCanvas(tk.Frame):
    def __init__(self, parent, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.canvas = Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Reference to the main window for callbacks
        self.main_window = None
        
        # Bind events
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # Drawing parameters
        self.padding = 50
        self.beam_y = 200  # Y position of the beam
        self.scale = 1.0   # Scale factor for drawing
        
        # Item tracking
        self.items = {}  # Maps item IDs to their data
        self.selected_item = None
        
        # Mouse position tracking
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Draw initial beam if config is provided
        if self.config:
            self.draw_beam()

    def set_main_window(self, main_window):
        """Set the reference to the main window for callbacks."""
        self.main_window = main_window

    def set_config(self, config):
        """Set the configuration and redraw the beam."""
        self.config = config
        self.draw_beam()

    def on_resize(self, event):
        """Handle canvas resize events."""
        self.draw_beam()

    def on_mouse_move(self, event):
        """Track mouse position for better user feedback."""
        self.mouse_x = event.x
        self.mouse_y = event.y
        
        # Update status with position info when adding elements
        if self.main_window and hasattr(self.main_window, 'toolbox'):
            selected_tool = self.main_window.toolbox.get_selected_tool()
            if selected_tool in ["add_pinned_support", "add_roller_support", "add_fixed_support", 
                               "add_point_load", "add_distributed_load"]:
                if self.config:
                    beam_length = float(self.config.get('beam_properties', {}).get('length', 10))
                    if beam_length > 0:
                        # Convert canvas x position to beam position
                        position = (self.mouse_x - self.padding) / self.scale
                        # Make sure position is within beam bounds
                        position = max(0, min(position, beam_length))
                        self.main_window.status_var.set(f"Position: {position:.2f}m")

    def on_click(self, event):
        """Handle mouse click events."""
        # Check if a tool is selected that requires adding elements
        if self.main_window and hasattr(self.main_window, 'toolbox'):
            selected_tool = self.main_window.toolbox.get_selected_tool()
            
            # Handle adding new elements
            if selected_tool in ["add_pinned_support", "add_roller_support", "add_fixed_support", 
                               "add_point_load", "add_distributed_load"]:
                self.add_element_at_position(event.x, event.y, selected_tool)
                return
                
        # Find all items near the click (within 10 pixels)
        items = self.canvas.find_overlapping(event.x-10, event.y-10, event.x+10, event.y+10)
        
        # Select the first item that's part of our beam elements
        for item_id in items:
            if item_id in self.items:
                self.select_item(item_id)
                return
                
        # If no items found, deselect
        self.deselect_item()

    def add_element_at_position(self, x, y, tool_id):
        """Add a new element at the clicked position."""
        if not self.config or not self.main_window:
            return
            
        # Calculate beam length and position
        beam_length = float(self.config.get('beam_properties', {}).get('length', 10))
        if beam_length <= 0:
            return
            
        # Convert canvas x position to beam position
        position = (x - self.padding) / self.scale
        
        # Make sure position is within beam bounds
        position = max(0, min(position, beam_length))
        
        # Add element based on tool
        if tool_id == "add_pinned_support":
            self.main_window.add_support("pinned", position)
        elif tool_id == "add_roller_support":
            self.main_window.add_support("roller", position)
        elif tool_id == "add_fixed_support":
            self.main_window.add_support("fixed", position)
        elif tool_id == "add_point_load":
            # For loads, we'll use a default magnitude
            self.main_window.add_load("point", -1000, position=position)
        elif tool_id == "add_distributed_load":
            # For distributed loads, we'll use a default range
            start = max(0, position - 1)
            end = min(beam_length, position + 1)
            self.main_window.add_load("distributed", -500, start=start, end=end)

    def draw_beam(self):
        """Draw the beam and all elements based on the current configuration."""
        # Clear the canvas and item tracking
        self.canvas.delete("all")
        self.items = {}
        
        if not self.config:
            return
            
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # If window is not yet sized, use requested dimensions
        if width <= 1 or height <= 1:
            width = 800
            height = 400
            
        # Calculate scale based on beam length and canvas width
        beam_length = float(self.config.get('beam_properties', {}).get('length', 10))
        self.scale = (width - 2 * self.padding) / beam_length if beam_length > 0 else 1.0
        
        # Draw the beam
        self.draw_beam_line(width, height)
        
        # Draw supports
        self.draw_supports(width, height)
        
        # Draw loads
        self.draw_loads(width, height)
        
        # Draw position indicator when adding elements
        if self.main_window and hasattr(self.main_window, 'toolbox'):
            selected_tool = self.main_window.toolbox.get_selected_tool()
            if selected_tool in ["add_pinned_support", "add_roller_support", "add_fixed_support", 
                               "add_point_load", "add_distributed_load"]:
                self.draw_position_indicator()

    def draw_position_indicator(self):
        """Draw a vertical line to indicate current mouse position."""
        if self.config:
            beam_length = float(self.config.get('beam_properties', {}).get('length', 10))
            if beam_length > 0:
                # Convert mouse position to beam position
                position = (self.mouse_x - self.padding) / self.scale
                # Make sure position is within beam bounds
                position = max(0, min(position, beam_length))
                # Convert back to canvas position
                x = self.padding + position * self.scale
                # Draw vertical line
                self.canvas.create_line(x, 20, x, self.beam_y * 2 - 20, 
                                       fill="blue", dash=(2, 4), width=1)

    def select_item(self, item_id):
        """Select an item and highlight it."""
        # Deselect previous item
        self.deselect_item()
        
        # Highlight the new item
        item_type = self.items[item_id].get("type", "")
        if item_type == "beam":
            self.canvas.itemconfig(item_id, fill="orange")
        else:
            # For supports and loads, we need to handle all related items
            item_data = self.items.get(item_id)
            if item_data:
                # Find all items with the same index (for composite elements like roller supports)
                index = item_data.get("index")
                for id_key, data in self.items.items():
                    if data.get("index") == index and data.get("type") == item_type:
                        if item_type == "support":
                            self.canvas.itemconfig(id_key, outline="orange", width=3)
                        elif item_type == "load":
                            self.canvas.itemconfig(id_key, fill="orange")
            
        self.selected_item = item_id
        
        # Notify parent about selection
        item_data = self.items.get(item_id)
        if item_data and self.main_window:
            self.main_window.on_canvas_selection_changed(item_data)

    def deselect_item(self):
        """Deselect the current item."""
        if self.selected_item:
            # Restore original appearance
            item_data = self.items.get(self.selected_item)
            if item_data:
                item_type = item_data.get("type", "")
                index = item_data.get("index")
                
                # Find all items with the same index (for composite elements)
                for id_key, data in self.items.items():
                    if data.get("index") == index and data.get("type") == item_type:
                        original_color = data.get("color", "black")
                        original_width = data.get("width", 1)
                        
                        if item_type == "beam":
                            self.canvas.itemconfig(id_key, fill=original_color)
                        elif item_type == "support":
                            # For supports, we need to handle the different parts
                            self.canvas.itemconfig(id_key, outline=original_color, width=original_width)
                        elif item_type == "load":
                            # For loads, we need to handle the different parts
                            self.canvas.itemconfig(id_key, fill=original_color)
                    
            self.selected_item = None
            # Notify that selection was cleared
            if self.main_window:
                self.main_window.on_canvas_selection_changed(None)

    def get_selected_item_data(self):
        """Get the data for the currently selected item."""
        if self.selected_item and self.selected_item in self.items:
            return self.items[self.selected_item]
        return None

    def delete_selected_item(self):
        """Delete the currently selected item."""
        if not self.selected_item or self.selected_item not in self.items:
            return False
            
        # Get item data
        item_data = self.items[self.selected_item]
        item_type = item_data.get("type", "")
        index = item_data.get("index", -1)
        
        # Delete all items with the same index (for composite elements like roller supports)
        items_to_delete = []
        for item_id, data in self.items.items():
            if data.get("index") == index and data.get("type") == item_type:
                items_to_delete.append(item_id)
        
        # Remove from canvas
        for item_id in items_to_delete:
            self.canvas.delete(item_id)
            del self.items[item_id]
            
        # Remove from config
        if self.config:
            if item_type == "support" and index < len(self.config.get("supports", [])):
                self.config["supports"].pop(index)
            elif item_type == "load" and index < len(self.config.get("loads", [])):
                self.config["loads"].pop(index)
                
        # Clear selection
        self.selected_item = None
        
        # Notify that selection was cleared
        if self.main_window:
            self.main_window.on_canvas_selection_changed(None)
            
        return True

    def draw_beam_line(self, width, height):
        """Draw the main beam line."""
        x1 = self.padding
        x2 = width - self.padding
        self.beam_y = height // 2
        
        # Draw beam
        beam_id = self.canvas.create_line(x1, self.beam_y, x2, self.beam_y, 
                                         width=8, fill="black", tags="beam")
        # Track the beam item
        self.items[beam_id] = {
            "type": "beam",
            "color": "black"
        }

    def draw_supports(self, width, height):
        """Draw all supports based on configuration."""
        beam_length = float(self.config.get('beam_properties', {}).get('length', 10))
        if beam_length <= 0:
            return
            
        supports = self.config.get('supports', [])
        for i, support in enumerate(supports):
            pos = float(support.get('position', 0))
            support_type = support.get('type', 'pinned')
            
            # Calculate x position
            x = self.padding + pos * self.scale
            
            if support_type == 'pinned':
                item_ids = self.draw_pinned_support(x, self.beam_y)
            elif support_type == 'roller':
                item_ids = self.draw_roller_support(x, self.beam_y)
            elif support_type == 'fixed':
                item_ids = self.draw_fixed_support(x, self.beam_y, width, height)
                
            # Track the support items
            for item_id in item_ids:
                self.items[item_id] = {
                    "type": "support",
                    "index": i,
                    "subindex": item_ids.index(item_id),
                    "data": support.copy(),
                    "color": "red" if support_type != 'fixed' else "black",
                    "width": 2
                }

    def draw_pinned_support(self, x, y):
        """Draw a pinned support."""
        # Triangle for pinned support
        size = 20
        points = [
            x, y + size,      # Bottom point
            x - size, y - size,  # Left point
            x + size, y - size   # Right point
        ]
        item_id = self.canvas.create_polygon(points, fill="red", outline="black", width=2, tags="support")
        return [item_id]

    def draw_roller_support(self, x, y):
        """Draw a roller support."""
        # Rectangle for roller support
        size = 20
        rect_id = self.canvas.create_rectangle(x - size, y - size, x + size, y + size,
                                              fill="white", outline="red", width=3, tags="support")
        
        # Small circle to indicate roller
        circle_id = self.canvas.create_oval(x - 7, y + size - 7, x + 7, y + size + 7,
                                           fill="red", outline="red", tags="support")
        return [rect_id, circle_id]

    def draw_fixed_support(self, x, y, width, height):
        """Draw a fixed support."""
        # Rectangle for fixed support
        support_width = 25
        rect_id = self.canvas.create_rectangle(x, y - 35, x + support_width, y + 35,
                                              fill="gray", outline="black", width=2, tags="support")
        return [rect_id]

    def draw_loads(self, width, height):
        """Draw all loads based on configuration."""
        beam_length = float(self.config.get('beam_properties', {}).get('length', 10))
        if beam_length <= 0:
            return
            
        loads = self.config.get('loads', [])
        for i, load in enumerate(loads):
            load_type = load.get('type', 'point')
            magnitude = float(load.get('magnitude', 0))
            
            # Only draw if magnitude is non-zero
            if magnitude == 0:
                continue
                
            # Determine color based on magnitude (negative = downward)
            color = "blue" if magnitude < 0 else "red"
            
            item_ids = []
            if load_type == 'point':
                pos = float(load.get('position', 0))
                x = self.padding + pos * self.scale
                item_ids = self.draw_point_load(x, self.beam_y - 40, magnitude, color)
                
            elif load_type == 'distributed':
                start = float(load.get('start', 0))
                end = float(load.get('end', 0))
                x1 = self.padding + start * self.scale
                x2 = self.padding + end * self.scale
                item_ids = self.draw_distributed_load(x1, x2, self.beam_y - 40, magnitude, color)
                
            # Track the load items
            for item_id in item_ids:
                self.items[item_id] = {
                    "type": "load",
                    "index": i,
                    "subindex": item_ids.index(item_id),
                    "data": load.copy(),
                    "color": color
                }

    def draw_point_load(self, x, y, magnitude, color):
        """Draw a point load."""
        item_ids = []
        # Arrow for point load
        arrow_length = 50 if magnitude < 0 else -50
        arrow_id = self.canvas.create_line(x, y, x, y - arrow_length,
                                          arrow=tk.LAST, fill=color, width=4, tags="load")
        item_ids.append(arrow_id)
        
        # Label
        label_id = self.canvas.create_text(x, y - arrow_length - 15, text=f"{abs(magnitude):.0f}N",
                                          fill=color, font=("Arial", 10, "bold"), tags="load")
        item_ids.append(label_id)
        return item_ids

    def draw_distributed_load(self, x1, x2, y, magnitude, color):
        """Draw a distributed load."""
        item_ids = []
        # Draw distributed load as series of arrows
        length = abs(x2 - x1)
        num_arrows = max(3, int(length / 40))  # At least 3 arrows, more for longer loads
        step = length / (num_arrows - 1) if num_arrows > 1 else 0
        
        arrow_length = 50 if magnitude < 0 else -50
        
        for i in range(num_arrows):
            x = x1 + i * step
            arrow_id = self.canvas.create_line(x, y, x, y - arrow_length,
                                              arrow=tk.LAST, fill=color, width=3, tags="load")
            item_ids.append(arrow_id)
        
        # Draw connecting line at top
        line_id = self.canvas.create_line(x1, y - arrow_length, x2, y - arrow_length,
                                         fill=color, width=3, tags="load")
        item_ids.append(line_id)
        
        # Label
        mid_x = (x1 + x2) / 2
        label_id = self.canvas.create_text(mid_x, y - arrow_length - 20, 
                                          text=f"{abs(magnitude):.0f}N/m",
                                          fill=color, font=("Arial", 10, "bold"), tags="load")
        item_ids.append(label_id)
        return item_ids