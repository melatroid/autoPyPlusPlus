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

class ProjectEditor:
    def __init__(self, master, project, texts, app=None):
        self.master = master
        self.project = project
        self.texts = texts
        self.app = app
        self.saved = False
        self.txt_options = None
        self.var_use_pytest = tk.BooleanVar(value=getattr(self.project, "use_pytest", False))
        self.var_use_sphinx = tk.BooleanVar(value=getattr(self.project, "use_sphinx", False))


    def on_use_pytest_toggle(self):
        if self.var_use_pytest.get():
            self.project.use_pytest = True
            self.win.destroy()
            pytest_editor = PytestEditor(self.master, self.project)
            if pytest_editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_pytest = False

    def on_use_sphinx_toggle(self):
        if self.var_use_sphinx.get():
            self.project.use_sphinx = True
            self.win.destroy()
            sphinx_editor = SphinxEditor(self.master, self.project, self.texts)
            if sphinx_editor.show() and self.app:
                self.app._refresh_tree()
        else:
            self.project.use_sphinx = False

    def on_use_nuitka_toggle(self):
        if self.var_use_nuitka.get():
            self.var_use_nuitka.set(True)
            self.var_use_pyarmor.set(False)
            self.var_use_cython.set(False)  
            self.project.use_pyarmor = False
            self.project.use_cython = False 
            self.toggle_pyarmor_fields()
            self.win.destroy()
            nuitka_editor = NuitkaEditor(self.master, self.project, self.texts)
            if nuitka_editor.show() and self.app:
                self.app._refresh_tree()


    def on_use_cython_toggle(self):
        if self.var_use_cython.get():
            self.var_use_cython.set(True)
            self.var_use_nuitka.set(False)
            self.var_use_pyarmor.set(False)
            self.project.use_nuitka = False
            self.project.use_pyarmor = False
            self.project.use_cython = True
            self.toggle_pyarmor_fields()
            self.win.destroy()
            cython_editor = CythonEditor(self.master, self.project)
            if cython_editor.show() and self.app:
                self.app._refresh_tree()

    def on_use_pyarmor_toggle(self):
        if self.var_use_pyarmor.get():
            self.var_use_nuitka.set(False)
            self.var_use_cython.set(False) 
            self.project.use_nuitka = False
            self.project.use_cython = False  
        self.toggle_pyarmor_fields()
        
    def _enforce_exclusivity(self):
        """Erzwingt gegenseitige Exklusivität der Compiler-Optionen."""
        # Jetzt 3-Wege-Exklusivität
        if (
            self.var_use_pyarmor.get() and self.var_use_nuitka.get()
        ) or (
            self.var_use_pyarmor.get() and self.var_use_cython.get()
        ) or (
            self.var_use_nuitka.get() and self.var_use_cython.get()
        ):
            # Nur die zuletzt aktivierte behalten
            if self.var_use_cython.get():
                self.var_use_nuitka.set(False)
                self.var_use_pyarmor.set(False)
                self.project.use_nuitka = False
                self.project.use_pyarmor = False
            elif self.var_use_nuitka.get():
                self.var_use_pyarmor.set(False)
                self.var_use_cython.set(False)
                self.project.use_pyarmor = False
                self.project.use_cython = False
            elif self.var_use_pyarmor.get():
                self.var_use_nuitka.set(False)
                self.var_use_cython.set(False)
                self.project.use_nuitka = False
                self.project.use_cython = False
        self.toggle_pyarmor_fields()

    def show(self):
        self.x = 860
        self.y = 560
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
        r_console = ttk.Radiobutton(check_frame_top, text=self.texts["console_label"], variable=self.var_console_mode, value=True)
        r_console.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        r_windowed = ttk.Radiobutton(check_frame_top, text=self.texts["windowed_label"], variable=self.var_console_mode, value=False)
        r_windowed.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        
        
        pytest_cb = ttk.Checkbutton(
            check_frame_top, text="Use Pytest",
            variable=self.var_use_pytest,
            command=self.on_use_pytest_toggle 
        )
        pytest_cb.grid(row=0, column=6, padx=5, pady=2, sticky="w")

        sphinx_cb = ttk.Checkbutton(
            check_frame_top, text="Use Sphinx",
            variable=self.var_use_sphinx,
            command=self.on_use_sphinx_toggle
        )
        sphinx_cb.grid(row=0, column=7, padx=5, pady=2, sticky="w")

        self.var_use_pyarmor = tk.BooleanVar(value=self.project.use_pyarmor)
        pyarmor_cb = ttk.Checkbutton(check_frame_top, text="Use PyArmor", variable=self.var_use_pyarmor, command=self.on_use_pyarmor_toggle)
        pyarmor_cb.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        
        self.var_use_nuitka = tk.BooleanVar(value=self.project.use_nuitka)
        nuitka_cb = ttk.Checkbutton(check_frame_top, text="Use Nuitka", variable=self.var_use_nuitka, command=self.on_use_nuitka_toggle)
        nuitka_cb.grid(row=0, column=4, padx=5, pady=2, sticky="w")
        
        # NEU: Cython Checkbutton
        self.var_use_cython = tk.BooleanVar(value=getattr(self.project, "use_cython", False))
        cython_cb = ttk.Checkbutton(check_frame_top, text="Use Cython", variable=self.var_use_cython, command=self.on_use_cython_toggle)
        cython_cb.grid(row=0, column=5, padx=5, pady=2, sticky="w")

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

        self.e_name, self.l_name = create_entry_row(self.texts["name_label"], 1, self.project.name)
        self.e_script, self.l_script = create_entry_row("Script:", 2, self.project.script, file_button=True)
        self.e_output, self.l_output = create_entry_row(self.texts["output_label"], 3, self.project.output, directory=True)
        self.e_icon, self.l_icon = create_entry_row(self.texts["icon_label"], 4, self.project.icon, file_button=True)
        self.e_add, self.l_add = create_entry_row(self.texts["add_data_label"], 5, self.project.add_data)

        separator = ttk.Separator(form_frame, orient="horizontal")
        separator.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)

        self.e_hidden, self.l_hidden = create_entry_row(self.texts["hidden_imports_label"], 7, self.project.hidden_imports)
        self.e_version, self.l_version = create_entry_row(self.texts["version_label"], 8, self.project.version, file_button=True)
        self.e_runtime_hook, self.l_runtime_hook = create_entry_row(self.texts["runtime_hook_label"], 9, self.project.runtime_hook, file_button=True)
        self.e_splash, self.l_splash = create_entry_row(self.texts["splash_label"], 10, self.project.splash, file_button=True)
        self.e_spec_file, self.l_spec_file = create_entry_row(self.texts["spec_file_label"], 11, self.project.spec_file, file_button=True)
        self.e_pyarmor_runtime_dir, self.l_pyarmor_runtime_dir = create_entry_row("PyArmor Runtime-Ordner:", 12, self.project.pyarmor_runtime_dir, directory=True)
        self.e_pyarmor_dist_dir, self.l_pyarmor_dist_dir = create_entry_row("PyArmor Dist-Ordner:", 13, self.project.pyarmor_dist_dir, directory=True)
        self.e_pyarmor_command, self.l_pyarmor_command = create_entry_row("PyArmor-Befehl:", 14, self.project.pyarmor_command)
        self.e_pyarmor_options, self.l_pyarmor_options = create_entry_row("PyArmor Optionen:", 15, "")

        # Ausblenden der PyArmor-Felder, wenn nicht aktiviert
        if not self.var_use_pyarmor.get():
            self.e_pyarmor_runtime_dir.master.grid_remove()
            self.l_pyarmor_runtime_dir.grid_remove()
            self.e_pyarmor_dist_dir.master.grid_remove()
            self.l_pyarmor_dist_dir.grid_remove()
            self.e_pyarmor_command.master.grid_remove()
            self.l_pyarmor_command.grid_remove()
            self.e_pyarmor_options.master.grid_remove()
            self.l_pyarmor_options.grid_remove()

        check_frame_bottom = ttk.Frame(form_frame)
        check_frame_bottom.grid(row=16, column=0, columnspan=2, pady=5, sticky="w")

        self.var_upx = tk.BooleanVar(value=self.project.upx)
        c_upx = ttk.Checkbutton(check_frame_bottom, text=self.texts["upx_label"], variable=self.var_upx)
        c_upx.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.var_debug = tk.BooleanVar(value=self.project.debug)
        c_debug = ttk.Checkbutton(check_frame_bottom, text=self.texts["debug_label"], variable=self.var_debug)
        c_debug.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.var_clean = tk.BooleanVar(value=self.project.clean)
        c_clean = ttk.Checkbutton(check_frame_bottom, text=self.texts["clean_label"], variable=self.var_clean)
        c_clean.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.var_strip = tk.BooleanVar(value=self.project.strip)
        c_strip = ttk.Checkbutton(check_frame_bottom, text=self.texts["strip_label"], variable=self.var_strip)
        c_strip.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.var_no_runtime_key = tk.BooleanVar(value=self.project.no_runtime_key)
        c_no_key = ttk.Checkbutton(check_frame_bottom, text="Ohne Runtime Key", variable=self.var_no_runtime_key)
        c_no_key.grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.var_exclude_tcl = tk.BooleanVar(value=self.project.exclude_tcl)
        c_tcl = ttk.Checkbutton(check_frame_bottom, text="Tcl deaktivieren", variable=self.var_exclude_tcl)
        c_tcl.grid(row=0, column=5, padx=5, pady=2, sticky="w")
        self.var_include_pyarmor_runtime = tk.BooleanVar(value=self.project.include_pyarmor_runtime)
        c_include_runtime = ttk.Checkbutton(check_frame_bottom, text="Include PyArmor-Runtime", variable=self.var_include_pyarmor_runtime, command=self.toggle_runtime_field)
        c_include_runtime.grid(row=0, column=6, padx=5, pady=2, sticky="w")
        CreateToolTip(c_include_runtime, "Bindet die PyArmor-Laufzeitbibliothek ein, wenn ein verschlüsseltes Skript kompiliert wird.")

        self.pyinstaller_widgets = [
            self.e_icon.master, self.l_icon, self.e_add.master, self.l_add,
            self.e_hidden.master, self.l_hidden, self.e_runtime_hook.master, self.l_runtime_hook,
            self.e_splash.master, self.l_splash, self.e_spec_file.master, self.l_spec_file,
            self.e_pyarmor_runtime_dir.master, self.l_pyarmor_runtime_dir,
            c_onefile, r_console, r_windowed, c_upx, c_debug, c_clean, c_strip, c_include_runtime
        ]

        self.security_frame = ttk.LabelFrame(form_frame, text="Security Level")
        self.security_frame.grid(row=18, column=0, columnspan=2, pady=5, sticky="ew")
        ttk.Button(self.security_frame, text="Easy", command=lambda: self.set_security_level("Easy")).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Medium", command=lambda: self.set_security_level("Medium")).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Hard", command=lambda: self.set_security_level("Hard")).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Ultra", command=lambda: self.set_security_level("Ultra")).grid(row=0, column=3, padx=5, pady=2)

        self.pyarmor_frame = ttk.LabelFrame(form_frame, text="PyArmor Erweiterte Optionen")
        self.pyarmor_frame.grid(row=19, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.pyarmor_frame.grid_columnconfigure(0, weight=1)
        self.pyarmor_frame.grid_columnconfigure(1, weight=1)

        self.var_obf_code = tk.StringVar(value=self.project.pyarmor_obf_code or "1")
        ttk.Label(self.pyarmor_frame, text="Obf-Code (Obfuscation level):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        ttk.Combobox(self.pyarmor_frame, textvariable=self.var_obf_code, values=["0", "1", "2"], width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.var_mix_str = tk.BooleanVar(value=self.project.pyarmor_mix_str)
        ttk.Checkbutton(self.pyarmor_frame, text="Mix-Str (Mix strings to make them unreadable)", variable=self.var_mix_str).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.var_private = tk.BooleanVar(value=self.project.pyarmor_private)
        ttk.Checkbutton(self.pyarmor_frame, text="Private (Add extra protection for functions)", variable=self.var_private).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.var_restrict = tk.BooleanVar(value=self.project.pyarmor_restrict)
        ttk.Checkbutton(self.pyarmor_frame, text="Restrict (Restrict usage to protect intellectual property)", variable=self.var_restrict).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.var_assert_import = tk.BooleanVar(value=self.project.pyarmor_assert_import)
        ttk.Checkbutton(self.pyarmor_frame, text="Assert-Import (Check integrity of imported modules)", variable=self.var_assert_import).grid(row=1, column=2, columnspan=2, sticky="w", padx=5, pady=2)

        self.var_assert_call = tk.BooleanVar(value=self.project.pyarmor_assert_call)
        ttk.Checkbutton(self.pyarmor_frame, text="Assert-Call (Check function call integrity)", variable=self.var_assert_call).grid(row=2, column=2, columnspan=2, sticky="w", padx=5, pady=2)

        ttk.Label(self.pyarmor_frame, text="Platform (Target platform):").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.e_platform = ttk.Entry(self.pyarmor_frame, width=30)
        self.e_platform.insert(0, self.project.pyarmor_platform)
        self.e_platform.grid(row=4, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(self.pyarmor_frame, text="Pack (Packaging method):").grid(row=4, column=2, sticky="e", padx=5, pady=2)
        self.var_pack = tk.StringVar(value=self.project.pyarmor_pack or "")
        ttk.Combobox(self.pyarmor_frame, textvariable=self.var_pack, values=["", "onefile", "onedir"], width=10).grid(row=4, column=3, sticky="w", padx=5, pady=2)

        ttk.Label(self.pyarmor_frame, text="Expired (yyyy-mm-dd) (Set expiry date):").grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.e_expired = ttk.Entry(self.pyarmor_frame, width=30)
        self.e_expired.insert(0, self.project.pyarmor_expired or "")
        self.e_expired.grid(row=5, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(self.pyarmor_frame, text="Bind-Device (Lock to hardware ID):").grid(row=5, column=2, sticky="e", padx=5, pady=2)
        self.e_bind_device = ttk.Entry(self.pyarmor_frame, width=30)
        self.e_bind_device.insert(0, self.project.pyarmor_bind_device or "")
        self.e_bind_device.grid(row=5, column=3, sticky="w", padx=5, pady=2)

        ttk.Label(form_frame, text=self.texts["options_label"]).grid(row=17, column=0, sticky="ne", pady=5)
        self.txt_options = scrolledtext.ScrolledText(form_frame, width=50, height=4, font=("Segoe UI", 10))
        self.txt_options.grid(row=17, column=1, pady=5, sticky="ew")
        self.txt_options.insert(tk.END, self.project.options)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=20, column=0, columnspan=2, pady=10)
        cancel_btn = ttk.Button(button_frame, text=self.texts["tooltip_cancel_project"].split(".")[0], command=self.win.destroy)
        cancel_btn.grid(row=0, column=0, padx=5, pady=5)
        analyze_btn = ttk.Button(button_frame, text="Analyse", command=self.analyze_inputs)
        analyze_btn.grid(row=0, column=1, padx=5, pady=5)
        save_btn = ttk.Button(button_frame, text=self.texts["tooltip_save_project"].split(".")[0], command=self.save, style="Accent.TButton")
        save_btn.grid(row=0, column=2, padx=5, pady=5)
        help_btn = ttk.Button(button_frame, text="❓Help", command=lambda: show_edit_helper(self.win))
        help_btn.grid(row=0, column=3, padx=5, pady=5)

        CreateToolTip(save_btn, self.texts["tooltip_save_project"])
        CreateToolTip(cancel_btn, self.texts["tooltip_cancel_project"])
        CreateToolTip(analyze_btn, "Analysiert sicherheitskritische Eingaben wie Ordnerstrukturen.")

        self._enforce_exclusivity()
        
        
        #if getattr(self.project, "use_pytest", False):
         #   self.on_use_pytest_toggle()
        #elif getattr(self.project, "use_sphinx", False):
        #    self.on_use_sphinx_toggle()

        if getattr(self.project, "use_cython", False):
            self.on_use_cython_toggle()
        elif self.project.use_nuitka:
            self.on_use_nuitka_toggle()
        else:
            self.toggle_pyarmor_fields()
        if self.win and self.win.winfo_exists():
            self.win.wait_window()

        return self.saved

    def toggle_runtime_field(self):
        if self.var_include_pyarmor_runtime.get():
            self.e_pyarmor_runtime_dir.master.grid()
            self.l_pyarmor_runtime_dir.grid()
        else:
            self.e_pyarmor_runtime_dir.master.grid_remove()
            self.l_pyarmor_runtime_dir.grid_remove()
        
        self.win.update_idletasks()
        self.win.geometry(f"{self.win.winfo_reqwidth()}x{self.win.winfo_reqheight()}")

    def toggle_pyarmor_fields(self):
        if self.var_use_pyarmor.get():
            for w in self.pyinstaller_widgets:
                w.grid_remove()
            self.e_pyarmor_dist_dir.master.grid()
            self.l_pyarmor_dist_dir.grid()
            self.e_pyarmor_command.master.grid()
            self.l_pyarmor_command.grid()
            self.e_pyarmor_options.master.grid()
            self.l_pyarmor_options.grid()
            self.pyarmor_frame.grid()
            self.security_frame.grid()
        else:
            for w in self.pyinstaller_widgets:
                w.grid()
            self.e_pyarmor_dist_dir.master.grid_remove()
            self.l_pyarmor_dist_dir.grid_remove()
            self.e_pyarmor_command.master.grid_remove()
            self.l_pyarmor_command.grid_remove()
            self.e_pyarmor_options.master.grid_remove()
            self.l_pyarmor_options.grid_remove()
            self.pyarmor_frame.grid_remove()
            self.security_frame.grid_remove()

        self.win.update_idletasks()
        self.win.geometry(f"{self.win.winfo_reqwidth()}x{self.win.winfo_reqheight()}")

        self.toggle_runtime_field()

    def analyze_inputs(self):
        issues = []

        script_path = self.e_script.get().strip()
        output_path = self.e_output.get().strip()
        pyarmor_runtime_dir = self.e_pyarmor_runtime_dir.get().strip()
        pyarmor_dist_dir = self.e_pyarmor_dist_dir.get().strip()
        pyarmor_command = self.e_pyarmor_command.get().strip()
        pyarmor_expired = self.e_expired.get().strip()

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

        if self.var_use_pyarmor.get():
            if pyarmor_command not in ["gen", "pack", "obfuscate"]:
                issues.append(f"Ungültiger PyArmor-Befehl: {pyarmor_command}")
            if pyarmor_expired:
                try:
                    datetime.strptime(pyarmor_expired, "%Y-%m-%d")
                except ValueError:
                    issues.append(f"Ungültiges Ablaufdatum: {pyarmor_expired} (Format: yyyy-mm-dd)")
            if self.var_include_pyarmor_runtime.get() and not pyarmor_runtime_dir:
                issues.append("PyArmor Runtime-Ordner muss angegeben werden, wenn Laufzeitbibliothek eingebunden wird.")
            if self.var_include_pyarmor_runtime.get():
                runtime_path = Path(pyarmor_runtime_dir) / "pyarmor_runtime_000000"
                if not runtime_path.is_dir():
                    issues.append(f"PyArmor-Laufzeitbibliothek nicht gefunden in: {runtime_path}")
            if pyarmor_dist_dir and not Path(pyarmor_dist_dir).exists():
                issues.append(f"Hinweis: PyArmor output directory {pyarmor_dist_dir} existiert noch nicht (wird beim Kompilieren erstellt).")

        if issues:
            messagebox.showwarning("Analyse-Ergebnis", "\n".join(issues))
        else:
            messagebox.showinfo("Analyse-Ergebnis", "Keine sicherheitskritischen Probleme gefunden!")

    def set_security_level(self, level):
        self.e_pyarmor_options.delete(0, tk.END)
        if level == "Easy":
            self.var_obf_code.set("1")
            self.var_mix_str.set(False)
            self.var_private.set(False)
            self.var_restrict.set(False)
            self.var_assert_import.set(False)
            self.var_assert_call.set(False)
        elif level == "Medium":
            self.var_obf_code.set("1")
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_restrict.set(False)
            self.var_assert_import.set(False)
            self.var_assert_call.set(False)
        elif level == "Hard":
            self.var_obf_code.set("2")
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_restrict.set(True)
            self.var_assert_import.set(True)
            self.var_assert_call.set(True)
            messagebox.showinfo("⚠️WARNING:", "Hard Security Level can cause runtime errors if imports or calls are not correct.")
        elif level == "Ultra":
            self.var_obf_code.set("2")
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_restrict.set(True)
            self.var_assert_import.set(True)
            self.var_assert_call.set(True)
            self.e_pyarmor_options.delete(0, tk.END)
            self.e_pyarmor_options.insert(0, "--enable-rft --enable-bcc --enable-jit --enable-themida")
            messagebox.showwarning(
                "⚠️WARNING",
                (
                    "These options significantly increase security but may affect performance.\n"
                    "Use them with caution!"
                    "⚠️This Ultra Security Level enables the following advanced PyArmor options:\n\n"
                    "  • --enable-rft: Runtime Function Transform for higher obfuscation.\n"
                    "  • --enable-bcc: Transforms Python code into C to make reverse engineering harder.\n"
                    "  • --enable-jit: Just-In-Time protection for dynamic runtime security.\n"
                    "  • --enable-themida: Uses Themida for extreme protection (Windows only).\n\n"
                    "Note: These options significantly increase security but may affect performance."
                )
            )

    def _choose_file(self, entry, directory=False, filetypes=None):
        if directory:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=filetypes or [("All Files", "*.*")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def save(self):
        p = self.project
        if not hasattr(self, 'txt_options') or self.txt_options is None:
            p.options = ""
        else:
            p.options = self.txt_options.get("1.0", tk.END).strip()

        p.name = self.e_name.get() or (Path(p.script).stem if p.script else "")
        p.script = self.e_script.get()
        p.icon = self.e_icon.get()

        valid_add_data = []
        for entry in self.e_add.get().split(";"):
            entry = entry.strip()
            if not entry:
                continue
            if ":" not in entry:
                messagebox.showinfo("Warnung", f"Ungültiger add_data-Eintrag: '{entry}' (Format: src:dest)")
                continue
            src, dest = entry.split(":", 1)
            src_path = Path(src)
            if not src_path.exists():
                messagebox.showwarning("Warnung", f"Ungültiger add_data-Eintrag: '{src}' existiert nicht.")
                continue
            valid_add_data.append(f"{src}:{dest}")
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
        p.runtime_hook = self.e_runtime_hook.get()
        p.splash = self.e_splash.get()
        p.spec_file = self.e_spec_file.get()

        # Gegenseitigen Ausschluss sicherstellen:
        if self.var_use_nuitka.get():
            p.use_nuitka = True
            p.use_pyarmor = False
            p.use_cython = False
        elif self.var_use_pyarmor.get():
            p.use_pyarmor = True
            p.use_nuitka = False
            p.use_cython = False
        elif self.var_use_cython.get():
            p.use_cython = True
            p.use_nuitka = False
            p.use_pyarmor = False
        else:
            p.use_nuitka = False
            p.use_pyarmor = False
            p.use_cython = False

        p.no_runtime_key = self.var_no_runtime_key.get()
        p.exclude_tcl = self.var_exclude_tcl.get()
        p.include_pyarmor_runtime = self.var_include_pyarmor_runtime.get()
        p.pyarmor_runtime_dir = self.e_pyarmor_runtime_dir.get()
        p.pyarmor_command = self.e_pyarmor_command.get()
        p.pyarmor_obf_code = self.var_obf_code.get()
        p.pyarmor_mix_str = self.var_mix_str.get()
        p.pyarmor_private = self.var_private.get()
        p.pyarmor_restrict = self.var_restrict.get()
        p.pyarmor_assert_import = self.var_assert_import.get()
        p.pyarmor_assert_call = self.var_assert_call.get()
        p.pyarmor_platform = self.e_platform.get()
        p.pyarmor_pack = self.var_pack.get()
        p.pyarmor_expired = self.e_expired.get()
        p.pyarmor_bind_device = self.e_bind_device.get()
        
        p.use_pytest = self.var_use_pytest.get()
        p.use_sphinx = self.var_use_sphinx.get()

        if p.script and not Path(p.script).suffix.lower() == ".py":
            messagebox.showerror("Fehler", f"Ungültiges Skript: {p.script} (muss .py sein)")
            return

        if p.use_pyarmor:
            valid_commands = ["gen", "pack", "obfuscate"]
            if p.pyarmor_command not in valid_commands:
                messagebox.showerror("Fehler", f"Ungültiger PyArmor-Befehl: {p.pyarmor_command}")
                return
            if p.pyarmor_expired:
                try:
                    datetime.strptime(p.pyarmor_expired, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Fehler", f"Ungültiges Ablaufdatum: {p.pyarmor_expired} (Format: yyyy-mm-dd)")
                    return
            if p.pyarmor_restrict or p.pyarmor_assert_import or p.pyarmor_assert_call:
                messagebox.showwarning("Warnung", "Restriktive PyArmor-Optionen können Laufzeitfehler verursachen.")

            if not p.pyarmor_dist_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                p.pyarmor_dist_dir = str(Path("dist") / f"{p.name}_{timestamp}")

            pyarmor_opts = []

            if p.pyarmor_obf_code:
                pyarmor_opts.extend(["--obf-code", p.pyarmor_obf_code])
            if p.pyarmor_mix_str:
                pyarmor_opts.append("--mix-str")
            if p.pyarmor_private:
                pyarmor_opts.append("--private")
            if p.pyarmor_restrict:
                pyarmor_opts.append("--restrict")
            if p.pyarmor_assert_import:
                pyarmor_opts.append("--assert-import")
            if p.pyarmor_assert_call:
                pyarmor_opts.append("--assert-call")
            if p.pyarmor_platform:
                pyarmor_opts.extend(["--platform", p.pyarmor_platform])
            if p.pyarmor_pack:
                pyarmor_opts.extend(["--pack", p.pyarmor_pack])
            if p.pyarmor_expired:
                pyarmor_opts.extend(["--expire", p.pyarmor_expired])
            if p.pyarmor_bind_device:
                pyarmor_opts.extend(["--bind-disk", p.pyarmor_bind_device])
            user_options = self.e_pyarmor_options.get().strip()
            if user_options:
                pyarmor_opts.extend(user_options.split())
            if "--output" not in " ".join(pyarmor_opts):
                pyarmor_opts.extend(["--output", p.pyarmor_dist_dir])
            p.pyarmor_options = " ".join(pyarmor_opts)
        else:
            p.pyarmor_dist_dir = ""

        if not p.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            p.output = str(Path("dist") / f"{p.name}_{timestamp}")

        self.saved = True
        self.win.destroy()
