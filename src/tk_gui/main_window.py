import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os
import yaml
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd

from ..main import run_pipeline as run_analysis_pipeline
from ..utils.config_loader import load_config
from .beam_canvas import BeamCanvas
from .toolbox import Toolbox
from .properties_panel import PropertiesPanel


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Civil Engineering Workbench")
        self.root.geometry("1600x900")
        
        self.current_config_path = "config.yaml"
        self.current_config = {}
        
        # Create widgets
        self._create_widgets()
        self._create_menu()
        self._connect_signals()
        
        # Load initial config
        self.load_initial_config()
        
        # Set status
        self.status_var.set("Ready")

    def _create_widgets(self):
        # Create a main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create toolbar
        self._create_toolbar(main_frame)
        
        # Create the main content area with panels
        self._create_main_content(main_frame)
        
        # Create log frame at bottom
        self._create_log_frame(main_frame)
        
        # Create status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_toolbar(self, parent):
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Open button
        self.open_btn = ttk.Button(toolbar_frame, text="Open Config", command=self.open_config_file)
        self.open_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save button
        self.save_btn = ttk.Button(toolbar_frame, text="Save Config", command=self.save_config_file)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Run button
        self.run_btn = ttk.Button(toolbar_frame, text="Run Analysis", command=self.start_analysis)
        self.run_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        separator = ttk.Separator(toolbar_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 10))
        
        # Toolbox toggle
        self.toolbox_visible = tk.BooleanVar(value=True)
        self.toolbox_check = ttk.Checkbutton(toolbar_frame, text="Toolbox", variable=self.toolbox_visible, 
                                           command=self.toggle_toolbox)
        self.toolbox_check.pack(side=tk.LEFT, padx=(0, 5))
        
        # Properties toggle
        self.properties_visible = tk.BooleanVar(value=True)
        self.properties_check = ttk.Checkbutton(toolbar_frame, text="Properties", variable=self.properties_visible,
                                              command=self.toggle_properties)
        self.properties_check.pack(side=tk.LEFT, padx=(0, 5))
        
        # Log viewer toggle
        self.log_visible = tk.BooleanVar(value=False)
        self.log_check = ttk.Checkbutton(toolbar_frame, text="Logs", variable=self.log_visible,
                                       command=self.toggle_logs)
        self.log_check.pack(side=tk.LEFT, padx=(0, 5))

    def _create_main_content(self, parent):
        # Create a frame for the main content area
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create toolbox panel (left)
        self.toolbox = Toolbox(content_frame)
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Create main canvas area
        canvas_container = ttk.Frame(content_frame)
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs (canvas and plots)
        self.notebook = ttk.Notebook(canvas_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas tab
        self.canvas_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.canvas_frame, text="Beam Canvas")
        self._create_canvas(self.canvas_frame)
        
        # Create properties panel (right)
        self.properties_panel = PropertiesPanel(content_frame)
        self.properties_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Initialize panel visibility
        self.toggle_toolbox()
        self.toggle_properties()

    def _create_canvas(self, parent):
        # Create the beam canvas
        self.beam_canvas = BeamCanvas(parent)
        self.beam_canvas.set_main_window(self)  # Set reference to main window for callbacks
        self.beam_canvas.pack(expand=True, fill=tk.BOTH)

    def _create_log_frame(self, parent):
        # Create log frame (initially hidden)
        self.log_frame = ttk.Frame(parent, height=150)
        self.log_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Create log text widget with scrollbar
        log_frame_inner = ttk.Frame(self.log_frame)
        log_frame_inner.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame_inner, wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame_inner, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pack log frame if initially visible
        if self.log_visible.get():
            self.log_frame.pack(fill=tk.X, pady=(5, 0))

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Config...", command=self.open_config_file)
        file_menu.add_command(label="Save Config", command=self.save_config_file)
        file_menu.add_command(label="Save Config As...", command=self.save_config_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Analysis", command=self.start_analysis)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Toolbox", variable=self.toolbox_visible, command=self.toggle_toolbox)
        view_menu.add_checkbutton(label="Properties Panel", variable=self.properties_visible, command=self.toggle_properties)
        view_menu.add_checkbutton(label="Log Viewer", variable=self.log_visible, command=self.toggle_logs)

    def _connect_signals(self):
        # Connect toolbox tool selection event to handler
        self.toolbox.set_tool_callback(self.on_tool_selected)

    def load_initial_config(self):
        if os.path.exists(self.current_config_path):
            self.current_config = load_config(self.current_config_path)
            if self.current_config:
                self.beam_canvas.set_config(self.current_config)
                self.update_window_title()
                self.start_analysis()  # Auto-run on load

    def update_window_title(self):
        self.root.title(f"Civil Engineering Workbench - {os.path.basename(self.current_config_path)}")

    def open_config_file(self):
        path = filedialog.askopenfilename(
            title="Open Config",
            filetypes=[("YAML Files", "*.yaml *.yml"), ("All Files", "*.*")]
        )
        if path:
            self.current_config_path = path
            self.current_config = load_config(path)
            if self.current_config:
                self.beam_canvas.set_config(self.current_config)
                self.update_window_title()
                self.start_analysis()  # Auto-run on load

    def save_config_file(self):
        if self.current_config_path:
            self._save_to_path(self.current_config_path)
        else:
            self.save_config_file_as()

    def save_config_file_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Config As",
            defaultextension=".yaml",
            filetypes=[("YAML Files", "*.yaml *.yml"), ("All Files", "*.*")]
        )
        if path:
            self.current_config_path = path
            self._save_to_path(path)
            self.update_window_title()

    def _save_to_path(self, path):
        try:
            with open(path, 'w') as f:
                yaml.dump(self.current_config, f, default_flow_style=False, sort_keys=False)
            self.status_var.set(f"Configuration saved to {path}")
            # Show message for 5 seconds
            self.root.after(5000, lambda: self.status_var.set("Ready") if "Configuration saved" in self.status_var.get() else None)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save configuration file:\n{e}")

    def toggle_toolbox(self):
        if self.toolbox_visible.get():
            self.toolbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        else:
            self.toolbox.pack_forget()

    def toggle_properties(self):
        if self.properties_visible.get():
            self.properties_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        else:
            self.properties_panel.pack_forget()

    def toggle_logs(self):
        if self.log_visible.get():
            self.log_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.log_frame.pack_forget()

    def start_analysis(self):
        if not self.current_config:
            logging.warning("No configuration loaded. Skipping analysis.")
            return

        self.set_running_state(is_running=True)
        self.beam_canvas.set_config(self.current_config)  # Update canvas before running
        
        try:
            # Run the analysis directly (no threading for simplicity in this conversion)
            results = run_analysis_pipeline(self.current_config, gui_mode=True)
            self.on_analysis_result(results)
            self.on_analysis_finished()
        except Exception as e:
            self.on_analysis_error(e)

    def set_running_state(self, is_running):
        # Enable/disable buttons
        state = tk.DISABLED if is_running else tk.NORMAL
        self.run_btn.config(state=state)
        
        # Update status
        if is_running:
            self.status_var.set("Running analysis... Please wait.")
        else:
            self.status_var.set("Analysis complete.")

    def on_analysis_finished(self):
        self.set_running_state(is_running=False)

    def on_analysis_error(self, error):
        logging.error(f"An error occurred during the analysis: {error}")
        self.set_running_state(is_running=False)
        messagebox.showerror("Analysis Error", f"An error occurred during the analysis:\n\n{error}")

    def on_analysis_result(self, results):
        if not results:
            return
            
        # Clear existing tabs except the canvas
        for i in range(self.notebook.index("end")-1, 0, -1):
            self.notebook.forget(i)
            
        # Process results
        for name, result in results.items():
            if result['type'] == 'dataframe':
                self.add_dataframe_tab(result['data'], result['name'])
            elif result['type'] == 'plot':
                self.add_plot_tab(result['data'], result['params'], result['name'], result['config'])

    def add_dataframe_tab(self, data, name):
        # Create a new tab for the dataframe
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=name)
        
        # Create treeview for dataframe
        tree_frame = ttk.Frame(tab_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbar
        tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Configure columns
        df_display = data.round(3)
        columns = list(df_display.columns)
        tree["columns"] = columns
        tree["show"] = "headings"
        
        # Set column headings and widths
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        
        # Insert data
        for index, row in df_display.iterrows():
            tree.insert("", "end", values=list(row))
        
        # Pack widgets
        tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

    def add_plot_tab(self, data, params, name, config):
        # Create a new tab for the plot
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=name)
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        x_col, y_col = 'Position_m', params['y_col']
        
        if y_col not in data.columns:
            logging.error(f"Column '{y_col}' not found for plotting in GUI.")
            return

        # Main plot line and fill
        ax.plot(data[x_col], data[y_col], color='blue', zorder=2)
        ax.fill_between(data[x_col], data[y_col], 0, color='skyblue', alpha=0.4, zorder=2)
        
        self._draw_beam_and_supports(ax, config)

        # Customizations per plot type
        if y_col == 'Deflection_m':
            ax.invert_yaxis()
            idx_max = data[y_col].idxmin() if data[y_col].min() < 0 else data[y_col].idxmax()
            max_defl_val = data[y_col][idx_max]
            max_defl_pos = data[x_col][idx_max]
            ax.annotate(f'Max Deflection: {max_defl_val*1000:.2f} mm', 
                        xy=(max_defl_pos, max_defl_val), 
                        xytext=(max_defl_pos, max_defl_val * 0.5),
                        arrowprops=dict(facecolor='black', shrink=0.05),
                        ha='center', va='center')

        # General plot formatting
        ax.set_title(params.get('title', 'Plot'), weight='bold')
        ax.set_xlabel('Position along beam (m)')
        ax.set_ylabel(params.get('ylabel', 'Value'))
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.tight_layout()
        
        # Create canvas and pack it
        canvas = FigureCanvasTkAgg(fig, tab_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _draw_beam_and_supports(self, ax, config):
        """Helper to draw the beam and supports on a plot axis."""
        length = float(config.get('beam_properties', {}).get('length', 10))
        ax.axhline(0, color='black', linewidth=2.5, zorder=1)  # The beam itself
        
        ylim = ax.get_ylim()
        marker_size = (ylim[1] - ylim[0]) * 0.05  # 5% of y-axis range

        for support in config.get('supports', []):
            pos = float(support['position'])
            if support['type'] == 'pinned':
                ax.plot(pos, 0, '^', color='red', markersize=12, zorder=5, clip_on=False)
            elif support['type'] == 'roller':
                ax.plot(pos, 0, 'o', color='red', markersize=12, zorder=5, clip_on=False, mfc='white')
            elif support['type'] == 'fixed':
                ax.axvspan(pos-length*0.01, pos, facecolor='gray', alpha=0.7, zorder=0)

    def append_log(self, message):
        """Add a message to the log viewer."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
    def on_canvas_selection_changed(self, item_data):
        """Handle canvas selection changes and update properties panel."""
        if item_data:
            # Show properties for the selected item
            self.properties_panel.show_properties(item_data, self.current_config)
        else:
            # Clear properties panel when nothing is selected
            self.properties_panel.show_properties(None, self.current_config)

    def on_tool_selected(self, tool_id):
        """Handle tool selection from the toolbox."""
        # Handle the delete tool specifically
        if tool_id == "delete":
            if self.beam_canvas.delete_selected_item():
                self.status_var.set("Item deleted successfully")
                self.beam_canvas.draw_beam()  # Redraw to update the display
            else:
                self.status_var.set("No item selected for deletion")
        # For other tools, we would implement their functionality here
        # For now, we're just showing a status message
        elif tool_id != "select":
            self.status_var.set(f"Tool selected: {tool_id}")
            
    def add_support(self, support_type, position):
        """Add a new support to the configuration."""
        if not self.current_config:
            self.current_config = {"supports": [], "loads": []}
            
        # Add support to config
        new_support = {
            "type": support_type,
            "position": position
        }
        self.current_config.setdefault("supports", []).append(new_support)
        
        # Redraw canvas
        self.beam_canvas.set_config(self.current_config)
        self.status_var.set(f"Added {support_type} support at position {position}")
        
    def add_load(self, load_type, magnitude, position=None, start=None, end=None):
        """Add a new load to the configuration."""
        if not self.current_config:
            self.current_config = {"supports": [], "loads": []}
            
        # Add load to config
        new_load = {
            "type": load_type,
            "magnitude": magnitude
        }
        
        if load_type == "point" and position is not None:
            new_load["position"] = position
        elif load_type == "distributed" and start is not None and end is not None:
            new_load["start"] = start
            new_load["end"] = end
            
        self.current_config.setdefault("loads", []).append(new_load)
        
        # Redraw canvas
        self.beam_canvas.set_config(self.current_config)
        self.status_var.set(f"Added {load_type} load")