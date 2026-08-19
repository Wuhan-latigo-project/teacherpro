from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import config


class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(60, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #777;
                border-radius: 15px;
                padding: 3px;
                border: none;
            }
            QPushButton::checked {
                background-color: #4361ee;
            }
        """)
        
        # Animation for smooth transition
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Connect the built-in toggled signal
        self.toggled.connect(self.on_toggled)
    
    def on_toggled(self, checked):
        """Handle button toggle to emit stateChanged signal"""
        self.update()
    
    def setChecked(self, checked):
        """Set the switch state"""
        super().setChecked(checked)
        self.update()
    
    def isChecked(self):
        """Get the switch state"""
        return super().isChecked()
    
    def paintEvent(self, event):
        """Custom painting for the switch"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background (using stylesheet colors)
        bg_color = QColor("#4361ee") if self.isChecked() else QColor("#777")
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 
                               self.height() // 2, self.height() // 2)
        
        # Draw slider knob
        painter.setBrush(QColor("#ffffff"))
        slider_size = self.height() - 8
        
        # Calculate knob position
        if self.isChecked():
            knob_x = self.width() - slider_size - 4
        else:
            knob_x = 4
            
        painter.drawEllipse(knob_x, 4, slider_size, slider_size)