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

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from token_manager import get_current_room, get_token, is_authenticated, get_user_data, get_auth_headers

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import QThread, Signal, QTimer, Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QIcon, QPixmap
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
    sys.exit(1)

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
        print(f"⚠️ WebSocket error: {error}")
        if self._running:
            self.error.emit(f"WebSocket error: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔌 WebSocket closed (code: {close_status_code}, msg: {close_msg})")
        if self._running and not self._ready_emitted:
            self.error.emit("WebSocket connection closed unexpectedly")

    def stop(self):
        self._running = False
        if self.ws:
            try:
                self.ws.close()
            except:
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
        self._is_streaming = False
        self._connection_status = "disconnected"
        self._waiting_thread = None
        self._reconnect_timer = QTimer()
        self._reconnect_timer.timeout.connect(self._check_stream_health)
        self._reconnect_attempts = 0
        self._max_reconnect = 5
        self._last_state = None

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(900, 620)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
        self.video_container.setStyleSheet("RoundedVideoFrame { border: 1px solid rgba(255,255,255,0.2); }")
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        video_layout.addWidget(self.video_frame)
        layout.addWidget(self.video_container)

        # Status bar
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet("QFrame { background-color: #0077be; border-radius: 20px; }")
        self.status_bar.setFixedHeight(40)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        status_layout.setSpacing(10)

        self.status_indicator = AnimatedStatusIndicator()
        self.status_indicator.set_status("disconnected")
        status_layout.addWidget(self.status_indicator)

        self.status_text = QLabel("Disconnected")
        self.status_text.setStyleSheet("color: white; font-size: 12px; font-weight: 500;")
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        room_badge = QLabel(f"🏠 {self.room_id}")
        room_badge.setStyleSheet("color: #AAAAAA; background-color: rgba(255,255,255,0.1); border-radius: 12px; padding: 4px 10px;")
        status_layout.addWidget(room_badge)
        status_layout.addSpacing(8)

        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(36, 36)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.2); border-radius: 18px; border: none; }
            QPushButton:hover { background-color: rgba(255,255,255,0.3); }
            QPushButton:pressed { background-color: rgba(255,255,255,0.4); }
        """)
        self.toggle_button.clicked.connect(self.toggle_stream)

        play_icon = load_svg_icon("play.svg", 24)
        stop_icon = load_svg_icon("stop.svg", 24)
        self.play_icon = play_icon if not play_icon.isNull() else QIcon()
        self.stop_icon = stop_icon if not stop_icon.isNull() else QIcon()
        self.toggle_button.setIcon(self.play_icon)
        self.toggle_button.setIconSize(self.toggle_button.size())
        status_layout.addWidget(self.toggle_button)

        layout.addWidget(self.status_bar)

    # ---- Check if room and stream already exist ----
    def check_room_status(self):
        """Check if the room exists and get stream ID if available"""
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
        if self._waiting_thread:
            self._waiting_thread.stop()
            self._waiting_thread.wait()
            self._waiting_thread = None
        self._waiting_thread = WaitingRoomThread(self.server_url, self.room_id, self.token)
        self._waiting_thread.room_ready.connect(self.on_room_ready)
        self._waiting_thread.error.connect(self.on_waiting_error)
        self._waiting_thread.start()
        self.update_status("connecting", "Waiting for room...")

    def on_room_ready(self, stream_id):
        print(f"✅ Room ready! Stream ID: {stream_id}")
        if self._waiting_thread:
            self._waiting_thread.stop()
            self._waiting_thread.wait()
            self._waiting_thread = None
        stream_url = f"{self.server_url}/stream/{stream_id}.ts?token={self.token}"
        self.start_vlc_playback(stream_url)

    def on_waiting_error(self, error_msg):
        print(f"❌ Waiting room error: {error_msg}")
        self.update_status("error", "Waiting room error")
        self.stop_stream()

    # ---- VLC playback with SSL verification disabled ----
    def start_vlc_playback(self, stream_url):
        if self._is_closing or not self._is_streaming:
            return
        self._cleanup_vlc()
        QTimer.singleShot(150, lambda: self._init_vlc_player(stream_url))

    def _init_vlc_player(self, stream_url):
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
            # (SSL/TLS is handled by installing the server's cert.pem into the
            # system's trusted root store, not via libVLC flags — VLC has no
            # supported option to bypass certificate verification.)
            vlc_args = [
                '--no-xlib',
                '--quiet',
                '--network-caching=2000',     # Increased caching for better stability
                '--live-caching=2000',        # Increased live caching
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
            self.update_status("error", f"VLC error: {str(e)[:30]}")
            self.stop_stream()

    # ---- Health check ----
    def _check_stream_health(self):
        if not self._is_streaming or not self.vlc_player:
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
        if self.vlc_player:
            try:
                self.vlc_player.stop()
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
        self._last_state = None
        gc.collect()

    # ---- UI status ----
    def update_status(self, status, message=None):
        self._connection_status = status
        self.status_text.setText(message if message else {
            "connected": "Live (HTTP)",
            "connecting": "Connecting...",
            "error": "Connection Error",
        }.get(status, "Disconnected"))
        self.status_indicator.set_status(status)

    # ---- Stream control ----
    def toggle_stream(self):
        if self._is_streaming:
            self.stop_stream()
        else:
            self.start_stream()

    def start_stream(self):
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
            self.start_vlc_playback(stream_url)
        else:
            self.start_waiting_room()

    def stop_stream(self):
        if not self._is_streaming and self._connection_status == "disconnected":
            return
        self._is_streaming = False
        self._reconnect_timer.stop()
        if self._waiting_thread:
            self._waiting_thread.stop()
            self._waiting_thread.wait()
            self._waiting_thread = None
        self._cleanup_vlc()
        self.update_status("disconnected", "Stopped")
        self._update_button_icon(False)

    def _update_button_icon(self, is_playing):
        self.toggle_button.setUpdatesEnabled(False)
        if is_playing:
            if not self.stop_icon.isNull():
                self.toggle_button.setIcon(self.stop_icon)
            else:
                self.toggle_button.setText("⏹️")
        else:
            if not self.play_icon.isNull():
                self.toggle_button.setIcon(self.play_icon)
            else:
                self.toggle_button.setText("▶️")
        self.toggle_button.setIconSize(self.toggle_button.size())
        self.toggle_button.setUpdatesEnabled(True)

    def resizeEvent(self, event):
        if hasattr(self, 'main_widget'):
            self.main_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        self._is_closing = True
        self.stop_stream()
        event.accept()

# ============================================================================
# MAIN
# ============================================================================
def main():
    if not TOKEN or not ROOM_ID or not is_authenticated():
        print("\n❌ ERROR: Invalid token or room. Please log in first.")
        input("Press Enter to exit...")
        sys.exit(1)

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