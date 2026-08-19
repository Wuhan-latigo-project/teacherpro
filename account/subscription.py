import sys
import os
import re
import base64
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtSvg import QSvgRenderer

class OceanGradientLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.offset = 0.0
        # Use Apple system fonts if available, with fallbacks
        font = QFont()
        font.setFamilies([
            "SF Pro Display", "Helvetica Neue", "Helvetica", 
            "Arial", "sans-serif"
        ])
        font.setPointSize(34)
        font.setWeight(QFont.Bold)
        self.setFont(font)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(60)
        self.setStyleSheet("background: transparent;")
        
        # Create timer for slow animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(60)
        
    def animate(self):
        self.offset += 0.005
        if self.offset > 1.0:
            self.offset = 0.0
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Create gradient
        rect = self.rect()
        gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        
        # Blue ocean colors
        gradient.setColorAt((0.0 + self.offset) % 1.0, QColor('#003366'))    # Dark blue
        gradient.setColorAt((0.3 + self.offset) % 1.0, QColor('#0066cc'))    # Medium blue
        gradient.setColorAt((0.6 + self.offset) % 1.0, QColor('#0099ff'))    # Bright blue
        gradient.setColorAt((0.9 + self.offset) % 1.0, QColor('#00ccff'))    # Light blue
        gradient.setColorAt((1.0 + self.offset) % 1.0, QColor('#003366'))    # Back to dark
        
        # Set the pen to use the gradient
        pen = QPen()
        pen.setBrush(QBrush(gradient))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Draw the text
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())

