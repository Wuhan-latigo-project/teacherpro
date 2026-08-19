# poll.py
import sys
import json
import socket
import ssl
import threading
from queue import Queue
from PySide6.QtCore import (
    Qt, Signal, QTimer, QRect, QPoint, QObject
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QFrame, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QFontDatabase

from token_manager import get_token, get_current_room

PORT = 12345


# ============================================================
# POLL BRIDGE - For communicating with the dashboard
# ============================================================

class PollBridge(QObject):
    """Bridge to communicate poll events to the dashboard."""
    poll_received = Signal(str)      # Emitted when a new poll is received
    poll_ended = Signal()            # Emitted when a poll ends
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
        self._response_callback = None
    
    def set_response_callback(self, callback):
        """Set the callback to handle poll responses."""
        self._response_callback = callback
    
    def submit_response(self, value):
        """Submit a poll response through the bridge."""
        if self._response_callback:
            self._response_callback(value)
        else:
            print("[POLL Bridge] No response callback set")


# ============================================================
# CUSTOM HORIZONTAL SLIDER
# ============================================================

class HorizonSlider(QFrame):
    """Custom horizontal slider matching the dark blue dashboard theme."""
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 50
        self._min = 0
        self._max = 100
        self._dragging = False
        self._hovered = False
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def value(self):
        return self._value

    def setValue(self, val):
        val = max(self._min, min(self._max, val))
        if val != self._value:
            self._value = val
            self.valueChanged.emit(val)
            self.update()

    def mousePressEvent(self, event):
        if self.isEnabled():
            self._dragging = True
            self._set_value_from_pos(event.position().x())

    def mouseMoveEvent(self, event):
        if self.isEnabled():
            self._hovered = True
            if self._dragging:
                self._set_value_from_pos(event.position().x())
            self.update()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def _set_value_from_pos(self, x):
        width = self.width() - 40
        x = max(0, min(width, x - 20))
        ratio = x / width if width > 0 else 0
        self.setValue(int(ratio * (self._max - self._min) + self._min))

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)

            rect = self.rect().adjusted(20, 16, -20, -16)
            center_y = rect.center().y()

            # Background track (dark navy)
            track_rect = QRect(rect.x(), center_y - 5, rect.width(), 10)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(10, 15, 40, 200)))
            painter.drawRoundedRect(track_rect, 5, 5)

            # Filled track (dashboard blue gradient)
            fill_width = int((self._value / 100) * rect.width())
            if fill_width > 0:
                fill_rect = QRect(rect.x(), center_y - 5, fill_width, 10)
                gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
                gradient.setColorAt(0.0, QColor(4, 0, 122))      # Deep blue
                gradient.setColorAt(0.5, QColor(21, 16, 204))    # Purple-blue
                gradient.setColorAt(1.0, QColor(127, 143, 255))  # Light blue
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(fill_rect, 5, 5)

            # Thumb
            thumb_x = rect.x() + fill_width
            thumb_radius = 12 if self._dragging or self._hovered else 10

            # Thumb glow
            if self.isEnabled():
                glow = QBrush(QColor(127, 143, 255, 50 if self._dragging else 25))
                painter.setBrush(glow)
                painter.drawEllipse(QPoint(thumb_x, center_y), thumb_radius + 8, thumb_radius + 8)

            # Thumb core
            painter.setBrush(QBrush(QColor(230, 230, 255)))
            painter.setPen(QPen(QColor(4, 0, 122), 2))
            painter.drawEllipse(QPoint(thumb_x, center_y), thumb_radius, thumb_radius)
        finally:
            painter.end()


# ============================================================
# MAIN WINDOW
# ============================================================

