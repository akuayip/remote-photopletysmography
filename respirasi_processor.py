import cv2
import numpy as np
import mediapipe as mp
from collections import deque

class RespirasiProcessor:
    def __init__(self, max_len=100, smoothing_window=5):
        self.pose = mp.solutions.pose.Pose(static_image_mode=False)
        self.prev_shoulder_y = None
        self.shoulder_motion_signal = []
        self.shoulder_points = []
        self.smoothed_signal = deque(maxlen=smoothing_window)

    def extract_resp_from_frame(self, frame):
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Gunakan bahu kiri (LEFT_SHOULDER = 11) dan bahu kanan (RIGHT_SHOULDER = 12)
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_x = int(left_shoulder.x * w)
            left_y = int(left_shoulder.y * h)
            right_x = int(right_shoulder.x * w)
            right_y = int(right_shoulder.y * h)

            # Menyimpan titik bahu kiri dan kanan
            self.shoulder_points.append(((left_x, left_y), (right_x, right_y)))

            if self.prev_shoulder_y is not None:
                # Perubahan posisi vertikal bahu kiri dan kanan
                dy_left = self.prev_shoulder_y[0] - left_y
                dy_right = self.prev_shoulder_y[1] - right_y
                self.smoothed_signal.append((dy_left + dy_right) / 2)
                smoothed_value = np.mean(self.smoothed_signal)
                self.shoulder_motion_signal.append(smoothed_value)
            else:
                self.shoulder_motion_signal.append(0)

            self.prev_shoulder_y = (left_y, right_y)
        else:
            self.shoulder_motion_signal.append(0)
            self.shoulder_points.append(((0, 0), (0, 0)))

    def get_signal(self):
        return self.shoulder_motion_signal

    def get_shoulder_points(self):
        return self.shoulder_points
