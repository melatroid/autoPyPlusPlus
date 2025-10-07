import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from .config import save_config


def show_general_settings(master, config: dict, style, theme_func):
    win = tk.Toplevel(master)
    win.title("AutoPy++ – General Settings")
    win.geometry("560x220") 
    win.transient(master)
    win.grab_set()

    # Apply theme if provided
    if theme_func:
        theme_func(style, win)

    # --- Working Directory ---
    frame_dir = ttk.LabelFrame(win, text="Working Directory", padding=10)
    frame_dir.pack(fill="x", padx=16, pady=10)

    # Use grid for stretchy layout
    frame_dir.columnconfigure(1, weight=1)

    working_dir_var = tk.StringVar(
        value=config.get(
            "working_dir",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        )
    )
    original_wd = working_dir_var.get()

    def browse_dir():
        folder = filedialog.askdirectory(
            title="Select Working Directory",
            initialdir=working_dir_var.get() or os.path.expanduser("~"),
        )
        if folder:
            working_dir_var.set(folder)

    def open_working_dir():
        p = working_dir_var.get()
        if not p:
            return
        try:
            if os.name == "nt":
                os.startfile(p)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                import subprocess
                subprocess.run(["open", p], check=False)
            else:
                import subprocess
                subprocess.run(["xdg-open", p], check=False)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder:\n{e}")

    def copy_path():
        win.clipboard_clear()
        win.clipboard_append(working_dir_var.get())
        win.update()
        messagebox.showinfo("Copied", "Working directory path copied to clipboard.")

    # Label
    ttk.Label(frame_dir, text="Path:").grid(
        row=0, column=0, padx=(0, 6), pady=(0, 6), sticky="w"
    )

    # Entry that stretches horizontally
    entry_dir = ttk.Entry(frame_dir, textvariable=working_dir_var)
    entry_dir.grid(row=0, column=1, padx=(0, 6), pady=(0, 6), sticky="ew")

    # Buttons: Browse / Open / Copy
    ttk.Button(frame_dir, text="Browse…", width=8, command=browse_dir).grid(
        row=0, column=2, pady=(0, 6), sticky="e"
    )
    ttk.Button(frame_dir, text="Open", width=6, command=open_working_dir).grid(
        row=0, column=3, padx=(6, 0), pady=(0, 6), sticky="e"
    )
    ttk.Button(frame_dir, text="Copy", width=6, command=copy_path).grid(
        row=0, column=4, padx=(6, 0), pady=(0, 6), sticky="e"
    )

    # Horizontal scrollbar
    xscroll = ttk.Scrollbar(
        frame_dir, orient="horizontal", command=entry_dir.xview
    )
    xscroll.grid(row=1, column=1, columnspan=4, sticky="ew")
    entry_dir.configure(xscrollcommand=xscroll.set)

    # Save button
    save_btn = ttk.Button(win, text="💾 Save")
    save_btn.pack(pady=10)

    def _toggle_save_btn(*_):
        changed = (working_dir_var.get() != original_wd)
        if changed:
            save_btn.state(["!disabled"])
        else:
            save_btn.state(["disabled"])

    working_dir_var.trace_add("write", _toggle_save_btn)
    _toggle_save_btn()

    def save():
        # expand %VARS% and ~
        raw = working_dir_var.get()
        expanded = os.path.expandvars(os.path.expanduser(raw))
        wd = Path(expanded).resolve()

        if wd.exists() and not wd.is_dir():
            messagebox.showerror("Error", "The selected path is not a directory.")
            return

        if not wd.exists():
            try:
                wd.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create working directory:\n{e}")
                return

        # writability check
        try:
            testfile = wd / ".appp_write_test.tmp"
            with open(testfile, "w", encoding="utf-8") as f:
                f.write("ok")
            try:
                testfile.unlink(missing_ok=True)  # py>=3.8
            except TypeError:
                if testfile.exists():
                    testfile.unlink()
        except Exception as e:
            messagebox.showerror("Error", f"Directory is not writable:\n{e}")
            return


        config["working_dir"] = str(wd)
        save_config(config)

        # Apply live changes
        if hasattr(master, "working_dir"):
            master.working_dir = str(wd)

        messagebox.showinfo(
            "Saved",
            f"Working Directory: {wd}\n"
            "(A restart might only be necessary if other modules cache the path during import.)",
        )
        win.destroy()

    save_btn.configure(command=save)
