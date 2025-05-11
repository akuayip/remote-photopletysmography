# rppg_processor.py

import numpy as np
import cv2
import mediapipe as mp

class RPPGProcessor:
    def __init__(self, fps=30):
        self.fps = fps
        self.r, self.g, self.b = [], [], []

        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    def extract_rgb_from_frame(self, frame):
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)

        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)

            bbox_size = 70
            cx, cy = x + width // 2, y + height // 2
            x1, y1 = cx - bbox_size, cy - bbox_size
            x2, y2 = cx + bbox_size, cy + bbox_size

            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                self.r.append(np.mean(roi[:, :, 2]))
                self.g.append(np.mean(roi[:, :, 1]))
                self.b.append(np.mean(roi[:, :, 0]))

    def get_rgb_signals(self):
        return np.array([self.r, self.g, self.b]).reshape(1, 3, -1)

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
