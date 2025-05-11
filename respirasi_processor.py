# respirasi_processor.py

import cv2
import numpy as np

class RespirasiProcessor:
    def __init__(self):
        self.respirasi_signal = []

    def extract_resp_from_frame(self, frame):
        """
        Ambil sinyal respirasi dari perubahan brightness di dada/leher (ROI).
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        roi = gray[int(h*0.6):int(h*0.8), int(w*0.4):int(w*0.6)]  # ROI bagian bawah tengah (dada)
        value = np.mean(roi)
        self.respirasi_signal.append(value)

    def get_signal(self):
        return self.respirasi_signal
