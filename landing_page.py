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

class LandingPage(tk.Tk):
    def __init__(self):
        super().__init__()
        print("DEBUG: LandingPage __init__ - Mulai")
        self.title("VitalCam - Selamat Datang!")

        self.guide_window_instance = None
        self.credit_window_instance = None

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

        self.title_font = tkFont.Font(family="Montserrat", size=32, weight="bold")
        self.subtitle_font = tkFont.Font(family="Montserrat", size=20, weight="bold")
        self.welcome_font = tkFont.Font(family="Montserrat", size=18, weight="bold")
        self.text_fg_color = "white"

        self.load_assets()
        self.setup_ui_elements()

        self.bind("<Configure>", self.on_resize_event)
        self.after(100, lambda: self.on_resize_event(None))
        print("DEBUG: LandingPage __init__ - Selesai")

    def load_assets(self):
        print("DEBUG: Memuat aset gambar mentah...")
        if not PILLOW_AVAILABLE: return

        self.raw_bg_image = self._load_pil_image("bg_lp.png")
        self.raw_button_images = {}
        self.bg_image_tk_resized = None
        self.button_image_tks = {}
        self.raw_button_images["start"] = self._load_pil_image("start.png")
        self.raw_button_images["guide"] = self._load_pil_image("guide.png")
        self.raw_button_images["credit"] = self._load_pil_image("credit.png")

        self.button_canvas_item_ids = {"start": None, "guide": None, "credit": None}
        self.button_clickable_areas = {"start": None, "guide": None, "credit": None}

        if self.raw_bg_image is None:
             messagebox.showwarning("Aset Kritis Hilang", "Gagal memuat gambar latar (bg_lp.png).")
             self.raw_bg_image = Image.new('RGB', (self.initial_width, self.initial_height), (74, 63, 107))

    def show_guide_window(self): 
        print("DEBUG: Tombol Guide diklik dari method!")
        if self.guide_window_instance is not None and self.guide_window_instance.winfo_exists():
            self.guide_window_instance.lift()
            self.guide_window_instance.focus_force()
            print("DEBUG: Jendela guide sudah ada, dibawa ke depan.")
            return

        self.guide_window_instance = tk.Toplevel(self) 
        self.guide_window_instance.title("Panduan - VitalCam")

        guide_width = 800  
        guide_height = 600

        parent_x = self.winfo_x(); parent_y = self.winfo_y()
        parent_w = self.winfo_width(); parent_h = self.winfo_height()
        pos_x = parent_x + (parent_w // 2) - (guide_width // 2)
        pos_y = parent_y + (parent_h // 2) - (guide_height // 2)
        self.guide_window_instance.geometry(f"{guide_width}x{guide_height}+{pos_x}+{pos_y}")

        self.guide_window_instance.resizable(True, True) 
        self.guide_window_instance.minsize(400, 300)  

        #Header frame untuk judul panduan
        guide_header_frame = tk.Frame(self.guide_window_instance, bg="#1E3A8A", height=40)
        guide_header_frame.pack(fill=tk.X, side=tk.TOP)
        guide_header_frame.pack_propagate(False)
        lbl_guide_header = tk.Label(guide_header_frame, text="Guide", font=("Arial", 14, "bold"), fg="white", bg="#1E3A8A")
        lbl_guide_header.pack(pady=5)

        guide_content_canvas = tk.Canvas(self.guide_window_instance, borderwidth=0, highlightthickness=0)
        guide_content_canvas.pack(fill=tk.BOTH, expand=True)
        self.guide_window_instance.guide_content_bg_raw_pil = self._load_pil_image("bg_guide_content.png") 
        self.guide_window_instance.guide_content_bg_tk_ref = None

        def _resize_and_draw_guide_bg(event=None):
            if self.guide_window_instance.guide_content_bg_raw_pil and PILLOW_AVAILABLE: # Akses via self.guide_window_instance
                canvas_w = guide_content_canvas.winfo_width()
                canvas_h = guide_content_canvas.winfo_height()
                if canvas_w > 1 and canvas_h > 1:
                    img_w, img_h = self.guide_window_instance.guide_content_bg_raw_pil.size
                    scale = max(canvas_w / img_w if img_w > 0 else 1, canvas_h / img_h if img_h > 0 else 1)
                    new_w, new_h = int(img_w * scale), int(img_h * scale)
                    resized_img = self.guide_window_instance.guide_content_bg_raw_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    x_crop = max(0, (new_w - canvas_w) / 2)
                    y_crop = max(0, (new_h - canvas_h) / 2)
                    cropped_img = resized_img.crop((x_crop, y_crop, x_crop + canvas_w, y_crop + canvas_h))

                    self.guide_window_instance.guide_content_bg_tk_ref = ImageTk.PhotoImage(cropped_img) 
                    guide_content_canvas.delete("guide_bg")
                    guide_content_canvas.create_image(0, 0, anchor=tk.NW, image=self.guide_window_instance.guide_content_bg_tk_ref, tags="guide_bg")
                    guide_content_canvas.lower("guide_bg") 
            else: 
                guide_content_canvas.config(bg="white") 

        guide_content_canvas.bind("<Configure>", _resize_and_draw_guide_bg)
        self.guide_window_instance.after(50, _resize_and_draw_guide_bg) 

        btn_close_guide = tk.Button(self.guide_window_instance, text="Tutup", 
                                     command=lambda: self._close_sub_window("guide"))
        btn_close_guide.pack(pady=10, side=tk.BOTTOM)

        self.guide_window_instance.protocol("WM_DELETE_WINDOW", lambda: self._close_sub_window("guide"))
        self.guide_window_instance.transient(self)
        self.guide_window_instance.grab_set()

    def show_credits_window(self): 
        print("DEBUG: Tombol Credit diklik dari method!")
        if self.credit_window_instance is not None and self.credit_window_instance.winfo_exists():
            self.credit_window_instance.lift()
            self.credit_window_instance.focus_force()
            print("DEBUG: Jendela kredit sudah ada, dibawa ke depan.")
            return

        self.credit_window_instance = tk.Toplevel(self)
        self.credit_window_instance.title("Credit - VitalCam")

        credit_width = 600; credit_height = 400 
        parent_x = self.winfo_x(); parent_y = self.winfo_y()
        parent_w = self.winfo_width(); parent_h = self.winfo_height()
        pos_x = parent_x + (parent_w // 2) - (credit_width // 2)
        pos_y = parent_y + (parent_h // 2) - (credit_height // 2)
        self.credit_window_instance.geometry(f"{credit_width}x{credit_height}+{pos_x}+{pos_y}")
        self.credit_window_instance.resizable(False, False)
        self.credit_window_instance.configure(bg="#1E3A8A")

        main_credit_frame = tk.Frame(self.credit_window_instance, bg=self.credit_window_instance.cget('bg'), padx=20, pady=20)
        main_credit_frame.pack(expand=True, fill=tk.BOTH)

        lbl_credit_title_top = tk.Label(main_credit_frame, text="Credit v", font=("Arial", 10, "italic"), fg="lightgrey", bg=self.credit_window_instance.cget('bg'))
        lbl_credit_title_top.pack(anchor="ne", pady=(0, 10)) 

        credits_data = [
            ("Presented by:", "", ("Montserrat", 16, "bold", "underline")), 
            ("1. Cindy Nadila Putri", "- 122140002", ("Consolas", 14)), 
            ("2. M. Arief Rahman Hakim", "- 122140083", ("Consolas", 14)),
            ("3. Zidan Raihan", "- 122140100", ("Consolas", 14))
        ]
        names_frame = tk.Frame(main_credit_frame, bg=self.credit_window_instance.cget('bg'))
        names_frame.pack(expand=True) 
        for nama, nim, font_config in credits_data:
            row_frame = tk.Frame(names_frame, bg=self.credit_window_instance.cget('bg'))
            row_frame.pack(fill=tk.X, pady=2)
            font_tuple = font_config if isinstance(font_config, tuple) else ("Montserrat", 14)
            if "Presented by" in nama:
                lbl_name = tk.Label(row_frame, text=nama, font=font_tuple, fg="white", bg=self.credit_window_instance.cget('bg'), anchor="center", justify=tk.CENTER)
                lbl_name.pack(fill=tk.X, expand=True)
            else:
                lbl_name = tk.Label(row_frame, text=nama, font=font_tuple, fg="white", bg=self.credit_window_instance.cget('bg'), width=30, anchor="w", justify=tk.LEFT)
                lbl_name.pack(side=tk.LEFT, padx=(0,10))
                lbl_nim = tk.Label(row_frame, text=nim, font=font_tuple, fg="white", bg=self.credit_window_instance.cget('bg'), anchor="w", justify=tk.LEFT)
                lbl_nim.pack(side=tk.LEFT)

        btn_close_credit = tk.Button(main_credit_frame, text="Tutup", command=lambda: self._close_sub_window("credit")) 
        btn_close_credit.pack(pady=(20,0))

        self.credit_window_instance.protocol("WM_DELETE_WINDOW", lambda: self._close_sub_window("credit"))
        self.credit_window_instance.transient(self)
        self.credit_window_instance.grab_set()

    def on_canvas_click(self, event):
        print(f"DEBUG: Canvas diklik pada ({event.x}, {event.y})")
        for key, rect in self.button_clickable_areas.items():
            if rect and rect[0] <= event.x <= rect[2] and rect[1] <= event.y <= rect[3]:
                print(f"DEBUG: Klik terdeteksi di area tombol '{key}'")
                if key == "start":
                    self.launch_main_application()
                elif key == "guide":
                    self.show_guide_window()
                elif key == "credit":
                    self.show_credits_window()
                return
        print("DEBUG: Klik di canvas, tapi bukan di area tombol.")
    
    def _close_sub_window(self, window_type):
        if window_type == "guide":
            if self.guide_window_instance and self.guide_window_instance.winfo_exists():
                self.guide_window_instance.destroy()
            self.guide_window_instance = None
            print("DEBUG: Jendela guide ditutup.")
        elif window_type == "credit": # TAMBAHKAN ATAU PASTIKAN INI ADA
            if self.credit_window_instance and self.credit_window_instance.winfo_exists():
                self.credit_window_instance.destroy()
            self.credit_window_instance = None
            print("DEBUG: Jendela credit ditutup.")

    def on_canvas_motion(self, event):
        on_button_area = False
        for key, rect in self.button_clickable_areas.items():
            if rect and rect[0] <= event.x <= rect[2] and rect[1] <= event.y <= rect[3]:
                on_button_area = True
                break
        
        if on_button_area:
            self.bg_canvas.config(cursor="hand2")
        else:
            self.bg_canvas.config(cursor="")

    def _load_pil_image(self, filename):
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

        self.bg_canvas.bind("<Button-1>", self.on_canvas_click)
        self.bg_canvas.bind("<Motion>", self.on_canvas_motion)

        print("DEBUG: Event binding untuk klik dan motion di canvas ditambahkan.")
        print("DEBUG: LandingPage setup_ui_elements - Selesai (tanpa membuat tk.Button untuk tombol utama)")

    def launch_main_application(self):
        print("DEBUG: Tombol START diklik! Meluncurkan aplikasi utama...")
        if GUI_APP_AVAILABLE and AppRPPG: # Pastikan AppRPPG berhasil diimpor
            print("DEBUG: Menutup LandingPage...")
            self.destroy() # Menutup jendela landing page

            print("DEBUG: Membuat instance AppRPPG...")
            main_app = AppRPPG() # Membuat instance aplikasi utama
            print("DEBUG: Menjalankan main_app.mainloop()... (jika AppRPPG adalah tk.Tk)")
            main_app.mainloop() # Jalankan mainloop dari aplikasi utama
        else:
            messagebox.showerror("Kesalahan Aplikasi",
                                 "Tidak bisa memuat modul aplikasi utama (gui_app.py).\n"
                                 "Pastikan file tersebut ada dan tidak ada error impor.")

    def on_resize_event(self, event):
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
            
            self.bg_canvas.delete("canvas_button_tag") 
            self.button_clickable_areas = {} 

            target_btn_width_ratio = 0.22 
            target_btn_height_ratio = 0.07 

            # Hitung ukuran target berdasarkan ukuran window saat ini
            btn_w = int(current_width * target_btn_width_ratio)
            btn_h = int(current_height * target_btn_height_ratio)
            
            # Batasan ukuran tombol dalam piksel absolut
            min_w_px = 100
            max_w_px = 292  
            min_h_px = 40   
            max_h_px = 70   

            btn_w = max(min_w_px, min(btn_w, max_w_px))
            btn_h = max(min_h_px, min(btn_h, max_h_px))

            current_rely_btn = rely_welcome + (120 / current_height if current_height > 0 else 0.15)
            button_rely_spacing_abs_factor = 25 / self.initial_height

            buttons_to_draw_on_canvas = [
                ("start", self.raw_button_images.get("start")),
                ("guide", self.raw_button_images.get("guide")),
                ("credit", self.raw_button_images.get("credit"))
            ]

            y_pos_btn_canvas = current_height * current_rely_btn

            for key, raw_img in buttons_to_draw_on_canvas:
                if raw_img and PILLOW_AVAILABLE:
                    aspect_ratio = raw_img.width / raw_img.height
                    resized_width = int(btn_h * aspect_ratio)
                    photo_img = self._create_photo_image(raw_img, (resized_width, btn_h))

                    if photo_img:
                        self.button_image_tks[key] = photo_img 
                        
                        # Gambar di canvas
                        x_pos_canvas = current_width / 2 
                        
                        # Buat item gambar di canvas
                        item_id = self.bg_canvas.create_image(
                            x_pos_canvas, y_pos_btn_canvas, 
                            anchor=tk.CENTER, 
                            image=photo_img, 
                            tags=("canvas_button_tag", f"btn_{key}")
                        )
                        self.button_canvas_item_ids[key] = item_id
                        
                        # Simpan koordinat (bounding box) tombol untuk deteksi klik
                        x1 = x_pos_canvas - (resized_width / 2)
                        y1 = y_pos_btn_canvas - (btn_h / 2)
                        x2 = x_pos_canvas + (resized_width / 2)
                        y2 = y_pos_btn_canvas + (btn_h / 2)
                        self.button_clickable_areas[key] = (x1, y1, x2, y2)
                        
                        print(f"DEBUG: Tombol gambar '{key}' digambar di canvas pada ({x_pos_canvas:.0f}, {y_pos_btn_canvas:.0f}) ukuran {btn_w}x{btn_h}")
                    else:
                        self.bg_canvas.create_text(current_width / 2, y_pos_btn_canvas, text=key.upper() + " (IMG ERR)",
                                                   font=("Arial", 10, "bold"), fill="red", anchor=tk.CENTER, tags=("canvas_button_tag", f"btn_{key}"))
                        self.button_clickable_areas[key] = None
                        print(f"PERINGATAN DEBUG: Gagal create PhotoImage untuk tombol '{key}'")
                elif key and not raw_img:
                     self.bg_canvas.create_text(current_width / 2, y_pos_btn_canvas, text=key.upper() + " (NO IMG)",
                                                   font=("Arial", 10, "bold"), fill="orange", anchor=tk.CENTER, tags=("canvas_button_tag", f"btn_{key}"))
                     self.button_clickable_areas[key] = None
                     print(f"PERINGATAN DEBUG: Raw image untuk tombol '{key}' tidak ada.")
                
                # Increment y_pos untuk tombol berikutnya
                button_spacing_canvas_factor = 35 / self.initial_height
                y_pos_btn_canvas += btn_h + (current_height * button_spacing_canvas_factor)

            print(f"DEBUG: Tombol-tombol (sebagai gambar canvas) di-update dan diposisikan.")

        except Exception as e_resize:
            print(f"ERROR KRITIS di on_resize_event: {e_resize}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
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