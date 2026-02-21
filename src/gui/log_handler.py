import logging
from PyQt6.QtCore import QObject, pyqtSignal

class QtLogHandler(logging.Handler, QObject):
    """
    A custom logging handler that emits a Qt signal for each log record.
    This allows sending log messages from any thread to the GUI thread safely.
    """
    # Define a signal that carries the log message string
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        """
        Overrides the default emit method to send a signal instead.
        """
        msg = self.format(record)
        self.log_signal.emit(msg)