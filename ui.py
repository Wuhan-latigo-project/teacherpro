import sys
import json
import urllib.request
import urllib.error
import ssl
from typing import Optional, Dict, Any
from PySide6.QtCore import (
    Qt, QPoint, Signal, QPropertyAnimation, Property, QEasingCurve, QTimer, QRect,QRectF, QByteArray
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient, QBrush, QRadialGradient,
    QPen, QFont, QResizeEvent, QMouseEvent, QAction
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QPushButton, QSizePolicy, QGraphicsDropShadowEffect,
    QButtonGroup, QTextEdit, QScrollArea, QDialog, QMessageBox,
    QGraphicsOpacityEffect, QListWidget, QListWidgetItem, QSpacerItem
)

# Import token manager for authentication
from token_manager import (
    get_token, get_current_room, get_username, is_authenticated,
    get_available_rooms
)

# ---------- SSL Configuration ----------
ssl._create_default_https_context = ssl._create_unverified_context
# ---------- SVG Icons ----------
CHAT_SVG = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M20 12C20 16.4183 16.4183 20 12 20C10.5937 20 9.27223 19.6372 8.12398 19C7.53267 18.6719 4.48731 20.4615 3.99998 20C3.44096 19.4706 5.4583 16.6708 5.07024 16C4.38956 14.8233 3.99999 13.4571 3.99999 12C3.99999 7.58172 7.58171 4 12 4C16.4183 4 20 7.58172 20 12Z" stroke="CURRENT_COLOR" stroke-linejoin="round"/>
</svg>"""

GRID_OVERVIEW_SVG = """<svg fill="CURRENT_COLOR" width="32" height="32" viewBox="0 0 32 32" version="1.1" xmlns="http://www.w3.org/2000/svg">
<path d="M10.24 21c-0.001-1.997-1.619-3.615-3.616-3.615s-3.616 1.619-3.616 3.616 1.619 3.616 3.616 3.616v0c1.996-0.003 3.614-1.621 3.616-3.617v-0zM5.508 21c0.001-0.616 0.5-1.115 1.116-1.115s1.116 0.5 1.116 1.116-0.5 1.116-1.116 1.116c0 0 0 0-0 0v0c-0.616-0.001-1.115-0.501-1.116-1.117v-0zM19.617 21c-0-1.997-1.619-3.616-3.617-3.616s-3.617 1.619-3.617 3.617c0 1.997 1.619 3.616 3.616 3.617h0c1.997-0.003 3.615-1.62 3.617-3.617v-0zM14.884 21c0-0.617 0.5-1.116 1.117-1.116s1.117 0.5 1.117 1.117-0.5 1.117-1.117 1.117c-0 0-0 0-0.001 0h0c-0.616-0.001-1.115-0.501-1.116-1.117v-0zM28.992 21c-0.001-1.997-1.619-3.615-3.616-3.615s-3.616 1.619-3.616 3.616 1.619 3.616 3.616 3.616c0 0 0.001 0 0.001 0h-0c1.996-0.003 3.614-1.621 3.615-3.617v-0zM24.26 21c0.001-0.616 0.5-1.115 1.116-1.115s1.116 0.5 1.116 1.116c0 0.616-0.499 1.116-1.115 1.116h-0c-0.616-0.001-1.116-0.501-1.117-1.117v-0zM25.377 25.031c-1.9 0.012-3.589 0.906-4.679 2.293l-0.010 0.013c-1.093-1.408-2.786-2.306-4.688-2.306s-3.596 0.898-4.678 2.293l-0.010 0.013c-1.1-1.409-2.8-2.306-4.708-2.306-2.846 0-5.226 1.995-5.818 4.664l-0.007 0.040c-0.018 0.080-0.029 0.172-0.029 0.266 0 0.69 0.56 1.25 1.25 1.25 0.596 0 1.095-0.418 1.22-0.976l0.002-0.008c0.356-1.575 1.743-2.734 3.402-2.734s3.046 1.159 3.397 2.711l0.004 0.023c0.127 0.567 0.625 0.984 1.221 0.984h0c0.021 0 0.044-0.006 0.065-0.007 0.022 0.001 0.044 0.007 0.065 0.007 0.595-0 1.093-0.417 1.218-0.974l0.002-0.008c0.355-1.576 1.744-2.736 3.403-2.736s3.046 1.159 3.398 2.711l0.004 0.023c0.17 0.559 0.681 0.959 1.285 0.959s1.114-0.399 1.282-0.947l0.003-0.009c0.356-1.576 1.744-2.736 3.403-2.736s3.048 1.16 3.399 2.713l0.004 0.023c0.127 0.565 0.624 0.982 1.219 0.982h0c0.096-0 0.189-0.011 0.278-0.031l-0.008 0.002c0.566-0.126 0.982-0.624 0.982-1.219 0-0.095-0.011-0.188-0.031-0.277l0.002 0.008c-0.62-2.702-2.998-4.689-5.842-4.701h-0.001zM30 0.75h-28c-0.69 0-1.25 0.56-1.25 1.25v0 14c0 0.69 0.56 1.25 1.25 1.25s1.25-0.56 1.25-1.25v0-12.75h25.5v12.75c0 0.69 0.56 1.25 1.25 1.25s1.25-0.56 1.25-1.25v0-14c-0-0.69-0.56-1.25-1.25-1.25h-0z"></path>
</svg>"""

INFO_HELP_SVG = """<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M8 42H32C33.1046 42 34 41.1046 34 40V8C34 6.89543 33.1046 6 32 6H8C6.89543 6 6 6.89543 6 8V40C6 41.1046 6.89543 42 8 42ZM32 44H8C5.79086 44 4 42.2091 4 40V8C4 5.79086 5.79086 4 8 4H32C34.2091 4 36 5.79086 36 8V40C36 42.2091 34.2091 44 32 44Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M18 13C18 12.4477 18.4477 12 19 12H31C31.5523 12 32 12.4477 32 13C32 13.5523 31.5523 14 31 14H19C18.4477 14 18 13.5523 18 13Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M18 17C18 16.4477 18.4477 16 19 16H31C31.5523 16 32 16.4477 32 17C32 17.5523 31.5523 18 31 18H19C18.4477 18 18 17.5523 18 17Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M18 25C18 24.4477 18.4477 24 19 24H31C31.5523 24 32 24.4477 32 25C32 25.5523 31.5523 26 31 26H19C18.4477 26 18 25.5523 18 25Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M18 29C18 28.4477 18.4477 28 19 28H31C31.5523 28 32 28.4477 32 29C32 29.5523 31.5523 30 31 30H19C18.4477 30 18 29.5523 18 29Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M10 26V29H13V26H10ZM9 24H14C14.5523 24 15 24.4477 15 25V30C15 30.5523 14.5523 31 14 31H9C8.44772 31 8 30.5523 8 30V25C8 24.4477 8.44772 24 9 24Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M15.7071 12.2929C16.0976 12.6834 16.0976 13.3166 15.7071 13.7071L11 18.4142L8.29289 15.7071C7.90237 15.3166 7.90237 14.6834 8.29289 14.2929C8.68342 13.9024 9.31658 13.9024 9.70711 14.2929L11 15.5858L14.2929 12.2929C14.6834 11.9024 15.3166 11.9024 15.7071 12.2929Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M42 24H40V39.3333L41 40.6667L42 39.3333V24ZM44 40L41 44L38 40V22H44V40Z" fill="CURRENT_COLOR"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M42 17H40V19H42V17ZM40 15H42C43.1046 15 44 15.8954 44 17V21H38V17C38 15.8954 38.8954 15 40 15Z" fill="CURRENT_COLOR"/>
</svg>"""

ACCOUNT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" fill="CURRENT_COLOR" width="24" height="24" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>"""


def colorize_svg(svg_str, color):
    return svg_str.replace("CURRENT_COLOR", color)
# ---------- Configuration ----------
SERVER_BASE = "https://127.0.0.1:8443"


# ============= FEEDBACK CODE START =============

# ---------- 1. Background (No color) ----------
class OrbBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #f0f0f0;")  # Simple light gray background

    def paintEvent(self, event):
        # Simple background without gradients
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        painter.end()


