import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, simpledialog
from pathlib import Path
from .project import Project
from .help import show_spec_helper

class SpecEditor:
    def __init__(self, master: tk.Tk, project: Project, texts: dict[str, str]):
        self.master = master
        self.project = project
        self.texts = texts
        self.saved = False

    def show(self) -> bool:
        self.win = tk.Toplevel(self.master)
        self.win.title("Spec-Editor")
        self.win.geometry("835x410")
        self.win.transient(self.master)
        self.win.grab_set()
        form_frame = ttk.Frame(self.win, padding="10")
        form_frame.pack(fill="both", expand=True)

        # Check-Frame oben
        check_frame_top = ttk.Frame(form_frame)
        check_frame_top.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")

        self.var_onefile = tk.BooleanVar(value=self.project.onefile)
        c_onefile = ttk.Checkbutton(check_frame_top, text="Onefile", variable=self.var_onefile)
        c_onefile.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.var_console = tk.BooleanVar(value=self.project.console)
        r_console = ttk.Radiobutton(check_frame_top, text="Konsole", variable=self.var_console, value=True)
        r_console.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        r_windowed = ttk.Radiobutton(check_frame_top, text="Windowed", variable=self.var_console, value=False)
        r_windowed.grid(row=0, column=2, padx=5, pady=2, sticky="w")

        # Entry-Zeilen mit Datei-Auswahl-Buttons
        def create_entry_row(text, row, default="", file_button=False, directory=False, filetypes=None):
            label = ttk.Label(form_frame, text=text)
            label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
            frame = ttk.Frame(form_frame)
            frame.grid(row=row, column=1, pady=2, sticky="ew")
            e = ttk.Entry(frame, width=100)
            e.grid(row=0, column=0, sticky="ew")
            e.insert(0, default)
            if file_button or directory:
                ttk.Button(
                    frame,
                    text="...",
                    command=lambda: self._choose_file(e, directory, filetypes)
                ).grid(row=0, column=1, padx=5)
            form_frame.grid_columnconfigure(1, weight=1)
            return e

        self.e_name = create_entry_row("Name:", 1, self.project.name)
        self.e_icon = create_entry_row("Icon:", 2, self.project.icon, file_button=True, filetypes=[("Icon Files", "*.ico")])
        self.e_spec_file = create_entry_row("Spec-Datei:", 3, self.project.spec_file, file_button=True, filetypes=[("Spec Files", "*.spec")])
        self.e_runtime_hook = create_entry_row("Runtime Hook:", 4, self.project.runtime_hook, file_button=True, filetypes=[("Python Files", "*.py")])

        # Separator
        separator = ttk.Separator(form_frame, orient="horizontal")
        separator.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        # Hidden Imports
        ttk.Label(form_frame, text="Hidden Imports:").grid(row=6, column=0, sticky="ne", pady=2, padx=5)
        self.txt_hidden = scrolledtext.ScrolledText(form_frame, width=50, height=3, font=("Segoe UI", 10))
        self.txt_hidden.grid(row=6, column=1, pady=2, sticky="ew")
        self.txt_hidden.insert(tk.END, self.project.hidden_imports or "")

        # Binaries (Add Data)
        ttk.Label(form_frame, text="Binaries (add_data):").grid(row=7, column=0, sticky="ne", pady=2, padx=5)
        self.txt_binaries = scrolledtext.ScrolledText(form_frame, width=50, height=3, font=("Segoe UI", 10))
        self.txt_binaries.grid(row=7, column=1, pady=2, sticky="ew")
        self.txt_binaries.insert(tk.END, self.project.add_data or "")
        ttk.Button(form_frame, text="Datei hinzufügen", command=self._add_binary_file).grid(row=7, column=2, padx=5)

        # Check-Frame unten
        check_frame_bottom = ttk.Frame(form_frame)
        check_frame_bottom.grid(row=8, column=0, columnspan=2, pady=5, sticky="w")

        self.var_upx = tk.BooleanVar(value=self.project.upx)
        c_upx = ttk.Checkbutton(check_frame_bottom, text="UPX aktivieren", variable=self.var_upx)
        c_upx.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.var_debug = tk.BooleanVar(value=self.project.debug)
        c_debug = ttk.Checkbutton(check_frame_bottom, text="Debug aktiv", variable=self.var_debug)
        c_debug.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        self.var_clean = tk.BooleanVar(value=self.project.clean)
        c_clean = ttk.Checkbutton(check_frame_bottom, text="Clean aktiv", variable=self.var_clean)
        c_clean.grid(row=0, column=2, padx=5, pady=2, sticky="w")

        self.var_strip = tk.BooleanVar(value=self.project.strip)
        c_strip = ttk.Checkbutton(check_frame_bottom, text="Strip aktiv", variable=self.var_strip)
        c_strip.grid(row=0, column=3, padx=5, pady=2, sticky="w")

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=10)
        cancel_btn = ttk.Button(button_frame, text="Abbrechen", command=self.win.destroy)
        cancel_btn.grid(row=0, column=0, padx=5, pady=5)
        save_btn = ttk.Button(button_frame, text="Speichern", command=self._save)
        save_btn.grid(row=0, column=1, padx=5, pady=5)
        help_btn = ttk.Button(button_frame, text="❓Help", command=lambda: show_spec_helper(self.win))
        help_btn.grid(row=0, column=2, padx=5, pady=5)

        self.master.wait_window(self.win)
        return self.saved

    def _choose_file(self, entry: ttk.Entry, directory=False, filetypes=None):
        path = ""
        if directory:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _add_binary_file(self) -> None:
        paths = filedialog.askopenfilenames(title="Wähle binäre Dateien aus")
        if not paths:
            return
        for p in paths:
            default_dest = "."
            dest = simpledialog.askstring(
                "Ziel eingeben",
                f"Zielordner für '{Path(p).name}' (Standard: '{default_dest}'):",
                initialvalue=default_dest,
                parent=self.win
            )
            if dest is None:
                dest = default_dest
            entry = f"{p}:{dest}"
            current = self.txt_binaries.get("1.0", tk.END).strip()
            if current:
                self.txt_binaries.insert(tk.END, "\n" + entry)
            else:
                self.txt_binaries.insert(tk.END, entry)

    def _save(self) -> None:
        self.project.name = self.e_name.get().strip()
        self.project.icon = self.e_icon.get().strip()
        self.project.spec_file = self.e_spec_file.get().strip()
        self.project.runtime_hook = self.e_runtime_hook.get().strip()
        self.project.onefile = self.var_onefile.get()
        self.project.console = self.var_console.get()
        self.project.upx = self.var_upx.get()
        self.project.debug = self.var_debug.get()
        self.project.clean = self.var_clean.get()
        self.project.strip = self.var_strip.get()
        self.project.hidden_imports = self.txt_hidden.get("1.0", tk.END).strip()
        self.project.add_data = self.txt_binaries.get("1.0", tk.END).strip()
        self.saved = True
        self.win.destroy()