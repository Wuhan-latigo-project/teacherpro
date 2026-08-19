from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class TagWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        
        # تعيين الخلفية البيضاء بشكل صريح
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            TagWidget {
                background-color: transparent;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(5)
        
        # تسمية النص مع ستايل محدد
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-size: 13px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                padding: 2px 0px;
            }
        """)
        
        # زر الإزالة مع ستايل محدد
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(18, 18)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 9px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        
        layout.addWidget(self.label)
        layout.addWidget(self.remove_btn)
        
        # ستايل الـ widget نفسه (الإطار والخلفية)
        self.setStyleSheet("""
            TagWidget {
                background-color: #e8f0fe;
                border: 1px solid #bbd4fd;
                border-radius: 15px;
                padding: 2px;
            }
        """)
        
        # تعيين حجم ثابت مناسب
        self.setFixedHeight(30)
        
    @property
    def text(self):
        return self.label.text()