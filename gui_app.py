import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import os # Diperlukan untuk path aset jika kamu memindahkan gambar ikon kamera

# Coba impor Pillow
try:
    from PIL import Image, ImageTk
    PILLOW_GUI_AVAILABLE = True
    print("DEBUG: Pillow (Image, ImageTk) berhasil diimpor di gui_app.py.")
except ImportError:
    PILLOW_GUI_AVAILABLE = False
    print("ERROR KRITIS: Pillow (PIL) tidak terinstal untuk gui_app.py.")

# Impor untuk Matplotlib
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
    # plt.style.use('seaborn-v0_8-darkgrid') # Opsional
    print("DEBUG: Matplotlib berhasil diimpor.")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("ERROR: Matplotlib tidak terinstal. Grafik tidak akan tampil.")

# Impor kelas prosesor
# !! GANTI NAMA FILE JIKA PERLU (misalnya rppg_proccessor.py) !!
try:
    from rppg_processor import RPPGProcessor
    from respirasi_processor import RespirasiProcessor
    PROCESSORS_AVAILABLE = True
    print("DEBUG: RPPGProcessor dan RespirasiProcessor berhasil diimpor.")
except ImportError as e:
    PROCESSORS_AVAILABLE = False
    RPPGProcessor = None
    RespirasiProcessor = None
    print(f"ERROR DEBUG: Tidak bisa impor RPPGProcessor atau RespirasiProcessor: {e}")


