import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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

    # --- Arbeitsverzeichnis (Working Directory) ---
    frame_dir = ttk.LabelFrame(win, text="Working Directory", padding=10)
    frame_dir.pack(fill="x", padx=16, pady=10)

    working_dir_var = tk.StringVar(value=config.get("working_dir", os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))))
    
    def browse_dir():
        folder = filedialog.askdirectory(title="Working Directory", initialdir=working_dir_var.get())
        if folder:
            working_dir_var.set(folder)

    ttk.Entry(frame_dir, textvariable=working_dir_var, width=34).pack(side="left", padx=(0, 4))
    ttk.Button(frame_dir, text="...", command=browse_dir, width=3).pack(side="left")

    # --- Legacy-GUI-Modus ---
    legacy_var = tk.BooleanVar(value=config.get("legacy_gui_mode", False))
    ttk.Checkbutton(
        win,
        text="Legacy-GUI",
        variable=legacy_var
    ).pack(anchor="w", padx=18, pady=(4, 0))

    # Save button
    def save():
        config["working_dir"] = working_dir_var.get()
        config["legacy_gui_mode"] = legacy_var.get()
        save_config(config)
        # Attribute im Parent (dein Main-Window) aktualisieren:
        if hasattr(master, "working_dir"):
            master.working_dir = working_dir_var.get()
        if hasattr(master, "legacy_gui_mode"):
            master.legacy_gui_mode = legacy_var.get()
            if hasattr(master, "_build_ui"):
                master._build_ui()  # GUI neu aufbauen!
        messagebox.showinfo("Saved", "Restart AutoPY++!")
        win.destroy()
        
    ttk.Button(win, text="💾 Save", command=save).pack(pady=10)
