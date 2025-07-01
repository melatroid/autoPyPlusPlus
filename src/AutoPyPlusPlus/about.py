import os
import tkinter as tk
from tkinter import ttk

def show_about_dialog(master, style, theme_func):
    # Setze Arbeitsverzeichnis auf Skriptordner
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    about_win = tk.Toplevel(master)
    about_win.title("About AutoPy++")
    about_win.geometry("250x420")
    about_win.resizable(False, False)
    about_win.transient(master)
    about_win.grab_set()

    theme_func(style, about_win)

    try:
        about_img = tk.PhotoImage(file="about.png")
    except Exception as e:
        about_img = None
        print("Fehler beim Laden von about.png:", e)

    if about_img:
        img_label = ttk.Label(about_win, image=about_img)
        img_label.image = about_img
        img_label.pack(pady=(5,5))

    text = (
        "AutoPy++\n"
        "Version 2.25 (Stand: 26.06.2025)\n"
        "Developer.: melatroid\n"
        "© 2025 by melatroid\n"
        "Bugs & Reports: dseccg@gmail.com\n"
        "www.autopyplusplus.wordpress.com\n\n"
        "Lizenz: MIT License\n\n"
        "Spend me a Coffee 😊☕ \n"      
        "PayPal: melatroid@gmail.com\n"
        "Software is much work, respect it\n"
    )

    label = ttk.Label(about_win, text=text, justify="center", font=("Segoe UI", 10))
    label.pack(expand=True, fill="both", padx=5, pady=10)

    ok_button = ttk.Button(about_win, text="OK", command=about_win.destroy)
    ok_button.pack(pady=5)

    about_win.update_idletasks()
    x = (master.winfo_width() // 2) - (about_win.winfo_width() // 2) + master.winfo_x()
    y = (master.winfo_height() // 2) - (about_win.winfo_height() // 2) + master.winfo_y()
    about_win.geometry(f"+{x}+{y}")
