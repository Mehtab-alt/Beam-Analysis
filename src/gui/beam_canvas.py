import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygonF, QBrush, QCursor
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal

class BeamCanvas(QWidget):
    """
    A widget that provides a visual 2D representation of the beam,
    including its supports and loads, based on a configuration dictionary.
    """
    # Signal emitted when an item on the canvas is clicked.
    itemSelected = pyqtSignal(object)
    # Signal emitted when a new item should be added to the model.
    requestAddItem = pyqtSignal(str, float) # item_type, position
    # Signal emitted when an item should be deleted from the model.
    requestDeleteItem = pyqtSignal(object) # item_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = {}
        self.setMinimumHeight(200)  # Increased minimum height for better visibility
        self.setStyleSheet("background-color: #3c3f41;")
        self.clickable_areas = []
        self.selected_item_rect = None
        self.active_tool = 'select' # Default tool
        self.setMouseTracking(True)

    def set_config(self, config):
        """Loads a new configuration and triggers a repaint."""
        self.config = config
        self.selected_item_rect = None
        self.update()

    def set_active_tool(self, tool_id):
        """Sets the current tool and updates the cursor."""
        self.active_tool = tool_id
        if 'add' in tool_id:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif 'delete' in tool_id:
            self.setCursor(QCursor(qta.icon('fa5s.trash-alt').pixmap(16, 16)))
        else: # select
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event):
        """Handles all the drawing for the canvas."""
        super().paintEvent(event)
        self.clickable_areas = [] # Reset for each paint cycle
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.config or 'beam_properties' not in self.config:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load a configuration to display the beam.")
            return

        # Get beam properties
        beam_props = self.config.get('beam_properties', {})
        beam_length = beam_props.get('length', 10.0)

        # --- Layout Constants ---
        margin = 50
        top_padding = 30      # Space for ruler numbers
        ruler_area_height = 20  # Space for the ruler ticks themselves
        ruler_beam_gap = 30   # Gap between ruler and the main drawing area

        # --- Coordinate Calculation ---
        canvas_width = self.width() - 2 * margin
        if beam_length == 0 or canvas_width <= 0: return
        scale_x = canvas_width / beam_length

        # 1. Ruler's Y position is fixed at the top of the canvas
        ruler_y = top_padding 
        
        # 2. The beam's Y position is centered in the remaining available space
        beam_area_start_y = ruler_y + ruler_area_height + ruler_beam_gap
        beam_area_height = self.height() - beam_area_start_y
        beam_y = beam_area_start_y + (beam_area_height / 2)

        # --- Draw Ruler ---
        self._draw_ruler(painter, scale_x, margin, beam_length, ruler_y)

        # --- Draw Beam ---
        painter.setPen(QPen(QColor("#f0f0f0"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(margin, int(beam_y), int(self.width() - margin), int(beam_y))

        # --- Draw Supports ---
        for support in self.config.get('supports', []):
            pos_x = margin + support.get('position', 0) * scale_x
            self._draw_support(painter, support, pos_x, beam_y)
        
        # --- Draw Loads ---
        for load in self.config.get('loads', []):
            if load.get('type') == 'point':
                self._draw_point_load(painter, load, scale_x, margin, beam_y)
            elif load.get('type') == 'distributed':
                self._draw_distributed_load(painter, load, scale_x, margin, beam_y)
        
        # --- Draw Selection Highlight ---
        if self.selected_item_rect:
            painter.setPen(QPen(QColor(255, 255, 0, 200), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.selected_item_rect)

    def mousePressEvent(self, event):
        pos = event.position()
        
        # Calculate physical position on beam from click coordinates
        beam_length = self.config.get('beam_properties', {}).get('length', 10.0)
        margin = 50
        canvas_width = self.width() - 2 * margin
        if canvas_width <= 0: return
        scale_x = canvas_width / beam_length
        physical_pos = (pos.x() - margin) / scale_x
        # Clamp position to be within the beam's length
        physical_pos = max(0, min(beam_length, physical_pos))

        # --- Handle different tools ---
        if self.active_tool.startswith('add'):
            self.requestAddItem.emit(self.active_tool, physical_pos)
        
        else: # 'select' or 'delete' tool
            clicked_item_data = None
            for rect, data in reversed(self.clickable_areas):
                if rect.contains(pos):
                    clicked_item_data = data
                    break # Found an item
            
            if clicked_item_data:
                if self.active_tool == 'select':
                    self.selected_item_rect = rect
                    self.itemSelected.emit(clicked_item_data)
                elif self.active_tool == 'delete_item':
                    self.requestDeleteItem.emit(clicked_item_data)
            else:
                # Clicked on empty space, deselect
                self.selected_item_rect = None
                self.itemSelected.emit(None)

        self.update() # Trigger repaint

    def _calculate_tick_interval(self, length):
        """Calculates a reasonable interval for ruler ticks."""
        if length <= 0:
            return 1, 0.2
        
        power = 10**np.floor(np.log10(length))
        relative_length = length / power

        if relative_length < 2:
            major = power / 5
            minor = power / 10
        elif relative_length < 5:
            major = power / 2
            minor = power / 10
        else:
            major = power
            minor = power / 5
            
        return major, minor

    def _draw_ruler(self, painter, scale_x, margin, length, ruler_y):
        """Draws a horizontal ruler at a specific y-coordinate."""
        painter.setPen(QPen(QColor("#f0f0f0"), 1.5))
        
        # Main ruler line
        painter.drawLine(margin, int(ruler_y), self.width() - margin, int(ruler_y))
        
        major_tick_interval, minor_tick_interval = self._calculate_tick_interval(length)
        if minor_tick_interval <= 0: return # Avoid division by zero

        num_ticks = int(length / minor_tick_interval) + 1
        
        for i in range(num_ticks):
            pos = i * minor_tick_interval
            if pos > length + 1e-9: continue # Add tolerance for float comparison

            x = margin + pos * scale_x
            
            # Check for floating point inaccuracies
            is_major_tick = abs(pos % major_tick_interval) < 1e-9 or abs(major_tick_interval - pos % major_tick_interval) < 1e-9

            if is_major_tick:
                painter.drawLine(int(x), int(ruler_y), int(x), int(ruler_y + 15))
                label = f'{pos:g}' # Use 'g' for general format (removes trailing zeros)
                # Draw text above the ruler line
                painter.drawText(int(x) - 20, int(ruler_y) - 20, 40, 20, Qt.AlignmentFlag.AlignHCenter, label)
            else:
                painter.drawLine(int(x), int(ruler_y), int(x), int(ruler_y + 8))

    def _draw_support(self, painter, support, pos_x, beam_y):
        painter.setPen(QPen(QColor("#c0392b"), 2))
        painter.setBrush(QColor("#e74c3c"))
        
        if support.get('type') == 'pinned':
            triangle = QPolygonF([QPointF(pos_x, beam_y), QPointF(pos_x - 12, beam_y + 20), QPointF(pos_x + 12, beam_y + 20)])
            painter.drawPolygon(triangle)
        elif support.get('type') == 'roller':
            painter.drawEllipse(QPointF(pos_x, beam_y + 12), 10, 10)
        elif support.get('type') == 'fixed':
            painter.setPen(QPen(Qt.GlobalColor.black, 8))
            painter.setBrush(Qt.GlobalColor.gray)
            painter.drawRect(int(pos_x - 10), int(beam_y - 25), 10, 50)

        # Define clickable area for the support
        clickable_rect = QRectF(pos_x - 15, beam_y, 30, 30)
        self.clickable_areas.append((clickable_rect, support))


    def _draw_point_load(self, painter, load, scale_x, margin, beam_y):
        pos_x = margin + load.get('position', 0) * scale_x
        magnitude = load.get('magnitude', 0)
        
        color = QColor("#2980b9") if magnitude < 0 else QColor("#27ae60")
        painter.setPen(QPen(color, 2.5))
        painter.setBrush(color)

        start_point = QPointF(pos_x, beam_y - 70) # Further increased distance for clarity
        end_point = QPointF(pos_x, beam_y)
        
        # Draw Arrow Line
        painter.drawLine(start_point, end_point)
        
        # Draw Arrowhead
        arrow_size = 8
        arrow_p1 = end_point - QPointF(arrow_size * 0.866, arrow_size * 0.5)
        arrow_p2 = end_point - QPointF(arrow_size * 0.866, -arrow_size * 0.5)
        painter.drawPolygon(QPolygonF([end_point, arrow_p1, arrow_p2]))

        # Draw Load Value Text
        painter.setPen(QColor("#f0f0f0")) # Light text for dark background
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        # Display in kN for readability
        load_text = f"{magnitude / 1000:.1f} kN"
        text_rect = painter.fontMetrics().boundingRect(load_text)
        text_rect.moveCenter(start_point.toPoint() - QPointF(0, 10).toPoint())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, load_text)

        # Define clickable area
        clickable_rect = QRectF(start_point, end_point).adjusted(-10, -15, 10, 10)
        self.clickable_areas.append((clickable_rect, load))

    def _draw_distributed_load(self, painter, load, scale_x, margin, beam_y):
        start_x = margin + load.get('start', 0) * scale_x
        end_x = margin + load.get('end', 0) * scale_x
        magnitude = load.get('magnitude', 0)

        color = QColor("#3498db") if magnitude < 0 else QColor("#2ecc71")
        
        load_height = 55 # Further increased distance for clarity
        
        # Draw the rectangle representing the distributed load area
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(52, 152, 219, 50)) # semi-transparent blue
        painter.drawRect(int(start_x), int(beam_y - load_height), int(end_x - start_x), load_height)

        # Draw small arrows
        painter.setPen(QPen(color, 1.5))
        num_arrows = max(2, int((end_x - start_x) / 30))
        for i in range(num_arrows + 1):
            x = start_x + (end_x - start_x) * i / num_arrows
            painter.drawLine(QPointF(x, beam_y - load_height), QPointF(x, beam_y))
            
        # Draw the top line
        painter.drawLine(QPointF(start_x, beam_y - load_height), QPointF(end_x, beam_y - load_height))

        # Draw Load Value Text
        painter.setPen(QColor("#f0f0f0"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        load_text = f"{magnitude / 1000:.1f} kN/m"
        text_rect = painter.fontMetrics().boundingRect(load_text)
        mid_point_x = (start_x + end_x) / 2
        text_rect.moveCenter(QPointF(mid_point_x, beam_y - load_height - 15).toPoint())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, load_text)
        
        # Define clickable area
        clickable_rect = QRectF(start_x, beam_y - load_height - 25, end_x - start_x, load_height + 25)
        self.clickable_areas.append((clickable_rect, load))