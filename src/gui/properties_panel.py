from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QDoubleSpinBox, 
                             QComboBox, QFormLayout, QFrame, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal

# --- Constants for UI Generation ---
# These could be moved to a shared constants file later
UNITS = {
    'length': '(m)', 'position': '(m)', 'start': '(m)', 'end': '(m)',
    'E': '(Pa)', 'I': '(m^4)',
    'magnitude': '(N or N/m)'
}

SELECTIONS = {
    'support_type': ['pinned', 'roller', 'fixed'],
    'load_type': ['point', 'distributed'],
}

class PropertiesPanel(QWidget):
    """
    A widget to dynamically display and edit the properties of a selected item.
    Emits signals whenever a property is changed or an item is to be deleted.
    """
    propertyChanged = pyqtSignal(object, str, object)
    requestDeleteItem = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.placeholder_label = QLabel("Select an item on the canvas to see its properties.")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setStyleSheet("font-style: italic; color: #8c8c8c; padding: 20px;")
        
        self.main_layout.addWidget(self.placeholder_label)
        self.setLayout(self.main_layout)
        
        self.current_item_data = None
        self.form_widget = None # A direct reference to the dynamic form widget

    def _clear_form(self):
        """Safely removes and deletes the existing form widget if it exists."""
        if self.form_widget:
            self.main_layout.removeWidget(self.form_widget)
            self.form_widget.deleteLater()
            self.form_widget = None
        self.current_item_data = None

    def show_properties(self, item_data, config=None):
        """
        Dynamically builds an editor form for the given item data.
        """
        self._clear_form()
        self.current_item_data = item_data

        if not item_data:
            self.placeholder_label.setVisible(True)
            return

        self.placeholder_label.setVisible(False)
        
        # Create the new form inside a QFrame, which will be our managed widget
        self.form_widget = QFrame()
        self.form_widget.setFrameShape(QFrame.Shape.StyledPanel)
        container_layout = QVBoxLayout(self.form_widget)
        
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        container_layout.addLayout(form_layout)

        # Populate the form based on the item's properties
        for key, value in item_data.items():
            unit = UNITS.get(key, '')
            label_text = f"{key.replace('_', ' ').title()} {unit}".strip()
            editor_widget = self._create_editor_widget(key, value, config)
            form_layout.addRow(label_text, editor_widget)
        
        # Add Delete Button
        delete_button = QPushButton("Delete Item")
        delete_button.setStyleSheet("background-color: #c0392b;") # Red color for delete
        delete_button.clicked.connect(self._on_delete_clicked)
        container_layout.addWidget(delete_button, 0, Qt.AlignmentFlag.AlignBottom)
        
        self.main_layout.addWidget(self.form_widget)

    def _on_delete_clicked(self):
        if self.current_item_data:
            self.requestDeleteItem.emit(self.current_item_data)

    def _create_editor_widget(self, key, value, config):
        """Creates the correct input widget for a given property key and value."""
        widget = None
        
        # --- Type Selector ---
        if key == 'type':
            options = []
            # Determine the context (is it a support or a load?)
            if self.current_item_data in config.get('supports', []):
                options = SELECTIONS['support_type']
            elif self.current_item_data in config.get('loads', []):
                options = SELECTIONS['load_type']
            
            if options:
                widget = QComboBox()
                widget.addItems(options)
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(
                    lambda text, k=key: self.propertyChanged.emit(self.current_item_data, k, text)
                )
        
        # --- Numeric Editor ---
        elif isinstance(value, (int, float)):
            widget = QDoubleSpinBox()
            widget.setDecimals(4)
            # Use beam length for sensible range on position-like properties
            beam_length = config.get('beam_properties', {}).get('length', 1e6)
            if key in ['position', 'start', 'end']:
                 widget.setRange(0, beam_length)
                 widget.setSingleStep(0.5)
            else:
                widget.setRange(-1e12, 1e12)
                widget.setSingleStep(1000)

            widget.setValue(float(value))
            widget.valueChanged.connect(
                lambda val, k=key: self.propertyChanged.emit(self.current_item_data, k, val)
            )

        # --- Text Editor (Default) ---
        else:
            widget = QLineEdit(str(value))
            widget.textChanged.connect(
                lambda text, k=key: self.propertyChanged.emit(self.current_item_data, k, text)
            )
            
        return widget