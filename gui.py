import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QGridLayout, QPushButton,
    QComboBox, QMessageBox, QSplitter
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QFont
import pyqtgraph as pg
from rppg_processor import RPPGProcessor
from respirasi_processor import RespirasiProcessor


class WelcomeScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.available_cameras = self.get_available_cameras()
        self.init_ui()
        self.dark_mode = False

    def init_ui(self):
        self.setWindowTitle('Welcome to Remote PPG')
        self.setGeometry(100, 100, 900, 500)

        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74ebd5, stop:1 #ACB6E5
                );
            }
        """)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        img_label = QLabel()
        img = QPixmap("assets/banner.png")
        img_label.setPixmap(img.scaledToHeight(150))
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img_label)

        title = QLabel('🩺 Remote PPG Monitor')
        title.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title)

        desc = QLabel('Monitor heart rate and respiration rate using your webcam in real-time.')
        desc.setFont(QFont('Arial', 14))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #34495e;")
        layout.addWidget(desc)

        features = QLabel("\u2714 Real-time signal visualization\n\u2714 Automatic detection\n\u2714 No contact required")
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features.setStyleSheet("color: #2d3436; font-size: 12pt; margin-top: 10px;")
        layout.addWidget(features)

        camera_layout = QHBoxLayout()
        camera_label = QLabel('Select Camera:')
        camera_label.setFont(QFont('Arial', 12))
        self.camera_combo = QComboBox()
        self.camera_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #222;
                font-size: 10pt;
                padding: 2px 6px;
                border: 1px solid #aaa;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                width: 20px;
                border-left: 1px solid #aaa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #222;
                selection-background-color: #cce5ff;
                border: 1px solid #aaa;
            }
        """)
        for cam_id, cam_name in self.available_cameras:
            self.camera_combo.addItem(f"{cam_name} (ID: {cam_id})", cam_id)
        camera_layout.addStretch()
        camera_layout.addWidget(camera_label)
        camera_layout.addWidget(self.camera_combo)
        camera_layout.addStretch()
        layout.addLayout(camera_layout)

        start_btn = QPushButton('🚀 Start Monitoring')
        start_btn.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white; 
                border-radius: 8px; 
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        start_btn.clicked.connect(self.start_monitoring)
        layout.addSpacing(20)
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def get_available_cameras(self):
        available_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append((i, f"Camera {i}"))
                cap.release()
        return available_cameras if available_cameras else [(0, "Default Camera")]

    def start_monitoring(self):
        selected_camera = self.camera_combo.currentData()
        if selected_camera is not None:
            self.dashboard = SignalDashboardGUI(selected_camera)
            self.dashboard.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Please select a camera first!")


