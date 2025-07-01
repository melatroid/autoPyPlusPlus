import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from .gcceditor import GCCEditor  # Import hier ganz oben

class CythonEditor:
    def __init__(self, master, project):
        self.master = master
        self.project = project
        self.saved = False
        self.win = None

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Cython Compilation Editor")
        self.win.geometry("1200x650")
        self.win.transient(self.master)
        self.win.grab_set()

        # Menüleiste mit Einträgen für Zusatzdateien
        menubar = tk.Menu(self.win)
        self.win.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Files for build", menu=file_menu)
        file_menu.add_command(label="Add a build File", command=self.add_additional_files)
        file_menu.add_command(label="Delete a build File", command=self.remove_selected_files)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.on_cancel)

        main_frame = ttk.Frame(self.win, padding=10)
        main_frame.pack(fill="both", expand=True)

        # ----------- 3 Spalten (Haupt-Gruppen) --------------------
        # 1. Standardoptionen (links)
        stdopt_frame = ttk.LabelFrame(main_frame, text="Cython Options", padding=(12,8))
        stdopt_frame.grid(row=0, column=0, sticky="nswe", padx=(0, 10), pady=4, ipadx=3, ipady=3)

        # 2. Erweiterte Optionen (Mitte)
        adv_frame = ttk.LabelFrame(main_frame, text="Cython Settings", padding=(12,8))
        adv_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=4, ipadx=3, ipady=3)

        # 3. Datei- und Advanced-Eingaben (rechts)
        file_frame = ttk.LabelFrame(main_frame, text="File & Advanced Settings", padding=(12,8))
        file_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0), pady=4, ipadx=3, ipady=3)
        main_frame.grid_columnconfigure(2, weight=1)  # Rechts dehnbar
        main_frame.grid_rowconfigure(0, weight=0)

        # ------- Links: Standardoptionen (Checkboxen, Language) -------
        self.var_use_cython = tk.BooleanVar(value=getattr(self.project, "use_cython", True))
        ttk.Checkbutton(stdopt_frame, text="Use Cython", variable=self.var_use_cython).pack(anchor="w", pady=2)

        self.var_use_cpp = tk.BooleanVar(value=getattr(self.project, "use_cpp", False))
        cb_use_cpp = ttk.Checkbutton(stdopt_frame, text="Use GCC Pipeline", variable=self.var_use_cpp)
        cb_use_cpp.pack(anchor="w", pady=2)

        self.var_boundscheck = tk.BooleanVar(value=getattr(self.project, "cython_boundscheck", False))
        ttk.Checkbutton(stdopt_frame, text="Boundscheck (Array index check)", variable=self.var_boundscheck).pack(anchor="w", pady=2)

        self.var_wraparound = tk.BooleanVar(value=getattr(self.project, "cython_wraparound", False))
        ttk.Checkbutton(stdopt_frame, text="Wraparound (allow negative indices)", variable=self.var_wraparound).pack(anchor="w", pady=2)

        self.var_nonecheck = tk.BooleanVar(value=getattr(self.project, "cython_nonecheck", False))
        ttk.Checkbutton(stdopt_frame, text="Nonecheck (None check on objects)", variable=self.var_nonecheck).pack(anchor="w", pady=2)

        self.var_cdivision = tk.BooleanVar(value=getattr(self.project, "cython_cdivision", True))
        ttk.Checkbutton(stdopt_frame, text="C Division (fast division)", variable=self.var_cdivision).pack(anchor="w", pady=2)

        self.var_keep_pyx = tk.BooleanVar(value=getattr(self.project, "cython_keep_pyx", True))
        ttk.Checkbutton(stdopt_frame, text="Keep .pyx file after build", variable=self.var_keep_pyx).pack(anchor="w", pady=2)

        ttk.Separator(stdopt_frame, orient="horizontal").pack(fill="x", pady=7)

        ttk.Label(stdopt_frame, text="Language Level:").pack(anchor="w", pady=(4,0))
        self.var_language_level = tk.StringVar(value=str(getattr(self.project, "cython_language_level", 3)))
        ttk.Combobox(stdopt_frame, textvariable=self.var_language_level, values=["2", "3"], width=5, state="readonly").pack(anchor="w", pady=2)

        ttk.Label(stdopt_frame, text="Language (C/C++):").pack(anchor="w", pady=(7,0))
        self.var_language = tk.StringVar(value=getattr(self.project, "cython_language", "c"))
        ttk.Combobox(stdopt_frame, textvariable=self.var_language, values=["c", "c++"], width=6, state="readonly").pack(anchor="w", pady=2)

        # ------- Mitte: Erweiterte Checkboxen -------
        self.var_build_with_setup = tk.BooleanVar(value=getattr(self.project, "cython_build_with_setup", True))
        ttk.Checkbutton(adv_frame, text="After run, build with setup.py?", variable=self.var_build_with_setup).pack(anchor="w", pady=2)

        self.var_profile = tk.BooleanVar(value=getattr(self.project, "cython_profile", False))
        ttk.Checkbutton(adv_frame, text="Profiling (cython_profile)", variable=self.var_profile).pack(anchor="w", pady=2)

        self.var_linemap = tk.BooleanVar(value=getattr(self.project, "cython_linemap", False))
        ttk.Checkbutton(adv_frame, text="Linemap (cython_linemap)", variable=self.var_linemap).pack(anchor="w", pady=2)

        self.var_gdb = tk.BooleanVar(value=getattr(self.project, "cython_gdb", False))
        ttk.Checkbutton(adv_frame, text="GDB-Debug (cython_gdb)", variable=self.var_gdb).pack(anchor="w", pady=2)

        self.var_embedsignature = tk.BooleanVar(value=getattr(self.project, "cython_embedsignature", False))
        ttk.Checkbutton(adv_frame, text="Embedsignature (Function signature in doc)", variable=self.var_embedsignature).pack(anchor="w", pady=2)

        self.var_cplus_exceptions = tk.BooleanVar(value=getattr(self.project, "cython_cplus_exceptions", False))
        ttk.Checkbutton(adv_frame, text="C++ Exceptions (cython_cplus_exceptions)", variable=self.var_cplus_exceptions).pack(anchor="w", pady=2)

        self.var_cpp_locals = tk.BooleanVar(value=getattr(self.project, "cython_cpp_locals", False))
        ttk.Checkbutton(adv_frame, text="C++ Locals (cython_cpp_locals)", variable=self.var_cpp_locals).pack(anchor="w", pady=2)

        self.var_annotate = tk.BooleanVar(value=getattr(self.project, "cython_annotate", False))
        ttk.Checkbutton(adv_frame, text="Annotate (HTML analysis)", variable=self.var_annotate).pack(anchor="w", pady=2)

        ttk.Separator(adv_frame, orient="horizontal").pack(fill="x", pady=7)

        ttk.Label(adv_frame, text="Target OS:").pack(anchor="w", pady=(3,0))
        self.var_target_os = tk.StringVar(value=getattr(self.project, "cython_target_os", "auto"))
        ttk.Combobox(adv_frame, textvariable=self.var_target_os, values=["auto", "windows", "linux", "macos"], width=10, state="readonly").pack(anchor="w", pady=2)

        # ------- Rechts: Datei- und Advanced-Settings -------
        def add_entry_row(label_text, var_text, row, btn_command=None, entry_width=46, filetypes=None):
            ttk.Label(file_frame, text=label_text).grid(row=row, column=0, sticky="e", pady=2, padx=(0, 3))
            entry = ttk.Entry(file_frame, width=entry_width)
            entry.insert(0, var_text)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
            if btn_command:
                ttk.Button(file_frame, text="...", command=lambda: btn_command(entry, filetypes)).grid(row=row, column=2, padx=5, pady=2)
            return entry

        self.e_script = add_entry_row("Source file (.py/.pyx):", getattr(self.project, "script", ""), 0, self._choose_file, filetypes=[("Python/Cython files", "*.py *.pyx")])
        self.e_icon = add_entry_row("Icon (.ico):", getattr(self.project, "icon", ""), 1, self._choose_file, filetypes=[("Icon files", "*.ico")])
        self.e_output = add_entry_row("Output folder:", getattr(self.project, "cython_output_dir", ""), 2, self._choose_dir)
        self.e_setup_py = add_entry_row("setup.py path (optional):", getattr(self.project, "cython_setup_py", "setup.py"), 3, self._choose_file, filetypes=[("Python setup file", "*.py")])

        self.e_include_dirs = add_entry_row(
            "Include Dirs (comma separated):",
            ", ".join(getattr(self.project, "cython_include_dirs", [])),
            4
        )

        directives_dict = getattr(self.project, "cython_directives", {}) or {}
        directives_str = ",".join(f"{k}={v}" for k, v in directives_dict.items())
        self.e_directives = add_entry_row(
            "Directives (key=val,key2=val2):",
            directives_str,
            5
        )

        self.e_compile_time_env = add_entry_row(
            "Compile-Time Env (key=val,key2=val2):",
            ",".join(f"{k}={v}" for k, v in (getattr(self.project, "cython_compile_time_env", {}) or {}).items()),
            6
        )

        self.e_extra_compile_args = add_entry_row(
            "Extra Compile Args (comma separated):",
            ", ".join(getattr(self.project, "cython_extra_compile_args", [])),
            7
        )
        self.e_extra_link_args = add_entry_row(
            "Extra Link Args (comma separated):",
            ", ".join(getattr(self.project, "cython_extra_link_args", [])),
            8
        )

        file_frame.grid_columnconfigure(1, weight=1)

        # --------------- Untere Zeile: Dateien, Security, Buttons ----------------
        # Zusatzdateien
        additional_files_frame = ttk.LabelFrame(main_frame, text="Add files for your C++ build, like python310.dll or tkinter.dll\nneeded for build with gcc-compiler")
        additional_files_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(18,6), padx=3)
        additional_files_frame.grid_columnconfigure(0, weight=1)
        additional_files_frame.grid_rowconfigure(0, weight=1)

        self.files_listbox = tk.Listbox(additional_files_frame, height=6, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(additional_files_frame, orient="vertical", command=self.files_listbox.yview)
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        self.files_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        btn_frame = ttk.Frame(additional_files_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Button(btn_frame, text="Add any build files", command=self.add_additional_files).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete File", command=self.remove_selected_files).pack(side="left", padx=5)

        self._refresh_files_listbox()

        # Security Level
        self.security_frame = ttk.LabelFrame(main_frame, text="Security Level")
        self.security_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew", padx=(0, 8))
        ttk.Button(self.security_frame, text="Secure", command=lambda: self.set_security_level("Easy")).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Fast build", command=lambda: self.set_security_level("Hard")).grid(row=0, column=1, padx=5, pady=2)

        # Untere Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=2, sticky="e", pady=10, padx=(0, 6))

        ttk.Button(button_frame, text="Cancel all", command=self.on_cancel).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Analyse", command=self.analyze_inputs).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save all", command=self.save).pack(side="left", padx=5)

        # Button für GCCEditor nur anzeigen, wenn use_cpp True ist
        gcc_button = ttk.Button(button_frame, text="GCC Pipeline", command=self.open_gcc_editor)
        if self.var_use_cpp.get():
            gcc_button.pack(side="left", padx=5)

        # Automatisch Button anzeigen oder verstecken, wenn use_cpp toggled wird
        def toggle_gcc_button(*args):
            if self.var_use_cpp.get():
                gcc_button.pack(side="left", padx=5)
            else:
                gcc_button.pack_forget()
        self.var_use_cpp.trace_add("write", toggle_gcc_button)

        self.win.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.win.wait_window(self.win)
        return self.saved

    def open_gcc_editor(self):
        gcc_editor = GCCEditor(self.master, self.project)
        saved = gcc_editor.show()
        if saved:
            messagebox.showinfo("Info", "C++ settings updated.")

    def _refresh_files_listbox(self):
        self.files_listbox.delete(0, tk.END)
        for f in self.project.additional_files:
            self.files_listbox.insert(tk.END, f)

    def add_additional_files(self):
        paths = filedialog.askopenfilenames(
            title="Select additional files",
            filetypes=[("All files", "*.*")],
            initialdir=str(Path.cwd())
        )
        if not paths:
            return
        for p in paths:
            if p not in self.project.additional_files:
                self.project.additional_files.append(p)
        self._refresh_files_listbox()

    def remove_selected_files(self):
        selected_indices = list(self.files_listbox.curselection())
        if not selected_indices:
            messagebox.showinfo("Info", "Please select at least one file to remove.")
            return
        for index in reversed(selected_indices):
            del self.project.additional_files[index]
        self._refresh_files_listbox()

    def set_security_level(self, level):
        if level == "Easy":
            self.var_boundscheck.set(True)
            self.var_wraparound.set(True)
            self.var_cdivision.set(False)
            self.var_nonecheck.set(True)
            self.var_keep_pyx.set(True)
            self.var_language_level.set("3")
            self.var_language.set("c")
            messagebox.showinfo(
                "Security Level: Easy",
                "All security checks enabled for optimal debugging and error detection."
            )
        elif level == "Hard":
            self.var_boundscheck.set(False)
            self.var_wraparound.set(False)
            self.var_cdivision.set(True)
            self.var_nonecheck.set(False)
            self.var_keep_pyx.set(False)
            self.var_language_level.set("3")
            self.var_language.set("c")
            messagebox.showwarning(
                "Security Level: Hard",
                "All checks disabled! Maximum speed and harder to analyze bytecode.\n"
                "Warning: Unsafe indices, no None check, pyx file will be deleted."
            )

    def analyze_inputs(self):
        issues = []
        script = self.e_script.get().strip()
        output = self.e_output.get().strip()
        icon = self.e_icon.get().strip()
        language_level = self.var_language_level.get()

        if not script:
            issues.append("Source file is empty.")
        else:
            path = Path(script)
            if not path.exists():
                issues.append(f"Source file does not exist: {script}")
            elif not (path.suffix.lower() in [".py", ".pyx"]):
                issues.append(f"Source file must be .py or .pyx: {script}")

        if not output:
            issues.append("Output folder is empty.")
        else:
            output_path = Path(output)
            if output_path.exists() and not output_path.is_dir():
                issues.append(f"Output folder is not a directory: {output}")

        if icon:
            icon_path = Path(icon)
            if not icon_path.exists():
                issues.append(f"Icon file does not exist: {icon}")
            elif icon_path.suffix.lower() != ".ico":
                issues.append(f"Icon must be a .ico file: {icon}")

        if language_level not in ("2", "3"):
            issues.append(f"Language level is invalid: {language_level}")

        if issues:
            messagebox.showwarning("Analysis Result", "\n".join(issues))
        else:
            messagebox.showinfo("Analysis Result", "All required fields are filled and valid.\nNo critical issues found!")

    def save(self):
        p = self.project
        p.use_cython = self.var_use_cython.get()
        p.use_cpp = self.var_use_cpp.get()
        p.cython_boundscheck = self.var_boundscheck.get()
        p.cython_wraparound = self.var_wraparound.get()
        p.cython_nonecheck = self.var_nonecheck.get()
        p.cython_cdivision = self.var_cdivision.get()
        p.cython_language_level = int(self.var_language_level.get())
        p.cython_keep_pyx = self.var_keep_pyx.get()
        p.script = self.e_script.get().strip()
        p.icon = self.e_icon.get().strip()
        p.cython_output_dir = self.e_output.get().strip()
        p.cython_language = self.var_language.get()
        p.cython_profile = self.var_profile.get()
        p.cython_linemap = self.var_linemap.get()
        p.cython_gdb = self.var_gdb.get()
        p.cython_embedsignature = self.var_embedsignature.get()
        p.cython_cplus_exceptions = self.var_cplus_exceptions.get()
        p.cython_cpp_locals = self.var_cpp_locals.get()
        p.cython_annotate = self.var_annotate.get()
        p.cython_build_with_setup = self.var_build_with_setup.get()
        p.cython_target_os = self.var_target_os.get()
        p.cython_setup_py = self.e_setup_py.get().strip()
        p.cython_extra_compile_args = [s.strip() for s in self.e_extra_compile_args.get().split(",") if s.strip()]
        p.cython_extra_link_args = [s.strip() for s in self.e_extra_link_args.get().split(",") if s.strip()]
        p.cython_include_dirs = [s.strip() for s in self.e_include_dirs.get().split(",") if s.strip()]

        directives_str = self.e_directives.get().strip()
        directives_dict = {}
        if directives_str:
            for pair in directives_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    directives_dict[k.strip()] = v.strip()
        p.cython_directives = directives_dict

        compile_time_env_str = self.e_compile_time_env.get().strip()
        compile_time_env_dict = {}
        if compile_time_env_str:
            for pair in compile_time_env_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    compile_time_env_dict[k.strip()] = v.strip()
        p.cython_compile_time_env = compile_time_env_dict

        if p.use_cython:
            if not p.script:
                messagebox.showerror("Error", "Source file missing!")
                return
            if not (p.script.endswith(".py") or p.script.endswith(".pyx")):
                messagebox.showerror("Error", "Source file must be .py or .pyx!")
                return
            if not p.cython_output_dir:
                messagebox.showerror("Error", "Output folder is empty!")
                return

        self.saved = True
        if self.win:
            self.win.destroy()

    def on_cancel(self):
        self.saved = False
        if self.win:
            self.win.destroy()

    def _choose_file(self, entry, filetypes=None):
        path = filedialog.askopenfilename(filetypes=filetypes or [("All Files", "*.*")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _choose_dir(self, entry, _=None):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
