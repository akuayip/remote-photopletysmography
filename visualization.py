# visualization.py

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cv2
import numpy as np
import matplotlib.gridspec as gridspec

class SignalDashboard:
    def __init__(self, rppg_processor, respirasi_processor):
        self.rppg = rppg_processor
        self.resp = respirasi_processor
        self.cap = cv2.VideoCapture(0)

        self.fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 2, width_ratios=[2, 1])

        self.ax_rppg = self.fig.add_subplot(gs[0, 0])
        self.ax_rppg.set_title("Sinyal rPPG")
        self.rppg_line, = self.ax_rppg.plot([], [], color='green')

        self.ax_resp = self.fig.add_subplot(gs[1, 0])
        self.ax_resp.set_title("Sinyal Respirasi")
        self.resp_line, = self.ax_resp.plot([], [], color='yellow')

        self.ax_cam = self.fig.add_subplot(gs[:, 1])
        self.ax_cam.set_title("Camera")
        self.img_cam = self.ax_cam.imshow(np.zeros((480, 640, 3), dtype=np.uint8))

        self.ax_rppg.set_xlim(0, 100)
        self.ax_resp.set_xlim(0, 100)
        self.ax_rppg.set_ylim(0, 255)
        self.ax_resp.set_ylim(0, 255)
        self.ax_cam.axis("off")  # opsional

    def update(self, frame):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.resize(frame, (640, 480))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.rppg.extract_rgb_from_frame(frame)
        self.resp.extract_resp_from_frame(frame)

        rppg_data = self.rppg.g[-100:]
        resp_data = self.resp.get_signal()[-100:]

        self.rppg_line.set_data(np.arange(len(rppg_data)), rppg_data)
        self.resp_line.set_data(np.arange(len(resp_data)), resp_data)
        self.img_cam.set_data(frame_rgb)

        self.ax_rppg.set_xlim(0, len(rppg_data))
        self.ax_resp.set_xlim(0, len(resp_data))

        if len(rppg_data) > 0:
            self.ax_rppg.set_ylim(min(rppg_data) - 10, max(rppg_data) + 10)
        if len(resp_data) > 0:
            self.ax_resp.set_ylim(min(resp_data) - 10, max(resp_data) + 10)

    def run(self):
        ani = animation.FuncAnimation(
            self.fig, self.update, interval=100,
            blit=False, cache_frame_data=False
        )
        plt.tight_layout()
        plt.show()
        self.cap.release()