# ---------- 2. Category Chips ----------
class CategoryChips(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        options = [
            ("feature request", "💎 Feature"),
            ("bug report", "🐛 Bug"),
            ("user experience", "🎨 UX"),
            ("general", "💬 General"),
        ]
        for value, text in options:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    border:1.5px solid #d0d0d0;
                    border-radius:24px; padding:12px 22px;
                    font-weight:600; font-size:13px; color:#333333;
                }
                QPushButton:hover { background: #f5f5f5; border-color:#999999; }
                QPushButton:checked {
                    background: #333333;
                    border-color:transparent; color:white;
                }
            """)
            self._group.addButton(btn)
            layout.addWidget(btn)
            btn.setProperty("category_value", value)
        layout.addStretch()

    def selected_category(self):
        btn = self._group.checkedButton()
        return btn.property("category_value") if btn else None

    def clear(self):
        btn = self._group.checkedButton()
        if btn:
            self._group.setExclusive(False)
            btn.setChecked(False)
            self._group.setExclusive(True)


# ---------- 3. Shake Button ----------
class ShakeButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._original_pos = None
        self._error_timer = QTimer(self)
        self._error_timer.timeout.connect(self._restore_button)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(50)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0,6)
        shadow.setColor(QColor(0,0,0,80))
        self.setGraphicsEffect(shadow)
        self._normal_style = """
            QPushButton {
                background: #333333;
                border:none; border-radius:25px; padding:12px;
                font-weight:700; font-size:15px; color:white;
            }
            QPushButton:hover { background: #555555; }
        """
        self.setStyleSheet(self._normal_style)

    def set_error_mode(self, text, duration=2600):
        self.setText(text)
        self.setStyleSheet("""
            QPushButton {
                background: #cc0000;
                border:none; border-radius:25px; padding:12px;
                font-weight:700; font-size:15px; color:white;
            }
        """)
        self._shake()
        self._error_timer.start(duration)

    def _shake(self):
        if not hasattr(self, '_shake_phase'):
            self._shake_phase = 0
            self._original_pos = self.pos()
            self._shake_timer = QTimer(self)
            self._shake_timer.timeout.connect(self._shake_step)
            self._shake_timer.start(40)
        else:
            self._shake_phase = 0

    def _shake_step(self):
        offsets = [0,4,-4,3,-3,2,-2,1,-1,0]
        if self._shake_phase < len(offsets):
            dx = offsets[self._shake_phase]
            if self._original_pos:
                self.move(self._original_pos.x()+dx, self._original_pos.y())
            self._shake_phase += 1
        else:
            self._shake_timer.stop()
            if self._original_pos:
                self.move(self._original_pos)

    def _restore_button(self):
        self._error_timer.stop()
        self.setText("Send feedback")
        self.setStyleSheet(self._normal_style)
        if self._original_pos:
            self.move(self._original_pos)


# ---------- 4. Toast ----------
class Toast(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet("""
            background:rgba(50,50,50,0.9);
            border-radius:22px;
            padding:6px 14px;
            font-weight:500;
            font-size:13px;
            color:#f1f5f9;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14,0,10,0)
        self.msg_label = QLabel()
        self.msg_label.setStyleSheet("color:white;")
        layout.addWidget(self.msg_label)
        layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22,22)
        close_btn.setStyleSheet("border:none; color:#cbd5e1; font-size:14px; background:transparent;")
        close_btn.clicked.connect(self.hide_toast)
        layout.addWidget(close_btn)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        self.hide()
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(300)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.fade_out)

    def show_message(self, text, is_error=False):
        self.msg_label.setText(text)
        if is_error:
            self.setStyleSheet("""
                background:rgba(80,30,30,0.9);
                border-left:4px solid #ff4444;
                border-radius:22px;
                padding:6px 14px;
                font-weight:500;
                font-size:13px;
                color:#f1f5f9;
            """)
        else:
            self.setStyleSheet("""
                background:rgba(50,50,50,0.9);
                border-left:4px solid #44cc88;
                border-radius:22px;
                padding:6px 14px;
                font-weight:500;
                font-size:13px;
                color:#f1f5f9;
            """)
        self.show()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        self._auto_hide_timer.start(4500)

    def fade_out(self):
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def hide_toast(self):
        self._opacity_effect.setOpacity(0.0)
        self.hide()


# ---------- 5. Popup ----------
class FeedbackDetailPopup(QDialog):
    def __init__(self, username, category, message, time, love_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Feedback Details")
        self.setFixedSize(450, 350)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        container = QFrame(self)
        container.setObjectName("pop")
        container.setGeometry(0, 0, 450, 350)
        container.setStyleSheet("""
            #pop {
                background: #ffffff;
                border-radius: 28px;
                border: 2px solid #e0e0e0;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        l = QVBoxLayout(container)
        l.setContentsMargins(28, 24, 28, 24)
        l.setSpacing(16)
        h = QHBoxLayout()
        icons = {"feature request": "💎", "bug report": "🐛", "user experience": "🎨", "general": "💬"}
        icon = icons.get(category, "💬")
        il = QLabel(icon)
        il.setFixedSize(44, 44)
        il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("background:rgba(0,0,0,0.05); border-radius:14px; font-size:24px;")
        h.addWidget(il)
        cl = QLabel(category.replace("_", " ").title())
        cl.setStyleSheet("font-size:18px; font-weight:700; color:#444444;")
        h.addWidget(cl)
        h.addStretch()
        cb = QPushButton("✕")
        cb.setFixedSize(32, 32)
        cb.setStyleSheet("""
            background: rgba(0, 0, 0, 0.05);
            border: none;
            border-radius: 16px;
            font-size: 16px;
            color: #666;
            font-weight: 700;
        """)
        cb.clicked.connect(self.close)
        h.addWidget(cb)
        l.addLayout(h)
        
        user_label = QLabel(f"👤 Posted by: {username}")
        user_label.setStyleSheet("font-size: 12px; color: #666666; padding: 4px 0;")
        l.addWidget(user_label)
        
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(0, 0, 0, 0.08);")
        l.addWidget(sep)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 8px;
                background: rgba(200, 200, 220, 0.15);
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #999999;
                border-radius: 4px;
                min-height: 35px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
                border: none;
            }
        """)
        mw = QWidget()
        ml = QVBoxLayout(mw)
        ml.setContentsMargins(0, 0, 0, 0)
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size:14px; color:#333333; font-weight:500; line-height:1.6; padding:8px;")
        ml.addWidget(msg_label)
        ml.addStretch()
        scroll.setWidget(mw)
        l.addWidget(scroll)
        f = QHBoxLayout()
        tl = QLabel(f"🕒 {time}")
        tl.setStyleSheet("font-size:11px; color:#999999; font-weight:500;")
        f.addWidget(tl)
        f.addStretch()
        ll = QLabel(f"❤️ {love_count} likes")
        ll.setStyleSheet("""
            font-size:12px;
            color:#cc4444;
            font-weight:600;
            background: rgba(255, 200, 200, 0.3);
            border-radius:12px;
            padding:4px 12px;
        """)
        f.addWidget(ll)
        l.addLayout(f)


# ---------- 6. Feedback Item ----------
class FeedbackItem(QFrame):
    loveToggled = Signal(str)

    def __init__(self, fb_id, username, category, message, time, likes, liked=False, parent=None):
        super().__init__(parent)
        self.fb_id = fb_id
        self.username = username
        self.category = category
        self.full_message = message
        self.time_label = time
        self.love_count = likes
        self.user_liked = liked

        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 16px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                background: #f8f8f8;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        ml = QVBoxLayout(self)
        ml.setContentsMargins(14, 12, 14, 12)
        ml.setSpacing(8)
        
        top = QHBoxLayout()
        icons = {"feature request": "💎", "bug report": "🐛", "user experience": "🎨", "general": "💬"}
        il = QLabel(icons.get(category, "💬"))
        il.setFixedSize(32, 32)
        il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("background: rgba(0,0,0,0.05); border-radius: 10px; font-size: 16px; border: none;")
        top.addWidget(il)
        
        info_label = QLabel(f"👤 {username}  •  {category.replace('_', ' ').title()}")
        info_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #555555; background: transparent; border: none;")
        top.addWidget(info_label, alignment=Qt.AlignVCenter)
        
        top.addStretch()
        
        self.time_display = QLabel(time)
        self.time_display.setStyleSheet("font-size: 9px; color: #999999; background: transparent; border: none;")
        top.addWidget(self.time_display)
        
        self.love_btn = QPushButton(f"❤️ {likes}")
        self.love_btn.setFixedHeight(26)
        self.love_btn.setCursor(Qt.PointingHandCursor)
        self._update_love_style()
        self.love_btn.clicked.connect(self._on_love)
        top.addWidget(self.love_btn)
        ml.addLayout(top)
        
        self.msg_label = QLabel()
        self.msg_label.setWordWrap(True)
        self.msg_label.setStyleSheet("font-size: 12px; color: #333333; font-weight: 500; background: transparent; padding: 4px 0; border: none;")
        self.msg_label.setText(self.full_message[:80] + "..." if len(self.full_message) > 80 else self.full_message)
        ml.addWidget(self.msg_label)

    def _update_love_style(self):
        if self.user_liked:
            self.love_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 100, 100, 0.5);
                    border: none;
                    border-radius: 13px;
                    padding: 2px 10px;
                    font-size: 11px;
                    font-weight: 600;
                    color: #cc4444;
                }
                QPushButton:hover {
                    background: rgba(255, 100, 100, 0.7);
                }
            """)
        else:
            self.love_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 200, 200, 0.4);
                    border: none;
                    border-radius: 13px;
                    padding: 2px 10px;
                    font-size: 11px;
                    font-weight: 600;
                    color: #cc4444;
                }
                QPushButton:hover {
                    background: rgba(255, 200, 200, 0.6);
                }
            """)

    def _on_love(self):
        self.loveToggled.emit(self.fb_id)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.love_btn.underMouse():
            self.show_detail()
        super().mousePressEvent(event)

    def show_detail(self):
        popup = FeedbackDetailPopup(
            self.username,
            self.category,
            self.full_message,
            self.time_label,
            self.love_count,
            self.window()
        )
        popup.move(
            self.window().x() + (self.window().width() - popup.width()) // 2,
            self.window().y() + (self.window().height() - popup.height()) // 2
        )
        popup.exec()


