from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont, QColor

class LogViewer(QTextEdit):
    """
    A QTextEdit widget specialized for displaying log messages.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        font = QFont("Courier New", 10)
        self.setFont(font)
        self.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;")

    def append_log(self, message):
        """
        Appends a log message to the text edit.
        It also provides basic color coding based on log level.
        """
        if "ERROR" in message or "CRITICAL" in message:
            self.setTextColor(QColor("red"))
        elif "WARNING" in message:
            self.setTextColor(QColor("yellow"))
        else:
            self.setTextColor(QColor("#f0f0f0"))

        self.append(message.strip())
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())