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

        # === Layout: 2x2 ===
        self.fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 2, width_ratios=[2, 1], height_ratios=[1, 1], figure=self.fig)

        # Sinyal rPPG
        self.ax_rppg = self.fig.add_subplot(gs[0, 0])
        self.ax_rppg.set_title("Sinyal rPPG")
        self.rppg_line, = self.ax_rppg.plot([], [], color='green')

        # Sinyal respirasi
        self.ax_resp = self.fig.add_subplot(gs[1, 0])
        self.ax_resp.set_title("Sinyal Respirasi")
        self.resp_line, = self.ax_resp.plot([], [], color='orange')

        # Kamera (kanan atas)
        self.ax_cam = self.fig.add_subplot(gs[0, 1])
        self.ax_cam.set_title("Camera")
        self.img_cam = self.ax_cam.imshow(np.zeros((480, 640, 3), dtype=np.uint8))
        self.ax_cam.axis("off")

        # Informasi angka realtime (kanan bawah)
        self.ax_info = self.fig.add_subplot(gs[1, 1])
        self.ax_info.axis("off")

        # Batas sumbu awal
        self.ax_rppg.set_xlim(0, 100)
        self.ax_resp.set_xlim(0, 100)
        self.ax_rppg.set_ylim(0, 255)
        self.ax_resp.set_ylim(-10, 10)

    def update(self, _):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.resize(frame, (640, 480))

        # Gambar kotak ROI jidat (rPPG)
        rect = self.rppg.get_forehead_rect()
        if rect:
            x1, y1, x2, y2 = rect
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        self.rppg.extract_rgb_from_frame(frame)
        self.resp.extract_resp_from_frame(frame)

        # Titik bahu dari pose
        shoulder_points = self.resp.get_shoulder_points()
        if shoulder_points:
            left_shoulder, right_shoulder = shoulder_points[-1]
            if left_shoulder[0] > 0 and left_shoulder[1] > 0:
                cv2.circle(frame, left_shoulder, 6, (0, 255, 0), -1)
            if right_shoulder[0] > 0 and right_shoulder[1] > 0:
                cv2.circle(frame, right_shoulder, 6, (0, 255, 0), -1)

        # Convert frame ke RGB untuk matplotlib
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.img_cam.set_data(frame_rgb)

        # Ambil sinyal
        rppg_data = self.rppg.g[-100:]
        resp_data = self.resp.get_signal()[-100:]

        # Update grafik
        self.rppg_line.set_data(np.arange(len(rppg_data)), rppg_data)
        self.resp_line.set_data(np.arange(len(resp_data)), resp_data)

        self.ax_rppg.set_xlim(0, len(rppg_data))
        self.ax_resp.set_xlim(0, len(resp_data))

        if rppg_data:
            self.ax_rppg.set_ylim(min(rppg_data) - 10, max(rppg_data) + 10)
        if resp_data:
            self.ax_resp.set_ylim(min(resp_data) - 1, max(resp_data) + 1)

        # Update nilai angka realtime
        rppg_val = rppg_data[-1] if rppg_data else 0
        resp_val = resp_data[-1] if resp_data else 0

        self.ax_info.clear()
        self.ax_info.axis("off")
        self.ax_info.set_title("Nilai Real-Time")

        self.ax_info.text(0.3, 0.6, "rPPG", fontsize=10, ha='center')
        self.ax_info.text(0.3, 0.3, f"{rppg_val:.1f}", fontsize=20, ha='center', color='green')

        self.ax_info.text(0.7, 0.6, "Resp", fontsize=10, ha='center')
        self.ax_info.text(0.7, 0.3, f"{resp_val:.1f}", fontsize=20, ha='center', color='orange')

    def run(self):
        ani = animation.FuncAnimation(
            self.fig, self.update, interval=100,
            blit=False, cache_frame_data=False
        )
        plt.tight_layout()
        plt.show()
        self.cap.release()
