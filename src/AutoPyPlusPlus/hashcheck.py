from __future__ import annotations
import hashlib
import os
import threading
import queue
import time  # <— NEU
from typing import List, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ------------------------ Hash logic  ---------------------------

SUPPORTED = ("sha256", "sha384", "sha512", "sha3_512", "blake2b_512")
EXCLUDE_DIRS = {".git", "__pycache__", "venv", ".venv", "build", "dist", "node_modules"}

ALLOWED_STEMS = {
    "CPA0000000",
    "CPB0000000",
    "CPC0000000",
    "CPD0000000",
    "CPE0000000",
    "CPF0000000",
    "CPG0000000",
    "gui",
    "core",
    "compiler",
    "projecteditor",
    "pytesteditor",
    "sphinxeditor",
    "speceditor",
    "nuitkaeditor",
    "gcceditor",
    "hashcheck",
    "apyeditor"
}

def _open_binary(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def _is_valid_python_source(path: str) -> bool:
    try:
        text = open(path, "r", encoding="utf-8").read()
    except UnicodeDecodeError:
        return False
    try:
        compile(text, path, "exec")
        return True
    except SyntaxError:
        return False

def list_valid_py_files(root: str, validate_syntax: bool = True) -> List[str]:
    """
    Collect .py files whose basename is in ALLOWED_STEMS.
    """
    root_abs = os.path.abspath(root)
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_abs):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            stem, ext = os.path.splitext(fn)
            if ext.lower() == ".py" and stem in ALLOWED_STEMS:
                full = os.path.join(dirpath, fn)
                if not validate_syntax or _is_valid_python_source(full):
                    files.append(full)
    files.sort(key=lambda p: os.path.relpath(p, root_abs).replace(os.sep, "/"))
    return files

def _make_hasher(name: str):
    if name == "blake2b_512":
        return hashlib.blake2b(digest_size=64)
    try:
        return hashlib.new(name)
    except Exception as e:
        raise ValueError(f"Unsupported algorithm: {name}") from e

def compute_dir_hash(
    root: str,
    algorithm: str = "sha512",
    validate_syntax: bool = True,
) -> str:
    if algorithm not in SUPPORTED:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    files = list_valid_py_files(root, validate_syntax=validate_syntax)
    h = _make_hasher(algorithm)
    root_abs = os.path.abspath(root)
    for path in files:
        rel = os.path.relpath(path, root_abs).replace(os.sep, "/")
        header = f"FILE:{rel}\n".encode("utf-8")
        content = _open_binary(path)
        h.update(header)
        h.update(content)
        h.update(b"\n")
    return h.hexdigest()

# ------------------------------- Tkinter GUI -----------------------------------

