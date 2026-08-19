#!/usr/bin/env python3
"""
Complete Notification System with Profile Images
Handles both sound and display independently
"""

import sys
import os
import subprocess
import threading
import json
import traceback
import requests
from pathlib import Path
from PySide6.QtCore import QThread, Signal

# -------------------------------------------------------------------
# SOUND PLAYER FUNCTION
# -------------------------------------------------------------------
def play_sound_async(sound_type):
    """
    Play sound using external executable - completely independent
    Sound continues playing even after Python exits
    """
    sound_type = sound_type.lower().strip()
    
    if sound_type == "news":
        args = ["sound_player.exe", "--news"]
        print("🔊 Playing news notification sound...")
    elif sound_type == "live alert":
        args = ["sound_player.exe", "--live"]
        print("🔊 Playing live alert sound...")
    else:
        args = ["sound_player.exe", "--news"]  # Default
        print(f"🔊 Playing default sound for type '{sound_type}'...")
    
    try:
        # Check if sound player exists
        if not os.path.exists("sound_player.exe"):
            print("❌ sound_player.exe not found!")
            print("   Place sound_player.exe in the same directory")
            return False
        
        # Launch sound player completely independently
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = (
                subprocess.CREATE_NO_WINDOW |
                subprocess.DETACHED_PROCESS |
                subprocess.CREATE_NEW_PROCESS_GROUP
            )
        
        subprocess.Popen(
            args,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"✅ Sound player launched independently")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch sound player: {e}")
        return False

# -------------------------------------------------------------------
# PROFILE IMAGE LOADER THREAD
# -------------------------------------------------------------------
class ProfileImageLoader(QThread):
    loaded = Signal(str, object)  # username, QPixmap
    
    def __init__(self, username, dimension="80x80"):
        super().__init__()
        self.username = username
        self.dimension = dimension
        
    def run(self):
        try:
            # Try to load profile image from server
            profile_server_url = 'https://localhost:8443'
            url = f"{profile_server_url}/profile/{self.username}/{self.dimension}"
            
            # Disable SSL verification for development
            requests.packages.urllib3.disable_warnings()
            response = requests.get(url, timeout=5, verify=False)
            
            if response.status_code == 200:
                from PySide6.QtGui import QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    print(f"✅ Loaded profile image for {self.username}")
                    self.loaded.emit(self.username, pixmap)
                    return
            
            # If failed, emit None to use default
            print(f"⚠️ Failed to load profile image for {self.username}, using default")
            self.loaded.emit(self.username, None)
            
        except Exception as e:
            print(f"❌ Error loading profile image for {self.username}: {e}")
            self.loaded.emit(self.username, None)

# -------------------------------------------------------------------
# NOTIFICATION DISPLAY FUNCTION
# -------------------------------------------------------------------
def show_notification_display(title, description, notification_type, username=None):
    """
    Show notification display in a separate process
    """
    try:
        # Convert notification type for display
        display_type = notification_type.lower().strip()
        if display_type not in ['news', 'live alert']:
            display_type = 'news'
        
        print(f"📱 Showing notification: {title}")
        if username:
            print(f"   Username: {username}")
        
        # Build command arguments
        args = [
            sys.executable,
            __file__,  # This same file
            "--display-only",
            title,
            description,
            display_type
        ]
        
        # Add username if provided
        if username:
            args.append(username)
        
        # Launch display as separate independent process
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = (
                subprocess.CREATE_NO_WINDOW |
                subprocess.DETACHED_PROCESS |
                subprocess.CREATE_NEW_PROCESS_GROUP
            )
        
        subprocess.Popen(args, creationflags=creation_flags)
        
        print(f"✅ Display launched independently")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch display: {e}")
        return False