class StudentWindow(QMainWindow):
    survey_received = Signal(dict)
    status_update = Signal(str)
    auth_result_signal = Signal(bool, str, str)

    def __init__(self, embedded=False):
        super().__init__()
        self.embedded = embedded
        self.setWindowTitle("Pulse · Student")
        self.setMinimumWidth(800)
        self.setMinimumHeight(220)
        self.resize(900, 220)

        # Network variables
        self.socket = None
        self.connected = False
        self.authenticated = False
        self.receive_queue = Queue()
        self.receive_thread = None

        # State
        self.username = None
        self.survey_active = False
        self.has_submitted = False

        # Poll Bridge
        self.bridge = PollBridge()
        self.bridge.poll_received.connect(self._on_poll_received_from_bridge)
        self.bridge.set_response_callback(self._submit_response_through_bridge)

        # Connect signals
        self.status_update.connect(self.update_status_label)
        self.auth_result_signal.connect(self.on_auth_result)
        self.survey_received.connect(self.handle_survey)

        # Setup new horizontal UI
        self.setup_ui()

        # Auth
        self.auth_token = get_token()
        self.room_name = get_current_room()

        if not self.auth_token:
            print("[POLL] No token found. Please login first.")
            self.submit_btn.setEnabled(False)
        else:
            self.connect_to_server()

        # Timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_connection)
        self.status_timer.start(5000)

    def setup_ui(self):
        """Horizontal dark UI matching the dashboard theme."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #070707;
            }
            QLabel {
                color: #f1f5f9;
                font-family: 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
            }
            QMessageBox {
                background-color: #0a0a1a;
            }
            QMessageBox QLabel {
                color: #f1f5f9;
            }
            QMessageBox QPushButton {
                background-color: #1510cc;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)

        # ── Left: Question & Info ──
        left_widget = QFrame()
        left_widget.setFixedWidth(280)
        left_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(127, 143, 255, 0.15);
                border-radius: 24px;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(24, 20, 24, 20)
        left_layout.setSpacing(8)

        # Big question text
        self.question_label = QLabel("Waiting for survey...")
        self.question_label.setWordWrap(True)
        self.question_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.question_label.setStyleSheet("""
            color: #ffffff;
            font-size: 22px;
            font-weight: 700;
            line-height: 1.3;
            background: transparent;
            border: none;
        """)
        left_layout.addWidget(self.question_label)

        # Subtitle
        self.question_sub = QLabel("Your teacher will start a survey soon.")
        self.question_sub.setWordWrap(True)
        self.question_sub.setStyleSheet("color: #7f8fff; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        left_layout.addWidget(self.question_sub)

        # User badge
        self.user_badge = QLabel("Guest")
        self.user_badge.setStyleSheet("""
            color: #94a3b8;
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        left_layout.addWidget(self.user_badge)
        left_layout.addStretch()

        main_layout.addWidget(left_widget)

        # ── Center: Slider & Value ──
        center_widget = QFrame()
        center_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(127, 143, 255, 0.15);
                border-radius: 24px;
            }
        """)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(24, 16, 24, 16)
        center_layout.setSpacing(4)

        # Big value display
        value_header = QHBoxLayout()
        self.value_display = QLabel("50")
        self.value_display.setAlignment(Qt.AlignCenter)
        self.value_display.setStyleSheet("""
            color: #7f8fff;
            font-size: 56px;
            font-weight: 800;
            font-family: 'SF Mono', 'Consolas', monospace;
            background: transparent;
            border: none;
        """)
        value_header.addWidget(self.value_display)

        percent_label = QLabel("%")
        percent_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        percent_label.setStyleSheet("color: #64748b; font-size: 18px; font-weight: 600; padding-bottom: 12px; background: transparent; border: none;")
        value_header.addWidget(percent_label)
        value_header.addStretch()
        center_layout.addLayout(value_header)

        # Slider
        self.slider = HorizonSlider()
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.setEnabled(False)
        center_layout.addWidget(self.slider)

        main_layout.addWidget(center_widget, stretch=1)

        # ── Right: Submit ──
        right_widget = QFrame()
        right_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(127, 143, 255, 0.15);
                border-radius: 24px;
            }
        """)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)

        # Submit button
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setFixedHeight(48)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #04007a, stop:1 #1510cc);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1510cc, stop:1 #3b82f6);
            }
            QPushButton:disabled {
                background: #1e1e2e;
                color: #475569;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #02004a, stop:1 #0a08aa);
            }
        """)
        self.submit_btn.clicked.connect(self.submit_response)
        self.submit_btn.setEnabled(False)
        right_layout.addWidget(self.submit_btn)

        # Reconnect button (small)
        self.reconnect_btn = QPushButton("↻")
        self.reconnect_btn.setFixedHeight(32)
        self.reconnect_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #94a3b8;
                border: 1px solid rgba(127, 143, 255, 0.1);
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #e2e8f0;
            }
        """)
        self.reconnect_btn.clicked.connect(self.manual_reconnect)
        self.reconnect_btn.setVisible(False)
        right_layout.addWidget(self.reconnect_btn)

        right_layout.addStretch()
        main_layout.addWidget(right_widget)

    def _on_slider_changed(self, value):
        self.value_display.setText(str(value))
        # Color shift based on value
        if value < 30:
            color = "#ef4444"
        elif value < 60:
            color = "#f59e0b"
        else:
            color = "#7f8fff"
        self.value_display.setStyleSheet(f"""
            color: {color};
            font-size: 56px;
            font-weight: 800;
            font-family: 'SF Mono', 'Consolas', monospace;
        """)

    def _set_status(self, status):
        """Status is logged to terminal only — no UI indicator."""
        pass

    # ─── POLL BRIDGE METHODS ─────────────────────────────────

    def _on_poll_received_from_bridge(self, question):
        """Handle poll received from bridge (for dashboard integration)."""
        print(f"[POLL Bridge] Received poll: {question[:50]}...")
        # The dashboard will handle showing the notification
        # This is just a pass-through

    def _submit_response_through_bridge(self, value):
        """Submit response through the bridge (called from dashboard)."""
        print(f"[POLL Bridge] Submitting response: {value}%")
        if self.survey_active and not self.has_submitted:
            self.slider.setValue(value)
            self.submit_response()
        else:
            print("[POLL Bridge] Cannot submit: survey not active or already submitted")

    # ─── NETWORK LOGIC ─────────────────────────────────────────────────

    def connect_to_server(self):
        """Connect to server using SSL - sends ONLY token and room."""
        def connect_thread():
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

                raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                raw_socket.settimeout(10)
                raw_socket.connect(('localhost', PORT))
                ssl_socket = context.wrap_socket(raw_socket, server_hostname='localhost')

                self.socket = ssl_socket
                self.connected = True

                auth_msg = {
                    "type": "auth",
                    "token": self.auth_token,
                    "room": self.room_name,
                    "client_type": "student"
                }
                self.send_data(auth_msg)
                print(f"[POLL] Sent auth request for room {self.room_name}")

                self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
                self.receive_thread.start()
                self.status_update.emit("connecting")

            except ConnectionRefusedError:
                self.connected = False
                self.status_update.emit("disconnected|Server not running")
            except Exception as e:
                self.connected = False
                self.status_update.emit(f"disconnected|{str(e)[:40]}")

        thread = threading.Thread(target=connect_thread, daemon=True)
        thread.start()

    def receive_loop(self):
        """Background thread for receiving data."""
        buffer = ""
        while self.connected and self.socket:
            try:
                self.socket.settimeout(30)
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    continue

                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            self.process_message(msg)
                        except json.JSONDecodeError as e:
                            print(f"[POLL] JSON decode error: {e}")
            except socket.timeout:
                if self.connected and self.authenticated:
                    self.send_data({"type": "ping"})
                continue
            except Exception as e:
                if self.connected:
                    print(f"[POLL] Receive error: {e}")
                break

        self.connected = False
        self.authenticated = False
        self.status_update.emit("disconnected|Disconnected from server")

    def process_message(self, msg):
        """Process received message."""
        msg_type = msg.get("type")
        print(f"[POLL] Received: {msg_type}")

        if msg_type == "auth_result":
            success = msg.get("success", False)
            role = msg.get("role", "")
            username = msg.get("username", "")
            self.auth_result_signal.emit(success, role, username)

        elif msg_type == "survey":
            self.survey_received.emit(msg)

        elif msg_type == "response_ack":
            self.status_update.emit("submitted|Response saved on server!")
            print("[POLL] Received response_ack from server")

        elif msg_type == "pong":
            pass

        elif msg_type == "error":
            error_msg = msg.get("message", "Unknown error")
            self.status_update.emit(f"error|{error_msg}")
            QMessageBox.warning(self, "Server Error", error_msg)

    def on_auth_result(self, success, role, username):
        """Handle authentication result."""
        if success:
            if role != "student":
                print(f"[POLL] Server error: Invalid role '{role}'")
                self.status_update.emit("error|Server error: Invalid role")
                self.disconnect()
            else:
                self.username = username
                self.authenticated = True
                self.setWindowTitle(f"Pulse · {self.username}")
                self.user_badge.setText(f"● @{self.username}")
                self.user_badge.setStyleSheet("""
                    color: #7f8fff;
                    font-size: 11px;
                    font-weight: 600;
                    background: transparent;
                    border: none;
                """)
                self.status_update.emit("connected|Authenticated")
                self.reconnect_btn.setVisible(False)
                print(f"[POLL] Authenticated as {self.username}")
        else:
            print(f"[POLL] Auth failed: {role}")
            self.status_update.emit(f"error|Auth failed: {role}")
            self.disconnect()

    def handle_survey(self, survey):
        """Handle survey message from server."""
        self.survey_active = survey["active"]

        if self.survey_active:
            # Emit signal to bridge for dashboard
            self.bridge.poll_received.emit(survey["question"])
            
            self.has_submitted = False
            self.question_label.setText(survey["question"])
            self.question_sub.setText("Drag the slider to set your understanding level.")
            
            QTimer.singleShot(10, self.adjustSize)

            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Submit")
            self.slider.setEnabled(True)
            self.slider.setValue(50)

            self.question_label.setStyleSheet("""
                color: #ffffff;
                font-size: 22px;
                font-weight: 700;
                line-height: 1.3;
            """)
            self.status_update.emit("survey|Survey active")
            print(f"[POLL] Survey active: {survey['question'][:50]}...")
        else:
            # Emit poll ended signal to bridge
            self.bridge.poll_ended.emit()
            
            if not self.has_submitted:
                self.question_label.setText("Waiting for survey...")
                self.question_sub.setText("Your teacher will start a survey soon.")
            
            QTimer.singleShot(10, self.adjustSize)

            self.submit_btn.setEnabled(False)
            self.slider.setEnabled(False)
            self.status_update.emit("connected|Waiting for next survey")

            self.question_label.setStyleSheet("""
                color: #94a3b8;
                font-size: 22px;
                font-weight: 700;
                line-height: 1.3;
            """)
            print("[POLL] Survey ended")

    def submit_response(self):
        """Submit student's understanding level."""
        if not self.survey_active:
            QMessageBox.warning(self, "No Active Survey", 
                "There is no active survey at the moment. Please wait for the teacher to start a survey.")
            return

        value = self.slider.value()

        # Check if called from bridge (already confirmed) or from button
        if not hasattr(self, '_from_bridge') or not self._from_bridge:
            reply = QMessageBox.question(self, "Confirm Submission",
                f"Submit <b>{value}%</b> as your understanding level?",
                QMessageBox.Yes | QMessageBox.No)

            if reply != QMessageBox.Yes:
                return
        else:
            self._from_bridge = False

        response = {
            "type": "response",
            "value": value
        }
        self.send_data(response)
        print(f"[POLL] Submitted response: {value}%")

        self.has_submitted = True
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("✓ Sent")
        self.slider.setEnabled(False)

        self.question_label.setText("Thank you!")
        self.question_sub.setText(f"Your response ({value}%) has been recorded.")
        QTimer.singleShot(10, self.adjustSize)
        self.status_update.emit("submitted|Response sent")

    def send_data(self, data):
        """Send JSON data to server."""
        if self.socket and self.connected:
            try:
                json_str = json.dumps(data) + '\n'
                self.socket.send(json_str.encode('utf-8'))
            except Exception as e:
                print(f"[POLL] Send error: {e}")
                self.connected = False

    def disconnect(self):
        """Disconnect from server."""
        self.connected = False
        self.authenticated = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def manual_reconnect(self):
        """Manually reconnect to server."""
        self.disconnect()
        print("[POLL] Manual reconnect...")
        self.reconnect_btn.setVisible(False)
        self.connect_to_server()

    def update_status_label(self, message):
        """Update status dot only — all logs go to terminal."""
        if "|" in message:
            status, text = message.split("|", 1)
        else:
            status = message
            text = ""

        self._set_status(status)

        # Log everything to terminal, never to UI
        if text:
            print(f"[POLL] Status: {text}")

        if status == "disconnected":
            self.reconnect_btn.setVisible(True)

    def check_connection(self):
        """Check connection status."""
        if not self.connected and self.auth_token and not self.authenticated:
            self._set_status("disconnected")
            self.reconnect_btn.setVisible(True)

    def closeEvent(self, event):
        """Handle window close event."""
        self.disconnect()
        event.accept()


# ============================================================
# POLL WRAPPER - For embedding in the dashboard
# ============================================================

class PollWidget(QWidget):
    """Wrapper widget for embedding the poll in the dashboard."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        
        # Create the student window but embed it
        self.student_window = StudentWindow(embedded=True)
        self.student_window.setParent(self)
        self.student_window.setWindowFlags(Qt.Widget)
        self.student_window.setStyleSheet("background: transparent;")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.student_window)
        
        # Store bridge for dashboard communication
        self.bridge = PollBridge()
    
    def get_bridge(self):
        """Return the poll bridge for dashboard communication."""
        return self.bridge
    
    def shutdown(self):
        """Clean shutdown."""
        if hasattr(self, 'student_window'):
            if hasattr(self.student_window, 'close'):
                self.student_window.close()
            self.student_window = None


# ============================================================
# MAIN - Standalone mode
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    font = QFont("Inter", 10)
    if not QFontDatabase.hasFamily("Inter"):
        font = QFont("SF Pro Display", 10)
    if not QFontDatabase.hasFamily("SF Pro Display"):
        font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = StudentWindow()
    window.show()
    sys.exit(app.exec())