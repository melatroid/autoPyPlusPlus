import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from .help import show_nuitka_helper  # Import the Help dialog

class NuitkaEditor:
    def __init__(self, master, project, texts):
        self.master = master
        self.project = project
        self.texts = texts
        self.saved = False
        self.win = None

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Nuitka Compilation Editor")
        self.win.geometry("730x590")
        self.win.transient(self.master)
        self.win.grab_set()

        main_frame = ttk.Frame(self.win, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Left column: Checkboxes & Build-Type
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.grid(row=0, column=0, sticky="nw", padx=10)

        self.var_use_nuitka = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkbox_frame, text="Use Nuitka", variable=self.var_use_nuitka, command=self._enforce_exclusivity).pack(anchor="w", pady=2)

        # --- Build-Type selection (Radiobuttons) ---
        buildtype_frame = ttk.LabelFrame(checkbox_frame, text="Build Type")
        buildtype_frame.pack(anchor="w", pady=8, fill="x")

        self.var_buildtype = tk.StringVar(value=getattr(self.project, "nuitka_buildtype", "standalone"))
        ttk.Radiobutton(buildtype_frame, text="Standalone EXE (.exe, Folder)", variable=self.var_buildtype, value="standalone").pack(anchor="w")
        ttk.Radiobutton(buildtype_frame, text="Onefile EXE (.exe, Single file)", variable=self.var_buildtype, value="onefile").pack(anchor="w")
        ttk.Radiobutton(buildtype_frame, text="Python Module (.pyd/.so)", variable=self.var_buildtype, value="module").pack(anchor="w")
        ttk.Radiobutton(buildtype_frame, text="Windows DLL (.dll, rare)", variable=self.var_buildtype, value="windowsdll").pack(anchor="w")

        self.var_use_tkinter_plugin = tk.BooleanVar(value=getattr(self.project, "nuitka_tkinter_plugin", False))
        ttk.Checkbutton(checkbox_frame, text="Use TKinter", variable=self.var_use_tkinter_plugin).pack(anchor="w", pady=2)

        # Console/Windowed Mode
        ttk.Label(checkbox_frame, text="Mode:").pack(anchor="w", pady=(10, 0))
        self.var_console = tk.BooleanVar(value=self.project.console)
        r_console = ttk.Radiobutton(checkbox_frame, text="Console", variable=self.var_console, value=True)
        r_console.pack(anchor="w", pady=2)
        r_windowed = ttk.Radiobutton(checkbox_frame, text="Windowed", variable=self.var_console, value=False)
        r_windowed.pack(anchor="w", pady=2)

        self.var_debug = tk.BooleanVar(value=self.project.debug)
        ttk.Checkbutton(checkbox_frame, text="Show debug log", variable=self.var_debug).pack(anchor="w", pady=2)
        self.var_follow_imports = tk.BooleanVar(value=self.project.nuitka_follow_imports)
        ttk.Checkbutton(checkbox_frame, text="Follow Imports", variable=self.var_follow_imports).pack(anchor="w", pady=2)
        self.var_follow_stdlib = tk.BooleanVar(value=self.project.nuitka_follow_stdlib)
        ttk.Checkbutton(checkbox_frame, text="Follow Stdlib", variable=self.var_follow_stdlib).pack(anchor="w", pady=2)
        self.var_show_progress = tk.BooleanVar(value=self.project.nuitka_show_progress)
        ttk.Checkbutton(checkbox_frame, text="Show Progress", variable=self.var_show_progress).pack(anchor="w", pady=2)
        self.var_show_memory = tk.BooleanVar(value=self.project.nuitka_show_memory)
        ttk.Checkbutton(checkbox_frame, text="Show Memory", variable=self.var_show_memory).pack(anchor="w", pady=2)
        self.var_show_scons = tk.BooleanVar(value=self.project.nuitka_show_scons)
        ttk.Checkbutton(checkbox_frame, text="Show Scons", variable=self.var_show_scons).pack(anchor="w", pady=2)
        self.var_windows_uac_admin = tk.BooleanVar(value=self.project.nuitka_windows_uac_admin)
        ttk.Checkbutton(checkbox_frame, text="Windows UAC Admin", variable=self.var_windows_uac_admin).pack(anchor="w", pady=2)

        # Right column: Entry fields
        entry_frame = ttk.Frame(main_frame)
        entry_frame.grid(row=0, column=1, sticky="nsew", padx=10)

        def add_entry_row(label_text, var_text, row, btn_command=None, entry_width=50):
            ttk.Label(entry_frame, text=label_text).grid(row=row, column=0, sticky="e", pady=2)
            entry = ttk.Entry(entry_frame, width=entry_width)
            entry.insert(0, var_text)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
            if btn_command:
                ttk.Button(entry_frame, text="...", command=lambda: btn_command(entry)).grid(row=row, column=2, padx=5, pady=2)
            return entry

        self.e_plugins = add_entry_row("Plugins:", self.project.nuitka_plugins, 0)
        self.e_extra_opts = add_entry_row("Extra Options:", self.project.nuitka_extra_opts, 1)
        self.e_output_dir = add_entry_row("Output Dir:", self.project.nuitka_output_dir, 2, self._choose_dir)

        # Output Name field
        self._output_user_edited = False
        if self.project.name:
            default_output_name = f"{self.project.name}.exe"
        else:
            default_output_name = "output.exe"
        self.e_output_name = add_entry_row("Output Name:", default_output_name, 3)
        self.e_output_name.bind('<KeyRelease>', self._on_output_name_edited)
        if not self.e_output_name.get().strip():
            self.e_output_name.delete(0, tk.END)
            self.e_output_name.insert(0, default_output_name)

        ttk.Label(entry_frame, text="LTO:").grid(row=4, column=0, sticky="e", pady=2)
        self.var_lto = tk.StringVar(value=self.project.nuitka_lto or "auto")
        self.cmb_lto = ttk.Combobox(entry_frame, textvariable=self.var_lto, values=["auto", "yes", "no"], state="readonly", width=18)
        self.cmb_lto.grid(row=4, column=1, sticky="ew", pady=2)

        ttk.Label(entry_frame, text="Jobs:").grid(row=5, column=0, sticky="e", pady=2)
        self.var_jobs = tk.StringVar(value=str(self.project.nuitka_jobs or 1))
        self.cmb_jobs = ttk.Combobox(entry_frame, textvariable=self.var_jobs, values=["1", "2", "4", "8"], state="readonly", width=10)
        self.cmb_jobs.grid(row=5, column=1, sticky="ew", pady=2)

        self.e_windows_icon = add_entry_row("Windows Icon:", self.project.nuitka_windows_icon, 6, self._choose_file)
        self.e_windows_splash = add_entry_row("Windows Splash:", self.project.nuitka_windows_splash, 7, self._choose_file)

        entry_frame.grid_columnconfigure(1, weight=1)

        # Security Level Frame
        self.security_frame = ttk.LabelFrame(main_frame, text="Security Level")
        self.security_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(self.security_frame, text="Easy", command=lambda: self.set_security_level("Easy")).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Medium", command=lambda: self.set_security_level("Medium")).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Hard", command=lambda: self.set_security_level("Hard")).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Ultra", command=lambda: self.set_security_level("Ultra")).grid(row=0, column=3, padx=5, pady=2)

        # Bottom centered buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Analyze", command=self.analyze_inputs).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Help", command=lambda: show_nuitka_helper(self.win)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side="left", padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.win.wait_window(self.win)
        return self.saved

    def _on_output_name_edited(self, event=None):
        self._output_user_edited = True

    def set_output_name_from_project(self):
        if not self._output_user_edited:
            name = self.project.name
            ext = ".exe"
            if name:
                self.e_output_name.delete(0, tk.END)
                self.e_output_name.insert(0, f"{name}{ext}")

    def set_security_level(self, level):
        """Sets predefined settings for different security levels."""
        if level == "Easy":
            self.var_standalone.set(False)
            self.var_onefile.set(False)
            self.var_follow_imports.set(True)
            self.var_follow_stdlib.set(False)
            self.var_show_progress.set(False)
            self.var_show_memory.set(False)
            self.var_show_scons.set(False)
            self.var_windows_uac_admin.set(False)
            self.var_lto.set("no")
            self.var_jobs.set("1")
            self.e_plugins.delete(0, tk.END)
            self.e_plugins.insert(0, "")
            self.e_extra_opts.delete(0, tk.END)
            self.e_extra_opts.insert(0, "")

        elif level == "Medium":
            self.var_standalone.set(True)
            self.var_onefile.set(False)
            self.var_follow_imports.set(True)
            self.var_follow_stdlib.set(True)
            self.var_show_progress.set(False)
            self.var_show_memory.set(False)
            self.var_show_scons.set(False)
            self.var_windows_uac_admin.set(False)
            self.var_lto.set("auto")
            self.var_jobs.set("2")
            self.e_plugins.delete(0, tk.END)
            self.e_plugins.insert(0, "")
            self.e_extra_opts.delete(0, tk.END)
            self.e_extra_opts.insert(0, "")

        elif level == "Hard":
            self.var_standalone.set(True)
            self.var_onefile.set(True)
            self.var_follow_imports.set(True)
            self.var_follow_stdlib.set(True)
            self.var_show_progress.set(False)
            self.var_show_memory.set(False)
            self.var_show_scons.set(False)
            self.var_windows_uac_admin.set(True)
            self.var_lto.set("yes")
            self.var_jobs.set("4")
            self.e_plugins.delete(0, tk.END)
            self.e_plugins.insert(0, "--enable-plugin=obfuscation")
            self.e_extra_opts.delete(0, tk.END)
            self.e_extra_opts.insert(0, "--optimize")
            messagebox.showinfo("Warning", "Hard Level may cause runtime issues if plugins or options are incompatible.")

        elif level == "Ultra":
            self.var_standalone.set(True)
            self.var_onefile.set(True)
            self.var_follow_imports.set(True)
            self.var_follow_stdlib.set(True)
            self.var_show_progress.set(False)
            self.var_show_memory.set(False)
            self.var_show_scons.set(False)
            self.var_windows_uac_admin.set(True)
            self.var_lto.set("yes")
            self.var_jobs.set("8")
            self.e_plugins.delete(0, tk.END)
            self.e_plugins.insert(0, "--enable-plugin=obfuscation --enable-plugin=anti-debug")
            self.e_extra_opts.delete(0, tk.END)
            self.e_extra_opts.insert(0, "--enable-lto --optimize")
            messagebox.showwarning("⚠️ Warning", "Ultra Level may impact performance and cause errors. Use with caution!")

    def _enforce_exclusivity(self):
        if self.var_use_nuitka.get() and getattr(self.project, "use_pyarmor", False):
            self.project.use_pyarmor = False
            if hasattr(self.master, 'var_use_pyarmor'):
                self.master.var_use_pyarmor.set(False)

    def analyze_inputs(self):
        issues = []
        script_path = getattr(self.project, "script", "")
        if not script_path:
            issues.append("Script path is empty.")
        else:
            p = Path(script_path)
            if not p.exists():
                issues.append(f"Script path does not exist: {script_path}")
            elif not p.suffix.lower() == ".py":
                issues.append(f"Script file does not have .py extension: {script_path}")

        output_path = self.e_output_dir.get().strip()
        if not output_path:
            issues.append("Output directory is empty.")
        else:
            p_out = Path(output_path)
            if p_out.exists() and not p_out.is_dir():
                issues.append(f"Output directory is not a directory: {output_path}")

        try:
            jobs = int(self.var_jobs.get())
            if jobs not in (1, 2, 4, 8):
                issues.append("Jobs must be one of: 1, 2, 4, 8.")
        except ValueError:
            issues.append("Jobs must be a valid integer.")

        plugins = self.e_plugins.get().strip()
        if plugins and not plugins.startswith("--plugin-enable=") and not plugins.startswith("--enable-plugin="):
            issues.append("Plugins should start with '--plugin-enable=' or '--enable-plugin=', or be empty.")

        output_name = self.e_output_name.get().strip()
        if not output_name:
            issues.append("Output Name is empty.")
        # Check output extension based on build type
        buildtype = self.var_buildtype.get()
        if buildtype in ("standalone", "onefile"):
            if not output_name.endswith(".exe"):
                issues.append("Output Name should end with '.exe' (for Windows).")
        elif buildtype == "module":
            if not (output_name.endswith(".pyd") or output_name.endswith(".so")):
                issues.append("Output Name should end with '.pyd' or '.so' (for module build).")
        elif buildtype == "windowsdll":
            if not output_name.endswith(".dll"):
                issues.append("Output Name should end with '.dll' (for Windows DLL build).")

        if issues:
            messagebox.showwarning("Analysis Result", "\n".join(issues))
        else:
            messagebox.showinfo("Analysis Result", "No security-critical issues found!")

    def save(self):
        p = self.project
        p.use_nuitka = self.var_use_nuitka.get()
        # Build type
        buildtype = self.var_buildtype.get()
        p.nuitka_buildtype = buildtype
        p.nuitka_standalone = (buildtype == "standalone")
        p.nuitka_onefile = (buildtype == "onefile")
        p.nuitka_module = (buildtype == "module")
        p.nuitka_windowsdll = (buildtype == "windowsdll")

        p.console = self.var_console.get()
        p.nuitka_plugins = self.e_plugins.get().strip()
        p.nuitka_extra_opts = self.e_extra_opts.get().strip()
        p.nuitka_output_dir = self.e_output_dir.get().strip()
        p.nuitka_follow_imports = self.var_follow_imports.get()
        p.nuitka_tkinter_plugin = self.var_use_tkinter_plugin.get()
        p.nuitka_follow_stdlib = self.var_follow_stdlib.get()
        p.nuitka_show_progress = self.var_show_progress.get()
        p.nuitka_show_memory = self.var_show_memory.get()
        p.nuitka_show_scons = self.var_show_scons.get()
        p.nuitka_windows_uac_admin = self.var_windows_uac_admin.get()
        p.nuitka_lto = self.var_lto.get()
        p.debug = self.var_debug.get()

        try:
            jobs = int(self.var_jobs.get())
            if jobs < 1:
                raise ValueError()
            p.nuitka_jobs = jobs
        except ValueError:
            messagebox.showerror("Error", "Jobs must be an integer greater than 0.")
            return

        p.nuitka_windows_icon = self.e_windows_icon.get().strip()
        p.nuitka_windows_splash = self.e_windows_splash.get().strip()
        p.nuitka_output_name = self.e_output_name.get().strip()

        if not p.use_nuitka:
            p.use_pyarmor = False
            self.saved = True
            if self.win:
                self.win.destroy()
            return

        if not getattr(p, "script", None):
            messagebox.showerror("Error", "No script specified.")
            return
        if not p.script.endswith(".py"):
            messagebox.showerror("Error", f"Invalid script: {p.script} (must be .py)")
            return
        if p.nuitka_output_dir:
            output_path = Path(p.nuitka_output_dir)
            if output_path.exists() and not output_path.is_dir():
                messagebox.showerror("Error", f"Output directory is not valid: {p.nuitka_output_dir}")
                return

        if not p.nuitka_output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            p.nuitka_output_dir = str(Path("dist") / f"{p.name}_nuitka_{timestamp}")

        if not p.nuitka_output_name:
            # Automatically choose the correct extension:
            buildtype = self.var_buildtype.get()
            if buildtype in ("standalone", "onefile"):
                p.nuitka_output_name = (p.name or "output") + ".exe"
            elif buildtype == "module":
                p.nuitka_output_name = (p.name or "output") + ".pyd"
            elif buildtype == "windowsdll":
                p.nuitka_output_name = (p.name or "output") + ".dll"
            else:
                p.nuitka_output_name = (p.name or "output") + ".exe"

        p.use_pyarmor = False
        self.saved = True
        if self.win:
            self.win.destroy()

    def on_cancel(self):
        self.saved = False
        if self.win:
            self.win.destroy()

    def _choose_dir(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _choose_file(self, entry):
        path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