# -------------------------------------------------------------------
# DISPLAY CLASS (With Profile Images)
# -------------------------------------------------------------------
class NotificationDisplay:
    """Qt-based notification display with profile images"""
    
    @staticmethod
    def run_display(title, description, notification_type, username=None):
        """Run the Qt display window with profile image"""
        try:
            from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, 
                                         QVBoxLayout, QPushButton, QSizePolicy)
            from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, 
                                      QPoint, QTimer, QSize, QParallelAnimationGroup)
            from PySide6.QtGui import (QColor, QPainter, QPen, QBrush, 
                                     QPixmap, QFont, QLinearGradient, QPainterPath)
            
            print(f"🔵 NotificationDisplay: username={username}")
            
            # -------------------------------------------------------------------
            # Circular Profile Label Class
            # -------------------------------------------------------------------
            class CircularProfileLabel(QLabel):
                def __init__(self, username=None, parent=None):
                    super().__init__(parent)
                    self.setFixedSize(80, 80)
                    self.setAlignment(Qt.AlignCenter)
                    self.username = username
                    self.current_pixmap = None
                    self.loader = None
                    self.image_loaded = False
                    
                    print(f"🔄 CircularProfileLabel created for: {username}")
                    
                    # Start loading profile image
                    if username:
                        self.load_profile_image()
                    else:
                        # Default icon if no username
                        print("⚠️ No username provided, using default icon")
                        self.set_default_icon()
                
                def load_profile_image(self):
                    """Load profile image from server"""
                    print(f"📥 Loading profile image for: {self.username}")
                    self.loader = ProfileImageLoader(self.username, "80x80")
                    self.loader.loaded.connect(self.on_profile_loaded)
                    self.loader.start()
                
                def on_profile_loaded(self, username, pixmap):
                    print(f"📥 Profile loaded callback for: {username}, has_pixmap={pixmap is not None}")
                    if pixmap and not pixmap.isNull():
                        self.current_pixmap = pixmap
                        self.image_loaded = True
                        print(f"✅ Profile image loaded for {username}")
                    else:
                        print(f"⚠️ No pixmap for {username}, using default")
                        self.set_default_icon()
                    self.update()
                
                def set_default_icon(self):
                    """Set default icon based on username"""
                    print(f"🎨 Setting default icon for: {self.username}")
                    pixmap = QPixmap(80, 80)
                    pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    # Use first letter of username or default icon
                    if self.username:
                        # Generate color from username
                        import hashlib
                        hash_val = int(hashlib.md5(self.username.encode()).hexdigest()[:6], 16)
                        r = (hash_val >> 16) & 0xFF
                        g = (hash_val >> 8) & 0xFF
                        b = hash_val & 0xFF
                        # Make colors brighter
                        r = min(255, r + 100)
                        g = min(255, g + 100)
                        b = min(255, b + 100)
                        color = QColor(r, g, b)
                        letter = self.username[0].upper()
                    else:
                        color = QColor(0, 122, 204)  # Default blue
                        letter = "📢"
                    
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(0, 0, 80, 80)
                    
                    # Draw letter or icon
                    painter.setPen(QPen(Qt.white, 2))
                    if len(letter) == 1 and letter.isalpha():
                        # Draw letter
                        painter.setFont(QFont("Segoe UI", 32, QFont.Bold))
                        painter.drawText(20, 52, letter)
                    else:
                        # Draw emoji
                        painter.setFont(QFont("Segoe UI", 28))
                        painter.drawText(20, 52, letter)
                    
                    painter.end()
                    self.current_pixmap = pixmap
                    self.image_loaded = False
                
                def set_image(self, pixmap):
                    """Set image directly"""
                    if pixmap and not pixmap.isNull():
                        self.current_pixmap = pixmap
                        self.image_loaded = True
                    else:
                        self.set_default_icon()
                    self.update()
                
                def paintEvent(self, event):
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setRenderHint(QPainter.SmoothPixmapTransform)
                    
                    # Create circular clipping path for the image
                    path = QPainterPath()
                    path.addEllipse(0, 0, self.width(), self.height())
                    painter.setClipPath(path)
                    
                    if self.current_pixmap and not self.current_pixmap.isNull():
                        # Scale pixmap to fill the circle (crops if needed)
                        pixmap = self.current_pixmap.scaled(
                            self.width(), self.height(),
                            Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation
                        )
                        # Center the pixmap
                        x = (self.width() - pixmap.width()) // 2
                        y = (self.height() - pixmap.height()) // 2
                        painter.drawPixmap(x, y, pixmap)
                    else:
                        # Fallback if no image – draw a colored circle
                        painter.fillRect(self.rect(), QColor(100, 100, 100, 100))
                    
                    # Remove clip to draw border without clipping
                    painter.setClipPath(QPainterPath())
                    
                    # Draw circular border (with a nicer style)
                    painter.setPen(QPen(QColor(255, 255, 255, 200), 3))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(0, 0, self.width(), self.height())
                    
                    # Optional inner glow
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
                    painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
            
            # -------------------------------------------------------------------
            # Animated Notification Class
            # -------------------------------------------------------------------
            class AnimatedNotification(QWidget):
                def __init__(self, title, description, notification_type="news", username=None):
                    super().__init__()
                    self.title = title
                    self.description = description
                    self.notification_type = notification_type.lower()
                    self.username = username
                    self.close_anim_group = None
                    
                    print(f"🔵 AnimatedNotification created: username={username}")
                    
                    # Define color schemes based on notification type
                    self.themes = {
                        "news": {
                            "primary": QColor(0, 122, 204),
                            "secondary": QColor(86, 156, 214),
                            "background": QColor(30, 30, 46),
                            "title_color": QColor(245, 247, 250),
                            "desc_color": QColor(200, 215, 235),
                            "button_bg": QColor(66, 133, 244),
                            "button_hover": QColor(82, 149, 255),
                            "title_font": QFont("Segoe UI", 16, QFont.Bold),
                            "desc_font": QFont("Segoe UI", 12, QFont.Normal)
                        },
                        "live alert": {
                            "primary": QColor(255, 193, 7),
                            "secondary": QColor(255, 214, 102),
                            "background": QColor(40, 35, 25),
                            "title_color": QColor(255, 255, 255),
                            "desc_color": QColor(255, 235, 200),
                            "button_bg": QColor(255, 193, 7),
                            "button_hover": QColor(255, 213, 79),
                            "title_font": QFont("Segoe UI", 16, QFont.Bold),
                            "desc_font": QFont("Segoe UI", 12, QFont.Normal)
                        }
                    }
                    
                    # Default to news theme if type not found
                    if self.notification_type not in self.themes:
                        self.notification_type = "news"
                    
                    self.theme = self.themes[self.notification_type]

                    # Load background logo image if exists
                    self.background_pixmap = None
                    logo_path = "logo.png"
                    if os.path.exists(logo_path):
                        temp_pixmap = QPixmap(logo_path)
                        if not temp_pixmap.isNull():
                            self.background_pixmap = temp_pixmap

                    # Window setup
                    self.setWindowFlags(
                        Qt.FramelessWindowHint | 
                        Qt.Tool | 
                        Qt.WindowStaysOnTopHint
                    )
                    self.setAttribute(Qt.WA_TranslucentBackground)
                    self.setStyleSheet("background: transparent;")
                    
                    # Create UI
                    self.setup_ui(title, description, notification_type, username)
                    
                    # Position at bottom-right of primary screen
                    screen_geo = QApplication.primaryScreen().availableGeometry()
                    self.start_pos = QPoint(
                        screen_geo.right() - self.width() - 20,
                        screen_geo.bottom() + 20
                    )
                    self.end_pos = QPoint(
                        screen_geo.right() - self.width() - 20,
                        screen_geo.bottom() - self.height() - 20
                    )
                    
                    # Initial position off-screen
                    self.move(self.start_pos)
                    
                    # Setup animations
                    self.setup_animations()
                    
                    # Auto-close timer (10 seconds)
                    self.auto_close_timer = QTimer()
                    self.auto_close_timer.setSingleShot(True)
                    self.auto_close_timer.timeout.connect(self.close_with_animation)
                    self.auto_close_timer.start(10000)

                def setup_ui(self, title, description, notification_type, username):
                    # Fixed size
                    self.setFixedSize(480, 160)
                    
                    # Main container widget
                    self.container = QWidget(self)
                    self.container.setGeometry(0, 0, self.width(), self.height())
                    self.container.setObjectName("container")
                    
                    # Main layout
                    main_layout = QHBoxLayout(self.container)
                    main_layout.setContentsMargins(20, 20, 20, 15)
                    main_layout.setSpacing(20)
                    
                    # Left side - Profile image container
                    self.profile_container = QWidget()
                    self.profile_container.setFixedSize(90, 90)
                    self.profile_container.setObjectName("profileContainer")
                    
                    # Circular profile label (with username)
                    self.profile_label = CircularProfileLabel(username, self.profile_container)
                    self.profile_label.setGeometry(5, 5, 80, 80)
                    
                    # Right side - content area
                    content_widget = QWidget()
                    content_layout = QVBoxLayout(content_widget)
                    content_layout.setContentsMargins(0, 0, 0, 0)
                    content_layout.setSpacing(8)
                    
                    # Header with notification type and close button
                    header_widget = QWidget()
                    header_layout = QHBoxLayout(header_widget)
                    header_layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Type badge with theme colors
                    type_badge = QLabel(notification_type.upper())
                    primary_color = self.theme["primary"]
                    secondary_color = self.theme["secondary"]
                    
                    type_badge.setStyleSheet(f"""
                        QLabel {{
                            color: {secondary_color.name()};
                            font-size: 11px;
                            font-weight: bold;
                            background-color: rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.3);
                            padding: 3px 12px;
                            border-radius: 6px;
                            border: 1px solid rgba({secondary_color.red()}, {secondary_color.green()}, {secondary_color.blue()}, 0.5);
                            letter-spacing: 1px;
                        }}
                    """)
                    type_badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                    
                    # Username badge (if available)
                    if username:
                        username_badge = QLabel(f"👤 {username}")
                        username_badge.setStyleSheet(f"""
                            QLabel {{
                                color: {secondary_color.name()};
                                font-size: 11px;
                                font-weight: normal;
                                background-color: rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.15);
                                padding: 3px 10px;
                                border-radius: 6px;
                            }}
                        """)
                        header_layout.addWidget(username_badge)
                        header_layout.addSpacing(5)
                    
                    # Spacer
                    header_layout.addStretch()
                    
                    # Close button (X) with theme colors
                    self.close_button = QPushButton("✕")
                    self.close_button.setFixedSize(26, 26)
                    self.close_button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.2);
                            color: {secondary_color.name()};
                            border-radius: 13px;
                            border: none;
                            font-size: 14px;
                            font-weight: bold;
                            padding-top: 0px;
                        }}
                        QPushButton:hover {{
                            background-color: rgba({secondary_color.red()}, {secondary_color.green()}, {secondary_color.blue()}, 0.4);
                        }}
                        QPushButton:pressed {{
                            background-color: rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.6);
                        }}
                    """)
                    self.close_button.clicked.connect(self.close_with_animation)
                    
                    header_layout.addWidget(self.close_button)
                    
                    # Title label with theme-specific styling
                    self.title_label = QLabel(title)
                    self.title_label.setWordWrap(True)
                    self.title_label.setFont(self.theme["title_font"])
                    self.title_label.setStyleSheet(f"""
                        QLabel {{
                            color: {self.theme["title_color"].name()};
                            background: transparent;
                            padding: 0;
                            line-height: 1.2;
                        }}
                    """)
                    
                    # Description label with theme-specific styling
                    self.description_label = QLabel(description)
                    self.description_label.setWordWrap(True)
                    self.description_label.setFont(self.theme["desc_font"])
                    self.description_label.setStyleSheet(f"""
                        QLabel {{
                            color: {self.theme["desc_color"].name()};
                            background: transparent;
                            padding: 0;
                            line-height: 1.4;
                        }}
                    """)
                    
                    # Add widgets to layouts
                    content_layout.addWidget(header_widget)
                    content_layout.addWidget(self.title_label)
                    content_layout.addWidget(self.description_label)
                    
                    main_layout.addWidget(self.profile_container)
                    main_layout.addWidget(content_widget)
                    
                    # Apply container styles with theme colors
                    bg_color = self.theme["background"]
                    self.container.setStyleSheet(f"""
                        #container {{
                            background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.92);
                            border-radius: 15px;
                            border: 2px solid rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.3);
                        }}
                        #profileContainer {{
                            background: qradialgradient(
                                cx: 0.5, cy: 0.5, radius: 0.5,
                                fx: 0.5, fy: 0.5,
                                stop: 0 rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.4),
                                stop: 1 rgba({secondary_color.red()}, {secondary_color.green()}, {secondary_color.blue()}, 0.1)
                            );
                            border-radius: 45px;
                            border: 2px solid rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 0.5);
                        }}
                    """)

                def setup_animations(self):
                    # Show animation
                    self.show_anim = QPropertyAnimation(self, b"pos")
                    self.show_anim.setDuration(800)
                    self.show_anim.setStartValue(self.start_pos)
                    self.show_anim.setEndValue(self.end_pos)
                    self.show_anim.setEasingCurve(QEasingCurve.OutBack)

                def showEvent(self, event):
                    """Show the notification with animation"""
                    super().showEvent(event)
                    self.show_anim.start()

                def close_with_animation(self):
                    """Close notification with smooth animation"""
                    # Stop auto-close timer
                    self.auto_close_timer.stop()
                    
                    # Disable buttons to prevent double clicks
                    self.close_button.setEnabled(False)
                    
                    # Create parallel animation group for smooth close
                    self.close_anim_group = QParallelAnimationGroup()
                    
                    # Slide down animation
                    screen_geo = QApplication.primaryScreen().availableGeometry()
                    slide_anim = QPropertyAnimation(self, b"pos")
                    slide_anim.setDuration(500)
                    slide_anim.setStartValue(self.pos())
                    slide_anim.setEndValue(QPoint(
                        self.pos().x(),
                        screen_geo.bottom() + 100
                    ))
                    slide_anim.setEasingCurve(QEasingCurve.InBack)
                    
                    # Fade out animation
                    fade_anim = QPropertyAnimation(self, b"windowOpacity")
                    fade_anim.setDuration(500)
                    fade_anim.setStartValue(self.windowOpacity())
                    fade_anim.setEndValue(0.0)
                    fade_anim.setEasingCurve(QEasingCurve.InCubic)
                    
                    # Add animations to group
                    self.close_anim_group.addAnimation(slide_anim)
                    self.close_anim_group.addAnimation(fade_anim)
                    
                    # Connect finished signal to close the window
                    def on_animation_finished():
                        self.hide()
                        QTimer.singleShot(100, self.deleteLater)
                        self.close_anim_group = None
                    
                    self.close_anim_group.finished.connect(on_animation_finished)
                    
                    # Start animation
                    self.close_anim_group.start()

                def paintEvent(self, event):
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    primary_color = self.theme["primary"]
                    secondary_color = self.theme["secondary"]
                    
                    # Outer glow with theme colors
                    glow_width = 25
                    for i in range(glow_width):
                        alpha = 60 - i * (60 / glow_width)
                        glow_alpha = alpha * 0.7
                        
                        # Alternate between primary and secondary colors
                        if i % 3 == 0:
                            glow_color = QColor(primary_color.red(), primary_color.green(), primary_color.blue(), glow_alpha)
                        else:
                            glow_color = QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), glow_alpha)
                        
                        painter.setPen(QPen(glow_color, 1.5))
                        painter.drawRoundedRect(
                            i, 
                            i, 
                            self.width() - 2*i, 
                            self.height() - 2*i,
                            15, 15
                        )
                    
                    # Draw background logo behind the notification
                    if hasattr(self, 'background_pixmap') and self.background_pixmap is not None and not self.background_pixmap.isNull():
                        scaled_logo = self.background_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                        x_off = (self.width() - scaled_logo.width()) // 2
                        y_off = (self.height() - scaled_logo.height()) // 2

                        rounded_area = QPainterPath()
                        rounded_area.addRoundedRect(self.rect(), 15, 15)

                        painter.save()
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setClipPath(rounded_area)
                        painter.setOpacity(0.75)
                        painter.drawPixmap(x_off, y_off, scaled_logo)
                        painter.restore()

                    # Glass-morphism effect with theme gradient
                    painter.setPen(Qt.NoPen)
                    
                    if self.notification_type == "news":
                        gradient = QLinearGradient(0, 0, self.width(), self.height())
                        gradient.setColorAt(0, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 80))
                        gradient.setColorAt(0.5, QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), 40))
                        gradient.setColorAt(1, QColor(255, 255, 255, 20))
                    else:
                        gradient = QLinearGradient(0, 0, self.width(), self.height())
                        gradient.setColorAt(0, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 100))
                        gradient.setColorAt(0.5, QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), 60))
                        gradient.setColorAt(1, QColor(255, 255, 200, 30))
                    
                    painter.setBrush(QBrush(gradient))
                    painter.drawRoundedRect(self.rect(), 15, 15)
            
            # Run the Qt application
            app = QApplication([])
            notification = AnimatedNotification(title, description, notification_type, username)
            notification.show()
            app.exec()
            
            return True
            
        except ImportError as e:
            print(f"❌ PySide6 not installed: {e}")
            print("   Install with: pip install PySide6")
            return False
        except Exception as e:
            print(f"❌ Display error: {e}")
            traceback.print_exc()
            return False

# -------------------------------------------------------------------
# MAIN NOTIFICATION FUNCTION
# -------------------------------------------------------------------
def show_notification(title, description, notification_type="news", username=None):
    """
    Main function to show notification with sound and display
    Returns immediately - all components work independently
    """
    print(f"\n🔔 NOTIFICATION: {notification_type.upper()}")
    print(f"   Title: {title}")
    print(f"   Description: {description}")
    if username:
        print(f"   👤 User: {username}")
    
    # Play sound in background (completely independent)
    sound_thread = threading.Thread(
        target=play_sound_async,
        args=(notification_type,),
        daemon=True
    )
    sound_thread.start()
    
    # Show display (separate process)
    display_success = show_notification_display(title, description, notification_type, username)
    
    return display_success

def show_notification_from_json(notification_json):
    """
    Show notification from JSON string
    """
    try:
        data = json.loads(notification_json)
        title = data.get('title', 'Notification')
        description = data.get('description', '')
        notification_type = data.get('type', 'news')
        username = data.get('username', None)
        
        return show_notification(title, description, notification_type, username)
    except json.JSONDecodeError:
        return show_notification("Notification", notification_json, "news")

# -------------------------------------------------------------------
# CLASS INTERFACE FOR IMPORTING
# -------------------------------------------------------------------
class NotificationSystem:
    """
    Class interface for importing as module
    """
    
    @staticmethod
    def show(title, description, notification_type="news", username=None):
        """Show notification - module interface"""
        return show_notification(title, description, notification_type, username)
    
    @staticmethod
    def show_from_json(json_string):
        """Show notification from JSON - module interface"""
        return show_notification_from_json(json_string)
    
    @staticmethod
    def show_notification(title, description, notification_type="news", username=None):
        """Alias for show() - matches the method name used by backend.py"""
        return show_notification(title, description, notification_type, username)

# Global instance for easy import
notification = NotificationSystem()

# -------------------------------------------------------------------
# EXPORT FOR BACKEND IMPORT
# -------------------------------------------------------------------
notification_system = NotificationSystem()

# -------------------------------------------------------------------
# COMMAND LINE INTERFACE
# -------------------------------------------------------------------
def main():
    """
    Command line interface
    """
    # Check if this is a display-only call
    if len(sys.argv) > 1 and sys.argv[1] == "--display-only":
        # Run display only (called from show_notification_display)
        if len(sys.argv) >= 5:
            username = None
            if len(sys.argv) >= 6:
                username = sys.argv[5]
                print(f"📥 Display-only with username: {username}")
            NotificationDisplay.run_display(sys.argv[2], sys.argv[3], sys.argv[4], username)
        return
    
    # Normal CLI mode
    print("📢 Notification System v2.0 (Profile Images)")
    print("=" * 50)
    
    if len(sys.argv) < 4:
        print("\nUsage:")
        print('  python notification.py "Title" "Description" "type" [username]')
        print('  python notification.py \'{"title":"Test","description":"Hello","type":"news","username":"john"}\'')
        print("\nTypes: 'news' or 'live alert'")
        print("\nExamples:")
        print('  python notification.py "Update" "System update available" "news"')
        print('  python notification.py "ALERT" "Emergency situation" "live alert"')
        print('  python notification.py "Message" "John sent you a message" "news" "john"')
        print('  python notification.py \'{"title":"Test","description":"Message","type":"live alert","username":"alice"}\'')
        print("\nRequired files in same directory:")
        print('  - sound_player.exe (for sound)')
        print('  - news.wav (news sound)')
        print('  - live.wav (live alert sound)')
        print('  - logo.png (optional background logo)')
        print('  - PySide6 installed (pip install PySide6)')
        return
    
    if len(sys.argv) == 2 and sys.argv[1].startswith('{'):
        # JSON mode
        show_notification_from_json(sys.argv[1])
    else:
        # Regular mode
        title = sys.argv[1]
        description = sys.argv[2]
        notification_type = sys.argv[3]
        username = sys.argv[4] if len(sys.argv) >= 5 else None
        show_notification(title, description, notification_type, username)
    
    print("\n✅ Notification sent. Components are running independently.")
    print("   Python process can exit now.")

# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()