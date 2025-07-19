import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

SPHINX_THEMES = [
    "alabaster", "sphinx_rtd_theme", "classic", "nature", "bizstyle", 
    "furo", "pydata_sphinx_theme", "press", "scrolls", "haiku", "agogo", "sphinx_book_theme"
]

class SphinxEditor:
    def __init__(self, master: tk.Tk, project, texts=None):
        self.master = master
        self.project = project
        self.texts = texts or {}
        self.saved = False

    def show(self) -> bool:
        self.win = tk.Toplevel(self.master)
        self.win.title("Sphinx Configuration")
        self.win.geometry("760x400")
        self.win.transient(self.master)
        self.win.grab_set()
        form = ttk.Frame(self.win, padding=14)
        form.pack(fill="both", expand=True)

        # --- Source/Build directories ---
        ttk.Label(form, text="Source directory:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.e_source = ttk.Entry(form, width=40)
        self.e_source.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        self.e_source.insert(0, getattr(self.project, "sphinx_source", "docs"))
        ttk.Button(form, text="...", command=lambda: self._choose_dir(self.e_source)).grid(row=0, column=2, padx=5)

        ttk.Label(form, text="Build directory:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.e_build = ttk.Entry(form, width=40)
        self.e_build.grid(row=1, column=1, padx=5, pady=4, sticky="ew")
        self.e_build.insert(0, getattr(self.project, "sphinx_build", "_build/html"))
        ttk.Button(form, text="...", command=lambda: self._choose_dir(self.e_build)).grid(row=1, column=2, padx=5)

        # --- Builder type ---
        ttk.Label(form, text="Builder (e.g., html, latex):").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.e_builder = ttk.Entry(form, width=18)
        self.e_builder.grid(row=2, column=1, sticky="w", padx=5, pady=4)
        self.e_builder.insert(0, getattr(self.project, "sphinx_builder", "html"))
        ttk.Button(form, text="?", command=lambda: messagebox.showinfo("Builder Info", "Examples: html, latex, epub, man, ...")).grid(row=2, column=2, padx=5)

        # --- conf.py path ---
        ttk.Label(form, text="conf.py path:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.e_conf = ttk.Entry(form, width=40)
        self.e_conf.grid(row=3, column=1, padx=5, pady=4, sticky="ew")
        self.e_conf.insert(0, getattr(self.project, "sphinx_conf_path", "docs/conf.py"))
        ttk.Button(form, text="...", command=lambda: self._choose_file(self.e_conf, [("Python files", "*.py")])).grid(row=3, column=2, padx=5)

        # --- doctrees directory ---
        ttk.Label(form, text="Doctrees directory (optional):").grid(row=4, column=0, sticky="e", padx=5, pady=4)
        self.e_doctrees = ttk.Entry(form, width=40)
        self.e_doctrees.grid(row=4, column=1, padx=5, pady=4, sticky="ew")
        self.e_doctrees.insert(0, getattr(self.project, "sphinx_doctrees", ""))

        # --- Theme selection ---
        ttk.Label(form, text="Theme:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
        self.theme_var = tk.StringVar()
        self.theme_combo = ttk.Combobox(form, textvariable=self.theme_var, values=SPHINX_THEMES, width=22, state="readonly")
        self.theme_combo.grid(row=5, column=1, sticky="w", padx=5, pady=4)
        current_theme = getattr(self.project, "sphinx_theme", "alabaster")
        self.theme_combo.set(current_theme if current_theme in SPHINX_THEMES else SPHINX_THEMES[0])
        ttk.Button(form, text="?", command=lambda: messagebox.showinfo("Themes", ", ".join(SPHINX_THEMES))).grid(row=5, column=2, padx=5)

        # --- Parallel jobs ---
        ttk.Label(form, text="Parallel jobs (-j):").grid(row=6, column=0, sticky="e", padx=5, pady=4)
        self.e_parallel = ttk.Entry(form, width=7)
        self.e_parallel.grid(row=6, column=1, sticky="w", padx=5, pady=4)
        self.e_parallel.insert(0, str(getattr(self.project, "sphinx_parallel", 1)))

        # --- SCHÖN ANGORDNETE Checkboxen ---
        cb_frame = ttk.Frame(form)
        cb_frame.grid(row=7, column=0, columnspan=3, sticky="w", pady=(6, 0))

        self.var_warning_is_error = tk.BooleanVar(value=getattr(self.project, "sphinx_warning_is_error", False))
        self.var_keep_going = tk.BooleanVar(value=getattr(self.project, "sphinx_keep_going", False))
        self.var_standalone = tk.BooleanVar(value=getattr(self.project, "use_sphinx_standalone", False))  # NEU

        ttk.Checkbutton(cb_frame, text="Treat warnings as errors (-W)", variable=self.var_warning_is_error).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Checkbutton(cb_frame, text="Keep going (--keep-going)", variable=self.var_keep_going).grid(row=0, column=1, padx=5, sticky="w")

        # Standalone Checkbox: abgesetzt, eigene Zeile, mit Abstand nach oben
        cb_standalone = ttk.Frame(form)
        cb_standalone.grid(row=8, column=0, columnspan=3, sticky="w", pady=(12, 0))
        ttk.Checkbutton(
            cb_standalone,
            text="Sphinx Standalone Mode",
            variable=self.var_standalone
        ).grid(row=0, column=0, sticky="w", padx=3)

        # --- Extra arguments ---
        ttk.Label(form, text="Additional options/arguments:").grid(row=9, column=0, sticky="ne", padx=5, pady=4)
        self.txt_args = scrolledtext.ScrolledText(form, width=40, height=3, font=("Segoe UI", 10))
        self.txt_args.grid(row=9, column=1, padx=5, pady=4, sticky="ew")
        self.txt_args.insert(tk.END, " ".join(getattr(self.project, "sphinx_args", [])))

        # --- Buttons ---
        button_frame = ttk.Frame(form)
        button_frame.grid(row=10, column=0, columnspan=3, pady=16)
        ttk.Button(button_frame, text="Cancel", command=self.win.destroy).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save", command=self._save).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="❓Help", command=lambda: messagebox.showinfo("Help", "See Sphinx documentation for more details.")).grid(row=0, column=2, padx=5)

        form.columnconfigure(1, weight=1)
        self.master.wait_window(self.win)
        return self.saved

    def _choose_dir(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _choose_file(self, entry, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _save(self):
        self.project.sphinx_source = self.e_source.get().strip()
        self.project.sphinx_build = self.e_build.get().strip()
        self.project.sphinx_builder = self.e_builder.get().strip()
        self.project.sphinx_conf_path = self.e_conf.get().strip()
        self.project.sphinx_doctrees = self.e_doctrees.get().strip()
        self.project.sphinx_theme = self.theme_var.get().strip()
        try:
            self.project.sphinx_parallel = int(self.e_parallel.get().strip())
        except Exception:
            self.project.sphinx_parallel = 1
        self.project.sphinx_warning_is_error = self.var_warning_is_error.get()
        self.project.sphinx_keep_going = self.var_keep_going.get()
        self.project.use_sphinx_standalone = self.var_standalone.get()  # NEU
        args = self.txt_args.get("1.0", tk.END).strip()
        self.project.sphinx_args = args.split() if args else []
        self.saved = True
        self.win.destroy()
