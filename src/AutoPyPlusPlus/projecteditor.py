import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
from datetime import datetime
from .tooltip import CreateToolTip
from .help import show_edit_helper
from .nuitkaeditor import NuitkaEditor
from .cythoneditor import CythonEditor
from .pytesteditor import PytestEditor
from .sphinxeditor import SphinxEditor
from .pyarmoreditor import PyarmorEditor
from glob import glob
import re
import sys


class ProjectEditor:
    def __init__(self, master, project, texts, app=None):
        self.master = master
        self.project = project
        self.texts = texts
        self.app = app
        self.saved = False
        self.txt_options = None

        # --- Sicherstellen, dass die Tool-Flags im Projekt existieren ---
        for attr in ("use_pytest", "use_sphinx", "use_pyarmor", "use_nuitka", "use_cython"):
            if not hasattr(self.project, attr):
                setattr(self.project, attr, False)

        # Tool flags (UI-Variablen)
        self.var_use_pytest  = tk.BooleanVar(value=self.project.use_pytest)
        self.var_use_sphinx  = tk.BooleanVar(value=self.project.use_sphinx)
        self.var_use_pyarmor = tk.BooleanVar(value=self.project.use_pyarmor)
        self.var_use_nuitka  = tk.BooleanVar(value=self.project.use_nuitka)
        self.var_use_cython  = tk.BooleanVar(value=self.project.use_cython)

        # PyInstaller: include PyArmor runtime
        self.var_include_pyarmor_runtime = tk.BooleanVar(
            value=getattr(self.project, "include_pyarmor_runtime", False)
        )

    # ----------------- Toggle handlers -----------------
    def on_use_pytest_toggle(self):
        if self.var_use_pytest.get():
            self.project.use_pytest = True
            self.win.destroy()
            editor = PytestEditor(self.master, self.project)
            if editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_pytest = False

    def on_use_sphinx_toggle(self):
        if self.var_use_sphinx.get():
            self.project.use_sphinx = True
            self.win.destroy()
            editor = SphinxEditor(self.master, self.project, self.texts)
            if editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_sphinx = False

    def on_use_nuitka_toggle(self):
        if self.var_use_nuitka.get():
            self.var_use_pyarmor.set(False)
            self.var_use_cython.set(False)
            self.project.use_pyarmor = False
            self.project.use_cython = False
            self.project.use_nuitka = True
            self.win.destroy()
            editor = NuitkaEditor(self.master, self.project, self.texts)
            if editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_nuitka = False

    def on_use_cython_toggle(self):
        if self.var_use_cython.get():
            self.var_use_nuitka.set(False)
            self.var_use_pyarmor.set(False)
            self.project.use_nuitka = False
            self.project.use_pyarmor = False
            self.project.use_cython = True
            self.win.destroy()
            editor = CythonEditor(self.master, self.project)
            if editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_cython = False

    def on_use_pyarmor_toggle(self):
        if self.var_use_pyarmor.get():
            self.var_use_nuitka.set(False)
            self.var_use_cython.set(False)
            self.project.use_nuitka = False
            self.project.use_cython = False
            self.project.use_pyarmor = True
            self.win.destroy()
            editor = PyarmorEditor(self.master, self.project)
            if editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_pyarmor = False

    def _enforce_exclusivity(self):
        active = [
            (self.var_use_pyarmor.get(), 'pyarmor'),
            (self.var_use_nuitka.get(), 'nuitka'),
            (self.var_use_cython.get(), 'cython'),
        ]
        if sum(1 for v, _ in active if v) > 1:
            self.var_use_pyarmor.set(False)
            self.var_use_nuitka.set(False)
            self.var_use_cython.set(False)

    # --- NEU: bereits gesetzte Flags beim Öffnen auswerten und passende Editoren starten ---
    def _launch_preselected_tools(self):
        """Startet passende Unter-Editoren für bereits gesetzte Flags.
           Beachtet Exklusivität (Nuitka / Cython / PyArmor)."""
        # Exklusivität einmal sicherstellen
        self._enforce_exclusivity()

        editors = []

        # Exklusive Build-Tools (max. einer)
        if self.var_use_nuitka.get():
            editors.append(lambda: NuitkaEditor(self.master, self.project, self.texts))
        elif self.var_use_cython.get():
            editors.append(lambda: CythonEditor(self.master, self.project))
        elif self.var_use_pyarmor.get():
            editors.append(lambda: PyarmorEditor(self.master, self.project))

        # Unabhängige Tools:
        if self.var_use_pytest.get():
            editors.append(lambda: PytestEditor(self.master, self.project))
        if self.var_use_sphinx.get():
            editors.append(lambda: SphinxEditor(self.master, self.project, self.texts))

        if not editors:
            return

        # Hauptfenster schließen wie in den Toggle-Handlern
        if self.win and self.win.winfo_exists():
            self.win.destroy()

        # Nacheinander öffnen; nach jedem Editor ggf. Tree refreshen
        for make_editor in editors:
            ed = make_editor()
            if ed.show() and self.app:
                self.app._refresh_tree()

    # ----------------- UI -----------------
    def show(self):
        self.x = 860
        self.y = 620
        self.win = tk.Toplevel(self.master)
        self.win.title("Python Compilation Editor")
        self.win.geometry(f"{self.x}x{self.y}")
        self.win.transient(self.master)
        self.win.grab_set()
        try:
            self.win.iconbitmap('autoPy++.ico')
        except Exception:
            pass

        form_frame = ttk.Frame(self.win, padding="10")
        form_frame.pack(fill="both", expand=True)

        check_frame_top = ttk.Frame(form_frame)
        check_frame_top.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")

        self.var_onefile = tk.BooleanVar(value=self.project.onefile)
        ttk.Checkbutton(check_frame_top, text=self.texts["onefile_label"], variable=self.var_onefile)\
            .grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.var_console_mode = tk.BooleanVar(value=self.project.console)
        ttk.Radiobutton(check_frame_top, text=self.texts["console_label"],
                        variable=self.var_console_mode, value=True)\
            .grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Radiobutton(check_frame_top, text=self.texts["windowed_label"],
                        variable=self.var_console_mode, value=False)\
            .grid(row=0, column=2, padx=5, pady=2, sticky="w")

        # Tool checkboxes
        ttk.Checkbutton(check_frame_top, text="Use PyArmor",
                        variable=self.var_use_pyarmor, command=self.on_use_pyarmor_toggle)\
            .grid(row=0, column=3, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(check_frame_top, text="Use Nuitka",
                        variable=self.var_use_nuitka, command=self.on_use_nuitka_toggle)\
            .grid(row=0, column=4, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(check_frame_top, text="Use Cython",
                        variable=self.var_use_cython, command=self.on_use_cython_toggle)\
            .grid(row=0, column=5, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(check_frame_top, text="Use Pytest",
                        variable=self.var_use_pytest, command=self.on_use_pytest_toggle)\
            .grid(row=0, column=6, padx=5, pady=2, sticky="w")

        ttk.Checkbutton(check_frame_top, text="Use Sphinx",
                        variable=self.var_use_sphinx, command=self.on_use_sphinx_toggle)\
            .grid(row=0, column=7, padx=5, pady=2, sticky="w")

        # Entry helper
        def create_entry_row(text, row, default="", file_button=False, directory=False):
            label = ttk.Label(form_frame, text=text)
            label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
            frame = ttk.Frame(form_frame)
            frame.grid(row=row, column=1, pady=2, sticky="ew")
            e = ttk.Entry(frame, width=100)
            e.grid(row=0, column=0, sticky="ew")
            e.insert(0, default)

            filetypes = [("All Files", "*.*")]
            if directory:
                filetypes = []
            elif text == self.texts["icon_label"]:
                filetypes = [("Icon Files", "*.ico")]
            elif text == "Script:":
                filetypes = [("Python Files", "*.py")]

            if file_button or directory:
                ttk.Button(frame, text="...",
                           command=lambda: self._choose_file(e, directory, filetypes))\
                    .grid(row=0, column=1, padx=5)
            return e, label

        # Basic fields
        self.e_name, _ = create_entry_row(self.texts["name_label"], 1, self.project.name)
        self.e_script, _ = create_entry_row("Script:", 2, self.project.script, file_button=True)
        self.e_output, _ = create_entry_row(self.texts["output_label"], 3, self.project.output, directory=True)
        self.e_icon, _ = create_entry_row(self.texts["icon_label"], 4, self.project.icon, file_button=True)
        self.e_add, _ = create_entry_row(self.texts["add_data_label"], 5, self.project.add_data)

        ttk.Separator(form_frame, orient="horizontal")\
            .grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)

        self.e_hidden, _ = create_entry_row(self.texts["hidden_imports_label"], 7, self.project.hidden_imports)
        self.e_version, _ = create_entry_row(self.texts["version_label"], 8, self.project.version, file_button=True)
        self.e_runtime_hook, _ = create_entry_row(self.texts["runtime_hook_label"], 9, self.project.runtime_hook, file_button=True)
        self.e_splash, _ = create_entry_row(self.texts["splash_label"], 10, self.project.splash, file_button=True)
        self.e_spec_file, _ = create_entry_row(self.texts["spec_file_label"], 11, self.project.spec_file, file_button=True)

        self.e_pyarmor_runtime_dir, self.l_pyarmor_runtime_dir = create_entry_row(
            "PyArmor runtime folder:", 12, getattr(self.project, "pyarmor_runtime_dir", ""), directory=True
        )

        # Options field
        ttk.Label(form_frame, text=self.texts["options_label"]).grid(row=13, column=0, sticky="ne", pady=5)
        self.txt_options = scrolledtext.ScrolledText(form_frame, width=50, height=4, font=("Segoe UI", 10))
        self.txt_options.grid(row=13, column=1, pady=5, sticky="ew")
        self.txt_options.insert(tk.END, self.project.options)

        # Bottom options
        check_frame_bottom = ttk.Frame(form_frame)
        check_frame_bottom.grid(row=14, column=0, columnspan=2, pady=5, sticky="w")

        self.var_upx = tk.BooleanVar(value=self.project.upx)
        self.var_debug = tk.BooleanVar(value=self.project.debug)
        self.var_clean = tk.BooleanVar(value=self.project.clean)
        self.var_strip = tk.BooleanVar(value=self.project.strip)
        self.var_exclude_tcl = tk.BooleanVar(value=getattr(self.project, "exclude_tcl", False))

        ttk.Checkbutton(check_frame_bottom, text=self.texts["upx_label"], variable=self.var_upx).grid(row=0, column=0, padx=5)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["debug_label"], variable=self.var_debug).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["clean_label"], variable=self.var_clean).grid(row=0, column=2, padx=5)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["strip_label"], variable=self.var_strip).grid(row=0, column=3, padx=5)
        ttk.Checkbutton(check_frame_bottom, text="Disable Tcl", variable=self.var_exclude_tcl).grid(row=0, column=4, padx=5)

        ttk.Checkbutton(check_frame_bottom, text="Include PyArmor runtime",
                        variable=self.var_include_pyarmor_runtime,
                        command=self._toggle_runtime_row)\
            .grid(row=0, column=5, padx=12, pady=2, sticky="w")

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=15, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Cancel", command=self.win.destroy).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Analyze", command=self.analyze_inputs).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Save", command=self.save, style="Accent.TButton").grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="❓Help", command=lambda: show_edit_helper(self.win)).grid(row=0, column=3, padx=5)

        self._toggle_runtime_row()
        self._enforce_exclusivity()

        # --- NEU: Falls Flags bereits True sind, sofort die passenden Editoren öffnen ---
        self._launch_preselected_tools()

        if self.win and self.win.winfo_exists():
            self.win.wait_window()
        return self.saved

    # ----------------- Helpers -----------------
    def _choose_file(self, entry, directory=False, filetypes=None):
        if directory:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=filetypes or [("All Files", "*.*")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _toggle_runtime_row(self):
        show = self.var_include_pyarmor_runtime.get()
        (self.e_pyarmor_runtime_dir.master.grid if show else self.e_pyarmor_runtime_dir.master.grid_remove)()
        (self.l_pyarmor_runtime_dir.grid if show else self.l_pyarmor_runtime_dir.grid_remove)()

    def _is_runtime_dir(self, path: Path) -> bool:
        if not (path and path.is_dir() and path.name.startswith("pyarmor_runtime_")):
            return False
        return any(child.is_file() and child.name.startswith("pyarmor_runtime") for child in path.iterdir())

    def _find_pyarmor_runtime_dir(self, base_dir: str):
        if not base_dir:
            return None
        p = Path(base_dir)
        if self._is_runtime_dir(p):
            return p
        candidates = [Path(d) for d in glob(str(p / "pyarmor_runtime_*")) if self._is_runtime_dir(Path(d))]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return candidates[0]

    def analyze_inputs(self):
        issues = []
        script_path = self.e_script.get().strip()
        output_path = self.e_output.get().strip()

        if not script_path:
            issues.append("Script path is empty.")
        elif not Path(script_path).exists():
            issues.append(f"Script path does not exist: {script_path}")
        elif not script_path.endswith(".py"):
            issues.append(f"Script path is not a Python file: {script_path}")

        if not output_path:
            issues.append("Output folder is empty.")
        elif Path(output_path).exists() and not Path(output_path).is_dir():
            issues.append(f"Output path is not a directory: {output_path}")

        if self.var_include_pyarmor_runtime.get():
            runtime_dir = (self.e_pyarmor_runtime_dir.get() or "").strip()
            found = self._find_pyarmor_runtime_dir(runtime_dir)
            if not found:
                issues.append(f"PyArmor runtime not found in {runtime_dir}")

        messagebox.showwarning("Analysis Result", "\n".join(issues) if issues else "No security issues found!")

    # ---------- Add-Data Normalisierung ----------
    def _normalize_add_data(self, s: str) -> str:
        if not s:
            return ""
        s = s.strip()
        pattern = r'(?P<prefix>^|[;\r\n])(?P<src>[A-Za-z]:[\\/][^;\r\n]+);(?P<dst>[A-Za-z0-9_.-]+)'
        return re.sub(pattern, lambda m: f"{m.group('prefix')}{m.group('src')}:{m.group('dst')}", s)

    def _autocorrect_add_data_token(self, token: str) -> str:
        t = token.strip().strip('"').strip("'")
        if not t:
            return ""
        if ":" in t and not t.endswith(":"):
            return t
        if ";" in t:
            i = t.rfind(";")
            return t[:i] + ":" + t[i + 1:]
        return t

    def save(self):
        p = self.project
        p.options = self.txt_options.get("1.0", tk.END).strip() if self.txt_options else ""
        p.script = self.e_script.get()
        p.name = self.e_name.get() or (Path(p.script).stem if p.script else "")
        p.icon = self.e_icon.get()

        valid_add_data = []
        raw_add_data = self.e_add.get()
        normalized = self._normalize_add_data(raw_add_data)

        for entry in re.split(r'[;\r\n]+', normalized):
            entry = entry.strip()
            if not entry:
                continue
            entry = self._autocorrect_add_data_token(entry)
            if ":" not in entry or entry.endswith(":"):
                continue
            src, dest = entry.rsplit(":", 1)
            src, dest = src.strip(), dest.strip()
            if not Path(src).exists():
                continue
            valid_add_data.append(f"{src}:{dest}")

        if self.var_include_pyarmor_runtime.get():
            runtime_dir = (self.e_pyarmor_runtime_dir.get() or "").strip()
            resolved = self._find_pyarmor_runtime_dir(runtime_dir)
            if resolved and resolved.is_dir():
                mapping = f"{resolved}:{resolved.name}"
                if mapping not in valid_add_data:
                    valid_add_data.append(mapping)
        p.add_data = ";".join(valid_add_data)

        p.hidden_imports = self.e_hidden.get()
        p.version = self.e_version.get()
        p.output = self.e_output.get()
        p.onefile = self.var_onefile.get()
        p.console = self.var_console_mode.get()
        p.upx = self.var_upx.get()
        p.debug = self.var_debug.get()
        p.clean = self.var_clean.get()
        p.strip = self.var_strip.get()
        p.exclude_tcl = self.var_exclude_tcl.get()

        p.include_pyarmor_runtime = self.var_include_pyarmor_runtime.get()
        p.pyarmor_runtime_dir = self.e_pyarmor_runtime_dir.get()

        # --- NEU: Flags aus den UI-Variablen zuverlässig zurückschreiben ---
        p.use_pytest  = self.var_use_pytest.get()
        p.use_sphinx  = self.var_use_sphinx.get()
        p.use_pyarmor = self.var_use_pyarmor.get()
        p.use_nuitka  = self.var_use_nuitka.get()
        p.use_cython  = self.var_use_cython.get()

        self.saved = True
        self.win.destroy()
