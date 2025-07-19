import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog

class PytestEditor:
    def __init__(self, master: tk.Tk, project):
        self.master = master
        self.project = project
        self.saved = False

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Pytest Configuration")
        self.win.geometry("720x560")
        self.win.transient(self.master)
        self.win.grab_set()
        form = ttk.Frame(self.win, padding=14)
        form.pack(fill="both", expand=True)

        # Test target: file or directory (only one!)
        ttk.Label(form, text="Test file:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.e_test_file = ttk.Entry(form, width=42)
        self.e_test_file.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        self.e_test_file.insert(0, getattr(self.project, "test_file", ""))
        ttk.Button(form, text="Choose file...", command=self._choose_test_file).grid(row=0, column=2, padx=5)

        ttk.Label(form, text="Test folder:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.e_test_dir = ttk.Entry(form, width=42)
        self.e_test_dir.grid(row=1, column=1, padx=5, pady=4, sticky="ew")
        self.e_test_dir.insert(0, getattr(self.project, "test_dir", ""))
        ttk.Button(form, text="Choose folder...", command=self._choose_test_dir).grid(row=1, column=2, padx=5)

        help_label = ttk.Label(
            form,
            text="Hint: Use only ONE of file or folder. If both are set, only the last changed will be used.",
            foreground="#505050", wraplength=520, justify="left"
        )
        help_label.grid(row=2, column=0, columnspan=3, padx=5, pady=(2,8), sticky="w")

        # Checkboxes für pytest-Optionen, SCHÖN ANGORDNET
        self.var_verbose = tk.BooleanVar(value=getattr(self.project, "pytest_verbose", False))
        self.var_quiet = tk.BooleanVar(value=getattr(self.project, "pytest_quiet", False))
        self.var_disable_warnings = tk.BooleanVar(value=getattr(self.project, "pytest_disable_warnings", False))
        self.var_lf = tk.BooleanVar(value=getattr(self.project, "pytest_lf", False))
        self.var_ff = tk.BooleanVar(value=getattr(self.project, "pytest_ff", False))
        self.var_standalone = tk.BooleanVar(value=getattr(self.project, "use_pytest_standalone", False))

        cb_frame = ttk.Frame(form)
        cb_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4,0))
        # Erste Reihe: v, q, disable_warnings
        ttk.Checkbutton(cb_frame, text="Verbose (-v)", variable=self.var_verbose).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Checkbutton(cb_frame, text="Quiet (-q)", variable=self.var_quiet).grid(row=0, column=1, padx=5, sticky="w")
        ttk.Checkbutton(cb_frame, text="Disable warnings", variable=self.var_disable_warnings).grid(row=0, column=2, padx=5, sticky="w")
        # Zweite Reihe: lf, ff
        ttk.Checkbutton(cb_frame, text="Only last failed (--lf)", variable=self.var_lf).grid(row=1, column=0, padx=5, sticky="w")
        ttk.Checkbutton(cb_frame, text="Fail fast (--ff)", variable=self.var_ff).grid(row=1, column=1, padx=5, sticky="w")

        # Standalone: eigene Zeile mit Abstand
        cb_standalone_frame = ttk.Frame(form)
        cb_standalone_frame.grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 6))
        ttk.Checkbutton(cb_standalone_frame, text="Pytest Standalone Mode", variable=self.var_standalone)\
            .grid(row=0, column=0, sticky="w", padx=3)

        # Labeled entry creator
        def create_labeled_entry(label, row, var_name, width=23):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=3)
            entry = ttk.Entry(form, width=width)
            entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
            val = getattr(self.project, var_name, "")
            entry.insert(0, "" if val is None else str(val))
            return entry

        self.e_maxfail = create_labeled_entry("Max failures (--maxfail):", 5, "pytest_maxfail")
        self.e_marker = create_labeled_entry("Marker (-m):", 6, "pytest_marker")
        self.e_keyword = create_labeled_entry("Keyword (-k):", 7, "pytest_keyword")
        self.e_tb = create_labeled_entry("Traceback style (--tb):", 8, "pytest_tb")
        self.e_durations = create_labeled_entry("Durations (--durations):", 9, "pytest_durations")
        self.e_capture = create_labeled_entry("Capture (--capture):", 10, "pytest_capture")
        self.e_html = create_labeled_entry("HTML report (--html):", 11, "pytest_html")

        # Free-form additional args
        ttk.Label(form, text="Additional Pytest arguments:").grid(row=12, column=0, sticky="ne", padx=5, pady=3)
        self.txt_args = scrolledtext.ScrolledText(form, width=40, height=3, font=("Segoe UI", 10))
        self.txt_args.grid(row=12, column=1, pady=3, sticky="w")
        pytest_args = getattr(self.project, "pytest_args", "")
        if isinstance(pytest_args, list):
            pytest_args = " ".join(str(x) for x in pytest_args)
        self.txt_args.insert(tk.END, pytest_args)

        # Pytest executable path
        ttk.Label(form, text="Pytest executable (optional):").grid(row=13, column=0, sticky="e", padx=5, pady=3)
        self.e_pytest_path = ttk.Entry(form, width=44)
        self.e_pytest_path.grid(row=13, column=1, padx=5, pady=3, sticky="w")
        self.e_pytest_path.insert(0, getattr(self.project, "pytest_path", "") or "")
        ttk.Button(form, text="...", command=self._choose_pytest_path).grid(row=13, column=2, padx=5)

        # Buttons
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=14, column=0, columnspan=3, pady=18)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).grid(row=0, column=0, padx=8)
        ttk.Button(btn_frame, text="Save", command=self._save).grid(row=0, column=1, padx=8)

        form.columnconfigure(1, weight=1)
        self.master.wait_window(self.win)
        return self.saved

    def _choose_test_file(self):
        path = filedialog.askopenfilename(
            title="Select test file",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if path:
            self.e_test_file.delete(0, tk.END)
            self.e_test_file.insert(0, path)
            self.e_test_dir.delete(0, tk.END)

    def _choose_test_dir(self):
        path = filedialog.askdirectory(title="Select test folder")
        if path:
            self.e_test_dir.delete(0, tk.END)
            self.e_test_dir.insert(0, path)
            self.e_test_file.delete(0, tk.END)

    def _choose_pytest_path(self):
        path = filedialog.askopenfilename(title="Select pytest executable")
        if path:
            self.e_pytest_path.delete(0, tk.END)
            self.e_pytest_path.insert(0, path)

    def _save(self):
        # Helper for robust int/None conversion
        def get_int_or_none(entry):
            val = entry.get().strip()
            try:
                return int(val) if val else None
            except ValueError:
                return None

        # Helper for robust string/None conversion
        def get_str_or_none(entry):
            val = entry.get().strip()
            return val if val else None

        # Save values to the Project object
        test_file = self.e_test_file.get().strip()
        test_dir  = self.e_test_dir.get().strip()
        # Priority: file > folder
        if test_file:
            self.project.test_file = test_file
            self.project.test_dir = ""
        elif test_dir:
            self.project.test_file = ""
            self.project.test_dir = test_dir
        else:
            self.project.test_file = ""
            self.project.test_dir = ""

        self.project.pytest_verbose = self.var_verbose.get()
        self.project.pytest_quiet = self.var_quiet.get()
        self.project.pytest_disable_warnings = self.var_disable_warnings.get()
        self.project.pytest_lf = self.var_lf.get()
        self.project.pytest_ff = self.var_ff.get()
        self.project.use_pytest_standalone = self.var_standalone.get()

        # Robust int or None
        self.project.pytest_maxfail = get_int_or_none(self.e_maxfail)
        self.project.pytest_durations = get_int_or_none(self.e_durations)

        # Strings (None wenn leer)
        self.project.pytest_marker = get_str_or_none(self.e_marker)
        self.project.pytest_keyword = get_str_or_none(self.e_keyword)
        self.project.pytest_tb = get_str_or_none(self.e_tb)
        self.project.pytest_capture = get_str_or_none(self.e_capture)
        self.project.pytest_html = get_str_or_none(self.e_html)

        # Args: immer als String
        args = self.txt_args.get("1.0", tk.END).strip()
        self.project.pytest_args = args if args else ""

        pytest_path = self.e_pytest_path.get().strip()
        self.project.pytest_path = pytest_path if pytest_path else ""

        self.saved = True
        self.win.destroy()
