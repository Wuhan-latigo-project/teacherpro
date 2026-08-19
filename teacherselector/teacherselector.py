import sys
import json
import io
import config
import os
import ssl
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QSize, QByteArray, QUrl
from PySide6.QtGui import QPixmap, QFont, QPainter, QIcon, QColor, QPainterPath, QImage, QPen, QMovie, QPalette, QBrush, QFontDatabase, QLinearGradient, QRadialGradient, QGradient
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy, QListWidget,
    QListWidgetItem, QSplitter, QAbstractItemView, QLineEdit,
    QMessageBox, QFileDialog, QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtSvg import QSvgRenderer

# Disable SSL certificate verification warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_requests_session():
    session = requests.Session()
    session.verify = False
    return session

def create_ssl_config():
    from PySide6.QtNetwork import QSslConfiguration, QSslSocket
    ssl_config = QSslConfiguration.defaultConfiguration()
    ssl_config.setPeerVerifyMode(QSslSocket.PeerVerifyMode(0))
    return ssl_config

try:
    from SoundManager import sound_manager
except ImportError:
    class DummySoundManager:
        def play_click(self): pass
        def play_success(self): pass
        def play_upload(self): pass
    sound_manager = DummySoundManager()


# ==================== Custom High-Quality GIF Label ====================
class QualityGifLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie = None
        self.current_pixmap = None
        self.setAlignment(Qt.AlignCenter)
        
    def setMovie(self, movie):
        if self.movie:
            try:
                self.movie.frameChanged.disconnect(self.update_frame)
            except:
                pass
        super().setMovie(movie)
        self.movie = movie
        if self.movie:
            self.movie.frameChanged.connect(self.update_frame)
            self.movie.start()
            self.update_frame()
        
    def update_frame(self):
        if self.movie:
            self.current_pixmap = self.movie.currentPixmap()
            self.update()
            
    def paintEvent(self, event):
        if self.current_pixmap and not self.current_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            scaled_pixmap = self.current_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            super().paintEvent(event)


