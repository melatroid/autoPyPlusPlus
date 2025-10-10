import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from .config import save_config


def show_general_settings(master, config: dict, style, theme_func):
    win = tk.Toplevel(master)
    win.title("AutoPy++ – General Settings")
    win.geometry("600x300")
    win.transient(master)
    win.grab_set()

    # Apply theme if provided
    if theme_func:
        theme_func(style, win)

    # -------------------- state + helpers --------------------
    working_dir_var = tk.StringVar(
        value=config.get(
            "working_dir",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        )
    )
    enable_hashcheck_var = tk.BooleanVar(value=bool(config.get("enable_hashcheck", True)))

    original_wd = working_dir_var.get()
    original_hash = enable_hashcheck_var.get()

    def enable_save_btn_if_changed(*_):
        changed = (
            working_dir_var.get() != original_wd
            or enable_hashcheck_var.get() != original_hash
        )
        if changed:
            save_btn.state(["!disabled"])
        else:
            save_btn.state(["disabled"])

    # ===================== Working Directory =====================
    frame_dir = ttk.LabelFrame(win, text="Working Directory", padding=10)
    frame_dir.pack(fill="x", padx=16, pady=(12, 8))
    frame_dir.columnconfigure(1, weight=1)

    # short description
    ttk.Label(
        frame_dir,
        text="Base folder where logs, artifacts and temporary files are stored.",
        wraplength=540,
        foreground="#666",
    ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 6))

    ttk.Label(frame_dir, text="Path:").grid(row=1, column=0, padx=(0, 6), pady=(0, 6), sticky="w")

    entry_dir = ttk.Entry(frame_dir, textvariable=working_dir_var)
    entry_dir.grid(row=1, column=1, padx=(0, 6), pady=(0, 6), sticky="ew")

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

    ttk.Button(frame_dir, text="Browse…", width=9, command=browse_dir).grid(row=1, column=2, pady=(0, 6), sticky="e")
    ttk.Button(frame_dir, text="Open",    width=7, command=open_working_dir).grid(row=1, column=3, padx=(6, 0), pady=(0, 6), sticky="e")
    ttk.Button(frame_dir, text="Copy",    width=7, command=copy_path).grid(row=1, column=4, padx=(6, 0), pady=(0, 6), sticky="e")

    xscroll = ttk.Scrollbar(frame_dir, orient="horizontal", command=entry_dir.xview)
    xscroll.grid(row=2, column=1, columnspan=4, sticky="ew")
    entry_dir.configure(xscrollcommand=xscroll.set)

    # ===================== Build Safety (Hash Check) =====================
    frame_hash = ttk.LabelFrame(win, text="Build Safety", padding=10)
    frame_hash.pack(fill="x", padx=16, pady=(0, 8))

    ttk.Label(
        frame_hash,
        text=(
            "Verify project source checksums against a trusted reference before running ‘Compile All’. "
            "This helps detect unintended edits or tampering."
        ),
        wraplength=540,
        foreground="#666",
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    chk = ttk.Checkbutton(
        frame_hash,
        text="Enable hash check before ‘Compile All’",
        variable=enable_hashcheck_var,
        onvalue=True,
        offvalue=False,
        command=enable_save_btn_if_changed,
    )
    chk.grid(row=1, column=0, sticky="w")

    # ===================== Save / Close =====================
    btns = ttk.Frame(win)
    btns.pack(fill="x", padx=16, pady=(6, 12))

    save_btn = ttk.Button(btns, text="💾 Save")
    save_btn.pack(side="right")
    close_btn = ttk.Button(btns, text="Close", command=win.destroy)
    close_btn.pack(side="right", padx=(0, 8))

    def save():
        # Resolve and validate working dir
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

        # persist
        config["working_dir"] = str(wd)
        config["enable_hashcheck"] = bool(enable_hashcheck_var.get())
        save_config(config)

        # live-apply to main window if available
        if hasattr(master, "working_dir"):
            master.working_dir = wd
        if hasattr(master, "enable_hashcheck_var"):
            try:
                master.enable_hashcheck_var.set(bool(enable_hashcheck_var.get()))
            except Exception:
                pass

        messagebox.showinfo(
            "Saved",
            f"Working Directory: {wd}\n"
            f"Hash Check: {'enabled' if enable_hashcheck_var.get() else 'disabled'}\n\n"
            "(A restart might only be necessary if other modules cache settings during import.)",
        )
        win.destroy()

    save_btn.configure(command=save)

    # traces to enable/disable save
    working_dir_var.trace_add("write", enable_save_btn_if_changed)
    enable_save_btn_if_changed()  # evaluate initial state
