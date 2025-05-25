import tkinter as tk
from tkinter import font as tkFont
from tkinter import messagebox
import os

# Coba impor Pillow di awal
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
    print("DEBUG: Pillow (Image, ImageTk) berhasil diimpor di awal.")
except ImportError:
    PILLOW_AVAILABLE = False
    print("ERROR KRITIS AWAL: Pillow (PIL) tidak terinstal.")


try:
    from gui_app import AppRPPG  # Asumsi kelas utama di gui_app.py adalah AppRPPG
    GUI_APP_AVAILABLE = True
    print("DEBUG: Kelas AppRPPG dari gui_app.py berhasil diimpor.")
except ImportError as e:
    GUI_APP_AVAILABLE = False
    print(f"ERROR DEBUG: Tidak bisa impor AppRPPG dari gui_app.py: {e}")
    # Pesan error akan ditampilkan jika tombol START diklik dan GUI_APP_AVAILABLE False

print("--- landing_page.py: Skrip Mulai Dijalankan ---")

# --- Fungsi Placeholder untuk Aksi Tombol (SEKARANG AKAN JADI METHOD) ---

def show_guide(): # Fungsi ini tetap bisa global atau jadi method
    print("DEBUG: Tombol Guide diklik!")
    messagebox.showinfo("Panduan", "Halaman panduan akan ditampilkan di sini.")

def show_credits(): # Fungsi ini tetap bisa global atau jadi method
    print("DEBUG: Tombol Credit diklik!")
    messagebox.showinfo("Kredit", "Dibuat oleh: Cindy Nadila Putri\nProyek VitalCam rPPG")

