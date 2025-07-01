import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from .help import show_nuitka_helper  # Importiere den Help-Dialog

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
        self.win.geometry("700x500")  
        self.win.transient(self.master)
        self.win.grab_set()

        main_frame = ttk.Frame(self.win, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Linke Spalte: Checkboxen
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.grid(row=0, column=0, sticky="nw", padx=10)

        self.var_use_nuitka = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkbox_frame, text="Use Nuitka", variable=self.var_use_nuitka, command=self._enforce_exclusivity).pack(anchor="w", pady=2)

        self.var_standalone = tk.BooleanVar(value=self.project.nuitka_standalone)
        ttk.Checkbutton(checkbox_frame, text="Standalone", variable=self.var_standalone).pack(anchor="w", pady=2)

        self.var_onefile = tk.BooleanVar(value=self.project.nuitka_onefile)
        ttk.Checkbutton(checkbox_frame, text="Onefile", variable=self.var_onefile).pack(anchor="w", pady=2)

        self.var_use_tkinter_plugin = tk.BooleanVar(value=getattr(self.project, "nuitka_tkinter_plugin", False))
        ttk.Checkbutton(checkbox_frame, text="Use TKinter", variable=self.var_use_tkinter_plugin).pack(anchor="w", pady=2)

        # Statt Checkbox Console: Radiobuttons Console vs Windowed
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

        # Rechte Spalte: Eingabefelder
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

        # --- LTO Combobox ---
        ttk.Label(entry_frame, text="LTO:").grid(row=3, column=0, sticky="e", pady=2)
        self.var_lto = tk.StringVar(value=self.project.nuitka_lto or "auto")
        self.cmb_lto = ttk.Combobox(entry_frame, textvariable=self.var_lto, values=["auto", "yes", "no"], state="readonly", width=18)
        self.cmb_lto.grid(row=3, column=1, sticky="ew", pady=2)

        # --- Jobs Combobox ---
        ttk.Label(entry_frame, text="Jobs:").grid(row=4, column=0, sticky="e", pady=2)
        self.var_jobs = tk.StringVar(value=str(self.project.nuitka_jobs or 1))
        self.cmb_jobs = ttk.Combobox(entry_frame, textvariable=self.var_jobs, values=["1", "2", "4", "8"], state="readonly", width=10)
        self.cmb_jobs.grid(row=4, column=1, sticky="ew", pady=2)

        self.e_windows_icon = add_entry_row("Windows Icon:", self.project.nuitka_windows_icon, 5, self._choose_file)
        self.e_windows_splash = add_entry_row("Windows Splash:", self.project.nuitka_windows_splash, 6, self._choose_file)

        entry_frame.grid_columnconfigure(1, weight=1)

        # Security Level Frame
        self.security_frame = ttk.LabelFrame(main_frame, text="Security Level")
        self.security_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Button(self.security_frame, text="Easy", command=lambda: self.set_security_level("Easy")).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Medium", command=lambda: self.set_security_level("Medium")).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Hard", command=lambda: self.set_security_level("Hard")).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(self.security_frame, text="Ultra", command=lambda: self.set_security_level("Ultra")).grid(row=0, column=3, padx=5, pady=2)

        # Buttons unten zentriert mit Analyse-Button und Help-Button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Analyse", command=self.analyze_inputs).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Help", command=lambda: show_nuitka_helper(self.win)).pack(side="left", padx=5)  # Help Button
        ttk.Button(button_frame, text="Save", command=self.save).pack(side="left", padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.win.wait_window(self.win)
        return self.saved
    
    
    def set_security_level(self, level):
        """Setzt vorgefertigte Einstellungen für verschiedene Sicherheitsstufen."""
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
            messagebox.showinfo("Warnung", "Hard Level kann zu Laufzeitproblemen führen, wenn Plugins oder Optionen nicht kompatibel sind.")

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
            messagebox.showwarning("⚠️Warnung", "Ultra Level kann die Performance beeinträchtigen und Fehler verursachen. Vorsicht!")

    def _enforce_exclusivity(self):
        if self.var_use_nuitka.get() and getattr(self.project, "use_pyarmor", False):
            self.project.use_pyarmor = False
            if hasattr(self.master, 'var_use_pyarmor'):
                self.master.var_use_pyarmor.set(False)

    def analyze_inputs(self):
        issues = []

        # Script Pfad prüfen (aus Projekt-Attribut)
        script_path = getattr(self.project, "script", "")
        if not script_path:
            issues.append("Script-Pfad ist leer.")
        else:
            p = Path(script_path)
            if not p.exists():
                issues.append(f"Script-Pfad existiert nicht: {script_path}")
            elif not p.suffix.lower() == ".py":
                issues.append(f"Script-Datei hat keine .py-Endung: {script_path}")

        # Output-Verzeichnis prüfen (aus GUI-Feld)
        output_path = self.e_output_dir.get().strip()
        if not output_path:
            issues.append("Output-Verzeichnis ist leer.")
        else:
            p_out = Path(output_path)
            if p_out.exists() and not p_out.is_dir():
                issues.append(f"Output-Verzeichnis ist kein Verzeichnis: {output_path}")

        # Jobs prüfen
        try:
            jobs = int(self.var_jobs.get())
            if jobs not in (1, 2, 4, 8):
                issues.append("Jobs muss eine der folgenden Zahlen sein: 1, 2, 4, 8.")
        except ValueError:
            issues.append("Jobs muss eine gültige ganze Zahl sein.")

        # Plugins prüfen (optional)
        plugins = self.e_plugins.get().strip()
        if plugins and not plugins.startswith("--plugin-enable=") and not plugins.startswith("--enable-plugin="):
            issues.append("Plugins sollten mit '--plugin-enable=' oder '--enable-plugin=' beginnen oder leer sein.")

        if issues:
            messagebox.showwarning("Analyse-Ergebnis", "\n".join(issues))
        else:
            messagebox.showinfo("Analyse-Ergebnis", "Keine sicherheitskritischen Probleme gefunden!")

    def save(self):
        p = self.project
        p.use_nuitka = self.var_use_nuitka.get()
        p.nuitka_standalone = self.var_standalone.get()
        p.nuitka_onefile = self.var_onefile.get()
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
            messagebox.showerror("Fehler", "Jobs muss eine ganze Zahl größer 0 sein.")
            return

        p.nuitka_windows_icon = self.e_windows_icon.get().strip()
        p.nuitka_windows_splash = self.e_windows_splash.get().strip()

        # Wenn Use Nuitka deaktiviert ist, speichern wir trotzdem die Werte und setzen ggf. related Flags
        if not p.use_nuitka:
            # z.B. kann man hier andere Flags zurücksetzen, wenn nötig:
            p.use_pyarmor = False
            self.saved = True
            if self.win:
                self.win.destroy()
            return

        # Wenn Use Nuitka aktiviert ist, weitere Validierungen
        if not getattr(p, "script", None):
            messagebox.showerror("Fehler", "Kein Script angegeben.")
            return
        if not p.script.endswith(".py"):
            messagebox.showerror("Fehler", f"Ungültiges Skript: {p.script} (muss .py sein)")
            return
        if p.nuitka_output_dir:
            output_path = Path(p.nuitka_output_dir)
            if output_path.exists() and not output_path.is_dir():
                messagebox.showerror("Fehler", f"Output-Verzeichnis ist kein gültiges Verzeichnis: {p.nuitka_output_dir}")
                return

        if not p.nuitka_output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            p.nuitka_output_dir = str(Path("dist") / f"{p.name}_nuitka_{timestamp}")

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
