# respirasi_processor.py

import cv2
import numpy as np
import mediapipe as mp
from collections import deque
from signal_utils import bandpass_filter_respirasi, calculate_respiration_rate


class RespirasiProcessor:
    def __init__(self, max_len=100, smoothing_window=5, fps=30):
        self.pose = mp.solutions.pose.Pose(static_image_mode=False)
        self.prev_shoulder_y = None
        self.shoulder_motion_signal = []
        self.filtered_signal = []
        self.respiration_rate = 0
        self.shoulder_points = []
        self.smoothed_signal = deque(maxlen=smoothing_window)
        self.fps = fps
        # Untuk menyimpan frame sebelumnya (Farneback Optical Flow)
        self.prev_gray = None

    def extract_resp_from_frame(self, frame):
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Ambil titik bahu kiri (id 11) dan kanan (id 12)
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]

            # Konversi koordinat normalisasi ke piksel
            left_x = int(left_shoulder.x * w)
            left_y = int(left_shoulder.y * h)
            right_x = int(right_shoulder.x * w)
            right_y = int(right_shoulder.y * h)

            # Simpan titik bahu
            self.shoulder_points.append(((left_x, left_y), (right_x, right_y)))

            if self.prev_shoulder_y is not None:
                # Perubahan posisi vertikal bahu kiri dan kanan
                dy_left = self.prev_shoulder_y[0] - left_y
                dy_right = self.prev_shoulder_y[1] - right_y
                motion = (dy_left + dy_right) / 2
                self.smoothed_signal.append(motion)
                smoothed_value = np.mean(self.smoothed_signal)
                self.shoulder_motion_signal.append(smoothed_value)
            else:
                self.shoulder_motion_signal.append(0)

            self.prev_shoulder_y = (left_y, right_y)
        else:
            self.shoulder_motion_signal.append(0)
            self.shoulder_points.append(((0, 0), (0, 0)))

        # Gunakan Farneback Optical Flow untuk memperhalus sinyal
        self._apply_optical_flow(frame)

        # Filter sinyal respirasi dan hitung RR (napas per menit)
        if len(self.shoulder_motion_signal) >= 30:
            self.filtered_signal = bandpass_filter_respirasi(
                self.shoulder_motion_signal, fs=self.fps)
            self.respiration_rate, _ = calculate_respiration_rate(
                self.filtered_signal, fs=self.fps)
        else:
            self.filtered_signal = self.shoulder_motion_signal
            self.respiration_rate = 0

    def _apply_optical_flow(self, frame):
        # Konversi frame ke grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is not None:
            # Hitung optical flow menggunakan metode Farneback
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )

            # Ambil pergerakan vertikal (sumbu y) dari optical flow
            flow_y = flow[..., 1]

            # Hitung rata-rata pergerakan vertikal di area bahu
            if self.shoulder_points:
                left_shoulder, right_shoulder = self.shoulder_points[-1]
                lx, ly = left_shoulder
                rx, ry = right_shoulder

                # Tentukan bounding box di sekitar bahu
                bbox_size = 10  # Ukuran bounding box (10x10 piksel)
                left_flow_y = np.mean(flow_y[max(0, ly - bbox_size):min(flow_y.shape[0], ly + bbox_size),
                                             max(0, lx - bbox_size):min(flow_y.shape[1], lx + bbox_size)])
                right_flow_y = np.mean(flow_y[max(0, ry - bbox_size):min(flow_y.shape[0], ry + bbox_size),
                                              max(0, rx - bbox_size):min(flow_y.shape[1], rx + bbox_size)])

                # Tambahkan hasil optical flow ke sinyal
                avg_flow_y = (left_flow_y + right_flow_y) / 2
                self.shoulder_motion_signal[-1] += avg_flow_y

        # Simpan frame saat ini sebagai frame sebelumnya untuk iterasi berikutnya
        self.prev_gray = gray

    # === Getter ===

    def get_signal(self):
        return self.shoulder_motion_signal

    def get_filtered_resp(self):
        return self.filtered_signal

    def get_respiration_rate(self):
        return self.respiration_rate

    def get_shoulder_points(self):
        return self.shoulder_points
