# rppg_processor.py

import numpy as np
import cv2
import mediapipe as mp
from signal_utils import bandpass_filter_rppg, calculate_heart_rate

class RPPGProcessor:
    def __init__(self, fps=30):
        self.fps = fps
        self.r, self.g, self.b = [], [], []
        self.filtered_rppg = []
        self.heart_rate = 0

        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

        self.last_forehead_rect = None  # Untuk menampilkan ROI di kamera

    def extract_rgb_from_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)

        h, w, _ = frame.shape
        r_mean = g_mean = b_mean = 0

        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box

            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)

            # ROI hanya jidat (lebih presisi)
            forehead_x1 = x + int(0.15 * width)
            forehead_x2 = x + int(0.85 * width)
            forehead_y1 = y - int(0.10 * height)
            forehead_y2 = y + int(0.08 * height)

            # Validasi batas ROI
            forehead_x1 = max(0, forehead_x1)
            forehead_x2 = min(w, forehead_x2)
            forehead_y1 = max(0, forehead_y1)
            forehead_y2 = min(h, forehead_y2)

            self.last_forehead_rect = (forehead_x1, forehead_y1, forehead_x2, forehead_y2)

            roi = frame[forehead_y1:forehead_y2, forehead_x1:forehead_x2]
            if roi.size > 0:
                r_mean = np.mean(roi[:, :, 2])
                g_mean = np.mean(roi[:, :, 1])
                b_mean = np.mean(roi[:, :, 0])
        else:
            self.last_forehead_rect = None

        # Simpan nilai ke sinyal
        self.r.append(r_mean)
        self.g.append(g_mean)
        self.b.append(b_mean)
        

        # Filter green channel (rPPG) dan hitung HR
        if len(self.g) >= 30:
            self.filtered_rppg = bandpass_filter_rppg(self.g, fs=self.fps)
            self.heart_rate, _ = calculate_heart_rate(self.filtered_rppg, fs=self.fps)
        else:
            self.filtered_rppg = self.g
            self.heart_rate = 0

    # ===== Akses ke data =====

    def get_forehead_rect(self):
        return self.last_forehead_rect

    def get_rgb_signals(self):
        return np.array([self.r, self.g, self.b]).reshape(1, 3, -1)

    def get_filtered_rppg(self):
        return self.filtered_rppg

    def get_heart_rate(self):
        return self.heart_rate

    # (Optional) Metode POS tetap bisa digunakan
    def compute_pos(self, signal):
        eps = 1e-9
        e, c, f = signal.shape
        w = int(1.6 * self.fps)
        P = np.array([[0, 1, -1], [-2, 1, 1]])
        Q = np.stack([P for _ in range(e)], axis=0)
        H = np.zeros((e, f))

        for n in np.arange(w, f):
            m = n - w + 1
            Cn = signal[:, :, m:(n + 1)]
            M = 1.0 / (np.mean(Cn, axis=2) + eps)
            M = np.expand_dims(M, axis=2)
            Cn = np.multiply(M, Cn)
            S = np.dot(Q, Cn)[0]
            S = np.swapaxes(S, 0, 1)
            S1, S2 = S[:, 0, :], S[:, 1, :]
            alpha = np.std(S1, axis=1) / (np.std(S2, axis=1) + eps)
            alpha = np.expand_dims(alpha, axis=1)
            Hn = S1 + alpha * S2
            Hn -= np.expand_dims(np.mean(Hn, axis=1), axis=1)
            H[:, m:(n + 1)] += Hn

        return H.reshape(-1)