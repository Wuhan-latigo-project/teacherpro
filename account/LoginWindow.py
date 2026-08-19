import sys
import json
from account_config import account_config
API_BASE_URL = account_config.API_BASE_URL
import os
import requests
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from ApiWorker import ApiWorker
from SoundManager import sound_manager
from account_config import account_config


class GradientTextLabel(QLabel):
    def __init__(self, segments, parent=None):
        super().__init__(parent)
        self.segments = segments
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        width = sum(metrics.horizontalAdvance(text) for text, _ in self.segments)
        return QSize(width, metrics.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = self.font()
        painter.setFont(font)
        metrics = QFontMetrics(font)
        total_width = sum(metrics.horizontalAdvance(text) for text, _ in self.segments)
        x = max(0, (self.width() - total_width) / 2)
        y = (self.height() + metrics.ascent() - metrics.descent()) / 2

        for text, stops in self.segments:
            segment_width = metrics.horizontalAdvance(text)
            gradient = QLinearGradient(x, 0, x + segment_width, 0)
            for position, color in stops:
                gradient.setColorAt(position, QColor(color))
            painter.setPen(QPen(QBrush(gradient), 0))
            painter.drawText(QPointF(x, y), text)
            x += segment_width


class LoginWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Variables for window dragging
        self.dragging = False
        self.drag_position = None
        
        # Forgot password state
        self.reset_verification_id = None
        self.reset_email = ""
        self.is_reset_verified = False
        
        # Make it a top-level window with frameless hint and translucent background
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set a proper background with white color and ensure it's opaque
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Create a main container with white background and smooth corners
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("background: transparent;")
        # Main layout with proper margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a container widget for all content with white background
        container = QWidget()
        container.setObjectName("loginContainer")
        container.setStyleSheet("""
            QWidget#loginContainer {
                background-color: white;
                border-radius: 40px;
            }
        """)
        
        # Add shadow effect to the container
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 0, 40, 20)
        container_layout.setSpacing(3)

        # Create a top bar with a fixed spacer and close button
        top_bar = QWidget()
        top_bar.setAttribute(Qt.WA_TranslucentBackground, True)
        top_bar.setStyleSheet("background: transparent;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)

        self.drag_area = QWidget()
        self.drag_area.setFixedHeight(24)
        self.drag_area.setStyleSheet("background: transparent;")
        self.drag_area.setCursor(Qt.ArrowCursor)
        top_bar_layout.addWidget(self.drag_area)

        top_bar_layout.addStretch()

        self.close_btn = QPushButton("x")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #1d1d1f;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #f2f2f7;
            }
        """)
        self.close_btn.clicked.connect(self.force_close_application)
        top_bar_layout.addWidget(self.close_btn)

        container_layout.addWidget(top_bar)

        # Stacked widget for login and forgot password views
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")
        
        # Create login view
        self.login_view = self.create_login_view()
        self.stacked_widget.addWidget(self.login_view)
        
        # Create forgot password view
        self.forgot_view = self.create_forgot_password_view()
        self.stacked_widget.addWidget(self.forgot_view)
        
        container_layout.addWidget(self.stacked_widget)

        # Footer
        footer_label = QLabel("© 2026 Latigo Platform. All rights reserved.")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("""
            QLabel {
                color: #86868b;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
                padding: 3px 0px 0px 0px;
            }
        """)
        container_layout.addWidget(footer_label)

        # Add the container to the main layout
        layout.addWidget(container)

        # Set fixed size
        self.setFixedSize(500, 520)
        

    
    def create_login_view(self):
        """Create the login view widget"""
        view = QWidget()
        view.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Apple-style header
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        welcome_label = GradientTextLabel([
            ("welcom to ", [(0.0, "#ffffff"), (0.5, "#7ab8d4"), (1.0, "#c8e0f0")]),
            ("paltigo", [(0.0, "#f5a623"), (1.0, "#f7c948")])
        ])
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 34px;
                font-weight: 700;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        header_layout.addWidget(welcome_label)

        subtitle_label = QLabel("Sign in to your account to continue")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #6e6e73;
                background: transparent;
                padding: 0px;
                margin: 0px 0px 3px 0px;
                letter-spacing: -0.2px;
            }
        """)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_container)

        # Form container with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f7;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(0, 0, 5, 0)
        form_layout.setSpacing(8)

        # Email field
        email_container = QWidget()
        email_container.setStyleSheet("background: transparent;")
        email_container_layout = QVBoxLayout(email_container)
        email_container_layout.setContentsMargins(0, 0, 0, 0)
        email_container_layout.setSpacing(3)
        
        email_label = QLabel("Email")
        email_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                padding-left: 2px;
            }
        """)
        email_container_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setFixedHeight(40)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f7;
                border: 0.5px solid #d2d2d7;
                border-radius: 10px;
                padding: 0px 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: white;
            }
        """)
        email_container_layout.addWidget(self.email_input)
        
        form_layout.addWidget(email_container)

        # Password field
        password_container = QWidget()
        password_container.setStyleSheet("background: transparent;")
        password_container_layout = QVBoxLayout(password_container)
        password_container_layout.setContentsMargins(0, 0, 0, 0)
        password_container_layout.setSpacing(3)
        
        password_label = QLabel("Password")
        password_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                padding-left: 2px;
            }
        """)
        password_container_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f7;
                border: 0.5px solid #d2d2d7;
                border-radius: 10px;
                padding: 0px 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: white;
            }
        """)
        password_container_layout.addWidget(self.password_input)
        
        form_layout.addWidget(password_container)

        # Remember me checkbox
        remember_container = QWidget()
        remember_container.setStyleSheet("background: transparent;")
        remember_layout = QHBoxLayout(remember_container)
        remember_layout.setContentsMargins(0, 0, 0, 0)
        remember_layout.setSpacing(0)
        
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #d2d2d7;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #0071e3;
                border: 1px solid #0071e3;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #0071e3;
            }
        """)
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        
        form_layout.addWidget(remember_container)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(40)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: white;
                margin-top: 2px;
            }
            QPushButton:hover {
                background-color: #0077ed;
            }
            QPushButton:pressed {
                background-color: #0068c9;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)
        self.login_btn.clicked.connect(self.login)
        form_layout.addWidget(self.login_btn)

        # Forgot password button
        self.forgot_password_btn = QPushButton("Forgot password?")
        self.forgot_password_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_password_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #0071e3;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                text-align: right;
                padding: 4px;
            }
            QPushButton:hover {
                color: #0077ed;
                text-decoration: underline;
            }
        """)
        self.forgot_password_btn.clicked.connect(self.show_forgot_password)
        form_layout.addWidget(self.forgot_password_btn, alignment=Qt.AlignRight)

        # Separator
        separator_container = QWidget()
        separator_container.setStyleSheet("background: transparent;")
        separator_layout = QHBoxLayout(separator_container)
        separator_layout.setContentsMargins(0, 2, 0, 2)
        separator_layout.setSpacing(0)
        
        line_left = QFrame()
        line_left.setFrameShape(QFrame.HLine)
        line_left.setFixedHeight(1)
        line_left.setStyleSheet("background-color: #d2d2d7;")
        
        or_label = QLabel("or")
        or_label.setAlignment(Qt.AlignCenter)
        or_label.setStyleSheet("""
            QLabel {
                color: #86868b;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                padding: 0px 15px;
                background: transparent;
                min-width: 20px;
            }
        """)
        
        line_right = QFrame()
        line_right.setFrameShape(QFrame.HLine)
        line_right.setFixedHeight(1)
        line_right.setStyleSheet("background-color: #d2d2d7;")
        
        separator_layout.addWidget(line_left, 1)
        separator_layout.addWidget(or_label, 0)
        separator_layout.addWidget(line_right, 1)
        
        form_layout.addWidget(separator_container)

        # Sign up button
        self.signup_btn = QPushButton("Create New Account")
        self.signup_btn.setFixedHeight(40)
        self.signup_btn.setCursor(Qt.PointingHandCursor)
        self.signup_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #0071e3;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #0071e3;
                margin-bottom: 2px;
            }
            QPushButton:hover {
                background-color: rgba(0, 113, 227, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(0, 113, 227, 0.2);
            }
        """)
        self.signup_btn.clicked.connect(self.main_window.show_registration)
        form_layout.addWidget(self.signup_btn)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        return view
    
    def create_forgot_password_view(self):
        """Create the forgot password view"""
        view = QWidget()
        view.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Back button row
        back_row = QHBoxLayout()
        back_row.setContentsMargins(0, 0, 0, 0)
        
        self.back_to_login_btn = QPushButton("← Back to Login")
        self.back_to_login_btn.setCursor(Qt.PointingHandCursor)
        self.back_to_login_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #0071e3;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                padding: 4px;
                text-align: left;
            }
            QPushButton:hover {
                color: #0077ed;
                text-decoration: underline;
            }
        """)
        self.back_to_login_btn.clicked.connect(self.show_login_view)
        back_row.addWidget(self.back_to_login_btn)
        back_row.addStretch()
        header_layout.addLayout(back_row)
        
        title_label = QLabel("Reset Password")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #000000;
                letter-spacing: -0.5px;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Enter your email to receive a verification code")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #6e6e73;
                background: transparent;
                padding: 0px;
                margin: 0px 0px 10px 0px;
            }
        """)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_container)

        # Form container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(0, 0, 5, 0)
        form_layout.setSpacing(10)

        # Email field for reset
        reset_email_container = QWidget()
        reset_email_container.setStyleSheet("background: transparent;")
        reset_email_layout = QVBoxLayout(reset_email_container)
        reset_email_layout.setContentsMargins(0, 0, 0, 0)
        reset_email_layout.setSpacing(3)
        
        reset_email_label = QLabel("Email Address")
        reset_email_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                padding-left: 2px;
            }
        """)
        reset_email_layout.addWidget(reset_email_label)
        
        self.reset_email_input = QLineEdit()
        self.reset_email_input.setPlaceholderText("Enter your email")
        self.reset_email_input.setFixedHeight(40)
        self.reset_email_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f7;
                border: 0.5px solid #d2d2d7;
                border-radius: 10px;
                padding: 0px 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: white;
            }
        """)
        reset_email_layout.addWidget(self.reset_email_input)
        form_layout.addWidget(reset_email_container)

        # Verification code section (hidden initially)
        self.verification_container = QWidget()
        self.verification_container.setVisible(False)
        self.verification_container.setStyleSheet("background: transparent;")
        verification_layout = QVBoxLayout(self.verification_container)
        verification_layout.setContentsMargins(0, 0, 0, 0)
        verification_layout.setSpacing(3)
        
        verification_label = QLabel("Verification Code")
        verification_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                padding-left: 2px;
            }
        """)
        verification_layout.addWidget(verification_label)
        
        code_container = QWidget()
        code_container.setStyleSheet("background: transparent;")
        code_layout = QHBoxLayout(code_container)
        code_layout.setContentsMargins(0, 0, 0, 0)
        code_layout.setSpacing(8)
        
        self.reset_code_input = QLineEdit()
        self.reset_code_input.setPlaceholderText("6-digit code")
        self.reset_code_input.setFixedHeight(40)
        self.reset_code_input.setMaxLength(6)
        self.reset_code_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f7;
                border: 0.5px solid #d2d2d7;
                border-radius: 10px;
                padding: 0px 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: white;
            }
        """)
        self.reset_code_input.textChanged.connect(self.on_reset_code_changed)
        code_layout.addWidget(self.reset_code_input)
        
        self.resend_code_btn = QPushButton("Resend")
        self.resend_code_btn.setFixedHeight(40)
        self.resend_code_btn.setFixedWidth(80)
        self.resend_code_btn.setCursor(Qt.PointingHandCursor)
        self.resend_code_btn.setEnabled(False)
        self.resend_code_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #0077ed;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.resend_code_btn.clicked.connect(self.resend_reset_code)
        code_layout.addWidget(self.resend_code_btn)
        
        verification_layout.addWidget(code_container)
        
        # Timer for cooldown
        self.cooldown_timer = QTimer()
        self.cooldown_timer.timeout.connect(self.update_cooldown)
        self.cooldown_seconds = 30
        self.cooldown_timer_running = False
        
        self.cooldown_label = QLabel("")
        self.cooldown_label.setStyleSheet("color: #6e6e73; font-size: 12px; background: transparent;")
        verification_layout.addWidget(self.cooldown_label)
        
        form_layout.addWidget(self.verification_container)

        # New password section (hidden initially)
        self.password_reset_container = QWidget()
        self.password_reset_container.setVisible(False)
        self.password_reset_container.setStyleSheet("background: transparent;")
        password_reset_layout = QVBoxLayout(self.password_reset_container)
        password_reset_layout.setContentsMargins(0, 0, 0, 0)
        password_reset_layout.setSpacing(3)
        
        new_pass_label = QLabel("New Password")
        new_pass_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                padding-left: 2px;
            }
        """)
        password_reset_layout.addWidget(new_pass_label)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("At least 6 characters")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setFixedHeight(40)
        self.new_password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f7;
                border: 0.5px solid #d2d2d7;
                border-radius: 10px;
                padding: 0px 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: white;
            }
        """)
        password_reset_layout.addWidget(self.new_password_input)
        
        confirm_pass_label = QLabel("Confirm New Password")
        confirm_pass_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
                padding-left: 2px;
            }
        """)
        password_reset_layout.addWidget(confirm_pass_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFixedHeight(40)
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f7;
                border: 0.5px solid #d2d2d7;
                border-radius: 10px;
                padding: 0px 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #0071e3;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: white;
            }
        """)
        password_reset_layout.addWidget(self.confirm_password_input)
        
        form_layout.addWidget(self.password_reset_container)

        # Status message
        self.reset_status_label = QLabel("")
        self.reset_status_label.setWordWrap(True)
        self.reset_status_label.setStyleSheet("color: #6e6e73; font-size: 13px; background: transparent; padding: 5px;")
        form_layout.addWidget(self.reset_status_label)

        # Send Code button
        self.send_code_btn = QPushButton("Send Code")
        self.send_code_btn.setFixedHeight(40)
        self.send_code_btn.setCursor(Qt.PointingHandCursor)
        self.send_code_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #0077ed;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)
        self.send_code_btn.clicked.connect(self.send_reset_code)
        form_layout.addWidget(self.send_code_btn)

        # Reset Password button (hidden initially)
        self.reset_password_btn = QPushButton("Reset Password")
        self.reset_password_btn.setFixedHeight(40)
        self.reset_password_btn.setCursor(Qt.PointingHandCursor)
        self.reset_password_btn.setVisible(False)
        self.reset_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)
        self.reset_password_btn.clicked.connect(self.reset_password)
        form_layout.addWidget(self.reset_password_btn)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        return view
    
    def show_login_view(self):
        """Switch back to login view"""
        self.stacked_widget.setCurrentIndex(0)
        self.is_reset_verified = False
        self.reset_verification_id = None
        self.verification_container.setVisible(False)
        self.password_reset_container.setVisible(False)
        self.reset_password_btn.setVisible(False)
        self.send_code_btn.setVisible(True)
        self.reset_status_label.setText("")
        self.reset_code_input.setText("")
        self.new_password_input.setText("")
        self.confirm_password_input.setText("")
        self.reset_email_input.setText("")
        self.resend_code_btn.setEnabled(False)
        if self.cooldown_timer_running:
            self.cooldown_timer.stop()
            self.cooldown_timer_running = False
            self.cooldown_label.setText("")
    
    def show_forgot_password(self):
        """Show forgot password view"""
        sound_manager.play_click()
        self.stacked_widget.setCurrentIndex(1)
        self.is_reset_verified = False
        self.reset_verification_id = None
        self.verification_container.setVisible(False)
        self.password_reset_container.setVisible(False)
        self.reset_password_btn.setVisible(False)
        self.send_code_btn.setVisible(True)
        self.reset_status_label.setText("")
        self.reset_code_input.setText("")
        self.new_password_input.setText("")
        self.confirm_password_input.setText("")
        self.reset_email_input.setText("")
        self.resend_code_btn.setEnabled(False)
        if self.cooldown_timer_running:
            self.cooldown_timer.stop()
            self.cooldown_timer_running = False
            self.cooldown_label.setText("")

    def send_reset_code(self):
        """Send password reset verification code"""
        email = self.reset_email_input.text().strip()
        
        if not email:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Please enter your email address")
            return
        
        if "@" not in email or "." not in email:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Please enter a valid email address")
            return
        
        self.send_code_btn.setEnabled(False)
        self.send_code_btn.setText("Sending...")
        self.reset_status_label.setText("")
        self.reset_status_label.setStyleSheet("color: #6e6e73; font-size: 13px; background: transparent; padding: 5px;")
        
        try:
            # ✅ Use account_config with CSRF support
            response = account_config.post("/api/password/reset/send", data={"email": email}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    sound_manager.play_success()
                    self.reset_email = email
                    self.reset_verification_id = data.get("data", {}).get("verification_id")
                    
                    self.reset_status_label.setText("Verification code sent to your email!")
                    self.reset_status_label.setStyleSheet("color: #28a745; font-size: 13px; background: transparent; padding: 5px;")
                    
                    # Show verification input
                    self.verification_container.setVisible(True)
                    self.send_code_btn.setVisible(False)
                    self.resend_code_btn.setEnabled(False)
                    
                    # Start cooldown
                    self.cooldown_seconds = 30
                    self.cooldown_timer_running = True
                    self.cooldown_timer.start(1000)
                    self.update_cooldown()
                else:
                    sound_manager.play_error()
                    error_msg = data.get("error", "Unknown error")
                    self.reset_status_label.setText(f"Error: {error_msg}")
                    self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                    self.send_code_btn.setEnabled(True)
                    self.send_code_btn.setText("Send Code")
            elif response.status_code == 404:
                sound_manager.play_error()
                self.reset_status_label.setText("Email not found. Please check your email address.")
                self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                self.send_code_btn.setEnabled(True)
                self.send_code_btn.setText("Send Code")
            else:
                sound_manager.play_error()
                data = response.json()
                error_msg = data.get("error", f"Server error: {response.status_code}")
                self.reset_status_label.setText(f"Error: {error_msg}")
                self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                self.send_code_btn.setEnabled(True)
                self.send_code_btn.setText("Send Code")
                
        except requests.exceptions.Timeout:
            sound_manager.play_error()
            self.reset_status_label.setText("Connection timeout. Please try again.")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            self.send_code_btn.setEnabled(True)
            self.send_code_btn.setText("Send Code")
        except requests.exceptions.ConnectionError:
            sound_manager.play_error()
            self.reset_status_label.setText("Cannot connect to server. Please check your connection.")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            self.send_code_btn.setEnabled(True)
            self.send_code_btn.setText("Send Code")
        except Exception as e:
            sound_manager.play_error()
            self.reset_status_label.setText(f"Error: {str(e)}")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            self.send_code_btn.setEnabled(True)
            self.send_code_btn.setText("Send Code")
    
    def update_cooldown(self):
        """Update cooldown timer display"""
        self.cooldown_seconds -= 1
        if self.cooldown_seconds <= 0:
            self.cooldown_timer.stop()
            self.cooldown_timer_running = False
            self.resend_code_btn.setEnabled(True)
            self.cooldown_label.setText("")
        else:
            self.cooldown_label.setText(f"Resend available in {self.cooldown_seconds}s")
    
    def resend_reset_code(self):
        """Resend the verification code"""
        if not self.reset_email:
            return
        
        self.resend_code_btn.setEnabled(False)
        self.reset_status_label.setText("Resending code...")
        self.reset_status_label.setStyleSheet("color: #6e6e73; font-size: 13px; background: transparent; padding: 5px;")
        
        try:
            # ✅ Use account_config with CSRF support
            response = account_config.post("/api/password/reset/send", data={"email": self.reset_email}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    sound_manager.play_success()
                    self.reset_verification_id = data.get("data", {}).get("verification_id")
                    
                    self.reset_status_label.setText("New verification code sent!")
                    self.reset_status_label.setStyleSheet("color: #28a745; font-size: 13px; background: transparent; padding: 5px;")
                    
                    # Start cooldown
                    self.cooldown_seconds = 30
                    self.cooldown_timer_running = True
                    self.cooldown_timer.start(1000)
                    self.update_cooldown()
                    self.resend_code_btn.setEnabled(False)
                    
                    # Clear code input
                    self.reset_code_input.setText("")
                else:
                    sound_manager.play_error()
                    error_msg = data.get("error", "Unknown error")
                    self.reset_status_label.setText(f"Error: {error_msg}")
                    self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                    self.resend_code_btn.setEnabled(True)
            else:
                sound_manager.play_error()
                data = response.json()
                error_msg = data.get("error", f"Server error: {response.status_code}")
                self.reset_status_label.setText(f"Error: {error_msg}")
                self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                self.resend_code_btn.setEnabled(True)
                
        except Exception as e:
            sound_manager.play_error()
            self.reset_status_label.setText(f"Error: {str(e)}")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            self.resend_code_btn.setEnabled(True)
    
    def verify_reset_code(self):
        """Verify the reset code using the dedicated verify endpoint"""
        code = self.reset_code_input.text().strip()
        
        if len(code) != 6 or not code.isdigit():
            self.reset_status_label.setText("Please enter a valid 6-digit code")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            return
        
        if not self.reset_verification_id:
            self.reset_status_label.setText("No verification session. Please request a new code.")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            return
        
        self.reset_status_label.setText("Verifying code...")
        self.reset_status_label.setStyleSheet("color: #6e6e73; font-size: 13px; background: transparent; padding: 5px;")
        
        try:
            # ✅ Use account_config with CSRF support
            response = account_config.post("/api/password/verify-code", data={
                "email": self.reset_email,
                "verification_id": self.reset_verification_id,
                "code": code
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    sound_manager.play_success()
                    self.is_reset_verified = True
                    self.reset_status_label.setText("Code verified! Enter your new password.")
                    self.reset_status_label.setStyleSheet("color: #28a745; font-size: 13px; background: transparent; padding: 5px;")
                    
                    # Show password fields
                    self.password_reset_container.setVisible(True)
                    self.reset_password_btn.setVisible(True)
                    self.resend_code_btn.setEnabled(False)
                else:
                    sound_manager.play_error()
                    error_msg = data.get("error", "Verification failed")
                    attempts_data = data.get("data", {})
                    if attempts_data.get("attempts_left") is not None:
                        error_msg = f"{error_msg} ({attempts_data.get('attempts_left')} attempts left)"
                    self.reset_status_label.setText(f"Error: {error_msg}")
                    self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                    self.reset_code_input.setText("")
                    self.reset_code_input.setFocus()
            elif response.status_code == 401:
                sound_manager.play_error()
                data = response.json()
                error_msg = data.get("error", "Invalid code")
                attempts_data = data.get("data", {})
                if attempts_data.get("attempts_left") is not None:
                    error_msg = f"{error_msg} ({attempts_data.get('attempts_left')} attempts left)"
                self.reset_status_label.setText(f"Error: {error_msg}")
                self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                self.reset_code_input.setText("")
                self.reset_code_input.setFocus()
            else:
                sound_manager.play_error()
                data = response.json()
                error_msg = data.get("error", f"Server error: {response.status_code}")
                self.reset_status_label.setText(f"Error: {error_msg}")
                self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                
        except Exception as e:
            sound_manager.play_error()
            self.reset_status_label.setText(f"Error: {str(e)}")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
    
    def reset_password(self):
        """Reset the password"""
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        if not new_password:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Please enter a new password")
            return
        
        if len(new_password) < 6:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return
        
        if new_password != confirm_password:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        
        if not self.is_reset_verified or not self.reset_verification_id:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Please verify your code first")
            return
        
        self.reset_password_btn.setEnabled(False)
        self.reset_password_btn.setText("Resetting...")
        self.reset_status_label.setText("Resetting password...")
        self.reset_status_label.setStyleSheet("color: #6e6e73; font-size: 13px; background: transparent; padding: 5px;")
        
        try:
            # ✅ Use account_config with CSRF support
            response = account_config.post("/api/password/reset", data={
                "email": self.reset_email,
                "verification_id": self.reset_verification_id,
                "code": self.reset_code_input.text().strip(),
                "new_password": new_password
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    sound_manager.play_success()
                    QMessageBox.information(self, "Success", "Password reset successfully! You can now login with your new password.")
                    
                    # Return to login view
                    self.show_login_view()
                    
                    # Pre-fill email
                    self.email_input.setText(self.reset_email)
                else:
                    sound_manager.play_error()
                    error_msg = data.get("error", "Failed to reset password")
                    self.reset_status_label.setText(f"Error: {error_msg}")
                    self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                    self.reset_password_btn.setEnabled(True)
                    self.reset_password_btn.setText("Reset Password")
            else:
                sound_manager.play_error()
                data = response.json()
                error_msg = data.get("error", f"Server error: {response.status_code}")
                self.reset_status_label.setText(f"Error: {error_msg}")
                self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
                self.reset_password_btn.setEnabled(True)
                self.reset_password_btn.setText("Reset Password")
                
        except Exception as e:
            sound_manager.play_error()
            self.reset_status_label.setText(f"Error: {str(e)}")
            self.reset_status_label.setStyleSheet("color: #dc3545; font-size: 13px; background: transparent; padding: 5px;")
            self.reset_password_btn.setEnabled(True)
            self.reset_password_btn.setText("Reset Password")
    
    def on_reset_code_changed(self, text):
        """Handle code input change - auto-verify when 6 digits entered"""
        if len(text) == 6 and text.isdigit():
            self.verify_reset_code()
    
    # ========== Mouse events disabled to keep window fixed ==========
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def force_close_application(self):
        os._exit(0)

    # ========== Login methods ==========
    def login(self):
        """Handle login process"""
        sound_manager.play_click()
        
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Please enter email and password")
            return

        # Disable button and show loading
        self.login_btn.setText("Signing in...")
        self.login_btn.setEnabled(False)

        # Create worker for login
        worker = ApiWorker(self.api_login, email, password)
        worker.signals.result.connect(self.on_login_success)
        worker.signals.error.connect(self.on_login_error)
        worker.signals.finished.connect(self.on_login_finished)

        # Start worker
        self.main_window.thread_pool.start(worker)
    
    def api_login(self, email, password):
        """API call for login with CSRF support using account_config"""
        data = {
            "email": email,
            "password": password
        }
        
        print(f"Login attempt for: {email}")
        print(f"API URL: {account_config.API_BASE_URL}/api/login")
        
        try:
            # ✅ Use account_config with CSRF support
            response = account_config.post("/api/login", data=data, timeout=10)
            print(f"Login response status: {response.status_code}")
            print(f"Login response: {response.text[:200]}...")
            return response
            
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            # Try without verification (fallback)
            try:
                # Force SSL verification off for this request
                import ssl
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = account_config.post("/api/login", data=data, timeout=10)
                return response
            except Exception as e2:
                print(f"SSL fallback error: {e2}")
                raise
        except Exception as e:
            print(f"Login error: {e}")
            raise
    
    def on_login_success(self, response):
        """Handle successful login response"""
        if response.status_code == 200:
            response_data = response.json()

            if response_data.get("success"):
                sound_manager.play_success()
                
                # Save authentication data
                data = response_data.get("data", {})
                account_data = data.get("account", {})
                token = data.get("token")
                user_id = account_data.get("id")
                
                # ✅ Save auth data using account_config
                account_config.save_auth_data(
                    user_id=user_id,
                    access_token=token,
                    refresh_token=None,
                    expires_in=86400,  # 24 hours
                    user_data=account_data
                )
                
                # Save token to token.txt for backwards compatibility
                token_txt_path = os.path.join(os.path.dirname(__file__), "token.txt")
                try:
                    with open(token_txt_path, 'w', encoding='utf-8') as f:
                        f.write(str(token))
                except Exception as e:
                    print(f"Failed to write token.txt: {e}")

                print(f"Login successful! User ID: {user_id}")

                # Call parent's on_login_success
                tokens = {
                    "access_token": token,
                    "refresh_token": None,
                    "expires_in": 86400
                }
                self.main_window.on_login_success(account_data, tokens)
                
                # Close the login window after successful login
                self.close()
                
            else:
                sound_manager.play_error()
                QMessageBox.warning(self, "Login Failed", 
                                  response_data.get("error", "Invalid login credentials"))
        else:
            sound_manager.play_error()
            try:
                error_data = response.json()
                error_msg = error_data.get("error", f"Server error: {response.status_code}")
            except:
                error_msg = f"Server error: {response.status_code}"
            QMessageBox.warning(self, "Login Failed", error_msg)
    
    def on_login_error(self, error_msg):
        """Handle connection errors"""
        sound_manager.play_error()
        
        if "SSL" in str(error_msg):
            message = "SSL Certificate error. The server certificate is self-signed.\n\nPlease run with VERIFY_SSL=False or use a valid certificate."
        elif "timeout" in str(error_msg).lower():
            message = "Connection timeout. Please check your internet connection."
        elif "connection" in str(error_msg).lower():
            message = "Unable to connect to server. Please check:\n- Server is running\n- IP/Port is correct\n- Firewall is not blocking"
        else:
            message = f"Connection error: {error_msg}"
        
        QMessageBox.warning(self, "Connection Error", message)
    
    def on_login_finished(self):
        """Handle login completion"""
        self.login_btn.setText("Sign In")
        self.login_btn.setEnabled(True)