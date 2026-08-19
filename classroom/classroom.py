#!/usr/bin/env python3
# screen.py - HTTP .ts viewer with WebSocket waiting room support

import sys
import json
import requests
import time
import config
import gc
import os
import urllib3
import websocket
import ssl
import traceback

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from token_manager import get_current_room, get_token, is_authenticated, get_user_data, get_auth_headers

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QPushButton, QSizePolicy, QMainWindow
)
from PySide6.QtCore import QThread, Signal, QTimer, Qt, QPropertyAnimation, QEasingCurve, Property, QMutex, QMutexLocker
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QIcon, QPixmap, QAction, QKeySequence, QFont
from PySide6.QtSvg import QSvgRenderer
import vlc

# ========== CONFIGURATION ==========
ROOM_ID = get_current_room()
TOKEN = get_token()
SERVER_URL = config.STREAM_BASE_URL

# Ensure HTTPS (the Go server runs TLS)
if SERVER_URL.startswith("https://"):
    SERVER_URL = SERVER_URL.replace("https://", "https://")
    print(f"⚠️  Auto-converted to HTTPS: {SERVER_URL}")

def get_websocket_url():
    ws_url = SERVER_URL.replace("https://", "wss://").replace("https://", "ws://")
    return ws_url

if not TOKEN or not ROOM_ID:
    print("❌ ERROR: No valid token or room found!")
    

print(f"✅ Viewer started | Room: {ROOM_ID} | Token: {TOKEN[:20]}...")
print(f"🔗 Server URL: {SERVER_URL}")

# ========== HELPER FUNCTIONS ==========
def get_insecure_session():
    session = requests.Session()
    session.verify = False
    return session

def load_svg_icon(filename, size=24):
    if os.path.exists(filename):
        renderer = QSvgRenderer(filename)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    return QIcon()

def load_svg_from_string(svg_data, size=24, color=None):
    """Load SVG from string data with optional color replacement"""
    svg_str = svg_data
    if color:
        # Replace fill colors with the specified color
        svg_str = svg_str.replace('fill="#FFFFFF"', f'fill="{color}"')
        svg_str = svg_str.replace('fill="#000000"', f'fill="{color}"')
    renderer = QSvgRenderer(svg_str.encode('utf-8'))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

# SVG for play icon
PLAY_SVG = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="800px" height="800px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M21.4086 9.35258C23.5305 10.5065 23.5305 13.4935 21.4086 14.6474L8.59662 21.6145C6.53435 22.736 4 21.2763 4 18.9671L4 5.0329C4 2.72368 6.53435 1.26402 8.59661 2.38548L21.4086 9.35258Z" fill="#FFFFFF"/>
</svg>'''

# SVG for pause icon
PAUSE_SVG = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="800px" height="800px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M2 6C2 4.11438 2 3.17157 2.58579 2.58579C3.17157 2 4.11438 2 6 2C7.88562 2 8.82843 2 9.41421 2.58579C10 3.17157 10 4.11438 10 6V18C10 19.8856 10 20.8284 9.41421 21.4142C8.82843 22 7.88562 22 6 22C4.11438 22 3.17157 22 2.58579 21.4142C2 20.8284 2 19.8856 2 18V6Z" fill="#FFFFFF"/>
<path d="M14 6C14 4.11438 14 3.17157 14.5858 2.58579C15.1716 2 16.1144 2 18 2C19.8856 2 20.8284 2 21.4142 2.58579C22 3.17157 22 4.11438 22 6V18C22 19.8856 22 20.8284 21.4142 21.4142C20.8284 22 19.8856 22 18 22C16.1144 22 15.1716 22 14.5858 21.4142C14 20.8284 14 19.8856 14 18V6Z" fill="#FFFFFF"/>
</svg>'''

