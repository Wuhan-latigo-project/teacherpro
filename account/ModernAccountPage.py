import sys
import json
import os
import config

# Helper function to get account_config
def _get_account_config(main_window):
    """Get account_config from main_window or return a wrapper around root config"""
    if hasattr(main_window, "config") and main_window.config:
        acc_cfg = main_window.config.get("account_config")
        if acc_cfg is not None:
            return acc_cfg
    
    # Return root config wrapped with compatibility attributes
    class ConfigWrapper:
        def __init__(self, root_cfg):
            self._root = root_cfg
            # Copy all root attributes
            for attr in dir(root_cfg):
                if not attr.startswith('_'):
                    try:
                        setattr(self, attr, getattr(root_cfg, attr))
                    except:
                        pass
            # Add missing attributes that account_config would have
            self.CURRENT_USER_ID = getattr(root_cfg, 'CURRENT_USER_ID', None)
            self.CURRENT_TOKEN = getattr(root_cfg, 'CURRENT_TOKEN', None)
            self.CURRENT_USER_DATA = getattr(root_cfg, 'CURRENT_USER_DATA', None)
            self.CURRENT_REFRESH_TOKEN = getattr(root_cfg, 'CURRENT_REFRESH_TOKEN', None)
            self.API_BASE_URL = root_cfg.API_BASE_URL
        
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    return ConfigWrapper(config)

# Import account_config for API calls
try:
    from account_config import account_config
    ACCOUNT_CONFIG_AVAILABLE = True
except ImportError:
    ACCOUNT_CONFIG_AVAILABLE = False
    account_config = None
    print("⚠️ account_config not available, some features may not work")

API_BASE_URL = config.API_BASE_URL

import requests
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSslConfiguration, QSslSocket

from .ApiWorker import ApiWorker, WorkerSignals
from .ToggleSwitch import ToggleSwitch
import config

# Import sound manager
from .SoundManager import sound_manager

# ========== IMPORT TEACHER SELECTOR FOR ROOM CHANGE ==========
try:
    from teacherselector import TeacherSelectorDialog
    TEACHER_SELECTOR_AVAILABLE = True
except ImportError:
    TEACHER_SELECTOR_AVAILABLE = False
    TeacherSelectorDialog = None

# ========== IMPORT TOKEN MANAGER ==========
try:
    from token_manager import token_manager
    TOKEN_MANAGER_AVAILABLE = True
except ImportError:
    TOKEN_MANAGER_AVAILABLE = False
    token_manager = None


