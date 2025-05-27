# main_dashboard.py

import tkinter as tk
from tkinter import messagebox
import sys
import traceback

try:
    from landing_page import LandingPage
    LANDING_PAGE_MODULE_AVAILABLE = True
except Exception as e:
    LANDING_PAGE_MODULE_AVAILABLE = False
    landing_page_import_error = e

def main():
    if LANDING_PAGE_MODULE_AVAILABLE:
        try:
            app = LandingPage()
            if hasattr(app, 'winfo_exists') and app.winfo_exists():
                app.mainloop()
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            traceback.print_exc()
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Aplikasi Error", f"Kesalahan saat menjalankan aplikasi.\n\n{e}")
                root.destroy()
            except:
                pass
    else:
        print(f"ERROR: Tidak dapat memuat LandingPage: {landing_page_import_error}", file=sys.stderr)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Aplikasi Error", f"Gagal memuat landing_page.py.\n\n{landing_page_import_error}")
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()
