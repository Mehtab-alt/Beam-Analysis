from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QToolButton, QFrame, QLabel, QButtonGroup
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import qtawesome as qta

class Toolbox(QWidget):
    """
    A widget that holds tool buttons for adding elements to the beam canvas.
    """
    # Signal: emits the string name of the tool that was activated (e.g., 'add_point_load')
    toolSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True) # Only one tool can be active at a time

        # --- General Tools Section ---
        self.main_layout.addWidget(self._create_header("Tools"))
        self._add_tool_button('select', 'fa5s.mouse-pointer', 'Select / Edit Item')
        self._add_tool_button('delete_item', 'fa5s.trash-alt', 'Delete Item')

        self.main_layout.addWidget(self._create_separator())

        # --- Supports Section ---
        self.main_layout.addWidget(self._create_header("Supports"))
        self._add_tool_button('add_pinned', 'fa5s.map-pin', 'Add Pinned Support')
        self._add_tool_button('add_roller', 'fa5s.circle', 'Add Roller Support')
        self._add_tool_button('add_fixed', 'fa5s.thumbtack', 'Add Fixed Support')

        self.main_layout.addWidget(self._create_separator())

        # --- Loads Section ---
        self.main_layout.addWidget(self._create_header("Loads"))
        self._add_tool_button('add_point_load', 'fa5s.arrow-down', 'Add Point Load')
        self._add_tool_button('add_dist_load', 'fa5s.arrows-alt-v', 'Add Distributed Load')
        
        self.setLayout(self.main_layout)
        
        # Connect the button group's signal
        self.button_group.buttonClicked.connect(self._on_tool_selected)

        # Set default tool
        self.button_group.buttons()[0].setChecked(True)
        self.toolSelected.emit('select')


    def _create_header(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; padding-top: 10px; padding-bottom: 5px;")
        return label
    
    def _create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _add_tool_button(self, tool_id, icon_name, text):
        button = QToolButton()
        button.setText(text)
        button.setIcon(qta.icon(icon_name))
        button.setCheckable(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setFixedSize(180, 30)
        
        # Store the tool_id within the button itself
        button.setProperty("tool_id", tool_id)
        
        self.button_group.addButton(button)
        self.main_layout.addWidget(button)

    def _on_tool_selected(self, button):
        tool_id = button.property("tool_id")
        self.toolSelected.emit(tool_id)

    def set_tool(self, tool_id):
        """Allows external setting of the active tool."""
        for button in self.button_group.buttons():
            if button.property("tool_id") == tool_id:
                button.setChecked(True)
                self.toolSelected.emit(tool_id)
                break