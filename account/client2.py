import sys
import os
import json
import time
from datetime import datetime
# Import account_config with fallback
try:
    from .account_config import account_config
except ImportError:
    from account_config import account_config
API_BASE_URL = account_config.API_BASE_URL
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# Import from external files - use relative imports
from .LoginWindow import LoginWindow
from .MultiStepFormWindow import MultiStepFormWindow
from .ModernAccountPage import ModernAccountPage

# Import sound manager
from .SoundManager import sound_manager

# ==================== Encryption Utilities ====================
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SECRET = b"latigo_platform_secure_key_2024"
SALT = b"latigo_salt_2024"

def _get_cipher():
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET))
    return Fernet(key)

def encrypt_data(data):
    if data is None:
        return None
    try:
        cipher = _get_cipher()
        encrypted = cipher.encrypt(str(data).encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Encryption error: {e}")
        return data

def decrypt_data(encrypted_data):
    if encrypted_data is None:
        return None
    try:
        cipher = _get_cipher()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"⚠️ Decryption error: {e}")
        return encrypted_data

def get_token_txt_path():
    """Get the path to token.txt in the account folder"""
    account_dir = os.path.join(os.path.dirname(__file__), "account")
    os.makedirs(account_dir, exist_ok=True)
    return os.path.join(account_dir, "token.txt")

def save_token_txt(token):
    """Save token to account/token.txt with encryption"""
    if token is None:
        return False
    try:
        token_txt_path = get_token_txt_path()
        encrypted_token = encrypt_data(token)
        with open(token_txt_path, 'w', encoding='utf-8') as f:
            f.write(encrypted_token)
        print(f"✅ Token saved to account/token.txt (encrypted)")
        return True
    except Exception as e:
        print(f"❌ Failed to write token.txt: {e}")
        return False

def load_token_txt():
    """Load token from account/token.txt with decryption"""
    try:
        token_txt_path = get_token_txt_path()
        if not os.path.exists(token_txt_path):
            return None
        with open(token_txt_path, 'r', encoding='utf-8') as f:
            encrypted_token = f.read().strip()
        if not encrypted_token:
            return None
        decrypted_token = decrypt_data(encrypted_token)
        return decrypted_token
    except Exception as e:
        print(f"❌ Failed to read token.txt: {e}")
        return None

def remove_token_txt():
    """Remove account/token.txt file"""
    try:
        token_txt_path = get_token_txt_path()
        if os.path.exists(token_txt_path):
            os.remove(token_txt_path)
            print(f"✅ account/token.txt removed")
            return True
    except Exception as e:
        print(f"❌ Failed to remove token.txt: {e}")
    return False

def remove_old_token_txt():
    """Remove old token.txt from main directory (cleanup)"""
    try:
        old_path = os.path.join(os.path.dirname(__file__), "token.txt")
        if os.path.exists(old_path):
            os.remove(old_path)
            print(f"✅ Old token.txt removed from main directory")
            return True
    except Exception as e:
        print(f"⚠️ Could not remove old token.txt: {e}")
    return False
# ==============================================================