# ---------- 7. Sidebar (Recent Feedback) ----------
class RecentFeedbackPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.feedbacks = []
        self.offset = 0
        self.limit = 15
        self.loading = False
        self.all_loaded = False

        l = QVBoxLayout(self)
        l.setContentsMargins(16, 24, 16, 24)
        l.setSpacing(12)
        h = QHBoxLayout()
        title = QLabel("📋 Recent Feedback")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #333333; background: transparent;")
        h.addWidget(title)
        h.addStretch()
        self.count_badge = QLabel("0")
        self.count_badge.setFixedSize(32, 32)
        self.count_badge.setAlignment(Qt.AlignCenter)
        self.count_badge.setStyleSheet("""
            QLabel {
                background: #444444;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 700;
                color: white;
                border: none;
            }
        """)
        h.addWidget(self.count_badge)
        l.addLayout(h)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: rgba(200, 200, 220, 0.15);
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #999999;
                border-radius: 4px;
                min-height: 35px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout(self.items_widget)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(10)
        self.items_layout.addStretch()
        self.scroll.setWidget(self.items_widget)
        l.addWidget(self.scroll)

        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self._fetch_feedbacks()

    def _fetch_feedbacks(self):
        if self.loading or self.all_loaded:
            return
        
        token = get_token()
        room = get_current_room()
        
        if not token or not room:
            return
        
        self.loading = True
        try:
            url = f"{SERVER_BASE}/feedbacks?room={room}&offset={self.offset}&limit={self.limit}"
            
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Bearer {token}')
            req.add_header('X-Room', room)
            
            with urllib.request.urlopen(req, context=ssl._create_unverified_context()) as resp:
                data = json.loads(resp.read())
            
            if not data:
                self.all_loaded = True
                self.loading = False
                return
            
            for fb in data:
                item = FeedbackItem(
                    fb["id"],
                    fb.get("username", "Anonymous"),
                    fb["category"],
                    fb["message"],
                    fb["time"],
                    fb["likes"],
                    liked=fb.get("liked_by_user", False)
                )
                self.feedbacks.append(item)
                self.items_layout.insertWidget(self.items_layout.count() - 1, item)
                item.loveToggled.connect(self.toggle_like)
            
            self.offset += len(data)
            self._update_badge()
            
        except Exception as e:
            print(f"Fetch error: {e}")
        finally:
            self.loading = False

    def _on_scroll(self, value):
        sb = self.scroll.verticalScrollBar()
        if sb.maximum() - value <= 10 and not self.loading:
            self._fetch_feedbacks()

    def add_feedback(self, category, message):
        token = get_token()
        room = get_current_room()
        
        if not token or not room:
            return
        
        try:
            data = json.dumps({
                "room": room,
                "category": category,
                "message": message
            }).encode()
            
            req = urllib.request.Request(f"{SERVER_BASE}/feedback", data=data, method='POST')
            req.add_header('Authorization', f'Bearer {token}')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-Room', room)
            
            with urllib.request.urlopen(req, context=ssl._create_unverified_context()) as resp:
                resp_data = json.loads(resp.read())
            
            self._clear_feedbacks()
            self.offset = 0
            self.all_loaded = False
            self._fetch_feedbacks()
            
        except Exception as e:
            print(f"Submit error: {e}")

    def toggle_like(self, feedback_id):
        token = get_token()
        room = get_current_room()
        
        if not token or not room:
            return
        
        try:
            data = json.dumps({
                "room": room,
                "feedback_id": feedback_id
            }).encode()
            
            req = urllib.request.Request(f"{SERVER_BASE}/like", data=data, method='POST')
            req.add_header('Authorization', f'Bearer {token}')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-Room', room)
            
            with urllib.request.urlopen(req, context=ssl._create_unverified_context()) as resp:
                resp_data = json.loads(resp.read())
            
            for item in self.feedbacks:
                if item.fb_id == feedback_id:
                    item.love_count = resp_data["likes"]
                    item.user_liked = resp_data["action"] == "liked"
                    item.love_btn.setText(f"❤️ {item.love_count}")
                    item._update_love_style()
                    break
                    
        except Exception as e:
            print(f"Like error: {e}")

    def _clear_feedbacks(self):
        for item in self.feedbacks:
            self.items_layout.removeWidget(item)
            item.deleteLater()
        self.feedbacks.clear()
        self._update_badge()

    def _update_badge(self):
        self.count_badge.setText(str(len(self.feedbacks)))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, -1, -1), 32, 32)
        painter.fillPath(path, QColor(255, 255, 255, 200))
        painter.setPen(QPen(QColor(200, 200, 200, 130), 1.2))
        painter.drawPath(path)
        painter.end()
        super().paintEvent(event)


