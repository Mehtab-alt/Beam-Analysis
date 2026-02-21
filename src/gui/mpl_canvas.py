from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(QWidget):
    """
    A custom widget to embed a Matplotlib figure into a PyQt6 application.
    It holds the figure and the canvas, but drawing is done by the caller.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        # We create an axes which can be used to plot on.
        self.axes = self.figure.add_subplot(111)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)