import sys
import json
import os
from account_config import account_config
API_BASE_URL = account_config.API_BASE_URL
import requests
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
import math

# ========== IMPORT TEACHER SELECTOR ==========
try:
    from teacherselector import TeacherSelectorDialog
    TEACHER_SELECTOR_AVAILABLE = True
    print("✅ TeacherSelectorDialog loaded in MultiStepFormWindow")
except ImportError as e:
    print(f"⚠️ TeacherSelectorDialog import failed: {e}")
    TEACHER_SELECTOR_AVAILABLE = False
    TeacherSelectorDialog = None


class AnimatedGradientPanel(QWidget):
    """A QWidget with an animated moving gradient background (blue ocean to yellow)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.start(30)  # ~33 FPS

    def _on_timeout(self):
        self._phase += 0.01
        if self._phase > 2 * math.pi:
            self._phase -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        # Animate the gradient stops
        shift = (math.sin(self._phase) + 1) / 2  # 0..1
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0 + 0.2 * shift, QColor("#1e3c72"))
        grad.setColorAt(0.3 + 0.2 * shift, QColor("#2a5298"))
        grad.setColorAt(0.7 - 0.2 * shift, QColor("#ffe53b"))
        grad.setColorAt(1.0 - 0.2 * shift, QColor("#f9d423"))
        painter.fillRect(rect, grad)
        super().paintEvent(event)


from ApiWorker import ApiWorker
from account_config import account_config

# Import sound manager
from SoundManager import sound_manager


class TermsDialog(QDialog):
    """Modern dialog for Terms & Conditions acceptance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terms & Conditions")
        self.setModal(True)
        self.setMinimumSize(550, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # Set style
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1a1a2e;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                margin-top: 10px;
            }
            QTextBrowser {
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
                background-color: #fafafa;
                font-size: 14px;
                color: #333;
                line-height: 1.5;
            }
            QCheckBox {
                font-size: 14px;
                color: #333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4361ee;
                border: 1px solid #4361ee;
            }
            QPushButton {
                background-color: #4361ee;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton#cancelBtn {
                background-color: #f0f0f0;
                color: #555;
            }
            QPushButton#cancelBtn:hover {
                background-color: #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Terms & Conditions")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Terms text (scrollable)
        self.terms_browser = QTextBrowser()
        self.terms_browser.setOpenExternalLinks(True)
        self.terms_browser.setHtml(self.get_terms_html())
        layout.addWidget(self.terms_browser, 1)
        
        # Accept checkbox
        self.accept_checkbox = QCheckBox("I have read and agree to the Terms & Conditions and Privacy Policy")
        self.accept_checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.accept_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton("Agree & Continue")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def on_checkbox_changed(self, state):
        """Enable/disable OK button based on checkbox state"""
        self.ok_btn.setEnabled(state == Qt.Checked)
    
    def get_terms_html(self):
        """Return beautiful HTML content for terms and conditions"""
        return """
        <h2 style="color:#1a1a2e; margin-bottom:10px;">Welcome to Latigo!</h2>
        <p style="margin-bottom:15px;">By using Latigo, you agree to the following terms and conditions.</p>
        
        <h3 style="color:#4361ee; margin-top:20px;">1. Account Registration</h3>
        <p>You must provide accurate, complete, and current information during registration. You are responsible for maintaining the confidentiality of your password and for all activities under your account.</p>
        
        <h3 style="color:#4361ee; margin-top:20px;">2. User Conduct</h3>
        <p>You agree to use Latigo only for lawful purposes and in a way that does not infringe the rights of others or restrict their use of the platform. Harassment, hate speech, or any form of abuse is strictly prohibited.</p>
        
        <h3 style="color:#4361ee; margin-top:20px;">3. Content Ownership</h3>
        <p>Users retain ownership of the content they create. By posting content, you grant Latigo a non-exclusive, royalty-free license to host, display, and distribute that content within the platform.</p>
        
        <h3 style="color:#4361ee; margin-top:20px;">4. Privacy Policy</h3>
        <p>We respect your privacy. Personal data collected during registration (email, name, age, role, etc.) will be used solely for platform functionality and will not be sold to third parties. See our full privacy policy for details.</p>
        
        <h3 style="color:#4361ee; margin-top:20px;">5. Termination</h3>
        <p>Latigo reserves the right to suspend or terminate accounts that violate these terms or any applicable laws.</p>
        
        <h3 style="color:#4361ee; margin-top:20px;">6. Limitation of Liability</h3>
        <p>Latigo is provided "as is" without warranties of any kind. We are not liable for any damages arising from your use of the platform.</p>
        
        <p style="margin-top:25px; font-style:italic; color:#555;">By checking the box and clicking "Agree & Continue", you acknowledge that you have read, understood, and agree to be bound by these terms.</p>
        
        <p style="margin-top:15px; font-size:12px; color:#777;">Last updated: May 2026</p>
        """
    