# ---------- 8. Feedback Form ----------
class FeedbackForm(QFrame):
    feedback_submitted = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glass")
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setMinimumWidth(400)
        self.setMaximumWidth(700)
        
        l = QVBoxLayout(self)
        l.setContentsMargins(32, 28, 32, 32)
        l.setSpacing(16)

        title = QLabel("Share your voice")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 800; color: #333333;")
        l.addWidget(title)

        sub = QLabel("We will take your suggestions into consideration. Thank you.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #555555; font-weight: 500; font-size: 12px; padding: 0 10px;")
        l.addWidget(sub)

        l.addWidget(QLabel("🏷 Category", styleSheet="font-weight: 600; font-size: 12px; color: #444444;"))
        self.chips = CategoryChips()
        l.addWidget(self.chips)

        l.addWidget(QLabel("✏️ Your message", styleSheet="font-weight: 600; font-size: 12px; color: #444444;"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("What's on your mind? Ideas, criticism, praise — all welcome.")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1.5px solid #d0d0d0;
                border-radius: 24px;
                padding: 12px 16px;
                font-size: 14px;
                color: #333333;
                font-weight: 500;
            }
            QTextEdit:focus {
                border-color: #999999;
                background: #ffffff;
            }
        """)
        self.text_edit.setMaximumHeight(90)
        l.addWidget(self.text_edit)

        self.char_counter = QLabel("0 / 500 characters")
        self.char_counter.setAlignment(Qt.AlignRight)
        self.char_counter.setStyleSheet("font-size: 10px; color: #777777;")
        l.addWidget(self.char_counter)
        self.text_edit.textChanged.connect(
            lambda: self.char_counter.setText(f"{len(self.text_edit.toPlainText())} / 500 characters")
        )

        self.submit_btn = ShakeButton("Send feedback")
        self.submit_btn.clicked.connect(self._on_submit)
        l.addWidget(self.submit_btn)

        self.toast = Toast(self)
        l.addWidget(self.toast)

        footer = QLabel(" Secure & encrypted — your voice shapes tomorrow")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 9px; color: #999999; margin-top: 4px;")
        l.addWidget(footer)

        if not is_authenticated():
            self.submit_btn.setEnabled(False)
            self.submit_btn.setText("Not authenticated")
            self.toast.show_message("Please login first", True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, -1, -1), 56, 56)
        p.fillPath(path, QColor(255, 255, 255, 220))
        p.setPen(QPen(QColor(200, 200, 200, 153), 1.5))
        p.drawPath(path)
        p.end()
        super().paintEvent(event)

    def _on_submit(self):
        if not is_authenticated():
            self.toast.show_message("Please login first", True)
            return
        
        cat = self.chips.selected_category()
        if not cat:
            self.submit_btn.set_error_mode("🏷️ Choose category")
            self.toast.show_message("Select a feedback category", True)
            return
        
        msg = self.text_edit.toPlainText().strip()
        if not msg:
            self.submit_btn.set_error_mode("✏️ Write a message")
            self.toast.show_message("Please write your feedback", True)
            return
        
        if len(msg) > 500:
            self.submit_btn.set_error_mode("📏 Max 500 chars")
            self.toast.show_message(f"Message too long ({len(msg)}/500)", True)
            return
        
        self.toast.show_message(f"🎉 Thanks! Your {cat} feedback has been recorded securely.", False)
        self.feedback_submitted.emit(cat, msg)
        self.chips.clear()
        self.text_edit.clear()
        self.submit_btn._restore_button()


# ---------- 9. Feedback Container (Always Centered) ----------
class FeedbackContainer(QWidget):
    """Container that always centers the feedback form and sidebar."""
    
    feedback_submitted = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(25)
        
        # Left side: Form
        form_container = QWidget()
        form_container.setAttribute(Qt.WA_StyledBackground, True)
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setAlignment(Qt.AlignCenter)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        self.feedback_form = FeedbackForm()
        form_layout.addWidget(self.feedback_form, alignment=Qt.AlignCenter)
        
        # Right side: Recent feedback
        self.recent_panel = RecentFeedbackPanel()
        
        # Add to main layout with stretch
        main_layout.addWidget(form_container, stretch=2)
        main_layout.addWidget(self.recent_panel, stretch=1)
        
        # Connect signals
        self.feedback_form.feedback_submitted.connect(self.recent_panel.add_feedback)
        self.feedback_form.feedback_submitted.connect(self.feedback_submitted.emit)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        if width < 900:
            self.layout().setSpacing(15)
            self.layout().setContentsMargins(10, 10, 10, 10)
        else:
            self.layout().setSpacing(25)
            self.layout().setContentsMargins(25, 25, 25, 25)

# ============= FEEDBACK CODE END =============


# ============= CHAT PANEL CODE START =============

class ChatPanel(QWidget):
    """Floating side panel for chat/messages with glass effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set fixed width and height, reducing height by 10%
        self.setFixedWidth(760)
        self.setFixedHeight(int(800 * 0.9))
        
        # Main container with ocean blue glass effect
        self.container = QFrame(self)
        self.container.setObjectName("chatPanel")
        self.container.setGeometry(0, 0, self.width(), self.height())
        self.container.setStyleSheet("""
            QFrame#chatPanel {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(9, 61, 113, 0.95), stop:1 rgba(21, 114, 183, 0.95));
                border-top-left-radius: 28px;
                border-bottom-left-radius: 28px;
                border-left: 1px solid rgba(255, 255, 255, 0.12);
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(-8, 0)
        self.container.setGraphicsEffect(shadow)
        
        # Layout for container - make it fill the container
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("border-bottom: 1px solid rgba(255, 255, 255, 0.1);")
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 20, 16)
        
        title_label = QLabel("Messages")
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: white;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 18px;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        close_btn.clicked.connect(self.hide_panel)
        header_layout.addWidget(close_btn)
        
        container_layout.addWidget(header)
        
        # Content container - this will hold the chat widget
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: transparent;")
        self.content_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        container_layout.addWidget(self.content_container, 1)  # stretch
        
        # Footer
        footer = QLabel("Stay connected with your conversations")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFixedHeight(50)
        footer.setStyleSheet("""
            color: #94a3b8;
            font-size: 12px;
            padding: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        """)
        container_layout.addWidget(footer)
        
        # Store the chat widget reference
        self.chat_widget = None
        
        # Animation properties
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Initially hidden (offscreen)
        self.setGeometry(self.parent().width(), 0, 760, 800)
        
        # Add a backdrop
        self.backdrop = QFrame(self.parent())
        self.backdrop.setStyleSheet("background: rgba(0, 0, 0, 0.35);")
        self.backdrop.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.backdrop.hide()
        self.backdrop.mousePressEvent = lambda e: self.hide_panel()
    
    def set_chat_widget(self, widget):
        """Set the chat widget inside the panel."""
        if self.chat_widget:
            self.content_layout.removeWidget(self.chat_widget)
            self.chat_widget.deleteLater()
        self.chat_widget = widget
        self.content_layout.addWidget(widget)
        widget.setParent(self.content_container)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def show_panel(self):
        """Show the chat panel with animation."""
        parent = self.parent()
        target_rect = QRect(parent.width() - self.width(), 0, self.width(), self.height())
        self.animation.setEndValue(target_rect)
        self.animation.start()
        self.show()
        self.backdrop.show()
        self.backdrop.raise_()
        self.raise_()
    
    def hide_panel(self):
        """Hide the chat panel with animation."""
        parent = self.parent()
        target_rect = QRect(parent.width(), 0, self.width(), self.height())
        self.animation.setEndValue(target_rect)
        self.animation.start()
        self.backdrop.hide()
        # Hide after animation
        QTimer.singleShot(350, self.hide)
    
    def resizeEvent(self, event):
        """Handle resize to keep panel properly positioned."""
        super().resizeEvent(event)
        if self.isVisible() and not self.animation.state():
            # If visible and not animating, ensure it's at the right edge
            parent = self.parent()
            if parent:
                self.setGeometry(parent.width() - self.width(), 0, self.width(), self.height())
                # Update container to fill the panel
                self.container.setGeometry(0, 0, self.width(), self.height())
    
    def toggle_panel(self):
        """Toggle the panel visibility."""
        if self.isVisible() and not self.animation.state():
            self.hide_panel()
        else:
            self.show_panel()


class ToggleSwitch(QWidget):
    """Modern toggle switch widget for theme switching"""
    
    toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 34)
        self._checked = False  # False = dark mode (moon), True = light mode (sun)
        self._offset = 0.0  # Initialize BEFORE animation
        self._animation = QPropertyAnimation(self, b"offset")
        self._animation.setDuration(200)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        if self._checked:
            bg_color = QColor(255, 193, 7)  # Orange/yellow for sun mode
        else:
            bg_color = QColor(100, 108, 118)  # Gray for moon mode
        
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 17, 17)
        
        # Draw handle
        handle_size = self.height() - 4
        handle_x = 2 + self._offset
        handle_y = 2
        
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(handle_x), int(handle_y), int(handle_size), int(handle_size))
        
        # Draw icon inside handle - make it fill the handle
        if self._checked:
            # Draw sun icon filling the handle
            center_x = handle_x + handle_size / 2
            center_y = handle_y + handle_size / 2
            size = handle_size * 0.85  # Almost fill the handle
            self.draw_sun_on_handle(painter, center_x, center_y, size)
        else:
            # Draw moon icon filling the handle
            center_x = handle_x + handle_size / 2
            center_y = handle_y + handle_size / 2
            size = handle_size * 0.9  # Fill the handle
            self.draw_moon_on_handle(painter, center_x, center_y, size)
    
    def draw_sun_on_handle(self, painter, cx, cy, size):
        """Draw a sun on the handle based on the provided SVG"""
        # Scale factor for the sun
        scale = size / 100
        painter.save()
        painter.translate(cx - 50 * scale, cy - 50 * scale)
        painter.scale(scale, scale)
        
        # Outer circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 140, 0))
        painter.drawEllipse(32, 32, 36, 36)
        
        # Inner circle
        painter.setBrush(QColor(255, 215, 0))
        painter.drawEllipse(40, 40, 20, 20)
        
        # Sun rays
        pen = QPen()
        pen.setColor(QColor(255, 140, 0))
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Top ray
        painter.drawLine(50, 5, 50, 20)
        # Bottom ray
        painter.drawLine(50, 80, 50, 95)
        # Left ray
        painter.drawLine(5, 50, 20, 50)
        # Right ray
        painter.drawLine(80, 50, 95, 50)
        # Top-right ray
        painter.drawLine(72, 28, 82, 18)
        # Bottom-right ray
        painter.drawLine(72, 72, 82, 82)
        # Bottom-left ray
        painter.drawLine(28, 72, 18, 82)
        # Top-left ray
        painter.drawLine(28, 28, 18, 18)
        
        # Eyes
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 224, 130))
        painter.drawEllipse(42, 42, 4, 4)
        painter.drawEllipse(54, 42, 4, 4)
        
        # Smile
        smile_pen = QPen()
        smile_pen.setColor(QColor(255, 224, 130))
        smile_pen.setWidth(2)
        painter.setPen(smile_pen)
        painter.setBrush(Qt.NoBrush)
        smile_path = QPainterPath()
        smile_path.moveTo(45, 55)
        smile_path.quadTo(50, 62, 55, 55)
        painter.drawPath(smile_path)
        
        painter.restore()
    
    def draw_moon_on_handle(self, painter, cx, cy, size):
        """Draw a moon filling the entire handle"""
        # Scale factor for the moon - make it bigger to fill the handle
        scale = size / 100
        painter.save()
        painter.translate(cx - 50 * scale, cy - 50 * scale)
        painter.scale(scale, scale)
        
        # Main moon circle - fill the entire space
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 245, 220))  # #F5F5DC Cream color
        painter.drawEllipse(20, 20, 60, 60)
        
        # Moon craters with different opacities and sizes
        painter.setBrush(QColor(192, 184, 152))  # #C0B898
        
        # Large crater
        painter.setOpacity(0.8)
        painter.drawEllipse(44, 24, 18, 18)  # Top-right crater
        
        # Medium crater
        painter.setOpacity(0.7)
        painter.drawEllipse(22, 48, 12, 12)  # Left crater
        
        # Small crater
        painter.setOpacity(0.7)
        painter.drawEllipse(38, 62, 10, 10)  # Bottom crater
        
        # Tiny craters
        painter.setOpacity(0.6)
        painter.drawEllipse(30, 34, 6, 6)  # Small crater top-left
        painter.drawEllipse(54, 44, 5, 5)  # Small crater right
        painter.drawEllipse(28, 58, 4, 4)  # Tiny crater bottom-left
        painter.drawEllipse(48, 50, 3, 3)  # Tiny crater center-right
        
        painter.setOpacity(1.0)
        painter.restore()
    
    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
        self.toggled.emit(self._checked)
    
    def setChecked(self, checked):
        self._checked = checked
        self._animation.stop()
        
        if checked:
            self._animation.setEndValue(self.width() - self.height() + 2)
        else:
            self._animation.setEndValue(0)
            
        self._animation.start()
        self.update()
    
    def isChecked(self):
        return self._checked
    
    @Property(float)
    def offset(self):
        return self._offset
    
    @offset.setter
    def offset(self, value):
        self._offset = value
        self.update()


class IconButton(QPushButton):
    """Circular icon button with hover effect."""
    def __init__(self, icon_paths=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 28px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.icon_paths = icon_paths or []
        self.icon_color = QColor(255, 255, 255)

    def set_icon_paths(self, paths):
        self.icon_paths = paths
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.icon_paths:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.icon_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Center the icon
        w, h = 20, 20
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        painter.translate(x, y)

        for path in self.icon_paths:
            painter.drawPath(path)


class DockCircle(QPushButton):
    """Circular dock icon button that can be active/inactive with shadow."""
    def __init__(self, icon_paths=None, icon_svg=None, parent=None, button_index=None):
        super().__init__(parent)
        self.setFixedSize(48, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_paths = icon_paths or []
        self.icon_svg = icon_svg
        self._svg_inactive = None
        self._svg_active = None
        if self.icon_svg:
            inactive_svg = colorize_svg(self.icon_svg, "#ffffff")
            active_svg = colorize_svg(self.icon_svg, "#111111")
            self._svg_inactive = QSvgRenderer(QByteArray(inactive_svg.encode()))
            self._svg_active = QSvgRenderer(QByteArray(active_svg.encode()))
        self._active = False
        self.icon_color = QColor(255, 255, 255, 204)
        self.button_index = button_index
        self.update_style()
        self.add_shadow()

    def add_shadow(self):
        """Add shadow effect to the button"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def update_style(self):
        if self._active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: none;
                    border-radius: 24px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            self.icon_color = QColor(17, 17, 17)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-radius: 24px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                }
            """)
            self.icon_color = QColor(255, 255, 255, 204)

    def set_active(self, active):
        self._active = active
        self.update_style()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.icon_paths and not self.icon_svg:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.icon_svg:
            renderer = self._svg_active if self._active else self._svg_inactive
            size = 24
            x = (self.width() - size) // 2
            y = (self.height() - size) // 2
            renderer.render(painter, QRectF(x, y, size, size))
        else:
            painter.setPen(QPen(self.icon_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            w, h = 24, 24
            x = (self.width() - w) // 2
            y = (self.height() - h) // 2
            painter.translate(x, y)
            for path in self.icon_paths:
                painter.drawPath(path)

class MinimizeButton(QPushButton):
    """Custom minimize button with yellow circle."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #ffcc00;
                border: none;
                border-radius: 18px;
                font-size: 20px;
                font-weight: bold;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: #ffd633;
            }
            QPushButton:pressed {
                background-color: #e6b800;
            }
        """)
        self.setText("−")
        self.clicked.connect(self.minimize_app)
    
    def minimize_app(self):
        window = self.window()
        if window:
            window.showMinimized()


class MaximizeButton(QPushButton):
    """Custom maximize button with green circle."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #5fd88f;
            }
            QPushButton:pressed {
                background-color: #28a745;
            }
        """)
        self.setText("▢")
        self.clicked.connect(self.maximize_app)
    
    def maximize_app(self):
        window = self.window()
        if window:
            window.showFullScreen()


class CloseButton(QPushButton):
    """Custom close button with red circle."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                border: none;
                border-radius: 18px;
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff6b5e;
            }
            QPushButton:pressed {
                background-color: #cc2f24;
            }
        """)
        self.setText("✕")
        self.clicked.connect(self.close_app)
    
    def close_app(self):
        QApplication.quit()


class SettingsButton(QPushButton):
    """Settings button with account SVG icon."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 23px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        # Add shadow to settings button
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        svg_white = colorize_svg(ACCOUNT_SVG, "#ffffff")
        self._svg_renderer = QSvgRenderer(QByteArray(svg_white.encode()))
    

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 24
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        self._svg_renderer.render(painter, QRectF(x, y, size, size))

