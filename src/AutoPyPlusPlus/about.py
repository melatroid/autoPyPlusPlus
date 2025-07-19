import os
import tkinter as tk
from tkinter import ttk

def show_about_dialog(master, style, theme_func):
    # Set working directory to script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    about_win = tk.Toplevel(master)
    about_win.title("About AutoPy++")
    about_win.geometry("250x520")
    about_win.resizable(False, False)
    about_win.transient(master)
    about_win.grab_set()
    about_win.protocol("WM_DELETE_WINDOW", lambda: None)

    theme_func(style, about_win)

    main_frame = ttk.Frame(about_win)
    main_frame.pack(expand=True, fill="both", padx=10, pady=10)

    try:
        about_img = tk.PhotoImage(file="about.png")
    except Exception as e:
        about_img = None
        print("Error loading about.png:", e)

    # Center the image
    if about_img:
        img_label = ttk.Label(main_frame, image=about_img)
        img_label.image = about_img
        img_label.pack(pady=(10, 10), anchor="center")

    text = (
        "AutoPy++\n"
        "Version 2.35 (Date: 20.07.2025)\n"
        "Developer: melatroid\n"
        "© 2025 by melatroid\n"
        "Bug reports: dseccg@gmail.com\n"
        "www.autopyplusplus.wordpress.com\n\n"
        "License: MIT License\n\n"
        "Buy me a coffee 😊☕\n"
        "Software is a lot of work\n please respect it.\n"
    )

    # Center the main text label
    label = ttk.Label(main_frame, text=text, justify="center", font=("Segoe UI", 10))
    label.pack(pady=8, anchor="center")

    # PayPal Section
    paypal_label = ttk.Label(main_frame, text="PayPal Address:", font=("Segoe UI", 10, "bold"))
    paypal_label.pack(pady=(5, 2), anchor="center")

    paypal_entry = ttk.Entry(main_frame, font=("Segoe UI", 10), justify="center", width=25)
    paypal_entry.insert(0, "melatroid@gmail.com")
    paypal_entry.config(state="readonly")
    paypal_entry.pack(pady=(0, 4), anchor="center")

    def copy_to_clipboard():
        about_win.clipboard_clear()
        about_win.update()
        countdown_var.set("Address copied! 😊")

    copy_button = ttk.Button(main_frame, text="📋 Copy to Clipboard", command=copy_to_clipboard)
    copy_button.pack(pady=(0, 10), anchor="center")

    # Countdown label
    countdown_var = tk.StringVar(value="This window will close in 5 seconds …")
    countdown_label = ttk.Label(main_frame, textvariable=countdown_var, font=("Segoe UI", 10, "bold"), foreground="#4444dd")
    countdown_label.pack(pady=(0, 8), anchor="center")

    # Center the window on screen
    about_win.update_idletasks()
    x = (master.winfo_screenwidth() // 2) - (about_win.winfo_reqwidth() // 2)
    y = (master.winfo_screenheight() // 2) - (about_win.winfo_reqheight() // 2)
    about_win.geometry(f"+{x}+{y}")

    # Countdown logic
    def update_countdown(remaining):
        if remaining > 0:
            if not countdown_var.get().startswith("Address copied"):
                countdown_var.set(f"Closing in {remaining} second{'s' if remaining != 1 else ''} …")
            about_win.after(1000, update_countdown, remaining - 1)
        else:
            countdown_var.set("Enjoy!")
            about_win.after(350, about_win.destroy)

    update_countdown(3)