# SVG for fullscreen icon
FULLSCREEN_SVG = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="800px" height="800px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M21 9V8C21 5.79086 18.9853 4 16.5 4H15.25M21 15V16C21 18.2091 18.9853 20 16.5 20H15.25M3 15V16C3 18.2091 5.01472 20 7.5 20H8.75M3 9V8C3 5.79086 5.01472 4 7.5 4H8.75" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# ========== FULLSCREEN STREAM WINDOW ==========
class FullscreenStreamWindow(QMainWindow):
    def __init__(self, stream_viewer, parent=None):
        super().__init__(parent)
        self.stream_viewer = stream_viewer
        self._is_closing = False
        self._closing_lock = QMutex()
        self.vlc_instance = None
        self.vlc_player = None
        self.stream_url = stream_viewer.stream_url
        self._last_state = None
        self._reconnect_timer = QTimer()
        self._reconnect_timer.timeout.connect(self._check_stream_health)
        self._reconnect_attempts = 0
        self._max_reconnect = 5
        self._is_waiting = False
        self._waiting_thread = None
        
        self.setWindowTitle("Fullscreen Stream")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #000000;")
        
        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create video container
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.video_container)
        
        # Create overlay label for waiting message
        self.waiting_label = QLabel("Click PLAY to start stream", self.video_container)
        self.waiting_label.setAlignment(Qt.AlignCenter)
        self.waiting_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 24px;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 20px;
                border-radius: 10px;
            }
        """)
        self.waiting_label.setVisible(True)
        self.waiting_label.setGeometry(
            (self.width() - self.waiting_label.sizeHint().width()) // 2,
            (self.height() - self.waiting_label.sizeHint().height()) // 2,
            self.waiting_label.sizeHint().width(),
            self.waiting_label.sizeHint().height()
        )
        
        # Create a close button overlay (top-right corner)
        self.close_button = QPushButton("✕", self)
        self.close_button.setFixedSize(50, 50)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.7);
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.9);
            }
        """)
        self.close_button.clicked.connect(self.secure_close)
        
        # Position the close button in top-right corner
        self.close_button.move(self.width() - 60, 10)
        
        # Show mouse cursor only when over close button area
        self.setMouseTracking(True)
        self.close_button.setMouseTracking(True)
        
        # Don't auto-start playback - just show waiting state
        self.show_waiting_message()
    
    def secure_close(self):
        """Securely close the window with proper cleanup"""
        print("🔒 Securely closing fullscreen window...")
        self.close()
    
    def show_waiting_message(self):
        """Show waiting message"""
        self.waiting_label.setVisible(True)
        self.waiting_label.setText("Click PLAY to start stream")
        self.waiting_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 24px;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 20px;
                border-radius: 10px;
            }
        """)
        self.waiting_label.setGeometry(
            (self.width() - self.waiting_label.sizeHint().width()) // 2,
            (self.height() - self.waiting_label.sizeHint().height()) // 2,
            self.waiting_label.sizeHint().width(),
            self.waiting_label.sizeHint().height()
        )
    
    def resizeEvent(self, event):
        """Update close button position on resize"""
        super().resizeEvent(event)
        self.close_button.move(self.width() - 60, 10)
        # Center the waiting label
        if self.waiting_label.isVisible():
            label_width = self.waiting_label.sizeHint().width()
            label_height = self.waiting_label.sizeHint().height()
            self.waiting_label.setGeometry(
                (self.width() - label_width) // 2,
                (self.height() - label_height) // 2,
                label_width,
                label_height
            )
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def start_playback(self, stream_url):
        """Start VLC playback in fullscreen window with the given URL"""
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        self.stream_url = stream_url
        self.waiting_label.setVisible(False)
        
        try:
            # VLC instance options
            vlc_args = [
                '--no-xlib',
                '--quiet',
                '--network-caching=2000',
                '--live-caching=2000',
                '--no-video-title-show',
                '--clock-synchro=0',
                '--no-rtsp-tcp',
                '--fullscreen',
            ]
            self.vlc_instance = vlc.Instance(*vlc_args)
            if self.vlc_instance is None:
                raise Exception("VLC instance creation failed")
            
            self.vlc_player = self.vlc_instance.media_player_new()
            if self.vlc_player is None:
                raise Exception("VLC media player creation failed")
            
            # Set window handle
            if sys.platform == "win32":
                self.vlc_player.set_hwnd(int(self.video_container.winId()))
            elif sys.platform == "darwin":
                self.vlc_player.set_nsobject(int(self.video_container.winId()))
            else:
                self.vlc_player.set_xwindow(int(self.video_container.winId()))
            
            # Create media
            media = self.vlc_instance.media_new(self.stream_url)
            media.add_option('--http-reconnect')
            media.add_option('--http-continuous')
            media.add_option('--network-caching=2000')
            media.add_option('--live-caching=2000')
            
            self.vlc_player.set_media(media)
            
            # Play
            ret = self.vlc_player.play()
            if ret == 0:
                print(f"✅ Fullscreen VLC playback started")
                self._reconnect_timer.start(5000)
            else:
                print(f"❌ Fullscreen VLC playback failed with code {ret}")
                self.show_waiting_message()
                self.waiting_label.setText("Playback failed")
                
        except Exception as e:
            print(f"Fullscreen VLC error: {e}")
            traceback.print_exc()
            self.show_waiting_message()
            self.waiting_label.setText(f"Error: {str(e)[:50]}")
    
    def _check_stream_health(self):
        """Check if stream is still playing"""
        with QMutexLocker(self._closing_lock):
            if self._is_closing or not self.vlc_player:
                return
                
        try:
            state = self.vlc_player.get_state()
            
            if state == vlc.State.Error:
                print("⚠️ Fullscreen VLC error state")
                self._cleanup_vlc()
                self.show_waiting_message()
                self.waiting_label.setText("Stream error - click PLAY to retry")
            elif state == vlc.State.Ended:
                print("⚠️ Fullscreen VLC ended")
                self._cleanup_vlc()
                self.show_waiting_message()
                self.waiting_label.setText("Stream ended - click PLAY to restart")
            elif state == vlc.State.Playing:
                self._reconnect_attempts = 0
        except Exception as e:
            print(f"⚠️ Fullscreen health check error: {e}")
    
    def _cleanup_vlc(self):
        """Clean up VLC resources"""
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        try:
            if self.vlc_player:
                try:
                    self.vlc_player.stop()
                except:
                    pass
                try:
                    self.vlc_player.release()
                except:
                    pass
                self.vlc_player = None
                
            if self.vlc_instance:
                try:
                    self.vlc_instance.release()
                except:
                    pass
                self.vlc_instance = None
                
            self._reconnect_timer.stop()
            gc.collect()
        except Exception as e:
            print(f"⚠️ Error cleaning up VLC: {e}")
    
    def closeEvent(self, event):
        """Handle close event with full cleanup"""
        print("🔒 Closing fullscreen window...")
        
        # Stop all threads first
        if self._waiting_thread:
            try:
                self._waiting_thread.stop()
                self._waiting_thread.wait(2000)  # Wait up to 2 seconds
            except:
                pass
            self._waiting_thread = None
        
        # Clean up VLC
        self._cleanup_vlc()
        
        # Mark as closing
        with QMutexLocker(self._closing_lock):
            self._is_closing = True
        
        # Clean up timers
        try:
            self._reconnect_timer.stop()
        except:
            pass
        
        # Force garbage collection
        gc.collect()
        
        print("✅ Fullscreen window closed successfully")
        event.accept()

# ----------------------------------------------------------------------
# WebSocket Waiting Thread
# ----------------------------------------------------------------------
class WaitingRoomThread(QThread):
    room_ready = Signal(str)   # stream_id
    error = Signal(str)

    def __init__(self, server_url, room_id, token):
        super().__init__()
        self.server_url = server_url
        self.room_id = room_id
        self.token = token
        self._running = True
        self._ready_emitted = False
        self.ws = None
        self._mutex = QMutex()

    def run(self):
        ws_url = f"{get_websocket_url()}/ws?room={self.room_id}&stream=default&token={self.token}&mode=view"
        print(f"🔗 Connecting to WebSocket waiting room: {ws_url}")
        try:
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            self.ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=30,
                ping_timeout=10
            )
        except Exception as e:
            self.error.emit(f"WebSocket error: {str(e)}")

    def on_open(self, ws):
        print("✅ WebSocket connected to waiting room")
        self._running = True

    def on_message(self, ws, message):
        if not self._running:
            return
        try:
            data = json.loads(message)
            print(f"📨 Waiting room message: {data}")
            if not self._ready_emitted and (data.get("type") == "stream_info" or data.get("streamId")):
                stream_id = data.get("streamId")
                if stream_id:
                    print(f"✅ Room ready! Stream ID: {stream_id}")
                    self._ready_emitted = True
                    self.room_ready.emit(stream_id)
        except json.JSONDecodeError:
            print(f"📨 Raw message: {message}")

    def on_error(self, ws, error):
        if not self._running:
            return
        print(f"⚠️ WebSocket error: {error}")
        if self._running:
            self.error.emit(f"WebSocket error: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔌 WebSocket closed (code: {close_status_code}, msg: {close_msg})")
        if self._running and not self._ready_emitted:
            self.error.emit("WebSocket connection closed unexpectedly")

    def stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

# ----------------------------------------------------------------------
# Status Bar with no background color
# ----------------------------------------------------------------------
class NoBackgroundStatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: none;
                border: none;
            }
        """)
        self.setFixedHeight(50)
    
    def paintEvent(self, event):
        """Override paint event to draw nothing (no background)"""
        # Don't call super().paintEvent to avoid drawing any background
        pass