class ChatButton(QPushButton):
    """Chat button with badge for unread messages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 28px;
                font-size: 22px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        svg_white = colorize_svg(CHAT_SVG, "#ffffff")
        self._svg_renderer = QSvgRenderer(QByteArray(svg_white.encode()))
        
        # Badge for unread count
        self.badge = QLabel(self)
        self.badge.setFixedSize(22, 22)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet("""
            background-color: #f72585;
            border-radius: 11px;
            color: white;
            font-size: 11px;
            font-weight: 700;
        """)
        self.badge.move(40, 2)
        self.badge.hide()
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        self.setText("💬") 

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 24
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        self._svg_renderer.render(painter, QRectF(x, y, size, size))
class OceanBlueTabBar(QWidget):
    """Ocean blue styled switch tabs for Company/Personal - 1.5x size"""
    
    tab_changed = Signal(str)  # Emits "company" or "personal"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Increased height by 1.5x: 28 * 1.5 = 42
        self.setFixedHeight(42)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
        # Tab container - increased height by 1.5x
        self.tab_container = QFrame(self)
        self.tab_container.setFixedHeight(42)
        self.tab_container.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 15, 26, 0.6);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 21px;
            }
        """)
        
        # Layout for tabs inside container
        self.tab_layout = QHBoxLayout(self.tab_container)
        self.tab_layout.setSpacing(3)  # 2 * 1.5 = 3
        self.tab_layout.setContentsMargins(5, 5, 5, 5)  # 3 * 1.5 ≈ 5
        
        # Create tabs
        self.tabs = []
        self.tab_names = ["Company", "Personal"]
        self.active_index = 0
        
        # Create the slider - increased height
        self.slider = QFrame(self.tab_container)
        self.slider.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #60a5fa, stop:1 #2563eb);
                border-radius: 15px;
            }
        """)
        self.slider.hide()
        
        # Create tab buttons - increased height and padding
        for i, name in enumerate(self.tab_names):
            btn = QPushButton(name)
            btn.setFixedHeight(32)  # 22 * 1.5 = 33 ≈ 32
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self.get_tab_style(i == 0))
            btn.clicked.connect(lambda checked=False, idx=i: self.switch_tab(idx))
            self.tab_layout.addWidget(btn)
            self.tabs.append(btn)
        
        # Set container layout
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.tab_container)
        
        # Initialize slider position after layout is done
        QTimer.singleShot(100, self.init_slider)
        
        # Animation for slider
        self.animation = QPropertyAnimation(self.slider, b"geometry")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
    
    def get_tab_style(self, is_active):
        if is_active:
            return """
                QPushButton {
                    background: transparent;
                    color: #ffffff;
                    border: none;
                    border-radius: 15px;
                    font-weight: 700;
                    font-size: 13px;
                    padding: 0 27px;
                    letter-spacing: 0.3px;
                }
                QPushButton:hover {
                    color: #ffffff;
                }
            """
        else:
            return """
                QPushButton {
                    background: transparent;
                    color: #94a3b8;
                    border: none;
                    border-radius: 15px;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 0 27px;
                    letter-spacing: 0.3px;
                }
                QPushButton:hover {
                    color: #bfdbfe;
                }
            """
    
    def init_slider(self):
        """Initialize slider position after layout is complete"""
        if not self.tabs:
            return
        
        # Get the first tab's geometry (relative to container)
        first_tab = self.tabs[0]
        tab_rect = first_tab.geometry()
        
        # Slider should exactly match the tab's position and size
        self.slider.setGeometry(tab_rect)
        self.slider.show()
        
        # Ensure slider is behind buttons
        self.slider.lower()
        for tab in self.tabs:
            tab.raise_()
    
    def switch_tab(self, index):
        """Switch to tab at given index with animation"""
        if index == self.active_index:
            return
            
        self.active_index = index
        
        # Update tab styles
        for i, tab in enumerate(self.tabs):
            tab.setStyleSheet(self.get_tab_style(i == index))
        
        # Animate slider to new position
        target_tab = self.tabs[index]
        target_rect = target_tab.geometry()
        
        self.animation.setEndValue(target_rect)
        self.animation.start()
        
        # Emit signal with tab name
        self.tab_changed.emit(self.tab_names[index].lower())
    
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        if self.slider.isVisible() and self.tabs:
            # Update slider position on resize
            current_tab = self.tabs[self.active_index]
            self.slider.setGeometry(current_tab.geometry())
            # Keep slider behind
            self.slider.lower()
            for tab in self.tabs:
                tab.raise_()


class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Futuristic Dashboard | TM")

        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_rect = screen.geometry()
            self.setGeometry(screen_rect)
            self.setFixedSize(screen_rect.size())
        else:
            self.setMinimumSize(1100, 650)
        
        # Open in full screen mode to match the screen dimensions
        self.setWindowState(Qt.WindowState.WindowFullScreen)

        # Current active tab
        self.current_tab = "company"  # "company" or "personal"
        # Current active dock button index
        self.current_dock_index = 0
        
        # Add theme tracking
        self.current_theme = "dashboard"  # "dashboard" or "feedback"

        # Frameless window with transparent background (outside the card)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Central widget - completely transparent
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)

        # Main layout with transparent background
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Dashboard container (the card) - this will have the gradient background
        self.dashboard = QFrame()
        self.dashboard.setObjectName("dashboard")
        self.dashboard.setStyleSheet("""
            QFrame#dashboard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #000000,
                    stop:0.4 #04007a,
                    stop:0.65 #1510cc,
                    stop:0.85 #7f8fff,
                    stop:1 #bcc6ff);
                border-radius: 48px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)
        main_layout.addWidget(self.dashboard)

        # Dashboard inner layout
        dock_layout = QVBoxLayout(self.dashboard)
        dock_layout.setContentsMargins(0, 0, 0, 0)
        dock_layout.setSpacing(0)

        # Create UI sections
        self.create_top_nav(dock_layout)
        self.create_hero_visual(dock_layout)
        
        # Shadow effect for the whole dashboard
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 30)
        self.dashboard.setGraphicsEffect(shadow)

        # For window dragging (only when clicking on top nav area)
        self.drag_position = None

    def _clear_hero_layout(self):
        """Clear the hero layout, preserving the feedback container if it exists."""
        for i in reversed(range(self.hero_layout.count())):
            item = self.hero_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                # If this is the feedback container, just remove it from layout
                if hasattr(self, 'feedback_container') and widget is self.feedback_container:
                    self.hero_layout.takeAt(i)
                    widget.setParent(None)  # detach but keep alive
                else:
                    widget.deleteLater()

    def resizeEvent(self, event: QResizeEvent):
        """Update bottom dock height and chat panel position when resizing"""
        super().resizeEvent(event)
        self.update_bottom_dock_height()
        # Update chat panel position if it exists
        if hasattr(self, 'chat_panel'):
            # Update panel size and position
            if self.chat_panel.isVisible() and not self.chat_panel.animation.state():
                self.chat_panel.setGeometry(
                    self.width() - self.chat_panel.width(), 0,
                    self.chat_panel.width(), self.height()
                )
            # Update backdrop
            if hasattr(self.chat_panel, 'backdrop'):
                self.chat_panel.backdrop.setGeometry(0, 0, self.width(), self.height())
    
    def update_bottom_dock_height(self):
        """Keep bottom dock at a fixed height."""
        if hasattr(self, 'bottom_dock'):
            self.bottom_dock.setFixedHeight(100)
    
    def switch_background_theme(self, checked):
        """Switch between dashboard gradient and feedback gradient using toggle switch."""
        if checked:
            # Switch to feedback gradient (lighter theme)
            self.dashboard.setStyleSheet("""
                QFrame#dashboard {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a78bfa,
                        stop:0.3 #c4b5fd,
                        stop:0.5 #60a5fa,
                        stop:0.7 #38bdf8,
                        stop:1 #bcc6ff);
                    border-radius: 48px;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                }
            """)
            self.current_theme = "feedback"
        else:
            # Switch back to dashboard gradient (dark theme)
            self.dashboard.setStyleSheet("""
                QFrame#dashboard {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #000000,
                        stop:0.4 #04007a,
                        stop:0.65 #1510cc,
                        stop:0.85 #7f8fff,
                        stop:1 #bcc6ff);
                    border-radius: 48px;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                }
            """)
            self.current_theme = "dashboard"
    
    def switch_tab(self, tab_name):
        """Switch between company and personal tabs"""
        if tab_name == self.current_tab:
            return
        
        self.current_tab = tab_name
        
        # Update content for selected tab
        self.update_content_for_tab(tab_name)
    
    def switch_dock_button(self, index):
        """Switch between dock buttons"""
        if index == self.current_dock_index:
            return
        
        # Deactivate current button
        self.dock_buttons[self.current_dock_index].set_active(False)
        # Activate new button
        self.dock_buttons[index].set_active(True)
        # Update current index
        self.current_dock_index = index
        
        # Update content based on selected dock button
        self.update_dock_content(index)
    
    def on_dock_button_clicked(self):
        """Handle dock button clicks using sender()"""
        button = self.sender()
        if button and hasattr(button, 'button_index'):
            self.switch_dock_button(button.button_index)
    
    def update_dock_content(self, index):
        """Update hero area content based on selected dock button"""
        self._clear_hero_layout()

        # Special case: Chat button (index 3) toggles the chat panel
        if index == 3:
            self.toggle_chat_panel()
            # Show a placeholder content
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title = QLabel("Chat")
            title.setStyleSheet("color: white; font-size: 48px; font-weight: 700; background: transparent;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle = QLabel("Chat panel is now open on the right side.")
            subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 18px; background: transparent;")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setWordWrap(True)
            content_layout.addWidget(title)
            content_layout.addSpacing(20)
            content_layout.addWidget(subtitle)
            self.hero_layout.addWidget(content_widget)
            return

        # Dock names for the 5 buttons: Classroom, Quiz, Poll, Chat, Account
        dock_names = ["Classroom", "Quiz", "Poll", "Chat", "Account"]
        
        # Create content based on selected dock button
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel(dock_names[index])
        title.setStyleSheet("color: white; font-size: 48px; font-weight: 700; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel(f"You selected the {dock_names[index]} section. This area would display relevant content.")
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 18px; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        
        content_layout.addWidget(title)
        content_layout.addSpacing(20)
        content_layout.addWidget(subtitle)
        
        # Add specific info based on index
        if index == 0:  # Classroom
            info = QLabel("• Live classroom stream\n• Student list\n• Class materials")
            info.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 16px; background: transparent;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addSpacing(30)
            content_layout.addWidget(info)
        elif index == 1:  # Quiz
            info = QLabel("• Create quizzes\n• View results\n• Question bank")
            info.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 16px; background: transparent;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addSpacing(30)
            content_layout.addWidget(info)
        elif index == 2:  # Poll
            info = QLabel("• Create polls\n• Real-time results\n• Student feedback")
            info.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 16px; background: transparent;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addSpacing(30)
            content_layout.addWidget(info)
        elif index == 4:  # Account
            info = QLabel("• Profile settings\n• Account management\n• Logout")
            info.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 16px; background: transparent;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addSpacing(30)
            content_layout.addWidget(info)
        
        self.hero_layout.addWidget(content_widget)
    
    def update_content_for_tab(self, tab_name):
        """Update the hero area content based on selected tab"""
        self._clear_hero_layout()
        
        if tab_name == "company":
            # Company tab content
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            title = QLabel("Company Dashboard")
            title.setStyleSheet("color: white; font-size: 48px; font-weight: 700; background: transparent;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            subtitle = QLabel("Manage your business analytics, team performance, and company metrics")
            subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 18px; background: transparent;")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setWordWrap(True)
            
            stats_widget = QWidget()
            stats_layout = QHBoxLayout(stats_widget)
            stats_layout.setSpacing(40)
            
            # Sample stats for company
            stats = [
                ("Revenue", "$2.4M", "+23%"),
                ("Users", "45.2K", "+12%"),
                ("Growth", "34%", "+5%")
            ]
            
            for stat_name, stat_value, stat_change in stats:
                stat_card = QFrame()
                stat_card.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.08);
                        border-radius: 20px;
                        padding: 20px;
                    }
                """)
                stat_card_layout = QVBoxLayout(stat_card)
                
                name_label = QLabel(stat_name)
                name_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 14px; background: transparent;")
                
                value_label = QLabel(stat_value)
                value_label.setStyleSheet("color: white; font-size: 32px; font-weight: 700; background: transparent;")
                
                change_label = QLabel(stat_change)
                change_label.setStyleSheet("color: #4ade80; font-size: 14px; background: transparent;")
                
                stat_card_layout.addWidget(name_label)
                stat_card_layout.addWidget(value_label)
                stat_card_layout.addWidget(change_label)
                stat_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                stats_layout.addWidget(stat_card)
            
            content_layout.addWidget(title)
            content_layout.addSpacing(20)
            content_layout.addWidget(subtitle)
            content_layout.addSpacing(40)
            content_layout.addWidget(stats_widget)
            
        else:
            # Personal tab content
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            title = QLabel("Personal Dashboard")
            title.setStyleSheet("color: white; font-size: 48px; font-weight: 700; background: transparent;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            subtitle = QLabel("Track your personal goals, habits, daily tasks, and achievements")
            subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 18px; background: transparent;")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setWordWrap(True)
            
            tasks_widget = QWidget()
            tasks_layout = QVBoxLayout(tasks_widget)
            tasks_layout.setSpacing(15)
            
            # Sample personal tasks
            tasks = [
                ("Complete project proposal", "High Priority", "#ef4444"),
                ("Morning meditation", "Daily", "#10b981"),
                ("Read 20 pages", "In Progress", "#f59e0b")
            ]
            
            for task_name, task_status, status_color in tasks:
                task_card = QFrame()
                task_card.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.08);
                        border-radius: 15px;
                        padding: 15px;
                    }
                """)
                task_card_layout = QHBoxLayout(task_card)
                
                task_label = QLabel(task_name)
                task_label.setStyleSheet("color: white; font-size: 16px; background: transparent;")
                
                status_label = QLabel(task_status)
                status_label.setStyleSheet(f"color: {status_color}; font-size: 14px; font-weight: 500; background: transparent;")
                status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                task_card_layout.addWidget(task_label)
                task_card_layout.addStretch()
                task_card_layout.addWidget(status_label)
                
                tasks_layout.addWidget(task_card)
            
            content_layout.addWidget(title)
            content_layout.addSpacing(20)
            content_layout.addWidget(subtitle)
            content_layout.addSpacing(40)
            content_layout.addWidget(tasks_widget)
        
        self.hero_layout.addWidget(content_widget)

    def create_top_nav(self, parent_layout):
        top = QWidget()
        top.setFixedHeight(72)
        top.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        top.setStyleSheet("background: transparent;")
        # Make the top bar draggable
        top.mousePressEvent = self.drag_start
        top.mouseMoveEvent = self.drag_move
        layout = QHBoxLayout(top)
        layout.setContentsMargins(28, 0, 20, 0)

        # Logo container with close and minimize buttons
        logo_container = QWidget()
        logo_container.setStyleSheet("background: transparent;")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(12)
        
        # Red close button
        close_btn = CloseButton()
        logo_layout.addWidget(close_btn)
        
        # Yellow minimize button
        minimize_btn = MinimizeButton()
        logo_layout.addWidget(minimize_btn)

        # Green maximize button
        maximize_btn = MaximizeButton()
        logo_layout.addWidget(maximize_btn)
        
        logo_text = QLabel("Student Studio")
        logo_text.setStyleSheet("color: white; font-size: 20px; font-weight: 700; letter-spacing: -0.3px; background: transparent;")
        logo_layout.addWidget(logo_text)
        layout.addWidget(logo_container)
        layout.addStretch()

        # Right controls - toggle switch and buttons
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # Add toggle switch for theme
        self.theme_toggle = ToggleSwitch()
        self.theme_toggle.toggled.connect(self.switch_background_theme)
        right_layout.addWidget(self.theme_toggle)
        
        # Notification button
        notif_btn = IconButton(self.create_bell_icon())
        right_layout.addWidget(notif_btn)
        
        # Chat button (NEW) - keep as quick toggle
        self.chat_btn = ChatButton()
        self.chat_btn.clicked.connect(self.toggle_chat_panel)
        right_layout.addWidget(self.chat_btn)
        
        # Create chat panel
        self.chat_panel = ChatPanel(self)
        
        # Store badge reference for chat panel to update
        self.chat_badge = self.chat_btn.badge
        
        # Notification dot
        dot = QLabel(notif_btn)
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: white; border-radius: 4px;")
        dot.move(40, 8)
        
        # Add the right widget with alignment to the right edge
        layout.addWidget(right, alignment=Qt.AlignmentFlag.AlignRight)

        parent_layout.addWidget(top)

    def toggle_chat_panel(self):
        """Toggle the chat panel visibility."""
        if hasattr(self, 'chat_panel'):
            self.chat_panel.toggle_panel()

    def create_hero_visual(self, parent_layout):
        # Hero area container with layout - ZERO MARGINS for full width content
        hero = QWidget()
        hero.setMinimumHeight(400)
        hero.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        hero.setStyleSheet("background: transparent;")
        
        # Create layout for hero content - NO MARGINS so modules take full width
        self.hero_layout = QVBoxLayout(hero)
        # Set ALL margins to ZERO for full width content
        self.hero_layout.setContentsMargins(0, 0, 0, 0)
        self.hero_layout.setSpacing(0)
        
        parent_layout.addWidget(hero, 1)
        
        # Create bottom dock after hero
        self.create_bottom_dock(parent_layout)
        
        # Initialize with company tab content
        self.update_content_for_tab("company")

    def create_bottom_dock(self, parent_layout):
        # Use QFrame for better styling control with border-radius
        self.bottom_dock = QFrame()
        self.bottom_dock.setObjectName("bottomDock")
        # Set initial height (will be updated by resizeEvent)
        self.bottom_dock.setFixedHeight(100)
        # Set stylesheet with border-radius that matches the dashboard card's bottom corners
        self.bottom_dock.setStyleSheet("""
            QFrame#bottomDock {
                background-color: #070707;
                border-radius: 0 0 48px 48px;
            }
        """)
        
        # Enable translucent background for smooth rounded corners
        self.bottom_dock.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.bottom_dock.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.bottom_dock.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        layout = QHBoxLayout(self.bottom_dock)
        layout.setContentsMargins(28, 0, 28, 0)

        # Overview label
        overview = QLabel("Paltigo")
        overview.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: 500;
            font-family: 'Courier New', monospace;
            letter-spacing: -0.5px;
            background: transparent;
        """)
        layout.addWidget(overview)

        # Dock icons (5 buttons: Classroom, Quiz, Poll, Chat, Account)
        icons_container = QWidget()
        icons_container.setStyleSheet("background: transparent;")
        icons_layout = QHBoxLayout(icons_container)
        icons_layout.setSpacing(10)
        
        # Only 5 icons: Classroom, Quiz, Poll, Chat, Account
        icon_paths_list = [
            self.create_grid_icon(),    # 0: Classroom
            self.create_wave_icon(),    # 1: Quiz
            self.create_bars_icon(),    # 2: Poll
            self.create_chat_icon(),    # 3: Chat - HIDDEN (not added to layout)
            self.create_user_icon(),    # 4: Account
        ]
        self.dock_buttons = []
        for i, paths in enumerate(icon_paths_list):
            svg = None
            if i == 0:
                svg = GRID_OVERVIEW_SVG      # Grid / Overview
            elif i == 1:
                svg = INFO_HELP_SVG          # Info / Help  (change index if you want it elsewhere)
            elif i == 4:
                svg = ACCOUNT_SVG            # Account
            btn = DockCircle(paths, icon_svg=svg, button_index=i)
            if i == 0:
                btn.set_active(True)
            btn.clicked.connect(self.on_dock_button_clicked)
            self.dock_buttons.append(btn)
            
            # Skip adding the Chat button (index 3) to the layout - it's hidden
            if i != 3:
                icons_layout.addWidget(btn)

        layout.addWidget(icons_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Right side (empty)
        right_container = QWidget()
        right_container.setStyleSheet("background: transparent;")
        right_container.setFixedHeight(100)
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        layout.addWidget(right_container)

        parent_layout.addWidget(self.bottom_dock)
        self.update_bottom_dock_height()




    # ---------- Icon path creators (each returns a LIST of QPainterPath) ----------
    def create_search_icon(self):
        path = QPainterPath()
        path.addEllipse(3, 3, 16, 16)
        path.moveTo(16.65, 16.65)
        path.lineTo(21, 21)
        return [path]

    def create_bell_icon(self):
        path = QPainterPath()
        path.moveTo(18, 8)
        path.cubicTo(18, 4, 14, 2, 12, 2)
        path.cubicTo(10, 2, 6, 4, 6, 8)
        path.lineTo(3, 17)
        path.lineTo(21, 17)
        path.lineTo(18, 8)
        path.moveTo(13.73, 21)
        path.arcTo(11.54, 19, 2.92, 2.92, 0, 180)
        return [path]

    def create_grid_icon(self):
        path = QPainterPath()
        path.addRect(3, 3, 7, 7)
        path.addRect(14, 3, 7, 7)
        path.addRect(14, 14, 7, 7)
        path.addRect(3, 14, 7, 7)
        return [path]

    def create_wave_icon(self):
        path = QPainterPath()
        path.moveTo(2, 12)
        path.lineTo(6, 12)
        path.lineTo(9, 21)
        path.lineTo(15, 3)
        path.lineTo(18, 12)
        path.lineTo(22, 12)
        return [path]

    def create_bars_icon(self):
        path = QPainterPath()
        path.moveTo(12, 20)
        path.lineTo(12, 10)
        path.moveTo(18, 20)
        path.lineTo(18, 4)
        path.moveTo(6, 20)
        path.lineTo(6, 16)
        return [path]

    def create_clock_icon(self):
        path = QPainterPath()
        path.addEllipse(2, 2, 20, 20)
        path.moveTo(12, 6)
        path.lineTo(12, 12)
        path.lineTo(16, 14)
        return [path]

    def create_moon_icon(self):
        path = QPainterPath()
        # Create a crescent moon shape
        path.moveTo(21, 12.79)
        path.arcTo(11.21, 3, 20, 20, 0, 360)
        return [path]

    def create_star_icon(self):
        path = QPainterPath()
        # Star shape
        points = [
            (12, 3),
            (14.0357, 8.1615),
            (14.4614, 9.0771),
            (14.9229, 9.5386),
            (15.8385, 9.9643),
            (15.8385, 14.0357),
            (14.9229, 14.4614),
            (14.4614, 14.9229),
            (14.0357, 15.8385),
            (12, 21),
            (9.96432, 15.8385),
            (9.53859, 14.9229),
            (9.0771, 14.4614),
            (8.16153, 14.0357),
            (8.16153, 9.9643),
            (9.0771, 9.5386),
            (9.53859, 9.0771),
            (9.96432, 8.1615),
            (12, 3)
        ]
        for i, (x, y) in enumerate(points):
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        return [path]

    def create_email_icon(self):
        path = QPainterPath()
        path.addRect(2, 4, 20, 14)
        path.moveTo(2, 6)
        path.lineTo(12, 13)
        path.lineTo(22, 6)
        return [path]

    def create_chat_icon(self):
        """Creates a chat bubble icon."""
        path = QPainterPath()
        # Draw a speech bubble with an ellipse and a small triangle
        path.addEllipse(2, 4, 20, 14)          # bubble body
        path.moveTo(6, 18)
        path.lineTo(10, 22)
        path.lineTo(14, 18)
        path.closeSubpath()
        return [path]

    def create_user_icon(self):
        """Creates a user/account icon."""
        path = QPainterPath()
        # Head (circle)
        path.addEllipse(7, 3, 10, 10)
        # Body (shoulders arc)
        path.moveTo(3, 18)
        path.arcTo(3, 14, 18, 12, 0, 180)
        return [path]

    # ---------- Window dragging ----------
    def drag_start(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint()

    def drag_move(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            delta = event.globalPosition().toPoint() - self.drag_position
            self.move(self.pos() + delta)
            self.drag_position = event.globalPosition().toPoint()

    def closeEvent(self, event):
        event.accept()


def main():
    app = QApplication(sys.argv)
    # Set default font
    font = QFont("Inter", 10)
    app.setFont(font)
    window = Dashboard()
    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()