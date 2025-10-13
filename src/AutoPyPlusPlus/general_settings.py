import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from .config import save_config


def show_general_settings(master, config: dict, style, theme_func):
    win = tk.Toplevel(master)
    win.title("AutoPy++ – Advanced Settings")
    win.geometry("600x600")
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
    sequential_build_var = tk.BooleanVar(value=bool(config.get("sequential_build", False)))

    # NEW: pipeline cooldown (seconds)
    def _get_cooldown_initial():
        try:
            return max(0, int(config.get("pipeline_cooldown_s", 0)))
        except Exception:
            return 0

    pipeline_cooldown_var = tk.IntVar(value=_get_cooldown_initial())

    # NEW: thread count (parallelism) – clamp to CPU count
    _cpu_max = max(1, (os.cpu_count() or 1))
    def _get_threads_initial():
        try:
            v = int(config.get("thread_count", _cpu_max))
        except Exception:
            v = _cpu_max
        return max(1, min(_cpu_max, v))

    thread_count_var = tk.IntVar(value=_get_threads_initial())

    original_wd        = working_dir_var.get()
    original_hash      = enable_hashcheck_var.get()
    original_seq       = sequential_build_var.get()
    original_cooldown  = pipeline_cooldown_var.get()
    original_threads   = thread_count_var.get()

    def enable_save_btn_if_changed(*_):
        changed = (
            working_dir_var.get()           != original_wd
            or enable_hashcheck_var.get()   != original_hash
            or sequential_build_var.get()   != original_seq
            or pipeline_cooldown_var.get()  != original_cooldown
            or thread_count_var.get()       != original_threads
        )
        if changed:
            save_btn.state(["!disabled"])
        else:
            save_btn.state(["disabled"])

    # ===================== Parallel Build Threads (TOP) =====================
    frame_threads = ttk.LabelFrame(win, text="Parallel Build Threads", padding=10)
    frame_threads.pack(fill="x", padx=16, pady=(12, 8))
    frame_threads.columnconfigure(1, weight=0)

    ttk.Label(
        frame_threads,
        text=(
            "Sets the number of worker threads used during ‘Compile All’ when Top/Down Pipeline Mode is disabled. "
            "Higher values can speed up builds on multi-core CPUs. "
            "This is capped by your CPU core count. While Top/Down mode is active, this setting is ignored."
        ),
        wraplength=540,
        foreground="#666",
        justify="left",
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

    ttk.Label(frame_threads, text="Threads:").grid(row=1, column=0, sticky="w", padx=(0, 6))

    _Spinbox = getattr(ttk, "Spinbox", tk.Spinbox)  # fallback for older Tk
    threads_spin = _Spinbox(
        frame_threads,
        from_=1,
        to=_cpu_max,
        increment=1,
        textvariable=thread_count_var,
        width=7,
        justify="center",
        state="normal",
        wrap=False,
    )
    threads_spin.grid(row=1, column=1, sticky="w")

    ttk.Label(
        frame_threads,
        text=f"Detected CPU cores: {_cpu_max}",
        foreground="#666"
    ).grid(row=1, column=2, sticky="w", padx=(8, 0))

    # ===================== Working Directory =====================
    frame_dir = ttk.LabelFrame(win, text="Working Directory", padding=10)
    frame_dir.pack(fill="x", padx=16, pady=(0, 8))
    frame_dir.columnconfigure(1, weight=1)

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
                os.startfile(p)
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

    # ===================== Build Safety (Compiler Interface Guard) =====================
    frame_hash = ttk.LabelFrame(win, text="Build Safety", padding=10)
    frame_hash.pack(fill="x", padx=16, pady=(0, 8))

    ttk.Label(
        frame_hash,
        text=(
            "Before ‘Compile All’, verifies that the local toolchain matches the developer-approved "
            "compiler interface. Any mismatch halts the build."
        ),
        wraplength=540,
        foreground="#666",
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    chk_hash = ttk.Checkbutton(
        frame_hash,
        text="Enforce compiler-interface parity before ‘Compile All’",
        variable=enable_hashcheck_var,
        onvalue=True,
        offvalue=False,
        command=enable_save_btn_if_changed,
    )
    chk_hash.grid(row=1, column=0, sticky="w")

    # ===================== Top/Down Pipeline Mode =====================
    frame_seq = ttk.LabelFrame(win, text="Top/Down Pipeline Mode", padding=10)
    frame_seq.pack(fill="x", padx=16, pady=(0, 8))
    frame_seq.columnconfigure(1, weight=1)

    ttk.Label(
        frame_seq,
        text=(
            "When enabled, 'Compile All' creates a top/down pipeline: no parallel exports. "
            "All projects run strictly from top to bottom (A/B/C)"
            "exactly as shown in the list — one after another. "
            "You can intentionally place the same project multiple times in a row to build flexible "
            "multi-step pipelines (e.g., first PyArmor, then PyInstaller). "
            "While this mode is active, the multi-thread setting is ignored."
        ),
        wraplength=540,
        foreground="#666",
        justify="left",
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

    chk_seq = ttk.Checkbutton(
        frame_seq,
        text="Enable Top/Down Pipeline Mode (per active mode A/B/C)",
        variable=sequential_build_var,
        onvalue=True,
        offvalue=False,
        command=enable_save_btn_if_changed,
    )
    chk_seq.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 6))

    ttk.Label(frame_seq, text="Cooldown between jobs (seconds):").grid(row=2, column=0, sticky="w", padx=(0, 6))
    _Spinbox2 = getattr(ttk, "Spinbox", tk.Spinbox)  # fallback for older Tk
    cooldown_spin = _Spinbox2(
        frame_seq,
        from_=0,
        to=86400,
        increment=1,
        textvariable=pipeline_cooldown_var,
        width=7,
        justify="center",
        state="normal",
        wrap=False,
    )
    cooldown_spin.grid(row=2, column=1, sticky="w")

    ttk.Label(frame_seq, text="Applies only when Top/Down mode is enabled.", foreground="#666").grid(
        row=2, column=2, sticky="w", padx=(8, 0)
    )

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
        config["sequential_build"] = bool(sequential_build_var.get())

        # NEW: persist cooldown (seconds)
        try:
            cooldown_val = max(0, int(pipeline_cooldown_var.get()))
        except Exception:
            cooldown_val = 0
        config["pipeline_cooldown_s"] = cooldown_val

        # NEW: persist threads (parallelism)
        try:
            threads_val = max(1, min(_cpu_max, int(thread_count_var.get())))
        except Exception:
            threads_val = _cpu_max
        config["thread_count"] = threads_val

        save_config(config)

        # live-apply to main window if available
        if hasattr(master, "working_dir"):
            master.working_dir = wd
        if hasattr(master, "enable_hashcheck_var"):
            try:
                master.enable_hashcheck_var.set(bool(enable_hashcheck_var.get()))
            except Exception:
                pass
        if hasattr(master, "sequential_build_var"):
            try:
                master.sequential_build_var.set(bool(sequential_build_var.get()))
            except Exception:
                pass

        try:
            master.config["pipeline_cooldown_s"] = cooldown_val
            master.config["thread_count"] = threads_val
        except Exception:
            pass
        if hasattr(master, "pipeline_cooldown_s"):
            try:
                master.pipeline_cooldown_s = cooldown_val
            except Exception:
                pass

        messagebox.showinfo(
            "Saved",
            f"Working Directory: {wd}\n"
            f"Hash Check: {'enabled' if enable_hashcheck_var.get() else 'disabled'}\n"
            f"Top/Down Pipeline Mode: {'enabled' if sequential_build_var.get() else 'disabled'}\n"
            f"Cooldown (seconds): {cooldown_val}\n"
            f"Threads: {threads_val}\n\n"
            "(A restart might only be necessary if other modules cache settings during import.)",
        )
        win.destroy()

    save_btn.configure(command=save)

    # traces to enable/disable save
    working_dir_var.trace_add("write", enable_save_btn_if_changed)
    enable_hashcheck_var.trace_add("write", enable_save_btn_if_changed)
    sequential_build_var.trace_add("write", enable_save_btn_if_changed)
    pipeline_cooldown_var.trace_add("write", enable_save_btn_if_changed)
    thread_count_var.trace_add("write", enable_save_btn_if_changed)
    enable_save_btn_if_changed()  # evaluate initial state