class TokenManager:
    """Manages token storage and retrieval with encryption"""
    
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token_data.json")
    
    @classmethod
    def save_tokens(cls, user_id, access_token, refresh_token, expires_in, user_data=None):
        """Save tokens to file with encryption"""
        expires_at = time.time() + expires_in
        
        # Encrypt sensitive data before saving
        encrypted_data = {
            "user_id": encrypt_data(str(user_id)) if user_id else None,
            "access_token": encrypt_data(access_token) if access_token else None,
            "refresh_token": encrypt_data(refresh_token) if refresh_token else None,
            "expires_at": expires_at,  # Numeric value, keep as is
            "saved_at": time.time(),  # Numeric value, keep as is
            "user_data": encrypt_data(json.dumps(user_data)) if user_data else None
        }
        
        try:
            with open(cls.TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(encrypted_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Tokens saved for user: {user_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to save tokens: {e}")
            return False
    
    @classmethod
    def load_tokens(cls):
        """Load tokens from file with decryption"""
        try:
            if not os.path.exists(cls.TOKEN_FILE):
                return None
            
            with open(cls.TOKEN_FILE, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            
            # Decrypt sensitive data
            token_data = {
                "user_id": decrypt_data(encrypted_data.get("user_id")),
                "access_token": decrypt_data(encrypted_data.get("access_token")),
                "refresh_token": decrypt_data(encrypted_data.get("refresh_token")),
                "expires_at": encrypted_data.get("expires_at"),  # Numeric value, not encrypted
                "saved_at": encrypted_data.get("saved_at"),  # Numeric value, not encrypted
                "user_data": json.loads(decrypt_data(encrypted_data.get("user_data"))) if encrypted_data.get("user_data") else None
            }
            
            # Check if tokens are still valid
            current_time = time.time()
            if token_data.get("expires_at", 0) < current_time:
                print("⚠️ Token expired")
                cls.clear_tokens()
                return None
            
            print(f"✅ Tokens loaded for user: {token_data.get('user_id')}")
            return token_data
        except Exception as e:
            print(f"❌ Failed to load tokens: {e}")
            return None
    
    @classmethod
    def clear_tokens(cls):
        """Clear saved tokens"""
        try:
            if os.path.exists(cls.TOKEN_FILE):
                os.remove(cls.TOKEN_FILE)
            print("✅ Tokens cleared")
        except Exception as e:
            print(f"❌ Failed to clear tokens: {e}")
    
    @classmethod
    def is_token_expired(cls):
        """Check if saved token is expired"""
        token_data = cls.load_tokens()
        if not token_data:
            return True
        
        current_time = time.time()
        expires_at = token_data.get("expires_at", 0)
        
        # Consider token expired if less than 5 minutes remaining
        return expires_at < (current_time + 300)
    
    @classmethod
    def update_tokens(cls, access_token, refresh_token, expires_in):
        """Update existing tokens"""
        token_data = cls.load_tokens()
        if not token_data:
            return False
        
        token_data["access_token"] = access_token
        token_data["refresh_token"] = refresh_token
        token_data["expires_at"] = time.time() + expires_in
        token_data["saved_at"] = time.time()
        
        try:
            with open(cls.TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Tokens updated for user: {token_data.get('user_id')}")
            return True
        except Exception as e:
            print(f"❌ Failed to update tokens: {e}")
            return False


class MainWindow(QMainWindow):
    """Main window with stacked widget for all screens"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Latigo Platform")
        self.setMinimumSize(900, 700)
        
        # Store reference to parent (for logout handling in embedded mode)
        self.parent_app = parent
        
        # Remove old token.txt from main directory on startup (cleanup)
        remove_old_token_txt()
        
        # Create central widget with stacked layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create stacked widget for all screens
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create thread pool
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)
        
        # Initialize windows
        self.login_window = None
        self.registration_form = None
        self.dashboard_window = None
        
        # Set stylesheet for all screens
        self.apply_styles()
        
        # Create sound test menu
        self.create_sound_test_menu()
        
        # Play startup sound
        QTimer.singleShot(500, sound_manager.play_notification)
        
        # Check for existing tokens and auto-login
        QTimer.singleShot(1000, self.check_auto_login)
    
    def check_auto_login(self):
        """Check for token txt file or saved tokens and auto-login"""
        print("🔍 Checking for saved tokens and token.txt...")
        token_data = None
        
        # Check for token.txt in account folder first (now encrypted)
        access_token = load_token_txt()
        if access_token:
            print("📄 account/token.txt found, attempting auto-login with token.txt...")
            # Show loading screen
            self.show_loading_screen()
            # Set config (user id will be set after validation)
            account_config.CURRENT_TOKEN = access_token
            self.validate_token_and_login(access_token, from_txt=True)
            return
        
        # Fallback to TokenManager
        token_data = TokenManager.load_tokens()
        if token_data:
            print("📁 Found saved tokens, attempting auto-login...")
            self.show_loading_screen()
            user_id = token_data.get("user_id")
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            user_data = token_data.get("user_data")
            account_config.CURRENT_USER_ID = user_id
            account_config.CURRENT_TOKEN = access_token
            account_config.CURRENT_REFRESH_TOKEN = refresh_token
            account_config.CURRENT_USER_DATA = user_data
            self.validate_token_and_login(access_token)
        else:
            print("📭 No saved tokens or token.txt found, showing login screen")
            self.show_login()
    
    def show_loading_screen(self):
        """Show loading screen while checking tokens"""
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        
        # Loading label
        loading_label = QLabel("🔐 Checking authentication...")
        loading_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #4361ee;
            margin-bottom: 20px;
        """)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        progress_bar.setFixedWidth(300)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4361ee;
                border-radius: 8px;
            }
        """)
        
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(progress_bar)
        
        self.stacked_widget.addWidget(loading_widget)
        self.stacked_widget.setCurrentWidget(loading_widget)
    
    def validate_token_and_login(self, token, from_txt=False):
        """Validate token with server and login if valid. If from_txt, set user id after validation."""
        import requests
        from .ApiWorker import ApiWorker
        
        def validate_token():
            try:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                # Use the token validation endpoint
                response = requests.get(f"{API_BASE_URL}/api/token/validate", headers=headers, timeout=5)
                return response
            except Exception as e:
                print(f"❌ Token validation error: {e}")
                return None
                
        def on_validation_response(response):
            # Remove loading screen
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if isinstance(widget, QWidget) and widget.layout() and widget.layout().itemAt(0):
                    if isinstance(widget.layout().itemAt(0).widget(), QLabel):
                        if "Checking authentication" in widget.layout().itemAt(0).widget().text():
                            self.stacked_widget.removeWidget(widget)
                            widget.deleteLater()
                            break
                            
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Token validated successfully, showing dashboard")
                    # Update user data from response
                    if account_config.CURRENT_USER_DATA is None:
                        account_config.CURRENT_USER_DATA = data.get("data", {})
                    # If from_txt, set user id and save to TokenManager
                    if from_txt:
                        user_id = data.get("data", {}).get("id")
                        account_config.CURRENT_USER_ID = user_id
                        # Save to TokenManager for future use
                        TokenManager.save_tokens(
                            user_id=user_id,
                            access_token=token,
                            refresh_token=None,
                            expires_in=86400,  # Default 24h
                            user_data=data.get("data", {})
                        )
                        # Save encrypted token to account/token.txt
                        save_token_txt(token)
                    self.show_dashboard()
                    return
                    
            print("❌ Token validation failed, showing login")
            # Clear invalid tokens
            TokenManager.clear_tokens()
            remove_token_txt()
            account_config.CURRENT_USER_ID = None
            account_config.CURRENT_TOKEN = None
            account_config.CURRENT_REFRESH_TOKEN = None
            account_config.CURRENT_USER_DATA = None
            self.show_login()
            
        worker = ApiWorker(validate_token)
        worker.signals.result.connect(on_validation_response)
        worker.signals.error.connect(lambda e: on_validation_response(None))
        self.thread_pool.start(worker)
    
    def show_login(self):
        """Show login screen"""
        if self.login_window is None:
            self.login_window = LoginWindow(self)
            self.stacked_widget.addWidget(self.login_window)
        
        self.stacked_widget.setCurrentWidget(self.login_window)
        self.resize(500, 600)
    
    def show_registration(self):
        """Show registration form"""
        sound_manager.play_click()
        
        if self.registration_form is None:
            self.registration_form = MultiStepFormWindow(self)
            self.stacked_widget.addWidget(self.registration_form)
        
        self.stacked_widget.setCurrentWidget(self.registration_form)
        self.resize(1000, 750)
        
        # Reset form when showing
        if hasattr(self.registration_form, 'reset_form'):
            self.registration_form.reset_form()
    
    def show_dashboard(self):
        """Show dashboard screen"""
        sound_manager.play_success()
        
        if not self.dashboard_window:
            self.dashboard_window = ModernAccountPage(self)
            self.stacked_widget.addWidget(self.dashboard_window)
        
        self.stacked_widget.setCurrentWidget(self.dashboard_window)
        self.resize(1200, 800)
    
    def on_login_success(self, user_data, tokens):
        """Handle successful login"""
        user_id = user_data.get("id")
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 86400)
        
        # Save tokens
        TokenManager.save_tokens(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_data=user_data
        )
        
        # Also save access_token to account/token.txt (encrypted)
        save_token_txt(access_token)
            
        account_config.CURRENT_USER_ID = user_id
        account_config.CURRENT_TOKEN = access_token
        account_config.CURRENT_REFRESH_TOKEN = refresh_token
        account_config.CURRENT_USER_DATA = user_data
        
        self.show_dashboard()
    
    def on_logout(self):
        """Handle logout"""
        # Clear tokens
        TokenManager.clear_tokens()
        
        # Remove account/token.txt
        remove_token_txt()
        
        # Clear config
        account_config.CURRENT_USER_ID = None
        account_config.CURRENT_TOKEN = None
        account_config.CURRENT_REFRESH_TOKEN = None
        account_config.CURRENT_USER_DATA = None
        
        # Remove dashboard window
        if self.dashboard_window:
            self.stacked_widget.removeWidget(self.dashboard_window)
            self.dashboard_window.deleteLater()
            self.dashboard_window = None
        
        # If this is an embedded instance (has parent_app), notify parent to handle logout
        if self.parent_app and hasattr(self.parent_app, 'handle_logout'):
            self.parent_app.handle_logout()
        else:
            # Standalone mode - just show login screen
            self.show_login()
    
    def on_registration_success(self, user_data, tokens):
        """Handle successful registration"""
        user_id = user_data.get("id")
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 86400)
        
        TokenManager.save_tokens(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_data=user_data
        )
        
        # Also save access_token to account/token.txt (encrypted)
        save_token_txt(access_token)
            
        account_config.CURRENT_USER_ID = user_id
        account_config.CURRENT_TOKEN = access_token
        account_config.CURRENT_REFRESH_TOKEN = refresh_token
        account_config.CURRENT_USER_DATA = user_data
        
        self.show_dashboard()
    
    def apply_styles(self):
        """Apply consistent styles to all screens"""
        style_sheet = """
        QMainWindow {
            background-color: #f5f7ff;
        }
        
        /* Input fields */
        QLineEdit {
            padding: 8px 12px;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            font-size: 13px;
            background-color: white;
            min-height: 32px;
            max-height: 32px;
        }
        
        QLineEdit:focus {
            border: 2px solid #4361ee;
        }
        
        QLineEdit[error="true"] {
            border: 2px solid #dc3545;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #4361ee;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 13px;
            min-height: 36px;
        }
        
        QPushButton:hover {
            background-color: #3a56d4;
        }
        
        QPushButton:disabled {
            background-color: #6c757d;
        }
        
        QComboBox {
            padding: 8px 12px;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            font-size: 13px;
            background-color: white;
            min-height: 32px;
        }
        
        QComboBox::drop-down {
            border: none;
            padding-right: 10px;
        }
        
        QComboBox QAbstractItemView {
            border: 1px solid #e9ecef;
            border-radius: 6px;
            background-color: white;
            selection-background-color: #e9ecef;
            padding: 8px;
        }
        
        QRadioButton {
            font-size: 13px;
            color: #212529;
            spacing: 8px;
        }
        
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid #ccc;
        }
        
        QRadioButton::indicator:checked {
            background-color: #4361ee;
            border-color: #4361ee;
        }
        
        QCheckBox {
            font-size: 12px;
            color: #212529;
        }
        
        /* New styles for registration form */
        QLabel[required="true"]::after {
            content: " *";
            color: #dc3545;
        }
        
        QPushButton#skipButton {
            background-color: #6c757d;
        }
        
        QPushButton#skipButton:hover {
            background-color: #5a6268;
        }
        
        /* Group boxes */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        /* Progress bar */
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 3px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4a00e0;
            border-radius: 3px;
        }
        
        /* Loading screen */
        QLabel#loadingLabel {
            font-size: 16px;
            font-weight: bold;
            color: #4361ee;
            padding: 20px;
        }
        """
        self.setStyleSheet(style_sheet)
    
    def create_sound_test_menu(self):
        """Create a menu to test all sounds"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 ملف")
        
        # Clear tokens action
        clear_action = QAction("🗑️ مسح بيانات الدخول", self)
        clear_action.triggered.connect(self.clear_token_data)
        file_menu.addAction(clear_action)
        
        # Exit action
        exit_action = QAction("🚪 خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Sound menu
        sound_menu = menubar.addMenu("🎵 الأصوات")
        
        # Add test actions for each sound
        sounds = [
            ("نقرة", sound_manager.play_click),
            ("نجاح", sound_manager.play_success),
            ("خطأ", sound_manager.play_error),
            ("إشعار", sound_manager.play_notification),
            ("رفع", sound_manager.play_upload),
            ("تعديل", sound_manager.play_edit),
            ("دخول", sound_manager.play_login),
            ("خروج", sound_manager.play_logout),
            ("تنبيه", sound_manager.play_alert),
        ]
        
        for sound_name, sound_func in sounds:
            action = QAction(f"تجربة صوت {sound_name}", self)
            action.triggered.connect(sound_func)
            sound_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("❓ مساعدة")
        about_action = QAction("حول التطبيق", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Token info menu
        token_action = QAction("🔐 معلومات التوكن", self)
        token_action.triggered.connect(self.show_token_info)
        help_menu.addAction(token_action)
    
    def clear_token_data(self):
        """Clear saved token data"""
        reply = QMessageBox.question(
            self, 
            "مسح بيانات الدخول",
            "هل أنت متأكد من رغبتك في مسح بيانات الدخول المحفوظة؟\n\n"
            "سيتم تسجيل خروجك من جميع الأجهزة.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            TokenManager.clear_tokens()
            remove_token_txt()
            remove_old_token_txt()
                
            sound_manager.play_success()
            QMessageBox.information(
                self,
                "تم المسح",
                "تم مسح بيانات الدخول بنجاح.\n\n"
                "ستحتاج إلى تسجيل الدخول مرة أخرى عند تشغيل التطبيق."
            )
    
    def show_about(self):
        """Show about information"""
        QMessageBox.information(self, "حول التطبيق",
            "منصة Latigo\n\n"
            "الإصدار: 2.1\n"
            "تطوير: فريق Latigo\n\n"
            "مميزات الإصدار الجديد:\n"
            "• تسجيل دخول تلقائي\n"
            "• حفظ توكنات آمن\n"
            "• دعم قاعدة بيانات SQLite\n"
            "• واجهة عربية محسنة\n"
            "• نظام صوتي تفاعلي")
    
    def show_token_info(self):
        """Show token information"""
        token_data = TokenManager.load_tokens()
        
        if not token_data:
            QMessageBox.information(self, "معلومات التوكن", "لا توجد توكنات محفوظة.")
            return
        
        user_id = token_data.get("user_id", "غير معروف")
        saved_at = token_data.get("saved_at", 0)
        expires_at = token_data.get("expires_at", 0)
        
        # Format dates
        saved_time = datetime.fromtimestamp(saved_at).strftime("%Y-%m-%d %H:%M:%S") if saved_at else "غير معروف"
        expires_time = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S") if expires_at else "غير معروف"
        
        # Calculate time remaining
        current_time = time.time()
        if expires_at > current_time:
            remaining_seconds = expires_at - current_time
            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            time_remaining = f"{hours} ساعة و {minutes} دقيقة"
        else:
            time_remaining = "منتهي"
        
        QMessageBox.information(self, "معلومات التوكن",
            f"معلومات التوكن المحفوظ:\n\n"
            f"👤 معرف المستخدم: {user_id}\n"
            f"📅 وقت الحفظ: {saved_time}\n"
            f"⏰ تاريخ الانتهاء: {expires_time}\n"
            f"🕒 المتبقي: {time_remaining}\n\n"
            f"الموقع: {TokenManager.TOKEN_FILE}")


def main():
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Apply Arabic language
    app.setApplicationName("منصة Latigo")
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()