class SubscriptionPopupSample(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upgrade Subscription")
        self.setFixedSize(650, 550)  # Slightly increased height to accommodate larger QR code
        
        self.dragging = False
        self.drag_position = None
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.current_plan_index = 0
        
        self.plans = [
            ("Basic Plan", "$9.99/month", ["Basic features", "10GB storage", "Email support"], "#4361ee", "#e7f0ff"),
            ("Premium Plan", "$19.99/month", ["All Basic features", "50GB storage", "Priority support"], "#7209b7", "#f0e7ff"),
            ("Enterprise Plan", "$49.99/month", ["All Premium features", "Unlimited storage", "24/7 support"], "#f72585", "#ffe7f0")
        ]
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        container = QWidget()
        container.setObjectName("subscriptionContainer")
        container.setStyleSheet("""
            QWidget#subscriptionContainer {
                background-color: white;
                border-radius: 40px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)
        
        main_horizontal_layout = QHBoxLayout(container)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        main_horizontal_layout.setSpacing(0)
        
        # LEFT SECTION
        left_section = QWidget()
        left_section.setObjectName("leftSection")
        left_section.setStyleSheet("""
            QWidget#leftSection {
                background-color: #f8f9fa;
                border-top-left-radius: 40px;
                border-bottom-left-radius: 40px;
                padding: 20px;
            }
        """)
        left_section.setFixedWidth(200)
        
        left_layout = QVBoxLayout(left_section)
        left_layout.setContentsMargins(20, 30, 20, 30)
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignTop)
        
        # Alipay logo container
        alipay_container = QWidget()
        alipay_container.setObjectName("alipayContainer")
        alipay_container.setStyleSheet("""
            QWidget#alipayContainer {
                background-color: white;
                border-radius: 20px;
                padding: 20px;
                border: 1px solid #e9ecef;
            }
        """)
        
        alipay_layout = QVBoxLayout(alipay_container)
        alipay_layout.setAlignment(Qt.AlignCenter)
        alipay_layout.setSpacing(10)
        
        # Load Alipay PNG with high quality
        alipay_logo = self.create_high_quality_png_label("alipay.png", 140, 100, "Alipay")
        alipay_layout.addWidget(alipay_logo)
        
        left_layout.addWidget(alipay_container)
        
        # Payment features
        features_widget = QWidget()
        features_widget.setStyleSheet("background: transparent;")
        features_layout = QVBoxLayout(features_widget)
        features_layout.setContentsMargins(0, 20, 0, 0)
        features_layout.setSpacing(15)
        
        features = [
            "✓ Secure Encryption",
            "✓ 24/7 Support",
            "✓ Money-back Guarantee",
            "✓ Instant Activation"
        ]
        
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet("""
                QLabel {
                    color: #1d1d1f;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                    background: transparent;
                    padding: 5px;
                }
            """)
            features_layout.addWidget(feature_label)
        
        left_layout.addWidget(features_widget)
        
        # QR Code section - INCREASED SIZE BY 30%
        qr_container = QWidget()
        qr_container.setStyleSheet("background: transparent;")
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setContentsMargins(0, 10, 0, 0)
        qr_layout.setSpacing(15)
        qr_layout.setAlignment(Qt.AlignCenter)
        
        # QR Code label with high quality - INCREASED FROM 100x100 TO 130x130 (+30%)
        qr_label = self.create_high_quality_png_label("qr.png", 169, 169, "QR Code")
        qr_layout.addWidget(qr_label)
        
        qr_text = QLabel("")
        qr_text.setAlignment(Qt.AlignCenter)
        qr_text.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
                margin-top: 5px;
            }
        """)
        qr_layout.addWidget(qr_text)
        
        left_layout.addWidget(qr_container)
        left_layout.addStretch()
        
        # RIGHT SECTION
        right_section = QWidget()
        right_section.setObjectName("rightSection")
        right_section.setStyleSheet("""
            QWidget#rightSection {
                background-color: white;
                border-top-right-radius: 40px;
                border-bottom-right-radius: 40px;
                padding: 20px;
            }
        """)
        
        right_layout = QVBoxLayout(right_section)
        right_layout.setContentsMargins(30, 0, 30, 20)
        right_layout.setSpacing(10)

        drag_area = QWidget()
        drag_area.setFixedHeight(12)
        drag_area.setStyleSheet("background: transparent; border-top-right-radius: 40px;")
        drag_area.setCursor(Qt.OpenHandCursor)
        right_layout.addWidget(drag_area)

        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Animated title with Apple font
        self.title = OceanGradientLabel("Choose Your Plan")
        header_layout.addWidget(self.title)

        subtitle_label = QLabel("Select the perfect plan for your needs")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #6e6e73;
                background: transparent;
                padding: 0px;
                margin: 0px 0px 5px 0px;
                letter-spacing: -0.2px;
            }
        """)
        header_layout.addWidget(subtitle_label)
        
        right_layout.addWidget(header_container)

        # Plan display
        plan_display_container = QWidget()
        plan_display_container.setStyleSheet("background: transparent;")
        plan_display_layout = QVBoxLayout(plan_display_container)
        plan_display_layout.setContentsMargins(0, 0, 0, 0)
        plan_display_layout.setSpacing(15)
        
        self.plan_widget = QWidget()
        self.plan_widget.setFixedHeight(140)
        self.plan_widget.setObjectName("currentPlan")
        
        plan_display_layout.addWidget(self.plan_widget, alignment=Qt.AlignCenter)
        
        # Navigation
        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 5, 0, 5)
        nav_layout.setSpacing(20)
        
        self.prev_btn = QPushButton("←")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                border: 1px solid #d2d2d7;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: #e9e9ed;
                border-color: #0071e3;
            }
            QPushButton:pressed {
                background-color: #d9d9df;
            }
            QPushButton:disabled {
                background-color: #f5f5f7;
                border-color: #e9e9ed;
                color: #c0c0c0;
            }
        """)
        self.prev_btn.clicked.connect(self.show_previous_plan)
        
        self.next_btn = QPushButton("→")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                border: 1px solid #d2d2d7;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: #e9e9ed;
                border-color: #0071e3;
            }
            QPushButton:pressed {
                background-color: #d9d9df;
            }
            QPushButton:disabled {
                background-color: #f5f5f7;
                border-color: #e9e9ed;
                color: #c0c0c0;
            }
        """)
        self.next_btn.clicked.connect(self.show_next_plan)
        
        self.plan_indicator = QLabel("1/3")
        self.plan_indicator.setAlignment(Qt.AlignCenter)
        self.plan_indicator.setStyleSheet("""
            QLabel {
                color: #6e6e73;
                font-size: 14px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
                min-width: 40px;
            }
        """)
        
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.plan_indicator)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        
        plan_display_layout.addWidget(nav_container)
        
        right_layout.addWidget(plan_display_container)

        # Buttons
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background: transparent;")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 5, 0, 0)
        buttons_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        self.upgrade_btn = QPushButton("Upgrade Now")
        self.upgrade_btn.setCursor(Qt.PointingHandCursor)
        self.upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0077ed;
            }
            QPushButton:pressed {
                background-color: #0068c9;
            }
        """)
        self.upgrade_btn.clicked.connect(self.accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.upgrade_btn)
        
        right_layout.addWidget(buttons_container)

        footer_label = QLabel("Cancel anytime • 30-day money-back guarantee")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("""
            QLabel {
                color: #86868b;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
                padding: 5px 0px 0px 0px;
            }
        """)
        right_layout.addWidget(footer_label)

        main_horizontal_layout.addWidget(left_section)
        main_horizontal_layout.addWidget(right_section)

        layout.addWidget(container)
        
        self.selected_plan = None
        self.update_plan_display()

    def create_high_quality_png_label(self, filename, width, height, fallback_text):
        """Create a QLabel with high-quality PNG loading using QImageReader."""
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumSize(width, height)
        
        file_path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(file_path):
            reader = QImageReader(file_path)
            reader.setAutoTransform(True)
            reader.setQuality(100)  # Highest quality
            # Optionally set scaled size to reduce memory and improve performance
            reader.setScaledSize(QSize(width, height))
            
            image = reader.read()
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                # Set device pixel ratio for high-DPI displays
                pixmap.setDevicePixelRatio(self.devicePixelRatio())
                # Ensure smooth scaling (in case scaledSize wasn't used)
                scaled = pixmap.scaled(
                    width, height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                label.setPixmap(scaled)
                print(f"✅ Successfully loaded {filename} with high quality")
            else:
                print(f"❌ Failed to load {filename}: {reader.errorString()}")
                label.setText(fallback_text)
                label.setStyleSheet(f"""
                    QLabel {{
                        color: #1677ff;
                        font-size: 28px;
                        font-weight: bold;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                        background: transparent;
                    }}
                """)
        else:
            print(f"❌ {filename} not found")
            label.setText(fallback_text)
            label.setStyleSheet(f"""
                QLabel {{
                    color: #1677ff;
                    font-size: 28px;
                    font-weight: bold;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                    background: transparent;
                }}
            """)
        return label

    def update_plan_display(self):
        plan_name, price, features, color, ocean_color = self.plans[self.current_plan_index]
        
        layout = self.plan_widget.layout()
        if layout:
            QWidget().setLayout(layout)
        
        plan_layout = QVBoxLayout(self.plan_widget)
        plan_layout.setContentsMargins(15, 15, 15, 15)
        plan_layout.setSpacing(8)
        
        top_row = QHBoxLayout()
        name_label = QLabel(plan_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                font-size: 18px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                color: #1d1d1f;
                background: transparent;
            }}
        """)
        price_label = QLabel(price)
        price_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 16px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
            }}
        """)
        top_row.addWidget(name_label)
        top_row.addStretch()
        top_row.addWidget(price_label)
        
        features_text = "\n".join(f"• {f}" for f in features)
        features_label = QLabel(features_text)
        features_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial;
                background: transparent;
                line-height: 1.4;
            }
        """)
        
        plan_layout.addLayout(top_row)
        plan_layout.addWidget(features_label)
        
        self.plan_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {ocean_color};
                border: 2px solid {color};
                border-radius: 16px;
                padding: 10px;
            }}
        """)
        
        self.plan_indicator.setText(f"{self.current_plan_index + 1}/{len(self.plans)}")
        self.prev_btn.setEnabled(self.current_plan_index > 0)
        self.next_btn.setEnabled(self.current_plan_index < len(self.plans) - 1)
        
    def show_previous_plan(self):
        if self.current_plan_index > 0:
            self.current_plan_index -= 1
            self.update_plan_display()
    
    def show_next_plan(self):
        if self.current_plan_index < len(self.plans) - 1:
            self.current_plan_index += 1
            self.update_plan_display()
    
    def accept(self):
        plan_name, price, _, _, _ = self.plans[self.current_plan_index]
        self.selected_plan = (plan_name, price)
        super().accept()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() <= 40:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()

# Test window (unchanged)
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subscription Popup Test")
        self.setFixedSize(300, 200)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        btn = QPushButton("Show Subscription Popup")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4361ee;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
        """)
        btn.clicked.connect(self.show_subscription_popup)
        
        layout.addStretch()
        layout.addWidget(btn)
        layout.addStretch()
        
        self.result_label = QLabel("Click button to open subscription dialog")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color: #6c757d; margin-top: 20px;")
        layout.addWidget(self.result_label)
    
    def show_subscription_popup(self):
        dialog = SubscriptionPopupSample(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_plan:
            plan_name, price = dialog.selected_plan
            self.result_label.setText(f"Selected: {plan_name} - {price}")
            self.result_label.setStyleSheet("color: #4361ee; font-weight: bold; margin-top: 20px;")
        else:
            self.result_label.setText("No plan selected")
            self.result_label.setStyleSheet("color: #6c757d; margin-top: 20px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())