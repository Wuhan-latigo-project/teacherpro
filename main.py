import sys
import os
import io
import threading
import time

# ============================================================
# STEP 0: Show tkinter Splash Screen with Threading & Rounded Corners
# ============================================================
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['ABSL_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'

_tk_splash = None
_tk_root = None
_splash_running = False
_splash_thread = None

def show_tkinter_splash():
    """Create and show tkinter splash screen with rounded corners in a separate thread."""
    global _tk_splash, _tk_root, _splash_running
    
    def splash_thread_func():
        global _tk_splash, _tk_root, _splash_running
        
        try:
            import tkinter as tk
            from PIL import Image, ImageDraw, ImageTk
            
            # Create root window
            _tk_root = tk.Tk()
            _tk_root.overrideredirect(True)
            _tk_root.attributes('-topmost', True)
            # Use transparent color for rounded corners
            _tk_root.attributes('-transparentcolor', '#000001')
            _tk_root.configure(bg='#000001')

            # Load logo
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latigo.png")
            logo_img = None
            img_w, img_h = 400, 300  # default size

            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path).convert('RGBA')
                    img_w, img_h = logo_img.size
                    # Limit size
                    max_w, max_h = 500, 400
                    if img_w > max_w or img_h > max_h:
                        ratio = min(max_w/img_w, max_h/img_h)
                        new_w = int(img_w*ratio)
                        new_h = int(img_h*ratio)
                        logo_img = logo_img.resize((new_w, new_h), Image.LANCZOS)
                        img_w, img_h = new_w, new_h
                except Exception as e:
                    print(f"⚠️ Could not load logo: {e}")
                    logo_img = None

            # Create rounded rectangle image with transparent corners
            corner_radius = 25
            rounded_img = Image.new('RGBA', (img_w, img_h), (0,0,0,0))
            draw = ImageDraw.Draw(rounded_img)
            draw.rounded_rectangle((0, 0, img_w, img_h), radius=corner_radius, fill=(255,255,255,255))

            # Paste logo centered with padding
            if logo_img:
                padding = 20
                max_w = img_w - 2*padding
                max_h = img_h - 2*padding
                logo_resized = logo_img.copy()
                logo_resized.thumbnail((max_w, max_h), Image.LANCZOS)
                x = (img_w - logo_resized.width)//2
                y = (img_h - logo_resized.height)//2
                rounded_img.paste(logo_resized, (x, y), logo_resized)
            else:
                # Fallback: draw text on the rounded image
                draw.text((img_w//2, img_h//2), "📱 Latigo", fill=(0,0,0), anchor="mm")

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(rounded_img)

            # Label to display the rounded image
            label = tk.Label(_tk_root, image=photo, borderwidth=0, bg='#000001')
            label.pack(fill=tk.BOTH, expand=True)
            label.image = photo  # keep reference

            # Add status text at bottom (on top of the image)
            status_label = tk.Label(
                _tk_root,
                text="Initializing...",
                font=("Arial", 10),
                fg="#666666",
                bg='white'
            )
            status_label.place(relx=0.5, rely=0.95, anchor='s')

            # Center window on screen
            screen_w = _tk_root.winfo_screenwidth()
            screen_h = _tk_root.winfo_screenheight()
            x = (screen_w - img_w)//2
            y = (screen_h - img_h)//2
            _tk_root.geometry(f"{img_w}x{img_h}+{x}+{y}")

            # Force window to appear
            _tk_root.update_idletasks()
            _tk_root.deiconify()
            _tk_root.lift()
            _tk_root.focus_force()
            _tk_root.update()

            _splash_running = True
            _tk_splash = _tk_root
            print("✅ Splash with rounded corners shown")

            # Start tkinter main loop
            _tk_root.mainloop()

        except Exception as e:
            print(f"⚠️ Splash error: {e}")
            import traceback
            traceback.print_exc()
            _splash_running = False
            _tk_splash = None

    # Start splash in daemon thread
    _splash_thread = threading.Thread(target=splash_thread_func, daemon=True)
    _splash_thread.start()
    time.sleep(0.3)
    return True

def _update_splash(text):
    """Update status text on splash screen (thread-safe)."""
    global _tk_root, _splash_running
    if not _splash_running or _tk_root is None:
        return
    try:
        def update():
            try:
                for child in _tk_root.winfo_children():
                    if isinstance(child, tk.Label):
                        # Check if it's the status label at bottom
                        try:
                            if child.place_info().get('rely') == '0.95':
                                child.config(text=text)
                                _tk_root.update_idletasks()
                                break
                        except:
                            pass
            except Exception:
                pass
        _tk_root.after(0, update)
    except Exception:
        pass

def _close_splash():
    """Close splash screen safely."""
    global _tk_root, _splash_running
    if _tk_root:
        try:
            _splash_running = False
            _tk_root.after(0, _tk_root.destroy)
            _tk_root = None
            print("✅ Splash closed")
        except Exception as e:
            print(f"⚠️ Error closing splash: {e}")

# Show splash at startup
show_tkinter_splash()

# ============================================================
# STEP 1: Load MediaPipe (while splash is visible)
# ============================================================
_update_splash("Loading MediaPipe...")

# FIXED: Properly capture and restore stderr
_stderr_backup = sys.stderr
sys.stderr = io.StringIO()

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python.vision import hand_landmarker, face_landmarker
    from mediapipe.tasks.python.vision.core import vision_task_running_mode
    MEDIAPIPE_AVAILABLE = True
    _update_splash("✅ MediaPipe loaded")
    print("✅ MediaPipe loaded successfully")
except ImportError as e:
    print(f"❌ MediaPipe import error: {e}")
    print("   Try: pip install mediapipe==0.10.8")
    MEDIAPIPE_AVAILABLE = False
    mp = None
    python = None
    hand_landmarker = None
    face_landmarker = None
    vision_task_running_mode = None
except Exception as e:
    print(f"❌ MediaPipe load error: {e}")
    MEDIAPIPE_AVAILABLE = False
    mp = None
    python = None
    hand_landmarker = None
    face_landmarker = None
    vision_task_running_mode = None

# FIXED: Safely get stderr content and restore
tf_warnings = sys.stderr.getvalue()
sys.stderr.close()  # Close the StringIO
sys.stderr = _stderr_backup
print(f"📋 Stderr captured: {len(tf_warnings)} bytes")

# ============================================================
# STEP 2: Continue loading remaining libraries
# ============================================================
_update_splash("Loading communication modules...")

import socket
import ssl
import json
import time
import math
import cv2
import numpy as np
from collections import deque
from datetime import datetime
from threading import Thread, Event
from cryptography.fernet import Fernet

_update_splash("Loading FlatBuffers...")
# ... rest of your code ...
# FlatBuffers
try:
    import flatbuffers
    try:
        from Attention.LoginRequest import LoginRequest
        from Attention.LoginResponse import LoginResponse
        from Attention.AttentionData import AttentionData
        from Attention.AttentionAnalysis import AttentionAnalysis
        from Attention.AudioMessage import AudioMessage
        from Attention.PermissionRequest import PermissionRequest
        from Attention.PermissionResponse import PermissionResponse
        from Attention.HandRaise import HandRaise
        from Attention.TextMessage import TextMessage
        from Attention.Envelope import Envelope
        from Attention.AbsentDetection import AbsentDetection
        from Attention.LowAttentionDetection import LowAttentionDetection
        FLATBUFFERS_AVAILABLE = True
        print("✅ FlatBuffers loaded successfully (explicit imports)")
    except ImportError:
        from Attention import (
            LoginRequest, LoginResponse, AttentionData,
            AttentionAnalysis, AudioMessage, PermissionRequest,
            PermissionResponse, HandRaise, TextMessage, Envelope,
            AbsentDetection, LowAttentionDetection
        )
        FLATBUFFERS_AVAILABLE = True
        print("✅ FlatBuffers loaded successfully (package import)")
except ImportError as e:
    print(f"⚠️ FlatBuffers import error: {e}")
    FLATBUFFERS_AVAILABLE = False
    flatbuffers = None
    LoginRequest = None
    LoginResponse = None
    AttentionData = None
    AttentionAnalysis = None
    AudioMessage = None
    PermissionRequest = None
    PermissionResponse = None
    HandRaise = None
    TextMessage = None
    Envelope = None
    AbsentDetection = None
    LowAttentionDetection = None

_update_splash("Loading PySide6...")
print("⏳ Loading PySide6...")

# NOW it's safe to import PySide6 (after MediaPipe is fully loaded)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QUrl, Slot, QEvent,
    QRectF, QPointF, QThreadPool, QRunnable, QMetaObject, Q_ARG
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QMessageBox, QHBoxLayout,
    QScrollArea, QFrame, QSizePolicy, QStackedWidget, QProgressBar, QDialog
)
from PySide6.QtGui import (
    QColor, QPalette, QPixmap, QPainter, QPainterPath, QBrush, QPen, QFont,
    QLinearGradient, QIcon
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

_update_splash("Loading audio libraries...")
print("⏳ Loading audio libraries...")

# Audio
import sounddevice as sd
import soundfile as sf
import shutil

_update_splash("Loading custom modules...")
print("⏳ Loading custom modules...")

# Custom imports with safe fallback
try:
    from audio_message_widget import AudioMessageWidget
except ImportError:
    print("⚠️ audio_message_widget not found, creating placeholder")
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
    
    class AudioMessageWidget(QWidget):
        def __init__(self, filename, username, main_window=None, cache=None):
            super().__init__()
            self.filename = filename
            self.username = username
            layout = QVBoxLayout(self)
            label = QLabel(f"🎵 Audio from {username}")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            self.play_btn = QPushButton("▶ Play")
            self.play_btn.clicked.connect(self.start_playback)
            layout.addWidget(self.play_btn)
            self.playback_started = False
        
        def start_playback(self):
            self.playback_started = True
            self.play_btn.setText("⏹ Stop")
            print(f"Playing audio from {self.username}: {self.filename}")
        
        def stop_playback(self):
            self.playback_started = False
            self.play_btn.setText("▶ Play")

from token_manager import get_current_room, get_token, get_username

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from notification import notification_system as notification
except ImportError:
    print("⚠️ notification module not found, creating dummy")
    class DummyNotification:
        @staticmethod
        def show_notification(*args, **kwargs):
            pass
    notification = DummyNotification()

_update_splash("Getting user credentials...")
print("⏳ Getting user credentials...")

# ============================================================
# ========== GET TOKEN AND ROOM ==========
# ============================================================
ROOM_ID = get_current_room()
TOKEN = get_token()
USERNAME = get_username()

if not TOKEN or not ROOM_ID:
    print("⚠️ WARNING: No valid token or room found in token_manager!")
    print("   Chat module will be disabled until login.")
    ROOM_ID = None
    TOKEN = None
    USERNAME = None
else:
    print(f"✅ Student chat module loaded with Room: {ROOM_ID}, Username: {USERNAME}")

profile_server_url = 'https://localhost:8443'

# ============================================================
# ========== 4. أدوات FlatBuffers (FIXED) ==========
# ============================================================

if FLATBUFFERS_AVAILABLE:

    def build_attention_data(username, value, timestamp):
        """بناء بيانات الانتباه باستخدام FlatBuffers"""
        try:
            builder = flatbuffers.Builder(1024)
            
            username_off = builder.CreateString(username)
            timestamp_off = builder.CreateString(timestamp)
            
            if hasattr(AttentionData, 'AttentionDataStart'):
                AttentionData.AttentionDataStart(builder)
                AttentionData.AttentionDataAddUsername(builder, username_off)
                AttentionData.AttentionDataAddValue(builder, value)
                AttentionData.AttentionDataAddTimestamp(builder, timestamp_off)
                attention = AttentionData.AttentionDataEnd(builder)
                
                builder.Finish(attention)
                return bytes(builder.Output())
            else:
                print("⚠️ AttentionData FlatBuffers methods not available, using JSON fallback")
                return json.dumps({'username': username, 'value': value, 'timestamp': timestamp}).encode('utf-8')
        except Exception as e:
            print(f"⚠️ Error building attention data: {e}, using JSON fallback")
            return json.dumps({'username': username, 'value': value, 'timestamp': timestamp}).encode('utf-8')

    def build_permission_request(student, timestamp):
        """بناء طلب إذن باستخدام FlatBuffers"""
        try:
            builder = flatbuffers.Builder(1024)
            
            student_off = builder.CreateString(student)
            timestamp_off = builder.CreateString(timestamp)
            
            if hasattr(PermissionRequest, 'PermissionRequestStart'):
                PermissionRequest.PermissionRequestStart(builder)
                PermissionRequest.PermissionRequestAddStudent(builder, student_off)
                PermissionRequest.PermissionRequestAddTimestamp(builder, timestamp_off)
                req = PermissionRequest.PermissionRequestEnd(builder)
                
                builder.Finish(req)
                return bytes(builder.Output())
            elif hasattr(PermissionRequest, 'Start'):
                PermissionRequest.Start(builder)
                PermissionRequest.AddStudent(builder, student_off)
                PermissionRequest.AddTimestamp(builder, timestamp_off)
                req = PermissionRequest.End(builder)
                
                builder.Finish(req)
                return bytes(builder.Output())
            else:
                print("⚠️ PermissionRequest FlatBuffers methods not available, using JSON fallback")
                return json.dumps({'student': student, 'timestamp': timestamp}).encode('utf-8')
        except Exception as e:
            print(f"⚠️ Error building permission request: {e}, using JSON fallback")
            return json.dumps({'student': student, 'timestamp': timestamp}).encode('utf-8')

    def build_audio_message(username, filename, file_data):
        """بناء رسالة صوتية باستخدام FlatBuffers"""
        try:
            builder = flatbuffers.Builder(1024)
            
            username_off = builder.CreateString(username)
            filename_off = builder.CreateString(filename)
            data_off = builder.CreateByteVector(file_data)
            
            if hasattr(AudioMessage, 'AudioMessageStart'):
                AudioMessage.AudioMessageStart(builder)
                AudioMessage.AudioMessageAddUsername(builder, username_off)
                AudioMessage.AudioMessageAddFilename(builder, filename_off)
                AudioMessage.AudioMessageAddFileData(builder, data_off)
                audio = AudioMessage.AudioMessageEnd(builder)
                
                builder.Finish(audio)
                return bytes(builder.Output())
            else:
                print("⚠️ AudioMessage FlatBuffers methods not available, using JSON fallback")
                return json.dumps({'username': username, 'filename': filename}).encode('utf-8')
        except Exception as e:
            print(f"⚠️ Error building audio message: {e}, using JSON fallback")
            return json.dumps({'username': username, 'filename': filename}).encode('utf-8')

    def build_hand_raise(username, timestamp):
        """بناء رسالة رفع اليد باستخدام FlatBuffers"""
        try:
            builder = flatbuffers.Builder(1024)
            
            username_off = builder.CreateString(username)
            timestamp_off = builder.CreateString(timestamp)
            
            if hasattr(HandRaise, 'HandRaiseStart'):
                HandRaise.HandRaiseStart(builder)
                HandRaise.HandRaiseAddUsername(builder, username_off)
                HandRaise.HandRaiseAddTimestamp(builder, timestamp_off)
                hand = HandRaise.HandRaiseEnd(builder)
                
                builder.Finish(hand)
                return bytes(builder.Output())
            else:
                print("⚠️ HandRaise FlatBuffers methods not available, using JSON fallback")
                return json.dumps({'username': username, 'timestamp': timestamp}).encode('utf-8')
        except Exception as e:
            print(f"⚠️ Error building hand raise: {e}, using JSON fallback")
            return json.dumps({'username': username, 'timestamp': timestamp}).encode('utf-8')

    def build_text_message(username, content, timestamp):
        """بناء رسالة نصية باستخدام FlatBuffers"""
        try:
            builder = flatbuffers.Builder(1024)
            
            username_off = builder.CreateString(username)
            content_off = builder.CreateString(content)
            timestamp_off = builder.CreateString(timestamp)
            
            if hasattr(TextMessage, 'TextMessageStart'):
                TextMessage.TextMessageStart(builder)
                TextMessage.TextMessageAddUsername(builder, username_off)
                TextMessage.TextMessageAddContent(builder, content_off)
                TextMessage.TextMessageAddTimestamp(builder, timestamp_off)
                text = TextMessage.TextMessageEnd(builder)
                
                builder.Finish(text)
                return bytes(builder.Output())
            else:
                print("⚠️ TextMessage FlatBuffers methods not available, using JSON fallback")
                return json.dumps({'username': username, 'content': content, 'timestamp': timestamp}).encode('utf-8')
        except Exception as e:
            print(f"⚠️ Error building text message: {e}, using JSON fallback")
            return json.dumps({'username': username, 'content': content, 'timestamp': timestamp}).encode('utf-8')

    def build_envelope(msg_type, payload):
        """بناء غلاف للرسالة باستخدام FlatBuffers"""
        try:
            builder = flatbuffers.Builder(1024)
            
            msg_type_off = builder.CreateString(msg_type)
            if isinstance(payload, bytearray):
                payload = bytes(payload)
            payload_off = builder.CreateByteVector(payload)
            
            if hasattr(Envelope, 'EnvelopeStart'):
                Envelope.EnvelopeStart(builder)
                Envelope.EnvelopeAddMsgType(builder, msg_type_off)
                Envelope.EnvelopeAddPayload(builder, payload_off)
                envelope = Envelope.EnvelopeEnd(builder)
                
                builder.Finish(envelope)
                return bytes(builder.Output())
            else:
                print("⚠️ Envelope FlatBuffers methods not available, using raw payload")
                return payload
        except Exception as e:
            print(f"⚠️ Error building envelope: {e}, using raw payload")
            return payload

    def parse_attention_analysis(data):
        """تحليل بيانات تحليل الانتباه من FlatBuffers"""
        try:
            try:
                envelope = Envelope.EnvelopeGetRootAs(data, 0)
                inner_type = envelope.MsgType().decode() if envelope.MsgType() else ''
                if inner_type == 'ATTENTION_ANALYSIS':
                    payload = envelope.PayloadAsNumpy().tobytes() if envelope.PayloadLength() > 0 else b''
                    if payload:
                        analysis = AttentionAnalysis.AttentionAnalysisGetRootAs(payload, 0)
                    else:
                        return None
                else:
                    analysis = AttentionAnalysis.AttentionAnalysisGetRootAs(data, 0)
            except:
                analysis = AttentionAnalysis.AttentionAnalysisGetRootAs(data, 0)
            
            result = {
                'timestamp': analysis.Timestamp().decode() if analysis.Timestamp() else '',
                'room': analysis.Room().decode() if analysis.Room() else '',
                'avg_percentage': analysis.AvgPercentage(),
                'student_count': analysis.StudentCount(),
                'students': [],
                'attention_values': [],
                'absent_minded': [],
                'low_attention': []
            }
            
            for i in range(analysis.StudentsLength()):
                result['students'].append(analysis.Students(i).decode())
            
            for i in range(analysis.AttentionValuesLength()):
                result['attention_values'].append(analysis.AttentionValues(i))
            
            for i in range(analysis.AbsentMindedLength()):
                absent = analysis.AbsentMinded(i)
                result['absent_minded'].append({
                    'username': absent.Username().decode() if absent.Username() else '',
                    'value': absent.Value(),
                    'mz_score': absent.MzScore(),
                    'severity': absent.Severity().decode() if absent.Severity() else '',
                    'detection_count': absent.DetectionCount(),
                    'timestamp': absent.Timestamp().decode() if absent.Timestamp() else ''
                })
            
            for i in range(analysis.LowAttentionLength()):
                low = analysis.LowAttention(i)
                result['low_attention'].append({
                    'username': low.Username().decode() if low.Username() else '',
                    'value': low.Value(),
                    'severity': low.Severity().decode() if low.Severity() else '',
                    'detection_count': low.DetectionCount(),
                    'timestamp': low.Timestamp().decode() if low.Timestamp() else ''
                })
            
            return result
        except Exception as e:
            print(f"Error parsing attention analysis: {e}")
            return None

    def parse_permission_response(data):
        """تحليل رد الإذن من FlatBuffers"""
        try:
            resp = PermissionResponse.PermissionResponseGetRootAs(data, 0)
            return {
                'accept': resp.Accept(),
                'countdown': resp.Countdown()
            }
        except Exception as e:
            print(f"Error parsing permission response: {e}")
            return None

    def parse_audio_message(data):
        """تحليل رسالة صوتية من FlatBuffers"""
        try:
            try:
                envelope = Envelope.EnvelopeGetRootAs(data, 0)
                inner_type = envelope.MsgType().decode() if envelope.MsgType() else ''
                if inner_type == 'AUDIO_MESSAGE':
                    payload = envelope.PayloadAsNumpy().tobytes() if envelope.PayloadLength() > 0 else b''
                    if payload:
                        audio = AudioMessage.AudioMessageGetRootAs(payload, 0)
                    else:
                        return None
                else:
                    audio = AudioMessage.AudioMessageGetRootAs(data, 0)
            except:
                audio = AudioMessage.AudioMessageGetRootAs(data, 0)
            
            return {
                'username': audio.Username().decode() if audio.Username() else '',
                'filename': audio.Filename().decode() if audio.Filename() else '',
                'file_data': audio.FileDataAsNumpy().tobytes() if audio.FileDataLength() > 0 else b''
            }
        except Exception as e:
            print(f"Error parsing audio message: {e}")
            return None

else:
    # Fallback: استخدام JSON
    def build_attention_data(username, value, timestamp):
        return json.dumps({'username': username, 'value': value, 'timestamp': timestamp}).encode('utf-8')
    
    def build_permission_request(student, timestamp):
        return json.dumps({'student': student, 'timestamp': timestamp}).encode('utf-8')
    
    def build_audio_message(username, filename, file_data):
        return json.dumps({'username': username, 'filename': filename}).encode('utf-8')
    
    def build_hand_raise(username, timestamp):
        return json.dumps({'username': username, 'timestamp': timestamp}).encode('utf-8')
    
    def build_text_message(username, content, timestamp):
        return json.dumps({'username': username, 'content': content, 'timestamp': timestamp}).encode('utf-8')
    
    def build_envelope(msg_type, payload):
        if isinstance(payload, str):
            return payload.encode('utf-8')
        return payload
    
    def parse_attention_analysis(data):
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return None
    
    def parse_permission_response(data):
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return None
    
    def parse_audio_message(data):
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return None

# ============================================================
# ========== 5. كود dara.py المدمج ==========
# ============================================================

HAND_MODEL_PATH = 'hand_landmarker.task'
FACE_MODEL_PATH = 'face_landmarker.task'

WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

LEFT_EYE = 33
RIGHT_EYE = 263
LEFT_EYE_INNER = 133
RIGHT_EYE_INNER = 362
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
LEFT_EYE_LEFT_POINT = 133
RIGHT_EYE_RIGHT_POINT = 263

EYE_LEVEL_OFFSET = 10
STABILITY_TIME = 2.5
STABILITY_RADIUS = 30
EYE_CLOSURE_THRESHOLD = 0.10
EYE_CLOSURE_FRAMES = 5
EYE_OPEN_EAR_BASELINE = 0.35

# ====== CombinedDetectionThread ======
class CombinedDetectionThread(QThread):
    update_signal = Signal(dict, dict, list, float, str, str, bool, float, float)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.cap = None
        self.hand_landmarker = None
        self.face_landmarker = None
        
        self.hand_tracking = {
            'Left': {
                'is_raised': False,
                'stable_start_time': None,
                'last_positions': deque(maxlen=30),
                'current_stable': False,
                'raise_confirmed': False,
                'last_confirmed_time': 0,
                'progress': 0
            },
            'Right': {
                'is_raised': False,
                'stable_start_time': None,
                'last_positions': deque(maxlen=30),
                'current_stable': False,
                'raise_confirmed': False,
                'last_confirmed_time': 0,
                'progress': 0
            }
        }
        self.cooldown_period = 3.0
        self.eye_closure_counter = 0
        self.eyes_closed = False
        self.last_ear = 0.0
        self.closure_percentage = 0.0
        
    def setup_cameras(self):
        global MEDIAPIPE_AVAILABLE, mp, python, hand_landmarker, face_landmarker, vision_task_running_mode
        
        if not MEDIAPIPE_AVAILABLE:
            print("❌ MediaPipe not available")
            return
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("❌ Cannot open camera")
            return
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        try:
            hand_base_options = python.BaseOptions(model_asset_path=HAND_MODEL_PATH)
            hand_options = hand_landmarker.HandLandmarkerOptions(
                base_options=hand_base_options,
                num_hands=2,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                running_mode=vision_task_running_mode.VisionTaskRunningMode.VIDEO
            )
            self.hand_landmarker = hand_landmarker.HandLandmarker.create_from_options(hand_options)
            
            face_base_options = python.BaseOptions(model_asset_path=FACE_MODEL_PATH)
            face_options = face_landmarker.FaceLandmarkerOptions(
                base_options=face_base_options,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1,
                running_mode=vision_task_running_mode.VisionTaskRunningMode.VIDEO
            )
            self.face_landmarker = face_landmarker.FaceLandmarker.create_from_options(face_options)
            
            print("✅ Camera and models initialized successfully")
            
        except Exception as e:
            print(f"Error loading models: {e}")
            self.hand_landmarker = None
            self.face_landmarker = None
    
    def get_eye_level(self, face_landmarks, w, h):
        if not face_landmarks:
            return None
        
        eye_points = [
            face_landmarks[LEFT_EYE],
            face_landmarks[RIGHT_EYE],
            face_landmarks[LEFT_EYE_INNER],
            face_landmarks[RIGHT_EYE_INNER]
        ]
        
        avg_eye_y = sum([lm.y for lm in eye_points]) / len(eye_points)
        eye_y_pixels = avg_eye_y * h
        
        min_y = float('inf')
        max_y = float('-inf')
        for lm in face_landmarks:
            y = lm.y * h
            min_y = min(min_y, y)
            max_y = max(max_y, y)
        
        return {
            'eye_y': eye_y_pixels,
            'face_height': max_y - min_y,
            'face_top': min_y,
            'face_bottom': max_y
        }
    
    def is_hand_open(self, landmarks):
        finger_tips = [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        finger_mcps = [5, 9, 13, 17]
        
        open_fingers = 0
        for tip, mcp in zip(finger_tips, finger_mcps):
            tip_y = landmarks[tip].y
            mcp_y = landmarks[mcp].y
            if tip_y < mcp_y - 0.02:
                open_fingers += 1
        
        thumb_y = landmarks[THUMB_TIP].y
        wrist_y = landmarks[WRIST].y
        if thumb_y < wrist_y - 0.02:
            open_fingers += 1
            
        return open_fingers >= 3
    
    def is_hand_raised(self, hand_landmarks, face_bounds, w, h):
        if not face_bounds or not hand_landmarks:
            return False
        
        wrist_y = hand_landmarks[WRIST].y * h
        eye_level = face_bounds['eye_y']
        
        threshold_y = eye_level - EYE_LEVEL_OFFSET
        is_above_eyes = wrist_y < threshold_y
        is_open = self.is_hand_open(hand_landmarks)
        
        return is_above_eyes and is_open
    
    def calculate_stability(self, positions_history):
        if len(positions_history) < 10:
            return False, 100
        
        avg_x = np.mean([p[0] for p in positions_history])
        avg_y = np.mean([p[1] for p in positions_history])
        
        max_distance = 0
        for x, y in positions_history:
            dist = math.sqrt((x - avg_x)**2 + (y - avg_y)**2)
            max_distance = max(max_distance, dist)
        
        is_stable = max_distance < STABILITY_RADIUS
        stability_percentage = max(0, 100 - (max_distance / STABILITY_RADIUS) * 100)
        
        return is_stable, stability_percentage
    
    def update_hand_tracking(self, hand_id, hand_type, wrist_pos, is_raised, current_time):
        tracking = self.hand_tracking[hand_type]
        tracking['last_positions'].append(wrist_pos)
        
        is_stable, stability_pct = self.calculate_stability(tracking['last_positions'])
        
        if is_raised:
            if not tracking['is_raised']:
                tracking['is_raised'] = True
                tracking['stable_start_time'] = current_time
                tracking['last_positions'].clear()
                tracking['last_positions'].append(wrist_pos)
                tracking['current_stable'] = False
                tracking['raise_confirmed'] = False
                tracking['progress'] = 0
            else:
                if tracking['stable_start_time']:
                    elapsed = current_time - tracking['stable_start_time']
                    tracking['progress'] = min(100, int((elapsed / STABILITY_TIME) * 100))
                    
                    if is_stable and not tracking['current_stable']:
                        tracking['current_stable'] = True
                    
                    if tracking['current_stable'] and elapsed >= STABILITY_TIME:
                        if not tracking['raise_confirmed'] and \
                           (current_time - tracking['last_confirmed_time']) > self.cooldown_period:
                            tracking['raise_confirmed'] = True
                            tracking['last_confirmed_time'] = current_time
                            return True, stability_pct, elapsed
        else:
            if tracking['is_raised']:
                tracking['is_raised'] = False
                tracking['stable_start_time'] = None
                tracking['current_stable'] = False
                tracking['raise_confirmed'] = False
                tracking['last_positions'].clear()
                tracking['progress'] = 0
        
        return False, stability_pct, 0
    
    def calculate_ear(self, landmarks, eye_top_idx, eye_bottom_idx, eye_left_idx, eye_right_idx):
        top = landmarks[eye_top_idx]
        bottom = landmarks[eye_bottom_idx]
        vertical_dist = math.sqrt((top.x - bottom.x)**2 + (top.y - bottom.y)**2)
        
        left = landmarks[eye_left_idx]
        right = landmarks[eye_right_idx]
        horizontal_dist = math.sqrt((left.x - right.x)**2 + (left.y - right.y)**2)
        
        if horizontal_dist == 0:
            return 1.0
        
        ear = vertical_dist / horizontal_dist
        return ear
    
    def are_eyes_closed(self, face_landmarks):
        if not face_landmarks:
            return False, 0.0, 0.0
        
        left_ear = self.calculate_ear(
            face_landmarks,
            LEFT_EYE_TOP, LEFT_EYE_BOTTOM,
            LEFT_EYE, LEFT_EYE_INNER
        )
        
        right_ear = self.calculate_ear(
            face_landmarks,
            RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM,
            RIGHT_EYE, RIGHT_EYE_INNER
        )
        
        avg_ear = (left_ear + right_ear) / 2
        self.last_ear = avg_ear
        
        open_ear = EYE_OPEN_EAR_BASELINE
        closed_ear = 0.05
        if avg_ear >= open_ear:
            closure_pct = 0.0
        elif avg_ear <= closed_ear:
            closure_pct = 100.0
        else:
            closure_pct = ((open_ear - avg_ear) / (open_ear - closed_ear)) * 100.0
            closure_pct = min(100.0, max(0.0, closure_pct))
        
        self.closure_percentage = closure_pct
        
        both_below = (left_ear < EYE_CLOSURE_THRESHOLD and right_ear < EYE_CLOSURE_THRESHOLD)
        both_closed = both_below and (avg_ear < EYE_CLOSURE_THRESHOLD)
        
        return both_closed, avg_ear, closure_pct
    
    def calculate_iris_distances(self, landmarks, frame_w, frame_h):
        left_iris_x = np.mean([landmarks[i].x for i in LEFT_IRIS]) * frame_w
        left_iris_y = np.mean([landmarks[i].y for i in LEFT_IRIS]) * frame_h
        left_point_x = landmarks[LEFT_EYE_LEFT_POINT].x * frame_w
        left_point_y = landmarks[LEFT_EYE_LEFT_POINT].y * frame_h
        distance_left = math.sqrt((left_iris_x - left_point_x)**2 + (left_iris_y - left_point_y)**2)
        
        right_iris_x = np.mean([landmarks[i].x for i in RIGHT_IRIS]) * frame_w
        right_iris_y = np.mean([landmarks[i].y for i in RIGHT_IRIS]) * frame_h
        right_point_x = landmarks[RIGHT_EYE_RIGHT_POINT].x * frame_w
        right_point_y = landmarks[RIGHT_EYE_RIGHT_POINT].y * frame_h
        distance_right = math.sqrt((right_iris_x - right_point_x)**2 + (right_iris_y - right_point_y)**2)
        
        return distance_left, distance_right
    
    def calculate_iris_center_percentage(self, dist_left, dist_right):
        if dist_left == 0 and dist_right == 0:
            return 100.0
        max_dist = max(dist_left, dist_right)
        if max_dist == 0:
            return 100.0
        return (min(dist_left, dist_right) / max_dist) * 100
    
    def determine_iris_status(self, percentage):
        if percentage >= 90:
            return "CENTER ✓", "#00ff88"
        elif percentage >= 70:
            return "SLIGHTLY OFF ⚠", "#ffcc00"
        else:
            return "OFF CENTER ✗", "#ff4444"
    
    def run(self):
        if not MEDIAPIPE_AVAILABLE:
            print("❌ MediaPipe not available - detection thread will exit")
            return
        
        if self.cap is None:
            self.setup_cameras()
        
        if self.hand_landmarker is None or self.face_landmarker is None:
            print("Failed to load models")
            return
        
        frame_timestamp = 0
        
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            
            h, w = frame.shape[:2]
            current_time = time.time()
            frame_timestamp += 33
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            
            face_result = self.face_landmarker.detect_for_video(mp_image, frame_timestamp)
            face_bounds = None
            face_landmarks = None
            
            if face_result.face_landmarks:
                face_landmarks = face_result.face_landmarks[0]
                face_bounds = self.get_eye_level(face_landmarks, w, h)
            
            eyes_closed = False
            ear_value = 0.0
            closure_pct = 0.0
            
            if face_landmarks:
                eyes_closed, ear_value, closure_pct = self.are_eyes_closed(face_landmarks)
                
                if eyes_closed:
                    self.eye_closure_counter += 1
                else:
                    self.eye_closure_counter = max(0, self.eye_closure_counter - 1)
                
                if self.eye_closure_counter >= EYE_CLOSURE_FRAMES:
                    self.eyes_closed = True
                else:
                    self.eyes_closed = False
            else:
                self.eye_closure_counter = max(0, self.eye_closure_counter - 1)
                if self.eye_closure_counter < EYE_CLOSURE_FRAMES:
                    self.eyes_closed = False
                    closure_pct = 0.0
            
            hand_result = self.hand_landmarker.detect_for_video(mp_image, frame_timestamp)
            
            confirmed_raises = []
            hand_progress = {'Left': 0, 'Right': 0}
            hand_raised = {'Left': False, 'Right': False}
            
            if not self.eyes_closed and hand_result.hand_landmarks and hand_result.handedness:
                for i, (landmarks, handedness) in enumerate(zip(hand_result.hand_landmarks, hand_result.handedness)):
                    hand_type = handedness[0].category_name
                    wrist_pos = (landmarks[WRIST].x * w, landmarks[WRIST].y * h)
                    
                    is_raised = self.is_hand_raised(landmarks, face_bounds, w, h)
                    
                    confirmed, stability_pct, elapsed = self.update_hand_tracking(
                        i, hand_type, wrist_pos, is_raised, current_time
                    )
                    
                    if confirmed:
                        confirmed_raises.append(hand_type)
                    
                    hand_progress[hand_type] = self.hand_tracking[hand_type]['progress']
                    hand_raised[hand_type] = self.hand_tracking[hand_type]['is_raised']
            else:
                for hand_type in self.hand_tracking:
                    if self.hand_tracking[hand_type]['is_raised']:
                        self.hand_tracking[hand_type]['is_raised'] = False
                        self.hand_tracking[hand_type]['stable_start_time'] = None
                        self.hand_tracking[hand_type]['last_positions'].clear()
                        self.hand_tracking[hand_type]['progress'] = 0
                        self.hand_tracking[hand_type]['raise_confirmed'] = False
                    if self.eyes_closed:
                        self.hand_tracking[hand_type]['progress'] = 0
            
            iris_percentage = 0
            iris_status = "No Face"
            iris_color = "#666666"
            
            if face_landmarks and not self.eyes_closed:
                dist_left, dist_right = self.calculate_iris_distances(face_landmarks, w, h)
                iris_percentage = self.calculate_iris_center_percentage(dist_left, dist_right)
                iris_status, iris_color = self.determine_iris_status(iris_percentage)
            elif self.eyes_closed:
                iris_percentage = 0
                iris_status = "EYES CLOSED ❌"
                iris_color = "#ff4444"
            
            self.update_signal.emit(
                hand_progress, hand_raised, confirmed_raises,
                iris_percentage, iris_status, iris_color,
                self.eyes_closed, ear_value, closure_pct
            )
            
            self.msleep(10)
        
        if self.cap:
            self.cap.release()
    
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.hand_landmarker:
            try:
                self.hand_landmarker.close()
            except:
                pass
        if self.face_landmarker:
            try:
                self.face_landmarker.close()
            except:
                pass
        self.wait()


# ============================================================
# ========== 6. PROGRESS CIRCLE WIDGET ==========
# ============================================================
class ProgressCircleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.is_active = False
        self.hand_type = None
        
        self.setFixedSize(90, 90)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()
        
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide)
        self.hide_timer.setSingleShot(True)
        
    def update_progress(self, progress, hand_type):
        self.progress = min(100, max(0, progress))
        self.hand_type = hand_type
        self.is_active = progress > 0
        
        if self.is_active:
            self.show()
            self.raise_()
            self.hide_timer.stop()
        else:
            self.hide_timer.start(1000)
        
        self.update()
    
    def paintEvent(self, event):
        if not self.is_active or self.progress <= 0:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        width = self.width()
        height = self.height()
        size = min(width, height)
        margin = 8
        radius = (size - margin * 2) / 2
        center = QPointF(width / 2, height / 2)
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        painter.setPen(QPen(QColor(60, 60, 80, 200), 2))
        painter.drawEllipse(center, radius, radius)
        
        if self.progress > 0:
            if self.progress < 50:
                color = QColor(255, 200, 0)
            elif self.progress < 80:
                color = QColor(255, 150, 0)
            else:
                color = QColor(0, 255, 136)
            
            pen = QPen(color, 6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            start_angle = 90 * 16
            span_angle = int(-(self.progress / 100) * 360 * 16)
            
            painter.drawArc(
                int(center.x() - radius + 4),
                int(center.y() - radius + 4),
                int((radius - 4) * 2),
                int((radius - 4) * 2),
                start_angle,
                span_angle
            )
        
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        text = f"{self.progress}%"
        text_rect = QRectF(center.x() - 25, center.y() - 15, 50, 30)
        painter.drawText(text_rect, Qt.AlignCenter, text)
        
        if self.hand_type:
            painter.setPen(QPen(QColor(200, 200, 200)))
            font.setPointSize(8)
            painter.setFont(font)
            
            hand_icon = "✋" if self.hand_type == "Left" else "✋"
            hand_text = f"{hand_icon} {self.hand_type}"
            text_rect = QRectF(center.x() - 30, center.y() + 15, 60, 20)
            painter.drawText(text_rect, Qt.AlignCenter, hand_text)
        
        painter.end()


# ============================================================
# ========== 7. PROFESSIONAL THREADING HELPERS ==========
# ============================================================

class AttentionSenderTask(QRunnable):
    """Send attention value in a separate thread to avoid UI freezing."""
    def __init__(self, attention_client, value):
        super().__init__()
        self.attention_client = attention_client
        self.value = value
        self.setAutoDelete(True)

    def run(self):
        try:
            if self.attention_client:
                self.attention_client.send_attention(self.value)
        except Exception as e:
            print(f"⚠️ Attention send error (background): {e}")

class ConnectionTimeoutGuard:
    """Helper to enforce connection timeout and UI feedback."""
    def __init__(self, parent, timeout_seconds=15):
        self.parent = parent
        self.timeout_seconds = timeout_seconds
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)
        self.triggered = False

    def start(self):
        self.triggered = False
        self.timer.start(self.timeout_seconds * 1000)

    def stop(self):
        self.timer.stop()

    def on_timeout(self):
        if not self.triggered:
            self.triggered = True
            self.parent.on_connection_timeout()


# ============================================================
# ========== 8. باقي الكود ==========
# ============================================================

class ProfileCacheManager:
    def __init__(self):
        # No disk caching — images are fetched from the server every time
        pass

    def get_profile_path(self, username):
        return None

    def has_cached(self, username):
        return False

    def load_from_cache(self, username):
        # Always return None to force a fresh network request
        return None

    def save_to_cache(self, username, pixmap):
        # No-op: do not cache anything locally
        pass

    def get_pixmap(self, username):
        # Always return None to force a fresh network request
        return None


class ProfileImageLoader(QThread):
    loaded = Signal(str, QPixmap)

    def __init__(self, username, dimension="480x480", cache_manager=None):
        super().__init__()
        self.username = username
        self.dimension = dimension
        # cache_manager is intentionally ignored — we always fetch from server

    def run(self):
        try:
            import requests
            url = f"{profile_server_url}/profile/{self.username}/{self.dimension}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.loaded.emit(self.username, pixmap)
            else:
                print(f"Failed to load profile for {self.username}: {response.status_code}")
        except Exception as e:
            print(f"Error loading profile image for {self.username}: {e}")
            if self.cache_manager:
                cached_pixmap = self.cache_manager.load_from_cache(self.username)
                if cached_pixmap:
                    self.loaded.emit(self.username, cached_pixmap)


class AudioRecorderThread(QThread):
    volume_updated = Signal(float)
    recording_finished = Signal(object)
    
    def __init__(self, input_device, sample_rate=44100, channels=2):
        super().__init__()
        self.input_device = input_device
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []
        
    def run(self):
        try:
            self.recording = True
            self.audio_data = []
            
            def audio_callback(indata, frames, time, status):
                if self.recording:
                    self.audio_data.extend(indata.copy())
                    if len(indata) > 0:
                        volume = min(1.0, abs(indata).mean() * 8)
                        self.volume_updated.emit(volume)
            
            self.stream = sd.InputStream(
                callback=audio_callback,
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.input_device,
                dtype='float32'
            )
            self.stream.start()
            
            while self.recording:
                self.msleep(100)
                
        except Exception as e:
            print(f"Recording thread error: {e}")
        finally:
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop()
                self.stream.close()
    
    def stop_recording(self):
        self.recording = False
        self.msleep(200)
        self.recording_finished.emit(self.audio_data)


class ClientSignals(QObject):
    new_audio = Signal(str, str)
    new_text = Signal(str, str)
    permission_response = Signal(dict)
    attention_analysis = Signal(dict)
    connection_status = Signal(bool, str)


class AvatarLabel(QLabel):
    def __init__(self, username, initial, color=None, cache_manager=None, parent=None):
        super().__init__(parent)
        self.username = username
        self.initial = initial
        self.color = color
        self.cache_manager = cache_manager
        self.pixmap = None
        self.setFixedSize(40, 40)
        self.setAlignment(Qt.AlignCenter)
        self.load_profile_image()
        
    def load_profile_image(self):
        self.loader = ProfileImageLoader(self.username, "40x40", self.cache_manager)
        self.loader.loaded.connect(self.on_profile_loaded)
        self.loader.start()
        
    def on_profile_loaded(self, username, pixmap):
        if username == self.username:
            self.pixmap = pixmap
            self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        if self.pixmap and not self.pixmap.isNull():
            scaled = self.pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(self.color or "#5e5e5e")))
            painter.drawEllipse(0, 0, self.width(), self.height())
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.white))
            painter.drawText(self.rect(), Qt.AlignCenter, self.initial)
        painter.end()


class AudioMessagesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_playing_audio = None
        self.main_window = parent
        self.cache_manager = None
        self.playback_started = False

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border: 2px solid #ddd; border-radius: 8px; background-color: white;")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Container for messages
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch()

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        self.audio_widgets = []

        self.placeholder = QLabel("No audio messages yet")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: #999; font-size: 14px; padding: 20px;")
        self.container_layout.insertWidget(0, self.placeholder)

    def set_audio(self, filename, username, cache_manager=None, play_callback=None, main_window=None, auto_play=True):
        # Remove placeholder if this is the first message
        if self.placeholder and self.placeholder.parent():
            self.container_layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None

        if main_window is None:
            main_window = self.main_window
        self.cache_manager = cache_manager

        widget = AudioMessageWidget(filename, username, main_window=main_window, cache=cache_manager)

        # Connect play callback if available
        if play_callback and hasattr(widget, 'play_requested'):
            try:
                widget.play_requested.connect(play_callback)
            except Exception as e:
                print(f"⚠️ Could not connect play_requested: {e}")

        # Append new messages at the bottom (oldest at top, newest at bottom)
        # Insert before the stretch spacer so it appears at the bottom
        stretch_idx = self.container_layout.count() - 1  # Last item is the stretch
        self.container_layout.insertWidget(stretch_idx, widget)
        self.audio_widgets.append(widget)

        # Scroll to bottom so the newest message is visible
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        if auto_play:
            print(f"🎵 Auto-play enabled for {username}'s audio: {filename}")
            if self.current_playing_audio and self.current_playing_audio != widget:
                self.current_playing_audio.stop_playback()
            self.playback_started = False
            self._attempt_auto_play(widget, 0)

    def _attempt_auto_play(self, widget, attempt):
        if self.playback_started:
            return
        if not widget or not widget.parent():
            return
        try:
            if hasattr(widget, 'start_playback'):
                print(f"🎵 Attempt {attempt + 1}: Auto-playing audio...")
                widget.start_playback()
                self.current_playing_audio = widget
                self.playback_started = True
                print("✅ Auto-play started successfully")
            else:
                print(f"❌ Auto-play failed: Widget doesn't have start_playback method")
        except Exception as e:
            print(f"❌ Auto-play attempt {attempt + 1} failed: {e}")
            if attempt < 5:
                delay = 300 + (attempt * 200)
                QTimer.singleShot(delay, lambda: self._attempt_auto_play(widget, attempt + 1))
            else:
                print("❌ Auto-play failed after 5 attempts")

    def clear_current(self):
        # Backward compatibility — clears all messages
        self.clear_all()

    def clear_all(self):
        for widget in self.audio_widgets:
            if widget and widget.parent():
                self.container_layout.removeWidget(widget)
                widget.deleteLater()
        self.audio_widgets.clear()
        if not self.placeholder:
            self.placeholder = QLabel("No audio messages yet")
            self.placeholder.setAlignment(Qt.AlignCenter)
            self.placeholder.setStyleSheet("color: #999; font-size: 14px; padding: 20px;")
            self.container_layout.insertWidget(0, self.placeholder)

    def handle_play_request(self, audio_widget):
        if self.current_playing_audio and self.current_playing_audio != audio_widget:
            self.current_playing_audio.stop_playback()
        self.current_playing_audio = audio_widget


