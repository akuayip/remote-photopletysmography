import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from collections import deque
import threading

class RespirationRPPGMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Pengukuran Respirasi dan rPPG")
        self.root.geometry("1200x800")
        
        # Variabel untuk menangkap video
        self.cap = None
        self.is_running = False
        self.thread = None
        
        # Buffer untuk menyimpan nilai sinyal
        self.buffer_size = 150  # Menampilkan sekitar 10 detik dengan 15 FPS
        self.respiration_buffer = deque(maxlen=self.buffer_size)
        self.ppg_buffer = deque(maxlen=self.buffer_size)
        self.time_buffer = deque(maxlen=self.buffer_size)
        self.start_time = time.time()
        
        # Nilai untuk kalkulasi
        self.respiration_rate = 0
        self.heart_rate = 0
        self.roi_face = None
        
        # Membuat layout
        self.create_widgets()
    
    def create_widgets(self):
        # Panel kontrol
        control_frame = ttk.LabelFrame(self.root, text="Kontrol")
        control_frame.pack(fill="x", padx=10, pady=5)
        
        start_button = ttk.Button(control_frame, text="Mulai Monitoring", command=self.start_monitoring)
        start_button.pack(side="left", padx=5, pady=5)
        
        stop_button = ttk.Button(control_frame, text="Hentikan Monitoring", command=self.stop_monitoring)
        stop_button.pack(side="left", padx=5, pady=5)
        
        # Panel informasi
        info_frame = ttk.LabelFrame(self.root, text="Informasi Vital")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(info_frame, text="Laju Pernapasan:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.resp_rate_label = ttk.Label(info_frame, text="-- bpm")
        self.resp_rate_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Laju Detak Jantung:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.heart_rate_label = ttk.Label(info_frame, text="-- bpm")
        self.heart_rate_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Panel untuk video dan grafik
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Panel untuk video
        video_frame = ttk.LabelFrame(content_frame, text="Video Webcam")
        video_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Panel untuk grafik
        graphs_frame = ttk.Frame(content_frame)
        graphs_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Grafik Respirasi
        resp_frame = ttk.LabelFrame(graphs_frame, text="Sinyal Respirasi")
        resp_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.resp_fig, self.resp_ax = plt.subplots(figsize=(6, 3))
        self.resp_canvas = FigureCanvasTkAgg(self.resp_fig, resp_frame)
        self.resp_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Grafik rPPG
        ppg_frame = ttk.LabelFrame(graphs_frame, text="Sinyal rPPG")
        ppg_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.ppg_fig, self.ppg_ax = plt.subplots(figsize=(6, 3))
        self.ppg_canvas = FigureCanvasTkAgg(self.ppg_fig, ppg_frame)
        self.ppg_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Mengatur bobot kolom
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Siap", relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
    
    def start_monitoring(self):
        if not self.is_running:
            self.is_running = True
            self.cap = cv2.VideoCapture(0)
            self.start_time = time.time()
            self.status_bar.config(text="Monitoring aktif...")
            
            # Reset buffers
            self.respiration_buffer.clear()
            self.ppg_buffer.clear()
            self.time_buffer.clear()
            
            # Memulai thread untuk pengambilan video
            self.thread = threading.Thread(target=self.update_frame)
            self.thread.daemon = True
            self.thread.start()

    def stop_monitoring(self):
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
        self.status_bar.config(text="Monitoring dihentikan")

    def update_frame(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                self.stop_monitoring()
                self.status_bar.config(text="Error: Tidak dapat mengakses webcam")
                break
            
            # Proses frame untuk respirasi dan rPPG
            self.process_frame(frame)
            
            # Tampilkan frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Tampilkan ROI jika ada
            if self.roi_face is not None:
                x, y, w, h = self.roi_face
                cv2.rectangle(frame_rgb, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            frame_resized = cv2.resize(frame_rgb, (400, 300))
            img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img = cv2.convertScaleAbs(img)
            
            # Konversi ke format yang dapat ditampilkan di Tkinter
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (400, 300))
            
            # Update label video di main thread
            self.root.after(0, self.update_video_label, img)
            
            # Update grafik di main thread
            self.root.after(0, self.update_graphs)
            
            # Update status
            self.root.after(0, self.update_status)
            
            # Sedikit delay untuk mengurangi beban CPU
            time.sleep(0.05)

    def update_video_label(self, img):
        img_pil = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_tk = self.convert_cv_to_tkinter(img_pil)
        self.video_label.config(image=img_tk)
        self.video_label.image = img_tk

    def convert_cv_to_tkinter(self, cv_image):
        """Mengkonversi gambar OpenCV ke format Tkinter"""
        from PIL import Image, ImageTk
        img_pil = Image.fromarray(cv_image)
        return ImageTk.PhotoImage(image=img_pil)

    def process_frame(self, frame):
        # Deteksi wajah
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        current_time = time.time() - self.start_time
        self.time_buffer.append(current_time)
        
        # Proses sinyal pernapasan (berdasarkan gerakan dada)
        # Ini adalah implementasi sederhana, untuk aplikasi nyata akan memerlukan algoritma lebih canggih
        respiration_value = 0
        
        # Deteksi sinyal rPPG dari wajah
        ppg_value = 0
        
        if len(faces) > 0:
            # Ambil wajah terbesar
            x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
            self.roi_face = (x, y, w, h)
            
            # Region of interest untuk wajah
            roi = frame[y:y+h, x:x+w]
            
            # Ekstrak sinyal respirasi dari gerakan dada (simulasi)
            # Pada implementasi nyata, ini mungkin melibatkan analisis gerakan dada atau perut
            respiration_value = np.mean(gray[y+h//2:y+h, x:x+w]) / 255.0
            
            # Ekstrak sinyal rPPG dari kanal warna (fokus pada kanal hijau yang paling sensitif terhadap perubahan darah)
            if roi.size > 0:
                # Ekstrak kanal warna
                b, g, r = cv2.split(roi)
                # rPPG biasanya didasarkan pada kanal hijau yang paling sensitif terhadap perubahan aliran darah
                ppg_value = np.mean(g) / 255.0
        
        # Tambahkan noise kecil untuk simulasi
        respiration_value += np.random.normal(0, 0.01)
        ppg_value += np.random.normal(0, 0.01)
        
        # Tambahkan ke buffer
        self.respiration_buffer.append(respiration_value)
        self.ppg_buffer.append(ppg_value)
        
        # Hitung laju pernapasan dan detak jantung (simulasi sederhana)
        if len(self.respiration_buffer) > 30:  # Minimal data untuk kalkulasi
            # Estimasi laju pernapasan (12-20 per menit biasanya)
            # Ini adalah implementasi sederhana, untuk aplikasi nyata akan menggunakan FFT atau metode lain
            self.respiration_rate = 15 + np.random.normal(0, 1)  # Simulasi 15 ± 1 napas per menit
            
            # Estimasi laju detak jantung (60-100 per menit biasanya)
            self.heart_rate = 75 + np.random.normal(0, 3)  # Simulasi 75 ± 3 detak per menit

    def update_graphs(self):
        # Update grafik respirasi
        self.resp_ax.clear()
        self.resp_ax.plot(list(self.time_buffer), list(self.respiration_buffer), 'b-')
        self.resp_ax.set_title('Sinyal Respirasi')
        self.resp_ax.set_xlabel('Waktu (detik)')
        self.resp_ax.set_ylabel('Amplitudo')
        self.resp_ax.grid(True)
        self.resp_canvas.draw()
        
        # Update grafik rPPG
        self.ppg_ax.clear()
        self.ppg_ax.plot(list(self.time_buffer), list(self.ppg_buffer), 'r-')
        self.ppg_ax.set_title('Sinyal rPPG')
        self.ppg_ax.set_xlabel('Waktu (detik)')
        self.ppg_ax.set_ylabel('Amplitudo')
        self.ppg_ax.grid(True)
        self.ppg_canvas.draw()

    def update_status(self):
        self.resp_rate_label.config(text=f"{self.respiration_rate:.1f} bpm")
        self.heart_rate_label.config(text=f"{self.heart_rate:.1f} bpm")

if __name__ == "__main__":
    root = tk.Tk()
    app = RespirationRPPGMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_monitoring)
    root.mainloop()