class SignalDashboardGUI(QMainWindow):
    def __init__(self, camera_id):
        super().__init__()
        self.rppg = RPPGProcessor(fps=30)
        self.resp = RespirasiProcessor(fps=30)
        self.cap = cv2.VideoCapture(camera_id)

        if not self.cap.isOpened():
            QMessageBox.critical(self, "Error", "Could not open the selected camera!")
            self.close()
            return

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        self.setWindowTitle('Remote PPG Dashboard')
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout(central_widget)

        # Splitter utama horizontal: kiri = grafik, kanan = video + nilai
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout.addWidget(main_splitter)

        # --- KIRI: GRAFIK SINYAL ---
        self.rppg_plot = pg.PlotWidget()
        self.rppg_plot.setTitle("Monitor sinyal rPPG")
        self.rppg_plot.setLabel('left', 'Amplitude')
        self.rppg_plot.setLabel('bottom', 'Samples')
        self.rppg_curve = self.rppg_plot.plot(pen='g')

        self.resp_plot = pg.PlotWidget()
        self.resp_plot.setTitle("Monitor sinyal Respirator")
        self.resp_plot.setLabel('left', 'Amplitude')
        self.resp_plot.setLabel('bottom', 'Samples')
        self.resp_curve = self.resp_plot.plot(pen='y')

        signal_splitter = QSplitter(Qt.Orientation.Vertical)
        signal_splitter.addWidget(self.rppg_plot)
        signal_splitter.addWidget(self.resp_plot)
        signal_splitter.setSizes([1, 1])

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(signal_splitter)
        main_splitter.addWidget(left_widget)

        # --- KANAN: VIDEO + LABEL HR/RR ---
        self.video_label = QLabel()
        self.video_label.setFixedSize(320, 240)
        self.video_label.setStyleSheet("border: 1px solid gray; background-color: #ddd;")

        self.camera_combo = QComboBox()
        for cam_id, cam_name in self.get_available_cameras():
            self.camera_combo.addItem(f"{cam_name} (ID: {cam_id})", cam_id)
        self.camera_combo.currentIndexChanged.connect(self.change_camera)

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label, alignment=Qt.AlignmentFlag.AlignCenter)
        video_layout.addWidget(self.camera_combo, alignment=Qt.AlignmentFlag.AlignCenter)

        # Label RR
        rr_title = QLabel("RR (rpm)")
        rr_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        rr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rr_title.setStyleSheet("margin-bottom: 2px;")

        self.rr_label = QLabel('00.0')
        self.rr_label.setFont(QFont('Arial', 36, QFont.Weight.Bold))
        self.rr_label.setStyleSheet("color: green; border: 1px solid blue; padding: 10px;")

        rr_container = QVBoxLayout()
        rr_container.addWidget(rr_title)
        rr_container.addWidget(self.rr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Label HR
        hr_title = QLabel("rPPG (bpm)")
        hr_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        hr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hr_title.setStyleSheet("margin-bottom: 2px;")

        self.hr_label = QLabel('00.0')
        self.hr_label.setFont(QFont('Arial', 36, QFont.Weight.Bold))
        self.hr_label.setStyleSheet("color: red; border: 1px solid blue; padding: 10px;")

        hr_container = QVBoxLayout()
        hr_container.addWidget(hr_title)
        hr_container.addWidget(self.hr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Gabungkan rate display
        rate_layout = QHBoxLayout()
        rate_layout.addLayout(rr_container)
        rate_layout.addLayout(hr_container)

        # Gabungkan video + rate
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addLayout(video_layout)
        right_layout.addSpacing(10)
        right_layout.addLayout(rate_layout)
        main_splitter.addWidget(right_widget)

        # Lebih banyak space untuk grafik
        main_splitter.setSizes([900, 300])


    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(33)

    def update_data(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.resize(frame, (640, 480))

        rect = self.rppg.get_forehead_rect()
        if rect:
            x1, y1, x2, y2 = rect
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        shoulder_points = self.resp.get_shoulder_points()
        if shoulder_points:
            left_shoulder, right_shoulder = shoulder_points[-1]
            if left_shoulder[0] > 0 and left_shoulder[1] > 0:
                cv2.circle(frame, left_shoulder, 6, (0, 255, 0), -1)
            if right_shoulder[0] > 0 and right_shoulder[1] > 0:
                cv2.circle(frame, right_shoulder, 6, (0, 255, 0), -1)

        self.rppg.extract_rgb_from_frame(frame)
        self.resp.extract_resp_from_frame(frame)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_img = QImage(rgb_frame.data, w, h, w * ch, QImage.Format.Format_RGB888)
        scaled_img = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_img)


        self.rppg_curve.setData(self.rppg.get_filtered_rppg()[-200:])
        self.resp_curve.setData(self.resp.get_filtered_resp()[-200:])

        self.hr_label.setText(f"{self.rppg.get_heart_rate():.1f}")
        self.rr_label.setText(f"{self.resp.get_respiration_rate():.1f}")

    def change_camera(self):
        cam_id = self.camera_combo.currentData()
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(cam_id)

    def get_available_cameras(self):
        cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append((i, f"Camera {i}"))
                cap.release()
        return cameras or [(0, "Default Camera")]

    def closeEvent(self, event):
        self.cap.release()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WelcomeScreen()
    window.show()
    sys.exit(app.exec())
