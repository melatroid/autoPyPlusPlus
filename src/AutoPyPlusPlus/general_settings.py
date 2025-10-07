import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from .config import save_config


def show_general_settings(master, config: dict, style, theme_func):
    win = tk.Toplevel(master)
    win.title("AutoPy++ – General Settings")
    win.geometry("360x260")
    #win.resizable(False, False)
    win.transient(master)
    win.grab_set()

    # Apply theme if provided
    if theme_func:
        theme_func(style, win)

    # --- Working Directory ---
    frame_dir = ttk.LabelFrame(win, text="Working Directory", padding=10)
    frame_dir.pack(fill="x", padx=16, pady=10)

    working_dir_var = tk.StringVar(
        value=config.get("working_dir", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    )

    def browse_dir():
        folder = filedialog.askdirectory(
            title="Select Working Directory",
            initialdir=working_dir_var.get()
        )
        if folder:
            working_dir_var.set(folder)

    ttk.Entry(frame_dir, textvariable=working_dir_var, width=34).pack(side="left", padx=(0, 4))
    ttk.Button(frame_dir, text="...", command=browse_dir, width=3).pack(side="left")

    # --- Legacy GUI Mode ---
    legacy_var = tk.BooleanVar(value=config.get("legacy_gui_mode", False))
    ttk.Checkbutton(
        win,
        text="Legacy GUI Mode",
        variable=legacy_var
    ).pack(anchor="w", padx=18, pady=(4, 0))

    # Save button
    def save():
        wd = Path(working_dir_var.get()).expanduser().resolve()

        if not wd.exists():
            try:
                wd.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create working directory:\n{e}")
                return

        config["working_dir"] = str(wd)
        config["legacy_gui_mode"] = legacy_var.get()
        save_config(config)

        # Apply live changes
        if hasattr(master, "working_dir"):
            master.working_dir = str(wd)
        if hasattr(master, "legacy_gui_mode"):
            master.legacy_gui_mode = legacy_var.get()
            if hasattr(master, "_build_ui"):
                master._build_ui()

        messagebox.showinfo(
            "Saved",
            f"Working Directory: {wd}\n"
            "(A restart might only be necessary if other modules cache the path during import.)"
        )
        win.destroy()

    ttk.Button(win, text="💾 Save", command=save).pack(pady=10)
