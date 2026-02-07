from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

from .project import Project
from .compiler import compile_single


class _UILog:
    """
    File-like logger that writes into a Tk Text widget.
    Works as log_file replacement for compile_single().
    """
    def __init__(self, text: tk.Text):
        self.text = text

    def write(self, s: str) -> None:
        try:
            self.text.insert(tk.END, s)
            self.text.see(tk.END)
            self.text.update_idletasks()
        except Exception:
            pass

    def flush(self) -> None:
        return


class MpyEditor:
    def __init__(self, master, style: Optional[ttk.Style] = None):
        self.master = master
        self.style = style
        self.win: Optional[tk.Toplevel] = None

        # Entries
        self.e_source_file: Optional[ttk.Entry] = None
        self.e_source_dir: Optional[ttk.Entry] = None
        self.e_output_dir: Optional[ttk.Entry] = None
        self.e_mpy_cross_path: Optional[ttk.Entry] = None
        self.e_extra_opts: Optional[ttk.Entry] = None
        self.e_exclude_glob: Optional[ttk.Entry] = None

        # Vars
        self.var_arch: Optional[tk.StringVar] = None
        self.var_opt: Optional[tk.StringVar] = None

        # Log
        self.log_text: Optional[tk.Text] = None

        # Buttons
        self.btn_compile: Optional[ttk.Button] = None

        # Thread guard
        self._compile_lock = threading.Lock()
        self._compiling = False

    def _require_ui(self) -> None:
        assert self.e_source_file is not None
        assert self.e_source_dir is not None
        assert self.e_output_dir is not None
        assert self.e_mpy_cross_path is not None
        assert self.e_extra_opts is not None
        assert self.e_exclude_glob is not None
        assert self.var_arch is not None
        assert self.var_opt is not None
        assert self.log_text is not None
        assert self.btn_compile is not None

    # ------------------------ Pickers ------------------------

    def _choose_py_file(self):
        self._require_ui()
        path = filedialog.askopenfilename(
            title="Select Python file",
            filetypes=[("Python Files", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return
        self.e_source_file.delete(0, tk.END)
        self.e_source_file.insert(0, path)
        if not self.e_output_dir.get().strip():
            self.e_output_dir.insert(0, str(Path(path).parent))

    def _choose_source_dir(self):
        self._require_ui()
        path = filedialog.askdirectory(title="Select source directory")
        if not path:
            return
        self.e_source_dir.delete(0, tk.END)
        self.e_source_dir.insert(0, path)
        if not self.e_output_dir.get().strip():
            self.e_output_dir.insert(0, str(Path(path)))

    def _choose_output_dir(self):
        self._require_ui()
        path = filedialog.askdirectory(title="Select output directory")
        if not path:
            return
        self.e_output_dir.delete(0, tk.END)
        self.e_output_dir.insert(0, path)

    def _choose_mpy_cross(self):
        self._require_ui()
        path = filedialog.askopenfilename(
            title="Select mpy-cross executable (optional)",
            filetypes=[("All files", "*.*")],
        )
        if not path:
            return
        self.e_mpy_cross_path.delete(0, tk.END)
        self.e_mpy_cross_path.insert(0, path)

    # ------------------------ Build Project ------------------------

    def _build_project_from_ui(self) -> Project:
        """
        Build a temporary Project instance that compile_single() can process.
        It will trigger CPH via:
            compiler="mpy" AND project.use_mpycross=True
        """
        self._require_ui()

        src_file = self.e_source_file.get().strip()
        src_dir = self.e_source_dir.get().strip()
        out_dir = self.e_output_dir.get().strip()
        mpy_cross = self.e_mpy_cross_path.get().strip()
        extra = self.e_extra_opts.get().strip()
        exclude = self.e_exclude_glob.get().strip()
        arch = (self.var_arch.get() or "").strip()
        opt = (self.var_opt.get() or "").strip()

        p = Project(name="Py→mpy (Tool)")

        # Minimal values used by your pipeline + CPH stage:
        p.script = src_file or ""                  # used if compile_dir empty
        p.mpy_compile_dir = src_dir or ""          # if set, CPH compiles recursively
        p.mpy_output_dir = out_dir or ""           # optional output dir
        p.mpy_cross_path = mpy_cross or None       # optional explicit mpy-cross path
        p.mpy_arch = arch or ""                    # optional -march=...
        p.mpy_extra_opts = extra or ""             # passthrough
        p.mpy_exclude_glob = exclude or ""         # optional exclude glob

        # opt string -> int|None (expects O0..O3)
        if opt.startswith("O") and opt[1:].isdigit():
            p.mpy_opt = int(opt[1:])
        else:
            p.mpy_opt = None

        # The flag that makes compiler.py choose CPH
        p.use_mpycross = True

        # Avoid accidental other compilers if Project() default ever changes
        p.use_pyarmor = False
        p.use_nuitka = False
        p.use_cython = False

        return p

    def _validate_inputs(self, p: Project) -> Optional[str]:
        src_file = (getattr(p, "script", "") or "").strip()
        src_dir = (getattr(p, "mpy_compile_dir", "") or "").strip()

        if not src_file and not src_dir:
            return "Please select a .py file OR a source directory."

        if src_file:
            sf = Path(src_file)
            if not sf.exists() or not sf.is_file():
                return f"Source file not found: {src_file}"
            if sf.suffix.lower() != ".py":
                return "The source file must be a .py file."

        if src_dir:
            sd = Path(src_dir)
            if not sd.exists() or not sd.is_dir():
                return f"Source directory not found: {src_dir}"

        out_dir = (getattr(p, "mpy_output_dir", "") or "").strip()
        if out_dir:
            od = Path(out_dir)
            if od.exists() and not od.is_dir():
                return f"Output path is not a directory: {out_dir}"

        return None

    # ------------------------ Compile ------------------------

    def _set_compiling_state(self, compiling: bool) -> None:
        self._require_ui()
        self._compiling = compiling
        try:
            self.btn_compile.config(state=("disabled" if compiling else "normal"))
        except Exception:
            pass

    def _compile_worker(self, p: Project) -> None:
        self._require_ui()
        log = _UILog(self.log_text)

        with self._compile_lock:
            self.master.after(0, lambda: self._set_compiling_state(True))

            try:
                log.write("\n" + "=" * 80 + "\n")
                log.write("Py to mpy: starting pipeline compile_single(..., compiler='mpy')\n")
                log.write("=" * 80 + "\n")
                log.write(f"script           : {getattr(p, 'script', '')}\n")
                log.write(f"mpy_compile_dir  : {getattr(p, 'mpy_compile_dir', '')}\n")
                log.write(f"mpy_output_dir   : {getattr(p, 'mpy_output_dir', '')}\n")
                log.write(f"mpy_cross_path   : {getattr(p, 'mpy_cross_path', None)}\n")
                log.write(f"mpy_arch         : {getattr(p, 'mpy_arch', '')}\n")
                log.write(f"mpy_opt          : {getattr(p, 'mpy_opt', None)}\n")
                log.write(f"mpy_extra_opts   : {getattr(p, 'mpy_extra_opts', '')}\n")
                log.write(f"mpy_exclude_glob : {getattr(p, 'mpy_exclude_glob', '')}\n\n")

                result = compile_single(p, log, compiler="mpy")

                log.write("\n" + "-" * 80 + "\n")
                log.write(f"Result: {result}\n")
                log.write("-" * 80 + "\n")
            except Exception as e:
                log.write(f"\nERROR: {e}\n")
            finally:
                self.master.after(0, lambda: self._set_compiling_state(False))

    def on_compile(self):
        self._require_ui()
        if self._compiling:
            return

        p = self._build_project_from_ui()
        err = self._validate_inputs(p)
        if err:
            messagebox.showerror("Py to mpy", err)
            return

        self.log_text.delete("1.0", tk.END)
        t = threading.Thread(target=self._compile_worker, args=(p,), daemon=True)
        t.start()

    # ------------------------ Window ------------------------

    def on_close(self):
        if self.win:
            try:
                self.win.destroy()
            except Exception:
                pass

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Py to mpy (mpy-cross)")
        self.win.geometry("980x400")
        self.win.transient(self.master)
        self.win.grab_set()

        menubar = tk.Menu(self.win)
        self.win.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select .py file", command=self._choose_py_file)
        file_menu.add_command(label="Select source directory", command=self._choose_source_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.on_close)

        main = ttk.Frame(self.win, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.LabelFrame(main, text="mpy-cross Settings", padding=(12, 8))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        right = ttk.LabelFrame(main, text="Log", padding=(12, 8))
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)

        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Vars
        self.var_arch = tk.StringVar(value="")
        self.var_opt = tk.StringVar(value="")

        def row_entry(parent, r, label, width=52, btn=None, btn_cmd=None):
            ttk.Label(parent, text=label).grid(row=r, column=0, sticky="e", pady=3, padx=(0, 6))
            e = ttk.Entry(parent, width=width)
            e.grid(row=r, column=1, sticky="ew", pady=3)
            if btn and btn_cmd:
                ttk.Button(parent, text=btn, command=btn_cmd).grid(row=r, column=2, padx=5, pady=3)
            return e

        self.e_source_file = row_entry(left, 0, "Source .py file:", btn="...", btn_cmd=self._choose_py_file)
        self.e_source_dir = row_entry(left, 1, "OR source directory:", btn="...", btn_cmd=self._choose_source_dir)
        self.e_output_dir = row_entry(left, 2, "Output directory:", btn="...", btn_cmd=self._choose_output_dir)
        self.e_mpy_cross_path = row_entry(left, 3, "mpy-cross path (optional):", btn="...", btn_cmd=self._choose_mpy_cross)

        ttk.Label(left, text="Target arch (optional):").grid(row=4, column=0, sticky="e", pady=3, padx=(0, 6))
        arch_values = ["", "xtensa", "armv6m", "armv7m", "armv7emsp", "armv7emdp", "rv32imc", "rv64imac"]
        ttk.Combobox(
            left, textvariable=self.var_arch, values=arch_values, width=18, state="readonly"
        ).grid(row=4, column=1, sticky="w", pady=3)

        ttk.Label(left, text="Optimization (optional):").grid(row=5, column=0, sticky="e", pady=3, padx=(0, 6))
        opt_values = ["", "O0", "O1", "O2", "O3"]
        ttk.Combobox(
            left, textvariable=self.var_opt, values=opt_values, width=6, state="readonly"
        ).grid(row=5, column=1, sticky="w", pady=3)

        self.e_extra_opts = row_entry(left, 6, "Extra options:", width=52)
        self.e_exclude_glob = row_entry(left, 7, "Exclude glob (dir mode):", width=52)

        left.grid_columnconfigure(1, weight=1)

        self.log_text = tk.Text(right, height=20, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.insert(tk.END, "Ready.\n")

        bottom = ttk.Frame(main)
        bottom.grid(row=1, column=0, columnspan=2, sticky="e", pady=(10, 0))

        self.btn_compile = ttk.Button(bottom, text="Compile", command=self.on_compile)
        self.btn_compile.pack(side="left", padx=6)

        ttk.Button(bottom, text="Close", command=self.on_close).pack(side="left", padx=6)

        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        self.win.wait_window(self.win)
        return True
