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

class ProjectEditor:
    def __init__(self, master, project, texts, app=None):
        self.master = master
        self.project = project
        self.texts = texts
        self.app = app
        self.saved = False
        self.txt_options = None

        # Tool-Flags
        self.var_use_pytest  = tk.BooleanVar(value=getattr(self.project, "use_pytest", False))
        self.var_use_sphinx  = tk.BooleanVar(value=getattr(self.project, "use_sphinx", False))
        self.var_use_pyarmor = tk.BooleanVar(value=getattr(self.project, "use_pyarmor", False))
        self.var_use_nuitka  = tk.BooleanVar(value=getattr(self.project, "use_nuitka", False))
        self.var_use_cython  = tk.BooleanVar(value=getattr(self.project, "use_cython", False))

        # PyInstaller-seitig: PyArmor-Runtime einbinden
        self.var_include_pyarmor_runtime = tk.BooleanVar(
            value=getattr(self.project, "include_pyarmor_runtime", False)
        )

    # ----------------- Toggle Handler -----------------
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
            # Exklusivität
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
        """Einfache 3-Wege-Exklusivität."""
        active = [
            (self.var_use_pyarmor.get(), 'pyarmor'),
            (self.var_use_nuitka.get(), 'nuitka'),
            (self.var_use_cython.get(), 'cython'),
        ]
        if sum(1 for v, _ in active if v) > 1:
            self.var_use_pyarmor.set(False)
            self.var_use_nuitka.set(False)
            self.var_use_cython.set(False)

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
        c_onefile = ttk.Checkbutton(check_frame_top, text=self.texts["onefile_label"], variable=self.var_onefile)
        c_onefile.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.var_console_mode = tk.BooleanVar(value=self.project.console)
        r_console = ttk.Radiobutton(check_frame_top, text=self.texts["console_label"],
                                    variable=self.var_console_mode, value=True)
        r_console.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        r_windowed = ttk.Radiobutton(check_frame_top, text=self.texts["windowed_label"],
                                     variable=self.var_console_mode, value=False)
        r_windowed.grid(row=0, column=2, padx=5, pady=2, sticky="w")

        # Nur Schalter – jeder öffnet seinen eigenen Editor
        pyarmor_cb = ttk.Checkbutton(check_frame_top, text="Use PyArmor",
                                     variable=self.var_use_pyarmor,
                                     command=self.on_use_pyarmor_toggle)
        pyarmor_cb.grid(row=0, column=3, padx=5, pady=2, sticky="w")

        nuitka_cb = ttk.Checkbutton(check_frame_top, text="Use Nuitka",
                                    variable=self.var_use_nuitka,
                                    command=self.on_use_nuitka_toggle)
        nuitka_cb.grid(row=0, column=4, padx=5, pady=2, sticky="w")

        cython_cb = ttk.Checkbutton(check_frame_top, text="Use Cython",
                                    variable=self.var_use_cython,
                                    command=self.on_use_cython_toggle)
        cython_cb.grid(row=0, column=5, padx=5, pady=2, sticky="w")

        pytest_cb = ttk.Checkbutton(check_frame_top, text="Use Pytest",
                                    variable=self.var_use_pytest,
                                    command=self.on_use_pytest_toggle)
        pytest_cb.grid(row=0, column=6, padx=5, pady=2, sticky="w")

        sphinx_cb = ttk.Checkbutton(check_frame_top, text="Use Sphinx",
                                    variable=self.var_use_sphinx,
                                    command=self.on_use_sphinx_toggle)
        sphinx_cb.grid(row=0, column=7, padx=5, pady=2, sticky="w")

        # Helper zum Erzeugen von Eingabezeilen
        def create_entry_row(text, row, default="", file_button=False, directory=False):
            label = ttk.Label(form_frame, text=text)
            label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
            frame = ttk.Frame(form_frame)
            frame.grid(row=row, column=1, pady=2, sticky="ew")
            e = ttk.Entry(frame, width=100)
            e.grid(row=0, column=0, sticky="ew")
            e.insert(0, default)

            filetypes = [("All Files", "*.*")] if not directory else []
            if text == self.texts["icon_label"]:
                filetypes = [("Icon Files", "*.ico")]
            elif text == self.texts["spec_file_label"]:
                filetypes = [("Spec Files", "*.spec")]
            elif text == self.texts["runtime_hook_label"]:
                filetypes = [("Python Files", "*.py")]
            elif text == self.texts["splash_label"]:
                filetypes = [("Image Files", "*.png *.jpg *.jpeg")]
            elif text == self.texts["version_label"]:
                filetypes = [("Text Files", "*.txt *.ver *.ini")]
            elif text == "Script:":
                filetypes = [("Python Files", "*.py")]

            if file_button or directory:
                ttk.Button(
                    frame,
                    text="...",
                    command=lambda: self._choose_file(e, directory, filetypes)
                ).grid(row=0, column=1, padx=5)

            form_frame.grid_columnconfigure(1, weight=1)
            return e, label

        # Allgemeine Felder
        self.e_name, self.l_name = create_entry_row(self.texts["name_label"], 1, self.project.name)
        self.e_script, self.l_script = create_entry_row("Script:", 2, self.project.script, file_button=True)
        self.e_output, self.l_output = create_entry_row(self.texts["output_label"], 3, self.project.output, directory=True)
        self.e_icon, self.l_icon = create_entry_row(self.texts["icon_label"], 4, self.project.icon, file_button=True)
        self.e_add, self.l_add = create_entry_row(self.texts["add_data_label"], 5, self.project.add_data)

        ttk.Separator(form_frame, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)

        self.e_hidden, self.l_hidden = create_entry_row(self.texts["hidden_imports_label"], 7, self.project.hidden_imports)
        self.e_version, self.l_version = create_entry_row(self.texts["version_label"], 8, self.project.version, file_button=True)
        self.e_runtime_hook, self.l_runtime_hook = create_entry_row(self.texts["runtime_hook_label"], 9, self.project.runtime_hook, file_button=True)
        self.e_splash, self.l_splash = create_entry_row(self.texts["splash_label"], 10, self.project.splash, file_button=True)
        self.e_spec_file, self.l_spec_file = create_entry_row(self.texts["spec_file_label"], 11, self.project.spec_file, file_button=True)

        # >>> PyInstaller: PyArmor Runtime (sichtbar per Checkbox)
        self.e_pyarmor_runtime_dir, self.l_pyarmor_runtime_dir = create_entry_row(
            "PyArmor Runtime-Ordner:", 12, getattr(self.project, "pyarmor_runtime_dir", ""), directory=True
        )

        # Optionen (allgemein)
        ttk.Label(form_frame, text=self.texts["options_label"]).grid(row=13, column=0, sticky="ne", pady=5)
        self.txt_options = scrolledtext.ScrolledText(form_frame, width=50, height=4, font=("Segoe UI", 10))
        self.txt_options.grid(row=13, column=1, pady=5, sticky="ew")
        self.txt_options.insert(tk.END, self.project.options)

        # Untere allgemeine Optionen (PyInstaller/Allgemein)
        check_frame_bottom = ttk.Frame(form_frame)
        check_frame_bottom.grid(row=14, column=0, columnspan=2, pady=5, sticky="w")

        self.var_upx = tk.BooleanVar(value=self.project.upx)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["upx_label"], variable=self.var_upx)\
            .grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.var_debug = tk.BooleanVar(value=self.project.debug)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["debug_label"], variable=self.var_debug)\
            .grid(row=0, column=1, padx=5, pady=2, sticky="w")

        self.var_clean = tk.BooleanVar(value=self.project.clean)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["clean_label"], variable=self.var_clean)\
            .grid(row=0, column=2, padx=5, pady=2, sticky="w")

        self.var_strip = tk.BooleanVar(value=self.project.strip)
        ttk.Checkbutton(check_frame_bottom, text=self.texts["strip_label"], variable=self.var_strip)\
            .grid(row=0, column=3, padx=5, pady=2, sticky="w")

        self.var_exclude_tcl = tk.BooleanVar(value=getattr(self.project, "exclude_tcl", False))
        ttk.Checkbutton(check_frame_bottom, text="Tcl deaktivieren", variable=self.var_exclude_tcl)\
            .grid(row=0, column=4, padx=5, pady=2, sticky="w")

        # Checkbox: Include PyArmor-Runtime (PyInstaller-Seite)
        c_include_runtime = ttk.Checkbutton(
            check_frame_bottom, text="Include PyArmor-Runtime",
            variable=self.var_include_pyarmor_runtime,
            command=self._toggle_runtime_row
        )
        c_include_runtime.grid(row=0, column=5, padx=12, pady=2, sticky="w")
        CreateToolTip(c_include_runtime, "Bindet den Ordner 'pyarmor_runtime_000000' ins Bundle ein.")

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=15, column=0, columnspan=2, pady=10)
        cancel_btn = ttk.Button(button_frame, text=self.texts["tooltip_cancel_project"].split(".")[0],
                                command=self.win.destroy)
        cancel_btn.grid(row=0, column=0, padx=5, pady=5)
        analyze_btn = ttk.Button(button_frame, text="Analyse", command=self.analyze_inputs)
        analyze_btn.grid(row=0, column=1, padx=5, pady=5)
        save_btn = ttk.Button(button_frame, text=self.texts["tooltip_save_project"].split(".")[0],
                              command=self.save, style="Accent.TButton")
        save_btn.grid(row=0, column=2, padx=5, pady=5)
        help_btn = ttk.Button(button_frame, text="❓Help", command=lambda: show_edit_helper(self.win))
        help_btn.grid(row=0, column=3, padx=5, pady=5)

        CreateToolTip(save_btn, self.texts["tooltip_save_project"])
        CreateToolTip(cancel_btn, self.texts["tooltip_cancel_project"])
        CreateToolTip(analyze_btn, "Analysiert sicherheitskritische Eingaben wie Ordnerstrukturen.")

        # Anfangszustand: Runtime-Row zeigen/verstecken
        self._toggle_runtime_row()

        self._enforce_exclusivity()

        # Standalone-Editoren bei gesetzten Flags öffnen
        if getattr(self.project, "use_pytest_standalone", False):
            self.on_use_pytest_toggle()
        elif getattr(self.project, "use_sphinx_standalone", False):
            self.on_use_sphinx_toggle()

        if getattr(self.project, "use_cython", False):
            self.on_use_cython_toggle()
        elif getattr(self.project, "use_nuitka", False):
            self.on_use_nuitka_toggle()
        elif getattr(self.project, "use_pyarmor", False):
            self.on_use_pyarmor_toggle()

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
        """Zeigt/verbirgt die PyArmor-Runtime-Zeile abhängig von der Checkbox."""
        show = self.var_include_pyarmor_runtime.get()
        (self.e_pyarmor_runtime_dir.master.grid if show else self.e_pyarmor_runtime_dir.master.grid_remove)()
        (self.l_pyarmor_runtime_dir.grid if show else self.l_pyarmor_runtime_dir.grid_remove)()
        if self.win and self.win.winfo_exists():
            self.win.update_idletasks()
            self.win.geometry(f"{self.win.winfo_reqwidth()}x{self.win.winfo_reqheight()}")

    def analyze_inputs(self):
        issues = []

        script_path = self.e_script.get().strip()
        output_path = self.e_output.get().strip()

        if not script_path:
            issues.append("Script-Pfad ist leer.")
        elif not Path(script_path).exists():
            issues.append(f"Script-Pfad existiert nicht: {script_path}")
        elif not script_path.endswith(".py"):
            issues.append(f"Script-Pfad ist keine Python-Datei: {script_path}")

        if not output_path:
            issues.append("Ausgabeordner ist leer.")
        else:
            output_dir = Path(output_path)
            if output_dir.exists() and not output_dir.is_dir():
                issues.append(f"Ausgabeordner ist kein gültiges Verzeichnis: {output_path}")

        # PyArmor-Runtime prüfen, falls gewünscht
        if self.var_include_pyarmor_runtime.get():
            runtime_dir = (self.e_pyarmor_runtime_dir.get() or "").strip()
            if not runtime_dir:
                issues.append("PyArmor Runtime-Ordner muss angegeben werden.")
            else:
                runtime_path = Path(runtime_dir) / "pyarmor_runtime_000000"
                if not runtime_path.is_dir():
                    issues.append(f"PyArmor-Laufzeitbibliothek nicht gefunden in: {runtime_path}")

        if issues:
            messagebox.showwarning("Analyse-Ergebnis", "\n".join(issues))
        else:
            messagebox.showinfo("Analyse-Ergebnis", "Keine sicherheitskritischen Probleme gefunden!")

    def save(self):
        p = self.project

        # Optionen
        p.options = self.txt_options.get("1.0", tk.END).strip() if self.txt_options else ""

        # Erst Script setzen, dann Name-Fallback
        p.script = self.e_script.get()
        p.name = self.e_name.get() or (Path(p.script).stem if p.script else "")
        p.icon = self.e_icon.get()

        # add_data Validierung (robust für Windows-Laufwerksbuchstaben)
        valid_add_data = []
        for entry in self.e_add.get().split(";"):
            entry = entry.strip()
            if not entry:
                continue
            if ":" not in entry:
                messagebox.showinfo("Warnung", f"Ungültiger add_data-Eintrag: '{entry}' (Format: src:dest)")
                continue
            src, dest = entry.rsplit(":", 1)  # rsplit – robust für 'C:\...'
            src_path = Path(src)
            if not src_path.exists():
                messagebox.showwarning("Warnung", f"Ungültiger add_data-Eintrag: '{src}' existiert nicht.")
                continue
            valid_add_data.append(f"{src}:{dest}")

        # >>> Auto-Include der PyArmor-Runtime per add_data (falls Checkbox aktiv)
        if self.var_include_pyarmor_runtime.get():
            runtime_dir = (self.e_pyarmor_runtime_dir.get() or "").strip()
            if runtime_dir:
                runtime_src = Path(runtime_dir) / "pyarmor_runtime_000000"
                if runtime_src.is_dir():
                    mapping = f"{runtime_src}:pyarmor_runtime_000000"
                    if mapping not in valid_add_data:
                        valid_add_data.append(mapping)
                else:
                    messagebox.showwarning(
                        "PyArmor Runtime",
                        f"Laufzeitbibliothek nicht gefunden:\n{runtime_src}\n"
                        "Bitte Ordner wählen, der 'pyarmor_runtime_000000' enthält."
                    )

        p.add_data = ";".join(valid_add_data)

        # Allgemeine Felder
        p.hidden_imports = self.e_hidden.get()
        p.version = self.e_version.get()
        p.output = self.e_output.get()
        p.onefile = self.var_onefile.get()
        p.console = self.var_console_mode.get()
        p.upx = self.var_upx.get()
        p.debug = self.var_debug.get()
        p.clean = self.var_clean.get()
        p.strip = self.var_strip.get()
        p.runtime_hook = self.e_runtime_hook.get()
        p.splash = self.e_splash.get()
        p.spec_file = self.e_spec_file.get()
        p.exclude_tcl = self.var_exclude_tcl.get()

        # PyArmor-Runtime Flags sichern
        p.include_pyarmor_runtime = self.var_include_pyarmor_runtime.get()
        p.pyarmor_runtime_dir = (self.e_pyarmor_runtime_dir.get() or "").strip()

        # Flags
        if self.var_use_nuitka.get():
            p.use_nuitka = True;  p.use_pyarmor = False; p.use_cython = False
        elif self.var_use_pyarmor.get():
            p.use_pyarmor = True; p.use_nuitka = False; p.use_cython = False
        elif self.var_use_cython.get():
            p.use_cython = True;  p.use_nuitka = False; p.use_pyarmor = False
        else:
            p.use_nuitka = p.use_pyarmor = p.use_cython = False

        p.use_pytest = self.var_use_pytest.get()
        p.use_sphinx = self.var_use_sphinx.get()

        # Validierung
        if p.script and Path(p.script).suffix.lower() != ".py":
            messagebox.showerror("Fehler", f"Ungültiges Skript: {p.script} (muss .py sein)")
            return

        if not p.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            p.output = str(Path("dist") / f"{p.name}_{timestamp}")

        self.saved = True
        self.win.destroy()