# ==================== Circular Profile Label (Ocean Theme) ====================
class CircularProfileLabel(QLabel):
    def __init__(self, username, server_url=config.API_BASE_URL, size=40, parent=None):
        super().__init__(parent)
        self.username = username
        self.server_url = server_url.rstrip('/')
        self.size = size
        self.pixmap = None
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255,255,255,0.1);
                border-radius: {size//2}px;
                border: 1px solid rgba(245,166,35,0.3);
            }}
        """)
        self.network_manager = QNetworkAccessManager()
        self.ssl_config = create_ssl_config()
        self.load_avatar()
    
    def load_avatar(self):
        request_size = self.size * 2
        url = f"{self.server_url}/profile/{self.username}/{request_size}x{request_size}"
        request = QNetworkRequest(QUrl(url))
        request.setSslConfiguration(self.ssl_config)
        self.reply = self.network_manager.get(request)
        self.reply.finished.connect(self.on_avatar_loaded)
    
    def on_avatar_loaded(self):
        if self.reply and self.reply.error() == QNetworkReply.NoError:
            pixmap = QPixmap()
            data = self.reply.readAll()
            if pixmap.loadFromData(data) and not pixmap.isNull():
                self.pixmap = self.create_circular_pixmap(pixmap, self.size)
                self.setPixmap(self.pixmap)
                self.setStyleSheet(f"background-color: transparent; border-radius: {self.size//2}px; border: 1px solid rgba(245,166,35,0.5);")
        self.cleanup()
    
    def create_circular_pixmap(self, source_pixmap, target_size):
        supersample_factor = 2
        high_res_size = target_size * supersample_factor
        high_res_pixmap = QPixmap(high_res_size, high_res_size)
        high_res_pixmap.fill(Qt.transparent)
        painter = QPainter(high_res_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        scaled = source_pixmap.scaled(
            high_res_size, high_res_size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        x_offset = (high_res_size - scaled.width()) // 2
        y_offset = (high_res_size - scaled.height()) // 2
        mask_path = QPainterPath()
        mask_path.addEllipse(0, 0, high_res_size, high_res_size)
        painter.setClipPath(mask_path)
        painter.drawPixmap(x_offset, y_offset, scaled)
        painter.end()
        result = high_res_pixmap.scaled(
            target_size, target_size,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )
        return result
    
    def cleanup(self):
        if self.reply:
            self.reply.deleteLater()
            self.reply = None
        if self.network_manager:
            self.network_manager.deleteLater()
            self.network_manager = None
    
    def set_placeholder(self, initial=""):
        self.setText(initial or "?")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255,255,255,0.1);
                border-radius: {self.size//2}px;
                font-size: {self.size//2}px;
                color: #7ab8d4;
                border: 1px solid rgba(245,166,35,0.3);
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


# ==================== Token Helpers ====================
def get_token():
    try:
        from token_manager import get_token as tm_get_token
        return tm_get_token()
    except ImportError:
        pass
    try:
        account_dir = os.path.join(os.path.dirname(__file__), "account")
        token_path = os.path.join(account_dir, "token.txt")
        if os.path.exists(token_path):
            with open(token_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except:
        pass
    return None

def get_user_id():
    try:
        from token_manager import get_user_id as tm_get_user_id
        return tm_get_user_id()
    except ImportError:
        pass
    try:
        account_dir = os.path.join(os.path.dirname(__file__), "account")
        user_data_path = os.path.join(account_dir, "user_data.json")
        if os.path.exists(user_data_path):
            with open(user_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('user_id') or data.get('user_data', {}).get('id')
    except:
        pass
    return None


# ==================== SVG to Pixmap ====================
def svg_to_pixmap(svg_string, size, color=None):
    renderer = QSvgRenderer()
    svg_data = QByteArray(svg_string.encode())
    if not renderer.load(svg_data):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        return pixmap
    scale_factor = 2
    high_res_size = size * scale_factor
    pixmap = QPixmap(high_res_size, high_res_size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    if color:
        colored_pixmap = QPixmap(high_res_size, high_res_size)
        colored_pixmap.fill(Qt.transparent)
        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        pixmap = colored_pixmap
    final_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return final_pixmap


# ==================== SVG Icons ====================
SEARCH_SVG = '''<svg xmlns="https://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
</svg>'''

QR_SVG = '''<svg xmlns="https://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 3.75 9.375v-4.5ZM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 0 1-1.125-1.125v-4.5ZM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 13.5 9.375v-4.5Z" />
  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 6.75h.75v.75h-.75v-.75ZM6.75 16.5h.75v.75h-.75v-.75ZM16.5 6.75h.75v.75h-.75v-.75ZM13.5 13.5h.75v.75h-.75v-.75ZM13.5 19.5h.75v.75h-.75v-.75ZM19.5 13.5h.75v.75h-.75v-.75ZM19.5 19.5h.75v.75h-.75v-.75ZM16.5 16.5h.75v.75h-.75v-.75Z" />
</svg>'''

STAR_SVG = '''<svg xmlns="https://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
  <path fill-rule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.006 5.404.434c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.434 2.082-5.005Z" clip-rule="evenodd" />
</svg>'''

SHARE_SVG = '''<svg xmlns="https://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-share-2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>'''

CLOCK_SVG = '''<svg xmlns="https://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
</svg>'''


# ==================== Teacher List Item (Ocean Theme) ====================
class TeacherListItem(QWidget):
    def __init__(self, teacher_data, server_url=config.API_BASE_URL):
        super().__init__()
        self.teacher_data = teacher_data
        self.server_url = server_url
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(8)
        
        username = teacher_data.get("username", teacher_data.get("name", "").lower().replace(" ", ""))
        self.profile_img = CircularProfileLabel(username, server_url, size=40)
        self.profile_img.set_placeholder(self.get_initial(teacher_data.get("name", "?")))
        
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(2)
        
        name_label = QLabel(teacher_data.get("name", "Unknown"))
        name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; background: transparent;")
        specialty_label = QLabel(teacher_data.get("specialties", ["Art"])[0] if teacher_data.get("specialties") else "Teacher")
        specialty_label.setStyleSheet("font-size: 11px; color: #7ab8d4; background: transparent;")
        rating_label = QLabel(f"★ {teacher_data.get('rating',0):.1f} · ${teacher_data.get('hourly_rate',0)}/hr")
        rating_label.setStyleSheet("font-size: 10px; color: #f5a623; background: transparent;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(specialty_label)
        info_layout.addWidget(rating_label)
        
        layout.addWidget(self.profile_img)
        layout.addWidget(info_widget)
        layout.addStretch()
    
    def get_initial(self, name):
        return name[0].upper() if name else "?"


# ==================== Review Card (Ocean Theme) - NO INNER BORDERS ====================
class ReviewCard(QWidget):
    def __init__(self, reviewer_name, reviewer_username, meta, date, text, server_url=config.API_BASE_URL):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255,255,255,0.08);
                border-radius: 12px;
                border: 1px solid rgba(245,166,35,0.2);
            }
            QLabel {
                border: none !important;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.profile_img = CircularProfileLabel(reviewer_username, server_url, size=40)
        self.profile_img.set_placeholder(reviewer_name[0].upper() if reviewer_name else "?")
        layout.addWidget(self.profile_img)

        content = QWidget()
        content.setStyleSheet("border: none !important; background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0,0,0,0)
        content_layout.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(8)
        name_label = QLabel(reviewer_name)
        name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; background: transparent; border: none !important;")
        meta_label = QLabel(meta)
        meta_label.setStyleSheet("font-size: 12px; color: #7ab8d4; background: transparent; border: none !important;")
        header.addWidget(name_label)
        header.addWidget(meta_label)
        header.addStretch()
        content_layout.addLayout(header)

        rating_row = QHBoxLayout()
        rating_row.setSpacing(12)
        gold_color = QColor(245, 166, 35)
        star_icon = QLabel()
        star_icon.setStyleSheet("border: none !important; background: transparent;")
        star_pixmap = svg_to_pixmap(STAR_SVG, 14, gold_color)
        star_icon.setPixmap(star_pixmap)
        star_icon.setFixedSize(14, 14)
        date_label = QLabel(date)
        date_label.setStyleSheet("font-size: 11px; color: #7ab8d4; background: transparent; border: none !important;")
        rating_row.addWidget(star_icon)
        rating_row.addWidget(QLabel("5.0"))
        rating_row.addWidget(date_label)
        rating_row.addStretch()
        content_layout.addLayout(rating_row)

        review_text = QLabel(text)
        review_text.setWordWrap(True)
        review_text.setStyleSheet("font-size: 13px; color: #c8e0f0; background: transparent; line-height: 1.4; border: none !important;")
        content_layout.addWidget(review_text)

        layout.addWidget(content)


# ==================== Clickable Label ====================
class ClickableLabel(QLabel):
    clicked = Signal()
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ==================== 3D Card Frame with Smooth Corners ====================
class ThreeDCardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("courseCard")
        self.setStyleSheet("""
            QFrame#courseCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 80, 140, 0.4),
                    stop:0.3 rgba(20, 60, 120, 0.3),
                    stop:0.7 rgba(15, 50, 100, 0.3),
                    stop:1 rgba(10, 40, 80, 0.5));
                border-radius: 20px;
                border: 1px solid rgba(245,166,35,0.3);
            }
        """)
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(6, 10)
        self.setGraphicsEffect(shadow)
        # Enable antialiasing
        self.setAttribute(Qt.WA_StyledBackground, True)
    
    def paintEvent(self, event):
        # Draw 3D lighting effects with smooth rounded corners
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        rect = self.rect()
        radius = 20
        
        # Create rounded rect path for clipping
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        
        # Top highlight glow
        highlight_gradient = QLinearGradient(0, 0, 0, rect.height() * 0.35)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 35))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setClipPath(path)
        painter.fillRect(0, 0, rect.width(), rect.height() * 0.35, highlight_gradient)
        
        # Left edge highlight
        left_highlight = QLinearGradient(0, 0, 25, 0)
        left_highlight.setColorAt(0, QColor(255, 255, 255, 25))
        left_highlight.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(0, 0, 25, rect.height(), left_highlight)
        
        # Bottom shadow gradient
        shadow_gradient = QLinearGradient(0, rect.height() * 0.75, 0, rect.height())
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 70))
        painter.fillRect(0, rect.height() * 0.75, rect.width(), rect.height() * 0.25, shadow_gradient)
        
        # Gold accent border glow with rounded corners
        border_gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        border_gradient.setColorAt(0, QColor(245, 166, 35, 90))
        border_gradient.setColorAt(0.25, QColor(245, 166, 35, 20))
        border_gradient.setColorAt(0.5, QColor(245, 166, 35, 70))
        border_gradient.setColorAt(0.75, QColor(245, 166, 35, 20))
        border_gradient.setColorAt(1, QColor(245, 166, 35, 50))
        
        # Draw rounded border with glow
        border_path = QPainterPath()
        border_path.addRoundedRect(rect.adjusted(1, 1, -1, -1), radius - 1, radius - 1)
        painter.setPen(QPen(border_gradient, 2))
        painter.drawPath(border_path)
        
        # Top-left corner bright spot (specular highlight)
        corner_glow = QRadialGradient(30, 30, 70)
        corner_glow.setColorAt(0, QColor(245, 166, 35, 30))
        corner_glow.setColorAt(0.5, QColor(245, 166, 35, 10))
        corner_glow.setColorAt(1, QColor(245, 166, 35, 0))
        painter.fillRect(0, 0, 90, 90, corner_glow)
        
        # Inner edge glow (subtle)
        inner_glow = QRadialGradient(rect.width() / 2, rect.height() / 2, rect.width() / 1.5)
        inner_glow.setColorAt(0, QColor(255, 255, 255, 0))
        inner_glow.setColorAt(0.7, QColor(255, 255, 255, 0))
        inner_glow.setColorAt(0.85, QColor(245, 166, 35, 8))
        inner_glow.setColorAt(1, QColor(245, 166, 35, 0))
        painter.fillRect(rect, inner_glow)
        
        painter.setClipping(False)
        painter.end()
        super().paintEvent(event)


# ==================== Main TeacherSelectorDialog (Ocean Theme) ====================
class TeacherSelectorDialog(QDialog):
    def __init__(self, token=None, server_url=config.API_BASE_URL, parent=None):
        super().__init__(parent, Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_AcceptDrops, False)
        
        # Set ocean theme palette
        ocean_palette = QPalette()
        ocean_palette.setColor(QPalette.Window, QColor(10, 46, 92))
        ocean_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        ocean_palette.setColor(QPalette.Base, QColor(10, 46, 92))
        ocean_palette.setColor(QPalette.AlternateBase, QColor(20, 60, 110))
        ocean_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        ocean_palette.setColor(QPalette.Button, QColor(10, 46, 92))
        ocean_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        ocean_palette.setColor(QPalette.BrightText, QColor(245, 166, 35))
        ocean_palette.setColor(QPalette.Highlight, QColor(245, 166, 35))
        ocean_palette.setColor(QPalette.HighlightedText, QColor(10, 46, 92))
        self.setPalette(ocean_palette)
        
        self.setWindowTitle("Select a Teacher")
        self.setMinimumSize(1000, 700)
        
        # Main stylesheet for ocean theme
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a2e5c, stop:1 #0a4a7a);
            }
            QWidget {
                background-color: transparent;
                color: #ffffff;
                font-family: 'Segoe UI', 'Inter', system-ui;
                font-size: 13px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QPushButton {
                font-weight: 500;
                font-size: 14px;
                border-radius: 60px;
                padding: 8px 16px;
            }
            QLineEdit {
                font-size: 14px;
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(245,166,35,0.3);
                border-radius: 18px;
                padding: 0 10px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #f5a623;
            }
            QLineEdit::placeholder {
                color: #7ab8d4;
            }
            QListWidget {
                background-color: rgba(255,255,255,0.05);
                border: 1px solid rgba(245,166,35,0.2);
                border-radius: 12px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid rgba(255,255,255,0.05);
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: rgba(245,166,35,0.2);
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: rgba(245,166,35,0.1);
                border-radius: 8px;
            }
            QProgressBar {
                border: 0.5px solid rgba(245,166,35,0.3);
                border-radius: 4px;
                height: 4px;
                background: rgba(255,255,255,0.1);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f5a623, stop:1 #e8910e);
                border-radius: 4px;
            }
        """)
        
        self.setAutoFillBackground(True)
        
        self.token = token if token else get_token()
        self.server_url = server_url
        self.all_teachers = []
        self.selected_teacher = None
        
        self.setup_ui()
        self.show_loading_state()
        QTimer.singleShot(100, self.fetch_teachers)
    
    def paintEvent(self, event):
        # Gradient background
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(10, 46, 92))
        gradient.setColorAt(1, QColor(10, 74, 122))
        painter.fillRect(self.rect(), gradient)
        painter.end()
        super().paintEvent(event)

    def setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)
        
        # LEFT PANEL - INCREASED WIDTH BY 20% (216px instead of 180px)
        left_panel = QWidget()
        left_panel.setFixedWidth(216)  # 180 * 1.2 = 216
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        search_bar = QWidget()
        search_bar.setFixedWidth(216)
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(5)

        self.search_btn = QPushButton()
        self.search_btn.setFixedSize(36, 36)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.08);
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.15); }
            QPushButton:pressed { background-color: rgba(245,166,35,0.2); }
        """)
        search_pix = svg_to_pixmap(SEARCH_SVG, 28)
        self.search_btn.setIcon(QIcon(search_pix))
        self.search_btn.setIconSize(QSize(24, 24))
        self.search_btn.clicked.connect(self.on_search_clicked)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(245,166,35,0.3);
                border-radius: 18px;
                padding: 0 10px;
                font-size: 14px;
                color: #ffffff;
            }
            QLineEdit:focus { border: 2px solid #f5a623; }
            QLineEdit::placeholder { color: #7ab8d4; }
        """)
        self.search_input.textChanged.connect(self.filter_teachers)

        self.qr_btn = QPushButton()
        self.qr_btn.setFixedSize(36, 36)
        self.qr_btn.setCursor(Qt.PointingHandCursor)
        self.qr_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.08);
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.15); }
            QPushButton:pressed { background-color: rgba(245,166,35,0.2); }
        """)
        qr_pix = svg_to_pixmap(QR_SVG, 28)
        self.qr_btn.setIcon(QIcon(qr_pix))
        self.qr_btn.setIconSize(QSize(24, 24))
        self.qr_btn.clicked.connect(self.show_coming_soon)

        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.qr_btn)

        left_layout.addWidget(search_bar)

        self.teacher_list = QListWidget()
        self.teacher_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255,255,255,0.05);
                border: 1px solid rgba(245,166,35,0.2);
                border-radius: 12px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid rgba(255,255,255,0.05);
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: rgba(245,166,35,0.2);
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: rgba(245,166,35,0.1);
                border-radius: 8px;
            }
        """)
        self.teacher_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.teacher_list.currentRowChanged.connect(self.on_teacher_selected)

        left_layout.addWidget(self.teacher_list)
        splitter.addWidget(left_panel)

        # RIGHT PANEL
        self.profile_panel = QWidget()
        self.profile_layout = QVBoxLayout(self.profile_panel)
        self.profile_layout.setContentsMargins(0,0,0,0)
        self.profile_layout.setSpacing(0)
        
        self.profile_content = QWidget()
        self.profile_content_layout = QVBoxLayout(self.profile_content)
        self.profile_content_layout.setContentsMargins(10,10,10,10)
        self.profile_content_layout.setSpacing(0)
        
        self.profile_layout.addWidget(self.profile_content)
        splitter.addWidget(self.profile_panel)
        splitter.setSizes([216, 800])
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)

    def show_coming_soon(self):
        QMessageBox.information(self, "Coming Soon", "This feature is coming soon!")

    def show_loading_state(self):
        self.clear_layout(self.profile_content_layout)
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_layout.setSpacing(20)
        loading_label = QLabel("🔄 Loading teachers...")
        loading_label.setStyleSheet("font-size: 18px; color: #f5a623; font-weight: 500; background: transparent;")
        loading_layout.addWidget(loading_label)
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setFixedWidth(300)
        progress.setStyleSheet("""
            QProgressBar {
                border: 0.5px solid rgba(245,166,35,0.3);
                border-radius: 4px;
                height: 4px;
                background: rgba(255,255,255,0.1);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f5a623, stop:1 #e8910e);
                border-radius: 4px;
            }
        """)
        loading_layout.addWidget(progress)
        self.profile_content_layout.addWidget(loading_widget)

    def show_error_state(self, error_message):
        self.clear_layout(self.profile_content_layout)
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignCenter)
        error_layout.setSpacing(20)
        icon_label = QLabel("❌")
        icon_label.setStyleSheet("font-size: 48px; color: #ff6b6b; background: transparent;")
        error_layout.addWidget(icon_label)
        error_label = QLabel(error_message)
        error_label.setStyleSheet("font-size: 16px; color: #ffaaaa; padding: 10px; background: transparent;")
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(error_label)
        retry_btn = QPushButton("🔄 Retry")
        retry_btn.setFixedHeight(40)
        retry_btn.setFixedWidth(200)
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                color: #7ab8d4;
                border: 1px solid rgba(245,166,35,0.3);
                border-radius: 60px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover { background: rgba(255,255,255,0.15); }
        """)
        retry_btn.clicked.connect(self.fetch_teachers)
        error_layout.addWidget(retry_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setFixedWidth(200)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                color: #7ab8d4;
                border: 1px solid rgba(245,166,35,0.3);
                border-radius: 60px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover { background: rgba(255,255,255,0.15); }
        """)
        cancel_btn.clicked.connect(self.reject)
        error_layout.addWidget(cancel_btn)
        self.profile_content_layout.addWidget(error_widget)

    def fetch_teachers(self):
        url = f"{self.server_url}/api/teachers"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            self.show_loading_state()
            QApplication.processEvents()
            session = get_requests_session()
            response = session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("success"):
                        self.all_teachers = response_data.get("data", [])
                        
                        # DEBUG: Check if room_id is present
                        if self.all_teachers:
                            first = self.all_teachers[0]
                            print(f"🔍 First teacher room_id: {first.get('room_id')}")
                            print(f"🔍 First teacher keys: {list(first.keys())}")
                        
                        if self.all_teachers and len(self.all_teachers) > 0:
                            self.populate_teacher_list(self.all_teachers)
                            self.teacher_list.setCurrentRow(0)
                            first_item = self.teacher_list.item(0)
                            if first_item:
                                widget = self.teacher_list.itemWidget(first_item)
                                if widget:
                                    self.selected_teacher = widget.teacher_data
                                    self.display_teacher(self.selected_teacher)
                        else:
                            self.show_error_state("No teachers found on server")
                    else:
                        error_msg = response_data.get("error", "Unknown error")
                        self.show_error_state(f"Server error: {error_msg}")
                except json.JSONDecodeError:
                    self.show_error_state("Invalid response from server")
            elif response.status_code == 401:
                self.show_error_state("Authentication failed. Please log in again.")
            else:
                error_msg = f"Server error ({response.status_code})"
                try:
                    error_data = response.json()
                    if error_data.get("error"):
                        error_msg = error_data.get("error")
                except:
                    pass
                self.show_error_state(error_msg)
        except requests.exceptions.ConnectionError:
            self.show_error_state("Cannot connect to server.\nPlease check if the server is running on:\n" + self.server_url)
        except requests.exceptions.Timeout:
            self.show_error_state("Connection timeout.\nThe server is not responding.")
        except requests.exceptions.RequestException as e:
            self.show_error_state(f"Network error: {str(e)}")
        except Exception as e:
            self.show_error_state(f"Unexpected error: {str(e)}")

    def populate_teacher_list(self, teachers):
        self.teacher_list.clear()
        for teacher in teachers:
            item = QListWidgetItem(self.teacher_list)
            widget = TeacherListItem(teacher, self.server_url)
            item.setSizeHint(widget.sizeHint())
            self.teacher_list.addItem(item)
            self.teacher_list.setItemWidget(item, widget)

    def filter_teachers(self, text):
        text = text.lower()
        filtered = [t for t in self.all_teachers 
                    if text in t.get('name', '').lower() 
                    or text in t.get('username', '').lower()
                    or any(text in s.lower() for s in t.get('specialties', []))]
        self.populate_teacher_list(filtered)
        if filtered:
            self.teacher_list.setCurrentRow(0)
            first_item = self.teacher_list.item(0)
            if first_item:
                widget = self.teacher_list.itemWidget(first_item)
                if widget:
                    self.selected_teacher = widget.teacher_data
                    self.display_teacher(self.selected_teacher)
        else:
            self.clear_layout(self.profile_content_layout)
            no_results = QLabel("No teachers found matching your search")
            no_results.setStyleSheet("font-size: 18px; color: #7ab8d4; padding: 40px; background: transparent;")
            no_results.setAlignment(Qt.AlignCenter)
            self.profile_content_layout.addWidget(no_results)

    def on_search_clicked(self):
        self.filter_teachers(self.search_input.text())

    def on_teacher_selected(self, index):
        item = self.teacher_list.item(index)
        if item:
            widget = self.teacher_list.itemWidget(item)
            if widget:
                self.selected_teacher = widget.teacher_data
                self.display_teacher(self.selected_teacher)

    def display_teacher(self, teacher_data):
        self.clear_layout(self.profile_content_layout)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        left = QWidget()
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(0)

        # Use 3D Card Frame with smooth corners
        right = ThreeDCardFrame()
        right.setFixedWidth(320)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)

        self.booking_content = QWidget()
        booking_layout = QVBoxLayout(self.booking_content)
        booking_layout.setContentsMargins(0,0,0,0)
        booking_layout.setSpacing(12)

        username = teacher_data.get("username", teacher_data.get("name", "").lower().replace(" ", ""))
        
        # Profile image with enhanced 3D effect
        profile_img_card = CircularProfileLabel(username, self.server_url, size=120)
        profile_img_card.set_placeholder(self.get_initial(teacher_data.get("name", "?")))
        profile_img_card.setFixedHeight(120)
        profile_img_card.setAlignment(Qt.AlignCenter)
        # Add shadow to profile image
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 6)
        profile_img_card.setGraphicsEffect(shadow)
        booking_layout.addWidget(profile_img_card, 0, Qt.AlignCenter)

        price = QLabel(f"{teacher_data.get('currency','$')}{teacher_data.get('hourly_rate',0)}/hour")
        price.setStyleSheet("font-size: 28px; font-weight: 700; color: #f5a623; background: transparent;")
        price.setAlignment(Qt.AlignCenter)
        booking_layout.addWidget(price)

        short_desc = QLabel("Book a session and start learning today!")
        short_desc.setWordWrap(True)
        short_desc.setStyleSheet("font-size: 14px; color: #7ab8d4; background: transparent;")
        short_desc.setAlignment(Qt.AlignCenter)
        booking_layout.addWidget(short_desc)

        # BOOK NOW BUTTON - 3D enhanced with gradient
        self.book_btn = QPushButton("Book Now")
        self.book_btn.setFixedHeight(48)
        self.book_btn.setCursor(Qt.PointingHandCursor)
        self.book_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5a623,
                    stop:0.5 #e8910e,
                    stop:1 #d4850a);
                color: #0a2e5c;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 700;
                padding: 4px 0;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffb84d,
                    stop:0.5 #f5a623,
                    stop:1 #e8910e);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d4850a,
                    stop:1 #b8730a);
            }
        """)
        self.book_btn.clicked.connect(self.accept_with_teacher)
        booking_layout.addWidget(self.book_btn)

        desc_long = QLabel(teacher_data.get("long_description", ""))
        desc_long.setWordWrap(True)
        desc_long.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #c8e0f0;
                background-color: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 16px;
                margin-top: 8px;
                line-height: 1.5;
            }
        """)
        booking_layout.addWidget(desc_long)

        expect_row = QHBoxLayout()
        expect_row.setSpacing(8)
        expect = QLabel("✨ What to expect:")
        expect.setStyleSheet("font-size: 13px; font-weight: 600; color: #f5a623; background: transparent;")
        expect_row.addWidget(expect)
        expect_row.addStretch()

        gold_color = QColor(245, 166, 35)
        star_btn = QPushButton()
        star_btn.setFixedSize(32, 32)
        star_btn.setCursor(Qt.PointingHandCursor)
        star_btn.setToolTip("Add to favorites")
        star_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        star_pix = svg_to_pixmap(STAR_SVG, 28, gold_color)
        star_btn.setIcon(QIcon(star_pix))
        star_btn.setIconSize(QSize(22, 22))
        star_btn.clicked.connect(self.show_coming_soon)

        share_btn = QPushButton()
        share_btn.setFixedSize(32, 32)
        share_btn.setCursor(Qt.PointingHandCursor)
        share_btn.setToolTip("Share profile")
        share_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        share_pix = svg_to_pixmap(SHARE_SVG, 28)
        share_btn.setIcon(QIcon(share_pix))
        share_btn.setIconSize(QSize(22, 22))
        share_btn.clicked.connect(self.show_coming_soon)

        expect_row.addWidget(star_btn)
        expect_row.addWidget(share_btn)
        booking_layout.addLayout(expect_row)

        bullets = QLabel(
            "• Personalized instruction\n"
            "• Step-by-step guidance\n"
            "• Practice exercises\n"
            "• Constructive feedback"
        )
        bullets.setWordWrap(True)
        bullets.setStyleSheet("font-size: 13px; color: #7ab8d4; margin-left: 8px; background: transparent; line-height: 1.5;")
        booking_layout.addWidget(bullets)

        help_row = QHBoxLayout()
        help_row.addStretch()
        # HELP BUTTON - 3D enhanced with gradient
        help_btn = QPushButton("?")
        help_btn.setFixedSize(36, 36)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5a623,
                    stop:0.5 #e8910e,
                    stop:1 #d4850a);
                color: #0a2e5c;
                border: none;
                border-radius: 18px;
                font-size: 20px;
                font-weight: 700;
                padding: 0 0 2px 0;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffb84d,
                    stop:0.5 #f5a623,
                    stop:1 #e8910e);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d4850a,
                    stop:1 #b8730a);
            }
        """)
        help_btn.clicked.connect(self.show_coming_soon)
        help_row.addWidget(help_btn)
        booking_layout.addLayout(help_row)

        booking_layout.addStretch()
        right_layout.addWidget(self.booking_content)

        self.done_container = QWidget()
        done_layout = QVBoxLayout(self.done_container)
        done_layout.setAlignment(Qt.AlignCenter)
        done_layout.setContentsMargins(20, 20, 20, 20)

        self.done_gif_label = QualityGifLabel()
        self.done_gif_label.setFixedSize(250, 250)
        self.done_gif_label.setAlignment(Qt.AlignCenter)
        self.done_gif_label.setStyleSheet("background: transparent;")
        done_layout.addWidget(self.done_gif_label)

        self.done_message = QLabel("Booking Confirmed!")
        self.done_message.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #4CAF50;
                margin-top: 10px;
                background: transparent;
            }
        """)
        self.done_message.setAlignment(Qt.AlignCenter)
        done_layout.addWidget(self.done_message)

        self.done_container.hide()
        right_layout.addWidget(self.done_container)
        right_layout.addStretch()

        # Left column content
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        author_widget = QWidget()
        author_layout = QHBoxLayout(author_widget)
        author_layout.setContentsMargins(0,0,0,0)
        author_layout.setSpacing(8)

        author_img = CircularProfileLabel(username, self.server_url, size=36)
        author_img.set_placeholder(self.get_initial(teacher_data.get("name", "?")))
        author_name = QLabel(teacher_data.get("name", "Unknown"))
        author_name.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff; background: transparent;")

        author_layout.addWidget(author_img)
        author_layout.addWidget(author_name)
        author_layout.addStretch()

        title = QLabel(teacher_data.get("hero_text", "Teacher Profile"))
        title.setStyleSheet("font-size: 40px; font-weight: 700; color: #ffffff; background: transparent; letter-spacing: -0.5px;")
        title.setWordWrap(True)

        top_row.addWidget(author_widget)
        top_row.addStretch()
        top_row.addWidget(title)
        top_row.addStretch()
        left_layout.addLayout(top_row)

        desc = QLabel(teacher_data.get("description", ""))
        desc.setWordWrap(True)
        desc.setFixedWidth(650)
        desc.setStyleSheet("font-size: 16px; color: #c8e0f0; margin-top: 12px; margin-bottom: 30px; background: transparent; line-height: 1.5;")
        left_layout.addWidget(desc)

        exp_years = teacher_data.get("experience_years", "N/A")
        exp_row = QHBoxLayout()
        exp_row.setSpacing(6)
        exp_row.setContentsMargins(0, 20, 0, 0)

        clock_btn = QPushButton()
        clock_btn.setFixedSize(24, 24)
        clock_btn.setCursor(Qt.PointingHandCursor)
        clock_btn.setToolTip("Experience years")
        clock_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        clock_pix = svg_to_pixmap(CLOCK_SVG, 22)
        clock_btn.setIcon(QIcon(clock_pix))
        clock_btn.setIconSize(QSize(18, 18))
        clock_btn.clicked.connect(self.show_coming_soon)

        exp_text = QLabel(f"Experience: {exp_years} years")
        exp_text.setStyleSheet("font-size: 14px; color: #7ab8d4; background: transparent;")

        exp_row.addWidget(clock_btn)
        exp_row.addWidget(exp_text)
        exp_row.addStretch()
        left_layout.addLayout(exp_row)

        stats = QHBoxLayout()
        stats.setSpacing(20)
        stats.setContentsMargins(0, 30, 0, 0)

        rating_widget = QWidget()
        rating_vbox = QVBoxLayout(rating_widget)
        rating_vbox.setSpacing(4)
        rating_vbox.setAlignment(Qt.AlignCenter)

        olive_container = QFrame()
        olive_container.setFixedSize(80,80)
        olive_container.setFrameShape(QFrame.NoFrame)
        olive_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        olive_label = QLabel(olive_container)
        olive_pixmap = QPixmap("olive.png")
        if not olive_pixmap.isNull():
            olive_label.setPixmap(olive_pixmap.scaled(70,70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            olive_label.setText("🫒")
            olive_label.setStyleSheet("font-size: 40px; color: #f5a623; background: transparent;")
        olive_label.setAlignment(Qt.AlignCenter)
        olive_label.setGeometry(5,5,70,70)

        rating_num = QLabel(olive_container)
        rating_num.setText(f"{teacher_data.get('rating',0):.1f}")
        rating_num.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        rating_num.setFont(font)
        rating_num.setStyleSheet("color: #ffffff; background: transparent; font-size: 22px; font-weight: bold;")
        rating_num.setGeometry(20, 25, 40, 30)

        star_container = QWidget()
        star_container.setFixedWidth(120)
        star_layout = QHBoxLayout(star_container)
        star_layout.setContentsMargins(0, 0, 0, 0)
        star_layout.setSpacing(4)
        star_layout.setAlignment(Qt.AlignCenter)

        star_size = 20
        for i in range(5):
            star_icon = QLabel()
            star_pixmap = svg_to_pixmap(STAR_SVG, star_size + 2, gold_color)
            star_icon.setPixmap(star_pixmap)
            star_icon.setFixedSize(star_size, star_size)
            star_icon.setAlignment(Qt.AlignCenter)
            star_layout.addWidget(star_icon)

        star_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        rating_vbox.addWidget(olive_container, 0, Qt.AlignCenter)
        rating_vbox.addWidget(star_container, 0, Qt.AlignCenter)
        stats.addWidget(rating_widget)

        line1 = QFrame()
        line1.setFrameShape(QFrame.VLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("background-color: rgba(245,166,35,0.3); max-width: 1px; margin: 5px 0;")
        line1.setFixedWidth(1)
        line1.setFixedHeight(60)
        stats.addWidget(line1)

        rev_widget = QWidget()
        rev_vbox = QVBoxLayout(rev_widget)
        rev_vbox.setSpacing(2)
        rev_num = QLabel(str(teacher_data.get('total_reviews',0)))
        rev_num.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; background: transparent;")
        rev_label = QLabel("Reviews")
        rev_label.setStyleSheet("font-size: 14px; color: #7ab8d4; background: transparent;")
        rev_vbox.addWidget(rev_num)
        rev_vbox.addWidget(rev_label)
        stats.addWidget(rev_widget)

        line2 = QFrame()
        line2.setFrameShape(QFrame.VLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("background-color: rgba(245,166,35,0.3); max-width: 1px; margin: 5px 0;")
        line2.setFixedWidth(1)
        line2.setFixedHeight(60)
        stats.addWidget(line2)

        stu_widget = QWidget()
        stu_vbox = QVBoxLayout(stu_widget)
        stu_vbox.setSpacing(2)
        stu_num = QLabel(str(teacher_data.get('students_count',0)))
        stu_num.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; background: transparent;")
        stu_label = QLabel("Students")
        stu_label.setStyleSheet("font-size: 14px; color: #7ab8d4; background: transparent;")
        stu_vbox.addWidget(stu_num)
        stu_vbox.addWidget(stu_label)
        stats.addWidget(stu_widget)

        line3 = QFrame()
        line3.setFrameShape(QFrame.VLine)
        line3.setFrameShadow(QFrame.Sunken)
        line3.setStyleSheet("background-color: rgba(245,166,35,0.3); max-width: 1px; margin: 5px 0;")
        line3.setFixedWidth(1)
        line3.setFixedHeight(60)
        stats.addWidget(line3)

        rate_widget = QWidget()
        rate_vbox = QVBoxLayout(rate_widget)
        rate_vbox.setSpacing(2)
        rate_num = QLabel(f"{teacher_data.get('currency','$')}{teacher_data.get('hourly_rate',0)}")
        rate_num.setStyleSheet("font-size: 24px; font-weight: 700; color: #f5a623; background: transparent;")
        rate_label = QLabel("per hour")
        rate_label.setStyleSheet("font-size: 14px; color: #7ab8d4; background: transparent;")
        rate_vbox.addWidget(rate_num)
        rate_vbox.addWidget(rate_label)
        stats.addWidget(rate_widget)

        stats.addStretch()
        left_layout.addLayout(stats)

        tabs = QHBoxLayout()
        tabs.setSpacing(28)
        tabs.setContentsMargins(0, 50, 0, 0)

        overview = ClickableLabel("Overview")
        overview.setStyleSheet("font-size: 16px; font-weight: 600; padding-bottom: 8px; border-bottom: 2px solid #f5a623; color: #f5a623; background: transparent;")
        overview.clicked.connect(self.show_coming_soon)

        experience = ClickableLabel("Experience")
        experience.setStyleSheet("font-size: 16px; font-weight: 600; padding-bottom: 8px; border-bottom: 2px solid transparent; color: #7ab8d4; background: transparent;")
        experience.clicked.connect(self.show_coming_soon)

        specialties = ClickableLabel("Specialties")
        specialties.setStyleSheet("font-size: 16px; font-weight: 600; padding-bottom: 8px; border-bottom: 2px solid transparent; color: #7ab8d4; background: transparent;")
        specialties.clicked.connect(self.show_coming_soon)

        reviews_tab = ClickableLabel("Reviews")
        reviews_tab.setStyleSheet("font-size: 16px; font-weight: 600; padding-bottom: 8px; border-bottom: 2px solid transparent; color: #7ab8d4; background: transparent;")
        reviews_tab.clicked.connect(self.show_coming_soon)

        tabs.addWidget(overview)
        tabs.addWidget(experience)
        tabs.addWidget(specialties)
        tabs.addWidget(reviews_tab)
        tabs.addStretch()
        left_layout.addLayout(tabs)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(245,166,35,0.3); max-height: 1px; margin-top: 4px;")
        left_layout.addWidget(line)

        reviews_title = QLabel("📝 What students say")
        reviews_title.setStyleSheet("font-size: 22px; font-weight: 700; margin-top: 24px; margin-bottom: 16px; color: #f5a623; background: transparent;")
        left_layout.addWidget(reviews_title)

        review_horizontal = QHBoxLayout()
        review_horizontal.setSpacing(16)
        reviews_list = teacher_data.get('reviews', [])
        if reviews_list:
            for review in reviews_list[:2]:
                reviewer_name = review.get('reviewer_name', 'Student')
                reviewer_username = review.get('reviewer_username', 'student')
                review_text = review.get('text', 'Great teacher!')
                review_date = review.get('date', '2025-03-14')
                card = ReviewCard(reviewer_name, reviewer_username, "Verified", review_date, review_text, self.server_url)
                card.setMinimumWidth(250)
                card.setMaximumWidth(300)
                review_horizontal.addWidget(card)
        else:
            card1 = ReviewCard("Emily Chen", "emily_chen", "5 lessons", "2025-03-14", "Excellent teacher! Very patient and knowledgeable.", self.server_url)
            card1.setMinimumWidth(250)
            card1.setMaximumWidth(300)
            card2 = ReviewCard("Michael Brown", "michael_b", "10 lessons", "2025-02-20", "Best teacher I've ever had! Highly recommend.", self.server_url)
            card2.setMinimumWidth(250)
            card2.setMaximumWidth(300)
            review_horizontal.addWidget(card1)
            review_horizontal.addWidget(card2)
        left_layout.addLayout(review_horizontal)

        review_input_widget = QWidget()
        review_input_layout = QHBoxLayout(review_input_widget)
        review_input_layout.setContentsMargins(0, 16, 0, 8)
        review_input_layout.setSpacing(8)

        review_input = QLineEdit()
        review_input.setPlaceholderText("Write a review...")
        review_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(245,166,35,0.3);
                border-radius: 18px;
                padding: 8px 14px;
                font-size: 14px;
                color: #ffffff;
            }
            QLineEdit:focus { border: 2px solid #f5a623; }
            QLineEdit::placeholder { color: #7ab8d4; }
        """)
        review_input.setFixedHeight(36)

        # SUBMIT REVIEW BUTTON - 3D enhanced with gradient
        submit_review_btn = QPushButton("Submit")
        submit_review_btn.setFixedHeight(36)
        submit_review_btn.setCursor(Qt.PointingHandCursor)
        submit_review_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5a623,
                    stop:0.5 #e8910e,
                    stop:1 #d4850a);
                color: #0a2e5c;
                border: none;
                border-radius: 18px;
                padding: 0 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffb84d,
                    stop:0.5 #f5a623,
                    stop:1 #e8910e);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d4850a,
                    stop:1 #b8730a);
            }
        """)
        submit_review_btn.clicked.connect(self.show_coming_soon)

        review_input_layout.addWidget(review_input)
        review_input_layout.addWidget(submit_review_btn)
        left_layout.addWidget(review_input_widget)
        left_layout.addStretch()

        columns_layout.addWidget(left)
        columns_layout.addWidget(right)
        self.profile_content_layout.addLayout(columns_layout)
        self.profile_content_layout.addStretch(1)

    def get_initial(self, name):
        return name[0].upper() if name else "?"

    def accept_with_teacher(self):
        if not self.selected_teacher:
            QMessageBox.warning(self, "No Teacher", "Please select a teacher first.")
            return
        
        # Validate that room_id exists BEFORE booking
        room_id = self.selected_teacher.get("room_id")
        if not room_id:
            error_msg = (
                f"❌ Server Error: No room_id found for teacher '{self.selected_teacher.get('name', 'Unknown')}'.\n\n"
                "The server is not returning the room_id field in the /api/teachers response.\n"
                "Please make sure the server is updated and running correctly.\n\n"
                "Contact your system administrator."
            )
            QMessageBox.critical(self, "Server Configuration Error", error_msg)
            return
        
        self.book_btn.setEnabled(False)
        self.book_btn.setText("Booking...")
        QTimer.singleShot(1500, self._on_booking_success)

    def _on_booking_success(self):
        self.show_done_animation()
        QTimer.singleShot(1500, self.accept)

    def show_done_animation(self):
        print("🔊 Playing happy alert chimes...")
        sound_manager.play_upload()
        self.booking_content.hide()
        self.done_container.show()
        gif_path = "done.gif"
        if not os.path.exists(gif_path):
            print(f"⚠️ GIF file not found: {gif_path}")
            self.show_done_fallback()
            return
        movie = QMovie(gif_path)
        if movie.isValid():
            self.done_gif_label.setMovie(movie)
            self.done_movie = movie
            frame_count = movie.frameCount()
            original_size = movie.frameRect().size()
            print(f"✅ GIF loaded: {frame_count} frames, original size: {original_size.width()}x{original_size.height()}")
        else:
            print("❌ Invalid GIF file")
            self.show_done_fallback()

    def show_done_fallback(self):
        pixmap = QPixmap(150, 150)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(76, 175, 80))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(10, 10, 130, 130)
        painter.setPen(QPen(Qt.white, 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(40, 75, 65, 100)
        painter.drawLine(65, 100, 110, 45)
        painter.end()
        self.done_gif_label.setPixmap(pixmap)
        self.done_gif_label.setFixedSize(150, 150)
        self.done_message.setText("Booking Confirmed!")

    # ==================== get_selected_room - NO FALLBACK ====================
    def get_selected_room(self):
        """
        Return the room ID of the selected teacher.
        This MUST come from the server's /api/teachers response.
        If room_id is missing, show error and return None.
        """
        if not self.selected_teacher:
            return None
        
        # Get room_id from teacher data
        room_id = self.selected_teacher.get("room_id")
        
        if room_id:
            print(f"✅ Returning room_id from teacher data: {room_id}")
            return room_id
        
        # No room_id found - this is a SERVER ERROR
        teacher_name = self.selected_teacher.get("name", "Unknown")
        teacher_username = self.selected_teacher.get("username", "Unknown")
        
        error_msg = (
            f"❌ SERVER ERROR: No room_id found for teacher '{teacher_name}'.\n\n"
            f"Teacher: {teacher_name}\n"
            f"Username: {teacher_username}\n\n"
            "The server is not returning the room_id field in the /api/teachers response.\n"
            "Please make sure:\n"
            "  1. The server is using the updated main.go with room_id in the query\n"
            "  2. The server has been recompiled and restarted\n"
            "  3. The teacher has a room in the rooms table\n\n"
            "Contact your system administrator."
        )
        
        print(error_msg)
        QMessageBox.critical(
            self,
            "Server Configuration Error",
            error_msg
        )
        
        return None

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                else:
                    self.clear_layout(item.layout())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    dialog = TeacherSelectorDialog()
    if dialog.exec() == QDialog.Accepted:
        print(f"Selected room: {dialog.get_selected_room()}")
    sys.exit(0)