# ============================================================
# ========== 9. MICROPHONE ANIMATION HTML ==========
# ============================================================
MIC_HTML_CODE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mic</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:transparent!important;display:flex;justify-content:center;align-items:center;min-height:100vh;overflow:hidden;font-family:sans-serif}
        .recorder-card{background:transparent!important;border-radius:3rem;padding:2rem;width:100%;max-width:540px;text-align:center}
        .status-chip{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:1rem;background:rgba(30,31,44,0.4);backdrop-filter:blur(10px);width:fit-content;margin:auto;padding:0.4rem 1.2rem;border-radius:50px;border:1px solid rgba(255,255,255,0.15)}
        .status-dot{width:10px;height:10px;border-radius:50%;background:#6b7280;transition:all .2s}
        .status-text{font-size:.8rem;font-weight:500;color:#f0f0f0}
        .countdown-circle{position:relative;width:160px;height:160px;margin:1rem auto}
        .countdown-number{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:3.5rem;font-weight:bold;color:#fff;z-index:2;transition:color 0.5s ease}
        .countdown-svg{transform:rotate(-90deg)}
        .countdown-circle-bg{stroke:rgba(255,255,255,0.2)}
        .countdown-circle-progress{stroke:#f43f5e;stroke-linecap:round;transition:stroke-dashoffset 1s linear}
        .mic-zone{display:flex;justify-content:center;margin:1rem 0}
        .mic-button{background:radial-gradient(circle at 35% 25%,#2d3348,#151a28);border:none;width:120px;height:120px;border-radius:50%;cursor:pointer;box-shadow:0 20px 35px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;transition:transform .1s}
        .mic-button:active{transform:scale(.95)}
        .mic-icon{font-size:3.5rem}
        .mic-button.recording-active{background:radial-gradient(circle at 35% 25%,#e11d48,#9f1239);box-shadow:0 0 0 5px rgba(225,29,72,0.4);animation:softPulse 1s infinite}
        @keyframes softPulse{0%{box-shadow:0 0 0 0 rgba(225,29,72,0.5)}70%{box-shadow:0 0 0 12px rgba(225,29,72,0)}100%{box-shadow:0 0 0 0 rgba(225,29,72,0)}}
        .bottom-animation{margin-top:2rem;background:rgba(0,0,0,0.15);backdrop-filter:blur(8px);border-radius:80px;padding:1rem .8rem;transition:all .35s cubic-bezier(.2,.9,.4,1.2);border:1px solid rgba(255,255,255,0.08)}
        .wave-container{display:flex;align-items:center;justify-content:center;gap:6px;height:80px}
        .wave-bar{width:8px;background:linear-gradient(180deg,#f472b6,#c084fc,#60a5fa);border-radius:20px;transition:height .05s;box-shadow:0 0 8px rgba(192,132,252,0.6)}
        .recording-label{text-align:center;margin-top:.9rem;font-size:.75rem;font-weight:600;color:#e2e8f0;display:flex;align-items:center;justify-content:center;gap:6px}
        .recording-label span{display:inline-block;width:8px;height:8px;background:#f43f5e;border-radius:50%;animation:blinkRed 1.2s infinite}
        @keyframes blinkRed{0%,100%{opacity:1}50%{opacity:.5}}
        .animation-hidden{opacity:0;visibility:hidden;transform:translateY(20px);pointer-events:none}
        .animation-visible{opacity:1;visibility:visible;transform:translateY(0)}
    </style>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
<div class="recorder-card">
    <div class="status-chip"><div class="status-dot" id="statusDot"></div><div class="status-text" id="statusMessage">🎤 Waiting...</div></div>
    <div id="countdownContainer" class="countdown-circle" style="display:none;">
        <svg class="countdown-svg" width="160" height="160" viewBox="0 0 160 160">
            <circle class="countdown-circle-bg" cx="80" cy="80" r="70" fill="none" stroke-width="8"/>
            <circle class="countdown-circle-progress" id="countdownProgress" cx="80" cy="80" r="70" fill="none" stroke="#f43f5e" stroke-width="8" stroke-dasharray="439.82" stroke-dashoffset="0"/>
        </svg>
        <div class="countdown-number" id="countdownNumber">3</div>
    </div>
    <div class="mic-zone"><button class="mic-button" id="micActionBtn"><div class="mic-icon">🎤</div></button></div>
    <div id="bottomWaveAnimation" class="bottom-animation animation-hidden">
        <div class="wave-container" id="waveVisualizer"></div>
        <div class="recording-label"><span></span> LIVE VOICE LEVELS</div>
    </div>
</div>
<script>
(function() {
    const micBtn = document.getElementById('micActionBtn');
    const bottomAnim = document.getElementById('bottomWaveAnimation');
    const waveContainer = document.getElementById('waveVisualizer');
    const statusDot = document.getElementById('statusDot');
    const statusMsg = document.getElementById('statusMessage');
    const countdownContainer = document.getElementById('countdownContainer');
    const countdownNumber = document.getElementById('countdownNumber');
    const countdownProgress = document.getElementById('countdownProgress');
    let isActive = false, barsArray = [], animationFrame = null, time = 0;
    const BAR_COUNT = 22;
    let baseMinHeight = 6, baseMaxHeight = 58;
    let countdownInterval = null, recordingStartCallback = null, recordingStopCallback = null, isRecording = false;
    let pyInterface = null;
    function createBars() {
        waveContainer.innerHTML = '';
        barsArray = [];
        for (let i = 0; i < BAR_COUNT; i++) {
            const bar = document.createElement('div');
            bar.className = 'wave-bar';
            bar.style.height = '4px';
            bar.style.width = window.innerWidth <= 500 ? '5px' : '8px';
            barsArray.push(bar);
            waveContainer.appendChild(bar);
        }
    }
    function updateWaveFromVolume(volume) {
        if (!isActive) return;
        for (let i = 0; i < barsArray.length; i++) {
            let intensity = volume * (0.5 + (i / BAR_COUNT) * 0.8);
            let barHeight = baseMinHeight + (intensity * (baseMaxHeight - baseMinHeight));
            barHeight = Math.max(4, Math.min(baseMaxHeight, barHeight));
            barsArray[i].style.height = barHeight + 'px';
        }
    }
    function animateWaves() {
        if (!isActive) return;
        time += 0.12;
        for (let i = 0; i < barsArray.length; i++) {
            const phase1 = Math.sin(time + i * 0.32) * 0.7;
            const phase2 = Math.sin(time * 1.7 + i * 0.18) * 0.5;
            const phase3 = Math.cos(time * 0.9 + i * 0.45) * 0.4;
            let intensity = (phase1 + phase2 + phase3) / 1.6;
            let normalized = (intensity + 1) / 2;
            let beatEffect = Math.sin(time * 4) * 0.2;
            let finalFactor = Math.min(0.98, Math.max(0.15, normalized + beatEffect));
            let barHeight = baseMinHeight + (finalFactor * (baseMaxHeight - baseMinHeight));
            barsArray[i].style.height = barHeight + 'px';
            const rColor = 120 + Math.floor(finalFactor * 100);
            const gColor = 70 + Math.floor(finalFactor * 70);
            const bColor = 200 + Math.floor(finalFactor * 55);
            barsArray[i].style.background = 'linear-gradient(180deg, rgb(245,158,184), rgb('+rColor+','+gColor+','+bColor+'))';
        }
        animationFrame = requestAnimationFrame(animateWaves);
    }
    function startWave() { if (animationFrame) cancelAnimationFrame(animationFrame); isActive = true; animateWaves(); }
    function stopWave(resetUI) { if (animationFrame) { cancelAnimationFrame(animationFrame); animationFrame = null; } isActive = false; if (resetUI) { bottomAnim.classList.remove('animation-visible'); bottomAnim.classList.add('animation-hidden'); statusDot.style.background = '#6b7280'; statusMsg.innerText = '🎤 Ready'; if (barsArray.length) barsArray.forEach(bar => bar.style.height = '4px'); } }
    function startCountdown(seconds, onStartRecording) {
        if (countdownInterval) clearInterval(countdownInterval);
        countdownContainer.style.display = 'block';
        countdownNumber.style.color = '#fff'; // Start with white
        let remaining = seconds;
        const circumference = 439.82;
        function updateCountdown() {
            countdownNumber.textContent = remaining;
            const progress = remaining / seconds;
            const dashOffset = circumference * (1 - progress);
            countdownProgress.style.strokeDashoffset = dashOffset;
            // Color transition: white (3) → ocean blue (0)
            // Ocean blue: #006994 (deep ocean) to #0077be (ocean blue)
            const colorProgress = 1 - progress; // 0 at start, 1 at end
            const r = Math.round(255 - (colorProgress * (255 - 0)));
            const g = Math.round(255 - (colorProgress * (255 - 105)));
            const b = Math.round(255 - (colorProgress * (255 - 148)));
            countdownNumber.style.color = `rgb(${r}, ${g}, ${b})`;
            if (remaining <= 0) { 
                clearInterval(countdownInterval); 
                countdownContainer.style.display = 'none'; 
                countdownNumber.style.color = '#fff'; // Reset color
                if (onStartRecording) onStartRecording(); 
            }
            remaining--;
        }
        updateCountdown();
        countdownInterval = setInterval(updateCountdown, 1000);
    }
    function startRecordingUI() {
        bottomAnim.classList.remove('animation-hidden'); bottomAnim.classList.add('animation-visible');
        statusDot.style.background = '#f43f5e';
        statusMsg.innerText = '🔴 RECORDING - Click mic to stop';
        time = 0; startWave(); isRecording = true;
        micBtn.onclick = function(e) { e.preventDefault(); if (isRecording && pyInterface) pyInterface.stopRecording(); return false; };
    }
    function stopRecordingUI() { isRecording = false; stopWave(true); micBtn.onclick = function(e) { e.preventDefault(); return false; }; }
    window.startRecordingSession = function(seconds, onStart, onStop) { recordingStartCallback = onStart; recordingStopCallback = onStop; startCountdown(seconds, function() { startRecordingUI(); if (recordingStartCallback) recordingStartCallback(); }); };
    window.updateVolumeLevel = function(volume) { if (isActive) updateWaveFromVolume(volume); };
    window.endRecordingSession = function() { stopRecordingUI(); if (recordingStopCallback) recordingStopCallback(); };
    createBars();
    bottomAnim.classList.add('animation-hidden');
    new QWebChannel(qt.webChannelTransport, function(channel) { pyInterface = channel.objects.pyInterface; });
    window.addEventListener('resize', function() { if (barsArray.length) { var w = window.innerWidth <= 500 ? '5px' : '8px'; barsArray.forEach(function(bar) { bar.style.width = w; }); } });
})();
</script>
</body>
</html>"""


class WebInterface(QObject):
    stop_recording_signal = Signal()
    @Slot()
    def stopRecording(self):
        print("🎤 User clicked microphone to stop recording")
        self.stop_recording_signal.emit()


class MicrophoneOverlay(QWidget):
    recording_started = Signal()
    recording_stopped = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(350, 420)
        self.web_view = QWebEngineView(self)
        self.web_view.setGeometry(0, 0, self.width(), self.height())
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)
        self.web_view.page().setBackgroundColor(QColor(0,0,0,0))
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, False)
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        self.channel = QWebChannel()
        self.web_interface = WebInterface()
        self.channel.registerObject("pyInterface", self.web_interface)
        self.web_view.page().setWebChannel(self.channel)
        self.web_view.setHtml(MIC_HTML_CODE, QUrl("about:blank"))
        self.web_interface.stop_recording_signal.connect(self.on_stop_recording_requested)
        self.drag_position = None
        self.setMouseTracking(True)
        self.hide()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent().mapToGlobal(self.pos())
            event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            parent = self.parent()
            if parent:
                new_pos = event.globalPosition().toPoint() - self.drag_position
                parent.move(new_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        event.accept()
    def start_recording_session(self, countdown_seconds=3):
        self.show()
        self.raise_()
        parent = self.parent()
        if parent:
            parent.raise_()
            parent.activateWindow()
        if parent:
            parent_rect = parent.rect()
            x = (parent_rect.width() - self.width()) // 2
            y = (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        self.web_view.page().runJavaScript(f'startRecordingSession({countdown_seconds}, function(){{}}, function(){{}});')
        QTimer.singleShot(countdown_seconds * 1000, lambda: self.recording_started.emit())
    def update_volume(self, volume):
        self.web_view.page().runJavaScript(f'updateVolumeLevel({volume});')
    def end_recording_session(self):
        self.web_view.page().runJavaScript('endRecordingSession();')
        self.recording_stopped.emit()
        QTimer.singleShot(500, self.hide)
    def on_stop_recording_requested(self):
        print("👆 User requested early stop")
        self.end_recording_session()


# ============================================================
# ========== 10. CONNECTION THREAD (بدون تشفير - SSL فقط) ==========
# ============================================================
class ConnectionThread(QThread):
    connected = Signal(object, object)
    error = Signal(str)
    
    def __init__(self, token, room, username):
        super().__init__()
        self.token = token
        self.room = room
        self.username = username
        self._connected_emitted = False
        self._error_emitted = False
        
    def run(self):
        try:
            print("🔌 Attempting to connect to server...")
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            
            print(f"🔌 Connecting to localhost:5003...")
            sock.connect(('localhost', 5003))
            print("✅ Socket connected")
            
            audio_sock = context.wrap_socket(sock, server_hostname='localhost')
            print("✅ SSL handshake complete")
            
            login_data = {
                'token': self.token,
                'room': self.room,
                'role': 'student'
            }
            
            login_json = json.dumps(login_data)
            print(f"📤 Sending login (JSON): {login_json}")
            audio_sock.sendall(login_json.encode())
            print("✅ Login data sent")
            
            print("⏳ Waiting for server response...")
            response = audio_sock.recv(1024).decode()
            print(f"📥 Received response: {response}")
            
            if not response:
                raise Exception("No response from server")
            
            resp = json.loads(response)
            
            if resp.get('status') != 'success':
                raise Exception(resp.get('message', 'Login failed'))
            
            print(f"✅ Login successful! Username: {resp.get('username')}")
            
            print("🔑 Requesting encryption key (for compatibility)...")
            audio_sock.sendall(b'GET_KEY')
            key = audio_sock.recv(1024)
            
            if not key or len(key) < 32:
                raise Exception("Failed to receive encryption key")
            
            print(f"✅ Encryption key received (length: {len(key)})")
            
            cipher = Fernet(key)
            print("✅ Fernet cipher created (for compatibility only)")
            
            self._connected_emitted = True
            self.connected.emit(audio_sock, cipher)
            print("✅ connected signal emitted")
            
            return
            
        except socket.timeout as e:
            if not self._connected_emitted and not self._error_emitted:
                self._error_emitted = True
                self.error.emit("Connection timeout - server not responding")
            print("❌ Socket timeout")
        except ConnectionRefusedError as e:
            if not self._connected_emitted and not self._error_emitted:
                self._error_emitted = True
                self.error.emit("Connection refused - server may not be running")
            print("❌ Connection refused")
        except json.JSONDecodeError as e:
            if not self._connected_emitted and not self._error_emitted:
                self._error_emitted = True
                self.error.emit(f"Invalid response from server: {e}")
            print(f"❌ JSON decode error: {e}")
        except Exception as e:
            if not self._connected_emitted and not self._error_emitted:
                self._error_emitted = True
                self.error.emit(f"Connection error: {str(e)}")
            print(f"❌ Connection error: {e}")
            import traceback
            traceback.print_exc()


# ============================================================
# ========== 11. MESSAGE RECEIVER THREAD (بدون تشفير - SSL فقط) ==========
# ============================================================
class MessageReceiverThread(QThread):
    new_audio = Signal(str, str)
    new_text = Signal(str, str)
    permission_response = Signal(dict)
    attention_analysis = Signal(dict)
    connection_lost = Signal()
    
    def __init__(self, socket, cipher):
        super().__init__()
        self.socket = socket
        self.cipher = cipher
        self.running = True
        self.audio_folder = "audio_sendreceive"
        # Clean up any existing audio files from previous sessions on startup
        if os.path.exists(self.audio_folder):
            try:
                shutil.rmtree(self.audio_folder)
                print(f"🧹 Cleaned up old audio folder on startup: {self.audio_folder}")
            except Exception as e:
                print(f"⚠️ Could not clean up old audio folder: {e}")
        os.makedirs(self.audio_folder, exist_ok=True)
        
    def stop(self):
        self.running = False
        
    def run(self):
        while self.running:
            try:
                self.socket.settimeout(1.0)
                
                try:
                    type_len = self.socket.recv(4)
                except socket.timeout:
                    continue
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break
                
                if not type_len or len(type_len) != 4:
                    print("Connection closed by server")
                    break
                
                msg_type = self.socket.recv(int.from_bytes(type_len, 'big')).decode()
                
                data_len_data = self.socket.recv(4)
                if not data_len_data:
                    break
                data_len = int.from_bytes(data_len_data, 'big')
                
                raw_data = b''
                while len(raw_data) < data_len:
                    chunk = self.socket.recv(min(4096, data_len - len(raw_data)))
                    if not chunk:
                        break
                    raw_data += chunk
                
                if not raw_data:
                    continue
                
                print(f"📥 [DEBUG] Received message type: {msg_type}, length: {len(raw_data)}")
                
                if msg_type == 'PERMISSION_RESPONSE':
                    print(f"📥 [DEBUG] Processing PERMISSION_RESPONSE")
                    response = None
                    if FLATBUFFERS_AVAILABLE:
                        try:
                            response = parse_permission_response(raw_data)
                            print(f"📥 [DEBUG] Parsed FlatBuffers response: {response}")
                        except Exception as e:
                            print(f"📥 [DEBUG] FlatBuffers parse error: {e}")
                    if not response:
                        try:
                            response = json.loads(raw_data.decode('utf-8'))
                            print(f"📥 [DEBUG] Parsed JSON response: {response}")
                        except Exception as e:
                            print(f"📥 [DEBUG] JSON parse error: {e}")
                    if response:
                        self.permission_response.emit(response)
                        print(f"📥 [DEBUG] Emitted permission_response signal")
                
                elif msg_type == 'ATTENTION_ANALYSIS':
                    pass
                
                elif msg_type == 'AUDIO_MESSAGE':
                    print(f"📥 [DEBUG] Processing AUDIO_MESSAGE")
                    try:
                        audio_data = None
                        if FLATBUFFERS_AVAILABLE:
                            try:
                                audio_data = parse_audio_message(raw_data)
                            except Exception as e:
                                print(f"📥 [DEBUG] FlatBuffers parse error: {e}")
                        if not audio_data:
                            try:
                                audio_data = json.loads(raw_data.decode('utf-8'))
                            except Exception as e:
                                print(f"📥 [DEBUG] JSON parse error: {e}")
                        if audio_data:
                            username = audio_data.get('username', '')
                            filename = audio_data.get('filename', '')
                            file_data = audio_data.get('file_data', b'')
                            
                            if isinstance(file_data, str):
                                try:
                                    file_data = bytes.fromhex(file_data)
                                    print(f"✅ Converted hex string to bytes: {len(file_data)} bytes")
                                except ValueError as e:
                                    print(f"Error decoding hex data: {e}")
                                    file_data = b''
                            elif isinstance(file_data, list):
                                try:
                                    file_data = bytes(file_data)
                                except:
                                    file_data = b''
                            
                            if file_data:
                                save_path = os.path.join(self.audio_folder, f"received_{filename}")
                                with open(save_path, 'wb') as f:
                                    f.write(file_data)
                                self.new_audio.emit(save_path, username)
                                print(f"📥 [DEBUG] Emitted new_audio signal for {username}")
                            else:
                                print(f"⚠️ No valid file data for {filename}")
                    except Exception as e:
                        print(f"Error processing audio message: {e}")
                        import traceback
                        traceback.print_exc()
                
                elif msg_type == 'TEXT_MESSAGE':
                    try:
                        text_data = json.loads(raw_data.decode('utf-8'))
                        self.new_text.emit(text_data.get('content', ''), text_data.get('username', ''))
                    except:
                        pass
                
                else:
                    print(f"Unknown message type: {msg_type}")
                    
            except Exception as e:
                print(f"Receive error: {e}")
                break
        
        self.connection_lost.emit()


# ============================================================
# ========== 12. STUDENT CHAT CLIENT (مع تحسينات الـ Threading) ==========
# ============================================================
class StudentChatClient(QMainWindow):
    def __init__(self, embedded=False):
        super().__init__()
        self.embedded = embedded
        print("🔧 Initializing StudentChatClient with advanced threading...")

        # Thread pool for non‑blocking tasks
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)

        if not TOKEN or not ROOM_ID:
            print("❌ Chat module disabled: No valid token or room")
            self.setEnabled(False)
            self.setWindowTitle("Chat - Disabled (No Token)")
            self._create_disabled_ui()
            return

        self.username = USERNAME
        self.room = ROOM_ID
        self.token = TOKEN
        self.audio_folder = "audio_sendreceive"
        # Clean up any existing audio files from previous sessions on startup
        if os.path.exists(self.audio_folder):
            try:
                shutil.rmtree(self.audio_folder)
                print(f"🧹 Cleaned up old audio folder on startup: {self.audio_folder}")
            except Exception as e:
                print(f"⚠️ Could not clean up old audio folder: {e}")
        os.makedirs(self.audio_folder, exist_ok=True)

        self.sample_rate = 44100
        self.channels = 2
        self.temp_filename = os.path.join(self.audio_folder, "temp_audio.wav")
        self.signals = ClientSignals()
        self.audio_sock = None
        self.cipher = None
        self.current_playing_audio = None
        self.permission_requested = False
        self.recorder_button = None
        self.status_label = None
        self.last_audio_widget = None
        self.connection_thread = None
        self.receiver_thread = None
        self.detection_thread = None
        self._connection_attempted = False
        self._is_connected = False
        self._closing = False

        # Timeout guard for connection
        self.connection_guard = None

        # Attention client (lazy)
        self.attention_client = None
        self._init_attention_client()

        # Attention timer – now uses thread pool
        self.attention_timer = QTimer()
        self.attention_timer.timeout.connect(self._schedule_attention_send)
# DO NOT START YET - wait for camera data
# self.attention_timer.start(500)  # REMOVED
        self.current_attention = 50.0
        self._attention_sending_active = False  # ADD THIS
        self._detection_counter = 0  # ADD THIS

        self.profile_cache_manager = ProfileCacheManager()
        self.recorder_thread = None
        self.progress_circle = None
        self.hand_raised = {'Left': False, 'Right': False}
        self.iris_percentage = 50.0
        self.eyes_closed = False
        self.closure_pct = 0.0

        print("🔧 Creating microphone overlay...")
        self.mic_overlay = MicrophoneOverlay(self)
        self.mic_overlay.recording_started.connect(self.on_animation_recording_start)
        self.mic_overlay.recording_stopped.connect(self.on_animation_recording_stop)

        self.signals.new_audio.connect(self.display_received_audio)
        self.signals.new_text.connect(self.display_received_text)
        self.signals.permission_response.connect(self.on_permission_response)
        self.signals.attention_analysis.connect(self.on_attention_analysis)
        self.signals.connection_status.connect(self.on_connection_status)

        print("🔧 Getting input device...")
        self.input_device = self.get_default_input_device()
        if self.input_device is None:
            QMessageBox.warning(self, "Audio Warning", "No microphone found!")

        print("🔧 Initializing UI...")
        self.init_ui()

        if not self.embedded:
            self.show()
            self.raise_()
            self.activateWindow()
            self.repaint()
            QApplication.processEvents()
        else:
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_TranslucentBackground, False)

        print(f"✅ Window visible: {self.isVisible()}")
        print(f"✅ Embedded mode: {self.embedded}")

        self.detection_thread = None
        self.camera_permission_granted = False

        if MEDIAPIPE_AVAILABLE:
            print("🔧 MediaPipe available - waiting for user camera permission...")
            # Delay slightly so the window renders before the dialog appears
            QTimer.singleShot(800, self.show_camera_permission_dialog)
        else:
            print("⚠️ MediaPipe not available - running without hand detection")

        print("🔧 Starting connection thread with timeout guard...")
        self.connect_to_server()

    def show_camera_permission_dialog(self):
        """Ask user before opening camera — clean white design, no emojis."""
        if self.camera_permission_granted:
            return

        # Prevent multiple dialogs
        if hasattr(self, '_permission_dialog_open') and self._permission_dialog_open:
            return
        self._permission_dialog_open = True

        # Create a custom styled dialog
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(480, 320)
        dialog.setStyleSheet("background: transparent;")

        # Main container – white background with subtle shadow
        container = QFrame(dialog)
        container.setGeometry(0, 0, 480, 320)
        container.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 20px;
                border: none;
            }
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        # Layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignCenter)

        # Title – no emoji, no border
        title = QLabel("Camera Access")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1d1d1f;
            background: transparent;
            letter-spacing: -0.3px;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(title)

        # Description – clean text, no border
        desc = QLabel(
            "This app uses your camera locally to detect hand raises "
            "and measure attention.\n\n"
            "No video is uploaded to any server – your privacy is fully protected."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            font-size: 14px;
            color: #3a3a3c;
            background: transparent;
            line-height: 1.5;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignCenter)

        cancel_btn = QPushButton("Not Now")
        cancel_btn.setFixedSize(120, 44)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f7;
                color: #1d1d1f;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #e5e5ea;
            }
            QPushButton:pressed {
                background: #d1d1d6;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        allow_btn = QPushButton("Allow Access")
        allow_btn.setFixedSize(150, 44)
        allow_btn.setCursor(Qt.PointingHandCursor)
        allow_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #005a9e;
            }
            QPushButton:pressed {
                background: #003d7e;
            }
        """)
        btn_layout.addWidget(allow_btn)

        layout.addLayout(btn_layout)

        # Connect buttons
        cancel_btn.clicked.connect(lambda: dialog.done(0))
        allow_btn.clicked.connect(lambda: dialog.done(1))

        # Center on parent
        if self.isVisible():
            parent_geo = self.geometry()
            dialog.move(
                parent_geo.center().x() - dialog.width() // 2,
                parent_geo.center().y() - dialog.height() // 2
            )
        else:
            screen = QApplication.primaryScreen().geometry()
            dialog.move(
                (screen.width() - dialog.width()) // 2,
                (screen.height() - dialog.height()) // 2
            )

        reply = dialog.exec()
        self._permission_dialog_open = False

        if reply == 1:
            self._start_camera_with_permission()
        else:
            self._deny_camera()

    def _start_camera_with_permission(self):
        """User clicked Allow — now safe to open camera."""
        self.camera_permission_granted = True

        # Hide the "Enable Camera" button since it's now allowed
        if hasattr(self, 'camera_btn'):
            self.camera_btn.hide()

        print("✅ Camera permission granted by user")
        self._update_status("Camera allowed — starting hand & eye tracking...")

        try:
            self.detection_thread = CombinedDetectionThread()
            self.detection_thread.update_signal.connect(self.on_detection_update)
            self.detection_thread.start()
            print("✅ Detection thread started after explicit user consent")
            self._update_status("Connected! Press the microphone button to request permission")
        except Exception as e:
            print(f"❌ Camera failed to start: {e}")
            self._update_status("Camera failed to start")
            QMessageBox.warning(self, "Camera Error", f"Could not start camera:\n{str(e)}")

    def _deny_camera(self):
        """User denied camera — run in chat-only mode."""
        self.camera_permission_granted = False

        # Keep button visible so user can change their mind later
        if hasattr(self, 'camera_btn'):
            self.camera_btn.show()
            # Add a subtle pulse animation hint
            self.camera_btn.setStyleSheet(self.camera_btn.styleSheet() + """
                QPushButton {
                    animation: pulse 2s infinite;
                }
            """)

        print("❌ Camera permission denied — running without detection")
        self._update_status("📷 Camera access denied. Tap 'Enable Camera' anytime to turn it on.")
        # detection_thread stays None; attention defaults to 50.0
    def _init_attention_client(self):
        """Initialize attention client in background to avoid blocking."""
        try:
            from attention_client import AttentionClient
            self.attention_client = AttentionClient.get_instance()
            print("✅ Attention client initialized")
        except Exception as e:
            print(f"⚠️ Attention client initialization failed: {e}")
            self.attention_client = None

    def _schedule_attention_send(self):
        """Queue attention send in thread pool."""
        if self.attention_client and self.current_attention is not None:
            task = AttentionSenderTask(self.attention_client, self.current_attention)
            self.thread_pool.start(task)

    def _create_disabled_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #f5f5f7;")
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("💬 Chat Unavailable")
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff6b6b;")
        layout.addWidget(label)
        sub_label = QLabel("Please log in first to access the chat feature.")
        sub_label.setStyleSheet("font-size: 14px; color: #86868b;")
        layout.addWidget(sub_label)
        self.setCentralWidget(central)

    def get_default_input_device(self):
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    return i
            return None
        except Exception:
            return None

    def init_ui(self):
        self.setWindowTitle(f"Student Chat - Room {self.room}")
        self.setGeometry(200, 200, 500, 700)
        self.setMinimumSize(400, 500)
        self.setStyleSheet("QMainWindow { background-color: #f0f0f0; }")
        central = QWidget()
        central.setStyleSheet("background-color: white;")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setCentralWidget(central)

        # ── Top bar: Camera enable button (for users who denied first time) ──
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.addStretch()

        self.camera_btn = QPushButton("Enable Camera")
        self.camera_btn.setFixedHeight(40)
        self.camera_btn.setCursor(Qt.PointingHandCursor)
        self.camera_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #4f46e5);
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 20px;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #818cf8, stop:1 #6366f1);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #4338ca);
            }
        """)
        self.camera_btn.clicked.connect(self.show_camera_permission_dialog)
        top_bar_layout.addWidget(self.camera_btn)

        # Hide if MediaPipe isn't even available
        if not MEDIAPIPE_AVAILABLE:
            self.camera_btn.hide()

        main_layout.addWidget(top_bar)

        # ── Main content (audio + recorder) ──
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        main_layout.addWidget(content_widget, stretch=1)

        # Messages container with floating recorder button
        self.messages_container = QWidget()
        self.messages_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.messages_container.setStyleSheet("border: 2px solid #ddd; border-radius: 8px; background-color: white;")
        messages_layout = QVBoxLayout(self.messages_container)
        messages_layout.setContentsMargins(0, 0, 0, 0)
        messages_layout.setSpacing(0)

        self.last_audio_widget = AudioMessagesWidget(self)
        self.last_audio_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.last_audio_widget.setStyleSheet("background: transparent; border: none;")
        messages_layout.addWidget(self.last_audio_widget, stretch=1)

        content_layout.addWidget(self.messages_container, stretch=1)

        # Floating recorder button - positioned over the messages area
        self.recorder_button = QPushButton("🎤")
        self.recorder_button.setFixedSize(56, 56)
        self.recorder_button.setCursor(Qt.PointingHandCursor)
        self.recorder_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 28px;
                font-size: 22px;
                box-shadow: 0 4px 12px rgba(0, 120, 212, 0.4);
            }
            QPushButton:hover { 
                background-color: #005a9e; 
                box-shadow: 0 6px 16px rgba(0, 90, 158, 0.5);
            }
            QPushButton:disabled { 
                background-color: #ccc; 
                box-shadow: none;
            }
            QPushButton:pressed { background-color: #003d7e; }
        """)
        self.recorder_button.clicked.connect(self.request_permission)
        self.recorder_button.setToolTip("Request permission to speak")
        self.recorder_button.setEnabled(False)

        # Position the button as a child of messages_container for z-index layering
        self.recorder_button.setParent(self.messages_container)
        self.recorder_button.raise_()  # Ensure it's on top (z-index)
        self._position_recorder_button()

        self.progress_circle = ProgressCircleWidget(self)
        self.progress_circle.hide()
        self.progress_circle.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Status bar with progress indicator
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel("Connecting to server...")
        self.status_label.setStyleSheet("color: #666; padding: 8px; font-size: 12px; background-color: #f0f0f0; border-radius: 8px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(35)
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 0)
        self.status_progress.setFixedSize(20, 20)
        self.status_progress.setStyleSheet("QProgressBar { border: none; background: transparent; } QProgressBar::chunk { background: #0078d4; border-radius: 10px; }")
        self.status_progress.hide()
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.status_progress)
        main_layout.addWidget(status_container)

        print("✅ UI initialized")

    def connect_to_server(self):
        if self._connection_attempted:
            print("⚠️ Connection already attempted, ignoring duplicate request.")
            return
        self._connection_attempted = True
        self._update_status("Connecting to server...", busy=True)
        self.recorder_button.setEnabled(False)

        self.connection_thread = ConnectionThread(self.token, self.room, self.username)
        self.connection_thread.connected.connect(self.on_connected)
        self.connection_thread.error.connect(self.on_connection_error)

        self.connection_guard = ConnectionTimeoutGuard(self, 15)
        self.connection_guard.start()

        self.connection_thread.start()

    def on_connection_timeout(self):
        """Handle connection timeout gracefully."""
        if self._is_connected or self._closing:
            return
        self._update_status("Connection timeout. Please try again.", busy=False)
        self.recorder_button.setEnabled(False)
        if self.connection_thread and self.connection_thread.isRunning():
            self.connection_thread.quit()
            self.connection_thread.wait(1000)
        QMessageBox.warning(self, "Connection Timeout",
                            "Failed to connect to server within 15 seconds.\n"
                            "Please check your network and try again.")

    def on_connected(self, audio_sock, cipher):
        if self._closing:
            return
        self._is_connected = True
        self.audio_sock = audio_sock
        self.cipher = cipher

        if self.connection_guard:
            self.connection_guard.stop()
            self.connection_guard = None

        try:
            self.connection_thread.error.disconnect(self.on_connection_error)
        except:
            pass

        self.receiver_thread = MessageReceiverThread(audio_sock, cipher)
        self.receiver_thread.new_audio.connect(self.signals.new_audio.emit)
        self.receiver_thread.new_text.connect(self.signals.new_text.emit)
        self.receiver_thread.permission_response.connect(self.signals.permission_response.emit)
        self.receiver_thread.attention_analysis.connect(self.signals.attention_analysis.emit)
        self.receiver_thread.connection_lost.connect(self.on_connection_lost)
        self.receiver_thread.start()

        self.recorder_button.setEnabled(True)
        self._update_status("Connected! Press the microphone button to request permission", busy=False)
        print("✅ Connected to server successfully")
        self.signals.connection_status.emit(True, "Connected")

    def on_connection_error(self, error_msg):
        if self._is_connected or self._closing:
            print(f"⚠️ Ignoring connection error (already connected): {error_msg}")
            return
        if self.connection_guard:
            self.connection_guard.stop()
            self.connection_guard = None
        self._update_status(f"Connection failed: {error_msg}", busy=False)
        self.recorder_button.setEnabled(False)
        print(f"❌ Connection error: {error_msg}")
        QMessageBox.warning(self, "Connection Error",
                            f"Failed to connect to server:\n\n{error_msg}\n\n"
                            "Please make sure the server is running and try again.")
        self.signals.connection_status.emit(False, error_msg)

    def on_connection_lost(self):
        self._is_connected = False
        self._update_status("Connection lost to server", busy=False)
        self.recorder_button.setEnabled(False)
        print("❌ Connection lost")
        QMessageBox.warning(self, "Connection Lost",
                            "Connection to the server was lost.\n\nPlease restart the application.")
        self.signals.connection_status.emit(False, "Connection lost")

    def on_connection_status(self, success, message):
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")

    def _update_status(self, text, busy=False):
        """Update status label and progress indicator."""
        self.status_label.setText(text)
        if busy:
            self.status_progress.show()
        else:
            self.status_progress.hide()

    def request_permission(self):
        """إرسال طلب إذن باستخدام TEXT_MESSAGE"""
        print("🎤 [DEBUG] request_permission called")
        
        if not self.audio_sock:
            self.status_label.setText("Not connected to server")
            print("❌ [DEBUG] No audio socket")
            return
            
        if self.permission_requested:
            self.status_label.setText("Permission already requested. Waiting for teacher...")
            print("⚠️ [DEBUG] Permission already requested")
            return
        
        self.permission_requested = True
        self.recorder_button.setEnabled(False)
        self.recorder_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 16px;
            }
        """)
        self.recorder_button.setText("⏳")
        self.status_label.setText("Requesting permission from teacher...")
        
        try:
            timestamp = datetime.now().isoformat()
            
            permission_data = {
                'type': 'permission_request',
                'student': self.username,
                'timestamp': timestamp
            }
            
            text_message = {
                'username': self.username,
                'content': json.dumps(permission_data)
            }
            
            data = json.dumps(text_message).encode('utf-8')
            
            print(f"📤 [DEBUG] Sending permission request as TEXT_MESSAGE")
            print(f"📤 [DEBUG] Data: {data}")
            print(f"📤 [DEBUG] Data length: {len(data)} bytes")
            
            msg_type = b'TEXT_MESSAGE'
            packet = len(msg_type).to_bytes(4, 'big') + msg_type + len(data).to_bytes(4, 'big') + data
            self.audio_sock.sendall(packet)
            
            print("✅ Permission request sent as TEXT_MESSAGE")
            QTimer.singleShot(30000, self.reset_permission_request)
            
        except socket.timeout:
            print("❌ [DEBUG] Socket timeout while sending")
            self.status_label.setText("Connection timeout. Please try again.")
            self.permission_requested = False
            self.recorder_button.setEnabled(True)
            self.recorder_button.setText("🎤")
            self.recorder_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }
                QPushButton:hover { background-color: #005a9e; }
                QPushButton:disabled { background-color: #ccc; }
            """)
        except Exception as e:
            self.status_label.setText("Failed to send request")
            self.permission_requested = False
            self.recorder_button.setEnabled(True)
            self.recorder_button.setText("🎤")
            self.recorder_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }
                QPushButton:hover { background-color: #005a9e; }
                QPushButton:disabled { background-color: #ccc; }
            """)
            print(f"❌ Error requesting permission: {e}")
            import traceback
            traceback.print_exc()

    def reset_permission_request(self):
        if self.permission_requested:
            self.permission_requested = False
            self.recorder_button.setEnabled(True)
            self.recorder_button.setText("🎤")
            self.recorder_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }
                QPushButton:hover { background-color: #005a9e; }
                QPushButton:disabled { background-color: #ccc; }
            """)
            self.status_label.setText("Permission request timed out. Please try again.")

    def on_permission_response(self, data):
        print(f"📥 [DEBUG] on_permission_response called with: {data}")
        self.permission_requested = False
        if data.get('accept', False):
            countdown = data.get('countdown', 3)
            self.status_label.setText(f"Permission granted! Recording starts in {countdown}...")
            self.recorder_button.setEnabled(False)
            self.recorder_button.setText("🎤")
            self.mic_overlay.start_recording_session(countdown)
            print(f"✅ [DEBUG] Permission granted, starting recording in {countdown}s")
        else:
            self.status_label.setText("Permission denied. You may try again.")
            self.recorder_button.setEnabled(True)
            self.recorder_button.setText("🎤")
            self.recorder_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }
                QPushButton:hover { background-color: #005a9e; }
                QPushButton:disabled { background-color: #ccc; }
            """)
            print(f"❌ [DEBUG] Permission denied")

    def on_attention_analysis(self, data):
        """معالجة تحليل الانتباه الوارد من الخادم"""
        print(f"📊 Attention Analysis for {data.get('room', 'Unknown')}:")
        print(f"   Average: {data.get('avg_percentage', 0):.1f}%")
        print(f"   Students: {data.get('student_count', 0)}")
        
        if data.get('absent_minded'):
            print("   🧠 Absent-minded students:")
            for student in data['absent_minded']:
                print(f"      - {student.get('username', 'Unknown')}: {student.get('severity', 'unknown')} ({student.get('value', 0):.1f}%)")
        
        if data.get('low_attention'):
            print("   ⚠️ Low attention students:")
            for student in data['low_attention']:
                print(f"      - {student.get('username', 'Unknown')}: {student.get('severity', 'unknown')} ({student.get('value', 0):.1f}%)")

    def on_animation_recording_start(self):
        print("🎤 Countdown finished, starting recording...")
        self.status_label.setText("Recording... Click the microphone button to stop")
        self.start_recording()

    def on_animation_recording_stop(self):
        print("🔴 Recording stopped, sending audio...")
        self.status_label.setText("Recording finished. Sending...")
        self.stop_recording()

    def start_recording(self):
        try:
            self.recorder_thread = AudioRecorderThread(
                self.input_device, 
                self.sample_rate, 
                self.channels
            )
            self.recorder_thread.volume_updated.connect(self.mic_overlay.update_volume)
            self.recorder_thread.recording_finished.connect(self.on_recording_finished)
            self.recorder_thread.start()
            print("✅ Recording started successfully")
            QTimer.singleShot(30000, self.auto_stop_recording)
        except Exception as e:
            print(f"❌ Recording error: {e}")
            QMessageBox.critical(self, "Recording Error", f"Could not start recording: {e}")
            self.mic_overlay.end_recording_session()
            self.recorder_button.setEnabled(True)
            self.recorder_button.setText("🎤")
            self.recorder_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }
                QPushButton:hover { background-color: #005a9e; }
                QPushButton:disabled { background-color: #ccc; }
            """)
            self.status_label.setText("Recording failed. Please try again.")

    def auto_stop_recording(self):
        if self.recorder_thread and self.recorder_thread.recording:
            print("⏱️ Auto-stopping recording after 30 seconds")
            self.mic_overlay.end_recording_session()

    def on_recording_finished(self, audio_data):
        if len(audio_data) > 0:
            print(f"✅ Recording saved: {len(audio_data)} samples")
            self.save_and_send_audio(audio_data)
        else:
            print("❌ No audio data recorded")
            self.status_label.setText("No audio recorded")
        
        self.recorder_button.setEnabled(True)
        self.recorder_button.setText("🎤")
        self.recorder_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 20px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.status_label.setText("Press the microphone button to request permission")

    def stop_recording(self):
        if self.recorder_thread and self.recorder_thread.isRunning():
            self.recorder_thread.stop_recording()
            self.recorder_thread.wait()
            self.recorder_thread = None

    def save_and_send_audio(self, audio_data):
        try:
            sf.write(self.temp_filename, audio_data, self.sample_rate)
            self.send_audio()
        except Exception as e:
            print(f"❌ Error saving audio: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def send_audio(self):
        """إرسال رسالة صوتية (بدون تشفير - SSL فقط)"""
        try:
            data, sr = sf.read(self.temp_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_{timestamp}.wav"
            save_path = os.path.join(self.audio_folder, filename)
            sf.write(save_path, data, sr, format='WAV', subtype='PCM_16')
            
            with open(save_path, 'rb') as f:
                file_data = f.read()
            
            print(f"📤 Sending audio: {filename} ({len(file_data)} bytes)")
            
            audio_dict = {
                'username': self.username,
                'filename': filename,
                'file_data': file_data.hex()
            }
            data = json.dumps(audio_dict).encode('utf-8')
            
            msg_type = b'AUDIO_MESSAGE'
            packet = len(msg_type).to_bytes(4, 'big') + msg_type + len(data).to_bytes(4, 'big') + data
            self.audio_sock.sendall(packet)

            self.display_received_audio(save_path, "You")
            print("✅ Audio sent successfully")
            self.status_label.setText("Audio sent successfully!")
            
        except Exception as e:
            print(f"❌ Error sending audio: {e}")
            self.status_label.setText(f"Error sending audio: {str(e)}")

    def display_received_audio(self, filename, username):
        try:
            if not os.path.exists(filename):
                print(f"Audio file not found: {filename}")
                return
            auto_play = (username != "You")
            print(f"📢 Displaying audio from {username}, auto_play={auto_play}")
            if self.last_audio_widget:
                self.last_audio_widget.set_audio(
                    filename, username, self.profile_cache_manager,
                    self.handle_audio_play_request, self, auto_play
                )
            if username != self.username and username != "You":
                try:
                    notification.show_notification(
                        title=f"Voice message from {username}",
                        description="🎤 Auto-playing...",
                        notification_type="news"
                    )
                except Exception as e:
                    print(f"Notification error: {e}")
        except Exception as e:
            print(f"Error displaying audio: {e}")

    def display_received_text(self, message, username):
        pass

    def handle_audio_play_request(self, audio_widget):
        if self.current_playing_audio and self.current_playing_audio != audio_widget:
            self.current_playing_audio.stop_playback()
        self.current_playing_audio = audio_widget
        if self.last_audio_widget:
            self.last_audio_widget.current_playing_audio = audio_widget


    @Slot(dict, dict, list, float, str, str, bool, float, float)
    def on_detection_update(self, hand_progress, hand_raised, confirmed_raises,
                           iris_percentage, iris_status, iris_color,
                           eyes_closed, ear_value, closure_pct):
        """
        Handle detection updates from the camera thread.
        Sends attention data ONLY when real camera data is available.
        """
        
        # ==== START ATTENTION SENDING ONLY WHEN WE HAVE REAL DATA ====
        if not hasattr(self, '_attention_sending_active') or not self._attention_sending_active:
            # Only start if we have a valid face detection (real data)
            if iris_percentage > 0 or closure_pct > 0 or eyes_closed:
                self._attention_sending_active = True
                if hasattr(self, 'attention_timer') and self.attention_timer:
                    self.attention_timer.start(500)  # Start only now
                    print("✅ ATTENTION SENDING STARTED (real camera data available)")
            else:
                # Still waiting for camera data - don't send anything
                print("⏳ Waiting for camera data before sending attention...")
                return
        
        # Update internal state
        self.hand_raised = hand_raised
        self.iris_percentage = iris_percentage
        self.eyes_closed = eyes_closed
        self.closure_pct = closure_pct
        
        # Calculate attention value based on detection data
        if eyes_closed:
            attention = 0
        else:
            attention = iris_percentage
            if hand_raised.get('Left', False) or hand_raised.get('Right', False):
                attention = min(100, attention + 10)
            if closure_pct > 50:
                attention = attention * (1 - (closure_pct / 100))
        
        attention = max(0, min(100, attention))
        self.current_attention = attention
        
        # Log attention data (reduced frequency to avoid spam)
        if hasattr(self, '_detection_counter'):
            self._detection_counter += 1
        else:
            self._detection_counter = 0
        
        if self._detection_counter % 10 == 0:  # Log every 10th update
            print(f"👁️ Attention: {attention:.1f}% | Iris: {iris_percentage:.1f}% | "
                  f"Eyes Closed: {eyes_closed} | Closure: {closure_pct:.0f}% | "
                  f"Hand Raised: {hand_raised}")
        
        # Update progress circle for hand raise
        if self.progress_circle:
            max_progress = 0
            hand_type = None
            for hand in ['Left', 'Right']:
                progress = hand_progress.get(hand, 0)
                if progress > max_progress:
                    max_progress = progress
                    hand_type = hand
            self.progress_circle.update_progress(max_progress, hand_type)
        
        # Auto-request permission when hand raise is confirmed
        if self.audio_sock and not self.permission_requested:
            if confirmed_raises and self.recorder_button and self.recorder_button.isEnabled():
                print(f"✋ Hand raised confirmed: {confirmed_raises} – sending permission request automatically!")
                self.request_permission()


    def _position_recorder_button(self):
        """Position the floating recorder button at bottom-right of messages area."""
        if hasattr(self, 'recorder_button') and self.recorder_button and self.recorder_button.parent():
            parent = self.recorder_button.parent()
            btn_size = self.recorder_button.size()
            margin = 16
            x = parent.width() - btn_size.width() - margin
            y = parent.height() - btn_size.height() - margin
            self.recorder_button.move(x, y)
            self.recorder_button.raise_()  # Keep on top

    def resizeEvent(self, event):
        """Reposition the floating button when window is resized."""
        super().resizeEvent(event)
        self._position_recorder_button()

    def showEvent(self, event):
        """Reposition the floating button when window is shown."""
        super().showEvent(event)
        QTimer.singleShot(50, self._position_recorder_button)

    def closeEvent(self, event):
        self._closing = True
        print("🛑 Closing student chat with thread cleanup...")

        # Stop attention timer
        if self.attention_timer:
            self.attention_timer.stop()
            self.attention_timer = None
        
        # Close attention client
        if self.attention_client:
            try:
                self.attention_client.close()
                print("✅ Attention client closed")
            except Exception as e:
                print(f"⚠️ Error closing attention client: {e}")
            self.attention_client = None

        # Cancel pending tasks in thread pool
        self.thread_pool.clear()

        # Stop timeout guard
        if self.connection_guard:
            self.connection_guard.stop()
            self.connection_guard = None
        
        # Clean up resources
        if self.recorder_thread:
            self.recorder_thread.stop_recording()
            self.recorder_thread.wait()
        if self.mic_overlay:
            self.mic_overlay.close()
        if self.receiver_thread:
            self.receiver_thread.stop()
            self.receiver_thread.wait()
        if self.connection_thread:
            if self.connection_thread.isRunning():
                self.connection_thread.quit()
                self.connection_thread.wait()
        if self.detection_thread and hasattr(self.detection_thread, 'stop'):
            self.detection_thread.stop()
            self.detection_thread.wait(3000)
        if self.audio_sock:
            try:
                self.audio_sock.close()
            except:
                pass

        # Wait for thread pool to finish
        self.thread_pool.waitForDone(3000)

        # Clean up audio files folder on exit
        try:
            if os.path.exists(self.audio_folder):
                shutil.rmtree(self.audio_folder)
                print(f"🧹 Cleaned up audio folder: {self.audio_folder}")
        except Exception as e:
            print(f"⚠️ Error cleaning up audio folder: {e}")

        event.accept()


"""
Teacher Application – Integrated with Dashboard UI
Modules: Classroom, Quiz, Chat, Poll, Account
With transparent backgrounds to show gradient from ui.py
"""

import sys
import os
import traceback
import contextlib
import io
import importlib.util
import asyncio
import subprocess
import requests
import json
import socket
import ssl
import gc
import weakref
import signal
from concurrent.futures import TimeoutError
from typing import Optional, Dict, Any, List

# ============ GLOBAL SSL CONFIGURATION - MUST BE EARLY ============
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

class InsecureHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['cert_reqs'] = ssl.CERT_NONE
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)
    def proxy_manager_for(self, *args, **kwargs):
        kwargs['cert_reqs'] = ssl.CERT_NONE
        kwargs['assert_hostname'] = False
        return super().proxy_manager_for(*args, **kwargs)

_original_get = requests.get
_original_post = requests.post
_original_put = requests.put
_original_delete = requests.delete

def _patch_request(original, *args, **kwargs):
    kwargs['verify'] = False
    return original(*args, **kwargs)

requests.get = lambda *args, **kwargs: _patch_request(_original_get, *args, **kwargs)
requests.post = lambda *args, **kwargs: _patch_request(_original_post, *args, **kwargs)
requests.put = lambda *args, **kwargs: _patch_request(_original_put, *args, **kwargs)
requests.delete = lambda *args, **kwargs: _patch_request(_original_delete, *args, **kwargs)

print("🔓 SSL verification globally disabled for development")
print(f"📡 API Base URL: {getattr(sys.modules.get('config'), 'API_BASE_URL', 'Not loaded yet')}")

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy, QMessageBox,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QProgressBar, QDialog, QToolTip,
    QLineEdit, QComboBox, QDialogButtonBox, QTextEdit, QListWidget, QSpinBox,
    QCheckBox, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QStatusBar,
    QSystemTrayIcon, QMenu, QSlider, QFileDialog
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QThreadPool, QTimer,
    QSize, QPoint, QPointF, QRect, QThread, Signal, QObject, QByteArray,
    QRectF, Property, QEventLoop, QMetaObject, Q_ARG
)
from PySide6.QtGui import (
    QPalette, QColor, QFont, QPainter, QPen, QBrush, QLinearGradient,
    QPainterPath, QPixmap, QImageReader, QIcon, QFontDatabase, QShortcut, QKeySequence,
    QAction
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtNetwork import QTcpSocket
from PySide6.QtCore import QProcess

import config
from ui import Dashboard, DockCircle, IconButton, CloseButton, SettingsButton, ChatPanel


# ============================================================
# Helper function to load modules from paths
# ============================================================
def load_module_from_path(module_name, file_path, class_name=None, add_to_path=True):
    """
    Load a module from a specific path with automatic sys.path handling.
    
    Args:
        module_name: Internal name for the module
        file_path: Full path to the Python file
        class_name: Name of the class to extract (optional)
        add_to_path: Whether to add the folder to sys.path
    
    Returns:
        tuple: (module, class_object) or (None, None) on failure
    """
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            return None, None
        
        # Add folder to sys.path
        if add_to_path:
            folder = os.path.dirname(file_path)
            if folder not in sys.path:
                sys.path.insert(0, folder)
                print(f"📁 Added to sys.path: {folder}")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if class_name and hasattr(module, class_name):
            return module, getattr(module, class_name)
        elif class_name:
            print(f"⚠️ Class '{class_name}' not found in {file_path}")
            return module, None
        
        return module, None
        
    except ImportError as e:
        print(f"❌ ImportError loading {file_path}: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# ============================================================
# Global shutdown and cleanup system
# ============================================================
class CleanupManager:
    _instance = None
    _shutdown_requested = False
    _cleanup_handlers = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_cleanup_handler(cls, handler, name=""):
        cls._cleanup_handlers.append((name, handler))
    
    @classmethod
    def request_shutdown(cls):
        cls._shutdown_requested = True
    
    @classmethod
    def is_shutdown_requested(cls):
        return cls._shutdown_requested
    
    @classmethod
    def run_all_cleanups(cls):
        print("\n🧹 Running all cleanup handlers...")
        for name, handler in cls._cleanup_handlers:
            try:
                handler()
                if name:
                    print(f"  ✅ {name} cleaned")
            except Exception as e:
                print(f"  ❌ Error in {name}: {e}")
        cls._cleanup_handlers.clear()


class ThreadCleanup:
    @staticmethod
    def safe_stop_thread(thread, timeout=3000):
        if not thread:
            return
        try:
            if hasattr(thread, 'isRunning') and thread.isRunning():
                thread.quit()
                if not thread.wait(timeout):
                    thread.terminate()
                    thread.wait(1000)
            if hasattr(thread, 'deleteLater'):
                thread.deleteLater()
        except Exception as e:
            print(f"Thread cleanup error: {e}")


class TimerCleanup:
    @staticmethod
    def cleanup_all_timers(widget):
        for timer in widget.findChildren(QTimer):
            if timer.isActive():
                timer.stop()
            timer.deleteLater()


class AnimationCleanup:
    @staticmethod
    def cleanup_animations(widget):
        effect = widget.graphicsEffect()
        if effect:
            widget.setGraphicsEffect(None)
            effect.deleteLater()
        for animation in widget.findChildren(QPropertyAnimation):
            animation.stop()
            animation.deleteLater()


class ModuleCleanupManager:
    _registered_modules = {}
    _module_instances = weakref.WeakSet()
    
    @classmethod
    def register_module(cls, name, module, cleanup_func=None):
        cls._registered_modules[name] = {
            'module': module,
            'cleanup': cleanup_func,
            'instances': []
        }
    
    @classmethod
    def register_instance(cls, module_name, instance):
        if module_name in cls._registered_modules:
            cls._registered_modules[module_name]['instances'].append(weakref.ref(instance))
        cls._module_instances.add(instance)
    
    @classmethod
    def cleanup_module(cls, module_name):
        if module_name not in cls._registered_modules:
            return False
        info = cls._registered_modules[module_name]
        if info['cleanup']:
            try:
                info['cleanup']()
            except Exception as e:
                print(f"Cleanup error for {module_name}: {e}")
        for instance_ref in info['instances']:
            instance = instance_ref()
            if instance:
                if hasattr(instance, 'shutdown'):
                    instance.shutdown()
                elif hasattr(instance, 'close'):
                    instance.close()
                if hasattr(instance, 'deleteLater'):
                    instance.deleteLater()
        info['instances'].clear()
        return True
    
    @classmethod
    def cleanup_all(cls):
        for module_name in list(cls._registered_modules.keys()):
            cls.cleanup_module(module_name)
        cls._module_instances.clear()


class ForceCleanup:
    @staticmethod
    def cleanup_websockets(obj):
        for attr_name in dir(obj):
            if 'websocket' in attr_name.lower() or 'ws' in attr_name.lower():
                attr = getattr(obj, attr_name)
                if hasattr(attr, 'close'):
                    try:
                        if asyncio.iscoroutinefunction(attr.close):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(attr.close())
                            loop.close()
                        else:
                            attr.close()
                    except Exception:
                        pass
    
    @staticmethod
    def cleanup_sockets(obj):
        for attr_name in dir(obj):
            if 'socket' in attr_name.lower():
                attr = getattr(obj, attr_name)
                try:
                    if hasattr(attr, 'shutdown'):
                        attr.shutdown(socket.SHUT_RDWR)
                    if hasattr(attr, 'close'):
                        attr.close()
                except Exception:
                    pass
    
    @staticmethod
    def cleanup_threads(obj):
        for attr_name in dir(obj):
            if 'thread' in attr_name.lower():
                attr = getattr(obj, attr_name)
                ThreadCleanup.safe_stop_thread(attr)


def force_close_all_websockets():
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                for task in asyncio.all_tasks(loop):
                    if not task.done():
                        task.cancel()
        except:
            pass
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()
        try:
            loop.run_until_complete(asyncio.sleep(0.1))
        except:
            pass
        loop.close()
        print("✅ Asyncio cleanup attempted")
    except Exception as e:
        print(f"Asyncio cleanup error (ignored): {e}")


def restart_application():
    program = sys.executable
    args = sys.argv[:]
    CleanupManager.run_all_cleanups()
    ModuleCleanupManager.cleanup_all()
    gc.collect()
    gc.collect()
    QProcess.startDetached(program, args)
    os._exit(0)


def close_application_securely(message=None):
    if message:
        print(f"🔒 Secure exit: {message}")
    else:
        print("🔒 Secure exit requested")
    CleanupManager.request_shutdown()
    CleanupManager.run_all_cleanups()
    app = QApplication.instance()
    if app is not None:
        try:
            app.closeAllWindows()
        except Exception as e:
            print(f"⚠️ closeAllWindows failed: {e}")
        try:
            app.quit()
        except Exception as e:
            print(f"⚠️ app.quit() failed: {e}")
    sys.exit(0)


# ============================================================
# SplashScreen, ProgressFill, MessageBoxInterceptor
# ============================================================
class ProgressFill(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(12)
        self.setMinimumWidth(350)
        self._progress = 0
        self._animation = None

    def get_progress(self):
        return self._progress

    def set_progress(self, value):
        self._progress = max(0, min(100, value))
        self.update()

    progress = Property(float, get_progress, set_progress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, 6, 6)
        painter.fillPath(path, QColor(0, 0, 0, 20))
        if self._progress > 0:
            progress_width = int(self.width() * self._progress / 100)
            progress_path = QPainterPath()
            progress_rect = (0, 0, progress_width, self.height())
            progress_path.addRoundedRect(*progress_rect, 6, 6)
            gradient = QLinearGradient(0, 0, progress_width, 0)
            gradient.setColorAt(0, QColor(255, 215, 0))
            gradient.setColorAt(1, QColor(255, 200, 0))
            painter.fillPath(progress_path, QBrush(gradient))
    
    def cleanup(self):
        if self._animation:
            self._animation.stop()
            self._animation.deleteLater()
            self._animation = None


class SplashWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(800, 480)
        self._timers = []
        self._effects = []

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

        container = QFrame(self)
        container.setGeometry(0, 0, self.width(), self.height())
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 40px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 20, 50, 80))
        shadow.setOffset(0, 15)
        container.setGraphicsEffect(shadow)
        self._effects.append(shadow)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(__file__), "latigo.png")
        if os.path.exists(logo_path):
            reader = QImageReader(logo_path)
            reader.setAutoTransform(True)
            reader.setQuality(100)
            image = reader.read()
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                pixmap.setDevicePixelRatio(self.devicePixelRatio())
                scaled_pixmap = pixmap.scaled(
                    1000, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(scaled_pixmap)
            else:
                logo_label.setText("📱 Latigo Teacher")
                logo_label.setStyleSheet("font-size: 48px; color: #1e2f48; font-weight: bold;")
        else:
            logo_label.setText("📱 Latigo Teacher")
            logo_label.setStyleSheet("font-size: 48px; color: #1e2f48; font-weight: bold;")
        layout.addWidget(logo_label)

        self.loading_text = QLabel("Loading Latigo Teacher Platform...")
        self.loading_text.setAlignment(Qt.AlignCenter)
        self.loading_text.setStyleSheet("font-size: 16px; color: #4285F4; margin-top: 10px;")
        layout.addWidget(self.loading_text)

        self.progress_bar = ProgressFill()
        self.progress_bar.setMinimumWidth(800)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

    def set_progress(self, value):
        self.progress_bar.set_progress(value)

    def set_loading_text(self, text):
        self.loading_text.setText(text)

    def cleanup(self):
        TimerCleanup.cleanup_all_timers(self)
        for effect in self._effects:
            effect.deleteLater()
        self._effects.clear()
        self.progress_bar.cleanup()


class MessageBoxInterceptor:
    @staticmethod
    def install():
        original_critical = QMessageBox.critical
        original_information = QMessageBox.information
        original_warning = QMessageBox.warning
        original_question = QMessageBox.question
        original_about = QMessageBox.about

        @staticmethod
        def patched_critical(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
            msg_box = QMessageBox(parent)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(buttons)
            msg_box.setDefaultButton(defaultButton)
            MessageInterceptorStyler.apply_style(msg_box)
            return msg_box.exec()

        @staticmethod
        def patched_information(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
            msg_box = QMessageBox(parent)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(buttons)
            msg_box.setDefaultButton(defaultButton)
            MessageInterceptorStyler.apply_style(msg_box)
            return msg_box.exec()

        @staticmethod
        def patched_warning(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
            msg_box = QMessageBox(parent)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(buttons)
            msg_box.setDefaultButton(defaultButton)
            MessageInterceptorStyler.apply_style(msg_box)
            return msg_box.exec()

        @staticmethod
        def patched_question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.NoButton):
            msg_box = QMessageBox(parent)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(buttons)
            msg_box.setDefaultButton(defaultButton)
            MessageInterceptorStyler.apply_style(msg_box)
            return msg_box.exec()

        @staticmethod
        def patched_about(parent, title, text):
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(QMessageBox.Ok)
            MessageInterceptorStyler.apply_style(msg_box)
            msg_box.exec()

        QMessageBox.critical = patched_critical
        QMessageBox.information = patched_information
        QMessageBox.warning = patched_warning
        QMessageBox.question = patched_question
        QMessageBox.about = patched_about


class MessageInterceptorStyler:
    @staticmethod
    def apply_style(msg_box):
        msg_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        msg_box.setAttribute(Qt.WA_TranslucentBackground)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: transparent; }
            QMessageBox QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                border: 0.5px solid rgba(0, 0, 0, 0.1);
            }
            QLabel#qt_msgbox_label {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                font-size: 13px;
                color: #1d1d1f;
                padding: 20px 20px 10px 20px;
                min-width: 300px;
                max-width: 400px;
            }
            QLabel#qt_msgboxex_icon_label { padding-left: 20px; }
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                font-size: 13px;
                font-weight: 500;
                min-width: 70px;
                min-height: 30px;
            }
            QPushButton:hover { background-color: #0077ed; }
            QPushButton:pressed { background-color: #0068c9; }
            QPushButton[text="Cancel"], QPushButton[text="No"] {
                background-color: #e9e9ed;
                color: #1d1d1f;
            }
            QPushButton[text="Cancel"]:hover, QPushButton[text="No"]:hover {
                background-color: #d9d9e0;
            }
            QPushButton[text="Yes"], QPushButton[text="OK"] {
                background-color: #0071e3;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 8)
        msg_box.setGraphicsEffect(shadow)

        icon = msg_box.icon()
        if icon == QMessageBox.Critical:
            msg_box.setStyleSheet(msg_box.styleSheet() + """
                QPushButton { background-color: #ff3b30; }
                QPushButton:hover { background-color: #ff5f57; }
                QPushButton:pressed { background-color: #e6352b; }
            """)
        elif icon == QMessageBox.Warning:
            msg_box.setStyleSheet(msg_box.styleSheet() + """
                QPushButton { background-color: #ffcc00; color: #1d1d1f; }
                QPushButton:hover { background-color: #ffd633; }
                QPushButton:pressed { background-color: #e6b800; }
            """)
        elif icon == QMessageBox.Information:
            msg_box.setStyleSheet(msg_box.styleSheet() + """
                QPushButton { background-color: #34c759; }
                QPushButton:hover { background-color: #3dda6a; }
                QPushButton:pressed { background-color: #2fb350; }
            """)


# ============================================================
# Startup Worker – loads only needed modules
# ============================================================
class StartupWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(dict)

    def run(self):
        result = {}

        def step(percent, status_text=None, key=None, value=None):
            self.progress.emit(percent)
            if status_text:
                self.status.emit(status_text)
            if key is not None:
                result[key] = value

        step(5, "Setting up directories...")
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        result['BASE_DIR'] = BASE_DIR

        # Account directory
        ACCOUNT_DIR = os.path.join(BASE_DIR, "account")
        if os.path.exists(ACCOUNT_DIR):
            if ACCOUNT_DIR not in sys.path:
                sys.path.insert(0, ACCOUNT_DIR)
            init_file = os.path.join(ACCOUNT_DIR, "__init__.py")
            if not os.path.exists(init_file):
                try:
                    with open(init_file, 'w') as f:
                        f.write('# Account package\n')
                except Exception as e:
                    print(f"⚠️ Could not create __init__.py: {e}")
        result['ACCOUNT_DIR'] = ACCOUNT_DIR

        ICONS_DIR = os.path.join(BASE_DIR, "icons")
        result['ICONS_DIR'] = ICONS_DIR

        step(10, "Loading token manager...")
        try:
            from token_manager import token_manager, get_current_room, get_available_rooms, set_token, clear_token, get_auth_headers, sync_token_with_server, sync_if_needed
            result['TOKEN_MANAGER_AVAILABLE'] = True
            result['token_manager'] = token_manager
            result['get_current_room'] = get_current_room
            result['get_available_rooms'] = get_available_rooms
            result['set_token'] = set_token
            result['clear_token'] = clear_token
            result['get_auth_headers'] = get_auth_headers
            result['sync_token_with_server'] = sync_token_with_server
            result['sync_if_needed'] = sync_if_needed
            print("✅ Central TokenManager imported")
        except ImportError as e:
            print(f"⚠️ TokenManager not available: {e}")
            result['TOKEN_MANAGER_AVAILABLE'] = False
            def dummy(*args, **kwargs): return None
            result['get_current_room'] = lambda: "room1"
            result['get_available_rooms'] = lambda: ["room1"]
            result['set_token'] = dummy
            result['clear_token'] = dummy
            result['get_auth_headers'] = lambda: {}
            result['sync_token_with_server'] = lambda *a, **kw: False
            result['sync_if_needed'] = lambda *a, **kw: False

        step(15, "Loading account modules (NEW versions)...")
        ACCOUNT_AVAILABLE = False
        AccountTokenManager = None
        ApiWorker = None
        LoginWindow = None
        MultiStepFormWindow = None
        ModernAccountPage = None
        account_config = None
        sound_manager = None
        try:
            from account.client2 import TokenManager as AccountTokenManager
            from account.ApiWorker import ApiWorker
            from account.LoginWindow import LoginWindow
            from account.MultiStepFormWindow import MultiStepFormWindow
            from account.ModernAccountPage import ModernAccountPage
            from account.account_config import account_config
            from account.SoundManager import sound_manager
            ACCOUNT_AVAILABLE = True
            print("✅ Account modules (new) imported")
        except ImportError as e:
            print(f"⚠️ Account import failed: {e}")
        result['ACCOUNT_AVAILABLE'] = ACCOUNT_AVAILABLE
        result['AccountTokenManager'] = AccountTokenManager
        result['ApiWorker'] = ApiWorker
        result['LoginWindow'] = LoginWindow
        result['MultiStepFormWindow'] = MultiStepFormWindow
        result['ModernAccountPage'] = ModernAccountPage
        result['account_config'] = account_config
        result['sound_manager'] = sound_manager

        step(20, "Skipping StudentManager module (not needed)...")
        result['STUDENT_MANAGER_AVAILABLE'] = False
        result['StudentManagerWidget'] = None
        print("⏭️ StudentManager disabled")

        # ===== LOAD TEACHER SELECTOR =====
        step(22, "Loading teacher selector...")
        TEACHER_SELECTOR_AVAILABLE = False
        TeacherSelectorDialog = None
        try:
            from teacherselector import TeacherSelectorDialog
            TEACHER_SELECTOR_AVAILABLE = True
            print("✅ TeacherSelectorDialog loaded")
        except ImportError as e:
            print(f"⚠️ TeacherSelectorDialog import failed: {e}")
        result['TEACHER_SELECTOR_AVAILABLE'] = TEACHER_SELECTOR_AVAILABLE
        result['TeacherSelectorDialog'] = TeacherSelectorDialog

# ===== LOAD QUIZ MODULE (teacher version) =====
        step(25, "Loading quiz module (teacher version)...")
        QUIZ_AVAILABLE = False
        QuizApp = None
        try:
            # Import the wrapper QuizApp from quiz.py
            from quiz import QuizApp
            QUIZ_AVAILABLE = True
            print("✅ Teacher Quiz module (QuizApp) imported successfully")
        except ImportError as e:
            print(f"⚠️ Teacher Quiz import failed: {e}")
            # Try to load from file path as fallback
            try:
                quiz_dir = os.path.join(BASE_DIR, "quiz")
                if os.path.exists(quiz_dir) and quiz_dir not in sys.path:
                    sys.path.insert(0, quiz_dir)
                quiz_path = os.path.join(quiz_dir, "quiz.py")
                if os.path.exists(quiz_path):
                    spec = importlib.util.spec_from_file_location("quiz_module", quiz_path)
                    quiz_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(quiz_module)
                    if hasattr(quiz_module, 'QuizApp'):
                        QuizApp = quiz_module.QuizApp
                        QUIZ_AVAILABLE = True
                        print("✅ QuizApp loaded from file path")
                    else:
                        print("⚠️ QuizApp not found in quiz.py")
                else:
                    print(f"⚠️ quiz/quiz.py not found at: {quiz_path}")
            except Exception as e2:
                print(f"⚠️ Quiz not available: {e2}")
        result['QUIZ_AVAILABLE'] = QUIZ_AVAILABLE
        result['QuizApp'] = QuizApp

        # ===== LOAD POLL MODULE – WITHOUT TEACHER WRAPPER =====
        step(30, "Loading poll module (student version, no teacher wrapper)...")
        POLL_AVAILABLE = False
        PollApp = None

        try:
            poll_dir = os.path.join(BASE_DIR, "poll")
            if os.path.exists(poll_dir) and poll_dir not in sys.path:
                sys.path.insert(0, poll_dir)
            poll_path = os.path.join(poll_dir, "poll.py")
            if os.path.exists(poll_path):
                spec = importlib.util.spec_from_file_location("poll_module", poll_path)
                poll_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(poll_module)
                
                # Try to load StudentWindow or any available window class
                if hasattr(poll_module, 'StudentWindow'):
                    PollApp = poll_module.StudentWindow
                    POLL_AVAILABLE = True
                    print("✅ Poll module (StudentWindow) loaded successfully")
                elif hasattr(poll_module, 'PollWindow'):
                    PollApp = poll_module.PollWindow
                    POLL_AVAILABLE = True
                    print("✅ Poll module (PollWindow) loaded successfully")
                elif hasattr(poll_module, 'MainWindow'):
                    PollApp = poll_module.MainWindow
                    POLL_AVAILABLE = True
                    print("✅ Poll module (MainWindow) loaded successfully")
                else:
                    # Fallback: try to find any QWidget class in the module
                    for attr_name in dir(poll_module):
                        attr = getattr(poll_module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, QWidget) and attr_name != 'QWidget':
                            PollApp = attr
                            POLL_AVAILABLE = True
                            print(f"✅ Poll module ({attr_name}) loaded successfully")
                            break
            else:
                print(f"⚠️ poll/poll.py not found at: {poll_path}")
        except Exception as e:
            print(f"⚠️ Poll import failed: {e}")

        result['POLL_AVAILABLE'] = POLL_AVAILABLE
        result['PollApp'] = PollApp

        # ===== SKIP AI Dashboard (eyes) =====
        step(35, "Skipping AI Dashboard (eyes) module...")
        result['AI_DASHBOARD_AVAILABLE'] = False
        result['AiDashboard'] = None
        print("⏭️ AI Dashboard disabled")

        # ===== SKIP Whiteboard =====
        step(40, "Skipping Whiteboard module...")
        result['WHITEBOARD_AVAILABLE'] = False
        result['WhiteboardApp'] = None
        print("⏭️ Whiteboard disabled")

        # ===== SKIP Feedback =====
        step(45, "Skipping Feedback module...")
        result['FEEDBACK_AVAILABLE'] = False
        result['FeedbackForm'] = None
        result['RecentFeedbackPanel'] = None
        result['OrbBackground'] = None
        print("⏭️ Feedback disabled")

        # ===== LOAD VIDEO STREAM (if needed) =====
        step(50, "Loading video stream module...")
        VIDEO_STREAM_AVAILABLE = False
        VideoWindow = None
        try:
            streamer_path = os.path.join(BASE_DIR, "stream1", "streamer.py")
            if os.path.exists(streamer_path):
                spec = importlib.util.spec_from_file_location("streamer", streamer_path)
                streamer_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(streamer_module)
                if hasattr(streamer_module, 'VideoWindow'):
                    VideoWindow = streamer_module.VideoWindow
                    VIDEO_STREAM_AVAILABLE = True
                    print("✅ VideoWindow imported")
        except Exception as e:
            print(f"❌ Stream module error: {e}")
        result['VIDEO_STREAM_AVAILABLE'] = VIDEO_STREAM_AVAILABLE
        result['VideoWindow'] = VideoWindow

        step(55, "Checking for existing token...")
        token = None
        from_txt = False
        if ACCOUNT_AVAILABLE:
            token_txt_path = os.path.join(ACCOUNT_DIR, "token.txt")
            if os.path.exists(token_txt_path):
                try:
                    with open(token_txt_path, 'r', encoding='utf-8') as f:
                        token = f.read().strip()
                    if token:
                        from_txt = True
                        print("📄 token.txt found")
                except Exception as e:
                    print(f"Failed to read token.txt: {e}")
            if not token and AccountTokenManager:
                token_data = AccountTokenManager.load_tokens()
                if token_data:
                    token = token_data.get("access_token")
                    print("📁 Saved tokens found")
        result['token'] = token
        result['from_txt'] = from_txt

        step(60, "Validating token...")
        token_valid = False
        user_data = None
        if token and ACCOUNT_AVAILABLE and account_config:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get(f"{config.API_BASE_URL}/api/token/validate",
                                   headers=headers, timeout=5)
                if resp.status_code == 200 and resp.json().get("success"):
                    token_valid = True
                    user_data = resp.json().get("data", {})
                    print("✅ Token validated")
                else:
                    print("❌ Token invalid")
                    if AccountTokenManager:
                        AccountTokenManager.clear_tokens()
            except Exception as e:
                print(f"Token validation error: {e}")
        result['token_valid'] = token_valid
        result['user_data'] = user_data

        # ===== LOAD CHAT AND CLASSROOM AFTER TOKEN VALIDATION =====
        step(62, "Loading Classroom and Chat modules (after token validation)...")
        CLASSROOM_AVAILABLE = False
        CHAT_AVAILABLE = False
        ClassroomWidget = None
        ChatWidget = None

        # Only load if token is valid
        if token_valid and token:
            print(f"✅ Token valid, loading Chat and Classroom modules...")
            
            # ===== Load Classroom =====
            classroom_path = os.path.join(BASE_DIR, "classroom", "classroom.py")
            if os.path.exists(classroom_path):
                _, ClassroomWidget = load_module_from_path(
                    "classroom_module", 
                    classroom_path, 
                    "StreamViewer"
                )
                if ClassroomWidget:
                    CLASSROOM_AVAILABLE = True
                    print("✅ Classroom module loaded successfully")
            else:
                print(f"⚠️ classroom/classroom.py not found at: {classroom_path}")

            # ===== Load Chat =====
            
            if True:
              
                class EmbeddedChatWrapper(StudentChatClient):
                    def __init__(self, parent=None):
                            # Pass embedded=True to the original class
                        super().__init__(embedded=True)
                        self.setParent(parent)
                        self.setWindowFlags(Qt.Widget)
                    
                ChatWidget = EmbeddedChatWrapper
                CHAT_AVAILABLE = True
                print("✅ Chat module loaded successfully (embedded mode)")
            else:
                print(f"⚠️ chat/chat.py not found at: {chat_path}")
        else:
            print(f"⏭️ Skipping Chat and Classroom: token_valid={token_valid}, token={'Present' if token else 'Missing'}")

        result['CLASSROOM_AVAILABLE'] = CLASSROOM_AVAILABLE
        result['CHAT_AVAILABLE'] = CHAT_AVAILABLE
        result['ClassroomWidget'] = ClassroomWidget
        result['ChatWidget'] = ChatWidget

        print("\n" + "=" * 50)
        print("MODULE AVAILABILITY SUMMARY:")
        print(f"  ACCOUNT_AVAILABLE: {result.get('ACCOUNT_AVAILABLE', False)}")
        print(f"  QUIZ_AVAILABLE: {result.get('QUIZ_AVAILABLE', False)}")
        print(f"  POLL_AVAILABLE: {result.get('POLL_AVAILABLE', False)}")
        print(f"  VIDEO_STREAM_AVAILABLE: {result.get('VIDEO_STREAM_AVAILABLE', False)}")
        print(f"  CLASSROOM_AVAILABLE: {result.get('CLASSROOM_AVAILABLE', False)}")
        print(f"  CHAT_AVAILABLE: {result.get('CHAT_AVAILABLE', False)}")
        print(f"  TEACHER_SELECTOR_AVAILABLE: {result.get('TEACHER_SELECTOR_AVAILABLE', False)}")
        print("=" * 50 + "\n")

        step(100, "Loading complete!", key=None)
        self.finished.emit(result)


def send_join_room_request(room_id: str, api_base_url: str = None) -> tuple[bool, str, Optional[str]]:
    """
    Sends a join request to the server for the selected room/teacher.
    Returns (success: bool, message: str, room_name: Optional[str]).
    """
    import requests
    from token_manager import get_token, get_auth_headers
    
    token = get_token()
    if not token:
        return False, "No authentication token available", None
    
    if api_base_url is None:
        import config
        api_base_url = getattr(config, 'API_BASE_URL', 'https://localhost:8080')
    
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{api_base_url}/api/student/join-room",
            headers=headers,
            json={"room_id": room_id, "action": "join"},
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # Try to get room name from response
                room_name = None
                if "data" in data:
                    room_name = data["data"].get("room_name") or data["data"].get("room") or data["data"].get("roomId")
                if not room_name and "room" in data:
                    room_name = data.get("room")
                if not room_name:
                    room_name = room_id  # Fallback to the requested room ID
                return True, data.get("message", "Joined successfully"), room_name
            else:
                return False, data.get("message", "Teacher rejected the join request"), None
        elif response.status_code == 403:
            return False, "You have been blocked from this room or need teacher approval", None
        elif response.status_code == 404:
            return False, "Room not found on server", None
        elif response.status_code == 409:
            return False, "You are already in this room", None
        else:
            return False, f"Server error ({response.status_code})", None
            
    except requests.exceptions.Timeout:
        return False, "Connection timeout while contacting server", None
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server", None
    except Exception as e:
        return False, f"Network error: {str(e)}", None


def ensure_room_selected(result, max_attempts=3):
    """
    Show teacher selection dialog if no current room is set.
    After the student picks a teacher, it sends a join request to the server.
    """
    token_manager = result.get('token_manager')
    if not token_manager:
        print("⚠️ No token manager available, cannot select room")
        QMessageBox.warning(
            None, 
            "Error", 
            "Token manager not available. Please restart the application."
        )
        return False

    if not token_manager.is_authenticated():
        print("⚠️ Token is no longer valid, cannot select room")
        QMessageBox.warning(
            None, 
            "Session Expired", 
            "Your session has expired. Please login again."
        )
        result['token_valid'] = False
        return False

    current_room = token_manager.get_current_room()
    available_rooms = token_manager.get_available_rooms()

    print(f"📋 Token Manager Info:")
    print(f"   - Current room: {current_room}")
    print(f"   - Available rooms: {available_rooms}")
    print(f"   - Is authenticated: {token_manager.is_authenticated()}")
    print(f"   - Has room selected: {token_manager.is_room_selected()}")

    if current_room and current_room in available_rooms:
        print(f"✅ Room already selected: {current_room}")
        return True

    if available_rooms and len(available_rooms) > 0:
        print(f"📌 Auto-selecting first available room: {available_rooms[0]}")
        token_manager.set_current_room(available_rooms[0])
        return True

    # ============================================================
    # No room available — open Teacher Selector and JOIN via server
    # ============================================================
    print("📢 No room selected. Opening Teacher Selection dialog...")
    
    TeacherSelectorDialog = result.get('TeacherSelectorDialog')
    if not TeacherSelectorDialog:
        print("⚠️ TeacherSelectorDialog not available in result, trying to import...")
        try:
            from teacherselector import TeacherSelectorDialog as TSD
            TeacherSelectorDialog = TSD
            result['TeacherSelectorDialog'] = TeacherSelectorDialog
            print("✅ TeacherSelectorDialog imported dynamically")
        except ImportError as e:
            print(f"❌ Failed to import TeacherSelectorDialog: {e}")
            # Show error and let user retry
            retry_box = QMessageBox(None)
            retry_box.setWindowTitle("Error Loading Teacher Selection")
            retry_box.setIcon(QMessageBox.Critical)
            retry_box.setText("The teacher selection dialog could not be loaded.")
            retry_box.setInformativeText(
                "Please make sure the file 'teacherselector.py' exists in the application folder.\n\n"
                "Click 'Retry' to try again, or 'Exit' to close the application."
            )
            retry_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Close)
            retry_box.setDefaultButton(QMessageBox.Retry)
            retry_box.setStyleSheet("""
                QMessageBox { background-color: #ffffff; border-radius: 12px; }
                QLabel { color: #1d1d1f; font-size: 13px; padding: 8px; }
                QPushButton { background-color: #0078d4; color: white; border: none; border-radius: 8px; padding: 8px 20px; font-size: 13px; font-weight: 500; min-width: 80px; }
                QPushButton:hover { background-color: #005a9e; }
                QPushButton[text="Close"] { background-color: #e9e9ed; color: #1d1d1f; }
                QPushButton[text="Close"]:hover { background-color: #d9d9e0; }
            """)
            if retry_box.exec() == QMessageBox.Retry:
                # Recursive call after import attempt (avoid infinite recursion)
                return ensure_room_selected(result, max_attempts - 1)
            else:
                return False

    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        print(f"📢 Attempt {attempt} of {max_attempts} to select and join room...")
        
        try:
            # Create the dialog
            dialog = TeacherSelectorDialog()
            result_code = dialog.exec()
            
            if result_code == QDialog.Accepted:
                room = dialog.get_selected_room()
                if not room:
                    print("⚠️ No room selected by user")
                    reply = QMessageBox.question(
                        None, 
                        "No Room Selected",
                        "No teacher was selected.\n\nDo you want to try again?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.No:
                        return False
                    continue
                
                print(f"✅ User selected room: {room}")
                print(f"📤 Sending join request to server for room: {room}...")
                
                # SEND JOIN REQUEST TO SERVER
                success, message, room_name = send_join_room_request(room)
                
                if success:
                    print(f"✅ Server accepted join: {message}")
                    final_room = room_name if room_name else room
                    token_manager.add_room(final_room)
                    token_manager.set_current_room(final_room)
                    print(f"✅ Room joined and saved: {final_room}")
                    return True
                else:
                    print(f"❌ Server rejected join: {message}")
                    
                    # Show error and let student try another teacher
                    retry_box = QMessageBox(None)
                    retry_box.setWindowTitle("Cannot Join Room")
                    retry_box.setIcon(QMessageBox.Warning)
                    retry_box.setText(f"Could not join room:\n\n{message}")
                    retry_box.setInformativeText(
                        "The teacher may have blocked you, the room may be full, "
                        "or your request was denied.\n\n"
                        "Would you like to pick another teacher and try again?"
                    )
                    retry_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    retry_box.setDefaultButton(QMessageBox.Yes)
                    retry_box.setStyleSheet("""...""")  # same style as before
                    
                    if retry_box.exec() == QMessageBox.Yes:
                        continue
                    else:
                        if attempt >= max_attempts:
                            QMessageBox.warning(
                                None, 
                                "Selection Failed",
                                "You were unable to join a room after multiple attempts.\n\n"
                                "Please contact your teacher or try again later."
                            )
                        return False
            else:
                # Dialog cancelled
                print("⚠️ Room selection dialog was cancelled")
                if attempt < max_attempts:
                    reply = QMessageBox.question(
                        None, 
                        "Room Selection Required",
                        "You need to select a teacher to continue.\n\n"
                        "Do you want to try again?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.No:
                        return False
                else:
                    return False
                    
        except Exception as e:
            print(f"❌ Error in teacher selection: {e}")
            import traceback
            traceback.print_exc()
            if attempt < max_attempts:
                reply = QMessageBox.question(
                    None, 
                    "Error",
                    f"An error occurred:\n\n{str(e)}\n\nDo you want to try again?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.No:
                    return False
            else:
                QMessageBox.critical(
                    None, 
                    "Error",
                    f"Failed to select a room after {max_attempts} attempts."
                )
                return False

    return False





# ============================================================
# Floating Widgets (Keep only Stream and Notification)
# ============================================================
class FloatingWidget(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.pinned = False
        self.drag_position = None
        self._effects = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background: rgba(255,255,255,0.95);
                border: 0.5px solid rgba(0,0,0,0.1);
                border-radius: 14px;
                backdrop-filter: blur(20px);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        self._effects.append(shadow)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("floatingTitleBar")
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet("""
            QFrame#floatingTitleBar {
                background-color: transparent;
                border-bottom: 1px solid rgba(0,0,0,0.1);
            }
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: 500; font-size: 13px; color: #1d1d1f;")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.pin_button = QPushButton()
        self.pin_button.setFixedSize(24, 24)
        self.pin_button.setCursor(Qt.PointingHandCursor)
        self.pin_button.setCheckable(True)
        self.pin_button.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 4px; }
            QPushButton:hover { background: rgba(0,0,0,0.05); }
        """)
        self.pin_button.toggled.connect(self.on_pin_toggled)
        title_layout.addWidget(self.pin_button)
        self.title_bar.hide()
        self.container_layout.addWidget(self.title_bar)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addLayout(self.content_layout)

        self.content_widget = None
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.hide()

    def enable_title_bar(self, title):
        self.title_bar.show()
        self.title_label.setText(title)
        self.update_pin_icon(False)
        self.title_bar.mousePressEvent = self.title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release
        self.update_size()

    def update_pin_icon(self, pinned):
        icon_name = "pin.svg" if pinned else "unpin.svg"
        icon_path = os.path.join(self.config.get('ICONS_DIR', ''), icon_name)
        if os.path.exists(icon_path):
            self.pin_button.setIcon(QIcon(icon_path))
            self.pin_button.setIconSize(QSize(16, 16))
        else:
            self.pin_button.setText("📌" if pinned else "📍")

    def on_pin_toggled(self, checked):
        self.pinned = checked
        self.update_pin_icon(checked)
        self.set_pinned_mode(checked)

    def set_pinned_mode(self, pinned):
        self.hide()
        geo = self.geometry()
        if pinned:
            self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setGeometry(geo)
        self.show()

    def is_pinned(self):
        return self.pinned

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def title_bar_mouse_release(self, event):
        self.drag_position = None

    def set_content(self, widget):
        if self.content_widget:
            self.content_layout.removeWidget(self.content_widget)
            self.content_widget.deleteLater()
        self.content_widget = widget
        self.content_layout.addWidget(widget)
        self.update_size()

    def update_size(self):
        self.container.adjustSize()
        self.setFixedSize(self.container.size())

    def show_at_position(self, global_pos):
        screen = QApplication.primaryScreen().geometry()
        x = global_pos.x() - self.width()
        y = global_pos.y()
        if y + self.height() > screen.height():
            y = screen.height() - self.height() - 20
        target_rect = QRect(x, y, self.width(), self.height())
        start_rect = QRect(global_pos.x(), global_pos.y(), 0, self.height())
        self.setGeometry(start_rect)
        self.show()
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(target_rect)
        self.animation.start()

    def hide_animated(self):
        current = self.geometry()
        end_rect = QRect(current.right(), current.y(), 0, current.height())
        self.animation.setStartValue(current)
        self.animation.setEndValue(end_rect)
        def finish_hide():
            if not self.animation or self.animation.state() != QPropertyAnimation.Running:
                self.hide()
        try:
            self.animation.finished.disconnect()
        except Exception:
            pass
        self.animation.finished.connect(finish_hide)
        self.animation.start()

    def cleanup(self):
        if hasattr(self, 'animation') and self.animation:
            self.animation.stop()
            self.animation.deleteLater()
        for effect in self._effects:
            effect.deleteLater()
        self._effects.clear()
        TimerCleanup.cleanup_all_timers(self)
        if self.content_widget:
            if hasattr(self.content_widget, 'shutdown'):
                self.content_widget.shutdown()
            elif hasattr(self.content_widget, 'close'):
                self.content_widget.close()
            self.content_widget.deleteLater()
        self.hide()
        self.deleteLater()


class StreamFloatingWidget(FloatingWidget):
    def __init__(self, config, parent=None):
        super().__init__(config, parent)
        print("📺 Creating StreamFloatingWidget...")
        if config.get('VIDEO_STREAM_AVAILABLE'):
            VideoWindow = config['VideoWindow']
            try:
                self.video_window = VideoWindow()
                self.video_window.setWindowFlags(Qt.Widget)
                self.video_window.setParent(self.container)
                self.video_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.set_content(self.video_window)
                self.setFixedSize(420, 200)
                print("✅ StreamFloatingWidget created")
            except Exception as e:
                label = QLabel(f"Stream error: {e}")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #ff3b30; padding:20px;")
                self.set_content(label)
        else:
            label = QLabel("Stream module not available")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #86868b; padding:20px;")
            self.set_content(label)

    def shutdown(self):
        if hasattr(self, 'video_window'):
            if hasattr(self.video_window, 'shutdown'):
                self.video_window.shutdown()
            elif hasattr(self.video_window, 'close'):
                self.video_window.close()
        self.cleanup()


class NotificationFloatingWidget(FloatingWidget):
    def __init__(self, config, parent=None):
        super().__init__(config, parent)
        self.panel = NotificationPanel()
        self.panel.setParent(self.container)
        self.set_content(self.panel)

    def shutdown(self):
        if self.panel:
            self.panel.cleanup()
        self.cleanup()


class NotificationPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: white; border: none; border-radius: 14px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Notifications")
        header.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f; padding-bottom: 8px; border-bottom: 0.5px solid rgba(255,255,255,0.3);")
        layout.addWidget(header)
        
        # Create placeholder widget for "coming soon" message
        placeholder_widget = QWidget()
        placeholder_widget.setFixedHeight(200)
        placeholder_widget.setStyleSheet("QWidget { background-color: white; border-radius: 10px; }")
        
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel("🔜")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(icon_label)
        
        # Main "coming soon" text - English
        coming_soon_label = QLabel("This feature coming soon")
        coming_soon_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f;")
        coming_soon_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(coming_soon_label)
        
        # Korean translation
        korean_label = QLabel("이 기능은 곧 제공됩니다")
        korean_label.setStyleSheet("font-size: 14px; font-weight: 400; color: #86868b;")
        korean_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(korean_label)
        
        # Subtext - English
        subtext_label = QLabel("We're working on something amazing!")
        subtext_label.setStyleSheet("font-size: 12px; color: #86868b;")
        subtext_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(subtext_label)
        
        # Korean subtext
        korean_subtext = QLabel("놀라운 무언가를 준비 중입니다!")
        korean_subtext.setStyleSheet("font-size: 11px; color: #a0a0a6;")
        korean_subtext.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(korean_subtext)
        
        layout.addWidget(placeholder_widget)
        self.notification_widgets = [placeholder_widget]
        
        self.setFixedSize(340, 380)
    
    def show_coming_soon(self):
        """Show a coming soon message when user interacts"""
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Coming Soon / 곧 제공됩니다")
        msg.setText("🔜 This feature coming soon!\n\n이 기능은 곧 제공됩니다!")
        msg.setInformativeText("We're working hard to bring you this feature. Stay tuned!\n\n여러분께 이 기능을 제공하기 위해 열심히 노력하고 있습니다. 기대해 주세요!")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def cleanup(self):
        for widget in self.notification_widgets:
            widget.deleteLater()
        self.notification_widgets.clear()
# ============================================================
# Tab content widgets (module pages) - Removed ChatPage, using ChatPanel from ui.py
# ============================================================
class PlaceholderPage(QWidget):
    def __init__(self, title, message="This module is not available yet.", icon="📄", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 80px; color: rgba(255,255,255,0.8); background: transparent;")
        layout.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 28px; font-weight: 600; color: white; letter-spacing: -0.5px; background: transparent;")
        layout.addWidget(title_label)
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 15px; color: rgba(255,255,255,0.7); padding: 10px 30px; background: transparent;")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        badge = QFrame()
        badge.setFixedSize(120, 32)
        badge.setStyleSheet("QFrame { background: rgba(255,255,255,0.2); border-radius: 16px; }")
        badge_layout = QHBoxLayout(badge)
        badge_label = QLabel("🚧 Coming Soon")
        badge_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; font-weight: 500; background: transparent;")
        badge_layout.addWidget(badge_label)
        layout.addWidget(badge)


class ClassroomPage(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if config.get('CLASSROOM_AVAILABLE'):
            try:
                StreamViewer = config['ClassroomWidget']
                self.stream_viewer = StreamViewer()
                self.stream_viewer.setParent(self)
                self.stream_viewer.setWindowFlags(Qt.Widget)
                self.stream_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.stream_viewer.setStyleSheet("background: transparent;")
                layout.addWidget(self.stream_viewer)
                print("✅ ClassroomPage loaded")
            except Exception as e:
                layout.addWidget(QLabel(f"Classroom error: {e}"))
        else:
            layout.addWidget(PlaceholderPage("Classroom", "Live classroom stream viewer.", "📺"))

    def shutdown(self):
        if hasattr(self, 'stream_viewer') and self.stream_viewer:
            if hasattr(self.stream_viewer, 'close'):
                self.stream_viewer.close()
            self.stream_viewer = None

class QuizPage(QWidget):
        """
        Main quiz page for the teacher dashboard.
        Follows the same pattern as ClassroomPage, PollPage, etc.
        """
        def __init__(self, config=None, parent=None, embedded=False):
                super().__init__(parent)
                self.config = config or {}
                self.quiz_widget = None
                self.setAttribute(Qt.WA_StyledBackground, True)
                self.setStyleSheet("background: transparent;")
                
                # Main layout
                layout = QVBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                
                # Check if quiz module is available
                if self.config.get('QUIZ_AVAILABLE', False):
                        try:
                                # Get credentials from token_manager
                                student_name = get_username() or "Student"
                                room_id = get_current_room() or ROOM_ID
                                token = get_token() or ""
                                
                                # Try to get QuizWidget from various sources
                                QuizWidgetClass = None
                                
                                # First, try to get it from the current module's global scope
                                import sys
                                current_module = sys.modules.get(__name__)
                                if current_module and hasattr(current_module, 'QuizWidget'):
                                        QuizWidgetClass = current_module.QuizWidget
                                        print("✅ QuizWidget found in current module")
                                else:
                                        # Try to get it from the global scope
                                        if 'QuizWidget' in globals():
                                                QuizWidgetClass = globals()['QuizWidget']
                                                print("✅ QuizWidget found in globals")
                                        else:
                                                # Try to import it from the module
                                                import importlib
                                                try:
                                                        # Reload the module to ensure it's fresh
                                                        if __name__ in sys.modules:
                                                                module = importlib.reload(sys.modules[__name__])
                                                                if hasattr(module, 'QuizWidget'):
                                                                        QuizWidgetClass = module.QuizWidget
                                                                        print("✅ QuizWidget found after reload")
                                                except Exception as reload_error:
                                                        print(f"⚠️ Could not reload module: {reload_error}")
                                
                                if QuizWidgetClass is None:
                                        # Last resort: try to import from quiz module
                                        try:
                                                import quiz
                                                if hasattr(quiz, 'QuizWidget'):
                                                        QuizWidgetClass = quiz.QuizWidget
                                                        print("✅ QuizWidget found in quiz module import")
                                        except ImportError:
                                                pass
                                
                                if QuizWidgetClass is None:
                                        raise NameError("QuizWidget class could not be found")
                                
                                # Create the quiz widget
                                self.quiz_widget = QuizWidgetClass(
                                        student_name=student_name,
                                        room_id=room_id,
                                        token=token,
                                        exam_data=None,
                                        parent=self
                                )
                                self.quiz_widget.setStyleSheet("background: transparent;")
                                layout.addWidget(self.quiz_widget)
                                print("✅ QuizPage loaded successfully")
                                
                        except NameError as ne:
                                print(f"❌ QuizWidget not found: {ne}")
                                # Show a fallback message
                                fallback = QLabel("Quiz module is not available.\nPlease check the installation.")
                                fallback.setAlignment(Qt.AlignCenter)
                                fallback.setStyleSheet("color: #ff6b6b; font-size: 16px; padding: 40px;")
                                layout.addWidget(fallback)
                        except Exception as e:
                                print(f"❌ Failed to load quiz: {e}")
                                import traceback
                                traceback.print_exc()
                                layout.addWidget(QLabel(f"Quiz error: {e}"))
                else:
                        layout.addWidget(PlaceholderPage("Quiz", "Create and manage quizzes.", "📝"))
        
        def get_embedded_widget(self):
                """Return the embedded widget for compatibility with main3.py."""
                return self.quiz_widget
        
        def shutdown(self):
                """Clean shutdown - called by parent dashboard."""
                if self.quiz_widget:
                        try:
                                if hasattr(self.quiz_widget, 'safe_exit'):
                                        self.quiz_widget.safe_exit()
                                elif hasattr(self.quiz_widget, 'close'):
                                        self.quiz_widget.close()
                                self.quiz_widget = None
                                print("✅ QuizPage shut down successfully")
                        except Exception as e:
                                print(f"⚠️ Error shutting down quiz: {e}")
        
        def closeEvent(self, event):
                """Handle close event."""
                self.shutdown()
                event.accept()
class PollPage(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if config.get('POLL_AVAILABLE'):
            try:
                PollApp = config['PollApp']
                # Instantiate the poll class as is (no wrapper)
                self.poll_app = PollApp()
                self.poll_app.setParent(self)
                self.poll_app.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                if hasattr(self.poll_app, 'setStyleSheet'):
                    self.poll_app.setStyleSheet("background: transparent;")
                layout.addWidget(self.poll_app)
                print("✅ PollPage loaded (student poll, no teacher wrapper)")
            except Exception as e:
                layout.addWidget(QLabel(f"Poll error: {e}"))
        else:
            layout.addWidget(PlaceholderPage("Poll", "Real‑time student understanding surveys.", "📊"))

    def shutdown(self):
        if self.poll_app:
            if hasattr(self.poll_app, 'close'):
                self.poll_app.close()
            self.poll_app = None


class AccountIntegrationWidget(QWidget):
    login_successful = Signal()
    logout_requested = Signal()
    roomChanged = Signal()  # Signal to notify that room has changed (triggers restart)

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self.config = config or {}
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)
        self.stacked_widget = QStackedWidget()
        self.login_window = None
        self.registration_form = None
        self.dashboard_window = None

        self.stacked_widget.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        if self.config.get('ACCOUNT_AVAILABLE'):
            QTimer.singleShot(100, self.check_auto_login)
        else:
            self.show_error("Account system not available")

    def show_error(self, message):
        error_widget = QWidget()
        error_widget.setAttribute(Qt.WA_StyledBackground, True)
        error_widget.setStyleSheet("background: transparent;")
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignCenter)
        error_label = QLabel(f"⚠️ {message}")
        error_label.setStyleSheet("font-size: 16px; color: #ff3b30; background-color: rgba(255, 242, 240, 0.9); border: 0.5px solid #ffcdc9; border-radius: 12px; padding: 20px;")
        error_layout.addWidget(error_label)
        self.stacked_widget.addWidget(error_widget)
        self.stacked_widget.setCurrentWidget(error_widget)

    def check_auto_login(self):
        if not self.config.get('ACCOUNT_AVAILABLE'):
            self.show_login()
            return
        AccountTokenManager = self.config.get('AccountTokenManager')
        account_config = self.config.get('account_config')
        ACCOUNT_DIR = self.config.get('ACCOUNT_DIR')
        token_txt_path = os.path.join(ACCOUNT_DIR, "token.txt") if ACCOUNT_DIR else None
        if token_txt_path and os.path.exists(token_txt_path):
            try:
                with open(token_txt_path, 'r', encoding='utf-8') as f:
                    access_token = f.read().strip()
                if access_token:
                    print("token.txt found, validating...")
                    self.show_loading_screen()
                    if account_config:
                        account_config.CURRENT_TOKEN = access_token
                    self.validate_token_and_login(access_token, from_txt=True)
                    return
            except Exception as e:
                print(f"Failed to read token.txt: {e}")
        if AccountTokenManager:
            token_data = AccountTokenManager.load_tokens()
            if token_data:
                print("Found saved tokens, attempting auto-login...")
                self.show_loading_screen()
                user_id = token_data.get("user_id")
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                user_data = token_data.get("user_data")
                if account_config:
                    account_config.CURRENT_USER_ID = user_id
                    account_config.CURRENT_TOKEN = access_token
                    account_config.CURRENT_REFRESH_TOKEN = refresh_token
                    account_config.CURRENT_USER_DATA = user_data
                self.validate_token_and_login(access_token)
                return
        print("No saved tokens, showing login")
        self.show_login()

    def show_loading_screen(self):
        loading_widget = QWidget()
        loading_widget.setAttribute(Qt.WA_StyledBackground, True)
        loading_widget.setStyleSheet("background: transparent;")
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_label = QLabel("🔐 Checking authentication...")
        loading_label.setStyleSheet("font-size: 18px; font-weight: 500; color: #0071e3; margin-bottom: 20px; background: transparent;")
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setFixedWidth(300)
        progress.setStyleSheet("QProgressBar { border: 0.5px solid #e9e9ed; border-radius: 4px; height: 4px; background: rgba(0,0,0,0.1); } QProgressBar::chunk { background-color: #0071e3; border-radius: 4px; }")
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(progress)
        self.stacked_widget.addWidget(loading_widget)
        self.stacked_widget.setCurrentWidget(loading_widget)

    def validate_token_and_login(self, token, from_txt=False):
        account_config = self.config.get('account_config')
        ApiWorker = self.config.get('ApiWorker')
        AccountTokenManager = self.config.get('AccountTokenManager')
        api_base_url = getattr(account_config, 'API_BASE_URL', None) or config.API_BASE_URL

        def validate():
            try:
                headers = {"Authorization": f"Bearer {token}"}
                return requests.get(f"{api_base_url}/api/token/validate", headers=headers, timeout=5)
            except Exception as e:
                print(f"Token validation error: {e}")
                return None

        def on_response(response):
            for i in range(self.stacked_widget.count()):
                w = self.stacked_widget.widget(i)
                if w and hasattr(w, 'layout') and w.layout():
                    item = w.layout().itemAt(0)
                    if item and item.widget() and isinstance(item.widget(), QLabel) and "Checking authentication" in item.widget().text():
                        self.stacked_widget.removeWidget(w)
                        w.deleteLater()
                        break
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Token validated")
                    user_data = data.get("data", {})
                    if from_txt:
                        user_id = user_data.get("id")
                        if account_config:
                            account_config.CURRENT_USER_ID = user_id
                        if AccountTokenManager:
                            AccountTokenManager.save_tokens(user_id=user_id, access_token=token, refresh_token=None, expires_in=86400, user_data=user_data)
                    if self.config.get('TOKEN_MANAGER_AVAILABLE'):
                        username = user_data.get("username") or user_data.get("display_name") or user_data.get("email", "").split('@')[0]
                        set_token = self.config['set_token']
                        set_token(token=token, user_data=user_data, username=username)
                        try:
                            sync_token_with_server = self.config['sync_token_with_server']
                            sync_token_with_server(api_base_url)
                        except Exception as e:
                            print(f"Could not sync token: {e}")
                    self.show_dashboard()
                    return
            print("Token validation failed")
            if AccountTokenManager:
                AccountTokenManager.clear_tokens()
            if account_config:
                account_config.CURRENT_USER_ID = None
                account_config.CURRENT_TOKEN = None
                account_config.CURRENT_REFRESH_TOKEN = None
                account_config.CURRENT_USER_DATA = None
            if self.config.get('TOKEN_MANAGER_AVAILABLE'):
                clear_token = self.config['clear_token']
                clear_token()
            self.show_login()

        if not ApiWorker:
            self.show_login()
            return
        worker = ApiWorker(validate)
        worker.signals.result.connect(on_response)
        worker.signals.error.connect(lambda e: on_response(None))
        self.thread_pool.start(worker)

    def show_login(self):
        if not self.config.get('ACCOUNT_AVAILABLE') or not self.config.get('LoginWindow'):
            self.show_error("Login not available")
            return
        if self.login_window is None:
            LoginWindow = self.config['LoginWindow']
            self.login_window = LoginWindow(self)
            self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.setCurrentWidget(self.login_window)

    def show_registration(self):
        if not self.config.get('ACCOUNT_AVAILABLE') or not self.config.get('MultiStepFormWindow'):
            return
        sound_manager = self.config.get('sound_manager')
        if sound_manager:
            sound_manager.play_click()
        if self.registration_form is None:
            MultiStepFormWindow = self.config['MultiStepFormWindow']
            self.registration_form = MultiStepFormWindow(self)
            self.stacked_widget.addWidget(self.registration_form)
        self.stacked_widget.setCurrentWidget(self.registration_form)
        if hasattr(self.registration_form, 'reset_form'):
            self.registration_form.reset_form()

    def show_dashboard(self):
        if not self.config.get('ACCOUNT_AVAILABLE') or not self.config.get('ModernAccountPage'):
            self.show_error("Dashboard not available")
            return
        sound_manager = self.config.get('sound_manager')
        if sound_manager:
            sound_manager.play_success()
        
        if self.dashboard_window is None:
            ModernAccountPage = self.config['ModernAccountPage']
            self.dashboard_window = ModernAccountPage(self)
            self.dashboard_window.setAttribute(Qt.WA_StyledBackground, True)
            self.dashboard_window.setStyleSheet("background: transparent;")
            if hasattr(self.dashboard_window, 'logoutRequested'):
                self.dashboard_window.logoutRequested.connect(self._on_dashboard_logout)
            # Forward the roomChanged signal
            if hasattr(self.dashboard_window, 'roomChanged'):
                self.dashboard_window.roomChanged.connect(self.roomChanged.emit)
            self.stacked_widget.addWidget(self.dashboard_window)
        self.stacked_widget.setCurrentWidget(self.dashboard_window)

    def _on_dashboard_logout(self):
        """Handle logout signal from the dashboard - call our logout method."""
        self.on_logout()

    def on_login_success(self, user_data, tokens):
        if not self.config.get('ACCOUNT_AVAILABLE'):
            return
        AccountTokenManager = self.config.get('AccountTokenManager')
        account_config = self.config.get('account_config')
        ACCOUNT_DIR = self.config.get('ACCOUNT_DIR')
        user_id = user_data.get("id")
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 86400)
        if AccountTokenManager:
            AccountTokenManager.save_tokens(user_id, access_token, refresh_token, expires_in, user_data)
        if ACCOUNT_DIR:
            token_txt_path = os.path.join(ACCOUNT_DIR, "token.txt")
            try:
                with open(token_txt_path, 'w', encoding='utf-8') as f:
                    f.write(access_token)
            except Exception as e:
                print(f"Failed to write token.txt: {e}")
        if account_config:
            account_config.CURRENT_USER_ID = user_id
            account_config.CURRENT_TOKEN = access_token
            account_config.CURRENT_REFRESH_TOKEN = refresh_token
            account_config.CURRENT_USER_DATA = user_data
        if self.config.get('TOKEN_MANAGER_AVAILABLE'):
            username = user_data.get("username") or user_data.get("display_name") or user_data.get("email", "").split('@')[0]
            set_token = self.config['set_token']
            set_token(token=access_token, user_data=user_data, username=username)
            try:
                api_url = account_config.API_BASE_URL if account_config else config.API_BASE_URL
                sync_token_with_server = self.config['sync_token_with_server']
                sync_token_with_server(api_url)
            except Exception as e:
                print(f"Could not sync token: {e}")
        self.show_dashboard()
        self.login_successful.emit()

    def on_registration_success(self, user_data, tokens):
        self.on_login_success(user_data, tokens)

    def on_logout(self):
        """Secure logout – clears tokens and emits signal, does NOT show login inside the main window."""
        print("🔐 Secure logout started")
        
        # Clear authentication data from all sources
        AccountTokenManager = self.config.get('AccountTokenManager')
        account_config = self.config.get('account_config')
        ACCOUNT_DIR = self.config.get('ACCOUNT_DIR')
        
        if AccountTokenManager:
            AccountTokenManager.clear_tokens()
        
        if ACCOUNT_DIR:
            token_txt_path = os.path.join(ACCOUNT_DIR, "token.txt")
            try:
                if os.path.exists(token_txt_path):
                    os.remove(token_txt_path)
                    print(f"✅ Removed token.txt from {token_txt_path}")
            except Exception as e:
                print(f"⚠️ Failed to remove token.txt: {e}")
        
        if account_config:
            account_config.CURRENT_USER_ID = None
            account_config.CURRENT_TOKEN = None
            account_config.CURRENT_REFRESH_TOKEN = None
            account_config.CURRENT_USER_DATA = None
        
        if self.config.get('TOKEN_MANAGER_AVAILABLE'):
            clear_token = self.config['clear_token']
            clear_token()
        
        # Remove the dashboard widget from the stack
        if self.dashboard_window:
            self.stacked_widget.removeWidget(self.dashboard_window)
            self.dashboard_window.deleteLater()
            self.dashboard_window = None
        
        # Emit signal to notify the parent (IntegratedDashboard) to close the main window
        self.logout_requested.emit()
        
        # ❌ DO NOT call self.show_login() here – the main window will close,
        #    and the outer loop will reopen the authentication window as a separate window.

    def shutdown(self):
        if self.thread_pool:
            self.thread_pool.clear()
            self.thread_pool.waitForDone(3000)
        if self.dashboard_window and hasattr(self.dashboard_window, 'close'):
            self.dashboard_window.close()
        if self.registration_form and hasattr(self.registration_form, 'close'):
            self.registration_form.close()
        if self.login_window and hasattr(self.login_window, 'close'):
            self.login_window.close()
        self.dashboard_window = None
        self.registration_form = None
        self.login_window = None


# ============================================================
# Integrated Dashboard - Main Teacher Window
# ============================================================
class IntegratedDashboard(Dashboard):
    logoutRequested = Signal()
    
    def __init__(self, config: dict):
        self.config = config
        self._module_pages = {}
        self._page_index_map = {}
        self._floating_widgets = {}
        self._current_page = None
        self.logout_requested = False
        self._is_shutting_down = False
        self._chat_widget = None  # Store chat widget reference for the panel

        super().__init__()
        
        # ===== PRE-LOAD CHAT WIDGET AT STARTUP =====
        self._preload_chat_widget()
        
        self.test_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.test_shortcut.activated.connect(self._toggle_stream_panel)
        print("✅ Added keyboard shortcut Ctrl+Shift+S to toggle stream panel")
        
        print("\n" + "=" * 50)
        print("STREAM MODULE CHECK:")
        print(f"VIDEO_STREAM_AVAILABLE in config: {self.config.get('VIDEO_STREAM_AVAILABLE', False)}")
        print(f"VideoWindow in config: {self.config.get('VideoWindow', None)}")
        print("=" * 50 + "\n")
        
        self._setup_module_stack()
        self._connect_teacher_actions()
        self._override_close_button()
        self._setup_cleanup()

        # Connect roomChanged signal from account page to restart
        account_widget = self._module_pages.get("account")
        if account_widget and hasattr(account_widget, 'roomChanged'):
            account_widget.roomChanged.connect(self._restart_app)
        
        # Connect logout signal from account page
        if account_widget and hasattr(account_widget, 'logout_requested'):
            account_widget.logout_requested.connect(self._on_logout_from_account)

        # ===== FIX: Make Account page the default page =====
        if "account" in self._page_index_map:
            QTimer.singleShot(100, lambda: self._switch_to_page("account"))

        print("\n" + "=" * 50)
        print("INTEGRATED DASHBOARD INITIALIZED")
        print(f"ACCOUNT_AVAILABLE: {self.config.get('ACCOUNT_AVAILABLE', False)}")
        print(f"QUIZ_AVAILABLE: {self.config.get('QUIZ_AVAILABLE', False)}")
        print(f"POLL_AVAILABLE: {self.config.get('POLL_AVAILABLE', False)}")
        print(f"CLASSROOM_AVAILABLE: {self.config.get('CLASSROOM_AVAILABLE', False)}")
        print(f"CHAT_AVAILABLE: {self.config.get('CHAT_AVAILABLE', False)}")
        print(f"Available pages: {list(self._page_index_map.keys())}")
        print("=" * 50 + "\n")

    def _on_logout_from_account(self):
        """Handle logout from account widget – closes the main window."""
        print("📤 Logout signal received from account widget")
        self.logoutRequested.emit()

    def _restart_app(self):
        """Restart the application to apply room change."""
        print("🔄 Restarting application after room change...")
        QTimer.singleShot(500, lambda: restart_application())

    def _preload_chat_widget(self):
        """Pre-load the chat widget at application startup for use in ChatPanel."""
        print("\n" + "=" * 60)
        print("📱 PRE-LOADING CHAT WIDGET AT STARTUP")
        print("=" * 60)
        
        if self.config.get('CHAT_AVAILABLE') and self.config.get('ChatWidget'):
            try:
                ChatWidget = self.config['ChatWidget']
                # Create the chat widget but keep it hidden
                self._chat_widget = ChatWidget(self)
                self._chat_widget.setVisible(False)  # Hidden initially
                print("✅ Chat widget pre-loaded successfully")
                print(f"   Chat widget: {self._chat_widget}")
            except Exception as e:
                print(f"❌ Failed to pre-load chat widget: {e}")
                self._chat_widget = None
        else:
            print("⚠️ Chat module not available, skipping pre-load")
            self._chat_widget = None
        print("=" * 60 + "\n")

    def _override_close_button(self):
        close_btn = self.findChild(CloseButton)
        if close_btn:
            try:
                close_btn.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            close_btn.clicked.connect(self._secure_close)

    def _secure_close(self):
        close_application_securely("Close button clicked")

    def _setup_module_stack(self):
        for i in reversed(range(self.hero_layout.count())):
            item = self.hero_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.module_stack = QStackedWidget()
        self.module_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.module_stack.setStyleSheet("background: transparent; border: none;")

        # ===== CHAT REMOVED FROM PAGE CREATORS - now using ChatPanel from ui.py =====
        # In IntegratedDashboard._setup_module_stack

        page_creators = {
    "classroom": lambda: ClassroomPage(self.config),
    "quiz": lambda: self.config.get('QuizApp')(  # ← use QuizApp directly
        student_name=get_username() or "Student",
        room_id=get_current_room() or ROOM_ID,
        token=get_token() or "",
        exam_data=None,
        parent=self,
        embedded=True
    ),
    "poll": lambda: PollPage(self.config),
    "account": lambda: AccountIntegrationWidget(self, self.config),
        }
        
        print("\n" + "=" * 60)
        print("SETTING UP MODULE STACK:")
        
        for page_id, creator in page_creators.items():
            show_page = False
            
            if page_id == "account":
                show_page = True
                print(f"  {page_id}: account - always True")
            else:
                config_key = f"{page_id.upper()}_AVAILABLE"
                show_page = self.config.get(config_key, False)
                print(f"  {page_id}: checking {config_key} = {show_page}")
            
            if show_page:
                try:
                    print(f"    → Creating widget for {page_id}...")
                    widget = creator()
                    widget.setAttribute(Qt.WA_StyledBackground, True)
                    widget.setStyleSheet(widget.styleSheet() + "background: transparent; background-color: transparent;")
                    idx = self.module_stack.addWidget(widget)
                    self._module_pages[page_id] = widget
                    self._page_index_map[page_id] = idx
                    print(f"    ✅ Added page: {page_id} at index {idx}")
                except Exception as e:
                    print(f"    ❌ Failed to create page {page_id}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"    ⏭️ Skipping page: {page_id} (show_page=False)")

        print(f"\n📊 FINAL available pages: {list(self._page_index_map.keys())}")
        print("=" * 60 + "\n")

        if not self._module_pages:
            placeholder = PlaceholderPage("No Modules", "No teacher modules could be loaded.")
            self.module_stack.addWidget(placeholder)

        self.hero_layout.addWidget(self.module_stack)

    def _switch_to_page(self, page_id: str):
        """Switch to a specific page in the module stack."""
        if self._is_shutting_down:
            return
        if not hasattr(self, 'module_stack') or not self.module_stack:
            return
        
        # إذا كانت الصفحة غير موجودة، انتقل إلى صفحة الحساب (الافتراضية)
        if page_id not in self._page_index_map:
            print(f"⚠️ Page '{page_id}' not found. Available: {list(self._page_index_map.keys())}")
            
            # محاولة الانتقال إلى صفحة الحساب
            if "account" in self._page_index_map:
                print(f"   → Switching to default page (account)")
                self.module_stack.setCurrentIndex(self._page_index_map["account"])
                self._current_page = "account"
                self._update_ui_for_page("account")
            elif self._page_index_map:
                # إذا لم تكن صفحة الحساب موجودة، انتقل إلى أول صفحة متوفرة
                first_page = list(self._page_index_map.keys())[0]
                print(f"   → Switching to first available page: {first_page}")
                self.module_stack.setCurrentIndex(self._page_index_map[first_page])
                self._current_page = first_page
                self._update_ui_for_page(first_page)
            return
        
        try:
            print(f"✅ Switching to page: {page_id}")
            self.module_stack.setCurrentIndex(self._page_index_map[page_id])
            self._current_page = page_id
            self._update_ui_for_page(page_id)
        except RuntimeError as e:
            print(f"⚠️ Error switching to page {page_id}: {e}")

    def _update_ui_for_page(self, page_id: str):
        """Update UI elements based on the current page."""
        if self._is_shutting_down:
            return
        try:
            # ===== تحديث المؤشرات العلوية (company/personal) =====
            if hasattr(self, 'company_indicator') and hasattr(self, 'company_label'):
                if page_id == "classroom":
                    self.company_indicator.show()
                    self.company_label.setStyleSheet("color: white; font-size: 15px; font-weight: 500; background: transparent;")
                    if hasattr(self, 'personal_indicator'):
                        self.personal_indicator.hide()
                    if hasattr(self, 'personal_label'):
                        self.personal_label.setStyleSheet("color: rgba(255, 255, 255, 0.35); font-size: 15px; font-weight: 500; background: transparent;")
                else:
                    # لأي صفحة أخرى (account, quiz, poll)
                    self.company_indicator.hide()
                    self.company_label.setStyleSheet("color: rgba(255, 255, 255, 0.35); font-size: 15px; font-weight: 500; background: transparent;")
                    if hasattr(self, 'personal_indicator'):
                        self.personal_indicator.hide()
                    if hasattr(self, 'personal_label'):
                        self.personal_label.setStyleSheet("color: rgba(255, 255, 255, 0.35); font-size: 15px; font-weight: 500; background: transparent;")

            # ===== تحديث أزرار الـ Dock (5 buttons) =====
            dock_mapping = {
                "classroom": 0,
                "quiz": 1,
                "poll": 2,
                "account": 4
            }
            # Note: Chat (index 3) is a toggle panel, not a page
            
            # التحقق من وجود dock_buttons
            if hasattr(self, 'dock_buttons') and self.dock_buttons:
                if page_id in dock_mapping:
                    target_idx = dock_mapping[page_id]
                    for idx, btn in enumerate(self.dock_buttons):
                        if hasattr(btn, 'set_active'):
                            btn.set_active(idx == target_idx)
                    self.current_dock_index = target_idx
                else:
                    for btn in self.dock_buttons:
                        if hasattr(btn, 'set_active'):
                            btn.set_active(False)
        except RuntimeError as e:
            print(f"⚠️ Error updating UI for page {page_id}: {e}")
        except AttributeError as e:
            print(f"⚠️ Attribute error in _update_ui_for_page: {e}")

    def _connect_teacher_actions(self):
        # ربط أزرار الـ Dock
        dock_mapping = ["classroom", "quiz", "poll", None, "account"]
        
        if hasattr(self, 'dock_buttons'):
            for idx, btn in enumerate(self.dock_buttons):
                if idx < len(dock_mapping) and dock_mapping[idx] is not None:
                    page_id = dock_mapping[idx]
                    try:
                        try:
                            btn.clicked.disconnect()
                        except (RuntimeError, TypeError):
                            pass
                        btn.clicked.connect(lambda checked=False, pid=page_id: self._switch_to_page(pid))
                        print(f"✅ Connected dock button {idx} to page: {page_id}")
                    except Exception as e:
                        print(f"⚠️ Error connecting dock button {idx}: {e}")
        
        # ربط أزرار العلامات العلوية
        if hasattr(self, 'company_label'):
            try:
                self.company_label.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.company_label.clicked.connect(lambda: self._switch_to_page("classroom"))
        
        if hasattr(self, 'personal_label'):
            try:
                self.personal_label.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.personal_label.clicked.connect(lambda: self._switch_to_page("chat"))

        # ===== CONNECT CHAT BUTTON - uses ChatPanel from ui.py =====
        print("\n" + "=" * 60)
        print("🔍 CONNECTING CHAT BUTTON")
        print("=" * 60)

        # Find the chat button - it's now in the UI
        chat_btn = None
        for btn in self.findChildren(IconButton):
            if btn.text() == "💬" or (hasattr(btn, 'objectName') and btn.objectName() == "chat_btn"):
                chat_btn = btn
                break
        
        # Also check for ChatButton type
        if not chat_btn:
            for btn in self.findChildren(QPushButton):
                if btn.text() == "💬":
                    chat_btn = btn
                    break

        if chat_btn:
            print(f"✅ Found chat button!")
            try:
                chat_btn.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            chat_btn.clicked.connect(self._toggle_chat_panel)
            print("✅ Chat button connected to _toggle_chat_panel")
        else:
            print("⚠️ Chat button not found - will use the one from ui.py")

        # ===== CONNECT NOTIFICATION BUTTON =====
        print("\n" + "=" * 60)
        print("🔍 CONNECTING NOTIFICATION BUTTON")
        print("=" * 60)
        
        bell_btn = None
        top_widget = None
        for child in self.findChildren(QWidget):
            if hasattr(child, 'layout') and child.layout() and child.height() == 72:
                top_widget = child
                break
        
        if top_widget:
            top_icon_buttons = top_widget.findChildren(IconButton)
            print(f"Found {len(top_icon_buttons)} IconButton(s) in top bar")
            for i, btn in enumerate(top_icon_buttons):
                if i == 0:
                    bell_btn = btn

        if bell_btn:
            try:
                bell_btn.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            bell_btn.clicked.connect(self._toggle_notification_panel)
            print("✅ Connected bell button to notification panel")
        else:
            print("❌ Bell button not found")
        
        print("=" * 60 + "\n")

    def _find_settings_button(self):
        for child in self.findChildren(SettingsButton):
            return child
        return None

    def _toggle_chat_panel(self):
        """Toggle the chat panel using ChatPanel from ui.py."""
        if self._is_shutting_down:
            return

        # Get the chat panel from the UI
        if not hasattr(self, 'chat_panel'):
            # The panel is created in ui.py, but we need to access it
            # Find it in the children
            for child in self.findChildren(QWidget):
                if child.__class__.__name__ == 'ChatPanel':
                    self.chat_panel = child
                    break
        
        if hasattr(self, 'chat_panel') and self.chat_panel:
            # Check if we need to set the chat widget
            if self._chat_widget is not None:
                # The ChatPanel has a set_chat_widget method
                if hasattr(self.chat_panel, 'set_chat_widget'):
                    # Only set if not already set
                    if not hasattr(self.chat_panel, '_chat_set') or not self.chat_panel._chat_set:
                        self.chat_panel.set_chat_widget(self._chat_widget)
                        self.chat_panel._chat_set = True
                        print("✅ Chat widget set in ChatPanel")
                
                # Make sure the chat widget is visible when panel opens
                self._chat_widget.setVisible(True)
            
            # Toggle the panel
            self.chat_panel.toggle_panel()
        else:
            # Fallback: create a chat panel if not found
            print("⚠️ ChatPanel not found, creating one...")
            self.chat_panel = ChatPanel(self)
            if self._chat_widget is not None:
                self.chat_panel.set_chat_widget(self._chat_widget)
                self.chat_panel._chat_set = True
            self.chat_panel.toggle_panel()

    def _toggle_stream_panel(self):
        print("\n🔴 _toggle_stream_panel called!")
        if self._is_shutting_down:
            return
        
        if not self.config.get('VIDEO_STREAM_AVAILABLE', False):
            print("❌ VIDEO_STREAM_AVAILABLE is False")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Stream Not Available")
            msg.setText("Video stream module is not available.\nMake sure stream1/streamer.py exists.")
            msg.exec()
            return
        
        if "stream_panel" not in self._floating_widgets:
            print("📺 Creating new StreamFloatingWidget...")
            self._floating_widgets["stream_panel"] = StreamFloatingWidget(self.config, self)
        
        panel = self._floating_widgets["stream_panel"]
        if panel and panel.isVisible():
            panel.hide_animated()
        elif panel:
            # Find the chat button position
            chat_btn = None
            for btn in self.findChildren(QPushButton):
                if btn.text() == "💬":
                    chat_btn = btn
                    break
            if chat_btn:
                pos = chat_btn.mapToGlobal(QPoint(0, chat_btn.height()))
                panel.show_at_position(pos)
            else:
                screen = QApplication.primaryScreen().geometry()
                panel.show_at_position(QPoint(screen.width() - 450, 80))

    def _toggle_notification_panel(self):
        if self._is_shutting_down:
            return
        if "notif_panel" not in self._floating_widgets:
            self._floating_widgets["notif_panel"] = NotificationFloatingWidget(self.config, self)
        panel = self._floating_widgets["notif_panel"]
        if panel and panel.isVisible():
            panel.hide_animated()
        elif panel:
            bell_btn = None
            for btn in self.findChildren(IconButton):
                if btn.parent() and btn.parent().layout() and btn.geometry().x() > 50 and btn.geometry().y() < 50:
                    bell_btn = btn
                    break
            if bell_btn:
                panel.show_at_position(bell_btn.mapToGlobal(QPoint(0, bell_btn.height())))
            else:
                panel.show()

    def _setup_cleanup(self):
        CleanupManager.register_cleanup_handler(self._shutdown_modules, "IntegratedDashboard modules")
        # Cleanup pre-loaded chat widget
        CleanupManager.register_cleanup_handler(
            lambda: self._chat_widget.close() if hasattr(self, '_chat_widget') and self._chat_widget else None,
            "PreloadedChatWidget"
        )
        self.destroyed.connect(self._emergency_cleanup)

    def _shutdown_modules(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        print("Shutting down all teacher modules...")
        for page_id, widget in self._module_pages.items():
            if widget and hasattr(widget, 'shutdown'):
                try:
                    widget.shutdown()
                except Exception as e:
                    print(f"Error shutting down {page_id}: {e}")
        
        # Clean up pre-loaded chat widget
        if self._chat_widget:
            try:
                if hasattr(self._chat_widget, 'close'):
                    self._chat_widget.close()
                self._chat_widget.deleteLater()
                self._chat_widget = None
                print("✅ Pre-loaded chat widget cleaned up")
            except Exception as e:
                print(f"Error cleaning up chat widget: {e}")
        
        for panel in self._floating_widgets.values():
            if panel and hasattr(panel, 'shutdown'):
                panel.shutdown()
            elif panel and hasattr(panel, 'cleanup'):
                panel.cleanup()
        TimerCleanup.cleanup_all_timers(self)
        AnimationCleanup.cleanup_animations(self)

    def _emergency_cleanup(self):
        self._shutdown_modules()

    def closeEvent(self, event):
        self._shutdown_modules()
        force_close_all_websockets()
        event.accept()


# ============================================================
# Modern Authentication Window
# ============================================================
class ModernAuthWindow(QMainWindow):
    login_completed = Signal(dict, dict)
    login_cancelled = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._auth_successful = False
        self._updating_window = False
        self.is_maximized = False
        self.normal_geometry = None
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("Latigo Teacher - Authentication")
        self.setFixedSize(500, 600)
        self.center_on_screen()

        central = QWidget()
        central.setObjectName("centralWidget")
        central.setStyleSheet("QWidget#centralWidget { background-color: transparent; }")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = self.create_title_bar()
        layout.addWidget(self.title_bar)
        self.title_bar.hide()
        
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        self.create_login_page()
        self.create_register_page()
        
        self.stacked.currentChanged.connect(self.on_page_changed)
        self.stacked.setCurrentWidget(self.login_window)

        self.apply_shadow()

    def create_title_bar(self):
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("QWidget#titleBar { background-color: #f5f5f7; border-top-left-radius: 12px; border-top-right-radius: 12px; border-bottom: 1px solid #e0e0e0; }")
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        title_label = QLabel("Create New Account")
        title_label.setStyleSheet("QLabel { color: #1d1d1f; font-size: 14px; font-weight: 600; }")
        layout.addWidget(title_label)
        layout.addStretch()
        
        self.minimize_btn = QPushButton("—")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setCursor(Qt.PointingHandCursor)
        self.minimize_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; border-radius: 4px; color: #666; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #e0e0e0; }")
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setCursor(Qt.PointingHandCursor)
        self.maximize_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; border-radius: 4px; color: #666; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #e0e0e0; }")
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; border-radius: 4px; color: #666; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #ff3b30; color: white; }")
        self.close_btn.clicked.connect(self.close)
        
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        title_bar.mouseReleaseEvent = self.title_bar_mouse_release
        return title_bar

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def title_bar_mouse_release(self, event):
        if hasattr(self, 'drag_position'):
            delattr(self, 'drag_position')

    def toggle_maximize(self):
        if self._updating_window:
            return
        self._updating_window = True
        if self.is_maximized:
            self.showNormal()
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.maximize_btn.setText("□")
            self.is_maximized = False
        else:
            self.normal_geometry = self.geometry()
            self.showMaximized()
            self.maximize_btn.setText("❐")
            self.is_maximized = True
        self._updating_window = False

    def on_page_changed(self, index):
        if self._updating_window:
            return
        self._updating_window = True
        current = self.stacked.currentWidget()
        if current == self.login_window:
            if self.is_maximized:
                self.showNormal()
                self.is_maximized = False
            self.title_bar.hide()
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setMinimumSize(500, 600)
            self.setMaximumSize(500, 600)
            self.resize(500, 600)
            self.apply_shadow()
        elif current == self.register_window:
            self.title_bar.show()
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setMinimumSize(800, 600)
            self.setMaximumSize(16777215, 16777215)
            self.resize(1000, 750)
            self.centralWidget().setGraphicsEffect(None)
        self.center_on_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        self._updating_window = False

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def apply_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.centralWidget().setGraphicsEffect(shadow)

    def create_login_page(self):
        LoginWindowClass = self.config.get('LoginWindow')
        if LoginWindowClass:
            self.login_window = LoginWindowClass(self)
            self.stacked.addWidget(self.login_window)
        else:
            self.login_window = self._fallback_page("Login not available")
            self.stacked.addWidget(self.login_window)

    def create_register_page(self):
        RegisterWindowClass = self.config.get('MultiStepFormWindow')
        if RegisterWindowClass:
            self.register_window = RegisterWindowClass(self)
            self.stacked.addWidget(self.register_window)
        else:
            self.register_window = self._fallback_page("Registration not available")
            self.stacked.addWidget(self.register_window)

    def _fallback_page(self, msg):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel(msg)
        label.setStyleSheet("color: #ff3b30; font-size: 16px;")
        layout.addWidget(label)
        return page

    def show_registration(self):
        self.stacked.setCurrentWidget(self.register_window)

    def on_login_success(self, user_data, tokens):
        self._auth_successful = True
        self.login_completed.emit(user_data, tokens)
        self.close()

    def on_registration_success(self, user_data, tokens):
        self._auth_successful = True
        self.login_completed.emit(user_data, tokens)
        self.close()

    def closeEvent(self, event):
        if not self._auth_successful:
            self.login_cancelled.emit()
        event.accept()


# ============================================================
# Main execution
# ============================================================

# ============================================================
# Main execution




# ============================================================
# Main execution - OPTIMIZED VERSION
# ============================================================

# ============================================================
# Main execution - WITH PROPER RESTART ON LOGIN/REGISTRATION
# ============================================================
def main():
    # Close tkinter splash BEFORE creating PySide6 QApplication
    # (PySide6 must be created AFTER tkinter is fully destroyed to avoid conflicts)
    _close_splash()

    # Small delay to ensure tkinter is fully cleaned up
    import time
    time.sleep(0.1)

    # Create PySide6 QApplication (AFTER MediaPipe is loaded and tkinter is closed)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont()
    font.setFamily("SF Pro Text, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial")
    font.setPointSize(11)
    app.setFont(font)
    QToolTip.setFont(font)

    MessageBoxInterceptor.install()

    # ── Main splash is created now (PySide6 version) ──
    splash = SplashWindow()
    splash.show()
    splash.set_progress(0)
    splash.set_loading_text("Initializing...")
    app.processEvents()

    # ============================================================
    # STEP 1: Check token FIRST - before loading heavy modules
    # ============================================================
    
    splash.set_progress(5)
    splash.set_loading_text("Checking authentication...")
    app.processEvents()
    
    # Get token from token_manager or file
    token = None
    user_data = None
    token_valid = False
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ACCOUNT_DIR = os.path.join(BASE_DIR, "account")
    
    # Try to get token from token_manager first
    TOKEN_MANAGER_AVAILABLE = False
    token_manager = None
    get_current_room = None
    get_available_rooms = None
    set_token = None
    clear_token = None
    get_auth_headers = None
    sync_token_with_server = None
    sync_if_needed = None
    sync_rooms_from_server_func = None
    
    try:
        from token_manager import (
            token_manager, 
            get_current_room, 
            get_available_rooms, 
            set_token, 
            clear_token, 
            get_auth_headers, 
            sync_token_with_server, 
            sync_if_needed,
            sync_rooms_from_server
        )
        TOKEN_MANAGER_AVAILABLE = True
        sync_rooms_from_server_func = sync_rooms_from_server
        print("✅ TokenManager imported")
        
        # Check if token exists
        token = token_manager.get_token()
        if token:
            print(f"📄 Token found in token_manager: {token[:20]}...")
    except ImportError:
        TOKEN_MANAGER_AVAILABLE = False
        print("⚠️ TokenManager not available")
        token_manager = None
        get_current_room = lambda: None
        get_available_rooms = lambda: []
        set_token = lambda *a, **kw: None
        clear_token = lambda: None
        get_auth_headers = lambda: {}
        sync_token_with_server = lambda *a, **kw: False
        sync_if_needed = lambda *a, **kw: False
        sync_rooms_from_server_func = lambda *a, **kw: False
    
    # If no token in token_manager, try account/token.txt
    if not token:
        token_txt_path = os.path.join(ACCOUNT_DIR, "token.txt")
        if os.path.exists(token_txt_path):
            try:
                with open(token_txt_path, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                if token:
                    print(f"📄 Token found in token.txt: {token[:20]}...")
            except Exception as e:
                print(f"Failed to read token.txt: {e}")
    
    splash.set_progress(10)
    splash.set_loading_text("Validating token with server...")
    app.processEvents()
    
    # Validate token with server
    if token:
        try:
            import requests
            import config
            
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{config.API_BASE_URL}/api/token/validate", 
                               headers=headers, timeout=5, verify=False)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    token_valid = True
                    user_data = data.get("data", {})
                    print("✅ Token validated with server")
                    
                    # Update token_manager with user data
                    if TOKEN_MANAGER_AVAILABLE and token_manager and set_token:
                        username = user_data.get("username") or user_data.get("display_name") or user_data.get("email", "").split('@')[0]
                        set_token(token=token, user_data=user_data, username=username)
                        print(f"✅ Token set for user: {username}")
                        
                        # Try to sync rooms from server
                        if sync_rooms_from_server_func:
                            print("📡 Syncing rooms from server...")
                            sync_rooms_from_server_func(config.API_BASE_URL)
                else:
                    print("❌ Token invalid according to server")
                    # Clear invalid token
                    if TOKEN_MANAGER_AVAILABLE and token_manager and clear_token:
                        clear_token()
                    token = None
            else:
                print(f"❌ Token validation failed with status: {resp.status_code}")
                if TOKEN_MANAGER_AVAILABLE and token_manager and clear_token:
                    clear_token()
                token = None
        except Exception as e:
            print(f"⚠️ Token validation error: {e}")
    
    if not token_valid:
        print("🔐 No valid token found. Will show authentication window.")
    
    # ============================================================
    # STEP 2: Build config with minimal info
    # ============================================================
    
    splash.set_progress(15)
    splash.set_loading_text("Preparing modules...")
    app.processEvents()
    
    result = {
        'BASE_DIR': BASE_DIR,
        'ACCOUNT_DIR': ACCOUNT_DIR,
        'TOKEN_MANAGER_AVAILABLE': TOKEN_MANAGER_AVAILABLE,
        'token_manager': token_manager,
        'get_current_room': get_current_room,
        'get_available_rooms': get_available_rooms,
        'set_token': set_token,
        'clear_token': clear_token,
        'get_auth_headers': get_auth_headers,
        'sync_token_with_server': sync_token_with_server,
        'sync_if_needed': sync_if_needed,
        'token': token,
        'user_data': user_data,
        'token_valid': token_valid,
    }
    
    # ============================================================
    # STEP 3: Load ONLY ACCOUNT module for authentication
    # ============================================================
    
    splash.set_progress(20)
    splash.set_loading_text("Loading account module...")
    app.processEvents()
    
    ACCOUNT_AVAILABLE = False
    AccountTokenManager = None
    ApiWorker = None
    LoginWindow = None
    MultiStepFormWindow = None
    ModernAccountPage = None
    account_config = None
    sound_manager = None
    
    try:
        from account.client2 import TokenManager as AccountTokenManager
        from account.ApiWorker import ApiWorker
        from account.LoginWindow import LoginWindow
        from account.MultiStepFormWindow import MultiStepFormWindow
        from account.ModernAccountPage import ModernAccountPage
        from account.account_config import account_config
        from account.SoundManager import sound_manager
        ACCOUNT_AVAILABLE = True
        print("✅ Account modules imported")
    except ImportError as e:
        print(f"⚠️ Account import failed: {e}")
    
    result['ACCOUNT_AVAILABLE'] = ACCOUNT_AVAILABLE
    result['AccountTokenManager'] = AccountTokenManager
    result['ApiWorker'] = ApiWorker
    result['LoginWindow'] = LoginWindow
    result['MultiStepFormWindow'] = MultiStepFormWindow
    result['ModernAccountPage'] = ModernAccountPage
    result['account_config'] = account_config
    result['sound_manager'] = sound_manager
    
    # ============================================================
    # STEP 4: If token is valid, load other modules
    # ============================================================
    
    if token_valid:
        splash.set_progress(25)
        splash.set_loading_text("Loading teacher modules...")
        app.processEvents()
        
        # Load TeacherSelector
        TEACHER_SELECTOR_AVAILABLE = False
        TeacherSelectorDialog = None
        try:
            from teacherselector import TeacherSelectorDialog
            TEACHER_SELECTOR_AVAILABLE = True
            print("✅ TeacherSelectorDialog loaded")
        except ImportError as e:
            print(f"⚠️ TeacherSelectorDialog import failed: {e}")
            # Try to load from path
            try:
                teacher_path = os.path.join(BASE_DIR, "teacherselector.py")
                if os.path.exists(teacher_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("teacherselector", teacher_path)
                    teacher_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(teacher_module)
                    if hasattr(teacher_module, 'TeacherSelectorDialog'):
                        TeacherSelectorDialog = teacher_module.TeacherSelectorDialog
                        TEACHER_SELECTOR_AVAILABLE = True
                        print("✅ TeacherSelectorDialog loaded from path")
            except Exception as e2:
                print(f"⚠️ Failed to load teacherselector from path: {e2}")
        
        result['TEACHER_SELECTOR_AVAILABLE'] = TEACHER_SELECTOR_AVAILABLE
        result['TeacherSelectorDialog'] = TeacherSelectorDialog
        
        # Load Quiz
        splash.set_progress(30)
        splash.set_loading_text("Loading quiz module...")
        app.processEvents()
        
        QUIZ_AVAILABLE = False
        QuizApp = None
        try:
            from quiz import QuizApp
            QUIZ_AVAILABLE = True
            print("✅ Quiz module loaded")
        except ImportError:
            try:
                quiz_dir = os.path.join(BASE_DIR, "quiz")
                quiz_path = os.path.join(quiz_dir, "quiz.py")
                if os.path.exists(quiz_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("quiz_module", quiz_path)
                    quiz_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(quiz_module)
                    if hasattr(quiz_module, 'QuizApp'):
                        QuizApp = quiz_module.QuizApp
                        QUIZ_AVAILABLE = True
                        print("✅ Quiz loaded from file")
            except Exception as e:
                print(f"⚠️ Quiz not available: {e}")
        result['QUIZ_AVAILABLE'] = QUIZ_AVAILABLE
        result['QuizApp'] = QuizApp
        
        # Load Poll
        splash.set_progress(35)
        splash.set_loading_text("Loading poll module...")
        app.processEvents()
        
        POLL_AVAILABLE = False
        PollApp = None
        try:
            poll_dir = os.path.join(BASE_DIR, "poll")
            poll_path = os.path.join(poll_dir, "poll.py")
            if os.path.exists(poll_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("poll_module", poll_path)
                poll_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(poll_module)
                
                if hasattr(poll_module, 'StudentWindow'):
                    PollApp = poll_module.StudentWindow
                    POLL_AVAILABLE = True
                    print("✅ Poll module (StudentWindow) loaded")
                elif hasattr(poll_module, 'PollWindow'):
                    PollApp = poll_module.PollWindow
                    POLL_AVAILABLE = True
                    print("✅ Poll module (PollWindow) loaded")
                elif hasattr(poll_module, 'MainWindow'):
                    PollApp = poll_module.MainWindow
                    POLL_AVAILABLE = True
                    print("✅ Poll module (MainWindow) loaded")
                else:
                    for attr_name in dir(poll_module):
                        attr = getattr(poll_module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, QWidget) and attr_name != 'QWidget':
                            PollApp = attr
                            POLL_AVAILABLE = True
                            print(f"✅ Poll module ({attr_name}) loaded")
                            break
        except Exception as e:
            print(f"⚠️ Poll import failed: {e}")
        result['POLL_AVAILABLE'] = POLL_AVAILABLE
        result['PollApp'] = PollApp
        
        # Load Classroom
        splash.set_progress(40)
        splash.set_loading_text("Loading classroom module...")
        app.processEvents()
        
        CLASSROOM_AVAILABLE = False
        ClassroomWidget = None
        try:
            classroom_path = os.path.join(BASE_DIR, "classroom", "classroom.py")
            if os.path.exists(classroom_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("classroom_module", classroom_path)
                classroom_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(classroom_module)
                if hasattr(classroom_module, 'StreamViewer'):
                    ClassroomWidget = classroom_module.StreamViewer
                    CLASSROOM_AVAILABLE = True
                    print("✅ Classroom module loaded")
        except Exception as e:
            print(f"⚠️ Classroom import failed: {e}")
        result['CLASSROOM_AVAILABLE'] = CLASSROOM_AVAILABLE
        result['ClassroomWidget'] = ClassroomWidget
        
        # Load Chat
        splash.set_progress(45)
        splash.set_loading_text("Loading chat module...")
        app.processEvents()
        
        CHAT_AVAILABLE = False
        ChatWidget = None
        try:
            # Import the StudentChatClient from this file
            if 'StudentChatClient' in globals():
                class EmbeddedChatWrapper(StudentChatClient):
                    def __init__(self, parent=None):
                        super().__init__(embedded=True)
                        self.setParent(parent)
                        self.setWindowFlags(Qt.Widget)
                ChatWidget = EmbeddedChatWrapper
                CHAT_AVAILABLE = True
                print("✅ Chat module loaded (embedded mode)")
            else:
                # Try to load from chat.py
                chat_path = os.path.join(BASE_DIR, "chat", "chat.py")
                if os.path.exists(chat_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("chat_module", chat_path)
                    chat_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(chat_module)
                    if hasattr(chat_module, 'StudentChatClient'):
                        ChatWidget = chat_module.StudentChatClient
                        CHAT_AVAILABLE = True
                        print("✅ Chat module loaded from file")
        except Exception as e:
            print(f"⚠️ Chat import failed: {e}")
        result['CHAT_AVAILABLE'] = CHAT_AVAILABLE
        result['ChatWidget'] = ChatWidget
        
        # Load Video Stream
        splash.set_progress(50)
        splash.set_loading_text("Loading video stream module...")
        app.processEvents()
        
        VIDEO_STREAM_AVAILABLE = False
        VideoWindow = None
        try:
            streamer_path = os.path.join(BASE_DIR, "stream1", "streamer.py")
            if os.path.exists(streamer_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("streamer", streamer_path)
                streamer_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(streamer_module)
                if hasattr(streamer_module, 'VideoWindow'):
                    VideoWindow = streamer_module.VideoWindow
                    VIDEO_STREAM_AVAILABLE = True
                    print("✅ Video stream module loaded")
        except Exception as e:
            print(f"⚠️ Stream module error: {e}")
        result['VIDEO_STREAM_AVAILABLE'] = VIDEO_STREAM_AVAILABLE
        result['VideoWindow'] = VideoWindow
        
        # Skip disabled modules
        result['AI_DASHBOARD_AVAILABLE'] = False
        result['AiDashboard'] = None
        result['WHITEBOARD_AVAILABLE'] = False
        result['WhiteboardApp'] = None
        result['FEEDBACK_AVAILABLE'] = False
        result['FeedbackForm'] = None
        result['RecentFeedbackPanel'] = None
        result['OrbBackground'] = None
        
        print("\n" + "=" * 50)
        print("MODULE AVAILABILITY SUMMARY:")
        print(f"  ACCOUNT_AVAILABLE: {result.get('ACCOUNT_AVAILABLE', False)}")
        print(f"  QUIZ_AVAILABLE: {result.get('QUIZ_AVAILABLE', False)}")
        print(f"  POLL_AVAILABLE: {result.get('POLL_AVAILABLE', False)}")
        print(f"  VIDEO_STREAM_AVAILABLE: {result.get('VIDEO_STREAM_AVAILABLE', False)}")
        print(f"  CLASSROOM_AVAILABLE: {result.get('CLASSROOM_AVAILABLE', False)}")
        print(f"  CHAT_AVAILABLE: {result.get('CHAT_AVAILABLE', False)}")
        print(f"  TEACHER_SELECTOR_AVAILABLE: {result.get('TEACHER_SELECTOR_AVAILABLE', False)}")
        print("=" * 50 + "\n")
    
    splash.set_progress(100)
    splash.set_loading_text("Loading complete!")
    app.processEvents()
    
    # ============================================================
    # STEP 5: Show the appropriate UI
    # ============================================================
    
    # Helper to close splash
    splash_closed = False
    
    def close_splash_once():
        nonlocal splash_closed
        if not splash_closed:
            splash_closed = True
            splash.cleanup()
            splash.close()
            app.processEvents()
    
    # ===== MAIN APPLICATION LOOP =====
    app_running = True
    
    while app_running:
        if token_valid:
            print("\n🔍 Valid token found. Checking room selection status...")
            
            close_splash_once()
            
            # Make sure TeacherSelectorDialog is available in result
            if not result.get('TeacherSelectorDialog'):
                print("⚠️ TeacherSelectorDialog not in result, trying to import...")
                try:
                    from teacherselector import TeacherSelectorDialog
                    result['TeacherSelectorDialog'] = TeacherSelectorDialog
                    result['TEACHER_SELECTOR_AVAILABLE'] = True
                    print("✅ TeacherSelectorDialog imported successfully")
                except ImportError as e:
                    print(f"❌ Failed to import TeacherSelectorDialog: {e}")
                    QMessageBox.critical(
                        None, 
                        "Error Loading Teacher Selection",
                        f"Failed to load TeacherSelectorDialog:\n\n{str(e)}\n\n"
                        "Please make sure teacherselector.py exists."
                    )
                    close_application_securely("TeacherSelectorDialog not available")
                    return
            
            room_selected = ensure_room_selected(result, max_attempts=3)
            
            if not room_selected:
                print("❌ Room selection failed or was cancelled.")
                # Show a proper dialog instead of just exiting
                reply = QMessageBox.question(
                    None, 
                    "Room Selection Required",
                    "You need to select a teacher to continue using the app.\n\n"
                    "Do you want to try selecting a teacher again?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    # Reset token_valid to force re-evaluation
                    # Actually, we need to loop again with same token_valid
                    continue
                else:
                    print("👋 User chose to exit without selecting a room.")
                    close_application_securely("Room selection cancelled by user")
                    return
            
            print("✅ Room selection successful! Opening dashboard...")
            
            main_window = IntegratedDashboard(result)
            
            loop = QEventLoop()
            logout_triggered = False
            
            def on_logout():
                nonlocal logout_triggered
                print("🔴 Main loop: Logout triggered, closing window...")
                logout_triggered = True
                result['token_valid'] = False
                main_window._is_shutting_down = True
                main_window.close()
                loop.quit()
            
            main_window.logoutRequested.connect(on_logout)
            
            def on_dashboard_closed():
                if not logout_triggered and main_window._is_shutting_down:
                    print("⚠️ Dashboard closed unexpectedly")
                    loop.quit()
            
            main_window.destroyed.connect(on_dashboard_closed)
            
            main_window.showMaximized()
            loop.exec()
            
            if not result.get('token_valid') or logout_triggered:
                print("🔄 Token invalid after logout, restarting authentication flow...")
                token_valid = False
                continue
            else:
                print("👋 Dashboard closed normally, exiting...")
                break
        else:
            # ===== AUTHENTICATION FLOW =====
            print("\n🔐 Showing authentication window...")
            
            # Make sure splash is closed before showing modal windows
            close_splash_once()
            
            auth_window = ModernAuthWindow(result)
            auth_loop = QEventLoop()
            login_success = False
            user_data = None
            tokens = None
            
            def on_success(ud, tk):
                nonlocal login_success, user_data, tokens
                print(f"✅ Authentication successful!")
                login_success = True
                user_data = ud
                tokens = tk
                auth_loop.quit()
            
            def on_cancelled():
                auth_loop.quit()
                close_application_securely("Login cancelled")
            
            auth_window.login_completed.connect(on_success)
            auth_window.login_cancelled.connect(on_cancelled)
            auth_window.show()
            auth_loop.exec()
            
            if login_success:
                print("✅ Login/Registration successful!")
                token_valid = True
                result['token_valid'] = True
                result['user_data'] = user_data
                
                token = tokens.get('access_token') or tokens.get('token')
                if not token:
                    print("❌ ERROR: No token received from authentication!")
                    QMessageBox.critical(
                        None, 
                        "Authentication Failed", 
                        "No token received from server. Please try again."
                    )
                    continue
                
                result['token'] = token
                
                # Save token
                if result.get('account_config'):
                    result['account_config'].CURRENT_TOKEN = token
                    result['account_config'].CURRENT_USER_ID = user_data.get('id')
                    result['account_config'].CURRENT_USER_DATA = user_data
                
                if result.get('TOKEN_MANAGER_AVAILABLE') and result.get('set_token'):
                    try:
                        username = user_data.get("username") or user_data.get("display_name") or user_data.get("email", "").split('@')[0]
                        result['set_token'](token=token, user_data=user_data, username=username)
                        print(f"✅ Token saved to token_manager")
                        
                        # Try to sync rooms
                        if sync_rooms_from_server_func:
                            import config
                            print("📡 Syncing rooms from server...")
                            sync_rooms_from_server_func(config.API_BASE_URL)
                    except Exception as e:
                        print(f"Error saving token to token_manager: {e}")
                
                if result.get('ACCOUNT_DIR'):
                    token_path = os.path.join(result['ACCOUNT_DIR'], "token.txt")
                    try:
                        with open(token_path, 'w', encoding='utf-8') as f:
                            f.write(token)
                        print(f"✅ Token saved to {token_path}")
                    except Exception as e:
                        print(f"Error writing token.txt: {e}")
                
                # ===== RESTART APPLICATION TO LOAD MODULES WITH NEW TOKEN =====
                print("\n" + "=" * 60)
                print("🔄 RESTARTING APPLICATION AFTER LOGIN/REGISTRATION")
                print("=" * 60)
                print("This ensures all modules are loaded with the new authentication context.")
                print("=" * 60 + "\n")
                
                # Close the auth window
                auth_window.close()
                
                # Show a restart message
                restart_msg = QMessageBox()
                restart_msg.setIcon(QMessageBox.Information)
                restart_msg.setWindowTitle("Login Successful")
                restart_msg.setText("✓ Login successful!\n\nThe application will now restart to load all modules with your new session.")
                restart_msg.setInformativeText("Please wait while the application restarts...")
                restart_msg.setStandardButtons(QMessageBox.Ok)
                restart_msg.setDefaultButton(QMessageBox.Ok)
                
                # Style the message box
                restart_msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #ffffff;
                        border-radius: 12px;
                    }
                    QLabel {
                        color: #1d1d1f;
                        font-size: 13px;
                        padding: 8px;
                    }
                    QPushButton {
                        background-color: #0078d4;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 20px;
                        font-size: 13px;
                        font-weight: 500;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #005a9e;
                    }
                """)
                
                restart_msg.exec()
                
                # Clean up the main application state
                CleanupManager.run_all_cleanups()
                ModuleCleanupManager.cleanup_all()
                gc.collect()
                
                # Restart the application
                program = sys.executable
                args = sys.argv[:]
                
                # Close all windows
                app.closeAllWindows()
                
                # Start the new process
                print(f"🚀 Starting new process: {program} {' '.join(args)}")
                QProcess.startDetached(program, args)
                
                # Exit the current process
                print("👋 Exiting current process...")
                sys.exit(0)
                
            else:
                print("❌ Login/Registration failed or cancelled.")
                break
    
    close_application_securely("Application closed")
if __name__ == "__main__":
    main()
