# TeacherSelectionWindow.py
import json
from urllib.parse import urljoin

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtSvg import QSvgRenderer

import config

# Get API base URL from config and ensure it ends with /api
API_BASE_URL = config.API_BASE_URL.rstrip('/')
if not API_BASE_URL.endswith('/api'):
    API_BASE_URL = API_BASE_URL + '/api'
print(f"🔵 TeacherSelectionWindow - API_BASE_URL: {API_BASE_URL}")

# Derive images base URL (remove /api from the end)
if API_BASE_URL.endswith('/api'):
    IMAGES_BASE_URL = API_BASE_URL[:-4]  # Remove '/api'
else:
    IMAGES_BASE_URL = API_BASE_URL
print(f"🔵 TeacherSelectionWindow - IMAGES_BASE_URL: {IMAGES_BASE_URL}")


# ------------------------------------------------------------
# Teacher Pricing Dialog
# ------------------------------------------------------------
class TeacherPricingDialog(QDialog):
    def __init__(self, teacher_name, teacher_data, theme_color, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{teacher_name} - Pricing & Availability")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        # Set dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: white;
                border-radius: 20px;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {theme_color}40;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {theme_color};
            }}
            QTableWidget {{
                border: 1px solid {theme_color}30;
                border-radius: 8px;
                gridline-color: {theme_color}20;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {theme_color}20;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: {theme_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header with teacher name and rating
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(teacher_name)
        name_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {theme_color};
        """)
        
        rating_label = QLabel(f"★ {teacher_data.get('rating', 'N/A')} ({teacher_data.get('total_reviews', 0)} reviews)")
        rating_label.setStyleSheet("""
            font-size: 16px;
            color: #666;
            padding: 5px 10px;
            background-color: #f8f9fa;
            border-radius: 15px;
        """)
        
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(rating_label)
        
        layout.addWidget(header_widget)
        
        # Tab widget for organized information
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                background: #f8f9fa;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 3px solid #0d6efd;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e9ecef;
            }
        """)
        
        # Tab 1: Basic Info & Rates
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Rate card
        rate_group = QGroupBox("Hourly Rate")
        rate_layout = QHBoxLayout(rate_group)
        
        rate_value = QLabel(f"{teacher_data.get('currency', 'USD')} {teacher_data.get('hourly_rate', 0):.2f}")
        rate_value.setStyleSheet(f"""
            font-size: 36px;
            font-weight: bold;
            color: {theme_color};
            padding: 10px;
        """)
        
        per_hour = QLabel("/hour")
        per_hour.setStyleSheet("font-size: 18px; color: #666;")
        
        rate_layout.addWidget(rate_value)
        rate_layout.addWidget(per_hour)
        rate_layout.addStretch()
        
        # Experience
        exp_label = QLabel(f"🎓 {teacher_data.get('experience_years', 0)} years of experience")
        exp_label.setStyleSheet("font-size: 16px; padding: 5px;")
        
        next_available = QLabel(f"📅 Next available: {teacher_data.get('next_available', 'Soon')}")
        next_available.setStyleSheet(f"""
            font-size: 16px;
            padding: 5px;
            color: {theme_color};
            font-weight: bold;
        """)
        
        basic_layout.addWidget(rate_group)
        basic_layout.addWidget(exp_label)
        basic_layout.addWidget(next_available)
        basic_layout.addStretch()
        
        # Tab 2: Package Deals
        packages_tab = QWidget()
        packages_layout = QVBoxLayout(packages_tab)
        
        packages_table = QTableWidget()
        packages_table.setColumnCount(5)
        packages_table.setHorizontalHeaderLabels(["Package", "Hours", "Price", "Savings", "Description"])
        packages_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        
        packages = teacher_data.get('package_deals', [])
        packages_table.setRowCount(len(packages))
        
        for i, package in enumerate(packages):
            packages_table.setItem(i, 0, QTableWidgetItem(package.get('name', '')))
            packages_table.setItem(i, 1, QTableWidgetItem(str(package.get('hours', 0))))
            packages_table.setItem(i, 2, QTableWidgetItem(f"${package.get('price', 0):.2f}"))
            packages_table.setItem(i, 3, QTableWidgetItem(f"${package.get('savings', 0):.2f}"))
            packages_table.setItem(i, 4, QTableWidgetItem(package.get('description', '')))
            
            # Color the savings cell
            if package.get('savings', 0) > 0:
                packages_table.item(i, 3).setForeground(QColor("#28a745"))
                packages_table.item(i, 3).setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        packages_table.resizeColumnsToContents()
        packages_layout.addWidget(packages_table)
        
        # Tab 3: Availability
        availability_tab = QWidget()
        availability_layout = QVBoxLayout(availability_tab)
        
        avail_group = QGroupBox("Available Time Slots")
        avail_layout = QVBoxLayout(avail_group)
        
        for slot in teacher_data.get('available_hours', []):
            slot_label = QLabel(f"• {slot}")
            slot_label.setStyleSheet("font-size: 14px; padding: 5px;")
            avail_layout.addWidget(slot_label)
        
        availability_layout.addWidget(avail_group)
        
        specialties_label = QLabel(f"Specialties: {', '.join(teacher_data.get('specialties', []))}")
        specialties_label.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 8px;
            margin-top: 10px;
        """)
        specialties_label.setWordWrap(True)
        availability_layout.addWidget(specialties_label)
        availability_layout.addStretch()
        
        # Add tabs
        tabs.addTab(basic_tab, "💰 Rates")
        tabs.addTab(packages_tab, "📦 Packages")
        tabs.addTab(availability_tab, "📅 Availability")
        
        layout.addWidget(tabs)
        
        # Action buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Style the OK button
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Book Now")
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme_color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {QColor(theme_color).darker(110).name()};
            }}
        """)
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout.addWidget(button_box)


# ------------------------------------------------------------
# Teacher Card
# ------------------------------------------------------------
class TeacherCard(QFrame):
    selected = Signal(str)  # emits teacher_id when "Select" is clicked
    pricing_requested = Signal(dict)
    
    def __init__(self, teacher_data, network_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("TeacherCard")
        self.setFixedWidth(560)
        self.setContentsMargins(0, 0, 0, 0)
        
        # Store data
        self.teacher_data = teacher_data
        self.teacher_id = teacher_data["id"]
        self.name = teacher_data["name"]
        self.description = teacher_data["description"]
        self.skills = teacher_data["skills"]
        self.theme_color = QColor(teacher_data["theme_color"])
        self.hero_text = teacher_data.get("hero_text", "🎨 Art Studio")
        self.hero_image_url = teacher_data.get("hero_image")
        self.profile_image_url = teacher_data.get("profile_image")
        self.network_manager = network_manager
        
        # Loading state for pricing
        self.loading_pricing = False
        
        # Card styling
        self.setStyleSheet("""
            #TeacherCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #ffffff, stop:1 #f8faff);
                border-radius: 36px;
                border: 1px solid rgba(13, 110, 253, 0.1);
            }
        """)

        # Colored stripe
        self.stripe = QFrame(self)
        self.stripe.setFixedHeight(8)
        self.stripe.setStyleSheet(f"background-color: {self.theme_color.name()}; border-top-left-radius: 36px; border-top-right-radius: 36px;")

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(13, 110, 253, 30))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Hero image label
        self.hero_label = QLabel()
        self.hero_label.setFixedHeight(200)
        self.hero_label.setAlignment(Qt.AlignCenter)
        self.hero_label.setText("Loading...")
        self.hero_label.setStyleSheet(f"""
            background-color: {self.theme_color.lighter(180).name()};
            border-radius: 24px;
            border: 1px solid {self.theme_color.name()}40;
            color: {self.theme_color.darker(150).name()};
            font-size: 24px;
            font-weight: bold;
        """)
        self.hero_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        main_layout.addWidget(self.hero_label)

        # Profile picture label
        self.profile_label = QLabel(self)
        self.profile_label.setFixedSize(96, 96)
        self.profile_label.setAlignment(Qt.AlignCenter)
        self.profile_label.setText("👤")
        self.profile_label.setStyleSheet(f"""
            background-color: {self.theme_color.name()};
            border: 3px solid white;
            border-radius: 48px;
            color: white;
            font-size: 48px;
            font-weight: bold;
        """)
        self.profile_label.raise_()

        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 40, 28, 30)
        content_layout.setSpacing(0)

        # Name label (will be positioned later)
        self.name_label = QLabel(self)
        self.name_label.setText(self.name)
        self.name_label.setStyleSheet("""
            font-size: 2.1rem;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        self.name_label.setFont(QFont("Arial", 33, QFont.Weight.Bold))
        self.name_label.setFixedWidth(400)
        self.name_label.raise_()

        # Description
        desc = QLabel(self.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 1rem; color: #495867; line-height: 1.6; background: transparent;")
        desc.setFont(QFont("Arial", 12))
        content_layout.addWidget(desc)
        content_layout.addSpacing(16)

        # Skills section
        skill_section = self.create_skill_section()
        content_layout.addWidget(skill_section)
        content_layout.addSpacing(16)

        # Buttons
        buttons_widget = self.create_buttons()
        content_layout.addWidget(buttons_widget)

        main_layout.addWidget(content_widget)

    def create_skill_section(self):
        section = QWidget()
        section.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(section)
        layout.setSpacing(16)

        def skill_row(name, percent):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            label = QLabel(name)
            label.setStyleSheet(f"font-size: 1rem; font-weight: 600; color: {self.theme_color.name()}; background: transparent;")
            label.setFixedWidth(90)

            # Simple progress bar
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(percent)
            progress.setTextVisible(False)
            progress.setFixedHeight(14)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #e9ecef;
                    border-radius: 7px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                stop:0 {self.theme_color.name()}, stop:1 {self.theme_color.darker(110).name()});
                    border-radius: 7px;
                }}
            """)

            percent_label = QLabel(f"{percent}%")
            percent_label.setStyleSheet(f"""
                font-size: 1.1rem; font-weight: 700; color: {self.theme_color.name()};
                background: white; padding: 4px 8px; border-radius: 12px;
                border: 1px solid {self.theme_color.name()}20;
            """)
            percent_label.setFixedWidth(60)
            percent_label.setAlignment(Qt.AlignCenter)

            row_layout.addWidget(label)
            row_layout.addWidget(progress, 1)
            row_layout.addWidget(percent_label)
            return row

        layout.addWidget(skill_row("Oil", self.skills["oil"]))
        layout.addWidget(skill_row("Sketch", self.skills["sketch"]))
        layout.addWidget(skill_row("Composition", self.skills["composition"]))
        return section

    def create_buttons(self):
        # SVG icons
        preview_svg = '''<svg xmlns="https://www.w3.org/2000/svg" width="20" height="20" fill="#0d6efd" viewBox="0 0 16 16">
            <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
            <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
        </svg>'''
        message_svg = '''<svg xmlns="https://www.w3.org/2000/svg" width="20" height="20" fill="#0d6efd" viewBox="0 0 16 16">
            <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
        </svg>'''
        select_svg = '''<svg xmlns="https://www.w3.org/2000/svg" width="20" height="20" fill="white" viewBox="0 0 16 16">
            <path d="M2.5 8a5.5 5.5 0 0 1 8.25-4.764.5.5 0 0 0 .5-.866A6.5 6.5 0 1 0 14.5 8a.5.5 0 0 0-1 0 5.5 5.5 0 1 1-11 0z"/>
            <path d="M15.354 3.354a.5.5 0 0 0-.708-.708L8 9.293 5.354 6.646a.5.5 0 1 0-.708.708l3 3a.5.5 0 0 0 .708 0l7-7z"/>
        </svg>'''

        def create_svg_icon(svg_string):
            renderer = QSvgRenderer()
            renderer.load(QByteArray(svg_string.encode()))
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)

        outline_style = f"""
            QPushButton {{
                background: white;
                border: 2px solid {self.theme_color.name()};
                color: {self.theme_color.name()};
                border-radius: 16px;
                padding: 16px 24px;
                font-weight: 600;
                font-size: 1.1rem;
                letter-spacing: 0.3px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {self.theme_color.lighter(190).name()};
                border-color: {self.theme_color.darker(110).name()};
                color: {self.theme_color.darker(110).name()};
            }}
            QPushButton:pressed {{
                background: {self.theme_color.name()}20;
            }}
            QPushButton:disabled {{
                opacity: 0.6;
            }}
        """
        primary_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {self.theme_color.name()}, stop:1 {self.theme_color.darker(110).name()});
                border: none;
                border-radius: 16px;
                padding: 16px 24px;
                font-weight: 600;
                font-size: 1.1rem;
                letter-spacing: 0.3px;
                color: white;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {self.theme_color.darker(110).name()}, stop:1 {self.theme_color.darker(120).name()});
            }}
            QPushButton:pressed {{
                background: {self.theme_color.darker(130).name()};
            }}
            QPushButton:disabled {{
                opacity: 0.6;
            }}
        """

        preview_btn = QPushButton(" Preview")
        preview_btn.setIcon(create_svg_icon(preview_svg))
        preview_btn.setIconSize(QSize(20, 20))
        preview_btn.setStyleSheet(outline_style)
        preview_btn.clicked.connect(self.on_pricing_clicked)

        message_btn = QPushButton(" Message")
        message_btn.setIcon(create_svg_icon(message_svg))
        message_btn.setIconSize(QSize(20, 20))
        message_btn.setStyleSheet(outline_style)

        self.select_btn = QPushButton(" Select")
        self.select_btn.setIcon(create_svg_icon(select_svg))
        self.select_btn.setIconSize(QSize(20, 20))
        self.select_btn.setStyleSheet(primary_style)
        self.select_btn.clicked.connect(self.on_select_clicked)

        for btn in (preview_btn, message_btn, self.select_btn):
            btn.setMinimumWidth(140)

        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(preview_btn)
        layout.addWidget(message_btn)
        layout.addWidget(self.select_btn)
        return widget

    def on_select_clicked(self):
        """Handle select button click - emit teacher_id for selection"""
        if self.loading_pricing:
            return
        self.selected.emit(self.teacher_id)

    def on_pricing_clicked(self):
        """Handle preview button click - request pricing data"""
        if self.loading_pricing:
            return
            
        self.loading_pricing = True
        self.select_btn.setEnabled(False)
        self.select_btn.setText(" Loading...")
        
        # Emit signal to request pricing
        self.pricing_requested.emit({
            'teacher_id': self.teacher_id,
            'teacher_name': self.name,
            'theme_color': self.theme_color.name(),
            'card': self
        })

    def pricing_loaded(self, pricing_data):
        """Called when pricing data is received"""
        self.loading_pricing = False
        self.select_btn.setEnabled(True)
        self.select_btn.setText(" Select")
        
        # Show pricing dialog
        dialog = TeacherPricingDialog(
            self.name, 
            pricing_data, 
            self.theme_color.name(),
            self.window()
        )
        dialog.exec()

    def pricing_error(self, error_message):
        """Called when pricing request fails"""
        self.loading_pricing = False
        self.select_btn.setEnabled(True)
        self.select_btn.setText(" Select")
        
        QMessageBox.warning(
            self.window(),
            "Error",
            f"Failed to load pricing information: {error_message}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_profile_geometry()
        self.stripe.setGeometry(0, 0, self.width(), 8)

    def update_profile_geometry(self):
        if not self.hero_label.geometry().isValid():
            return
        hero_left = self.hero_label.x()
        hero_top = self.hero_label.y()
        hero_bottom = hero_top + self.hero_label.height()
        profile_left = hero_left + 28
        profile_top = hero_bottom - 58
        self.profile_label.setGeometry(profile_left, profile_top, 96, 96)
        name_left = profile_left + 96 + 20
        name_top = profile_top - 15
        self.name_label.setGeometry(name_left, name_top, 400, 50)

    def set_hero_image(self, pixmap):
        if not pixmap.isNull():
            scaled = pixmap.scaled(self.hero_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.hero_label.setPixmap(scaled)
            self.hero_label.setText("")

    def set_profile_image(self, pixmap):
        if not pixmap.isNull():
            # Create circular mask
            rounded = QPixmap(96, 96)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, 96, 96)
            painter.setClipPath(path)
            scaled = pixmap.scaled(96, 96, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled)
            painter.end()
            self.profile_label.setPixmap(rounded)
            self.profile_label.setText("")


# ------------------------------------------------------------
# Teacher Selection Window
# ------------------------------------------------------------
class TeacherSelectionWindow(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("اختر معلمك (Choose Your Teacher)")
        self.setMinimumSize(1200, 800)
        self.setModal(True)

        print(f"🔵 TeacherSelectionWindow initialized with user_id: {user_id}")
        print(f"🔵 API_BASE_URL: {API_BASE_URL}")
        print(f"🔵 IMAGES_BASE_URL: {IMAGES_BASE_URL}")

        # Network manager
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_request_finished)
        
        # Store pending pricing requests
        self.pricing_requests = {}  # QNetworkReply -> card
        self.cards = []  # Store card references

        # UI setup
        self.setup_ui()

        # Start fetching teachers
        self.fetch_teachers()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("اختر معلمك المفضل لبدء رحلة التعلم")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; padding: 20px;")
        main_layout.addWidget(header)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: #f8f9fa; }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #e9ecef; width: 10px; height: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #0d6efd; border-radius: 5px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #0b5ed7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none; background: none; height: 0; width: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignCenter)

        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area)

        # Bottom button: Skip
        self.skip_btn = QPushButton("تخطي (Skip)")
        self.skip_btn.clicked.connect(self.reject)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 10px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        main_layout.addWidget(self.skip_btn, alignment=Qt.AlignCenter)

    def fetch_teachers(self):
        """Fetch teachers from the server"""
        # Construct URL with /api prefix
        url = QUrl(f"{API_BASE_URL}/teachers")
        print(f"🔵 Fetching teachers from: {url.toString()}")
        
        request = QNetworkRequest(url)
        request.setTransferTimeout(10000)  # 10 second timeout
        self.network_manager.get(request)

    def on_request_finished(self, reply):
        url = reply.url().toString()
        print(f"🔵 Request finished for URL: {url}")
        
        if "teachers" in url:
            self.handle_teachers_reply(reply)
        elif "pricing" in url:
            self.handle_pricing_reply(reply)
        elif "images" in url:
            self.handle_image_reply(reply)
        else:
            reply.deleteLater()

    def handle_teachers_reply(self, reply):
        if reply.error() != QNetworkReply.NoError:
            error_string = reply.errorString()
            print(f"❌ Error fetching teachers: {error_string}")
            print(f"❌ URL: {reply.url().toString()}")
            
            QMessageBox.critical(
                self,
                "خطأ في الاتصال",
                f"فشل تحميل قائمة المعلمين: {error_string}\n\n"
                f"تأكد من تشغيل الخادم على {API_BASE_URL}"
            )
            reply.deleteLater()
            return

        data = reply.readAll()
        reply.deleteLater()

        try:
            response = json.loads(data.data().decode())
            print(f"✅ Teachers response received")
            
            # Handle both wrapped and unwrapped responses
            if isinstance(response, dict) and "data" in response:
                teachers = response["data"]
            elif isinstance(response, list):
                teachers = response
            else:
                teachers = []
                
            print(f"✅ Loaded {len(teachers)} teachers")
            
            if len(teachers) == 0:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    "لا يوجد معلمين متاحين حالياً"
                )
                
        except Exception as e:
            print(f"❌ JSON parse error: {e}")
            QMessageBox.critical(self, "خطأ", f"خطأ في قراءة بيانات المعلمين: {e}")
            return

        # Clear any existing cards
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.cards.clear()

        # Create cards for each teacher
        for i, teacher_data in enumerate(teachers):
            card = TeacherCard(teacher_data, self.network_manager, self)
            card.selected.connect(self.on_teacher_selected)
            card.pricing_requested.connect(self.on_pricing_requested)
            self.cards.append(card)
            
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(card, row, col)

            # Start downloading images
            if teacher_data.get("hero_image"):
                self.download_image(card, teacher_data["hero_image"], "hero")
            if teacher_data.get("profile_image"):
                self.download_image(card, teacher_data["profile_image"], "profile")

    def on_pricing_requested(self, request_data):
        teacher_id = request_data['teacher_id']
        card = request_data['card']
        
        # Construct URL with /api prefix
        url = QUrl(f"{API_BASE_URL}/teacher/{teacher_id}/pricing")
        print(f"🔵 Fetching pricing for teacher {teacher_id} from: {url.toString()}")
        
        request = QNetworkRequest(url)
        reply = self.network_manager.get(request)
        
        # Store mapping
        self.pricing_requests[reply] = card

    def handle_pricing_reply(self, reply):
        card = self.pricing_requests.pop(reply, None)
        
        if not card:
            reply.deleteLater()
            return
            
        if reply.error() != QNetworkReply.NoError:
            error_msg = reply.errorString()
            print(f"❌ Error fetching pricing: {error_msg}")
            card.pricing_error(error_msg)
            reply.deleteLater()
            return

        data = reply.readAll()
        reply.deleteLater()

        try:
            response = json.loads(data.data().decode())
            # Handle both wrapped and unwrapped responses
            if isinstance(response, dict) and "data" in response:
                pricing_data = response["data"]
            else:
                pricing_data = response
            print(f"✅ Pricing data received for teacher {card.teacher_id}")
            card.pricing_loaded(pricing_data)
        except Exception as e:
            print(f"❌ Pricing JSON parse error: {e}")
            card.pricing_error(str(e))

    def download_image(self, card, image_filename, image_type):
        # Construct URL for images
        url = QUrl(f"{IMAGES_BASE_URL}/images/{image_filename}")
        print(f"🔵 Downloading {image_type} image from: {url.toString()}")
        
        request = QNetworkRequest(url)
        reply = self.network_manager.get(request)
        
        # Store with metadata
        reply.setProperty("card", card)
        reply.setProperty("image_type", image_type)

    def handle_image_reply(self, reply):
        card = reply.property("card")
        image_type = reply.property("image_type")
        
        if not card or not image_type:
            reply.deleteLater()
            return
            
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            
            if image_type == "hero":
                card.set_hero_image(pixmap)
            elif image_type == "profile":
                card.set_profile_image(pixmap)
        else:
            print(f"⚠️ Error downloading {image_type}: {reply.errorString()}")
            
        reply.deleteLater()

    def on_teacher_selected(self, teacher_id):
        """User clicked Select on a card"""
        print(f"🔵 Teacher selected: {teacher_id}")
        
        # Disable further interaction while saving
        self.setEnabled(False)

        # Construct URL for saving selection with /api prefix
        url = QUrl(f"{API_BASE_URL}/user/select-teacher")
        print(f"🔵 Saving teacher selection to: {url.toString()}")
        
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setRawHeader(b"X-User-ID", self.user_id.encode())

        data = json.dumps({"teacher_id": teacher_id}).encode()
        reply = self.network_manager.post(request, data)
        reply.finished.connect(lambda: self.on_selection_reply(reply, teacher_id))

    def on_selection_reply(self, reply, teacher_id):
        if reply.error() == QNetworkReply.NoError:
            print(f"✅ Teacher selection saved successfully")
            self.accept()  # Close dialog with success
        else:
            error_msg = reply.errorString()
            print(f"❌ Failed to save teacher selection: {error_msg}")
            QMessageBox.warning(
                self,
                "خطأ",
                f"فشل حفظ اختيار المعلم: {error_msg}"
            )
            self.setEnabled(True)  # Re-enable
        reply.deleteLater()