class AppRPPG(tk.Tk):
    def __init__(self, master=None):
        super().__init__(master)
        print("DEBUG: AppRPPG __init__ - Mulai")
        self.title("VitalCam - Real-Time Monitoring")

        if not PILLOW_GUI_AVAILABLE:
            self.withdraw()
            messagebox.showerror("Kesalahan Dependensi", "Library Pillow (PIL) tidak terinstal!")
            self.destroy()
            return
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showwarning("Kesalahan Dependensi", "Matplotlib tidak terinstal! Grafik tidak akan berfungsi.")

        self.geometry("1200x750")
        self.minsize(800, 600)

        self.available_cameras = []
        self.selected_camera_index = 0
        self.cap = None
        self.webcam_active = False
        self.webcam_update_job = None
        self.camera_selection_visible = False # Untuk melacak status combobox kamera

        # Inisialisasi Processor
        self.rppg_proc = None
        self.resp_proc = None
        if PROCESSORS_AVAILABLE:
            try:
                self.rppg_proc = RPPGProcessor(fps=30)
                # Berikan fps yang sama ke RespirasiProcessor jika ia menerimanya
                self.resp_proc = RespirasiProcessor(fps=getattr(self.rppg_proc, 'fps', 15))
                print("DEBUG: Objek RPPGProcessor dan RespirasiProcessor berhasil dibuat.")
            except Exception as e:
                messagebox.showerror("Error Processor", f"Gagal membuat instance processor: {e}")
                print(f"ERROR saat membuat instance processor: {e}")
        else:
            messagebox.showwarning("Peringatan Processor", "Modul Processor tidak ditemukan/gagal impor.")

        # Setup untuk Plot Matplotlib (Fig, Axes, Line)
        self._setup_plots()

        self.create_widgets() # Panggil setelah semua atribut dasar diinisialisasi
        self.detect_available_cameras() # Panggil setelah combobox dibuat

        self.bind("<Configure>", self.on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing_window)
        print("DEBUG: AppRPPG __init__ - Selesai")

    def _setup_plots(self):
        """Mempersiapkan figure, axes, dan lines untuk plot Matplotlib."""
        if MATPLOTLIB_AVAILABLE:
            self.fig_rppg = Figure(figsize=(5, 2.5), dpi=100)
            self.ax_rppg = self.fig_rppg.add_subplot(111)
            self.ax_rppg.set_title("Sinyal rPPG", fontsize=10)
            self.ax_rppg.set_xlabel("Sampel", fontsize=8)
            self.ax_rppg.set_ylabel("Intensitas", fontsize=8)
            self.line_rppg, = self.ax_rppg.plot([], [], 'r-') # Merah
            self.fig_rppg.tight_layout()

            self.fig_resp = Figure(figsize=(5, 2.5), dpi=100)
            self.ax_resp = self.fig_resp.add_subplot(111)
            self.ax_resp.set_title("Sinyal Respirasi", fontsize=10)
            self.ax_resp.set_xlabel("Sampel", fontsize=8)
            self.ax_resp.set_ylabel("Pergerakan", fontsize=8)
            self.line_resp, = self.ax_resp.plot([], [], 'g-') # Hijau
            self.fig_resp.tight_layout()
        else:
            self.fig_rppg = self.ax_rppg = self.line_rppg = None
            self.fig_resp = self.ax_resp = self.line_resp = None
        print("DEBUG: Setup plot Matplotlib selesai.")


    def detect_available_cameras(self):
        self.available_cameras = []
        index = 0
        print("DEBUG: Mendeteksi kamera yang tersedia...")
        while True:
            cap_test = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap_test.isOpened():
                cap_test.release(); break
            else:
                self.available_cameras.append({"id": index, "name": f"Kamera {index}"})
            cap_test.release()
            index += 1
            if index > 3: print("DEBUG: Pencarian kamera dibatasi hingga indeks 3."); break
        
        if not self.available_cameras:
            print("PERINGATAN: Tidak ada kamera yang terdeteksi.")
        else:
            print(f"DEBUG: Kamera terdeteksi: {self.available_cameras}")
            if hasattr(self, 'camera_combobox'): # Pastikan combobox sudah dibuat
                self.camera_combobox['values'] = [cam['name'] for cam in self.available_cameras]
                if self.available_cameras:
                    self.camera_combobox.current(0)
                    self.selected_camera_index = self.available_cameras[0]['id']

    def create_widgets(self):
        print("DEBUG: AppRPPG create_widgets - Mulai")
        # 1. Header Frame
        header_frame = tk.Frame(self, bg="#1A2F5A", height=50); header_frame.pack(fill=tk.X, side=tk.TOP); header_frame.pack_propagate(False)
        lbl_header_title = tk.Label(header_frame, text="Sinyal Respirasi dan rPPG Real-Time", fg="white", bg="#1A2F5A", font=("Arial", 16, "bold")); lbl_header_title.pack(pady=10)

        # --- Tombol Kontrol Kamera Global ---
        global_control_frame = tk.Frame(self, pady=5); global_control_frame.pack(fill=tk.X, side=tk.TOP)
        self.btn_start_webcam = ttk.Button(global_control_frame, text="Mulai Kamera", command=self.start_webcam_feed); self.btn_start_webcam.pack(side=tk.LEFT, padx=10)
        self.btn_stop_webcam = ttk.Button(global_control_frame, text="Stop Kamera", command=self.stop_webcam_feed, state=tk.DISABLED); self.btn_stop_webcam.pack(side=tk.LEFT, padx=5)

        # 2. Main Content Frame
        main_content_frame = tk.Frame(self, bg="white"); main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        main_content_frame.columnconfigure(0, weight=1, minsize=300, uniform="app_cols")
        main_content_frame.columnconfigure(1, weight=1, minsize=300, uniform="app_cols")
        main_content_frame.rowconfigure(0, weight=2, minsize=250, uniform="app_rows") 
        main_content_frame.rowconfigure(1, weight=1, minsize=200, uniform="app_rows") 

        left_column_frame = ttk.Frame(main_content_frame); left_column_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        left_column_frame.rowconfigure(0, weight=1); left_column_frame.rowconfigure(1, weight=1); left_column_frame.columnconfigure(0, weight=1)

        rppg_plot_area = ttk.LabelFrame(left_column_frame, text=" Monitor sinyal rPPG "); rppg_plot_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0,5))
        if MATPLOTLIB_AVAILABLE and self.fig_rppg:
            self.canvas_rppg = FigureCanvasTkAgg(self.fig_rppg, master=rppg_plot_area)
            self.canvas_rppg.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            self.canvas_rppg.draw()
            print("DEBUG: Canvas rPPG dibuat.")
        else:
            tk.Label(rppg_plot_area, text="Grafik rPPG (Matplotlib error)", bg="lightgrey").pack(fill=tk.BOTH, expand=True)

        resp_plot_area = ttk.LabelFrame(left_column_frame, text=" Monitor sinyal Respirator "); resp_plot_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5,0))
        if MATPLOTLIB_AVAILABLE and self.fig_resp:
            self.canvas_resp = FigureCanvasTkAgg(self.fig_resp, master=resp_plot_area)
            self.canvas_resp.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            self.canvas_resp.draw()
            print("DEBUG: Canvas Respirasi dibuat.")
        else:
            tk.Label(resp_plot_area, text="Grafik Respirasi (Matplotlib error)", bg="lightgrey").pack(fill=tk.BOTH, expand=True)

        right_column_frame = ttk.Frame(main_content_frame); right_column_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 0))
        right_column_frame.rowconfigure(0, weight=3); right_column_frame.rowconfigure(1, weight=1, minsize=120); right_column_frame.columnconfigure(0, weight=1)
        
        webcam_frame_container = ttk.LabelFrame(right_column_frame, text=" Webcam Realtime "); webcam_frame_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0,5))
        self.webcam_label = tk.Label(webcam_frame_container, bg="black"); self.webcam_label.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.camera_control_frame = tk.Frame(webcam_frame_container) ; self.camera_control_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
        # Pastikan self.toggle_camera_selection adalah method dari self (AppRPPG)
        self.btn_select_camera = ttk.Button(self.camera_control_frame, text="📷", width=3, command=self.toggle_camera_selection)
        self.btn_select_camera.pack(side=tk.LEFT)
        self.camera_var = tk.StringVar(); self.camera_combobox = ttk.Combobox(self.camera_control_frame, textvariable=self.camera_var, state="readonly", width=15); self.camera_combobox.bind("<<ComboboxSelected>>", self.on_camera_selected)

        numeric_data_area = ttk.LabelFrame(right_column_frame, text=" Data Terukur "); numeric_data_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5,0)); numeric_data_area.columnconfigure(0, weight=1); numeric_data_area.columnconfigure(1, weight=1); numeric_data_area.rowconfigure(0, weight=1); numeric_data_area.rowconfigure(1, weight=2)
        lbl_rr_title = tk.Label(numeric_data_area, text="RR", font=("Arial", 12, "bold"), fg="green"); lbl_rr_title.grid(row=0, column=0, sticky="s", pady=(5,0))
        self.lbl_rr_value = tk.Label(numeric_data_area, text="--", font=("Arial", 36, "bold"), fg="green"); self.lbl_rr_value.grid(row=1, column=0, sticky="n", pady=(0,5))
        lbl_rr_unit = tk.Label(numeric_data_area, text="rpm", font=("Arial", 10), fg="green"); lbl_rr_unit.grid(row=1, column=0, sticky="s", padx=(50,0), pady=(0,5))
        lbl_hr_title = tk.Label(numeric_data_area, text="rPPG", font=("Arial", 12, "bold"), fg="red"); lbl_hr_title.grid(row=0, column=1, sticky="s", pady=(5,0))
        self.lbl_hr_value = tk.Label(numeric_data_area, text="--", font=("Arial", 36, "bold"), fg="red"); self.lbl_hr_value.grid(row=1, column=1, sticky="n", pady=(0,5))
        lbl_hr_unit = tk.Label(numeric_data_area, text="bpm", font=("Arial", 10), fg="red"); lbl_hr_unit.grid(row=1, column=1, sticky="s", padx=(50,0), pady=(0,5))
        print("DEBUG: AppRPPG create_widgets - Selesai")

    def toggle_camera_selection(self):
        print("DEBUG: Tombol pilih kamera diklik.")
        if self.camera_selection_visible: # Gunakan flag status
            self.camera_combobox.pack_forget()
            self.camera_selection_visible = False
            print("DEBUG: Camera combobox disembunyikan.")
        else:
            if self.available_cameras:
                self.camera_combobox['values'] = [cam['name'] for cam in self.available_cameras]
                try:
                    current_cam_name = next(c['name'] for c in self.available_cameras if c['id'] == self.selected_camera_index)
                    self.camera_combobox.set(current_cam_name)
                except StopIteration:
                     if self.available_cameras: self.camera_combobox.current(0)
                self.camera_combobox.pack(side=tk.LEFT, padx=(5,0))
                self.camera_selection_visible = True
                print("DEBUG: Camera combobox ditampilkan.")
            else:
                messagebox.showinfo("Info Kamera", "Tidak ada kamera terdeteksi.")

    def on_camera_selected(self, event):
        selected_name = self.camera_var.get()
        print(f"DEBUG: Kamera dipilih: {selected_name}")
        new_cam_index = -1
        try:
            new_cam_index = next(cam['id'] for cam in self.available_cameras if cam['name'] == selected_name)
        except StopIteration:
            print(f"ERROR: Kamera dengan nama {selected_name} tidak ditemukan."); return

        if new_cam_index != self.selected_camera_index:
            print(f"DEBUG: Indeks kamera diubah ke: {new_cam_index}")
            self.selected_camera_index = new_cam_index
            if self.webcam_active:
                self.stop_webcam_feed(); self.start_webcam_feed()
        
        if self.camera_selection_visible : # Sembunyikan setelah dipilih
            self.camera_combobox.pack_forget()
            self.camera_selection_visible = False

    def start_webcam_feed(self):
        if self.webcam_active: print("DEBUG: Webcam sudah aktif."); return
        print(f"DEBUG: Mencoba webcam indeks: {self.selected_camera_index}")
        self.cap = cv2.VideoCapture(self.selected_camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            messagebox.showerror("Error Kamera", f"Tidak bisa buka kamera {self.selected_camera_index}."); self.cap = None; return
        self.webcam_active = True
        self.btn_start_webcam.config(state=tk.DISABLED); self.btn_stop_webcam.config(state=tk.NORMAL)
        self.btn_select_camera.config(state=tk.DISABLED)
        if self.camera_selection_visible: self.camera_combobox.pack_forget(); self.camera_selection_visible = False
        print("DEBUG: Webcam feed dimulai."); self._update_frame()

    def stop_webcam_feed(self):
        if not self.webcam_active: print("DEBUG: Webcam sudah tidak aktif."); return
        self.webcam_active = False
        if self.webcam_update_job: self.after_cancel(self.webcam_update_job); self.webcam_update_job = None
        if self.cap: self.cap.release(); self.cap = None
        self.btn_start_webcam.config(state=tk.NORMAL); self.btn_stop_webcam.config(state=tk.DISABLED)
        self.btn_select_camera.config(state=tk.NORMAL)
        if MATPLOTLIB_AVAILABLE: # Kosongkan plot
            if hasattr(self, 'line_rppg'): self._update_rppg_plot([])
            if hasattr(self, 'line_resp'): self._update_resp_plot([])
        self.lbl_hr_value.config(text="--"); self.lbl_rr_value.config(text="--")
        print("DEBUG: Webcam feed dihentikan.")

    def _update_frame(self):
        if not self.webcam_active or not self.cap or not self.cap.isOpened():
            self.stop_webcam_feed(); return
        ret, frame = self.cap.read()
        if ret:
            frame_asli = frame.copy()
            frame_tampil = frame.copy()
            
            if self.rppg_proc:
                try:
                    self.rppg_proc.extract_rgb_from_frame(frame_asli)
                    forehead_rect = self.rppg_proc.get_forehead_rect()
                    if forehead_rect: cv2.rectangle(frame_tampil, forehead_rect[:2], forehead_rect[2:], (0,255,0), 2)
                except Exception as e: print(f"ERROR rppg_proc.extract/get_rect: {e}")
            if self.resp_proc:
                try:
                    self.resp_proc.extract_resp_from_frame(frame_asli)
                    shoulder_points_list = self.resp_proc.get_shoulder_points()
                    if shoulder_points_list and len(shoulder_points_list) > 0:
                        last_shoulders = shoulder_points_list[-1]
                        if last_shoulders[0]!=(0,0): cv2.circle(frame_tampil, last_shoulders[0], 5, (0,255,0), -1)
                        if last_shoulders[1]!=(0,0): cv2.circle(frame_tampil, last_shoulders[1], 5, (0,255,0), -1)
                except Exception as e: print(f"ERROR resp_proc.extract/get_points: {e}")
            
            display_frame_rgb = cv2.cvtColor(frame_tampil, cv2.COLOR_BGR2RGB)
            target_w = self.webcam_label.winfo_width(); target_h = self.webcam_label.winfo_height()
            if target_w > 1 and target_h > 1 :
                h_ori, w_ori = display_frame_rgb.shape[:2]
                if w_ori > 0 and h_ori > 0 :
                    ratio_ori = w_ori / h_ori; ratio_target = target_w / target_h
                    if ratio_ori > ratio_target: new_w = target_w; new_h = int(target_w / ratio_ori) if ratio_ori != 0 else target_h
                    else: new_h = target_h; new_w = int(target_h * ratio_ori) if ratio_target != 0 else target_w
                    if new_w > 0 and new_h > 0: resized_frame = cv2.resize(display_frame_rgb, (new_w, new_h))
                    else: resized_frame = display_frame_rgb
                    img = Image.fromarray(resized_frame)
                else: img = Image.fromarray(display_frame_rgb)
            else: img = Image.fromarray(display_frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.webcam_label.configure(image=imgtk); self.webcam_label.image = imgtk

            if MATPLOTLIB_AVAILABLE:
                if self.rppg_proc:
                    try:
                        rppg_plot_data = self.rppg_proc.get_latest_signal_chunk()
                        if rppg_plot_data is not None and len(rppg_plot_data) > 1: self._update_rppg_plot(rppg_plot_data)
                        current_hr = self.rppg_proc.get_current_hr(fs=getattr(self.rppg_proc, 'fps', 30))
                        print(f"DEBUG GUI: get_current_hr() mengembalikan: {current_hr} (tipe: {type(current_hr)})")
                        self.lbl_hr_value.config(text=f"{current_hr:.0f}" if current_hr is not None else "--")
                    except AttributeError as ae: print(f"Missing method rPPG: {ae}")
                    except Exception as e: print(f"Error update rPPG: {e}")
                if self.resp_proc:
                    try:
                        resp_plot_data = self.resp_proc.get_latest_signal_chunk()
                        if resp_plot_data is not None and len(resp_plot_data) > 1: self._update_resp_plot(resp_plot_data)
                        video_fps = getattr(self.rppg_proc, 'fps', getattr(self.resp_proc, 'fps', 30))
                        current_rr = self.resp_proc.get_current_rr(fs=video_fps)
                        print(f"DEBUG GUI: get_current_rr() mengembalikan: {current_rr} (tipe: {type(current_rr)})")

                        self.lbl_rr_value.config(text=f"{current_rr:.0f}" if current_rr is not None else "--")
                    except AttributeError as ae: print(f"Missing method Resp: {ae}")
                    except Exception as e: print(f"Error update Resp: {e}")
        if self.webcam_active:
            self.webcam_update_job = self.after(30, self._update_frame)

    def _update_rppg_plot(self, data):
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'line_rppg') or self.line_rppg is None: return
        try:
            self.line_rppg.set_ydata(data); self.line_rppg.set_xdata(np.arange(len(data)))
            self.ax_rppg.relim(); self.ax_rppg.autoscale_view(True,True,True)
            self.canvas_rppg.draw_idle()
        except Exception as e: print(f"Error update RPPG plot: {e}")

    def _update_resp_plot(self, data):
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'line_resp') or self.line_resp is None: return
        try:
            self.line_resp.set_ydata(data); self.line_resp.set_xdata(np.arange(len(data)))
            self.ax_resp.relim(); self.ax_resp.autoscale_view(True,True,True)
            self.canvas_resp.draw_idle()
        except Exception as e: print(f"Error update Resp plot: {e}")

    def on_window_resize(self, event):
        print(f"DEBUG: AppRPPG window resized to {self.winfo_width()}x{self.winfo_height()}")

    def on_closing_window(self):
        print("DEBUG: Jendela AppRPPG ditutup.")
        if self.webcam_active: self.stop_webcam_feed()
        self.destroy()

if __name__ == "__main__":
    if not PILLOW_GUI_AVAILABLE:
        root_err = tk.Tk(); root_err.withdraw(); messagebox.showerror("Pillow Missing", "Pillow tidak terinstal!"); root_err.destroy(); exit()
    
    print("DEBUG: Menjalankan AppRPPG sbg main...")
    app = AppRPPG()
    if hasattr(app, 'winfo_exists') and app.winfo_exists():
        app.mainloop()
    print("DEBUG: AppRPPG mainloop selesai.")