class LandingPage(tk.Tk):
    def __init__(self):
        super().__init__()
        print("DEBUG: LandingPage __init__ - Mulai")
        self.title("VitalCam - Selamat Datang!")

        if not PILLOW_AVAILABLE:
            self.withdraw()
            messagebox.showerror("Kesalahan Dependensi Kritis", "Library Pillow (PIL) tidak terinstal...")
            self.destroy()
            return

        self.initial_width = 1140
        self.initial_height = 1024
        self.geometry(f"{self.initial_width}x{self.initial_height}")
        self.resizable(True, True)
        self.minsize(700, 500)

        self.base_path = os.path.dirname(__file__)
        self.assets_path = os.path.join(self.base_path, "assets")

        self.raw_bg_image = None
        self.raw_button_images = {}
        self.bg_image_tk_resized = None
        self.button_image_tks = {}

        self.title_font = tkFont.Font(family="Arial", size=32, weight="bold")
        self.subtitle_font = tkFont.Font(family="Arial", size=20, weight="bold")
        self.welcome_font = tkFont.Font(family="Arial", size=18, weight="bold")
        self.text_fg_color = "white"

        self.load_assets()
        self.setup_ui_elements()

        self.bind("<Configure>", self.on_resize_event)
        self.after(100, lambda: self.on_resize_event(None))
        print("DEBUG: LandingPage __init__ - Selesai")

    def load_assets(self):
        # ... (kode load_assets tetap sama seperti sebelumnya) ...
        print("DEBUG: Memuat aset gambar mentah...")
        if not PILLOW_AVAILABLE: return

        self.raw_bg_image = self._load_pil_image("bg_lp.png")
        self.raw_button_images["start"] = self._load_pil_image("start.png")
        self.raw_button_images["guide"] = self._load_pil_image("guide.png")
        self.raw_button_images["credit"] = self._load_pil_image("credit.png")

        if self.raw_bg_image is None:
             messagebox.showwarning("Aset Kritis Hilang", "Gagal memuat gambar latar (bg_lp.png).")
             self.raw_bg_image = Image.new('RGB', (self.initial_width, self.initial_height), (74, 63, 107))


    def _load_pil_image(self, filename):
        # ... (kode _load_pil_image tetap sama seperti sebelumnya) ...
        try:
            path = os.path.join(self.assets_path, filename)
            img = Image.open(path)
            if img.mode != 'RGBA': img = img.convert('RGBA')
            print(f"DEBUG: Gambar mentah '{filename}' berhasil dimuat (mode: {img.mode}).")
            return img
        except FileNotFoundError:
            print(f"PERINGATAN DEBUG: File '{filename}' TIDAK DITEMUKAN di {path}")
            messagebox.showwarning("File Aset Hilang", f"File gambar '{filename}' tidak ditemukan di folder 'assets'.")
        except Exception as e:
            print(f"ERROR DEBUG saat memuat '{filename}': {e}")
            messagebox.showerror("Error Memuat Gambar", f"Gagal memuat gambar '{filename}': {e}")
        return None


    def _create_photo_image(self, pil_image, size=None):
        # ... (kode _create_photo_image tetap sama seperti sebelumnya) ...
        if not PILLOW_AVAILABLE or pil_image is None: return None
        try:
            current_image = pil_image
            if size:
                size = (max(1, int(size[0])), max(1, int(size[1])))
                if size[0] <= 0 or size[1] <= 0:
                    placeholder_pil = Image.new('RGBA', (50,20) , (255,0,0,0))
                    return ImageTk.PhotoImage(placeholder_pil)
                current_image = pil_image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(current_image)
        except Exception as e:
            print(f"Error saat membuat PhotoImage: {e}")
        return None

    def setup_ui_elements(self):
        print("DEBUG: LandingPage setup_ui_elements - Mulai")
        self.bg_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        print("DEBUG: Canvas latar belakang dibuat.")

        # PERHATIKAN PERUBAHAN `command` DI SINI untuk tombol start
        self.btn_start_widget = tk.Button(self, command=self.launch_main_application,
                                   borderwidth=0, highlightthickness=0, relief="flat", cursor="hand2")
        self.btn_guide_widget = tk.Button(self, command=show_guide, # Tetap fungsi global
                                   borderwidth=0, highlightthickness=0, relief="flat", cursor="hand2")
        self.btn_credit_widget = tk.Button(self, command=show_credits, # Tetap fungsi global
                                    borderwidth=0, highlightthickness=0, relief="flat", cursor="hand2")
        print("DEBUG: Widget tombol (untuk canvas) dibuat.")
        print("DEBUG: LandingPage setup_ui_elements - Selesai")

    def launch_main_application(self):
        print("DEBUG: Tombol START diklik! Meluncurkan aplikasi utama...")
        if GUI_APP_AVAILABLE and AppRPPG: # Pastikan AppRPPG berhasil diimpor
            print("DEBUG: Menutup LandingPage...")
            self.destroy() # Menutup jendela landing page

            print("DEBUG: Membuat instance AppRPPG...")
            main_app = AppRPPG() # Membuat instance aplikasi utama
            # diasumsikan AppRPPG adalah subclass dari tk.Tk dan akan memanggil mainloop sendiri
            # atau memiliki cara sendiri untuk memulai.
            # Jika AppRPPG juga memanggil mainloop(), ini seharusnya berjalan setelah landing page di-destroy.
            print("DEBUG: Menjalankan main_app.mainloop()... (jika AppRPPG adalah tk.Tk)")
            main_app.mainloop() # Jalankan mainloop dari aplikasi utama
        else:
            messagebox.showerror("Kesalahan Aplikasi",
                                 "Tidak bisa memuat modul aplikasi utama (gui_app.py).\n"
                                 "Pastikan file tersebut ada dan tidak ada error impor.")

    def on_resize_event(self, event):
        # ... (kode on_resize_event tetap sama seperti versi "perbaiki kode ini" terakhir) ...
        # Pastikan di dalam loop tombol, nama variabel tombolnya sesuai (self.btn_start_widget, dll.)
        try:
            current_width = self.winfo_width()
            current_height = self.winfo_height()

            if current_width < 10 or current_height < 10: return
            print(f"DEBUG: Event resize/configure ke: {current_width}x{current_height}")

            if self.raw_bg_image:
                resized_bg_pil = self._create_photo_image(self.raw_bg_image, (current_width, current_height))
                if resized_bg_pil:
                    self.bg_image_tk_resized = resized_bg_pil
                    self.bg_canvas.delete("bg_image_tag")
                    self.bg_canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image_tk_resized, tags="bg_image_tag")
                else:
                     self.bg_canvas.delete("bg_image_tag")
                     self.bg_canvas.config(bg="#4A3F6B")
            else:
                self.bg_canvas.delete("bg_image_tag")
                self.bg_canvas.config(bg="#4A3F6B")

            self.bg_canvas.delete("landing_text")
            rely_title = 0.25
            rely_subtitle = rely_title + (70 / current_height if current_height > 0 else 0.1)
            rely_welcome = rely_subtitle + (90 / current_height if current_height > 0 else 0.1)

            self.bg_canvas.create_text(current_width / 2, current_height * rely_title,
                                       text="VitalCam", font=self.title_font, fill=self.text_fg_color,
                                       anchor=tk.CENTER, tags="landing_text")
            self.bg_canvas.create_text(current_width / 2, current_height * rely_subtitle,
                                       text="Real-Time Respiratory & rPPG\nMonitoring from Webcam",
                                       font=self.subtitle_font, fill=self.text_fg_color, anchor=tk.CENTER,
                                       justify=tk.CENTER, width=current_width * 0.8, tags="landing_text")
            self.bg_canvas.create_text(current_width / 2, current_height * rely_welcome,
                                       text="WELCOME!", font=self.welcome_font, fill=self.text_fg_color,
                                       anchor=tk.CENTER, tags="landing_text")
            
            btn_w_ratio = 292 / self.initial_width
            btn_h_ratio = 100 / self.initial_height
            btn_w = int(current_width * btn_w_ratio)
            btn_h = int(current_height * btn_h_ratio)
            btn_w = max(int(self.initial_width * 0.15), min(btn_w, int(self.initial_width * 0.35)))
            btn_h = max(int(self.initial_height * 0.05), min(btn_h, int(self.initial_height * 0.12)))

            current_rely_btn = rely_welcome + (120 / current_height if current_height > 0 else 0.15)
            button_rely_spacing_abs_factor = 25 / self.initial_height

            buttons_map = { # Ganti nama variabel tombol di sini
                "start": self.btn_start_widget,
                "guide": self.btn_guide_widget,
                "credit": self.btn_credit_widget,
            }

            for key, btn_widget in buttons_map.items(): # Menggunakan btn_widget dari map
                raw_img = self.raw_button_images.get(key)
                if raw_img:
                    new_btn_img_tk = self._create_photo_image(raw_img, (btn_w, btn_h))
                    if new_btn_img_tk:
                        btn_widget.configure(image=new_btn_img_tk)
                        self.button_image_tks[key] = new_btn_img_tk
                        btn_widget.image = new_btn_img_tk
                    else:
                        btn_widget.configure(image='', text=key.upper(), font=("Arial",10))
                else:
                     btn_widget.configure(image='', text=key.upper() + " (no img)", font=("Arial",10))

                # Tempatkan tombol menggunakan create_window di canvas
                # atau jika tombol adalah child dari self (jendela utama), gunakan .place()
                # Untuk konsistensi dengan kode terakhirmu, kita asumsikan tombol adalah child dari self
                # dan di-place, lalu di-lift di atas canvas.
                btn_widget.place(relx=0.5, rely=current_rely_btn, anchor=tk.CENTER,
                                 width=btn_w, height=btn_h)
                btn_widget.lift(self.bg_canvas)
                current_rely_btn += (btn_h / current_height if current_height > 0 else 0.1) + button_rely_spacing_abs_factor
            print(f"DEBUG: Tombol di-update dan diposisikan ulang untuk ukuran {btn_w}x{btn_h}.")

        except Exception as e_resize:
            print(f"ERROR KRITIS di on_resize_event: {e_resize}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # ... (blok if __name__ == "__main__" tetap sama seperti versi terakhir) ...
    print("DEBUG: Masuk blok if __name__ == '__main__'")
    if not PILLOW_AVAILABLE:
        root_err_check = tk.Tk()
        root_err_check.withdraw()
        messagebox.showerror("Kesalahan Dependensi Kritis", "Pillow tidak terinstal...")
        root_err_check.destroy()
        exit()

    app = None
    app_created_successfully = False
    try:
        print("DEBUG: Mencoba membuat instance LandingPage...")
        app = LandingPage()
        if hasattr(app, 'winfo_exists') and app.winfo_exists():
            app_created_successfully = True
            print("DEBUG: Instance LandingPage berhasil dibuat dan jendela masih ada.")
        else:
            print("PERINGATAN DEBUG: Jendela sudah di-destroy saat __init__.")
    except Exception as e:
        print(f"ERROR KRITIS UTAMA saat instance LandingPage: {e}")
        import traceback
        traceback.print_exc()

    if app_created_successfully:
        print("DEBUG: Menjalankan app.mainloop()...")
        app.mainloop()
        print("DEBUG: app.mainloop() selesai.")
    else:
        print("DEBUG: Gagal menjalankan mainloop.")
    print("--- landing_page.py: Skrip Selesai ---")