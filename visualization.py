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

        # Subplot sinyal rPPG
        self.ax_rppg = self.fig.add_subplot(gs[0, 0])
        self.ax_rppg.set_title("Sinyal rPPG")
        self.rppg_line, = self.ax_rppg.plot([], [], color='green')

        # Subplot sinyal respirasi
        self.ax_resp = self.fig.add_subplot(gs[1, 0])
        self.ax_resp.set_title("Sinyal Respirasi (Pergerakan Bahu)")
        self.resp_line, = self.ax_resp.plot([], [], color='orange')

        # Subplot kamera
        self.ax_cam = self.fig.add_subplot(gs[:, 1])
        self.ax_cam.set_title("Camera)")
        self.img_cam = self.ax_cam.imshow(np.zeros((480, 640, 3), dtype=np.uint8))
        self.ax_cam.axis("off")

        # Batas sumbu awal
        self.ax_rppg.set_xlim(0, 100)
        self.ax_resp.set_xlim(0, 100)
        self.ax_rppg.set_ylim(0, 255)
        self.ax_resp.set_ylim(-10, 10)

    def update(self, _):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Ambil dan gambar kotak hijau di jidat
        rect = self.rppg.get_forehead_rect()
        if rect:
            x1, y1, x2, y2 = rect
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        frame = cv2.resize(frame, (640, 480))

        self.rppg.extract_rgb_from_frame(frame)
        self.resp.extract_resp_from_frame(frame)

        # Ambil data sinyal
        rppg_data = self.rppg.g[-100:]
        resp_data = self.resp.get_signal()[-100:]

        # Convert BGR ke RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Menambahkan titik bahu kiri dan kanan dari MediaPipe Pose
        shoulder_points = self.resp.get_shoulder_points()
        if shoulder_points:
            left_shoulder, right_shoulder = shoulder_points[-1]
            if left_shoulder[0] > 0 and left_shoulder[1] > 0:
                cv2.circle(frame_rgb, left_shoulder, 6, (0, 255, 0), -1)  # Bahu Kiri
            if right_shoulder[0] > 0 and right_shoulder[1] > 0:
                cv2.circle(frame_rgb, right_shoulder, 6, (0, 255, 0), -1)  # Bahu Kanan

        # Update grafik sinyal
        self.rppg_line.set_data(np.arange(len(rppg_data)), rppg_data)
        self.resp_line.set_data(np.arange(len(resp_data)), resp_data)
        self.img_cam.set_data(frame_rgb)

        # Update sumbu X
        self.ax_rppg.set_xlim(0, len(rppg_data))
        self.ax_resp.set_xlim(0, len(resp_data))

        # Update sumbu Y dinamis
        if len(rppg_data) > 0:
            self.ax_rppg.set_ylim(min(rppg_data) - 10, max(rppg_data) + 10)
        if len(resp_data) > 0:
            self.ax_resp.set_ylim(min(resp_data) - 1, max(resp_data) + 1)

    def run(self):
        ani = animation.FuncAnimation(
            self.fig, self.update, interval=100,
            blit=False, cache_frame_data=False
        )
        plt.tight_layout()
        plt.show()
        self.cap.release()
