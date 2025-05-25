import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2 # Untuk OpenCV
from PIL import Image, ImageTk # Untuk menampilkan frame OpenCV di Tkinter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Impor kelas prosesor kamu (pastikan path-nya benar)
# Misal mereka ada di folder yang sama atau bisa diimpor Python
try:
    from rppg_processor import RPPGProcessor
    from respirasi_processor import RespirasiProcessor
except ImportError:
    messagebox.showerror("Error Impor", "Pastikan file rppg_processor.py dan respirasi_processor.py ada dan bisa diimpor.")
    RPPGProcessor = None
    RespirasiProcessor = None

class AppRPPG(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplikasi Analisis rPPG & Respirasi")
        self.geometry("1200x800")

        # Inisialisasi Processor (jika berhasil diimpor)
        if RPPGProcessor and RespirasiProcessor:
            self.rppg_proc = RPPGProcessor(fps=30) # Asumsi FPS kamera, bisa diatur
            self.resp_proc = RespirasiProcessor()
        else:
            self.rppg_proc = None
            self.resp_proc = None
            # Tambahkan label error atau disable tombol jika prosesor tidak ada
            ttk.Label(self, text="ERROR: Processor tidak bisa dimuat!", foreground="red").pack(pady=20)


        self.video_source = 0 # 0 untuk kamera default, bisa diganti path file
        self.cap = None
        self.processing_active = False
        self.frame_width = 640
        self.frame_height = 480

        self.create_widgets()
        self.update_interval = 30 # ms, sekitar 33 FPS untuk update GUI

    def create_widgets(self):
        # --- Menu Bar ---
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Buka Video File...", command=self.open_video_file)
        file_menu.add_separator()
        file_menu.add_command(label="Keluar", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        # Tambahkan menu lain jika perlu (Pengaturan, Bantuan)
        self.config(menu=menubar)

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Panel Kontrol ---
        control_panel = ttk.LabelFrame(main_frame, text="Kontrol", padding="10")
        control_panel.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.btn_start_cam = ttk.Button(control_panel, text="Mulai Kamera", command=self.start_camera_processing)
        self.btn_start_cam.pack(side=tk.LEFT, padx=5)
        self.btn_stop_cam = ttk.Button(control_panel, text="Stop Kamera", command=self.stop_processing, state=tk.DISABLED)
        self.btn_stop_cam.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(control_panel, text="Status: Idle")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # --- Area Tampilan (Video, Grafik, Data) ---
        display_area = ttk.Frame(main_frame)
        display_area.pack(fill=tk.BOTH, expand=True, pady=10)

        # Area Video (Kiri)
        video_frame_container = ttk.LabelFrame(display_area, text="Live Feed Kamera", padding="5")
        video_frame_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.video_label = ttk.Label(video_frame_container) # Label untuk menampilkan frame video
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Area Grafik & Data (Kanan) - bisa pakai Notebook/Tabs jika banyak
        plot_data_frame = ttk.Frame(display_area)
        plot_data_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Placeholder untuk Grafik rPPG (Matplotlib)
        rppg_plot_frame = ttk.LabelFrame(plot_data_frame, text="Sinyal rPPG")
        rppg_plot_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.fig_rppg, self.ax_rppg = plt.subplots() # Buat figure dan axes untuk rPPG
        self.rppg_line, = self.ax_rppg.plot([], [], 'g-') # Garis awal
        self.ax_rppg.set_title("Detak Jantung (rPPG)")
        self.ax_rppg.set_xlabel("Sampel")
        self.ax_rppg.set_ylabel("Intensitas (G)")
        self.canvas_rppg = FigureCanvasTkAgg(self.fig_rppg, master=rppg_plot_frame)
        self.canvas_rppg.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_rppg.draw()

        # Placeholder untuk Grafik Respirasi (Matplotlib)
        resp_plot_frame = ttk.LabelFrame(plot_data_frame, text="Sinyal Respirasi")
        resp_plot_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.fig_resp, self.ax_resp = plt.subplots() # Buat figure dan axes untuk Respirasi
        self.resp_line, = self.ax_resp.plot([], [], 'b-') # Garis awal
        self.ax_resp.set_title("Pernapasan")
        self.ax_resp.set_xlabel("Sampel")
        self.ax_resp.set_ylabel("Pergerakan")
        self.canvas_resp = FigureCanvasTkAgg(self.fig_resp, master=resp_plot_frame)
        self.canvas_resp.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_resp.draw()

        # Placeholder untuk Data Numerik
        numeric_data_frame = ttk.LabelFrame(plot_data_frame, text="Data Terukur")
        numeric_data_frame.pack(fill=tk.X, pady=2)
        self.hr_label = ttk.Label(numeric_data_frame, text="Detak Jantung (BPM): --")
        self.hr_label.pack(anchor=tk.W, padx=5)
        self.rr_label = ttk.Label(numeric_data_frame, text="Laju Pernapasan (BrPM): --")
        self.rr_label.pack(anchor=tk.W, padx=5)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text="Selamat Datang!", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_video_file(self):
        filepath = filedialog.askopenfilename(
            title="Pilih Video File",
            filetypes=(("Video files", "*.mp4 *.avi *.mov"), ("All files", "*.*"))
        )
        if filepath:
            self.video_source = filepath
            self.status_bar.config(text=f"Video dipilih: {filepath}")
            messagebox.showinfo("Info Video", f"Video file dipilih: {filepath}\nKlik 'Mulai Kamera' untuk memproses (akan diubah jadi 'Proses File').")
            # Di sini bisa ubah teks tombol Start atau tambahkan tombol baru "Proses File"

    def start_camera_processing(self):
        if self.rppg_proc is None or self.resp_proc is None:
            messagebox.showerror("Error", "Processor rPPG/Respirasi tidak berhasil dimuat.")
            return

        if self.processing_active:
            messagebox.showwarning("Peringatan", "Pemrosesan sudah aktif.")
            return

        try:
            self.cap = cv2.VideoCapture(self.video_source)
            if not self.cap.isOpened():
                raise ValueError("Tidak bisa membuka sumber video.")
            self.processing_active = True
            self.status_label.config(text="Status: Memproses...")
            self.status_bar.config(text=f"Memproses dari: {'Kamera' if isinstance(self.video_source, int) else self.video_source}")
            self.btn_start_cam.config(state=tk.DISABLED)
            self.btn_stop_cam.config(state=tk.NORMAL)

            # Reset data rppg/resp proc jika perlu
            self.rppg_proc.r, self.rppg_proc.g, self.rppg_proc.b = [], [], []
            self.resp_proc.shoulder_motion_signal = []
            self.resp_proc.shoulder_points = []


            self.update_frame_and_plots() # Mulai loop update
        except Exception as e:
            messagebox.showerror("Error Memulai Kamera", str(e))
            self.status_label.config(text="Status: Error")
            self.processing_active = False
            if self.cap:
                self.cap.release()
                self.cap = None


    def stop_processing(self):
        self.processing_active = False
        self.status_label.config(text="Status: Idle")
        self.status_bar.config(text="Pemrosesan dihentikan.")
        self.btn_start_cam.config(state=tk.NORMAL)
        self.btn_stop_cam.config(state=tk.DISABLED)
        if self.cap:
            self.cap.release()
            self.cap = None
        # Reset video_source ke kamera default setelah file selesai atau dihentikan
        if not isinstance(self.video_source, int):
            self.video_source = 0


    def update_frame_and_plots(self):
        if not self.processing_active or not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            # Jika dari file video dan sudah habis, stop
            if not isinstance(self.video_source, int):
                self.stop_processing()
                messagebox.showinfo("Info", "Pemrosesan file video selesai.")
                return
            # Jika dari kamera dan error, coba lagi atau stop
            self.after(self.update_interval, self.update_frame_and_plots) # Coba lagi
            return

        frame_display = cv2.resize(frame, (self.frame_width, self.frame_height))

        # Proses dengan RPPG dan Respirasi Processor
        # Frame yang diproses oleh processor bisa frame asli atau frame_display
        # tergantung kebutuhan akurasi vs kecepatan display
        self.rppg_proc.extract_rgb_from_frame(frame_display.copy()) # copy() jika frame_display akan diubah
        self.resp_proc.extract_resp_from_frame(frame_display.copy())

        # Ambil ROI dahi dan gambar di frame_display
        forehead_rect = self.rppg_proc.get_forehead_rect()
        if forehead_rect:
            x1, y1, x2, y2 = forehead_rect
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Ambil titik bahu dan gambar
        shoulder_points = self.resp_proc.get_shoulder_points()
        if shoulder_points and len(shoulder_points) > 0:
            last_shoulders = shoulder_points[-1]
            if last_shoulders[0] != (0,0): # Cek jika valid
                 cv2.circle(frame_display, last_shoulders[0], 5, (0, 255, 0), -1) # Kiri
            if last_shoulders[1] != (0,0): # Cek jika valid
                 cv2.circle(frame_display, last_shoulders[1], 5, (0, 0, 255), -1) # Kanan

        # Konversi frame OpenCV ke format Tkinter PhotoImage
        frame_rgb = cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk # Simpan referensi
        self.video_label.config(image=imgtk)

        # Update Grafik rPPG (misalnya ambil sinyal Green, 100-200 data terakhir)
        rppg_plot_data = np.array(self.rppg_proc.g[-200:])
        self.rppg_line.set_data(np.arange(len(rppg_plot_data)), rppg_plot_data)
        self.ax_rppg.set_xlim(0, len(rppg_plot_data) if len(rppg_plot_data) > 1 else 100)
        if len(rppg_plot_data) > 0:
            self.ax_rppg.set_ylim(min(rppg_plot_data)-5 if min(rppg_plot_data) is not None else 0,
                                  max(rppg_plot_data)+5 if max(rppg_plot_data) is not None else 255)
        self.canvas_rppg.draw_idle() # draw_idle lebih efisien untuk update sering

        # Update Grafik Respirasi
        resp_plot_data = np.array(self.resp_proc.get_signal()[-200:])
        self.resp_line.set_data(np.arange(len(resp_plot_data)), resp_plot_data)
        self.ax_resp.set_xlim(0, len(resp_plot_data) if len(resp_plot_data) > 1 else 100)
        if len(resp_plot_data) > 0:
            self.ax_resp.set_ylim(min(resp_plot_data)-1 if min(resp_plot_data) is not None else -5,
                                  max(resp_plot_data)+1 if max(resp_plot_data) is not None else 5)
        self.canvas_resp.draw_idle()

        # TODO: Hitung dan tampilkan HR & RR aktual
        # Ini contoh placeholder, kamu perlu panggil fungsi dari signal_utils.py
        # setelah sinyal cukup panjang dan sudah difilter
        # if len(self.rppg_proc.g) > N_SAMPLES_MINIMUM:
        #     # rppg_raw = self.rppg_proc.compute_pos(...) # jika perlu
        #     # rppg_filtered = bandpass_filter(rppg_raw_or_green_signal)
        #     # hr, peaks = calculate_heart_rate(rppg_filtered)
        #     # self.hr_label.config(text=f"Detak Jantung (BPM): {hr:.2f}")
        #     pass
        # if len(self.resp_proc.get_signal()) > M_SAMPLES_MINIMUM:
        #     # rr = calculate_respiration_rate(...)
        #     # self.rr_label.config(text=f"Laju Pernapasan (BrPM): {rr:.2f}")
        #     pass

        # Jadwalkan update berikutnya
        if self.processing_active:
            self.after(self.update_interval, self.update_frame_and_plots)

    def quit_app(self):
        self.stop_processing() # Pastikan kamera dilepas
        self.quit()
        self.destroy()


if __name__ == "__main__":
    # Cek dependensi Pillow
    try:
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror("Error Dependensi", "Pillow (PIL) tidak terinstal. \nSilakan install dengan: pip install Pillow")
        exit()

    app = AppRPPG()
    app.mainloop()