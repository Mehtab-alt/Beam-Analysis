import logging
import qtawesome as qta
import yaml
import os
import numpy as np
import logging
import qtawesome as qta
import yaml
import os
import numpy as np
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtWidgets import (QMainWindow, QDockWidget, QTabWidget, QTableView, 
                             QToolBar, QMessageBox, QFileDialog, QVBoxLayout, QWidget, QSplitter)
from PyQt6.QtCore import Qt, QThreadPool

from .log_viewer import LogViewer
from .worker import Worker
from .pandas_model import PandasModel
from .mpl_canvas import MplCanvas
from .beam_canvas import BeamCanvas
from .toolbox import Toolbox
from .properties_panel import PropertiesPanel

from ..main import run_pipeline as run_analysis_pipeline
from ..utils.config_loader import load_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Civil Engineering Workbench")
        self.setGeometry(100, 100, 1600, 900)
        self.threadpool = QThreadPool()
        self.current_config_path = "config.yaml"
        self.current_config = {}
        
        self._create_widgets()
        self._create_actions()
        self._create_toolbars()
        self._create_menus()
        self._create_docks()
        self._connect_signals()
        
        self.load_initial_config()
        self.statusBar().showMessage("Ready")
        self.show()
        # Ensure equal sizing of splitter on initial show
        self.central_splitter.setSizes([self.central_splitter.height() // 2, self.central_splitter.height() // 2])

    def _create_widgets(self):
        # --- Main Interactive Widgets ---
        self.beam_canvas = BeamCanvas()
        self.toolbox = Toolbox()
        self.properties_panel = PropertiesPanel()

        # --- Output and Logging Widgets ---
        self.log_viewer = LogViewer()
        self.plot_tabs = QTabWidget() # For plots and tables
        self.plot_tabs.setTabsClosable(True)

        # --- Layout Assembly ---
        # Central splitter for canvas and plots
        self.central_splitter = QSplitter(Qt.Orientation.Vertical)
        self.central_splitter.addWidget(self.beam_canvas)
        self.central_splitter.addWidget(self.plot_tabs)
        self.central_splitter.setStretchFactor(0, 1) # Make canvas and plots same size
        self.central_splitter.setStretchFactor(1, 1) # Make canvas and plots same size
        self.setCentralWidget(self.central_splitter)

    def _create_actions(self):
        self.open_action = QAction(qta.icon('fa5s.folder-open'), "&Open Config...", self)
        self.save_action = QAction(qta.icon('fa5s.save'), "&Save Config", self)
        self.save_as_action = QAction(qta.icon('fa5s.file-export'), "Save Config &As...", self)
        self.exit_action = QAction(qta.icon('fa5s.times-circle'), "&Exit", self)
        self.run_action = QAction(qta.icon('fa5s.play-circle'), "&Run Analysis", self)
        self.toggle_toolbox_action = QAction("Toolbox", self)
        self.toggle_toolbox_action.setCheckable(True)
        self.toggle_toolbox_action.setChecked(True)
        self.toggle_properties_action = QAction("Properties Panel", self)
        self.toggle_properties_action.setCheckable(True)
        self.toggle_properties_action.setChecked(True)
        self.toggle_log_viewer_action = QAction("Log Viewer", self)
        self.toggle_log_viewer_action.setCheckable(True)
        self.toggle_log_viewer_action.setChecked(False) # Hidden by default

    def _create_toolbars(self):
        self.main_toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.main_toolbar)
        self.main_toolbar.addAction(self.open_action)
        self.main_toolbar.addAction(self.save_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.run_action)

    def _create_menus(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        run_menu = menu.addMenu("&Run")
        run_menu.addAction(self.run_action)
        view_menu = menu.addMenu("&View")
        view_menu.addAction(self.toggle_toolbox_action)
        view_menu.addAction(self.toggle_properties_action)
        view_menu.addAction(self.toggle_log_viewer_action)

    def _create_docks(self):
        # Left dock for Toolbox
        self.toolbox_dock = QDockWidget("Toolbox", self)
        self.toolbox_dock.setWidget(self.toolbox)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.toolbox_dock)

        # Right dock for Properties Panel
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_dock)
        self.properties_dock.setFixedWidth(300) # Set a fixed width to prevent resizing affecting the canvas
        
        # Bottom dock for Logs
        self.log_dock = QDockWidget("Logs", self)
        self.log_dock.setWidget(self.log_viewer)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)
        self.log_dock.setVisible(False) # Initially hidden

    def _connect_signals(self):
        self.open_action.triggered.connect(self.open_config_file)
        self.save_action.triggered.connect(self.save_config_file)
        self.save_as_action.triggered.connect(self.save_config_file_as)
        self.exit_action.triggered.connect(self.close)
        self.run_action.triggered.connect(self.start_analysis)

        # View menu toggles
        self.toggle_toolbox_action.triggered.connect(self.toolbox_dock.setVisible)
        self.toolbox_dock.visibilityChanged.connect(self.toggle_toolbox_action.setChecked)
        self.toggle_properties_action.triggered.connect(self.properties_dock.setVisible)
        self.properties_dock.visibilityChanged.connect(self.toggle_properties_action.setChecked)
        self.toggle_log_viewer_action.triggered.connect(self.log_dock.setVisible)
        self.log_dock.visibilityChanged.connect(self.toggle_log_viewer_action.setChecked)

        # --- Connect Interactive Components ---
        self.toolbox.toolSelected.connect(self.beam_canvas.set_active_tool)
        self.beam_canvas.itemSelected.connect(self.on_canvas_item_selected)
        self.beam_canvas.requestAddItem.connect(self.on_add_item_requested)
        self.beam_canvas.requestDeleteItem.connect(self.on_delete_item_requested)
        self.properties_panel.propertyChanged.connect(self.on_property_changed)
        self.properties_panel.requestDeleteItem.connect(self.on_delete_item_requested)

        # Closing plot tabs
        self.plot_tabs.tabCloseRequested.connect(self.close_tab)

    def load_initial_config(self):
        if os.path.exists(self.current_config_path):
            self.current_config = load_config(self.current_config_path)
            if self.current_config:
                self.beam_canvas.set_config(self.current_config)
                self.update_window_title()
                self.start_analysis() # Auto-run on load

    def update_window_title(self):
        self.setWindowTitle(f"Civil Engineering Workbench - {os.path.basename(self.current_config_path)}")

    def open_config_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Config", "", "YAML Files (*.yaml *.yml)")
        if path:
            self.current_config_path = path
            self.current_config = load_config(path)
            if self.current_config:
                self.beam_canvas.set_config(self.current_config)
                self.update_window_title()
                self.start_analysis() # Auto-run on load

    def save_config_file(self):
        if self.current_config_path: self._save_to_path(self.current_config_path)
        else: self.save_config_file_as()

    def save_config_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Config As", "", "YAML Files (*.yaml *.yml)")
        if path:
            self.current_config_path = path
            self._save_to_path(path)
            self.update_window_title()
            
    def _save_to_path(self, path):
        try:
            with open(path, 'w') as f: yaml.dump(self.current_config, f, default_flow_style=False, sort_keys=False)
            self.statusBar().showMessage(f"Configuration saved to {path}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save configuration file:\n{e}")

    def on_canvas_item_selected(self, item_data):
        """
        Updates the properties panel when an item is selected on the canvas.
        """
        self.properties_panel.show_properties(item_data, self.current_config)

    def close_tab(self, index):
        widget = self.plot_tabs.widget(index)
        if widget: widget.deleteLater()
        self.plot_tabs.removeTab(index)

    def add_dataframe_tab(self, data, name, **kwargs):
        df_display = data.round(3)
        table_view = QTableView()
        model = PandasModel(df_display)
        table_view.setModel(model)
        table_view.resizeColumnsToContents()
        self.plot_tabs.addTab(table_view, name)
        self.plot_tabs.setCurrentWidget(table_view)

    def _draw_beam_and_supports(self, ax, config):
        """Helper to draw the beam and supports on a plot axis."""
        length = float(config.get('beam_properties', {}).get('length', 10))
        ax.axhline(0, color='black', linewidth=2.5, zorder=1) # The beam itself
        
        ylim = ax.get_ylim()
        marker_size = (ylim[1] - ylim[0]) * 0.05 # 5% of y-axis range

        for support in config.get('supports', []):
            pos = float(support['position'])
            if support['type'] == 'pinned':
                ax.plot(pos, 0, '^', color='red', markersize=12, zorder=5, clip_on=False)
            elif support['type'] == 'roller':
                ax.plot(pos, 0, 'o', color='red', markersize=12, zorder=5, clip_on=False, mfc='white')
            elif support['type'] == 'fixed':
                ax.axvspan(pos-length*0.01, pos, facecolor='gray', alpha=0.7, zorder=0)

    # FIX: Added **kwargs to accept unexpected arguments like 'type'.
    def add_plot_tab(self, data, params, name, config, **kwargs):
        plot_widget = MplCanvas(self)
        ax = plot_widget.axes
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
        plot_widget.figure.tight_layout()
        
        self.plot_tabs.addTab(plot_widget, name)
        self.plot_tabs.setCurrentWidget(plot_widget)
            
    def start_analysis(self):
        if not self.current_config:
            logging.warning("No configuration loaded. Skipping analysis.")
            return

        self.set_running_state(is_running=True)
        self.beam_canvas.set_config(self.current_config) # Update canvas before running
        self.plot_tabs.clear() # Clear previous results

        worker = Worker(run_analysis_pipeline, self.current_config, gui_mode=True)
        worker.signals.finished.connect(self.on_analysis_finished)
        worker.signals.error.connect(self.on_analysis_error)
        worker.signals.result.connect(self.on_analysis_result)
        self.threadpool.start(worker)
        
    def set_running_state(self, is_running):
        self.run_action.setEnabled(not is_running)
        self.statusBar().showMessage("Running analysis... Please wait." if is_running else "Analysis complete.")

    def on_analysis_finished(self):
        self.set_running_state(is_running=False)
        # Reset splitter sizes to ensure equal sizing
        self.central_splitter.setSizes([self.central_splitter.height() // 2, self.central_splitter.height() // 2])

    def on_analysis_error(self, err_tuple):
        exctype, value, tb = err_tuple
        logging.error(f"An error occurred in the analysis worker: {value}")
        self.set_running_state(is_running=False)
        QMessageBox.critical(self, "Analysis Error", f"An error occurred during the analysis:\n\n{value}")

    def on_analysis_result(self, results):
        for name, result in results.items():
            if result['type'] == 'dataframe':
                self.add_dataframe_tab(**result)
            elif result['type'] == 'plot':
                self.add_plot_tab(**result)

    def on_property_changed(self, item_data, key, new_value):
        """
        Handles updates when a property is changed in the PropertiesPanel.
        This is the core of the interactive loop.
        """
        if not item_data: return
        
        # Update the value in the master config dictionary
        item_data[key] = new_value

        # Handle special case where changing the 'type' requires restructuring
        if key == 'type':
            if new_value == 'point':
                item_data.pop('start', None)
                item_data.pop('end', None)
                if 'position' not in item_data: item_data['position'] = item_data.get('start', 0.0)
            elif new_value == 'distributed':
                item_data.pop('position', None)
                if 'start' not in item_data: item_data['start'] = item_data.get('position', 0.0)
                if 'end' not in item_data: item_data['end'] = item_data['start'] + 2.0

            # Refresh the properties panel to show the new fields
            self.properties_panel.show_properties(item_data, self.current_config)

        # Trigger a full re-analysis and repaint
        self.start_analysis()

    def on_add_item_requested(self, tool_id, position):
        """Adds a new item to the configuration based on a canvas click."""
        item_type = tool_id.replace('add_', '').replace('_load', '')

        new_item = {'type': item_type}
        
        if 'support' in tool_id or 'pinned' in tool_id or 'roller' in tool_id or 'fixed' in tool_id:
            new_item['type'] = tool_id.replace('add_', '')
            new_item['position'] = round(position, 2)
            self.current_config['supports'].append(new_item)
        
        elif 'point' in tool_id:
            new_item['magnitude'] = -10000.0
            new_item['position'] = round(position, 2)
            self.current_config['loads'].append(new_item)

        elif 'dist' in tool_id:
            new_item['type'] = 'distributed'
            new_item['magnitude'] = -5000.0
            new_item['start'] = round(position, 2)
            new_item['end'] = round(position + 2.0, 2)
            self.current_config['loads'].append(new_item)

        # After adding, switch back to the select tool for a better workflow
        self.toolbox.set_tool('select')
        self.start_analysis()

    def on_delete_item_requested(self, item_data):
        """Deletes an item that was clicked with the delete tool."""
        if not item_data: return

        # Find and remove the item from the appropriate list in the config
        for key in ['loads', 'supports']:
            if item_data in self.current_config.get(key, []):
                # Enforce minimum support rule
                if key == 'supports' and len(self.current_config[key]) <= 1:
                    QMessageBox.warning(self, "Action Denied", "Cannot delete the last support.")
                    return
                self.current_config[key].remove(item_data)
                break
        
        # Deselect and trigger update
        self.on_canvas_item_selected(None)
        self.start_analysis()
        
    def get_log_viewer(self):
        return self.log_viewer

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Maintain equal sizing when window is resized
        if self.central_splitter.count() == 2:
            self.central_splitter.setSizes([self.central_splitter.height() // 2, self.central_splitter.height() // 2])

    def closeEvent(self, event):
        event.accept()