# ----------------------------------------------------------------------
# AnimatedStatusIndicator
# ----------------------------------------------------------------------
class AnimatedStatusIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._opacity = 1.0
        self._animation = None
        self._status = "disconnected"
        self.setStyleSheet("background-color: transparent;")

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.update()

    custom_opacity = Property(float, get_opacity, set_opacity)

    def set_status(self, status):
        self._status = status
        self._start_animation()

    def _start_animation(self):
        if self._animation is not None:
            try:
                self._animation.stop()
            except RuntimeError:
                pass
            self._animation.deleteLater()
            self._animation = None

        if self._status == "connecting":
            self._animation = QPropertyAnimation(self, b"custom_opacity")
            self._animation.setDuration(800)
            self._animation.setStartValue(0.3)
            self._animation.setEndValue(1.0)
            self._animation.setEasingCurve(QEasingCurve.InOutSine)
            self._animation.setLoopCount(-1)
            self._animation.start()
        else:
            self._opacity = 1.0
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._status == "connected":
            color = QColor(0, 255, 0)
        elif self._status == "connecting":
            color = QColor(255, 165, 0)
        elif self._status == "error":
            color = QColor(255, 0, 0)
        else:
            color = QColor(128, 128, 128)

        color.setAlphaF(self._opacity)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 8, 8)

        if self._status == "connecting":
            glow_color = QColor(255, 165, 0)
            glow_color.setAlphaF(self._opacity * 0.5)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(1, 1, 10, 10)

