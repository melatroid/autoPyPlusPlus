import os
import tkinter as tk
from tkinter import ttk

def show_about_dialog(master, style, theme_func):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    about_win = tk.Toplevel(master)
    about_win.title("About AutoPy++")
    about_win.geometry("250x570")
    about_win.resizable(False, False)
    about_win.transient(master)
    about_win.grab_set()
    about_win.protocol("WM_DELETE_WINDOW", lambda: None)

    # --- Fenster-Icon (.ico) ---
    try:
        about_win.iconbitmap('autoPy++.ico')
    except Exception:
        pass

    theme_func(style, about_win)

    # --- Main frame using grid to center all items ---
    main_frame = ttk.Frame(about_win)
    main_frame.pack(expand=True, fill="both", padx=10, pady=10)

    # Centering config
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure("all", weight=1)

    row = 0

    # --- ICO im Fenster mit fester Größe ---
    try:
        from PIL import Image, ImageTk
        ico_img = Image.open("autoPy++.ico").resize((64, 64), Image.LANCZOS)
        ico_photo = ImageTk.PhotoImage(ico_img)
        ico_label = ttk.Label(main_frame, image=ico_photo)
        ico_label.image = ico_photo
        ico_label.grid(row=row, column=0, pady=(4, 8), padx=(65, 0), sticky="w")
        row += 1
    except Exception as e:
        print("ICO konnte nicht geladen werden:", e)

    # --- about.png darunter ---
    try:
        about_img = tk.PhotoImage(file="about.png")
        img_label = ttk.Label(main_frame, image=about_img)
        img_label.image = about_img
        img_label.grid(row=row, column=0, pady=(4, 8))
        row += 1
    except Exception as e:
        print("about.png konnte nicht geladen werden:", e)

    # --- Text ---
    text = (
        "Version 2.38b (Date: 14.08.2025)\n"
        "Developer: melatroid\n"
        "© 2025 by melatroid\n"
        "Bug reports: dseccg@gmail.com\n"
        "www.autopyplusplus.wordpress.com\n\n"
        "License: MIT License\n\n"
        "Buy me a coffee 😊☕\n"
        "Software is a lot of work\n please respect it.\n"
    )
    label = ttk.Label(main_frame, text=text, justify="center", font=("Segoe UI", 10))
    label.grid(row=row, column=0, pady=8)
    row += 1

    # --- PayPal ---
    paypal_label = ttk.Label(main_frame, text="PayPal Address:", font=("Segoe UI", 10, "bold"))
    paypal_label.grid(row=row, column=0, pady=(5, 2))
    row += 1

    paypal_entry = ttk.Entry(main_frame, font=("Segoe UI", 10), justify="center", width=25)
    paypal_entry.insert(0, "melatroid@gmail.com")
    paypal_entry.config(state="readonly")
    paypal_entry.grid(row=row, column=0, pady=(0, 4))
    row += 1

    def copy_to_clipboard():
        about_win.clipboard_clear()
        about_win.clipboard_append(paypal_entry.get())
        about_win.update()
        countdown_var.set("Address copied! 😊")

    copy_button = ttk.Button(main_frame, text="📋 Copy to Clipboard", command=copy_to_clipboard)
    copy_button.grid(row=row, column=0, pady=(0, 10))
    row += 1

    # --- Countdown ---
    countdown_var = tk.StringVar(value="This window will close in 5 seconds …")
    countdown_label = ttk.Label(
        main_frame,
        textvariable=countdown_var,
        font=("Segoe UI", 10, "bold"),
        foreground="#4444dd"
    )
    countdown_label.grid(row=row, column=0, pady=(0, 8))
    row += 1

    # --- Fenster zentrieren ---
    about_win.update_idletasks()
    x = (master.winfo_screenwidth() // 2) - (about_win.winfo_reqwidth() // 2)
    y = (master.winfo_screenheight() // 2) - (about_win.winfo_reqheight() // 2)
    about_win.geometry(f"+{x}+{y}")

    # --- Countdown-Logik ---
    def update_countdown(remaining):
        if remaining > 0:
            if not countdown_var.get().startswith("Address copied"):
                countdown_var.set(
                    f"Closing in {remaining} second{'s' if remaining != 1 else ''} …"
                )
            about_win.after(1000, update_countdown, remaining - 1)
        else:
            countdown_var.set("Enjoy!")
            about_win.after(350, about_win.destroy)

    update_countdown(5)