class HashCompareApp(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=12)
        master.title("autoPy++ Hashcheck")
        self.pack(fill="both", expand=True)

        # State
        self.dir_var = tk.StringVar(value=os.getcwd())
        self.alg_var = tk.StringVar(value="sha512")
        self.validate_var = tk.BooleanVar(value=True)
        self.input_hash_var = tk.StringVar(value="")
        self.output_hash_var = tk.StringVar(value="")

        self._q: "queue.Queue[Tuple[str, str]]" = queue.Queue()
        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        # Row: directory
        r1 = ttk.Frame(self); r1.pack(fill="x", pady=(0,8))
        ttk.Label(r1, text="Directory:").pack(side="left")
        ttk.Entry(r1, textvariable=self.dir_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r1, text="Browse…", command=self._choose_dir).pack(side="left")

        # Row: options
        r2 = ttk.Frame(self); r2.pack(fill="x", pady=(0,8))
        ttk.Label(r2, text="Algorithm:").pack(side="left")
        alg_cb = ttk.Combobox(r2, textvariable=self.alg_var, values=SUPPORTED, state="readonly", width=12)
        alg_cb.pack(side="left", padx=6)
        self.validate_var.set(True) 
        ttk.Checkbutton(
            r2,
            text="Deep Check",
            variable=self.validate_var,
            state="disabled"
        ).pack(side="left", padx=(10,0))
        # Row: input hash
        r3 = ttk.LabelFrame(self, text="Input hash (hex)"); r3.pack(fill="x", pady=(0,8))
        ttk.Entry(r3, textvariable=self.input_hash_var).pack(fill="x", padx=8, pady=6)

        # Row: actions
        r4 = ttk.Frame(self); r4.pack(fill="x", pady=(0,8))
        self.run_btn = ttk.Button(r4, text="Check & Compare", command=self._run_compare)
        self.run_btn.pack(side="left")
        ttk.Button(r4, text="Copy result", command=self._copy_result).pack(side="left", padx=6)

        # Row: result
        r5 = ttk.LabelFrame(self, text="Result"); r5.pack(fill="x", pady=(0,8))
        self.result_label = ttk.Label(r5, text="Ready.", font=("TkDefaultFont", 10, "bold"))
        self.result_label.pack(anchor="w", padx=8, pady=6)

        # Row: computed hash (readonly)
        r6 = ttk.LabelFrame(self, text="Computed hash"); r6.pack(fill="x")
        ttk.Entry(r6, textvariable=self.output_hash_var, state="readonly").pack(fill="x", padx=8, pady=6)

        # Progress/status
        r7 = ttk.Frame(self); r7.pack(fill="x", pady=(8,0))
        self.progress = ttk.Progressbar(r7, mode="indeterminate")
        self.progress.pack(fill="x", expand=True)

        # Polish
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or os.getcwd())
        if d:
            self.dir_var.set(d)

    @staticmethod
    def _normalize_hash(s: str) -> str:
        """Normalize hex string: strip spaces, lower, remove common separators."""
        return "".join(s.strip().lower().split())

    def _copy_result(self):
        self.clipboard_clear()
        self.clipboard_append(self.output_hash_var.get())
        self.update()

    def _run_compare(self):
        # Basic input validation
        expected = self._normalize_hash(self.input_hash_var.get())
        if not expected:
            messagebox.showwarning("Input required", "Please enter an input hash to compare against.")
            return
        if any(c not in "0123456789abcdef" for c in expected):
            if not messagebox.askyesno("Non-hex characters",
                                       "The input contains non-hex characters. Continue anyway?"):
                return

        directory = self.dir_var.get()
        alg = self.alg_var.get()
        validate = self.validate_var.get()

        # UI state
        self.run_btn.configure(state="disabled")
        self.result_label.configure(text="Computing…", foreground="")
        self.progress.configure(mode="indeterminate")
        self.progress.start(8)

        # Threaded compute + charwise compare
        t = threading.Thread(target=self._worker_compute_and_compare, args=(directory, alg, validate, expected), daemon=True)
        t.start()

    def _worker_compute_and_compare(self, directory: str, alg: str, validate: bool, expected_norm: str):
        try:
            computed = compute_dir_hash(directory, algorithm=alg, validate_syntax=validate)
            self._q.put(("computed", computed))

            got = self._normalize_hash_static(computed)
            exp = expected_norm
            total = max(len(exp), len(got))

            self._q.put(("cmp_start", str(total)))

            mismatch_index = -1

            SLOWDOWN_SEC = 0.004  

            for i in range(total):
                ch_exp = exp[i] if i < len(exp) else None
                ch_got = got[i] if i < len(got) else None
                if mismatch_index == -1 and ch_exp != ch_got:
                    mismatch_index = i
                if i % 1 == 0:
                    self._q.put(("cmp_progress", str(i + 1)))
                if SLOWDOWN_SEC > 0:
                    time.sleep(SLOWDOWN_SEC)

            if mismatch_index == -1 and len(exp) == len(got):
                self._q.put(("compare", "MATCH"))
            else:
                if mismatch_index == -1:
                    mismatch_index = min(len(exp), len(got))
                self._q.put(("compare", f"MISMATCH:{mismatch_index}"))
        except Exception as e:
            self._q.put(("error", str(e)))

    @staticmethod
    def _normalize_hash_static(s: str) -> str:
        return "".join(s.strip().lower().split())

    def _poll_queue(self):
        try:
            while True:
                typ, payload = self._q.get_nowait()
                if typ == "computed":
                    self.output_hash_var.set(payload)

                elif typ == "cmp_start":
                    try:
                        total = int(payload)
                    except ValueError:
                        total = 0
                    self.progress.stop()
                    self.progress.configure(mode="determinate", maximum=total, value=0)

                elif typ == "cmp_progress":
                    try:
                        val = int(payload)
                    except ValueError:
                        val = 0
                    self.progress["value"] = val

                elif typ == "compare":
                    if payload == "MATCH":
                        self.result_label.configure(text="✅ Hashes match", foreground="green")
                    else:
                        if payload.startswith("MISMATCH:"):
                            idx_str = payload.split(":", 1)[1]
                            try:
                                idx = int(idx_str)
                                self.result_label.configure(
                                    text=f"❌ Hashes do NOT match (first diff at pos {idx})",
                                    foreground="red"
                                )
                            except ValueError:
                                self.result_label.configure(text="❌ Hashes do NOT match", foreground="red")
                        else:
                            self.result_label.configure(text="❌ Hashes do NOT match", foreground="red")
                    self.run_btn.configure(state="normal")

                elif typ == "error":
                    self.result_label.configure(text="Error occurred", foreground="orange")
                    messagebox.showerror("Error", payload)
                    self.run_btn.configure(state="normal")
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

# ---------------------------------- Run app -------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = HashCompareApp(root)
    root.geometry("700x360")
    root.mainloop()