# ----------------------------------------------------------------------
# Rounded video frame
# ----------------------------------------------------------------------
class RoundedVideoFrame(QFrame):
    def __init__(self, parent=None, radius=24):
        super().__init__(parent)
        self.radius = radius
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("RoundedVideoFrame { background-color: #000000; border: none; border-radius: 24px; }")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.radius, self.radius)
        painter.fillPath(path, QBrush(QColor(0, 0, 0)))
        super().paintEvent(event)

# ----------------------------------------------------------------------
# Main StreamViewer with WebSocket waiting room
# ----------------------------------------------------------------------
class StreamViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.server_url = SERVER_URL
        self.room_id = ROOM_ID
        self.token = TOKEN
        self.stream_url = None
        self.vlc_instance = None
        self.vlc_player = None
        self._is_closing = False
        self._closing_lock = QMutex()
        self._is_streaming = False
        self._connection_status = "disconnected"
        self._waiting_thread = None
        self._reconnect_timer = QTimer()
        self._reconnect_timer.timeout.connect(self._check_stream_health)
        self._reconnect_attempts = 0
        self._max_reconnect = 5
        self._last_state = None
        self._fullscreen_window = None

        # Load icons
        self.play_icon = load_svg_from_string(PLAY_SVG, 24)
        self.pause_icon = load_svg_from_string(PAUSE_SVG, 24)
        self.fullscreen_icon = load_svg_from_string(FULLSCREEN_SVG, 24)

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(900, 620)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: #1a1a1a;")

        main_widget = QWidget(self)
        main_widget.setGeometry(0, 0, self.width(), self.height())
        main_widget.setStyleSheet("background-color: transparent;")
        self.main_widget = main_widget

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Video container
        self.video_container = RoundedVideoFrame(radius=32)
        self.video_container.setMinimumHeight(380)
        self.video_container.setStyleSheet("RoundedVideoFrame { border: 1px solid rgba(255,255,255,0.1); }")
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        video_layout.addWidget(self.video_frame)
        layout.addWidget(self.video_container)

        # Status bar with no background color
        self.status_bar = NoBackgroundStatusBar()
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        status_layout.setSpacing(10)

        self.status_indicator = AnimatedStatusIndicator()
        self.status_indicator.set_status("disconnected")
        status_layout.addWidget(self.status_indicator)

        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 12px; font-weight: 500; background-color: transparent;")
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        # Play/Pause button with transparent background
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(36, 36)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet("""
            QPushButton { 
                background-color: rgba(255,255,255,0.15); 
                border-radius: 18px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: rgba(255,255,255,0.25); 
            }
            QPushButton:pressed { 
                background-color: rgba(255,255,255,0.35); 
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_stream)
        self.toggle_button.setIcon(self.play_icon)
        self.toggle_button.setIconSize(self.toggle_button.size())
        status_layout.addWidget(self.toggle_button)

        # Fullscreen button with transparent background
        self.fullscreen_button = QPushButton()
        self.fullscreen_button.setFixedSize(36, 36)
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.setStyleSheet("""
            QPushButton { 
                background-color: rgba(255,255,255,0.15); 
                border-radius: 18px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: rgba(255,255,255,0.25); 
            }
            QPushButton:pressed { 
                background-color: rgba(255,255,255,0.35); 
            }
        """)
        self.fullscreen_button.clicked.connect(self.open_fullscreen)
        self.fullscreen_button.setIcon(self.fullscreen_icon)
        self.fullscreen_button.setIconSize(self.fullscreen_button.size())
        status_layout.addWidget(self.fullscreen_button)

        layout.addWidget(self.status_bar)

    # ---- Check if room and stream already exist ----
    def check_room_status(self):
        """Check if the room exists and get stream ID if available"""
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return None
                
        url = f"{self.server_url}/api/rooms/info"
        params = {"room": self.room_id, "token": self.token}
        headers = get_auth_headers()
        session = get_insecure_session()
        try:
            print(f"🔍 Checking room status: {url}?room={self.room_id}")
            r = session.get(url, params=params, headers=headers, timeout=5)
            print(f"📊 Response status: {r.status_code}")
            print(f"📊 Response body: {r.text}")
            
            if r.status_code == 200:
                data = r.json()
                stream_id = data.get("streamId", "")
                stream_status = data.get("streamStatus", "")
                print(f"📊 Room info response: streamId='{stream_id}', status='{stream_status}'")
                
                if stream_id:
                    print(f"✅ Room exists with stream: {stream_id} (status: {stream_status})")
                    return stream_id
                else:
                    print(f"⏳ Room exists but no stream yet (status: {stream_status})")
                    return None
            elif r.status_code == 404:
                print(f"⏳ Room not found (404)")
                return None
            else:
                print(f"⏳ Room check returned status: {r.status_code}")
                return None
        except Exception as e:
            print(f"⚠️ Room check error: {e}")
            return None

    # ---- Get stream URL directly (for existing active stream) ----
    def get_stream_url_direct(self):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return None, None
                
        # First check if room exists with any stream
        stream_id = self.check_room_status()
        if stream_id:
            stream_url = f"{self.server_url}/stream/{stream_id}.ts?token={self.token}"
            print(f"✅ Using existing stream: {stream_id}")
            return stream_id, stream_url
        
        # If no stream, try the join request API (may return 202 if waiting)
        url = f"{self.server_url}/api/rooms/request"
        params = {"room": self.room_id, "stream": "default", "token": self.token}
        headers = get_auth_headers()
        session = get_insecure_session()
        try:
            r = session.get(url, params=params, headers=headers, timeout=10)
            print(f"📊 Join request response status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                stream_id = data.get("streamId", "")
                if stream_id:
                    stream_url = f"{self.server_url}/stream/{stream_id}.ts?token={self.token}"
                    return stream_id, stream_url
            elif r.status_code == 202:
                print("⏳ Room not ready yet, connecting to waiting room...")
                return None, None
        except Exception as e:
            print(f"Request error: {e}")
        return None, None

    # ---- WebSocket waiting ----
    def start_waiting_room(self):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        if self._waiting_thread:
            self._waiting_thread.stop()
            self._waiting_thread.wait(2000)
            self._waiting_thread = None
            
        self._waiting_thread = WaitingRoomThread(self.server_url, self.room_id, self.token)
        self._waiting_thread.room_ready.connect(self.on_room_ready)
        self._waiting_thread.error.connect(self.on_waiting_error)
        self._waiting_thread.start()
        self.update_status("connecting", "Waiting for room...")

    def on_room_ready(self, stream_id):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        print(f"✅ Room ready! Stream ID: {stream_id}")
        if self._waiting_thread:
            self._waiting_thread.stop()
            self._waiting_thread.wait(2000)
            self._waiting_thread = None
            
        stream_url = f"{self.server_url}/stream/{stream_id}.ts?token={self.token}"
        self.stream_url = stream_url
        
        # If fullscreen is open, update it
        if self._fullscreen_window and self._fullscreen_window.isVisible():
            self._fullscreen_window.start_playback(stream_url)
        
        self.start_vlc_playback(stream_url)

    def on_waiting_error(self, error_msg):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
        print(f"❌ Waiting room error: {error_msg}")
        self.update_status("error", "Waiting room error")
        self.stop_stream()

    # ---- VLC playback with SSL verification disabled ----
    def start_vlc_playback(self, stream_url):
        with QMutexLocker(self._closing_lock):
            if self._is_closing or not self._is_streaming:
                return
                
        self.stream_url = stream_url
        self._cleanup_vlc()
        QTimer.singleShot(150, lambda: self._init_vlc_player(stream_url))

    def _init_vlc_player(self, stream_url):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        try:
            # First, verify the stream URL is reachable (with SSL disabled)
            session = get_insecure_session()
            try:
                resp = session.head(stream_url, timeout=5)
                if resp.status_code != 200:
                    print(f"⚠️ Stream URL returned {resp.status_code}, but continuing anyway")
                else:
                    print(f"✅ Stream URL is reachable (status: {resp.status_code})")
            except Exception as e:
                print(f"⚠️ Stream URL check failed: {e}")

            # VLC instance options
            vlc_args = [
                '--no-xlib',
                '--quiet',
                '--network-caching=2000',
                '--live-caching=2000',
                '--no-video-title-show',
                '--clock-synchro=0',
                '--no-rtsp-tcp',
            ]
            self.vlc_instance = vlc.Instance(*vlc_args)
            if self.vlc_instance is None:
                raise Exception("VLC instance creation failed")

            self.vlc_player = self.vlc_instance.media_player_new()
            if self.vlc_player is None:
                raise Exception("VLC media player creation failed")

            # Set window handle
            if sys.platform == "win32":
                self.vlc_player.set_hwnd(int(self.video_frame.winId()))
            elif sys.platform == "darwin":
                self.vlc_player.set_nsobject(int(self.video_frame.winId()))
            else:
                self.vlc_player.set_xwindow(int(self.video_frame.winId()))

            # Create media and add SSL bypass options
            media = self.vlc_instance.media_new(stream_url)
            media.add_option('--http-reconnect')
            media.add_option('--http-continuous')
            media.add_option('--network-caching=2000')
            media.add_option('--live-caching=2000')

            self.vlc_player.set_media(media)

            # Play with retry
            ret = self.vlc_player.play()
            if ret == 0:
                print(f"✅ VLC playback started for {stream_url}")
                self.update_status("connected", "Live (HTTP)")
                self._reconnect_attempts = 0
                self._last_state = None
                self._reconnect_timer.start(5000)
            else:
                print(f"❌ VLC playback failed with code {ret}")
                # Try alternative approach - set media again and retry
                try:
                    time.sleep(0.5)
                    media2 = self.vlc_instance.media_new(stream_url)
                    self.vlc_player.set_media(media2)
                    ret2 = self.vlc_player.play()
                    if ret2 == 0:
                        print(f"✅ VLC playback started on retry for {stream_url}")
                        self.update_status("connected", "Live (HTTP)")
                        self._reconnect_attempts = 0
                        self._last_state = None
                        self._reconnect_timer.start(5000)
                    else:
                        self.update_status("error", f"Playback failed (code {ret})")
                        self.stop_stream()
                except:
                    self.update_status("error", f"Playback failed (code {ret})")
                    self.stop_stream()

        except Exception as e:
            print(f"VLC error: {e}")
            traceback.print_exc()
            self.update_status("error", f"VLC error: {str(e)[:30]}")
            self.stop_stream()

    # ---- Health check ----
    def _check_stream_health(self):
        with QMutexLocker(self._closing_lock):
            if self._is_closing or not self._is_streaming or not self.vlc_player:
                return
                
        try:
            state = self.vlc_player.get_state()
            
            if state != self._last_state:
                print(f"🔄 VLC state: {state}")
                self._last_state = state
            
            if state == vlc.State.Error:
                print("⚠️ VLC error state - reconnecting")
                if self._reconnect_attempts < self._max_reconnect:
                    self._reconnect_attempts += 1
                    self.update_status("connecting", f"Reconnecting ({self._reconnect_attempts}/{self._max_reconnect})...")
                    QTimer.singleShot(3000, self.start_stream)
                else:
                    self.update_status("error", "Connection lost")
                    self.stop_stream()
            elif state == vlc.State.Ended:
                print("⚠️ VLC ended - stream may have stopped")
                if self._reconnect_attempts < self._max_reconnect:
                    self._reconnect_attempts += 1
                    self.update_status("connecting", f"Reconnecting ({self._reconnect_attempts}/{self._max_reconnect})...")
                    QTimer.singleShot(3000, self.start_stream)
                else:
                    self.update_status("error", "Stream ended")
                    self.stop_stream()
            elif state == vlc.State.Playing:
                if self._reconnect_attempts > 0:
                    self._reconnect_attempts = 0
                self.update_status("connected", "Live (HTTP)")
            elif state in (vlc.State.Opening, vlc.State.Buffering):
                self.update_status("connecting", "Buffering...")
        except Exception as e:
            print(f"⚠️ Health check error: {e}")

    def _cleanup_vlc(self):
        """Clean up VLC resources"""
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        try:
            if self.vlc_player:
                try:
                    self.vlc_player.stop()
                except:
                    pass
                try:
                    self.vlc_player.release()
                except:
                    pass
                self.vlc_player = None
                
            if self.vlc_instance:
                try:
                    self.vlc_instance.release()
                except:
                    pass
                self.vlc_instance = None
                
            self._reconnect_timer.stop()
            self._last_state = None
            gc.collect()
        except Exception as e:
            print(f"⚠️ Error cleaning up VLC: {e}")

    # ---- UI status ----
    def update_status(self, status, message=None):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        self._connection_status = status
        self.status_text.setText(message if message else {
            "connected": "Live (HTTP)",
            "connecting": "Connecting...",
            "error": "Connection Error",
        }.get(status, "Disconnected"))
        self.status_indicator.set_status(status)

    # ---- Fullscreen functionality ----
    def open_fullscreen(self):
        """Open stream in fullscreen window without auto-starting"""
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        # If fullscreen window already exists, bring it to front
        if self._fullscreen_window is not None and self._fullscreen_window.isVisible():
            self._fullscreen_window.raise_()
            self._fullscreen_window.activateWindow()
            return
        
        # Create fullscreen window (does NOT auto-start playback)
        self._fullscreen_window = FullscreenStreamWindow(self)
        self._fullscreen_window.showFullScreen()
        
        # If there's an active stream URL, pass it to the fullscreen window
        if self.stream_url and self._is_streaming:
            self._fullscreen_window.start_playback(self.stream_url)
    
    def _on_fullscreen_closed(self):
        """Called when fullscreen window is closed"""
        self._fullscreen_window = None

    # ---- Stream control ----
    def toggle_stream(self):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        if self._is_streaming:
            # If fullscreen is open, close it first
            if self._fullscreen_window:
                self._fullscreen_window.close()
            self.stop_stream()
        else:
            self.start_stream()

    def start_stream(self):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        if self._is_streaming:
            return
            
        self.stop_stream()
        self._is_streaming = True
        self._reconnect_attempts = 0
        self._last_state = None
        self._update_button_icon(True)
        self.update_status("connecting", "Checking stream...")

        stream_id, stream_url = self.get_stream_url_direct()
        if stream_url:
            self.stream_url = stream_url
            # If fullscreen is open, update it
            if self._fullscreen_window and self._fullscreen_window.isVisible():
                self._fullscreen_window.start_playback(stream_url)
            self.start_vlc_playback(stream_url)
        else:
            self.start_waiting_room()

    def stop_stream(self):
        with QMutexLocker(self._closing_lock):
            if self._is_closing:
                return
                
        if not self._is_streaming and self._connection_status == "disconnected":
            return
            
        self._is_streaming = False
        self._reconnect_timer.stop()
        
        if self._waiting_thread:
            self._waiting_thread.stop()
            self._waiting_thread.wait(2000)
            self._waiting_thread = None
            
        self._cleanup_vlc()
        self.update_status("disconnected", "Stopped")
        self._update_button_icon(False)

    def _update_button_icon(self, is_playing):
        self.toggle_button.setUpdatesEnabled(False)
        if is_playing:
            self.toggle_button.setIcon(self.pause_icon)
        else:
            self.toggle_button.setIcon(self.play_icon)
        self.toggle_button.setIconSize(self.toggle_button.size())
        self.toggle_button.setUpdatesEnabled(True)

    def resizeEvent(self, event):
        if hasattr(self, 'main_widget'):
            self.main_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        """Secure close event with full cleanup"""
        print("🔒 Securely closing application...")
        
        with QMutexLocker(self._closing_lock):
            self._is_closing = True
        
        # Stop all threads
        if self._waiting_thread:
            try:
                self._waiting_thread.stop()
                self._waiting_thread.wait(2000)
            except:
                pass
            self._waiting_thread = None
        
        # Close fullscreen window if open
        if self._fullscreen_window:
            try:
                self._fullscreen_window.close()
            except:
                pass
            self._fullscreen_window = None
        
        # Clean up VLC
        self._cleanup_vlc()
        
        # Clean up timers
        try:
            self._reconnect_timer.stop()
        except:
            pass
        
        # Force garbage collection
        gc.collect()
        
        print("✅ Application closed successfully")
        event.accept()

# ============================================================================
# MAIN
# ============================================================================
def main():
    if not TOKEN or not ROOM_ID or not is_authenticated():
        print("\n❌ ERROR: Invalid token or room. Please log in first.")
        input("Press Enter to exit...")
        

    print("\n" + "="*60)
    print("  STREAM VIEWER – WebSocket Waiting Room + VLC")
    print("="*60)
    print(f"  Room: {ROOM_ID} | Server: {SERVER_URL}")
    print("="*60 + "\n")

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    viewer = StreamViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()