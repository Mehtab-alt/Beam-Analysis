import sys
import logging
import os
import tkinter as tk
from tkinter import ttk

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Try to import sv-ttk for modern themes
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

from src.tk_gui.main_window import MainWindow
from src.utils.config_loader import load_config


def setup_gui_logging(log_handler):
    """
    Sets up the logging system to use the custom log handler.
    This will redirect all log messages to the GUI's log viewer.
    """
    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[log_handler]  # Use our custom handler
    )
    logging.info("GUI logging initialized.")


class TkLogHandler(logging.Handler):
    """
    A custom logging handler that forwards log messages to the GUI.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

    def emit(self, record):
        """
        Emit a log record by forwarding it to the GUI.
        """
        if self.main_window:
            log_message = self.format(record)
            self.main_window.append_log(log_message)


def main():
    # Create the main Tkinter window
    root = tk.Tk()
    root.title("Civil Engineering Workbench")
    
    # Set the window theme using sv-ttk if available, otherwise use built-in themes
    if HAS_SV_TTK:
        # Use sv-ttk for modern themes
        sv_ttk.set_theme("light")  # or "dark"
    else:
        # Fallback to built-in themes
        try:
            style = ttk.Style()
            if 'clam' in style.theme_names():
                style.theme_use('clam')
            elif 'alt' in style.theme_names():
                style.theme_use('alt')
        except:
            # If themes aren't available, continue with default
            pass
    
    # Create the main window
    main_window = MainWindow(root)
    
    # Set up logging to go to the log viewer widget
    log_handler = TkLogHandler(main_window)
    setup_gui_logging(log_handler)
    
    # Start the application event loop
    root.mainloop()


if __name__ == "__main__":
    main()