class ModernAccountPage(QWidget):
    # Add logout signal for secure logout handling
    logoutRequested = Signal()
    # Add signal for room change
    roomChanged = Signal()
    
    def __init__(self, main_window):
        super().__init__()
        # Get account_config from main_window or use root config
        account_config_obj = getattr(main_window, "account_config", None)
        if account_config_obj is None:
            account_config_obj = config
            print("✅ Using root config for account_config in ModernAccountPage")

        print("Creating ModernAccountPage...")
        self.main_window = main_window
        
        # Debug prints with proper error handling
        try:
            user_id = _get_account_config(self.main_window).CURRENT_USER_ID
            print(f"DEBUG: CURRENT_USER_ID = {user_id}")
        except AttributeError:
            print("DEBUG: CURRENT_USER_ID not available")
        
        try:
            token = _get_account_config(self.main_window).CURRENT_TOKEN
            print(f"DEBUG: CURRENT_TOKEN = {'Present' if token else 'Missing'}")
        except AttributeError:
            print("DEBUG: CURRENT_TOKEN not available")
        
        try:
            user_data = _get_account_config(self.main_window).CURRENT_USER_DATA
            print(f"DEBUG: CURRENT_USER_DATA = {user_data}")
        except AttributeError:
            print("DEBUG: CURRENT_USER_DATA not available")
        
        # Play dashboard sound
        if sound_manager:
            sound_manager.play_notification()
        
        # Initialize missing attributes
        self.parameters_page = None
        self.network_manager = QNetworkAccessManager()  # For avatar loading
        self.network_reply = None
        self.avatar_loading = False
        self.avatar_loaded = False
        
        # Debug: Check authentication status
        print(f"DEBUG: Checking auth status in ModernAccountPage...")
        
        # Check if user is authenticated - use try/except to handle missing attributes
        try:
            user_id = _get_account_config(self.main_window).CURRENT_USER_ID
            if not user_id:
                print("ERROR: No user ID, showing login...")
                if self.main_window and hasattr(self.main_window, 'show_login'):
                    self.main_window.show_login()
                return
            print(f"User authenticated with ID: {user_id}")
        except AttributeError as e:
            print(f"ERROR: Authentication check failed: {e}")
            if self.main_window and hasattr(self.main_window, 'show_login'):
                self.main_window.show_login()
            return
        
        # Initialize all attributes
        self.account_data = None
        self.activities_data = []
        self.toggle_switches = []
        self.thread_pool = None
        self.api_headers = None
        
        # Initialize API data with current user data
        try:
            user_data = _get_account_config(self.main_window).CURRENT_USER_DATA
            if user_data:
                self.account_data = user_data
                print(f"DEBUG: Loaded user data from config: {self.account_data}")
            else:
                self.account_data = {}
                print("WARNING: No user data in config")
        except AttributeError:
            self.account_data = {}
            print("WARNING: Could not load user data")
        
        self.activities_data = []
        self.toggle_switches = []
        
        # Create API headers
        try:
            user_id = _get_account_config(self.main_window).CURRENT_USER_ID
            token = _get_account_config(self.main_window).CURRENT_TOKEN
            self.api_headers = {"X-User-ID": str(user_id), "Content-Type": "application/json"}
            if token:
                self.api_headers["Authorization"] = f"Bearer {token}"
        except AttributeError as e:
            print(f"ERROR: Could not create API headers: {e}")
            self.api_headers = {"Content-Type": "application/json"}
        
        # Create thread pool for API calls
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)
        
        # Create central widget with scroll area
        self.create_scrollable_interface()
        
        # Apply styles
        self.apply_styles()
        
        print("Dashboard created, starting data load...")
        
        # Load data from API after window is shown
        QTimer.singleShot(500, self.load_all_data)
    
    def create_scrollable_interface(self):
        """Create a scrollable main interface with transparent background"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header (fixed, not scrollable) - FULLY TRANSPARENT
        self.create_header(main_layout)
        
        # Create scroll area for main content with transparent background
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(233, 236, 239, 0.3);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(67, 97, 238, 0.6);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(67, 97, 238, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create scroll content widget with transparent background
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        
        # Create main content
        self.create_main_content(scroll_layout)
        
        # Create footer
        self.create_footer(scroll_layout)
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def create_header(self, parent_layout):
        """Create the header with logo and user menu - FULLY TRANSPARENT"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QWidget#header {
                background: transparent;
                border-bottom: none;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 0, 40, 0)
        
        # Logo
        logo_layout = QHBoxLayout()

        logo_text = QLabel("Paltigo Dashboard")
        logo_text.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        
        # User menu
        user_menu_layout = QHBoxLayout()
        user_menu_layout.setSpacing(20)
        
        # Avatar - TRANSPARENT
        self.avatar_btn = QPushButton()
        self.avatar_btn.setFixedSize(50, 50)
        self.avatar_btn.clicked.connect(self.show_user_menu)
        self.avatar_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 25px;
            }
        """)
        user_menu_layout.addWidget(self.avatar_btn)
        
        # Add to header
        header_layout.addLayout(logo_layout)
        header_layout.addStretch()
        header_layout.addLayout(user_menu_layout)
        
        parent_layout.addWidget(header)

    def create_main_content(self, parent_layout):
        """Create the main content area with transparent backgrounds"""
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(30)
        
        # Create content container
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout(container)
        container_layout.setSpacing(30)
        
        # Create sidebar
        self.create_sidebar(container_layout)
        
        # Create main panel with stacked widget for different views
        self.create_main_panel(container_layout)
        
        content_layout.addWidget(container)
        parent_layout.addWidget(content_widget)

    def create_sidebar(self, parent_layout):
        """Create the sidebar with profile card and navigation"""
        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("background: transparent;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(20)
        
        # Profile card
        self.profile_card = self.create_profile_card()
        sidebar_layout.addWidget(self.profile_card)
        
        # Navigation menu
        nav_menu = self.create_navigation_menu()
        sidebar_layout.addWidget(nav_menu)
        sidebar_layout.addStretch()
        
        parent_layout.addWidget(sidebar)

    def create_profile_card(self):
        """Create the profile card widget with glass effect"""
        card = QWidget()
        card.setObjectName("profileCard")
        card.setFixedHeight(300)
        card.setStyleSheet("""
            QWidget#profileCard {
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(10)
        
        # Avatar container
        avatar_container = QWidget()
        avatar_container.setStyleSheet("background: transparent;")
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignCenter)
        
        # Create a circular avatar container
        self.avatar_container = QWidget()
        self.avatar_container.setFixedSize(120, 120)
        self.avatar_container.setStyleSheet("background: transparent;")
        
        # Create a layout for the avatar container
        container_layout = QVBoxLayout(self.avatar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create avatar label for image
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(120, 120)
        self.avatar_label.setObjectName("avatarLabel")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            #avatarLabel {
                border-radius: 60px;
                border: 3px solid rgba(255,255,255,0.4);
                background-color: rgba(108, 117, 125, 0.3);
            }
        """)
        
        # Create overlay widget for text (fallback)
        self.avatar_overlay = QWidget(self.avatar_label)
        self.avatar_overlay.setGeometry(0, 0, 120, 120)
        self.avatar_overlay.setStyleSheet("background: transparent;")
        overlay_layout = QVBoxLayout(self.avatar_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignCenter)
        
        self.avatar_text = QLabel("")
        self.avatar_text.setStyleSheet("""
            color: white;
            font-size: 36px;
            font-weight: bold;
            background: transparent;
        """)
        self.avatar_text.setAlignment(Qt.AlignCenter)
        
        overlay_layout.addWidget(self.avatar_text)
        
        container_layout.addWidget(self.avatar_label)
        avatar_layout.addWidget(self.avatar_container)
        
        # Name and role
        self.name_label = QLabel("Loading...")
        self.name_label.setObjectName("profileName")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel#profileName {
                font-size: 20px;
                font-weight: bold;
                color: #1d1d1f;
                background: transparent;
            }
        """)
        
        self.role_label = QLabel("Member")
        self.role_label.setObjectName("profileRole")
        self.role_label.setAlignment(Qt.AlignCenter)
        self.role_label.setStyleSheet("""
            QLabel#profileRole {
                color: #6c757d;
                font-size: 13px;
                background: transparent;
            }
        """)
        
        card_layout.addWidget(avatar_container)
        card_layout.addWidget(self.name_label)
        card_layout.addWidget(self.role_label)
        
        return card

    def create_profile_stats(self):
        """Create profile statistics widget"""
        stats_widget = QWidget()
        stats_widget.setFixedHeight(80)
        stats_widget.setStyleSheet("background: transparent;")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(20)
        
        # Create stat widgets
        self.stat_projects = self.create_stat_widget("0", "Projects")
        self.stat_following = self.create_stat_widget("0", "Following")
        self.stat_followers = self.create_stat_widget("0", "Followers")
        
        stats_layout.addWidget(self.stat_projects)
        stats_layout.addWidget(self.stat_following)
        stats_layout.addWidget(self.stat_followers)
        
        return stats_widget

    def create_stat_widget(self, value, label):
        """Create a single stat widget"""
        stat_widget = QWidget()
        stat_widget.setStyleSheet("background: transparent;")
        stat_layout = QVBoxLayout(stat_widget)
        stat_layout.setAlignment(Qt.AlignCenter)
        stat_layout.setSpacing(5)
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            QLabel#statValue {
                font-size: 22px;
                font-weight: bold;
                color: #4361ee;
                background: transparent;
            }
        """)
        
        label_label = QLabel(label)
        label_label.setObjectName("statLabel")
        label_label.setAlignment(Qt.AlignCenter)
        label_label.setStyleSheet("""
            QLabel#statLabel {
                font-size: 11px;
                color: #6c757d;
                background: transparent;
            }
        """)
        
        stat_layout.addWidget(value_label)
        stat_layout.addWidget(label_label)
        
        return stat_widget

    def create_navigation_menu(self):
        """Create navigation menu widget with glass effect"""
        menu_widget = QWidget()
        menu_widget.setObjectName("navMenu")
        menu_widget.setStyleSheet("""
            QWidget#navMenu {
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setSpacing(10)
        
        menu_items = [
            ("📊", "Dashboard", False),
            ("⚙️", "Settings", False),
            ("❓", "Help & Support", False)
        ]
        
        self.nav_buttons = []
        for icon, text, active in menu_items:
            btn = QPushButton(f"   {icon}  {text}")
            btn.setObjectName("navButton")
            btn.setProperty("active", "true" if active else "false")
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton#navButton {
                    text-align: left;
                    padding: 15px;
                    border-radius: 10px;
                    border: none;
                    background: transparent;
                    font-size: 14px;
                    color: #212529;
                }
                QPushButton#navButton[active="true"] {
                    background: rgba(67, 97, 238, 0.15);
                    color: #4361ee;
                    font-weight: bold;
                }
                QPushButton#navButton:hover {
                    background: rgba(67, 97, 238, 0.08);
                }
            """)
            menu_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
            # Connect signal
            btn.clicked.connect(lambda checked=False, b=btn: self.on_nav_clicked(b))
        
        return menu_widget

    def create_main_panel(self, parent_layout):
        """Create the main panel with stacked widget for different views"""
        panel_widget = QWidget()
        panel_widget.setObjectName("mainPanel")
        panel_widget.setStyleSheet("background: transparent;")
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setSpacing(30)

        # Create stacked widget for different views
        self.main_panel_stacked = QStackedWidget()
        self.main_panel_stacked.setStyleSheet("background: transparent;")

        # Dashboard page (default)
        self.dashboard_page = self.create_dashboard_page()
        self.main_panel_stacked.addWidget(self.dashboard_page)

        panel_layout.addWidget(self.main_panel_stacked)
        parent_layout.addWidget(panel_widget)

    def create_dashboard_page(self):
        """Create the dashboard page with transparent background"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(30)
        
        # Panel header
        header_widget = self.create_panel_header()
        layout.addWidget(header_widget)
        
        # Cards container
        self.cards_widget = self.create_cards_container()
        layout.addWidget(self.cards_widget)
        
        # Settings section
        self.settings_widget = self.create_settings_section()
        layout.addWidget(self.settings_widget)
        
        return page

    def create_panel_header(self):
        """Create panel header with title and button - TRANSPARENT"""
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Account Dashboard")
        title_label.setObjectName("panelTitle")
        title_label.setStyleSheet("""
            QLabel#panelTitle {
                font-size: 28px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        
        # Edit profile button - TRANSPARENT
        edit_btn = QPushButton("✏️  Edit Profile")
        edit_btn.setObjectName("editProfileBtn")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self.on_edit_profile)
        edit_btn.setStyleSheet("""
            QPushButton#editProfileBtn {
                background: rgba(255,255,255,0.15);
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#editProfileBtn:hover {
                background: rgba(255,255,255,0.25);
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(edit_btn)
        
        return header_widget

    def create_cards_container(self):
        """Create the cards container widget"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        
        # Create grid layout for cards
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setHorizontalSpacing(25)
        self.grid_layout.setVerticalSpacing(25)
        
        # Create placeholder cards (will be updated with API data)
        self.card1 = None
        self.card2 = None
        self.card3 = None
        
        # Add cards to grid
        self.grid_layout.addWidget(self.create_placeholder_card(), 0, 0)
        self.grid_layout.addWidget(self.create_placeholder_card(), 0, 1)
        self.grid_layout.addWidget(self.create_placeholder_card(), 1, 0, 1, 2)
        
        # Set column stretch for responsiveness
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        
        container_layout.addWidget(grid_widget)
        return container

    def create_placeholder_card(self):
        """Create a placeholder card while loading"""
        card = QWidget()
        card.setObjectName("card")
        card.setMinimumHeight(250)
        card.setStyleSheet("""
            QWidget#card {
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        
        loading_label = QLabel("Loading...")
        loading_label.setStyleSheet("color: #212529; font-size: 14px; background: transparent;")
        card_layout.addWidget(loading_label)
        
        return card

    def create_card(self, title, icon, icon_color, content_widget):
        """Create a card widget with consistent styling"""
        card = QWidget()
        card.setObjectName("card")
        card.setMinimumHeight(250)
        card.setStyleSheet("""
            QWidget#card {
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        
        # Card header
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet("""
            QLabel#cardTitle {
                font-size: 18px;
                font-weight: bold;
                color: #1d1d1f;
                background: transparent;
            }
        """)
        
        # Icon label with gradient background
        icon_label = QLabel(icon)
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Create gradient colors
        color1 = icon_color
        if icon_color == "#4361ee":
            color2 = "#4cc9f0"
        elif icon_color == "#7209b7":
            color2 = "#f72585"
        else:
            color2 = "#4895ef"
        
        icon_label.setStyleSheet(f"""
            border-radius: 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {color1}, stop:1 {color2});
            font-size: 24px;
            color: white;
            font-weight: bold;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        
        # Add to card
        card_layout.addWidget(header_widget)
        card_layout.addWidget(content_widget)
        
        return card

    def create_subscription_content(self):
        """Create subscription plan content"""
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        
        self.plan_info = QLabel("Loading subscription info...")
        self.plan_info.setWordWrap(True)
        self.plan_info.setStyleSheet("color: #212529; background: transparent;")
        
        self.renew_info = QLabel("")
        self.renew_info.setStyleSheet("color: #212529; background: transparent;")
        
        self.upgrade_btn = QPushButton("🔄  Upgrade Plan")
        self.upgrade_btn.setObjectName("upgradeBtn")
        self.upgrade_btn.setCursor(Qt.PointingHandCursor)
        self.upgrade_btn.clicked.connect(self.on_upgrade_plan)
        self.upgrade_btn.setStyleSheet("""
            QPushButton#upgradeBtn {
                background: rgba(67, 97, 238, 0.9);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#upgradeBtn:hover {
                background: rgba(67, 97, 238, 1);
            }
        """)
        
        layout.addWidget(self.plan_info)
        layout.addWidget(self.renew_info)
        layout.addStretch()
        layout.addWidget(self.upgrade_btn)
        
        return content

    def create_security_content(self):
        """Create security status content"""
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        
        self.security_info = QLabel("Loading security status...")
        self.security_info.setWordWrap(True)
        self.security_info.setStyleSheet("color: #212529; background: transparent;")
        
        # Security items
        self.items_widget = QWidget()
        self.items_widget.setStyleSheet("background: transparent;")
        self.items_layout = QVBoxLayout(self.items_widget)
        self.items_layout.setSpacing(10)
        
        # Placeholder items
        item1 = self.create_activity_item("✅", "2FA Status", "Loading...")
        item2 = self.create_activity_item("⚠️", "Unusual Activity", "Loading...")
        
        self.items_layout.addWidget(item1)
        self.items_layout.addWidget(item2)
        
        layout.addWidget(self.security_info)
        layout.addStretch()
        layout.addWidget(self.items_widget)
        
        return content

    def create_activity_content(self):
        """Create recent activity content"""
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.activity_layout = QVBoxLayout(content)  # Store as instance attribute
        self.activity_layout.setSpacing(10)
        
        # Placeholder
        placeholder = QLabel("Loading activities...")
        placeholder.setStyleSheet("color: #212529; font-size: 14px; background: transparent;")
        self.activity_layout.addWidget(placeholder)
        
        return content

    def create_activity_item(self, icon, title, description, time=None):
        """Create an activity item widget"""
        item = QWidget()
        item.setFixedHeight(60)
        item.setStyleSheet("""
            QWidget {
                background: transparent;
                border-radius: 8px;
            }
            QWidget:hover {
                background: rgba(0,0,0,0.03);
            }
        """)
        layout = QHBoxLayout(item)
        layout.setSpacing(15)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFixedSize(40, 40)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("""
                border-radius: 10px;
                background-color: rgba(76, 201, 240, 0.3);
                color: white;
                font-size: 20px;
                font-weight: bold;
            """)
            layout.addWidget(icon_label)
        
        # Details
        details_widget = QWidget()
        details_widget.setStyleSheet("background: transparent;")
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #212529; background: transparent;")
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #6c757d; font-size: 12px; background: transparent;")
        
        details_layout.addWidget(title_label)
        details_layout.addWidget(desc_label)
        
        layout.addWidget(details_widget)
        layout.addStretch()
        
        if time:
            time_label = QLabel(time)
            time_label.setStyleSheet("color: #6c757d; font-size: 12px; background: transparent;")
            layout.addWidget(time_label)
        
        return item

    def create_settings_section(self):
        """Create account settings section with glass effect"""
        section = QWidget()
        section.setObjectName("settingsSection")
        section.setStyleSheet("""
            QWidget#settingsSection {
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        layout = QVBoxLayout(section)
        layout.setSpacing(20)
        
        # Section title
        title = QLabel("Account Settings")
        title.setObjectName("settingsTitle")
        title.setStyleSheet("""
            QLabel#settingsTitle {
                font-size: 22px;
                font-weight: bold;
                color: #1d1d1f;
                padding-bottom: 10px;
                border-bottom: 1px solid rgba(0,0,0,0.08);
                background: transparent;
            }
        """)
        layout.addWidget(title)
        
        # Settings form
        self.form_widget = QWidget()
        self.form_widget.setStyleSheet("background: transparent;")
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setSpacing(20)
        
        # Email field
        email_layout = QVBoxLayout()
        email_label = QLabel("Email Address")
        email_label.setObjectName("formLabel")
        email_label.setStyleSheet("""
            QLabel#formLabel {
                font-weight: 500;
                color: #1d1d1f;
                font-size: 13px;
                background: transparent;
            }
        """)
        self.email_input = QLineEdit("Loading...")
        self.email_input.setObjectName("formInput")
        self.email_input.setFixedHeight(32)
        self.email_input.setReadOnly(True)
        self.email_input.setStyleSheet("""
            QLineEdit#formInput {
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1d1d1f;
            }
            QLineEdit#formInput:focus {
                border: 2px solid rgba(67, 97, 238, 0.5);
                background: rgba(255,255,255,0.8);
            }
        """)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        
        # Phone field
        phone_layout = QVBoxLayout()
        phone_label = QLabel("Phone Number")
        phone_label.setObjectName("formLabel")
        phone_label.setStyleSheet("""
            QLabel#formLabel {
                font-weight: 500;
                color: #1d1d1f;
                font-size: 13px;
                background: transparent;
            }
        """)
        self.phone_input = QLineEdit("")
        self.phone_input.setObjectName("formInput")
        self.phone_input.setFixedHeight(32)
        self.phone_input.setStyleSheet(self.email_input.styleSheet())
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_input)
        
        # Add form fields
        self.form_layout.addLayout(email_layout)
        self.form_layout.addLayout(phone_layout)
        
        # Save button
        self.save_btn = QPushButton("💾  Save Changes")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.on_save_changes)
        self.save_btn.setEnabled(False)
        self.save_btn.setFixedHeight(36)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton#saveBtn {
                background: rgba(67, 97, 238, 0.9);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#saveBtn:hover {
                background: rgba(67, 97, 238, 1);
            }
            QPushButton#saveBtn:disabled {
                background: rgba(0,0,0,0.1);
                color: rgba(0,0,0,0.3);
            }
        """)
        
        layout.addWidget(self.form_widget)
       # layout.addWidget(self.save_btn)
        
        # ===== CHANGE ROOM BUTTON =====
        self.change_room_btn = QPushButton("Change Room")
        self.change_room_btn.setObjectName("changeRoomBtn")
        self.change_room_btn.setCursor(Qt.PointingHandCursor)
        self.change_room_btn.clicked.connect(self.change_room)
        self.change_room_btn.setFixedHeight(36)
        self.change_room_btn.setStyleSheet( '''
              QPushButton#changeRoomBtn {
        background: rgba(30, 144, 255, 0.9);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 13px;
    }
    QPushButton#changeRoomBtn:hover {
        background: rgba(30, 144, 255, 1);
    }''')
        layout.addWidget(self.change_room_btn)
        
        return section

    def create_footer(self, parent_layout):
        """Create the footer with transparent background"""
        footer = QWidget()
        footer.setObjectName("footer")
        footer.setFixedHeight(80)
        footer.setStyleSheet("background: transparent;")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(40, 20, 40, 20)
        
        footer_text = QLabel("© 2026 Paltigo Platform. All rights reserved. | Privacy Policy | Terms of Service")
        footer_text.setAlignment(Qt.AlignCenter)
        footer_text.setObjectName("footerText")
        footer_text.setStyleSheet("""
            QLabel#footerText {
                color: rgba(255,255,255,0.6);
                font-size: 12px;
                background: transparent;
            }
        """)
        
        footer_layout.addWidget(footer_text)
        parent_layout.addWidget(footer)

    def apply_styles(self):
        """Apply all CSS styles to widgets - updated for transparent backgrounds"""
        style_sheet = """
            /* Main window */
            QMainWindow {
                background: transparent;
            }
            
            /* Central widget - transparent */
            #centralWidget {
                background: transparent;
            }
            
            #scrollContent {
                background: transparent;
            }
            
            #contentWidget {
                background: transparent;
            }
            
            /* Header - FULLY TRANSPARENT */
            #header {
                background: transparent;
                border-bottom: none;
            }
            
            /* General - transparent backgrounds */
            QWidget {
                background-color: transparent;
            }
            
            QLabel {
                background-color: transparent;
                color: #212529;
            }
            
            QPushButton {
                background-color: transparent;
                color: #212529;
            }
            
            /* Message Box Styles */
            QMessageBox {
                background-color: rgba(255,255,255,0.95);
            }
            QMessageBox QLabel {
                color: #212529;
                font-size: 14px;
                background: transparent;
            }
            QMessageBox QPushButton {
                background-color: #4361ee;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3a56d4;
            }
            QMessageBox QPushButton:pressed {
                background-color: #2a46b4;
            }
            
            /* Dialog Styles */
            QDialog {
                background-color: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
            }
            QDialog QLabel {
                color: #212529;
                background: transparent;
            }
            QDialog QLineEdit, QDialog QTextEdit, QDialog QComboBox {
                color: #212529;
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                padding: 8px;
            }
            QDialog QPushButton {
                color: white;
                background-color: #4361ee;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QDialog QPushButton:hover {
                background-color: #3a56d4;
            }
            QDialog QPushButton:pressed {
                background-color: #2a46b4;
            }
            QDialog QPushButton#cancelBtn {
                background-color: rgba(255,255,255,0.5);
                color: #4361ee;
                border: 2px solid #4361ee;
            }
            QDialog QPushButton#cancelBtn:hover {
                background-color: rgba(67, 97, 238, 0.1);
            }
            
            /* Group Box Styles */
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #212529;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: transparent;
            }
            
            /* Radio Button and Checkbox Styles */
            QRadioButton, QCheckBox {
                color: #212529;
                spacing: 8px;
                background: transparent;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 9px;
            }
            QRadioButton::indicator:checked {
                background-color: #4361ee;
                border: 2px solid #4361ee;
            }
            QCheckBox::indicator:checked {
                background-color: #4361ee;
                border: 2px solid #4361ee;
                border-radius: 4px;
            }
            QRadioButton::indicator:hover, QCheckBox::indicator:hover {
                border: 1px solid #4361ee;
            }
            
            /* Toggle Switches */
            #toggleLabel {
                font-weight: bold;
                color: #212529;
                background: transparent;
            }
        """
        
        self.setStyleSheet(style_sheet)

    # ========== API Methods ==========
    def load_all_data(self):
        """Load all data from API"""
        if not _get_account_config(self.main_window).CURRENT_USER_ID:
            print("ERROR: Cannot load data - no user ID")
            return
            
        print("Starting data load...")
        
        # Create worker for loading account data
        worker = ApiWorker(self.api_get_account)
        worker.signals.result.connect(self.on_account_data_loaded)
        worker.signals.error.connect(self.on_api_error)
        self.thread_pool.start(worker)
        
        # Create worker for loading activities
        worker2 = ApiWorker(self.api_get_activities)
        worker2.signals.result.connect(self.on_activities_loaded)
        worker2.signals.error.connect(self.on_api_error)
        self.thread_pool.start(worker2)
        
        # Notifications removed: no worker created
        
        # Create worker for loading dashboard stats
        worker5 = ApiWorker(self.api_get_dashboard_stats)
        worker5.signals.result.connect(self.on_dashboard_stats_loaded)
        worker5.signals.error.connect(self.on_api_error)
        self.thread_pool.start(worker5)

    def api_get_account(self):
        """API call to get account data using account_config"""
        print("Loading account data...")
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.get("/api/account", timeout=5)
                print(f"Account response status: {response.status_code}")
                return response
            except Exception as e:
                print(f"Account API error: {e}")
                raise
        else:
            # Fallback to requests
            response = requests.get(f"{API_BASE_URL}/api/account", headers=self.api_headers, timeout=5)
            print(f"Account response status: {response.status_code}")
            return response

    def api_get_activities(self):
        """API call to get activities using account_config"""
        print("Loading activities...")
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.get("/api/account/activities", timeout=5)
                return response
            except Exception as e:
                print(f"Activities API error: {e}")
                raise
        else:
            response = requests.get(f"{API_BASE_URL}/api/account/activities", headers=self.api_headers, timeout=5)
            return response

    def api_get_notifications(self):
        """API call to get notifications using account_config"""
        # Notifications removed: no API call
        raise NotImplementedError("Notifications have been removed from this build")

    def api_get_security(self):
        """API call to get security status using account_config"""
        print("Loading security...")
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.get("/api/account/security", timeout=5)
                return response
            except Exception as e:
                print(f"Security API error: {e}")
                raise
        else:
            response = requests.get(f"{API_BASE_URL}/api/account/security", headers=self.api_headers, timeout=5)
            return response

    def api_get_dashboard_stats(self):
        """API call to get dashboard stats using account_config"""
        print("Loading dashboard stats...")
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.get("/api/account/dashboard/stats", timeout=5)
                return response
            except Exception as e:
                print(f"Dashboard stats API error: {e}")
                raise
        else:
            response = requests.get(f"{API_BASE_URL}/api/account/dashboard/stats", headers=self.api_headers, timeout=5)
            return response

    def on_account_data_loaded(self, response):
        """Handle loaded account data"""
        if response.status_code == 200:
            data = response.json()
            print(f"Account data: {data}")
            
            if data.get("success"):
                self.account_data = data.get("data", {})
                self.update_profile_display()
                
                # Load avatar if exists
                avatar_url = self.account_data.get("avatar")
                print(f"DEBUG: Avatar URL from account data: {avatar_url}")
                
                if avatar_url and avatar_url.strip() and avatar_url != "not set yet!":
                    print(f"DEBUG: Loading avatar from URL: {avatar_url}")
                    if hasattr(self, 'avatar_loading') and self.avatar_loading:
                        print("DEBUG: Avatar already loading, skipping...")
                    else:
                        self.avatar_loading = True
                        self.avatar_loaded = False
                        self.cleanup_network_reply()
                        QTimer.singleShot(200, lambda: self.load_avatar_image(avatar_url))
                else:
                    print("DEBUG: No avatar URL in account data, showing initials")
                    self.show_avatar_initials()

    def on_activities_loaded(self, response):
        """Handle loaded activities"""
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.activities_data = data.get("data", [])
                QTimer.singleShot(0, self.update_activities_display)

    def on_notifications_loaded(self, response):
        """Notifications removed; handler disabled."""
        return

    def on_security_loaded(self, response):
        """Handle loaded security status"""
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                security_data = data.get("data", {})
                self.update_security_display(security_data)

    def on_dashboard_stats_loaded(self, response):
        """Handle loaded dashboard stats"""
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats_data = data.get("data", {})
                self.update_dashboard_cards(stats_data)

    def on_api_error(self, error_msg):
        """Handle API error"""
        print(f"API Error: {error_msg}")

    def load_avatar_image(self, avatar_url):
        """Load avatar image from URL with SSL bypass"""
        print(f"\n=== DEBUG: Loading avatar image ===")
        print(f"DEBUG: Avatar URL: {avatar_url}")
        
        if not avatar_url or avatar_url.strip() == "" or avatar_url.strip() == "not set yet!":
            print("DEBUG: No valid avatar URL provided, using initials")
            self.show_avatar_initials()
            return
            
        try:
            # Build the full URL
            if avatar_url.startswith('/'):
                full_url = f"https://{config.SERVER_IP}:8443{avatar_url}"
            elif avatar_url.startswith('http'):
                full_url = avatar_url
            else:
                full_url = f"https://{config.SERVER_IP}:8443/uploads/avatars/{avatar_url}"
                
            print(f"DEBUG: Full URL: {full_url}")
            
            # Create a new network manager if needed
            if not hasattr(self, 'network_manager') or self.network_manager is None:
                self.network_manager = QNetworkAccessManager()
            
            # ✅ FIX: Configure SSL to ignore certificate errors for self-signed certs
            ssl_config = QSslConfiguration.defaultConfiguration()
            ssl_config.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyNone)
            
            request = QNetworkRequest(QUrl(full_url))
            request.setSslConfiguration(ssl_config)
            request.setRawHeader(b"Accept", b"image/*")
            request.setAttribute(QNetworkRequest.Attribute.Http2AllowedAttribute, True)
            request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, 
                                QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
            
            # Add authentication headers
            try:
                token = _get_account_config(self.main_window).CURRENT_TOKEN
                user_id = _get_account_config(self.main_window).CURRENT_USER_ID
                if token:
                    request.setRawHeader(b"Authorization", f"Bearer {token}".encode())
                if user_id:
                    request.setRawHeader(b"X-User-ID", str(user_id).encode())
            except:
                pass
            
            self.current_avatar_url = full_url
            self.cleanup_network_reply()
            
            # Make the request
            self.network_reply = self.network_manager.get(request)
            self.network_reply.finished.connect(self.on_avatar_loaded)
            self.network_reply.errorOccurred.connect(self.on_avatar_error)
            
        except Exception as e:
            print(f"DEBUG: Error preparing avatar load: {type(e).__name__}: {e}")
            self.avatar_loading = False
            self.show_avatar_initials()

    def on_avatar_error(self, error):
        """Handle avatar loading error"""
        print(f"DEBUG: Avatar network error: {error}")
        self.avatar_loading = False
        self.show_avatar_initials()
        self.cleanup_network_reply()

    def on_avatar_loaded(self):
        """Handle loaded avatar image"""
        print(f"\n=== DEBUG: Avatar load completed ===")
        
        self.avatar_loading = False
        
        if not hasattr(self, 'network_reply') or self.network_reply is None:
            print("DEBUG: Network reply no longer exists, skipping...")
            return
        
        reply = self.network_reply
        
        try:
            try:
                error = reply.error()
                is_no_error = (error == QNetworkReply.NoError)
            except RuntimeError:
                print("DEBUG: Network reply object was deleted, skipping...")
                self.cleanup_network_reply()
                return
                
            if is_no_error:
                try:
                    data = reply.readAll()
                    print(f"DEBUG: Received {len(data)} bytes of image data")
                    
                    if len(data) == 0:
                        print("DEBUG: No image data received")
                        self.show_avatar_initials()
                        return
                    
                    pixmap = QPixmap()
                    load_success = pixmap.loadFromData(data)
                    
                    if load_success and not pixmap.isNull():
                        # Scale and create circular avatar
                        frame_size = 120
                        border_thickness = 3
                        inner_size = frame_size - 2 * border_thickness

                        scaled_pixmap = pixmap.scaled(
                            inner_size, inner_size,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        # Create circular pixmap for profile card
                        circular_pixmap = QPixmap(frame_size, frame_size)
                        circular_pixmap.fill(Qt.GlobalColor.transparent)

                        painter = QPainter(circular_pixmap)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                        # Draw border
                        painter.setBrush(QColor("#ffffff"))
                        painter.setPen(QPen(QColor("rgba(255,255,255,0.4)"), border_thickness))
                        painter.drawEllipse(border_thickness/2, border_thickness/2,
                                            frame_size - border_thickness,
                                            frame_size - border_thickness)

                        # Clip to circle and draw image
                        path = QPainterPath()
                        path.addEllipse(border_thickness, border_thickness, inner_size, inner_size)
                        painter.setClipPath(path)

                        offset = border_thickness
                        painter.drawPixmap(offset, offset, scaled_pixmap)
                        painter.end()

                        self.avatar_label.setPixmap(circular_pixmap)
                        self.avatar_label.setStyleSheet("""
                            #avatarLabel {
                                border-radius: 60px;
                                border: none;
                                background-color: transparent;
                            }
                        """)
                        self.avatar_text.hide()
                        self.avatar_loaded = True
                        
                        # Update header avatar
                        self.update_header_avatar(circular_pixmap)
                        
                        print("DEBUG: Avatar image loaded and displayed successfully")
                    else:
                        print("DEBUG: Failed to load pixmap from data")
                        self.show_avatar_initials()
                except Exception as e:
                    print(f"DEBUG: Error reading image data: {type(e).__name__}: {e}")
                    self.show_avatar_initials()
            else:
                try:
                    error_str = reply.errorString()
                    print(f"DEBUG: Network error loading avatar: {error_str}")
                except RuntimeError:
                    print("DEBUG: Network error (reply object deleted)")
                self.show_avatar_initials()
                
        except Exception as e:
            print(f"DEBUG: Error processing avatar image: {type(e).__name__}: {e}")
            self.show_avatar_initials()
        finally:
            print("=== DEBUG: Avatar load process finished ===\n")
            self.cleanup_network_reply()

    def update_header_avatar(self, pixmap):
        """Update header avatar button with image"""
        if pixmap and not pixmap.isNull():
            header_pixmap = pixmap.scaled(
                50, 50,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            circular_header_pixmap = QPixmap(50, 50)
            circular_header_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(circular_header_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addEllipse(0, 0, 50, 50)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, header_pixmap)
            painter.end()
            
            icon = QIcon(circular_header_pixmap)
            self.avatar_btn.setIcon(icon)
            self.avatar_btn.setIconSize(QSize(50, 50))
            self.avatar_btn.setText("")

    def show_avatar_initials(self):
        """Show avatar initials as fallback"""
        self.avatar_loading = False
        self.avatar_loaded = False
        
        if not self.account_data:
            return
            
        name = self.account_data.get("display_name", "")
        if not name:
            name = self.account_data.get("first_name", "") + " " + self.account_data.get("last_name", "")
        
        parts = name.split()
        if len(parts) >= 2:
            initials = parts[0][0].upper() + parts[1][0].upper()
        elif len(parts) == 1 and len(parts[0]) > 0:
            initials = parts[0][0].upper()
        else:
            initials = "AM"
        
        self.avatar_text.setText(initials)
        self.avatar_text.show()
        
        colors = ['#4361ee', '#7209b7', '#4cc9f0', '#f72585', '#4895ef']
        color_index = hash(initials) % len(colors)
        self.avatar_label.setStyleSheet(f"""
            #avatarLabel {{
                border-radius: 60px;
                border: 3px solid rgba(255,255,255,0.4);
                background-color: {colors[color_index]};
            }}
        """)
        
        # Clear any existing pixmap
        self.avatar_label.setPixmap(QPixmap())
        
        self.update_header_with_initials(initials, colors[color_index])

    def update_header_with_initials(self, initials, color):
        """Update header avatar with initials"""
        header_pixmap = QPixmap(50, 50)
        header_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(header_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 50, 50)
        
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        painter.drawText(header_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initials)
        painter.end()
        
        icon = QIcon(header_pixmap)
        self.avatar_btn.setIcon(icon)
        self.avatar_btn.setIconSize(QSize(50, 50))
        self.avatar_btn.setText("")

    def cleanup_network_reply(self):
        """Safely clean up network reply"""
        try:
            if hasattr(self, 'network_reply') and self.network_reply is not None:
                reply = self.network_reply
                self.network_reply = None
                try:
                    try:
                        reply.finished.disconnect()
                        reply.errorOccurred.disconnect()
                    except:
                        pass
                    try:
                        reply.deleteLater()
                    except RuntimeError:
                        pass
                except Exception as e:
                    print(f"DEBUG: Error in reply cleanup: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"DEBUG: Unexpected error cleaning up network reply: {type(e).__name__}: {e}")

    def update_profile_display(self):
        """Update profile display with API data"""
        if not self.account_data:
            return
            
        print("Updating profile display...")
        
        self.name_label.setText(self.account_data.get("display_name", "Unknown"))
        self.role_label.setText(self.account_data.get("role", "Member"))
        
        self.email_input.setText(self.account_data.get("email", ""))
        self.phone_input.setText(self.account_data.get("phone", ""))
        
        for i in reversed(range(self.form_layout.count())):
            widget = self.form_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                if widget.findChild(ToggleSwitch):
                    widget.deleteLater()
        
        self.toggle_switches = []
        
        toggles = [
            ("Two-Factor Authentication", self.account_data.get("two_factor_enabled", True))
        ]
        
        for label_text, checked in toggles:
            toggle_widget = self.create_switch_setting(label_text, checked)
            self.form_layout.addWidget(toggle_widget)
        
        self.save_btn.setEnabled(True)

    def update_activities_display(self):
        """Update activities display with API data"""
        if not hasattr(self, 'activity_layout') or not self.activity_layout:
            return
            
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for activity in self.activities_data[:3]:
            icon = activity.get("icon", "")
            action = activity.get("action", "")
            description = activity.get("description", "")
            timestamp = activity.get("timestamp", "")
            
            time_text = self.format_relative_time(timestamp)
            
            item = self.create_activity_item(icon, action, description, time_text)
            self.activity_layout.addWidget(item)
        
        if len(self.activities_data) > 3:
            view_all_btn = QPushButton("View All Activities →")
            view_all_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #4361ee;
                    border: none;
                    padding: 5px;
                    font-size: 12px;
                    text-align: left;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)
            view_all_btn.setCursor(Qt.PointingHandCursor)
            view_all_btn.clicked.connect(self.view_all_activities)
            self.activity_layout.addWidget(view_all_btn)

    def update_notifications_badge(self, unread_count):
        # Notifications removed: no badge to update
        return

    def update_security_display(self, security_data):
        """Update security display"""
        if not security_data:
            return
            
        print("Updating security display...")
        
        if not hasattr(self, 'security_info') or not self.security_info:
            return
            
        if not hasattr(self, 'items_layout') or not self.items_layout:
            return
        
        two_fa = "enabled" if security_data.get("two_factor_enabled") else "disabled"
        unusual = "No" if not security_data.get("unusual_activity") else "Yes"
        last_login = security_data.get("last_login", "Unknown")
        
        self.security_info.setText(
            f"Your account security is <strong>{'strong' if two_fa == 'enabled' else 'moderate'}</strong>. "
            f"Two-factor authentication is {two_fa}. Last login: {last_login}"
        )
        
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        item1 = self.create_activity_item("✅" if two_fa == "enabled" else "❌", 
                                          "2FA Status", 
                                          f"Two-factor authentication is {two_fa}")
        item2 = self.create_activity_item("⚠️" if unusual == "Yes" else "✅", 
                                          "Unusual Activity", 
                                          f"{unusual} unusual activity detected")
        
        self.items_layout.addWidget(item1)
        self.items_layout.addWidget(item2)

    def update_dashboard_cards(self, stats_data):
        """Update dashboard cards with API data"""
        print("Updating dashboard cards...")
        
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        activity_content = self.create_activity_content()
        self.card3 = self.create_card(
            "Recent Activity",
            "🔄",
            "#4cc9f0",
            activity_content
        )
        
        self.grid_layout.addWidget(self.card3, 0, 0, 1, 2)
        # If activities were already loaded, refresh the new activity widget
        try:
            if hasattr(self, 'activities_data') and self.activities_data:
                QTimer.singleShot(0, self.update_activities_display)
        except Exception:
            pass

    def format_relative_time(self, timestamp_str):
        """Format timestamp to relative time (e.g., '10 min ago')"""
        try:
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(timestamp.tzinfo)
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes} min ago"
            else:
                return "Just now"
        except:
            return timestamp_str

    def create_switch_setting(self, label_text, checked):
        """Create a toggle switch setting with working switch button"""
        widget = QWidget()
        widget.setFixedHeight(50)
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setObjectName("toggleLabel")
        label.setStyleSheet("""
            QLabel#toggleLabel {
                font-weight: 500;
                color: #1d1d1f;
                font-size: 14px;
                background: transparent;
            }
        """)
        
        toggle_switch = ToggleSwitch()
        toggle_switch.setChecked(checked)
        
        toggle_switch.toggled.connect(
            lambda state, lbl=label_text: self.on_switch_changed(lbl, state)
        )
        
        self.toggle_switches.append((label_text, toggle_switch))
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(toggle_switch)
        
        return widget

    # ========== Event Handlers ==========
    def on_nav_clicked(self, button):
        """Handle navigation button clicks"""
        if sound_manager:
            sound_manager.play_click()
        
        for btn in self.nav_buttons:
            btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        button.setProperty("active", "true")
        button.style().unpolish(button)
        button.style().polish(button)
        
        button_text = button.text()
        if "Dashboard" in button_text:
            self.show_dashboard_page()
        elif "Parameters" in button_text:
            self.show_parameters_page()
        elif "Settings" in button_text:
            if sound_manager:
                sound_manager.play_click()
            QMessageBox.information(self, "Coming Soon", "this futchers comming soon !")
        elif "Billing" in button_text:
            if sound_manager:
                sound_manager.play_click()
            QMessageBox.information(self, "Coming Soon", "this futchers comming soon !")
        elif "Security" in button_text:
            if sound_manager:
                sound_manager.play_click()
            QMessageBox.information(self, "Coming Soon", "this futchers comming soon !")
        elif "Help" in button_text:
            if sound_manager:
                sound_manager.play_click()
            QMessageBox.information(self, "Help & Support", 
                                  "For assistance, please contact:\n\n"
                                  "Email: support@Paltigoplatform.com\n"
                                  "Phone: 1-800-123-4567\n"
                                  "Live Chat: Available 9AM-5PM EST")

    def show_dashboard_page(self):
        """Show dashboard page"""
        if hasattr(self, 'main_panel_stacked'):
            self.main_panel_stacked.setCurrentWidget(self.dashboard_page)

    def show_parameters_page(self):
        """Show parameters page"""
        from ParametersPage import ParametersPage
        
        if not hasattr(self, 'parameters_page') or self.parameters_page is None:
            self.parameters_page = ParametersPage(self.main_window)
            self.main_panel_stacked.addWidget(self.parameters_page)
        
        if hasattr(self, 'main_panel_stacked'):
            self.main_panel_stacked.setCurrentWidget(self.parameters_page)

    def on_switch_changed(self, label, state):
        """Handle toggle switch state changes"""
        if label == "Two-Factor Authentication":
            QMessageBox.information(self, "Coming Soon", "this futchers comming soon !")
            for label_text, toggle in self.toggle_switches:
                if label_text == label:
                    toggle.blockSignals(True)
                    toggle.setChecked(not state)
                    toggle.blockSignals(False)
                    break
            return
        status = "enabled" if state else "disabled"
        print(f"Switch '{label}' changed to: {status}")

    def on_edit_profile(self):
        """Handle edit profile button click"""
        if sound_manager:
            sound_manager.play_click()
            
        if not self.account_data:
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(self, "Error", "No account data loaded")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Profile")
        dialog.setFixedSize(400, 500)
        dialog.setStyleSheet("""
            QDialog {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
            }
            QLabel {
                color: #212529;
                font-size: 14px;
                background: transparent;
            }
            QLineEdit, QTextEdit {
                color: #212529;
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton {
                color: white;
                background-color: #4361ee;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:pressed {
                background-color: #2a46b4;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        name_input = QLineEdit(self.account_data.get("display_name", ""))
        email_input = QLineEdit(self.account_data.get("email", ""))
        email_input.setReadOnly(True)
        bio_input = QTextEdit(self.account_data.get("bio", ""))
        bio_input.setMaximumHeight(100)
        phone_input = QLineEdit(self.account_data.get("phone", ""))
        
        avatar_label = QLabel("Avatar:")
        avatar_btn = QPushButton("Upload New Avatar")
        avatar_btn.clicked.connect(lambda: self.upload_avatar(dialog))
        
        form_layout.addRow("Name:", name_input)
        form_layout.addRow("Email:", email_input)
        form_layout.addRow("Phone:", phone_input)
        form_layout.addRow("Bio:", bio_input)
        form_layout.addRow(avatar_label, avatar_btn)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_profile_changes(
            dialog, name_input.text(), phone_input.text(), bio_input.toPlainText()
        ))
        button_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        
        dialog.exec()

    def save_profile_changes(self, dialog, name, phone, bio):
        """Save profile changes to API using worker"""
        if sound_manager:
            sound_manager.play_click()
        
        data = {
            "display_name": name,
            "phone": phone,
            "bio": bio
        }
        
        print(f"Saving profile changes: {data}")
        
        worker = ApiWorker(self.api_update_profile, data)
        worker.signals.result.connect(lambda r: self.on_profile_update_response(r, dialog))
        worker.signals.error.connect(lambda e: self.on_profile_update_error(e, dialog))
        self.thread_pool.start(worker)
        
        dialog.findChild(QDialogButtonBox).setEnabled(False)
        dialog.setWindowTitle("Saving...")

    def api_update_profile(self, data):
        """API call to update profile using account_config"""
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.put("/api/account", data=data, timeout=5)
                return response
            except Exception as e:
                print(f"Update profile API error: {e}")
                raise
        else:
            response = requests.put(f"{API_BASE_URL}/api/account", 
                                   headers=self.api_headers,
                                   json=data,
                                   timeout=5)
            return response

    def on_profile_update_response(self, response, dialog):
        """Handle profile update response"""
        dialog.findChild(QDialogButtonBox).setEnabled(True)
        dialog.setWindowTitle("Edit Profile")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                if sound_manager:
                    sound_manager.play_success()
                self.load_all_data()
                dialog.accept()
                QMessageBox.information(self, "Success", "Profile updated successfully!")
            else:
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "Error", response_data.get("error", "Failed to update profile"))
        else:
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(self, "Error", f"API error: {response.status_code}")

    def on_profile_update_error(self, error_msg, dialog):
        """Handle profile update error"""
        dialog.findChild(QDialogButtonBox).setEnabled(True)
        dialog.setWindowTitle("Edit Profile")
        if sound_manager:
            sound_manager.play_error()
        QMessageBox.warning(self, "API Error", f"Failed to save changes: {error_msg}")

    def upload_avatar(self, dialog):
        """Upload avatar image with SSL verification disabled"""
        if sound_manager:
            sound_manager.play_click()
        print("\n=== DEBUG: Starting avatar upload ===")
        
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.webp)")
        file_dialog.setWindowTitle("Select Avatar Image")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            print(f"DEBUG: Selected files: {selected_files}")
            
            if not selected_files:
                print("DEBUG: No files selected")
                return
                
            file_path = selected_files[0]
            print(f"DEBUG: Selected file path: {file_path}")
            
            # Check file size (max 10MB)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "Error", "File too large. Maximum size is 10MB.")
                return
            
            try:
                # Get file extension and MIME type
                file_ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_types.get(file_ext, 'application/octet-stream')
                
                if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    if sound_manager:
                        sound_manager.play_error()
                    QMessageBox.warning(self, "Error", "Invalid file format. Allowed: JPG, PNG, GIF, WEBP")
                    return
                
                with open(file_path, 'rb') as f:
                    files = {'avatar': (os.path.basename(file_path), f, mime_type)}
                    
                    # Build headers with authentication
                    user_id = _get_account_config(self.main_window).CURRENT_USER_ID
                    token = _get_account_config(self.main_window).CURRENT_TOKEN
                    headers = {}
                    if user_id:
                        headers["X-User-ID"] = str(user_id)
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    
                    # Build URL with HTTPS
                    url = f"https://{config.SERVER_IP}:8443/api/account/avatar"
                    if url.startswith("http://"):
                        url = url.replace("http://", "https://", 1)
                    
                    print(f"DEBUG: Uploading avatar to: {url}")
                    
                    # ✅ Disable SSL verification for self-signed certs
                    response = requests.post(
                        url,
                        headers=headers,
                        files=files,
                        timeout=30,
                        verify=False  # Disable SSL verification
                    )
                    
                    print(f"DEBUG: Response status code: {response.status_code}")
                    print(f"DEBUG: Response text: {response.text}")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            print(f"DEBUG: Response data: {response_data}")
                            
                            if response_data.get("success"):
                                if sound_manager:
                                    sound_manager.play_upload()
                                
                                QMessageBox.information(self, "Success", "Avatar uploaded successfully!")
                                
                                avatar_url = response_data.get("data", {}).get("avatar_url")
                                print(f"DEBUG: Avatar URL from response: {avatar_url}")
                                
                                if avatar_url:
                                    print(f"DEBUG: Loading new avatar from URL: {avatar_url}")
                                    # Force refresh avatar
                                    self.avatar_loading = False
                                    self.avatar_loaded = False
                                    self.cleanup_network_reply()
                                    self.avatar_label.clear()
                                    self.avatar_label.setPixmap(QPixmap())
                                    QTimer.singleShot(100, lambda: self.load_avatar_image(avatar_url))
                                else:
                                    print("DEBUG: No avatar URL in response, reloading all data")
                                    self.load_all_data()
                            else:
                                error_msg = response_data.get("error", "Failed to upload avatar")
                                print(f"DEBUG: API returned error: {error_msg}")
                                if sound_manager:
                                    sound_manager.play_error()
                                QMessageBox.warning(self, "Error", error_msg)
                                
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error: {e}")
                            if sound_manager:
                                sound_manager.play_error()
                            QMessageBox.warning(self, "Error", "Invalid server response")
                            
                    elif response.status_code == 401:
                        if sound_manager:
                            sound_manager.play_error()
                        QMessageBox.warning(self, "Authentication Error", 
                                          "Your session has expired. Please logout and login again.")
                        self.logout()
                    elif response.status_code == 415:
                        if sound_manager:
                            sound_manager.play_error()
                        QMessageBox.warning(self, "Error", 
                                          "Unsupported media type. Please make sure you're uploading a valid image file.")
                    elif response.status_code == 413:
                        if sound_manager:
                            sound_manager.play_error()
                        QMessageBox.warning(self, "Error", "File too large. Maximum size is 10MB.")
                    else:
                        print(f"DEBUG: Server error: {response.status_code}")
                        if sound_manager:
                            sound_manager.play_error()
                        QMessageBox.warning(self, "Error", f"Server error: {response.status_code}")
                        
            except requests.exceptions.SSLError:
                print("DEBUG: SSL Error during upload")
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "SSL Error", 
                                  "Unable to establish secure connection. Please check your network settings.")
            except requests.exceptions.Timeout:
                print("DEBUG: Timeout during upload")
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "Timeout Error", 
                                  "The request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                print("DEBUG: Connection error during upload")
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "Connection Error", 
                                  "Unable to connect to the server. Please check your internet connection.")
            except Exception as e:
                print(f"DEBUG: Unexpected error: {type(e).__name__}: {e}")
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "Error", f"Failed to upload avatar: {str(e)}")
                
            finally:
                print("=== DEBUG: Avatar upload process finished ===\n")
        else:
            print("DEBUG: File dialog was cancelled")

    def on_upgrade_plan(self):
        """Handle upgrade plan button click"""
        if sound_manager:
            sound_manager.play_click()
        
        try:
            from subscription import SubscriptionPopupSample
        except ImportError as e:
            print(f"Failed to import SubscriptionPopupSample: {e}")
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(
                self, 
                "Error", 
                "Failed to load subscription popup. Please check that subscription.py exists."
            )
            return
        
        dialog = SubscriptionPopupSample(self)
        
        if dialog.exec() == QDialog.Accepted and dialog.selected_plan:
            plan_name, price = dialog.selected_plan
            
            confirm_reply = QMessageBox.question(
                self, 
                "Confirm Plan Change",
                f"Are you sure you want to change to the <b>{plan_name}</b>?\n\n"
                f"Price: {price}\n"
                f"This will update your subscription immediately.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm_reply != QMessageBox.Yes:
                return
            
            plan_mapping = {
                "Basic Plan": "basic",
                "Premium Plan": "premium",
                "Enterprise Plan": "enterprise"
            }
            
            api_plan = plan_mapping.get(plan_name, plan_name.split()[0].lower())
            
            worker = ApiWorker(self.api_upgrade_plan, api_plan)
            worker.signals.result.connect(lambda r: self.on_plan_upgrade_response(r, plan_name))
            worker.signals.error.connect(lambda e: self.on_plan_upgrade_error(e))
            self.thread_pool.start(worker)
            
            self.upgrade_btn.setText("⏳ Processing...")
            self.upgrade_btn.setEnabled(False)
        else:
            if sound_manager:
                sound_manager.play_click()
            print("Subscription upgrade cancelled")

    def api_upgrade_plan(self, api_plan):
        """API call to upgrade plan using account_config"""
        data = {"plan": api_plan}
        print(f"Upgrading plan to: {api_plan}")
        
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.put("/api/account/subscription", data=data, timeout=10)
                print(f"Plan upgrade response status: {response.status_code}")
                return response
            except Exception as e:
                print(f"Plan upgrade API error: {e}")
                raise
        else:
            try:
                response = requests.put(
                    f"{API_BASE_URL}/api/account/subscription", 
                    headers=self.api_headers,
                    json=data,
                    timeout=10,
                    verify=False
                )
                print(f"Plan upgrade response status: {response.status_code}")
                return response
            except requests.exceptions.Timeout:
                raise Exception("Connection timeout. Please try again.")
            except requests.exceptions.ConnectionError:
                raise Exception("Unable to connect to server. Please check your internet connection.")
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

    def on_plan_upgrade_response(self, response, plan_name):
        """Handle plan upgrade response"""
        self.upgrade_btn.setText("🔄  Upgrade Plan")
        self.upgrade_btn.setEnabled(True)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"Plan upgrade response data: {response_data}")
                
                if response_data.get("success"):
                    if sound_manager:
                        sound_manager.play_success()
                    
                    if self.account_data:
                        data = response_data.get("data", {})
                        self.account_data["subscription_plan"] = data.get("plan", plan_name)
                        self.account_data["subscription_renewal"] = data.get("renewal_date", "Unknown")
                    
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"Your subscription has been successfully changed to <b>{plan_name}</b>!\n\n"
                        f"The new plan features are now active on your account."
                    )
                    
                    self.load_all_data()
                    
                else:
                    error_msg = response_data.get("error", "Failed to update subscription")
                    print(f"API error: {error_msg}")
                    if sound_manager:
                        sound_manager.play_error()
                    QMessageBox.warning(
                        self, 
                        "Error", 
                        f"Failed to update subscription:\n{error_msg}"
                    )
                    
            except Exception as e:
                print(f"Error parsing response: {e}")
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Error processing server response:\n{str(e)}"
                )
        else:
            error_text = f"API error: {response.status_code}"
            try:
                error_data = response.json()
                if error_data.get("error"):
                    error_text = error_data.get("error")
            except:
                pass
                
            print(f"{error_text}")
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(
                self, 
                "Error", 
                f"Failed to update subscription:\n{error_text}"
            )

    def on_plan_upgrade_error(self, error_msg):
        """Handle plan upgrade error"""
        print(f"Plan upgrade error: {error_msg}")
        
        self.upgrade_btn.setText("🔄  Upgrade Plan")
        self.upgrade_btn.setEnabled(True)
        
        if sound_manager:
            sound_manager.play_error()
        
        error_messages = {
            "timeout": "Connection timeout. Please check your internet connection and try again.",
            "connection": "Unable to connect to server. Please check your internet connection.",
            "json": "Server response error. Please try again later.",
        }
        
        user_message = error_messages.get("connection", f"Error: {error_msg}")
        
        QMessageBox.warning(
            self, 
            "Connection Error", 
            f"{user_message}\n\nTechnical details: {error_msg}"
        )

    def on_save_changes(self):
        """Handle save changes button click"""
        if sound_manager:
            sound_manager.play_click()
        
        settings_data = {
            "two_factor_enabled": False,
            "phone": self.phone_input.text()
        }
        
        for label_text, toggle in self.toggle_switches:
            if "Two-Factor Authentication" in label_text:
                settings_data["two_factor_enabled"] = toggle.isChecked()
        
        print(f"Saving settings: {settings_data}")
        
        worker = ApiWorker(self.api_save_settings, settings_data)
        worker.signals.result.connect(self.on_settings_save_response)
        worker.signals.error.connect(self.on_settings_save_error)
        self.thread_pool.start(worker)
        
        self.save_btn.setText("⏳ Saving...")
        self.save_btn.setEnabled(False)

    def api_save_settings(self, settings_data):
        """API call to save settings using account_config"""
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.put("/api/account/settings", data=settings_data, timeout=5)
                return response
            except Exception as e:
                print(f"Save settings API error: {e}")
                raise
        else:
            response = requests.put(f"{API_BASE_URL}/api/account/settings", 
                                   headers=self.api_headers,
                                   json=settings_data,
                                   timeout=5,
                                   verify=False)
            return response

    def on_settings_save_response(self, response):
        """Handle settings save response"""
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                self.on_save_complete()
            else:
                self.on_save_error(response_data.get("error", "Unknown error"))
        else:
            self.on_save_error(f"API error: {response.status_code}")

    def on_settings_save_error(self, error_msg):
        """Handle settings save error"""
        self.on_save_error(f"Network error: {error_msg}")

    def on_save_complete(self):
        """Handle successful save"""
        if sound_manager:
            sound_manager.play_success()
        self.save_btn.setText("✅ Saved!")
        self.save_btn.setStyleSheet("""
            QPushButton#saveBtn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
        """)
        QTimer.singleShot(2000, self.reset_save_button)

    def on_save_error(self, error_message):
        """Handle save error"""
        if sound_manager:
            sound_manager.play_error()
        self.save_btn.setText("❌ Error!")
        self.save_btn.setStyleSheet("""
            QPushButton#saveBtn {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
        """)
        QMessageBox.warning(self, "Save Error", f"Failed to save changes: {error_message}")
        QTimer.singleShot(2000, self.reset_save_button)

    def reset_save_button(self):
        """Reset save button to original state"""
        self.save_btn.setText("💾  Save Changes")
        self.save_btn.setEnabled(True)
        self.save_btn.setStyleSheet("""
            QPushButton#saveBtn {
                background: rgba(67, 97, 238, 0.9);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton#saveBtn:hover {
                background: rgba(67, 97, 238, 1);
            }
            QPushButton#saveBtn:disabled {
                background: rgba(0,0,0,0.1);
                color: rgba(0,0,0,0.3);
            }
        """)

    def show_notifications(self):
        # Notifications feature removed: no UI to show
        return

    def mark_notifications_read(self, dialog):
        # Notifications feature removed
        return

    def api_mark_notifications_read(self):
        # Notifications removed: no API call
        raise NotImplementedError("Notifications have been removed from this build")

    def on_mark_notifications_response(self, response, dialog):
        # Notifications removed: handler disabled
        return

    def on_mark_notifications_error(self, error_msg, dialog):
        # Notifications removed: handler disabled
        return

    def show_user_menu(self):
        """Show user menu"""
        if sound_manager:
            sound_manager.play_click()
        
        menu = QMenu(self)
        # Use a translucent, frameless popup so rounded corners appear smooth
        menu.setWindowFlags(menu.windowFlags() | Qt.Popup | Qt.FramelessWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)

        menu.setStyleSheet("""
            QMenu {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.08);
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 8px;
                color: #212529;
            }
            QMenu::item:selected {
                background: rgba(67, 97, 238, 0.1);
                color: #4361ee;
            }
        """)
        
        menu.addAction("👤 View Profile", lambda: self.on_nav_clicked(self.nav_buttons[0]))
        menu.addAction("⚙️ Account Settings", lambda: self.on_nav_clicked(self.nav_buttons[1]))
        menu.addSeparator()
        menu.addAction("🔒 Privacy Controls", self.show_privacy_controls)
        menu.addSeparator()
        menu.addAction("🚪 Logout", self.logout)
        
        menu.exec(self.avatar_btn.mapToGlobal(self.avatar_btn.rect().bottomLeft()))

    def show_privacy_controls(self):
        """Show privacy controls dialog"""
        if sound_manager:
            sound_manager.play_click()
        QMessageBox.information(self, "Privacy Controls", 
            "Privacy options:\n\n"
            "• Data Export\n"
            "• Account Deletion\n"
            "• Privacy Settings\n"
            "• Cookie Preferences")

    def logout(self):
        """SECURE LOGOUT - Clear all tokens and session"""
        if sound_manager:
            sound_manager.play_click()
        
        reply = QMessageBox.question(self, "Logout", 
                                   "Are you sure you want to logout?\n\n"
                                   "All session data will be cleared.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            print("\n🔐 SECURE LOGOUT: Starting secure logout process...")
            
            if sound_manager:
                sound_manager.play_logout()
            
            # Use account_config to clear all auth data (including session and CSRF)
            if ACCOUNT_CONFIG_AVAILABLE and account_config:
                account_config.clear_auth()
                print(f"Cleared account_config - USER_ID: {account_config.CURRENT_USER_ID}")
            else:
                # Fallback: clear from config
                _get_account_config(self.main_window).CURRENT_USER_ID = None
                _get_account_config(self.main_window).CURRENT_TOKEN = None
                _get_account_config(self.main_window).CURRENT_USER_DATA = None
            
            # Clear local data
            self.account_data = {}
            self.activities_data = []
            # notifications removed
            
            # Cleanup
            self.cleanup_network_reply()
            
            if hasattr(self, 'thread_pool') and self.thread_pool:
                self.thread_pool.clear()
                self.thread_pool.waitForDone(1000)
            
            print("🔐 SECURE LOGOUT: Notifying main window...")
            if self.main_window and hasattr(self.main_window, 'on_logout'):
                self.main_window.on_logout()
            elif self.main_window and hasattr(self.main_window, 'handle_logout'):
                self.main_window.handle_logout()
            
            print("🔐 SECURE LOGOUT: Emitting logout signal...")
            self.logoutRequested.emit()
            
            print("🔐 SECURE LOGOUT: Logout complete.")
        else:
            print("🔐 SECURE LOGOUT: Logout cancelled by user")

    def show_subscription_details(self):
        """Show detailed subscription information"""
        if sound_manager:
            sound_manager.play_click()
        
        if not self.account_data:
            return
        
        plan = self.account_data.get("subscription_plan", "Unknown")
        renewal = self.account_data.get("subscription_renewal", "Unknown")
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Subscription Details")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
            }
            QLabel {
                color: #212529;
                background: transparent;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #212529;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: transparent;
            }
            QTextEdit {
                color: #212529;
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 8px;
            }
            QPushButton {
                color: white;
                background-color: #4361ee;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:pressed {
                background-color: #2a46b4;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        current_group = QGroupBox("Current Plan")
        current_layout = QVBoxLayout()
        
        plan_label = QLabel(f"<h3>{plan}</h3>")
        renewal_label = QLabel(f"Renewal date: {renewal}")
        status_label = QLabel("Status: Active")
        
        current_layout.addWidget(plan_label)
        current_layout.addWidget(renewal_label)
        current_layout.addWidget(status_label)
        
        features_label = QLabel("<b>Features:</b>")
        current_layout.addWidget(features_label)
        
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setMaximumHeight(100)
        
        if "Premium" in plan:
            features = ["50GB storage", "Priority support", "Advanced analytics", "All Basic features"]
        elif "Basic" in plan:
            features = ["10GB storage", "Email support", "All Free features"]
        elif "Enterprise" in plan:
            features = ["Unlimited storage", "24/7 support", "Custom integrations", "All Premium features"]
        else:
            features = ["5GB storage", "Community support", "Basic features"]
        
        features_text.setText("\n".join([f"• {feature}" for feature in features]))
        current_layout.addWidget(features_text)
        
        current_group.setLayout(current_layout)
        
        upgrade_btn = QPushButton("🔄  Change Plan")
        upgrade_btn.clicked.connect(lambda: [dialog.accept(), self.on_upgrade_plan()])
        
        layout.addWidget(current_group)
        layout.addWidget(upgrade_btn)
        
        dialog.exec()

    def show_security_details(self):
        """Show detailed security information"""
        if sound_manager:
            sound_manager.play_click()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Security Details")
        dialog.setFixedSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
            }
            QLabel {
                color: #212529;
                background: transparent;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #212529;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: transparent;
            }
            QPushButton {
                color: white;
                background-color: #4361ee;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:pressed {
                background-color: #2a46b4;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        status_group = QGroupBox("Security Status")
        status_layout = QVBoxLayout()
        
        try:
            # Use account_config for security data
            if ACCOUNT_CONFIG_AVAILABLE and account_config:
                response = account_config.get("/api/account/security", timeout=5)
            else:
                response = requests.get(f"{API_BASE_URL}/api/account/security", headers=self.api_headers, timeout=5, verify=False)
                
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    security_data = data.get("data", {})
                    
                    items = [
                        ("Two-Factor Authentication", 
                         "Enabled" if security_data.get("two_factor_enabled") else "Disabled",
                         "✅" if security_data.get("two_factor_enabled") else "❌"),
                        ("Last Login", 
                         security_data.get("last_login", "Unknown"), 
                         "🕒"),
                        ("Login Location", 
                         security_data.get("login_location", "Unknown"), 
                         "📍"),
                        ("Unusual Activity", 
                         "No issues detected" if not security_data.get("unusual_activity") else "Potential issues",
                         "✅" if not security_data.get("unusual_activity") else "⚠️"),
                    ]
                    
                    for title, value, icon in items:
                        item_widget = self.create_security_item(title, value, icon)
                        status_layout.addWidget(item_widget)
        
        except Exception as e:
            print(f"Security details error: {e}")
        
        status_group.setLayout(status_layout)
        
        actions_group = QGroupBox("Security Actions")
        actions_layout = QVBoxLayout()
        
        change_pass_btn = QPushButton("🔑 Change Password")
        change_pass_btn.clicked.connect(self.change_password)
        
        session_btn = QPushButton("🖥️ Manage Sessions")
        session_btn.clicked.connect(self.manage_sessions)
        
        actions_layout.addWidget(change_pass_btn)
        actions_layout.addWidget(session_btn)
        actions_group.setLayout(actions_layout)
        
        layout.addWidget(status_group)
        layout.addWidget(actions_group)
        
        dialog.exec()

    def create_security_item(self, title, value, icon):
        """Create a security item widget"""
        widget = QWidget()
        widget.setFixedHeight(50)
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        
        icon_label = QLabel(icon)
        icon_label.setFixedSize(30, 30)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #212529; background: transparent;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: #6c757d; background: transparent;")
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(value_label)
        
        return widget

    def change_password(self):
        """Change password dialog"""
        if sound_manager:
            sound_manager.play_click()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Password")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
            }
            QLabel {
                color: #212529;
                background: transparent;
            }
            QLineEdit {
                color: #212529;
                background: rgba(255,255,255,0.5);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton {
                color: white;
                background-color: #4361ee;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:pressed {
                background-color: #2a46b4;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        current_pass = QLineEdit()
        current_pass.setEchoMode(QLineEdit.Password)
        new_pass = QLineEdit()
        new_pass.setEchoMode(QLineEdit.Password)
        confirm_pass = QLineEdit()
        confirm_pass.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Current Password:", current_pass)
        form_layout.addRow("New Password:", new_pass)
        form_layout.addRow("Confirm Password:", confirm_pass)
        
        requirements = QLabel("Password must be at least 8 characters long")
        requirements.setStyleSheet("color: #6c757d; font-size: 12px; background: transparent;")
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.process_password_change(
            dialog, current_pass.text(), new_pass.text(), confirm_pass.text()
        ))
        button_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(requirements)
        layout.addWidget(button_box)
        
        dialog.exec()

    def process_password_change(self, dialog, current_pass, new_pass, confirm_pass):
        """Process password change with API"""
        if new_pass != confirm_pass:
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(self, "Error", "New passwords do not match")
            return
        
        if len(new_pass) < 8:
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters long")
            return
        
        if sound_manager:
            sound_manager.play_click()
        
        worker = ApiWorker(self.api_change_password, current_pass, new_pass)
        worker.signals.result.connect(lambda r: self.on_password_change_response(r, dialog))
        worker.signals.error.connect(lambda e: self.on_password_change_error(e, dialog))
        self.thread_pool.start(worker)
        
        dialog.findChild(QDialogButtonBox).setEnabled(False)
        dialog.setWindowTitle("Processing...")

    def api_change_password(self, current_pass, new_pass):
        """API call to change password using account_config"""
        data = {
            "current_password": current_pass,
            "new_password": new_pass
        }
        
        if ACCOUNT_CONFIG_AVAILABLE and account_config:
            try:
                response = account_config.post("/api/account/change-password", data=data, timeout=5)
                return response
            except Exception as e:
                print(f"Change password API error: {e}")
                raise
        else:
            response = requests.post(f"{API_BASE_URL}/api/account/change-password", 
                                   headers=self.api_headers,
                                   json=data,
                                   timeout=5,
                                   verify=False)
            return response

    def on_password_change_response(self, response, dialog):
        """Handle password change response"""
        dialog.findChild(QDialogButtonBox).setEnabled(True)
        dialog.setWindowTitle("Change Password")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                if sound_manager:
                    sound_manager.play_success()
                dialog.accept()
                QMessageBox.information(self, "Success", "Password changed successfully")
            else:
                if sound_manager:
                    sound_manager.play_error()
                QMessageBox.warning(self, "Error", response_data.get("error", "Failed to change password"))
        else:
            if sound_manager:
                sound_manager.play_error()
            QMessageBox.warning(self, "Error", f"API error: {response.status_code}")

    def on_password_change_error(self, error_msg, dialog):
        """Handle password change error"""
        dialog.findChild(QDialogButtonBox).setEnabled(True)
        dialog.setWindowTitle("Change Password")
        if sound_manager:
            sound_manager.play_error()
        QMessageBox.warning(self, "API Error", f"Failed to change password: {error_msg}")

    def manage_sessions(self):
        """Manage active sessions"""
        if sound_manager:
            sound_manager.play_click()
        QMessageBox.information(self, "Manage Sessions", 
            "Active Sessions:\n\n"
            "• Chrome on Windows (Current)\n"
            "• Mobile App\n\n"
            "To log out from other devices, visit the security settings.")

    def view_all_activities(self):
        """View all activities"""
        if sound_manager:
            sound_manager.play_click()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("All Activities")
        dialog.setFixedSize(600, 500)
        dialog.setStyleSheet("""
            QDialog {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
            }
            QLabel {
                color: #212529;
                background: transparent;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        
        for activity in self.activities_data:
            icon = activity.get("icon", "")
            action = activity.get("action", "")
            description = activity.get("description", "")
            timestamp = activity.get("timestamp", "")
            
            time_text = self.format_relative_time(timestamp)
            
            item = self.create_activity_item(icon, action, description, time_text)
            scroll_layout.addWidget(item)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        
        dialog.exec()

    # ==================== CHANGE ROOM METHOD ====================
    def change_room(self):
        """Show teacher selection dialog to change the current room."""
        if sound_manager:
            sound_manager.play_click()
        
        if not TEACHER_SELECTOR_AVAILABLE or TeacherSelectorDialog is None:
            QMessageBox.warning(
                self, 
                "Error", 
                "Room selection is not available. Please restart the application."
            )
            return
        
        # Check if token manager is available
        if not TOKEN_MANAGER_AVAILABLE or token_manager is None:
            QMessageBox.warning(
                self, 
                "Error", 
                "Token manager is not available. Please restart the application."
            )
            return

        dialog = TeacherSelectorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            room = dialog.get_selected_room()
            if room:
                # Update token manager
                token_manager.add_room(room)
                token_manager.set_current_room(room)
                sound_manager.play_success()
                QMessageBox.information(
                    self,
                    "Room Changed",
                    f"Room changed to: {room}\n\nThe application will now restart to apply changes."
                )
                # Emit signal to restart the application
                self.roomChanged.emit()
            else:
                sound_manager.play_error()
                QMessageBox.warning(self, "Error", "No room selected.")