# ==================== VERIFICATION BRIDGE ====================
class VerificationBridge(QObject):
    """Bridge between JavaScript and Python for OTP verification"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # MultiStepFormWindow
        self.web_view = None

    @Slot()
    def pageReady(self):
        """Called when the web page is fully loaded."""
        print("Verification page ready")
        # Set the email in the OTP page
        email = self.parent_window.registration_data.get("email", "")
        if self.web_view and email:
            self.web_view.page().runJavaScript(f'setEmail("{email}")')
        # Start cooldown for resend
        self.web_view.page().runJavaScript('setResendCooldown(30)')

    @Slot(str)
    def verifyCode(self, code):
        """Called from JavaScript when the user submits a code."""
        print(f"Bridge: verifyCode called with code: {code}")
        # Call the parent window's verification method
        self.parent_window.verify_otp_code(code)

    @Slot()
    def resendCode(self):
        """Called from JavaScript when user clicks Resend."""
        print("Bridge: resendCode called")
        self.parent_window.resend_verification_code()


class MultiStepFormWindow(QWidget):
    """Simplified 4-step registration form with email verification"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Create New Account - Latigo Platform")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  # No maximize/minimize buttons, no resize
        self.setMinimumSize(900, 700)

        # Registration data
        self.registration_data = {
            "email": "",
            "password": "",
            "first_name": "",
            "last_name": "",
            "age": "",
            "role": "student",  # Default role is student
            "avatar": None,
            "study_level": "",  # For students, this will be filled
            "selected_room": None  # Will be set after teacher selection
        }

        # Verification data
        self.verification_id = None
        self.verification_expires = 300  # 5 minutes default
        self.is_verified = False

        self.current_page = 0
        self.total_pages = 4  # 4 steps now (account, profile, study level, verification)
        # Debounce timer: when user edits email, wait briefly then apply change
        self._email_debounce_timer = QTimer(self)
        self._email_debounce_timer.setSingleShot(True)
        self._email_debounce_timer.setInterval(800)  # ms
        self._email_debounce_timer.timeout.connect(self._apply_email_change)
        # When True, skip automatic send-verification on immediate navigation
        self._email_recently_changed = False

        self.setup_ui()
        sound_manager.play_notification()
        self.update_navigation()

        # Maximize the window after UI creation
        self.showMaximized()

    def setup_ui(self):
        """Two-column layout with form and verification"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== Left panel (logo/brand) ==========
        self.left_panel = AnimatedGradientPanel()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setAlignment(Qt.AlignCenter)

        # Logo text
        logo_text = QLabel("Latigo")
        logo_text.setStyleSheet("""
            font-size: 54px;
            font-weight: bold;
            color: #ffe53b;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
            text-shadow: 2px 2px 12px #1e3c72, 0 2px 8px #2a5298;
            letter-spacing: 2px;
        """)
        logo_text.setAlignment(Qt.AlignCenter)

        tagline = QLabel("Learn. Create. Grow.")
        tagline.setStyleSheet("""
            font-size: 22px;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
            margin-top: 20px;
            text-shadow: 1px 1px 8px #2a5298;
        """)
        tagline.setAlignment(Qt.AlignCenter)

        description = QLabel("Join our community of learners and teachers")
        description.setStyleSheet("""
            font-size: 15px;
            color: #fffbe6;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
            margin-top: 40px;
            text-shadow: 1px 1px 6px #1e3c72;
        """)
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)

        left_layout.addStretch()
        left_layout.addWidget(logo_text)
        left_layout.addWidget(tagline)
        left_layout.addWidget(description)
        left_layout.addStretch()

        # ========== Right panel (form) ==========
        self.right_panel = QWidget()
        self.right_panel.setObjectName("rightPanel")
        self.right_panel.setStyleSheet("""
            QWidget#rightPanel {
                background-color: white;
            }
        """)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(50, 40, 50, 40)
        right_layout.setSpacing(20)

        # Progress indicator
        self.create_progress_indicator(right_layout)

        # Stacked pages
        self.pages_container = QStackedWidget()
        self.pages_container.setMinimumHeight(500)

        self.create_page1_account()
        self.create_page2_profile()
        self.create_page3_study_level()
        self.create_page4_verification()

        right_layout.addWidget(self.pages_container)

        # Navigation buttons
        self.create_navigation_buttons(right_layout)

        # Add panels to main layout
        main_layout.addWidget(self.left_panel, 4)  # 40%
        main_layout.addWidget(self.right_panel, 6)  # 60%

    def create_progress_indicator(self, parent_layout):
        """Create progress indicator with 4 steps"""
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(10)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4361ee;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setRange(0, self.total_pages - 1)
        self.progress_bar.setValue(0)

        # Step labels
        steps_widget = QWidget()
        steps_layout = QHBoxLayout(steps_widget)
        steps_layout.setContentsMargins(0, 0, 0, 0)

        self.step_labels = []
        step_names = ["Account", "Profile", "Complete", "Verify"]
        
        for i, name in enumerate(step_names):
            step_container = QWidget()
            step_layout = QVBoxLayout(step_container)
            step_layout.setAlignment(Qt.AlignCenter)
            step_layout.setSpacing(5)
            
            step_circle = QLabel(str(i + 1))
            step_circle.setFixedSize(30, 30)
            step_circle.setAlignment(Qt.AlignCenter)
            step_circle.setObjectName(f"stepCircle{i}")
            
            step_text = QLabel(name)
            step_text.setAlignment(Qt.AlignCenter)
            step_text.setStyleSheet("font-size: 12px; color: #666;")
            
            step_layout.addWidget(step_circle)
            step_layout.addWidget(step_text)
            
            steps_layout.addWidget(step_container)
            self.step_labels.append((step_circle, step_text))
            
            if i < len(step_names) - 1:
                steps_layout.addStretch()
        
        progress_layout.addWidget(progress_widget)
        progress_layout.addWidget(steps_widget)
        parent_layout.addWidget(progress_widget)

    def create_page1_account(self):
        """Page 1: Email with domain selector and Password"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Create Account")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1a1a2e;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
        """)

        subtitle = QLabel("Enter your email and password to get started")
        subtitle.setStyleSheet("""
            color: #666;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
            margin-bottom: 20px;
        """)

        # Email field with domain selector
        email_layout = QVBoxLayout()
        email_label = QLabel("Email Address *")
        email_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        
        # Create a container for the email input + domain selector
        email_container = QWidget()
        email_container.setStyleSheet("""
            QWidget {
                background-color: #fff;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            QWidget:focus-within {
                border: 1.5px solid #80bdff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
        """)
        email_container_layout = QHBoxLayout(email_container)
        email_container_layout.setContentsMargins(0, 0, 0, 0)
        email_container_layout.setSpacing(0)
        
        # Email username input
        self.email_username_input = QLineEdit()
        self.email_username_input.setPlaceholderText("username")
        self.email_username_input.setFixedHeight(46)
        self.email_username_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 0 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background-color: transparent;
                color: #495057;
            }
            QLineEdit:focus {
                outline: none;
            }
        """)
        # Prevent entering '@' or whitespace in the username part; use domain selector instead
        try:
            regex = QRegularExpression("^[^@\\s]*$")
            validator = QRegularExpressionValidator(regex, self.email_username_input)
            self.email_username_input.setValidator(validator)
        except Exception:
            # Fall back silently if QRegularExpression/Validator not available
            pass

        self.email_username_input.textChanged.connect(self.update_full_email)
        
        # @ symbol label
        at_label = QLabel("@")
        at_label.setStyleSheet("""
            font-size: 16px;
            color: #6c757d;
            padding: 0 4px;
            background: transparent;
        """)
        
        # Domain selector dropdown
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(["gmail.com", "icloud.com"])
        self.domain_combo.setFixedHeight(46)
        self.domain_combo.setMinimumWidth(130)
        self.domain_combo.setStyleSheet("""
            QComboBox {
                border: none;
                border-left: 1px solid #ced4da;
                padding: 0 8px 0 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background-color: #f8f9fa;
                color: #495057;
                border-radius: 0;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
                margin-right: 5px;
            }
            QComboBox:hover {
                background-color: #e9ecef;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #495057;
                font-size: 14px;
                selection-background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
        """)
        self.domain_combo.currentTextChanged.connect(self.update_full_email)
        
        email_container_layout.addWidget(self.email_username_input, 1)
        email_container_layout.addWidget(at_label)
        email_container_layout.addWidget(self.domain_combo)
        
        # Hidden field to store full email
        self.full_email = QLineEdit()
        self.full_email.setVisible(False)
        
        email_layout.addWidget(email_label)
        email_layout.addWidget(email_container)
        
        # Email preview
        self.email_preview = QLabel("Your email: username@gmail.com")
        self.email_preview.setStyleSheet("""
            color: #6c757d;
            font-size: 13px;
            margin-top: 4px;
            font-style: italic;
        """)
        email_layout.addWidget(self.email_preview)

        # Password field
        password_layout = QVBoxLayout()
        password_label = QLabel("Password *")
        password_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("At least 6 characters")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(48)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 0 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background-color: #fff;
                color: #495057;
            }
            QLineEdit:focus {
                border: 1.5px solid #80bdff;
                outline: none;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
        """)
        
        self.password_strength = QLabel("Password must be at least 6 characters")
        self.password_strength.setStyleSheet("color: #999; font-size: 12px; margin-top: 5px;")
        self.password_input.textChanged.connect(self.check_password_strength)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.password_strength)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(email_layout)
        layout.addLayout(password_layout)
        layout.addStretch()

        self.pages_container.addWidget(page)
        
        # Initialize email preview
        self.update_full_email()

    def update_full_email(self):
        """Update the full email address and preview"""
        # Ensure username never contains '@' (user should use the domain selector)
        username = self.email_username_input.text()
        if '@' in username or '\\s' in username:
            # Strip disallowed characters and update the field without re-triggering signals
            clean = username.replace('@', '')
            clean = ' '.join(clean.split())  # remove stray whitespace
            try:
                self.email_username_input.blockSignals(True)
                self.email_username_input.setText(clean)
            finally:
                try:
                    self.email_username_input.blockSignals(False)
                except Exception:
                    pass
            username = clean

        username = username.strip()
        domain = self.domain_combo.currentText()

        if username:
            full_email = f"{username}@{domain}"
            self.full_email.setText(full_email)
            self.email_preview.setText(f"Your email: {full_email}")
            self.email_preview.setStyleSheet("""
                color: #28a745;
                font-size: 13px;
                margin-top: 4px;
                font-style: italic;
                font-weight: 500;
            """)
        else:
            self.full_email.setText("")
            self.email_preview.setText("Please enter your username")
            self.email_preview.setStyleSheet("""
                color: #6c757d;
                font-size: 13px;
                margin-top: 4px;
                font-style: italic;
            """)

        # Start (or restart) debounce timer to apply email change after typing stops
        try:
            self._email_debounce_timer.start()
        except Exception:
            pass

    def _apply_email_change(self):
        """Apply the debounced email change to registration data and reset verification UI if needed."""
        email = self.full_email.text().strip()
        # Update stored email
        if email:
            self.registration_data["email"] = email
        else:
            self.registration_data["email"] = ""

        # Mark that the email was recently changed so we can avoid auto-sending
        # a verification immediately when navigating back to that page.
        self._email_recently_changed = True
        QTimer.singleShot(2000, lambda: setattr(self, '_email_recently_changed', False))

        # If on verification page, clear any in-progress verification
        if getattr(self, 'current_page', None) == self.total_pages - 1:
            # Clear server verification id and verified flag
            self.verification_id = None
            self.is_verified = False

            # Reset the webview verification UI if available
            if hasattr(self, 'verification_webview') and self.verification_webview:
                try:
                    self.verification_webview.page().runJavaScript('resetVerification()')
                    if email:
                        escaped = email.replace('"', '\\"')
                        self.verification_webview.page().runJavaScript(f'setEmail("{escaped}")')
                except Exception:
                    pass

            # Re-enable next button (request flow) so user can re-send code manually
            if hasattr(self, 'next_btn'):
                try:
                    self.next_btn.setEnabled(True)
                    self.next_btn.setText("Next")
                except Exception:
                    pass

    def create_page2_profile(self):
        """Page 2: Name, Age, and Avatar (Role is hidden, default student)"""
        page = QWidget()
        page.setStyleSheet("background: white;")
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        title = QLabel("Your Profile")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1a1a2e;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
        """)

        subtitle = QLabel("Tell us about yourself")
        subtitle.setStyleSheet("""
            color: #666;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
        """)

        # Name fields (First and Last)
        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setSpacing(15)
        
        # First name
        firstname_layout = QVBoxLayout()
        firstname_label = QLabel("First Name *")
        firstname_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        self.firstname_input = QLineEdit()
        self.firstname_input.setPlaceholderText("John")
        self.firstname_input.setFixedHeight(48)
        self.firstname_input.setStyleSheet(self.get_input_style())
        firstname_layout.addWidget(firstname_label)
        firstname_layout.addWidget(self.firstname_input)
        
        # Last name
        lastname_layout = QVBoxLayout()
        lastname_label = QLabel("Last Name")
        lastname_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        self.lastname_input = QLineEdit()
        self.lastname_input.setPlaceholderText("Doe")
        self.lastname_input.setFixedHeight(48)
        self.lastname_input.setStyleSheet(self.get_input_style())
        lastname_layout.addWidget(lastname_label)
        lastname_layout.addWidget(self.lastname_input)
        
        name_layout.addLayout(firstname_layout)
        name_layout.addLayout(lastname_layout)

        # Age
        age_layout = QVBoxLayout()
        age_label = QLabel("Age *")
        age_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("25")
        self.age_input.setValidator(QIntValidator(16, 100))
        self.age_input.setFixedHeight(48)
        self.age_input.setStyleSheet(self.get_input_style())
        age_layout.addWidget(age_label)
        age_layout.addWidget(self.age_input)

        # Avatar section
        avatar_layout = QVBoxLayout()
        avatar_label = QLabel("Profile Picture (Optional)")
        avatar_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        
        avatar_container = QWidget()
        avatar_container_layout = QHBoxLayout(avatar_container)
        avatar_container_layout.setSpacing(20)
        
        # Avatar preview
        self.avatar_preview = QLabel()
        self.avatar_preview.setFixedSize(100, 100)
        self.avatar_preview.setAlignment(Qt.AlignCenter)
        self.avatar_preview.setStyleSheet("""
            border: 2px dashed #ddd;
            border-radius: 50px;
            background-color: #f5f5f5;
            overflow: hidden;
        """)
        
        default_avatar_text = QLabel("User")
        default_avatar_text.setStyleSheet("font-size: 48px;")
        default_avatar_text.setAlignment(Qt.AlignCenter)
        
        preview_layout = QVBoxLayout(self.avatar_preview)
        preview_layout.addWidget(default_avatar_text)
        
        # Upload button
        upload_btn = QPushButton("Choose Photo")
        upload_btn.setFixedSize(120, 40)
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #4361ee;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
        """)
        upload_btn.clicked.connect(self.select_avatar)
        
        avatar_container_layout.addWidget(self.avatar_preview)
        avatar_container_layout.addWidget(upload_btn)
        avatar_container_layout.addStretch()
        
        avatar_layout.addWidget(avatar_label)
        avatar_layout.addWidget(avatar_container)
        
        # File info
        self.avatar_info = QLabel("No file selected")
        self.avatar_info.setStyleSheet("color: #999; font-size: 12px; margin-top: 5px;")
        avatar_layout.addWidget(self.avatar_info)

        scroll_layout.addWidget(title)
        scroll_layout.addWidget(subtitle)
        scroll_layout.addWidget(name_container)
        scroll_layout.addLayout(age_layout)
        scroll_layout.addLayout(avatar_layout)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.pages_container.addWidget(page)

    def get_input_style(self):
        """Return consistent input style"""
        return """
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 0 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background-color: #fff;
                color: #495057;
            }
            QLineEdit:focus {
                border: 1.5px solid #80bdff;
                outline: none;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
        """

    def create_page3_study_level(self):
        """Page 3: Academic level (for students)"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Academic Information")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1a1a2e;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
        """)

        subtitle = QLabel("Tell us about your educational background")
        subtitle.setStyleSheet("""
            color: #666;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
            margin-bottom: 20px;
        """)

        # Study level combo
        study_layout = QVBoxLayout()
        study_label = QLabel("Academic Stage *")
        study_label.setStyleSheet("font-weight: 500; color: #333; font-size: 14px;")
        
        self.study_combo = QComboBox()
        self.study_combo.addItems([
            "Select your academic stage",
            "High School Student",
            "University Student (Year 1)",
            "University Student (Year 2)",
            "University Student (Year 3)",
            "University Student (Year 4)",
            "Graduate Student",
            "Master's Student",
            "PhD Student",
            "Graduate",
            "Employed Professional",
            "Other"
        ])
        self.study_combo.setFixedHeight(60)
        self.study_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 0 16px;
                font-size: 18px;
                background-color: #fff;
                color: #495057;
                min-height: 60px;
                height: 60px;
            }
            QComboBox:focus, QComboBox:hover {
                border: 1.5px solid #80bdff;
                outline: none;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.15);
            }
            QComboBox QAbstractItemView {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e3f0ff, stop:1 #b3cfff);
                color: #1a237e;
                font-size: 17px;
                selection-background-color: #c7e0ff;
                border-radius: 0 0 8px 8px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 10px;
            }
        """)
        
        study_layout.addWidget(study_label)
        study_layout.addWidget(self.study_combo)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(study_layout)
        layout.addStretch()

        self.pages_container.addWidget(page)

    def create_page4_verification(self):
        """Page 4: OTP Verification using QWebEngineView"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Web view for OTP
        self.verification_webview = QWebEngineView()
        self.verification_webview.setHtml(self.get_verification_html(), QUrl("about:blank"))
        
        # Set up web channel
        self.verification_channel = QWebChannel()
        self.verification_bridge = VerificationBridge(self)
        self.verification_bridge.web_view = self.verification_webview
        self.verification_channel.registerObject("pyApi", self.verification_bridge)
        self.verification_webview.page().setWebChannel(self.verification_channel)

        layout.addWidget(self.verification_webview)
        self.pages_container.addWidget(page)

    def get_verification_html(self):
        """Return the HTML for the OTP verification page with minimal padding"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Code</title>
    <style>
        :root {
            --bg-primary: #f8f9fb;
            --bg-card: #ffffff;
            --text-primary: #1a1d24;
            --text-secondary: #5f6b7a;
            --text-tertiary: #8b95a5;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --accent-light: #eff6ff;
            --accent-glow: rgba(37, 99, 235, 0.18);
            --border: #e2e8f0;
            --border-focus: #2563eb;
            --input-bg: #f8fafc;
            --input-bg-focus: #ffffff;
            --error: #ef4444;
            --error-bg: #fef2f2;
            --success: #10b981;
            --success-bg: #ecfdf5;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', system-ui, sans-serif;
            background: var(--bg-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 8px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .container {
            width: 100%;
            max-width: 420px;
        }

        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 16px 24px 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
            border: 1px solid var(--border);
            text-align: center;
            position: relative;
        }

        .icon-wrapper {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            border-radius: 14px;
            background: var(--accent-light);
            margin-bottom: 12px;
        }

        .icon-wrapper svg {
            width: 24px;
            height: 24px;
            color: var(--accent);
        }

        .title {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
            line-height: 1.2;
        }

        .subtitle {
            font-size: 0.85rem;
            color: var(--text-secondary);
            line-height: 1.4;
            margin-bottom: 2px;
        }

        .email-highlight {
            display: inline-block;
            font-weight: 600;
            color: var(--text-primary);
            background: #f1f5f9;
            padding: 2px 10px;
            border-radius: 6px;
            font-size: 0.85rem;
            word-break: break-all;
            max-width: 100%;
            margin: 2px 0;
        }

        /* Animated gradient hint for checking Spam/Tab folders */
        .hint {
            display: inline-block;
            margin-top: 8px;
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1.2;
            background: linear-gradient(135deg, #ffffff 0%, #7ab8d4 50%, #c8e0f0 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-transform: none;
            border-radius: 6px;
            padding: 2px 6px;
            animation: slideGradient 3.5s ease-in-out infinite;
            box-decoration-break: clone;
        }

        @keyframes slideGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .otp-container {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin: 16px 0 6px;
            flex-wrap: nowrap;
        }

        .otp-input {
            width: 44px;
            height: 50px;
            text-align: center;
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            border: 2px solid var(--border);
            border-radius: 8px;
            background: var(--input-bg);
            color: var(--text-primary);
            outline: none;
            transition: all 0.2s;
            caret-color: var(--accent);
            font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            -webkit-appearance: none;
            -moz-appearance: textfield;
        }

        .otp-input::-webkit-outer-spin-button,
        .otp-input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }

        .otp-input:hover {
            border-color: #c4cdd8;
            background: #fcfdfe;
        }

        .otp-input:focus {
            border-color: var(--border-focus);
            background: var(--input-bg-focus);
            box-shadow: 0 0 0 3px var(--accent-glow);
            outline: none;
            transform: translateY(-1px);
        }

        .otp-input.filled {
            border-color: #bcc7d6;
            background: #fafbfc;
        }

        .otp-input.error {
            border-color: var(--error);
            background: var(--error-bg);
            animation: shake 0.4s ease;
        }

        .otp-input.success {
            border-color: var(--success);
            background: var(--success-bg);
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20% { transform: translateX(-4px); }
            40% { transform: translateX(4px); }
            60% { transform: translateX(-3px); }
            80% { transform: translateX(3px); }
        }

        .error-message {
            font-size: 0.78rem;
            color: var(--error);
            min-height: 18px;
            margin-bottom: 2px;
            font-weight: 500;
            opacity: 0;
            transform: translateY(-3px);
            transition: all 0.2s;
        }
        .error-message.visible {
            opacity: 1;
            transform: translateY(0);
        }

        .success-message {
            font-size: 0.78rem;
            color: var(--success);
            min-height: 18px;
            margin-bottom: 2px;
            font-weight: 500;
            opacity: 0;
            transform: translateY(-3px);
            transition: all 0.2s;
        }
        .success-message.visible {
            opacity: 1;
            transform: translateY(0);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 10px 20px;
            font-size: 0.9rem;
            font-weight: 600;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
            white-space: nowrap;
            margin-top: 4px;
        }

        .btn-primary {
            background: #1a1d24;
            color: #ffffff;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }
        .btn-primary:hover:not(:disabled) {
            background: #2d323c;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transform: translateY(-1px);
        }
        .btn-primary:active:not(:disabled) {
            transform: translateY(0) scale(0.985);
            background: #0f1117;
        }
        .btn-primary:disabled {
            background: #c4cdd8;
            cursor: not-allowed;
            color: #8b95a5;
        }

        .btn-primary .spinner {
            display: none;
            width: 18px;
            height: 18px;
            border: 2.5px solid rgba(255, 255, 255, 0.3);
            border-top-color: #ffffff;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        .btn-primary.loading .spinner {
            display: inline-block;
        }
        .btn-primary.loading .btn-text {
            opacity: 0.7;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .checkmark-icon {
            display: none;
            width: 18px;
            height: 18px;
            margin-right: 8px;
            color: #ffffff;
            animation: checkmark-in 0.3s ease;
        }
        .btn-primary.verified .checkmark-icon {
            display: inline-block;
        }
        .btn-primary.verified {
            background: var(--success);
            pointer-events: none;
            cursor: default;
        }

        @keyframes checkmark-in {
            0% { transform: scale(0) rotate(-30deg); opacity: 0; }
            100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }

        .resend-section {
            margin-top: 12px;
            font-size: 0.82rem;
            color: var(--text-tertiary);
        }
        .resend-btn {
            background: none;
            border: none;
            color: var(--accent);
            font-weight: 600;
            cursor: pointer;
            font-size: 0.82rem;
            font-family: inherit;
            transition: color 0.2s;
            padding: 2px 4px;
            border-radius: 4px;
        }
        .resend-btn:hover:not(:disabled) {
            color: var(--accent-hover);
            background: var(--accent-light);
        }
        .resend-btn:disabled {
            color: var(--text-tertiary);
            cursor: not-allowed;
        }
        .timer {
            display: inline-block;
            font-variant-numeric: tabular-nums;
            min-width: 28px;
            text-align: center;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .footer-text {
            margin-top: 12px;
            font-size: 0.72rem;
            color: var(--text-tertiary);
            line-height: 1.4;
        }
        .footer-text a {
            color: var(--text-secondary);
            text-decoration: underline;
            text-underline-offset: 2px;
        }
        .footer-text a:hover {
            color: var(--text-primary);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #0d1117;
                --bg-card: #161b22;
                --text-primary: #e6edf3;
                --text-secondary: #8b949e;
                --text-tertiary: #6e7681;
                --accent: #58a6ff;
                --accent-hover: #79b8ff;
                --accent-light: #0d2847;
                --accent-glow: rgba(88, 166, 255, 0.15);
                --border: #30363d;
                --border-focus: #58a6ff;
                --input-bg: #0d1117;
                --input-bg-focus: #0d1117;
                --error: #f85149;
                --error-bg: #1f1315;
                --success: #3fb950;
                --success-bg: #132416;
            }
            .btn-primary {
                background: #e6edf3;
                color: #0d1117;
            }
            .btn-primary:hover:not(:disabled) {
                background: #ffffff;
            }
            .btn-primary:disabled {
                background: #30363d;
                color: #6e7681;
            }
            .btn-primary .spinner {
                border-color: rgba(13, 17, 23, 0.3);
                border-top-color: #0d1117;
            }
            .email-highlight {
                background: #21262d;
                color: #e6edf3;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="icon-wrapper" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect>
                    <polyline points="2 7 12 15 22 7"></polyline>
                </svg>
            </div>
            <h1 class="title">Check your email</h1>
            <p class="subtitle">We sent a 6-digit code to</p>
            <span class="email-highlight" id="userEmail">your@email.com</span>
            <p class="hint" id="spamHint">If you don't find the email, check your Spam/Promotions/Tab folder in your email app.</p>
            <div class="otp-container" id="otpContainer">
                <input type="text" class="otp-input" id="otp1" maxlength="1" inputmode="numeric" pattern="[0-9]" autocomplete="one-time-code" aria-label="Digit 1">
                <input type="text" class="otp-input" id="otp2" maxlength="1" inputmode="numeric" pattern="[0-9]" aria-label="Digit 2">
                <input type="text" class="otp-input" id="otp3" maxlength="1" inputmode="numeric" pattern="[0-9]" aria-label="Digit 3">
                <input type="text" class="otp-input" id="otp4" maxlength="1" inputmode="numeric" pattern="[0-9]" aria-label="Digit 4">
                <input type="text" class="otp-input" id="otp5" maxlength="1" inputmode="numeric" pattern="[0-9]" aria-label="Digit 5">
                <input type="text" class="otp-input" id="otp6" maxlength="1" inputmode="numeric" pattern="[0-9]" aria-label="Digit 6">
            </div>
            <p class="error-message" id="errorMessage" role="alert">Invalid code. Please try again.</p>
            <p class="success-message" id="successMessage" role="status">Email verified successfully!</p>
            <button class="btn btn-primary" id="verifyBtn" type="button">
                <span class="spinner"></span>
                <svg class="checkmark-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span class="btn-text">Verify Email</span>
            </button>
            <div class="resend-section">
                <span>Didn't receive the code? </span>
                <button class="resend-btn" id="resendBtn" type="button">Resend</button>
                <span class="timer" id="timerDisplay"></span>
            </div>
            <p class="footer-text">
                If you're having trouble, contact <a href="#">support@latigo.com</a>
            </p>
        </div>
    </div>

    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        // Global variables
        var countdown = 30;
        var timerInterval = null;
        var isVerifying = false;
        var verified = false;
        var pyApi = null;

        // DOM Elements
        var otpInputs = document.querySelectorAll('.otp-input');
        var otpContainer = document.getElementById('otpContainer');
        var verifyBtn = document.getElementById('verifyBtn');
        var resendBtn = document.getElementById('resendBtn');
        var errorMessage = document.getElementById('errorMessage');
        var successMessage = document.getElementById('successMessage');
        var timerDisplay = document.getElementById('timerDisplay');
        var userEmailSpan = document.getElementById('userEmail');

        // ============ GLOBAL FUNCTIONS (callable from Python) ============
        window.setEmail = function(email) {
            userEmailSpan.textContent = email;
        };

        window.setStatus = function(message, type) {
            errorMessage.classList.remove('visible');
            successMessage.classList.remove('visible');
            
            if (type === 'success') {
                successMessage.textContent = message;
                successMessage.classList.add('visible');
                verifyBtn.classList.add('verified');
                verifyBtn.classList.remove('loading');
                verifyBtn.disabled = true;
                otpInputs.forEach(function(input) {
                    input.disabled = true;
                    input.style.cursor = 'default';
                    input.style.opacity = '0.7';
                });
                verified = true;
                isVerifying = false;
            } else if (type === 'error') {
                errorMessage.textContent = message;
                errorMessage.classList.add('visible');
                verifyBtn.classList.remove('loading', 'verified');
                verifyBtn.disabled = false;
                otpInputs.forEach(function(input) {
                    input.disabled = false;
                    input.style.cursor = '';
                    input.style.opacity = '';
                    input.classList.add('error');
                });
                isVerifying = false;
                setTimeout(function() {
                    clearOtpInputs();
                    otpInputs.forEach(function(input) {
                        input.classList.remove('error');
                    });
                }, 2000);
            } else if (type === 'loading') {
                verifyBtn.classList.add('loading');
                verifyBtn.classList.remove('verified');
                verifyBtn.disabled = true;
                isVerifying = true;
            } else {
                verifyBtn.classList.remove('loading', 'verified');
                verifyBtn.disabled = false;
                otpInputs.forEach(function(input) {
                    input.disabled = false;
                    input.style.cursor = '';
                    input.style.opacity = '';
                    input.classList.remove('error', 'success');
                });
                isVerifying = false;
            }
        };

        window.setResendCooldown = function(seconds) {
            countdown = seconds;
            resendBtn.disabled = true;
            updateTimerDisplay();
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(function() {
                countdown--;
                updateTimerDisplay();
                if (countdown <= 0) {
                    clearInterval(timerInterval);
                    timerInterval = null;
                    resendBtn.disabled = false;
                    timerDisplay.textContent = '';
                }
            }, 1000);
        };

        window.clearOtpInputs = function() {
            otpInputs.forEach(function(input) {
                input.value = '';
                input.classList.remove('filled', 'error', 'success');
            });
            otpInputs[0].focus();
        };

        window.resetVerification = function() {
            verified = false;
            isVerifying = false;
            verifyBtn.classList.remove('verified', 'loading');
            verifyBtn.disabled = false;
            otpInputs.forEach(function(input) {
                input.disabled = false;
                input.style.cursor = '';
                input.style.opacity = '';
                input.classList.remove('error', 'success');
            });
            errorMessage.classList.remove('visible');
            successMessage.classList.remove('visible');
            clearOtpInputs();
        };

        // ============ HELPER FUNCTIONS ============
        function updateTimerDisplay() {
            if (countdown > 0) {
                var mins = Math.floor(countdown / 60);
                var secs = countdown % 60;
                if (mins > 0) {
                    timerDisplay.textContent = '(' + mins + ':' + secs.toString().padStart(2, '0') + ')';
                } else {
                    timerDisplay.textContent = '(0:' + secs.toString().padStart(2, '0') + ')';
                }
            } else {
                timerDisplay.textContent = '';
            }
        }

        function getOtpValue() {
            var otp = '';
            otpInputs.forEach(function(input) {
                otp += input.value;
            });
            return otp;
        }

        // ============ EVENT HANDLERS ============
        function handleOtpInput(e) {
            var input = e.target;
            var value = input.value;
            if (!/^\\d*$/.test(value)) {
                input.value = value.replace(/\\D/g, '');
                return;
            }
            if (value) {
                input.classList.add('filled');
            } else {
                input.classList.remove('filled');
            }
            input.classList.remove('error', 'success');
            
            if (value && input.nextElementSibling && input.nextElementSibling.classList.contains('otp-input')) {
                input.nextElementSibling.focus();
            }
            
            var otp = getOtpValue();
            if (otp.length === 6 && !isVerifying && !verified && pyApi) {
                setTimeout(function() {
                    if (getOtpValue().length === 6 && !isVerifying && !verified) {
                        console.log('Auto-submitting OTP:', otp);
                        pyApi.verifyCode(otp);
                    }
                }, 300);
            }
        }

        function handleOtpKeydown(e) {
            var input = e.target;
            if (e.key === 'Backspace' && !input.value && input.previousElementSibling &&
                input.previousElementSibling.classList.contains('otp-input')) {
                input.previousElementSibling.focus();
                input.previousElementSibling.select();
            }
            if (e.key === 'ArrowLeft' && input.previousElementSibling &&
                input.previousElementSibling.classList.contains('otp-input')) {
                e.preventDefault();
                input.previousElementSibling.focus();
                input.previousElementSibling.select();
            }
            if (e.key === 'ArrowRight' && input.nextElementSibling &&
                input.nextElementSibling.classList.contains('otp-input')) {
                e.preventDefault();
                input.nextElementSibling.focus();
                input.nextElementSibling.select();
            }
        }

        function handlePaste(e) {
            e.preventDefault();
            var pasteData = (e.clipboardData || window.clipboardData).getData('text').trim();
            var digits = pasteData.replace(/\\D/g, '').slice(0, 6);
            if (digits.length === 0) return;
            otpInputs.forEach(function(input, index) {
                if (index < digits.length) {
                    input.value = digits[index];
                    input.classList.add('filled');
                } else {
                    input.value = '';
                    input.classList.remove('filled');
                }
                input.classList.remove('error', 'success');
            });
            var nextEmptyIndex = digits.length < 6 ? digits.length : 5;
            otpInputs[nextEmptyIndex].focus();
            if (digits.length === 6 && pyApi) {
                setTimeout(function() {
                    if (getOtpValue().length === 6 && !isVerifying && !verified) {
                        pyApi.verifyCode(getOtpValue());
                    }
                }, 350);
            }
        }

        function handleContainerClick(e) {
            if (e.target.classList.contains('otp-input')) return;
            if (verified) return;
            for (var i = 0; i < otpInputs.length; i++) {
                var input = otpInputs[i];
                if (!input.value) {
                    input.focus();
                    return;
                }
            }
            otpInputs[otpInputs.length - 1].focus();
        }

        // ============ SETUP ============
        // Initialize QWebChannel
        new QWebChannel(qt.webChannelTransport, function(channel) {
            pyApi = channel.objects.pyApi;
            if (pyApi) {
                console.log('pyApi connected successfully');
                pyApi.pageReady();
            } else {
                alert('pyApi is not available! Please restart the application.');
            }
        });

        // Event listeners
        otpInputs.forEach(function(input) {
            input.addEventListener('input', handleOtpInput);
            input.addEventListener('keydown', handleOtpKeydown);
            input.addEventListener('paste', handlePaste);
            input.addEventListener('beforeinput', function(e) {
                if (e.data && !/^\\d$/.test(e.data) && e.inputType === 'insertText') {
                    e.preventDefault();
                }
            });
        });
        otpContainer.addEventListener('paste', function(e) {
            if (!document.activeElement || !document.activeElement.classList.contains('otp-input')) {
                handlePaste.call(this, e);
            }
        });
        otpContainer.addEventListener('click', handleContainerClick);

        // Verify button
        verifyBtn.addEventListener('click', function() {
            if (!isVerifying && !verified) {
                var otp = getOtpValue();
                if (otp.length === 6) {
                    if (pyApi) {
                        console.log('Manual verify OTP:', otp);
                        pyApi.verifyCode(otp);
                    } else {
                        alert('pyApi is not available! Please restart the application.');
                    }
                } else {
                    errorMessage.textContent = 'Please enter the full 6-digit code.';
                    errorMessage.classList.add('visible');
                    setTimeout(function() {
                        errorMessage.classList.remove('visible');
                    }, 3000);
                }
            }
        });

        // Resend button
        resendBtn.addEventListener('click', function() {
            if (resendBtn.disabled || isVerifying || !pyApi) return;
            clearOtpInputs();
            errorMessage.classList.remove('visible');
            successMessage.classList.remove('visible');
            if (verified) {
                verifyBtn.classList.remove('verified');
                verifyBtn.disabled = false;
                verified = false;
                otpInputs.forEach(function(input) {
                    input.disabled = false;
                    input.style.cursor = '';
                    input.style.opacity = '';
                });
            }
            pyApi.resendCode();
        });

        // Focus first input on load
        setTimeout(function() {
            otpInputs[0].focus();
        }, 400);
    </script>
</body>
</html>"""

    def create_navigation_buttons(self, parent_layout):
        """Create navigation buttons"""
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 20, 0, 0)
        nav_layout.setSpacing(15)

        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedHeight(44)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setVisible(False)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 500;
                color: #333;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #4361ee;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)

        self.next_btn = QPushButton("Next")
        self.next_btn.setFixedHeight(44)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #4361ee;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 500;
                color: white;
                padding: 0 35px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.next_btn.clicked.connect(self.go_next)

        self.register_btn = QPushButton("Create Account")
        self.register_btn.setFixedHeight(44)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setVisible(False)
        self.register_btn.setStyleSheet(self.next_btn.styleSheet())
        self.register_btn.clicked.connect(self.submit_registration)

        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.register_btn)

        parent_layout.addWidget(nav_widget)

    def select_avatar(self):
        """Select avatar image"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.jpg *.jpeg *.png *.gif)")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            file_size = os.path.getsize(file_path)
            
            if file_size > 5 * 1024 * 1024:
                sound_manager.play_error()
                QMessageBox.warning(self, "File Too Large", "Image must be less than 5MB")
                return

            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Cannot open image")
                return

            # Scale and crop to circle
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            circular_pixmap = QPixmap(100, 100)
            circular_pixmap.fill(Qt.transparent)
            
            painter = QPainter(circular_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, 100, 100)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()
            
            # Update preview
            while self.avatar_preview.layout().count():
                item = self.avatar_preview.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            preview_label = QLabel()
            preview_label.setPixmap(circular_pixmap)
            preview_label.setAlignment(Qt.AlignCenter)
            self.avatar_preview.layout().addWidget(preview_label)
            
            self.registration_data["avatar"] = file_path
            self.avatar_info.setText(os.path.basename(file_path))
            sound_manager.play_success()

    def check_password_strength(self, password):
        """Check password strength"""
        if len(password) >= 8:
            self.password_strength.setText("Strong password")
            self.password_strength.setStyleSheet("color: #28a745; font-size: 12px; margin-top: 5px;")
        elif len(password) >= 6:
            self.password_strength.setText("Password strength: OK")
            self.password_strength.setStyleSheet("color: #ffc107; font-size: 12px; margin-top: 5px;")
        else:
            self.password_strength.setText("Password must be at least 6 characters")
            self.password_strength.setStyleSheet("color: #999; font-size: 12px; margin-top: 5px;")

    def validate_current_page(self):
        """Validate current page before proceeding"""
        if self.current_page == 0:  # Account page
            email = self.full_email.text().strip()
            password = self.password_input.text().strip()
            username = self.email_username_input.text().strip()
            
            if not username:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please enter your email username")
                return False
            if not email:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please enter your email")
                return False
            if "@" not in email or "." not in email:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please enter a valid email address")
                return False
            if len(password) < 6:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
                return False
            
            # Store data
            self.registration_data["email"] = email
            self.registration_data["password"] = password
            return True
            
        elif self.current_page == 1:  # Profile page
            first_name = self.firstname_input.text().strip()
            age = self.age_input.text().strip()
            
            if not first_name:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please enter your first name")
                return False
            if not age:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please enter your age")
                return False
            try:
                age_int = int(age)
                if age_int < 16 or age_int > 100:
                    sound_manager.play_error()
                    QMessageBox.warning(self, "Error", "Age must be between 16 and 100")
                    return False
            except ValueError:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please enter a valid age")
                return False
            
            # Store data
            self.registration_data["first_name"] = first_name
            self.registration_data["last_name"] = self.lastname_input.text().strip()
            self.registration_data["age"] = age
            return True
            
        elif self.current_page == 2:  # Study level page
            study_level = self.study_combo.currentText()
            if study_level == "Select your academic stage":
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "Please select your academic stage")
                return False
            self.registration_data["study_level"] = study_level
            return True
            
        return True

    def go_next(self):
        """Go to next page"""
        if not self.validate_current_page():
            return

        sound_manager.play_click()

        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.pages_container.setCurrentIndex(self.current_page)
            
            # Show verification page on last page
            if self.current_page == self.total_pages - 1:
                self.show_verification_page()
            else:
                self.next_btn.setVisible(True)
                self.register_btn.setVisible(False)
            
            self.update_navigation()

    def go_back(self):
        """Go to previous page"""
        sound_manager.play_click()
        if self.current_page > 0:
            self.current_page -= 1
            self.pages_container.setCurrentIndex(self.current_page)
            # Ensure navigation controls are reset when going back
            self.next_btn.setVisible(True)
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Next")
            self.register_btn.setVisible(False)

            # Clear any verification state/UI if we came back from verification
            try:
                self.verification_id = None
                self.is_verified = False
                if hasattr(self, 'verification_webview') and self.verification_webview:
                    self.verification_webview.page().runJavaScript('resetVerification()')
            except Exception:
                pass

            self.update_navigation()

    def show_verification_page(self):
        """Show the verification page and request code"""
        self.next_btn.setVisible(False)
        self.register_btn.setVisible(False)
        self.back_btn.setVisible(True)

        # If the user recently changed the email, do not auto-send a verification
        # code immediately. Instead just show the verification UI and let the
        # user trigger sending (or come back to Next to re-send).
        if getattr(self, '_email_recently_changed', False):
            try:
                email = self.registration_data.get('email', '')
                if email and hasattr(self, 'verification_webview') and self.verification_webview:
                    escaped = email.replace('"', '\\"')
                    self.verification_webview.page().runJavaScript(f'setEmail("{escaped}")')
                    self.verification_webview.page().runJavaScript('resetVerification()')
            except Exception:
                pass
            # clear the flag after showing the page (allow next navigation to send)
            QTimer.singleShot(1500, lambda: setattr(self, '_email_recently_changed', False))
            return

        self.request_verification()

    def update_navigation(self):
        """Update navigation buttons and progress"""
        self.back_btn.setVisible(self.current_page > 0)
        
        self.progress_bar.setValue(self.current_page)
        
        for i, (circle, label) in enumerate(self.step_labels):
            if i <= self.current_page:
                circle.setStyleSheet("""
                    background-color: #4361ee;
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 14px;
                """)
                label.setStyleSheet("font-size: 12px; color: #4361ee; font-weight: 500;")
            else:
                circle.setStyleSheet("""
                    background-color: #e0e0e0;
                    color: #666;
                    border-radius: 15px;
                    font-size: 14px;
                """)
                label.setStyleSheet("font-size: 12px; color: #999;")

    def show_terms_dialog(self):
        """Display Terms & Conditions dialog; returns True if accepted."""
        dialog = TermsDialog(self)
        result = dialog.exec()
        return result == QDialog.Accepted

    # ==================== VERIFICATION METHODS ====================

    def request_verification(self):
        """Send request to /api/send-verification using account_config"""
        email = self.registration_data.get("email")
        if not email:
            QMessageBox.warning(self, "Error", "Email not set")
            return

        print(f"Requesting verification for: {email}")
        self.next_btn.setEnabled(False)
        self.next_btn.setText("Sending code...")

        try:
            # Use account_config with CSRF support
            response = account_config.post("/api/send-verification", data={"email": email}, timeout=10)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.verification_id = data.get("data", {}).get("verification_id")
                    self.verification_expires = data.get("data", {}).get("expires_in", 300)
                    print(f"Verification sent, ID: {self.verification_id}")
                    
                    self.verification_webview.page().runJavaScript(f'setEmail("{email}")')
                    self.verification_webview.page().runJavaScript('setStatus("Code sent to your email", "waiting")')
                    self.verification_webview.page().runJavaScript('setResendCooldown(30)')
                    self.verification_webview.page().runJavaScript('clearOtpInputs()')
                    
                    self.pages_container.setCurrentIndex(3)
                    self.current_page = 3
                    self.update_navigation()
                    
                    self.next_btn.setVisible(False)
                    self.register_btn.setVisible(False)
                    self.back_btn.setVisible(True)
                else:
                    error = data.get("error", "Unknown error")
                    print(f"Error: {error}")
                    QMessageBox.warning(self, "Error", f"Failed to send code: {error}")
                    self.next_btn.setEnabled(True)
                    self.next_btn.setText("Next")
                    self.go_back()
            else:
                error_data = response.json()
                error = error_data.get("error", f"Server error: {response.status_code}")
                print(f"Error: {error}")
                QMessageBox.warning(self, "Error", f"Failed to send code: {error}")
                self.next_btn.setEnabled(True)
                self.next_btn.setText("Next")
                self.go_back()
        except requests.exceptions.Timeout:
            print("Timeout error")
            QMessageBox.warning(self, "Error", "Connection timeout. Please try again.")
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Next")
            self.go_back()
        except requests.exceptions.ConnectionError:
            print("Connection error")
            QMessageBox.warning(self, "Connection Error", "Cannot connect to server. Make sure the backend is running.")
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Next")
            self.go_back()
        except Exception as e:
            print(f"Exception: {e}")
            QMessageBox.warning(self, "Error", f"Failed to send code: {str(e)}")
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Next")
            self.go_back()

    def verify_otp_code(self, code):
        """Verify the OTP code using account_config"""
        print(f"DEBUG: verify_otp_code called with code: {code}")
        print(f"DEBUG: verification_id = {self.verification_id}")
        
        if not self.verification_id:
            error_msg = "No verification session"
            print(f"ERROR: {error_msg}")
            self.show_verification_error(error_msg)
            QMessageBox.warning(self, "Error", error_msg)
            return

        print(f"DEBUG: Sending verification request to {account_config.API_BASE_URL}/api/verify-code")
        
        self.verification_webview.page().runJavaScript('setStatus("Verifying...", "loading")')

        try:
            # Use account_config with CSRF support
            response = account_config.post("/api/verify-code", data={
                "verification_id": self.verification_id,
                "code": code
            }, timeout=10)
            
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("DEBUG: Verification successful!")
                    self.is_verified = True
                    self.verification_webview.page().runJavaScript('setStatus("Verified! Selecting teacher...", "success")')
                    QTimer.singleShot(1500, self.show_teacher_selection)
                else:
                    error_msg = data.get("error", "Verification failed")
                    print(f"ERROR: {error_msg}")
                    self.show_verification_error(error_msg)
                    QMessageBox.warning(self, "Verification Failed", error_msg)
            else:
                error_data = response.json()
                error_msg = error_data.get("error", f"Server error: {response.status_code}")
                attempts_data = error_data.get("data", {})
                if attempts_data.get("attempts_left") is not None:
                    error_msg = f"{error_msg} ({attempts_data.get('attempts_left')} attempts left)"
                print(f"ERROR: {error_msg}")
                self.show_verification_error(error_msg)
                QMessageBox.warning(self, "Verification Failed", error_msg)
        except requests.exceptions.Timeout:
            error_msg = "Connection timeout. Please try again."
            print(f"ERROR: {error_msg}")
            self.show_verification_error(error_msg)
            QMessageBox.warning(self, "Error", error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Server unreachable. Please check your connection."
            print(f"ERROR: {error_msg}")
            self.show_verification_error(error_msg)
            QMessageBox.warning(self, "Connection Error", error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.show_verification_error(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def show_verification_error(self, message):
        """Show error message in the verification page"""
        escaped_message = message.replace('"', '\\"')
        js = f'setStatus("{escaped_message}", "error")'
        self.verification_webview.page().runJavaScript(js)

    def resend_verification_code(self):
        """Resend the verification code using account_config"""
        email = self.registration_data.get("email")
        if not email:
            return
        
        print(f"Resending verification to: {email}")
        self.verification_webview.page().runJavaScript('setStatus("Sending new code...", "loading")')
        
        try:
            # Use account_config with CSRF support
            response = account_config.post("/api/send-verification", data={"email": email}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.verification_id = data.get("data", {}).get("verification_id")
                    print(f"New verification sent, ID: {self.verification_id}")
                    self.verification_webview.page().runJavaScript('setStatus("New code sent! Check your email.", "waiting")')
                    self.verification_webview.page().runJavaScript('setResendCooldown(30)')
                    self.verification_webview.page().runJavaScript('clearOtpInputs()')
                else:
                    self.verification_webview.page().runJavaScript(f'setStatus("Failed to resend: {data.get("error", "Unknown error")}", "error")')
            else:
                error_data = response.json()
                self.verification_webview.page().runJavaScript(f'setStatus("Server error: {error_data.get("error", response.status_code)}", "error")')
        except Exception as e:
            self.verification_webview.page().runJavaScript(f'setStatus("Error: {str(e)}", "error")')

    # ==================== TEACHER SELECTION ====================
    def show_teacher_selection(self):
        """Show the teacher selection dialog and then register the user."""
        if not TEACHER_SELECTOR_AVAILABLE or TeacherSelectorDialog is None:
            print("⚠️ TeacherSelectorDialog not available. Proceeding without room selection.")
            self.register_with_room(None)
            return

        print("📢 Opening Teacher Selection dialog after verification...")
        try:
            # Create dialog with maximized state and no resize
            dialog = TeacherSelectorDialog()
            dialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
            dialog.showMaximized()
            
            if dialog.exec() == QDialog.Accepted:
                room = dialog.get_selected_room()
                if room:
                    print(f"✅ User selected room: {room}")
                    self.registration_data["selected_room"] = room
                    self.register_with_room(room)
                else:
                    print("⚠️ No room selected by user")
                    reply = QMessageBox.question(
                        self,
                        "No Room Selected",
                        "No teacher was selected.\n\n"
                        "Do you want to skip this step and choose later?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.register_with_room(None)
                    else:
                        # Try again
                        QTimer.singleShot(500, self.show_teacher_selection)
            else:
                print("⚠️ Teacher selection dialog was cancelled")
                reply = QMessageBox.question(
                    self,
                    "Room Selection Required",
                    "You need to select a teacher to continue.\n\n"
                    "Do you want to try again?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    QTimer.singleShot(500, self.show_teacher_selection)
                else:
                    self.register_with_room(None)
        except Exception as e:
            print(f"❌ Error in teacher selection: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to open teacher selection: {str(e)}")
            self.register_with_room(None)

    def join_room_after_registration(self, token, room_value, user_id):
        """
        Join a room using the /api/account/join-room endpoint.
        
        Args:
            token: The authentication token
            room_value: The room ID or room name (from get_selected_room)
            user_id: The user ID
        """
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "X-User-ID": str(user_id),
                "Content-Type": "application/json"
            }
            
            json_data = {
                "room": room_value
            }
            
            print(f"📤 Sending join-room request for room: {room_value}")
            print(f"   Headers: Authorization=Bearer {token[:20]}..., X-User-ID={user_id}")
            
            response = account_config.post("/api/account/join-room", data=json_data, timeout=10, headers=headers)
            
            print(f"📥 Join-room response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Successfully joined room: {room_value}")
                    return True
                else:
                    error_msg = data.get("error", "Unknown error")
                    print(f"⚠️ Failed to join room: {error_msg}")
                    return False
            elif response.status_code == 401:
                print("⚠️ Authentication failed when joining room (token may need validation)")
                return False
            else:
                print(f"⚠️ Join-room failed with status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    pass
                return False
        except requests.exceptions.Timeout:
            print("⚠️ Timeout joining room")
            return False
        except requests.exceptions.ConnectionError:
            print("⚠️ Connection error joining room")
            return False
        except Exception as e:
            print(f"⚠️ Error joining room: {e}")
            return False

    def register_with_room(self, room):
        """Register the user with the selected room using account_config"""
        first_name = self.registration_data.get('first_name', '').strip()
        last_name = self.registration_data.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = first_name

        # ✅ FIX: Include the room in the registration request
        json_data = {
            "full_name": full_name,
            "age": str(self.registration_data.get("age", "")),
            "role": self.registration_data.get("role", "student"),
            "email": self.registration_data.get("email", ""),
            "password": self.registration_data.get("password", ""),
            "academic_stage": self.registration_data.get("study_level", "University Student"),
            "verification_id": self.verification_id,
            "room": room if room else ""  # ✅ Send the selected room to the server
        }

        print("Sending registration data:")
        for key, value in json_data.items():
            if key == "password":
                print(f"   {key}: {'*' * len(value)}")
            else:
                print(f"   {key}: {value}")

        self.verification_webview.page().runJavaScript('document.getElementById("verifyBtn").disabled = true')
        self.register_btn.setText("⏳ Creating...")
        self.register_btn.setEnabled(False)

        try:
            # Use account_config with CSRF support
            response = account_config.post("/api/register/quick", data=json_data, timeout=30)
            
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get("success"):
                    sound_manager.play_success()
                    account_data = data.get("data", {}).get("account", {})
                    token = data.get("data", {}).get("token")
                    
                    # Save auth data
                    account_config.save_auth_data(
                        user_id=account_data.get("id"),
                        access_token=token,
                        refresh_token=None,
                        expires_in=86400,
                        user_data=account_data
                    )
                    
                    # Save token to file
                    token_txt_path = os.path.join(os.path.dirname(__file__), "token.txt")
                    try:
                        with open(token_txt_path, 'w', encoding='utf-8') as f:
                            f.write(str(token))
                        print(f"✅ Token saved to {token_txt_path}")
                    except Exception as e:
                        print(f"Failed to save token: {e}")
                    
                    # ✅ If room was selected and included in registration, we don't need to join again
                    # The server already joined the user to the room during registration
                    if room:
                        print(f"✅ User registered with room: {room}")
                    else:
                        # If no room was selected, try to join via API (backward compatibility)
                        user_id = account_data.get("id")
                        if user_id and room:
                            print(f"📢 Joining room via API: {room}")
                            self.join_room_after_registration(token, room, user_id)
                    
                    tokens = {
                        "access_token": token,
                        "refresh_token": None,
                        "expires_in": 86400
                    }
                    
                    self.verification_webview.page().runJavaScript('setStatus("Account created successfully! Redirecting...", "success")')
                    QTimer.singleShot(1500, lambda: self.main_window.on_registration_success(account_data, tokens))
                else:
                    error_msg = data.get("error", "Registration failed")
                    self.show_verification_error(error_msg)
                    QMessageBox.warning(self, "Registration Failed", error_msg)
                    self.verification_webview.page().runJavaScript('document.getElementById("verifyBtn").disabled = false')
                    self.register_btn.setText("Create Account")
                    self.register_btn.setEnabled(True)
            else:
                error_data = response.json()
                error_msg = error_data.get("error", f"Server error: {response.status_code}")
                self.show_verification_error(error_msg)
                QMessageBox.warning(self, "Registration Failed", error_msg)
                self.verification_webview.page().runJavaScript('document.getElementById("verifyBtn").disabled = false')
                self.register_btn.setText("Create Account")
                self.register_btn.setEnabled(True)
        except Exception as e:
            self.show_verification_error(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error", f"Registration failed: {str(e)}")
            self.verification_webview.page().runJavaScript('document.getElementById("verifyBtn").disabled = false')
            self.register_btn.setText("Create Account")
            self.register_btn.setEnabled(True)

    def submit_registration(self):
        """Original submit_registration - now redirects to verification flow."""
        if not self.validate_current_page():
            return
        
        if not self.registration_data.get("role"):
            self.registration_data["role"] = "student"
        
        if not self.show_terms_dialog():
            sound_manager.play_error()
            QMessageBox.information(self, "Terms Required", 
                                   "You must accept the Terms & Conditions to create an account.")
            return
        
        sound_manager.play_click()
        self.request_verification()

    def closeEvent(self, event):
        """Clean up when closing"""
        if hasattr(self, 'verification_webview'):
            self.verification_webview.stop()
            self.verification_webview.setPage(None)
        event.accept()