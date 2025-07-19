# general_settings.py

import tkinter as tk
from tkinter import ttk, messagebox
from .config import save_config

def show_general_settings(master, config: dict, style, theme_func):
    win = tk.Toplevel(master)
    win.title("AutoPy++ – General Settings")
    win.geometry("360x260")
    win.resizable(False, False)
    win.transient(master)
    win.grab_set()

    # Apply theme if needed
    if theme_func:
        theme_func(style, win)


    # Save button
    def save():
        save_config(config)
        messagebox.showinfo("Saved", "Settings saved successfully.")
        win.destroy()

    ttk.Button(win, text="💾 Save", command=save).pack(pady=10)
