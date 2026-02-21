import sys
import logging
import os
from PyQt6.QtWidgets import QApplication
import qt_material # Import qt_material

from src.gui.main_window import MainWindow
from src.gui.log_handler import QtLogHandler

def setup_gui_logging(log_viewer):
    """
    Sets up the logging system to use the custom Qt handler.
    This will redirect all log messages to the GUI's log viewer.
    """
    qt_log_handler = QtLogHandler()
    
    # Connect the handler's signal to the log viewer's slot
    qt_log_handler.log_signal.connect(log_viewer.append_log)

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[qt_log_handler] # Use our custom handler
    )
    logging.info("GUI logging initialized.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply the qt-material theme with a red color scheme
    qt_material.apply_stylesheet(app, theme='dark_red.xml') # Apply 'red-dark' theme
    
    # The custom style.qss is no longer needed as qt-material provides comprehensive styling.
    # style_path = os.path.join(os.path.dirname(__file__), "src/gui/style.qss")
    # try:
    #     with open(style_path, "r") as f:
    #         app.setStyleSheet(f.read())
    # except FileNotFoundError:
    #     logging.warning(f"Stylesheet not found at {style_path}. Using default style.")

    # Create the main window
    main_window = MainWindow()

    # Set up logging to go to the log viewer widget inside the main window
    log_viewer_widget = main_window.get_log_viewer()
    setup_gui_logging(log_viewer_widget)
    
    # Start the application event loop
    sys.exit(app.exec())