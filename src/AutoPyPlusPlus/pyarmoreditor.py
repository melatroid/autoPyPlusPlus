import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import List
import os
import shlex

try:
    from .tooltip import CreateToolTip
except Exception: 
    def CreateToolTip(widget, text: str):
        try:
            widget.tooltip_text = text
        except Exception:
            pass

PRO_ONLY_FLAGS = ['--enable-rft', '--enable-bcc', '--enable-jit', '--enable-themida', '--enable-fly']

CMD_DESCRIPTIONS = {
    'gen': 'Generate obfuscated sources (.py) and PyArmor runtime (for AutoPy++ pipeline, standard mode).',
    'pack': 'Obfuscate and bundle into an executable with PyInstaller (direct EXE output, experimental).',
    'obfuscate': "Legacy: obfuscate sources only (don't use).",
}

PLATFORM_CHOICES = [
    'Current system (auto)',
    'windows.x86_64',
    'windows.arm64',
    'windows.x86',
    'linux.x86_64',
    'linux.aarch64',
    'linux.armv7',
    'darwin.x86_64',
    'darwin.arm64',
    'android.aarch64',
    'android.armv7',
    'windows.x86_64,linux.x86_64',
    'Custom...'
]
class PyarmorEditor:
    """Full English-only PyArmor configuration editor widget.

    This editor configures and previews PyArmor/pack options and persists them
    on the provided ``project`` object (any object with attributes used here).
    """

    def __init__(self, master, project):
        self.master = master
        self.project = project
        self.win = None
        self.saved = False

        # --- Master switches ---
        self.var_use_pyarmor = tk.BooleanVar(value=getattr(project, 'use_pyarmor', False))
        self.var_edition = tk.StringVar(value=(getattr(project, 'pyarmor_edition', None) or 'basic'))  # 'basic' | 'pro'

        # Build configuration (Debug / Release)
        self.var_build_mode = tk.StringVar(value=(getattr(project, 'build_mode', None) or 'debug'))  # 'debug' | 'release'

        # Dist mode: 'auto' (relative to Output) or 'manual' (custom dist path)
        self.var_dist_mode = tk.StringVar(value=getattr(project, 'pyarmor_dist_mode', 'auto'))

        # --- PyArmor state/flags ---
        self.var_use_outer_key = tk.BooleanVar(value=getattr(project, 'pyarmor_use_outer_key', False))
        self.var_obf_code = tk.StringVar(value=(getattr(project, 'pyarmor_obf_code', None) or '1'))
        self.var_mix_str = tk.BooleanVar(value=getattr(project, 'pyarmor_mix_str', False))
        self.var_private = tk.BooleanVar(value=getattr(project, 'pyarmor_private', False))
        self.var_restrict = tk.BooleanVar(value=getattr(project, 'pyarmor_restrict', False))
        self.var_assert_import = tk.BooleanVar(value=getattr(project, 'pyarmor_assert_import', False))
        self.var_assert_call = tk.BooleanVar(value=getattr(project, 'pyarmor_assert_call', False))
        self.var_pack = tk.StringVar(value=getattr(project, 'pyarmor_pack', ''))

        # Command dropdown (validated)
        default_cmd = getattr(project, 'pyarmor_command', None)
        if default_cmd not in ('gen', 'pack', 'obfuscate'):
            default_cmd = 'gen'
        self.var_command = tk.StringVar(value=default_cmd)

        # --- Pro-only options (persisted in project) ---
        self.var_rft = tk.BooleanVar(value=getattr(project, 'pyarmor_enable_rft', False))
        self.var_bcc = tk.BooleanVar(value=getattr(project, 'pyarmor_enable_bcc', False))
        self.var_jit = tk.BooleanVar(value=getattr(project, 'pyarmor_enable_jit', False))
        self.var_themida = tk.BooleanVar(value=getattr(project, 'pyarmor_enable_themida', False))
        self.var_fly = tk.BooleanVar(value=getattr(project, 'pyarmor_enable_fly', False))

        # --- Platform selection state ---
        self.var_platform_choice = tk.StringVar(value='Current system (auto)')

        # Python interpreter path (keeps backward compat with two possible attrs)
        initial_py = getattr(project, 'pyarmor_python_exe', None) or getattr(project, 'python_exec_path', '')
        self.var_python_exec = tk.StringVar(value=initial_py or '')

        # --- Pack Options state ---
        self.var_pack_windowed = tk.BooleanVar(value=bool(getattr(project, 'pyinstaller_windowed', False)))  # False=console, True=windowed
        self.var_pack_icon = tk.StringVar(value=getattr(project, 'pyinstaller_icon_path', ''))

        # Widget references, set in show()
        self.cb_platform = None
        self.e_platform_custom = None
        self.cb_pack = None
        self.btn_pack_opts = None
        self._pack_quick_open = False


    @staticmethod
    def _quote_for_e(arg: str) -> str:
        """Quote a path/arg safely inside the single -e string."""
        if not arg:
            return arg
        if os.name == 'nt':
            a = arg.replace('"', '\\"')
            if ' ' in a or any(c in a for c in (';', ',', '(', ')')):
                return f'"{a}"'
            return a
        return shlex.quote(arg)

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title('PyArmor Editor')
        self.win.geometry('800x800')
        self.win.transient(self.master)
        self.win.grab_set()
        try:
            self.win.iconbitmap('autoPy++.ico')
        except Exception:
            pass

        root = ttk.Frame(self.win, padding=10)
        root.pack(fill='both', expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        def row(parent, label_text, row, default='', file_button=False, directory=False, width=72, filetypes=None):
            lbl = ttk.Label(parent, text=label_text)
            lbl.grid(row=row, column=0, sticky='e', padx=5, pady=2)
            frame = ttk.Frame(parent)
            frame.grid(row=row, column=1, sticky='ew', pady=2)
            ent = ttk.Entry(frame, width=width)
            ent.grid(row=0, column=0, sticky='ew')
            ent.insert(0, default or '')
            if file_button or directory:
                ttk.Button(frame, text='...', command=lambda: self._choose(ent, directory, filetypes)).grid(row=0, column=1, padx=5)
            parent.grid_columnconfigure(1, weight=1)
            return ent

        # ===== Header: Build Mode + Use PyArmor + Edition =====
        header = ttk.Frame(root)
        header.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 8))
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        bm_frame = ttk.Frame(header)
        bm_frame.grid(row=0, column=0, sticky='w', padx=(0, 16))
        ttk.Label(bm_frame, text='Build mode:').grid(row=0, column=0, padx=(0, 6))
        rb_dbg = ttk.Radiobutton(bm_frame, text='Debug', value='debug', variable=self.var_build_mode, command=self._apply_build_mode)
        rb_rel = ttk.Radiobutton(bm_frame, text='Release', value='release', variable=self.var_build_mode, command=self._apply_build_mode)
        rb_dbg.grid(row=0, column=1, padx=(0, 8))
        rb_rel.grid(row=0, column=2)
        CreateToolTip(rb_dbg, 'Debug: fast iteration. Prefers onedir, console output, no strip/UPX. Safer defaults.')
        CreateToolTip(rb_rel, 'Release: optimized deliverable. Prefers onefile, strip/clean, higher obfuscation.')

        cb_use = ttk.Checkbutton(header, text='Use PyArmor', variable=self.var_use_pyarmor, command=self._toggle_enabled)
        cb_use.grid(row=0, column=1, sticky='w')
        CreateToolTip(cb_use, 'Enable or disable PyArmor for this project.')

        ed_frame = ttk.Frame(header)
        ed_frame.grid(row=0, column=2, sticky='w', padx=20)
        ttk.Label(ed_frame, text='PyArmor Edition:').grid(row=0, column=0, padx=(0, 6))
        rb_basic = ttk.Radiobutton(ed_frame, text='Basic', value='basic', variable=self.var_edition, command=self._toggle_enabled)
        rb_pro = ttk.Radiobutton(ed_frame, text='Pro', value='pro', variable=self.var_edition, command=self._toggle_enabled)
        rb_basic.grid(row=0, column=1)
        rb_pro.grid(row=0, column=2)
        CreateToolTip(rb_basic, 'Basic edition: standard protection; Pro-only flags are ignored.')
        CreateToolTip(rb_pro, 'Pro edition: enables advanced hardening (RFT/BCC/JIT/Themida/FLY).')

        # ===== Build targets =====
        self.targets = ttk.LabelFrame(root, text='Build Targets')
        self.targets.grid(row=1, column=0, columnspan=2, sticky='ew', pady=6)
        self.e_script = row(self.targets, 'Script (.py):', 0, getattr(self.project, 'script', ''), file_button=True, filetypes=[('Python Files', '*.py')])
        self.e_output = row(self.targets, 'Output folder:', 1, getattr(self.project, 'output', ''), directory=True)
        CreateToolTip(self.e_script, 'Entry script (.py) to obfuscate/pack.')
        CreateToolTip(self.e_output, 'Output folder for your build artifacts.')
        self.e_output.bind('<KeyRelease>', lambda e: (self._recompute_dist_from_output(), self._rebuild_preview()))

        # --- Python interpreter picker ---
        py_row = ttk.Frame(self.targets)
        py_row.grid(row=2, column=0, columnspan=2, sticky='ew', pady=2)
        ttk.Label(py_row, text='Python interpreter (python executable):').grid(row=0, column=0, sticky='e', padx=5)
        self.e_python = ttk.Entry(py_row, width=72, textvariable=self.var_python_exec)
        self.e_python.grid(row=0, column=1, sticky='ew')
        ttk.Button(
            py_row,
            text='...',
            command=lambda: self._choose(
                self.e_python,
                directory=False,
                filetypes=[('python.exe', 'python.exe'), ('Executables', '*.exe'), ('All Files', '*.*')]
            )
        ).grid(row=0, column=2, padx=5)
        CreateToolTip(self.e_python, 'Interpreter used for running "python -m pyarmor". Example: C:\\Python310\\python.exe')
        self.targets.grid_columnconfigure(1, weight=1)

        self.build = ttk.LabelFrame(root, text='PyArmor Build (Dist & Command)')
        self.build.grid(row=2, column=0, columnspan=2, sticky='ew', pady=6)

        dist_mode_frame = ttk.Frame(self.build)
        dist_mode_frame.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 2))
        ttk.Label(dist_mode_frame, text='Dist path:').grid(row=0, column=0, padx=(0, 8))
        rb_auto = ttk.Radiobutton(
            dist_mode_frame, text='Auto (relative to Output)', value='auto', variable=self.var_dist_mode,
            command=lambda: (self._on_toggle_dist_mode(), self._rebuild_preview())
        )
        rb_manual = ttk.Radiobutton(
            dist_mode_frame, text='Working Directory', value='manual', variable=self.var_dist_mode,
            command=lambda: (self._on_toggle_dist_mode(), self._rebuild_preview())
        )
        rb_auto.grid(row=0, column=1, padx=(0, 10))
        rb_manual.grid(row=0, column=2)

        self.e_dist_dir = row(self.build, 'PyArmor dist folder:', 1, getattr(self.project, 'pyarmor_dist_dir', ''), directory=True)
        CreateToolTip(self.e_dist_dir, 'PyArmor output directory (dist).')
        self.e_dist_dir.bind('<KeyRelease>', lambda e: self._rebuild_preview())
    
        cmd_row = ttk.Frame(self.build)
        cmd_row.grid(row=2, column=0, columnspan=2, sticky='ew', pady=2)

        ttk.Label(cmd_row, text='PyArmor command:').grid(row=0, column=0, padx=(0, 8))

        self.cb_command = ttk.Combobox(
            cmd_row, textvariable=self.var_command,
            values=['gen', 'pack', 'obfuscate'], state='readonly', width=12
        )
        self.cb_command.grid(row=0, column=1, sticky='w')
        CreateToolTip(self.cb_command, 'Choose the PyArmor subcommand.')

        self.btn_pack_opts = ttk.Button(cmd_row, text='Pack Options…', command=self._open_pack_quick)
        self.btn_pack_opts.grid(row=0, column=2, padx=(10, 0), sticky='w')
        CreateToolTip(self.btn_pack_opts, 'Quick settings for console/windowed and EXE icon.')

        self.var_cmd_desc = tk.StringVar()
        self.lbl_cmd_desc = ttk.Label(cmd_row, textvariable=self.var_cmd_desc, anchor='w', justify='left')
        self.lbl_cmd_desc.grid(row=0, column=3, padx=(10, 0), sticky='ew')

        cmd_row.grid_columnconfigure(0, weight=0)
        cmd_row.grid_columnconfigure(1, weight=0)
        cmd_row.grid_columnconfigure(2, weight=0, minsize=120)  # fixed minimum width for the button
        cmd_row.grid_columnconfigure(3, weight=1)

        def _wrap_desc(_=None):
            avail = max(200, cmd_row.winfo_width() - 350)
            self.lbl_cmd_desc.configure(wraplength=avail)

        cmd_row.bind('<Configure>', _wrap_desc)

        self.cb_command.bind(
            '<<ComboboxSelected>>',
            lambda e: (
                self._update_cmd_desc(),
                self._apply_build_mode(),
                self._maybe_open_pack_quick(),
                self._rebuild_preview()
            )
        )
        self._update_cmd_desc()
        self._sync_pack_enabled()

        # ===== Security Presets =====
        self.sec = ttk.LabelFrame(root, text='Security Level')
        self.sec.grid(row=3, column=0, columnspan=2, sticky='ew', pady=6)
        ttk.Button(self.sec, text='Easy', command=lambda: self._preset('Easy')).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(self.sec, text='Medium', command=lambda: self._preset('Medium')).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.sec, text='Hard', command=lambda: self._preset('Hard')).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(self.sec, text='Ultra', command=lambda: self._preset('Ultra')).grid(row=0, column=3, padx=5, pady=2)
        CreateToolTip(self.sec, 'Presets set recommended combinations. Hard/Ultra keep assertions OFF by default for stability.')

        # ===== Advanced options (English only) =====
        self.adv = ttk.LabelFrame(root, text='PyArmor – Advanced Options')
        self.adv.grid(row=4, column=0, columnspan=2, sticky='ew', pady=6, ipadx=4, ipady=2)
        self.adv.grid_columnconfigure(0, weight=1)
        self.adv.grid_columnconfigure(1, weight=1)

        # -- Left column: Obfuscation --
        lf_obf = ttk.LabelFrame(self.adv, text='Obfuscation')
        lf_obf.grid(row=0, column=0, sticky='nsew', padx=(6, 3), pady=6)
        lf_obf.grid_columnconfigure(1, weight=1)

        ttk.Label(lf_obf, text='Obf code (0/1/2):').grid(row=0, column=0, sticky='e', padx=6, pady=4)
        self.cb_obf = ttk.Combobox(
            lf_obf, textvariable=self.var_obf_code,
            values=['0', '1', '2'], width=10, state='readonly'
        )
        self.cb_obf.grid(row=0, column=1, sticky='w', pady=4)
        self.cb_obf.bind('<<ComboboxSelected>>', lambda e: self._rebuild_preview())
        CreateToolTip(self.cb_obf, '0=off, 1=standard, 2=aggressive (recommended).')

        self.ck_mix = ttk.Checkbutton(
            lf_obf, text='Mix strings',
            variable=self.var_mix_str, command=self._rebuild_preview
        )
        self.ck_mix.grid(row=1, column=0, columnspan=2, sticky='w', padx=6, pady=2)
        CreateToolTip(self.ck_mix, 'Obfuscates string literals; slight size/CPU overhead.')

        self.ck_private = ttk.Checkbutton(
            lf_obf, text='Private',
            variable=self.var_private, command=self._rebuild_preview
        )
        self.ck_private.grid(row=2, column=0, columnspan=2, sticky='w', padx=6, pady=2)

        self.ck_restr = ttk.Checkbutton(
            lf_obf, text='Restrict',
            variable=self.var_restrict, command=self._rebuild_preview
        )
        self.ck_restr.grid(row=3, column=0, columnspan=2, sticky='w', padx=6, pady=2)

        # -- Right column: Runtime checks --
        lf_runtime = ttk.LabelFrame(self.adv, text='Runtime checks')
        lf_runtime.grid(row=0, column=1, sticky='nsew', padx=(3, 6), pady=6)
        lf_runtime.grid_columnconfigure(0, weight=1)

        self.ck_ai = ttk.Checkbutton(
            lf_runtime, text='Assert import',
            variable=self.var_assert_import, command=self._rebuild_preview
        )
        self.ck_ai.grid(row=0, column=0, sticky='w', padx=6, pady=2)

        self.ck_ac = ttk.Checkbutton(
            lf_runtime, text='Assert call',
            variable=self.var_assert_call, command=self._rebuild_preview
        )
        self.ck_ac.grid(row=1, column=0, sticky='w', padx=6, pady=2)

        self.ck_outer = ttk.Checkbutton(
            lf_runtime, text='Use outer key',
            variable=self.var_use_outer_key, command=self._rebuild_preview
        )
        self.ck_outer.grid(row=2, column=0, sticky='w', padx=6, pady=(2, 6))

        # Separator
        ttk.Separator(self.adv, orient='horizontal').grid(
            row=1, column=0, columnspan=2, sticky='ew', padx=6, pady=(0, 6)
        )

        # -- Target platform --
        lf_platform = ttk.LabelFrame(self.adv, text='Target platform')
        lf_platform.grid(row=2, column=0, columnspan=2, sticky='ew', padx=6, pady=(0, 6))
        lf_platform.grid_columnconfigure(1, weight=1)

        ttk.Label(lf_platform, text='Platform(s):').grid(row=0, column=0, sticky='e', padx=6, pady=4)
        plat_row = ttk.Frame(lf_platform); plat_row.grid(row=0, column=1, sticky='ew')
        plat_row.grid_columnconfigure(0, weight=0)
        plat_row.grid_columnconfigure(1, weight=1)

        self.cb_platform = ttk.Combobox(
            plat_row, textvariable=self.var_platform_choice,
            values=PLATFORM_CHOICES, state='readonly', width=28
        )
        self.cb_platform.grid(row=0, column=0, sticky='w')
        CreateToolTip(self.cb_platform, 'Choose target(s) or select "Custom..." to enter tags.')
        self.cb_platform.bind('<<ComboboxSelected>>', lambda e: (self._on_platform_selected(), self._rebuild_preview()))

        self.e_platform_custom = ttk.Entry(plat_row, width=36)
        self.e_platform_custom.grid(row=0, column=1, sticky='ew', padx=(6, 0))
        self.e_platform_custom.grid_remove()
        self.e_platform_custom.bind('<KeyRelease>', lambda e: self._rebuild_preview())

        # -- Usage limits --
        lf_limit = ttk.LabelFrame(self.adv, text='Usage limits')
        lf_limit.grid(row=3, column=0, columnspan=2, sticky='ew', padx=6, pady=(0, 6))
        lf_limit.grid_columnconfigure(1, weight=1)
        lf_limit.grid_columnconfigure(3, weight=1)

        ttk.Label(lf_limit, text='Expired (YYYY-MM-DD):').grid(row=0, column=0, sticky='e', padx=6, pady=4)
        self.e_expired = ttk.Entry(lf_limit)
        self.e_expired.grid(row=0, column=1, sticky='ew', padx=(0, 12), pady=4)
        self.e_expired.insert(0, getattr(self.project, 'pyarmor_expired', '') or '')
        self.e_expired.bind('<KeyRelease>', lambda e: self._rebuild_preview())

        ttk.Label(lf_limit, text='Bind device:').grid(row=0, column=2, sticky='e', padx=6, pady=4)
        self.e_bind_device = ttk.Entry(lf_limit)
        self.e_bind_device.grid(row=0, column=3, sticky='ew', pady=4)
        self.e_bind_device.insert(0, getattr(self.project, 'pyarmor_bind_device', '') or '')
        self.e_bind_device.bind('<KeyRelease>', lambda e: self._rebuild_preview())

        # ===== Pro features (Pro edition only) =====
        self.pro = ttk.LabelFrame(root, text='PyArmor Pro Features')
        self.pro.grid(row=5, column=0, columnspan=2, sticky='ew', pady=6)
        self.ck_rft = ttk.Checkbutton(self.pro, text='RFT', variable=self.var_rft, command=self._rebuild_preview)
        self.ck_bcc = ttk.Checkbutton(self.pro, text='BCC', variable=self.var_bcc, command=self._rebuild_preview)
        self.ck_jit = ttk.Checkbutton(self.pro, text='JIT', variable=self.var_jit, command=self._rebuild_preview)
        self.ck_themida = ttk.Checkbutton(self.pro, text='Themida', variable=self.var_themida, command=self._rebuild_preview)
        self.ck_fly = ttk.Checkbutton(self.pro, text='FLY', variable=self.var_fly, command=self._rebuild_preview)
        self.ck_rft.grid(row=0, column=0, sticky='w', padx=5)
        self.ck_bcc.grid(row=0, column=1, sticky='w', padx=5)
        self.ck_jit.grid(row=0, column=2, sticky='w', padx=5)
        self.ck_themida.grid(row=0, column=3, sticky='w', padx=5)
        self.ck_fly.grid(row=0, column=4, sticky='w', padx=5)
        CreateToolTip(self.pro, 'These flags are only available in the Pro edition. In Basic they are ignored/removed.')
        CreateToolTip(self.ck_rft, 'RFT — Randomized Function Transform (Pro): randomizes function layout to defeat pattern matching. May impact performance.')
        CreateToolTip(self.ck_bcc, 'BCC — Bytecode Control-Flow Obfuscation (Pro): strong but heavy; can slow down and may fail with packers.')
        CreateToolTip(self.ck_jit, 'JIT — Runtime mutation/verification (Pro): increases startup; may trigger AV/EDR.')
        CreateToolTip(self.ck_themida, 'Themida (Pro, Windows only): native anti-tamper wrapper; may conflict with AV/VM.')
        CreateToolTip(self.ck_fly, 'FLY — Run-from-memory (Pro): fewer disk artifacts; higher RAM, possible AV false positives.')

        # ===== Preview =====
        self.preview = ttk.LabelFrame(root, text='Preview (read-only)')
        self.preview.grid(row=6, column=0, columnspan=2, sticky='nsew', pady=(6, 4))
        root.grid_rowconfigure(6, weight=1)
        self.txt_preview = scrolledtext.ScrolledText(self.preview, width=80, height=4)
        self.txt_preview.pack(fill='both', expand=True, padx=6, pady=(6, 2))
        # Interpreter label
        self.lbl_interpreter = ttk.Label(self.preview, text='', foreground='#7a7a7a')
        self.lbl_interpreter.pack(anchor='w', padx=8, pady=(0, 6))
        self._set_preview('(PyArmor disabled)' if not self.var_use_pyarmor.get() else '')

        # ===== Buttons =====
        btns = ttk.Frame(root)
        btns.grid(row=7, column=0, columnspan=2, pady=8)
        self.btn_analyze = ttk.Button(btns, text='Analyze', command=self._analyze)
        self.btn_save = ttk.Button(btns, text='Save', style='Accent.TButton', command=self.save)
        self.btn_cancel = ttk.Button(btns, text='Cancel', command=self.win.destroy)
        self.btn_analyze.grid(row=0, column=0, padx=5)
        self.btn_save.grid(row=0, column=1, padx=5)
        self.btn_cancel.grid(row=0, column=2, padx=5)

        # Initial state
        self._apply_build_mode(init=True)
        self._toggle_enabled()
        self._on_toggle_dist_mode()
        self._recompute_dist_from_output()
        self._init_platform_choice_from_project()
        self._sync_pack_enabled()
        self._rebuild_preview()

        if self.win and self.win.winfo_exists():
            self.win.wait_window()
        return self.saved

    # -------------------- Internals --------------------
    def _update_cmd_desc(self):
        cmd = self.var_command.get()
        self.var_cmd_desc.set(CMD_DESCRIPTIONS.get(cmd, ''))

    def _choose(self, entry, directory=False, filetypes=None):
        if directory:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=book_filetypes(filetypes))
        if path:
            entry.delete(0, 'end')
            entry.insert(0, path)
            if entry is self.e_output:
                self._recompute_dist_from_output()
            self._rebuild_preview()

    def _set_children_state(self, parent, state: str):
        for child in parent.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass
            self._set_children_state(child, state)

    def _is_pro(self):
        return self.var_use_pyarmor.get() and self.var_edition.get() == 'pro'

    def _on_toggle_dist_mode(self):
        try:
            if self.var_use_pyarmor.get() and self.var_dist_mode.get() == 'manual':
                self.e_dist_dir.configure(state='normal')
            else:
                self.e_dist_dir.configure(state='disabled')
        except tk.TclError:
            pass
        if self.var_dist_mode.get() == 'auto':
            self._recompute_dist_from_output()

    def _recompute_dist_from_output(self):
        if not (self.var_use_pyarmor.get() and self.var_dist_mode.get() == 'auto'):
            return
        output = (self.e_output.get() or '').strip()
        dist = str(Path(output) / 'dist') if output else 'dist'
        try:
            self.e_dist_dir.configure(state='normal')
        except tk.TclError:
            pass
        self.e_dist_dir.delete(0, 'end')
        self.e_dist_dir.insert(0, dist)
        try:
            self.e_dist_dir.configure(state='disabled')
        except tk.TclError:
            pass
        self._rebuild_preview()

    def _toggle_enabled(self):
        enabled = self.var_use_pyarmor.get()
        self._set_children_state(self.build, 'normal' if enabled else 'disabled')
        self._set_children_state(self.sec, 'normal' if enabled else 'disabled')
        self._set_children_state(self.adv, 'normal' if enabled else 'disabled')
        self._set_children_state(self.pro, 'normal' if enabled else 'disabled')
        self.btn_analyze.configure(state=('normal' if enabled else 'disabled'))
        state = 'normal' if self._is_pro() else 'disabled'
        for w in (self.ck_rft, self.ck_bcc, self.ck_jit, self.ck_themida, self.ck_fly):
            try:
                w.configure(state=state)
            except tk.TclError:
                pass
        self._on_toggle_dist_mode()
        if not enabled:
            self._set_preview('(PyArmor disabled)')
        else:
            self._rebuild_preview()

    # --- Pack UI enable/disable based on command ---
    def _sync_pack_enabled(self):
        """Enable Pack selection and Pack Options button only for command=pack; otherwise clear & disable."""
        cmd = (self.var_command.get() or 'gen').strip()
        try:
            cb = self.cb_pack
            btn = self.btn_pack_opts
            if cmd == 'pack':
                if cb:
                    cb.configure(state='readonly')
                if btn:
                    btn.configure(state='normal')
            else:
                if cb:
                    cb.configure(state='disabled')
                self.var_pack.set('')
                if btn:
                    btn.configure(state='disabled')
        except tk.TclError:
            pass

    # --- Pack Options dialog control ---
    def _maybe_open_pack_quick(self):
        if (self.var_command.get() or '') == 'pack':
            self._open_pack_quick()
            
    def _open_pack_quick(self):
        if self._pack_quick_open:
            return
        self._pack_quick_open = True

        dlg = tk.Toplevel(self.win)
        dlg.title('Pack Options…')
        dlg.transient(self.win)
        dlg.grab_set()
        dlg.resizable(False, False)

        def _close():
            self._pack_quick_open = False
            dlg.destroy()

        dlg.protocol("WM_DELETE_WINDOW", _close)

        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill='both', expand=True)

        # --- Bundle Mode (onefile/onedir) ---
        group_bundle = ttk.LabelFrame(frm, text='Bundle Mode')
        group_bundle.pack(fill='x', pady=(0, 8))

        rb_onedir  = ttk.Radiobutton(group_bundle, text='Onedir (dev/test)',
                                     value='onedir', variable=self.var_pack,
                                     command=self._rebuild_preview)
        rb_onefile = ttk.Radiobutton(group_bundle, text='Onefile (single EXE)',
                                     value='onefile', variable=self.var_pack,
                                     command=self._rebuild_preview)

        rb_onedir.pack(anchor='w', padx=8, pady=2)
        rb_onefile.pack(anchor='w', padx=8, pady=2)

        CreateToolTip(group_bundle, 'Choose PyInstaller bundle mode: onedir (faster testing) or onefile (single-file release).')

        # --- App mode (Console/Windowed) ---
        group_mode = ttk.LabelFrame(frm, text='App Mode')
        group_mode.pack(fill='x', pady=(0, 8))
        ttk.Radiobutton(group_mode, text='Console (with console)', value=False,
                        variable=self.var_pack_windowed,
                        command=self._rebuild_preview).pack(anchor='w', padx=8, pady=2)
        ttk.Radiobutton(group_mode, text='Windowed (no console)', value=True,
                        variable=self.var_pack_windowed,
                        command=self._rebuild_preview).pack(anchor='w', padx=8, pady=2)

        # --- Icon ---
        group_icon = ttk.LabelFrame(frm, text='EXE/App Icon')
        group_icon.pack(fill='x', pady=(0, 8))
        row = ttk.Frame(group_icon); row.pack(fill='x', padx=6, pady=6)
        ttk.Label(row, text='Icon file:').pack(side='left', padx=(0, 6))
        e = ttk.Entry(row, textvariable=self.var_pack_icon, width=54)
        e.pack(side='left', fill='x', expand=True)

        def _pick_icon():
            path = filedialog.askopenfilename(
                filetypes=[('Windows Icon', '*.ico'),
                           ('macOS Icon', '*.icns'),
                           ('PNG', '*.png'),
                           ('All Files', '*.*')]
            )
            if path:
                self.var_pack_icon.set(path)
                self._rebuild_preview()

        ttk.Button(row, text='...', width=3, command=_pick_icon).pack(side='left', padx=6)

        # --- Buttons ---
        btns = ttk.Frame(frm); btns.pack(fill='x', pady=(4, 0))
        ttk.Button(btns, text='OK', command=lambda: (_close(), self._rebuild_preview())).pack(side='right', padx=4)
        ttk.Button(btns, text='Cancel', command=_close).pack(side='right')

    # --- Presets ---
    def _preset(self, level: str):
        self.var_obf_code.set('2')
        self.var_mix_str.set(True)
        self.var_private.set(True)
        self.var_restrict.set(True)
        self.var_assert_import.set(False)
        self.var_assert_call.set(False)
        self.var_rft.set(False)
        self.var_bcc.set(False)
        self.var_jit.set(False)
        self.var_themida.set(False)
        self.var_fly.set(False)

        if level == 'Easy':
            self.var_obf_code.set('1')
            self.var_mix_str.set(False)
            self.var_private.set(False)
            self.var_restrict.set(False)
            messagebox.showinfo('Info', 'Easy: minimal protection, no restrictions.')
        elif level == 'Medium':
            self.var_obf_code.set('1')
            messagebox.showinfo('Info', 'Medium: solid defaults without risky assertions.')
        elif level == 'Hard':
            messagebox.showinfo('Info', 'Hard: strong & stable defaults. If needed, enable "Assert import/call" manually.')
        elif level == 'Ultra':
            if self._is_pro():
                self.var_rft.set(True)
                self.var_bcc.set(True)
                self.var_jit.set(True)
                self.var_themida.set(True)
                self.var_fly.set(False)
                messagebox.showwarning('Ultra (Pro)', 'Ultra enables Pro hardening. Assertions stay OFF by default to keep builds stable.')
            else:
                messagebox.showwarning('Ultra (Basic)', 'Ultra Pro features are not available in Basic. Assertions stay OFF to keep builds stable.')
        else:
            messagebox.showinfo('Info', f'Unknown preset: {level}')

        self._apply_build_mode()
        self._rebuild_preview()

    # --- Build Mode handler (Debug/Release) ---
    def _apply_build_mode(self, init: bool = False):
        mode = (self.var_build_mode.get() or 'debug').lower()
        cmd = (self.var_command.get() or 'gen').strip()

        if cmd == 'pack':
            # Defaults for pack mode
            if mode == 'debug':
                self.var_pack.set('onedir')
                self.var_pack_windowed.set(False)  # console for quick debugging
                if (self.var_obf_code.get() or '1') not in ('0', '1', '2'):
                    self.var_obf_code.set('1')
            else:
                self.var_pack.set('onefile')
                self.var_pack_windowed.set(True)   # GUI by default in release
                if self.var_obf_code.get() in ('0', '1'):
                    self.var_obf_code.set('2')
        else:
            self.var_pack.set('')

        self._sync_pack_enabled()
        self._rebuild_preview()

    def _set_preview(self, text: str):
        try:
            self.txt_preview.configure(state='normal')
            self.txt_preview.delete('1.0', 'end')
            self.txt_preview.insert('1.0', text or '')
        finally:
            self.txt_preview.configure(state='disabled')

    # --- Platform helpers ---
    def _on_platform_selected(self):
        choice = (self.var_platform_choice.get() or '').strip()
        if choice == 'Custom...':
            self.e_platform_custom.grid()
            self.e_platform_custom.focus_set()
        elif choice == 'Current system (auto)':
            self.e_platform_custom.delete(0, 'end')
            self.e_platform_custom.grid_remove()
        else:
            self.e_platform_custom.delete(0, 'end')
            self.e_platform_custom.insert(0, choice)
            self.e_platform_custom.grid_remove()

    def _get_platform_text(self) -> str:
        """Final platform string for CLI."""
        choice = (self.var_platform_choice.get() or '').strip()
        if choice == 'Current system (auto)':
            return ''
        if choice == 'Custom...':
            return (self.e_platform_custom.get() or '').strip()
        return choice

    def _init_platform_choice_from_project(self):
        """Force default to 'Current system (auto)' on every open."""
        self.var_platform_choice.set('Current system (auto)')
        self._on_platform_selected()
        try:
            setattr(self.project, 'pyarmor_platform', '')
        except Exception:
            pass

    def _build_options_from_ui(self) -> List[str]:
        """Build the PyArmor CLI options list based on the current UI state (excluding 'Auto')."""
        if not self.var_use_pyarmor.get():
            return []

        opts: List[str] = []
        cmd = (self.var_command.get() or '').strip()

        # --- Common PyArmor options ---
        obf = (self.var_obf_code.get() or '').strip()
        if obf:
            opts += ['--obf-code', obf]
        if self.var_mix_str.get():
            opts += ['--mix-str']
        if self.var_private.get():
            opts += ['--private']
        if self.var_restrict.get():
            opts += ['--restrict']
        if self.var_assert_import.get():
            opts += ['--assert-import']
        if self.var_assert_call.get():
            opts += ['--assert-call']
        if self.var_use_outer_key.get():
            opts += ['--outer']

        platform_txt = self._get_platform_text()
        if platform_txt:
            opts += ['--platform', platform_txt]

        # --- PyInstaller flags (for single -e) ---
        pi_flags: List[str] = []

        if cmd == 'pack':
            # pack is active -> mode MUST be set (UI guarantees this)
            opts += ['--pack']
            effective_pack_mode = (self.var_pack.get() or '').strip()

            if effective_pack_mode == 'onefile':
                pi_flags.append('--onefile')
            elif effective_pack_mode == 'onedir':
                pi_flags.append('--onedir')
            else:
                effective_pack_mode = 'onedir'
                pi_flags.append('--onedir')

            if self.var_pack_windowed.get():
                pi_flags.append('--windowed')  # console is default

            icon_path = (self.var_pack_icon.get() or '').strip()
            if icon_path:
                pi_flags.append(f'--icon {self._quote_for_e(icon_path)}')
        else:
            effective_pack_mode = ''

        if pi_flags:
            opts += ['-e', ' '.join(pi_flags)]

        # Expiration / bind device
        expired = (self.e_expired.get() or '').strip()
        if expired:
            opts += ['--expire', expired]

        bind_device = (self.e_bind_device.get() or '').strip()
        if bind_device:
            opts += ['--bind-disk', bind_device]

        # Pro flags only if edition=pro
        if self.var_edition.get() == 'pro':
            if self.var_rft.get():
                opts += ['--enable-rft']
            if self.var_bcc.get():
                opts += ['--enable-bcc']
            if self.var_jit.get():
                opts += ['--enable-jit']
            if self.var_themida.get():
                opts += ['--enable-themida']
            if self.var_fly.get():
                opts += ['--enable-fly']

        # Dist dir (same as when saving)
        if self.var_dist_mode.get() == 'auto':
            output = (self.e_output.get() or '').strip()
            dist_dir = str(Path(output) / 'dist') if output else 'dist'
        else:
            dist_dir = (self.e_dist_dir.get() or '').strip() or 'dist'

        # Guard: Remove assertions for onefile (effective mode!)
        if cmd == 'pack' and effective_pack_mode == 'onefile':
            opts = [t for t in opts if t not in ('--assert-import', '--assert-call')]

        # Ensure output flag present
        if '--output' not in opts:
            opts += ['--output', dist_dir]

        return opts

    def _rebuild_preview(self):
        if not self.var_use_pyarmor.get():
            self._set_preview('(PyArmor disabled)')
            self.lbl_interpreter.configure(text='')
            return
        opts = self._build_options_from_ui()
        cmd = (self.var_command.get() or '').strip()
        preview = ((cmd + ' ') if cmd else '') + ' '.join(opts).strip()
        self._set_preview(preview if preview else '(no options)')
        # Interpreter hint
        interp = (self.var_python_exec.get() or '').strip()
        self.lbl_interpreter.configure(
            text=(f'Interpreter: {interp}' if interp else 'Interpreter: (system default / PATH)')
        )

    def _analyze(self):
        issues: List[str] = []
        helps: List[str] = []

        # General: Script & Output
        script_path = (self.e_script.get() or '').strip()
        output_path = (self.e_output.get() or '').strip()

        if not script_path:
            issues.append('[ERROR] Script path is empty.')
            helps.append('[HELP] Provide the entry .py script to obfuscate.')
        elif not Path(script_path).exists():
            issues.append(f'[ERROR] Script path does not exist: {script_path}')
            helps.append("[HELP] Select a valid .py file using the '...' button.")
        elif not script_path.endswith('.py'):
            issues.append(f'[ERROR] Script path is not a Python file: {script_path}')
            helps.append('[HELP] Ensure the path ends with .py.')
        else:
            if not Path(script_path).is_absolute():
                issues.append(f'[WARN] Script path is relative: {script_path}')
                helps.append('[HELP] Use an absolute path for consistency across builds.')

        if not output_path:
            issues.append('[WARN] Output folder is empty.')
            helps.append("[HELP] Specify an output folder; dist will default to './dist' if auto mode.")
        elif Path(output_path).exists() and not Path(output_path).is_dir():
            issues.append(f'[ERROR] Output folder is not a directory: {output_path}')
            helps.append("[HELP] Choose a valid directory using the '...' button.")

        # Interpreter checks
        pyexec = (self.var_python_exec.get() or '').strip()
        if pyexec:
            p = Path(pyexec)
            if not p.exists():
                issues.append(f'[ERROR] Python interpreter not found: {pyexec}')
                helps.append("[HELP] Pick a valid python.exe (e.g., C:\\Python310\\python.exe).")
            else:
                if os.name == 'nt':
                    if p.name.lower() != 'python.exe':
                        issues.append(f'[WARN] Interpreter does not look like python.exe: {pyexec}')
                        helps.append('[HELP] Use the CPython executable, not a launcher or dll.')
                    if 'WindowsApps' in pyexec:
                        issues.append('[WARN] Microsoft Store alias selected (WindowsApps).')
                        helps.append('[HELP] Choose the real CPython python.exe to avoid runtime mismatches.')
                else:
                    if p.name not in ('python', 'python3') and not p.name.startswith('python'):
                        issues.append(f'[WARN] Interpreter may not be a CPython binary: {pyexec}')
                        helps.append('[HELP] Use a CPython interpreter (e.g., /usr/bin/python3).')
        else:
            helps.append('[HELP] Set a specific interpreter to guarantee the same MAJOR.MINOR for build and runtime.')

        # Only check PyArmor if active
        if self.var_use_pyarmor.get():
            cmd = (self.var_command.get() or '').strip()
            expired = (self.e_expired.get() or '').strip()
            dist_dir = (self.e_dist_dir.get() or '').strip()
            pack_mode = (self.var_pack.get() or '').strip()
            platform = (self._get_platform_text() or '').strip().lower()
            build_mode = (self.var_build_mode.get() or 'debug').lower()
            obf_code = (self.var_obf_code.get() or '').strip()
            bind_device = (self.e_bind_device.get() or '').strip()

            if not cmd:
                issues.append('[ERROR] PyArmor command is empty.')
                helps.append('[HELP] Select a command from the dropdown: gen, pack, or obfuscate.')
            elif cmd not in ['gen', 'pack', 'obfuscate']:
                issues.append(f'[ERROR] Invalid PyArmor command: {cmd}')
                helps.append('[HELP] Choose from: gen (recommended), pack, or obfuscate (legacy).')

            if not obf_code:
                issues.append('[ERROR] Obfuscation code is empty.')
                helps.append('[HELP] Select 0 (off), 1 (standard), or 2 (aggressive) from the dropdown.')
            elif obf_code not in ['0', '1', '2']:
                issues.append(f'[ERROR] Invalid obf-code: {obf_code} (must be 0, 1, or 2)')
                helps.append('[HELP] Use the combobox to select a valid level.')

            if not dist_dir:
                issues.append('[WARN] Dist folder is empty.')
                helps.append('[HELP] Use auto mode (relative to output) or specify a manual path.')
            elif self.var_dist_mode.get() == 'manual' and not Path(dist_dir).exists():
                issues.append(f'[NOTE] Manual dist directory {dist_dir} does not exist yet (it will be created when compiling).')

            if expired:
                try:
                    datetime.strptime(expired, '%Y-%m-%d')
                except ValueError:
                    issues.append(f'[ERROR] Invalid expiration date: {expired} (format: yyyy-mm-dd)')
                    helps.append('[HELP] Use YYYY-MM-DD format, e.g., 2025-12-31.')
            elif not expired and (self.var_restrict.get() or self.var_assert_import.get() or self.var_assert_call.get()):
                helps.append('[HELP] Consider adding an expiration date for better protection with restrictive modes.')

            if bind_device:
                serial_like = bind_device.replace('-', '').replace(':', '')
                if len(bind_device) < 5 or not serial_like.isalnum():
                    issues.append(f"[WARN] Bind device '{bind_device}' looks invalid (should be a serial like 'ABC123' or 'disk-XYZ').")
                    helps.append('[HELP] Use a device/disk serial number; test with --bind-disk to verify.')
            elif (self.var_restrict.get() or self.var_assert_import.get() or self.var_assert_call.get()):
                helps.append('[HELP] Device binding increases security; consider adding for restrictive setups.')

            # Platform checks
            if platform:
                platforms = [p.strip().lower() for p in platform.split(',')]
                invalid_platforms = [p for p in platforms if not any(kw in p for kw in ['windows', 'linux', 'darwin', 'android']) and p != '']
                if invalid_platforms:
                    issues.append(f"[WARN] Invalid platform tag(s): {', '.join(invalid_platforms)}")
                    helps.append("[HELP] Use tags like 'windows.x86_64' or comma-separated lists; see PyArmor docs.")
            else:
                helps.append("[HELP] 'Current system (auto)' uses host platform; specify for cross-compilation.")

            if pack_mode and pack_mode not in ['onefile', 'onedir']:
                issues.append(f"[ERROR] Invalid pack mode: {pack_mode} (must be onefile or onedir)")
                helps.append('[HELP] Select a valid mode in the Pack combobox.')

            # Pro flags active while Basic?
            pro_flags_active = any((self.var_rft.get(), self.var_bcc.get(), self.var_jit.get(), self.var_themida.get(), self.var_fly.get()))
            if self.var_edition.get() == 'basic' and pro_flags_active:
                issues.append('[WARN] Pro-only options are enabled, but edition is Basic. They will be ignored/removed.')
                helps.append('[HELP] Switch to Pro edition or disable Pro flags for Basic compatibility.')

            # Relationships and stability checks
            assertions_active = self.var_assert_import.get() or self.var_assert_call.get()
            restrict_active = self.var_restrict.get()
            pro_active = pro_flags_active
            is_packing = (cmd == 'pack') or bool(pack_mode)

            if assertions_active and pack_mode == 'onefile':
                issues.append('[WARN] Assertions + pack=onefile can be unstable.')
                helps.append('[HELP] Build onedir first for testing, then try onefile. Disable assertions if issues persist.')

            if assertions_active and not restrict_active:
                issues.append('[WARN] Assertions without Restrict: inconsistent setup.')
                helps.append('[HELP] Enable Restrict for coherent protection, or disable assertions for flexibility.')

            if restrict_active and not assertions_active:
                helps.append('[HELP] Assertions (import/call) complement Restrict; enable them for stricter checks.')

            if self.var_use_outer_key.get() and (restrict_active or assertions_active):
                issues.append('[WARN] Outer key + restrictive modes: ensure key file is distributed and handled correctly.')
                helps.append('[HELP] Generate key with pyarmor gen key; test runtime key loading.')

            if expired and bind_device:
                helps.append('[HELP] Expiration + device binding: strong combo for time/device-limited apps.')
            elif expired or bind_device:
                helps.append('[HELP] Combine expiration and device binding for layered protection.')

            if cmd == 'pack' and not pack_mode:
                issues.append('[NOTE] Command=pack but Pack mode empty: defaults to onedir.')
                helps.append('[HELP] Specify onefile (release) or onedir (debug) for explicit control.')

            if is_packing and pack_mode == 'onefile' and obf_code == '2':
                issues.append('[WARN] Aggressive obf-code=2 + onefile: may lead to larger files or extraction errors.')
                helps.append('[HELP] Try obf-code=1 for better onefile stability.')

            if (bind_device or expired) and pack_mode == 'onefile':
                issues.append('[WARN] Device binding or expiration with onefile: reduces portability.')
                helps.append('[HELP] Test on target machines; consider onedir for development.')

            if restrict_active and is_packing:
                issues.append('[WARN] Restrict + packing: may cause "check restrict mode failed" during packing.')
                helps.append('[HELP] Obfuscate (gen) first, then pack separately; verify with tests.')

            if self.var_rft.get():
                issues.append('[WARN] RFT enabled: may impact performance and complicate debugging.')
                helps.append('[HELP] Test thoroughly, especially with JIT/BCC.]')
            if self.var_bcc.get():
                issues.append('[WARN] BCC enabled: heavy control-flow obfuscation may slow down or break in some environments.')
                if pack_mode == 'onefile':
                    issues.append('[WARN] BCC + pack=onefile: higher risk of packing failures.')
                    helps.append('[HELP] Prefer onedir for testing.]')
            if self.var_themida.get():
                if not platform or 'windows' not in platform:
                    issues.append('[ERROR] Themida enabled but platform not set to Windows: Windows-only feature.')
                    helps.append('[HELP] Select a Windows platform or disable Themida.')
                if pack_mode == 'onefile':
                    issues.append('[WARN] Themida + pack=onefile: potential AV/VM conflicts.')
                    helps.append('[HELP] Test in target environment; monitor for false positives.]')
            if self.var_fly.get():
                issues.append('[WARN] FLY enabled: higher RAM usage and possible AV false positives.')
                helps.append('[HELP] Suitable for low-disk scenarios; often paired with Themida on Windows.]')
            if self.var_jit.get():
                issues.append('[WARN] JIT enabled: may increase startup time and trigger EDR/AV alerts.')
                helps.append('[HELP] Disable for sensitive environments; enable RFT for alternatives.]')

            if build_mode == 'debug' and pack_mode == 'onefile':
                issues.append('[NOTE] Debug mode usually pairs better with Pack=onedir for faster iterations.')
                helps.append('[HELP] Switch to onedir for quick testing.]')
            if build_mode == 'release' and pack_mode == 'onedir':
                issues.append('[NOTE] Release mode usually pairs better with Pack=onefile for single-file distribution.')
                helps.append('[HELP] Use onefile for final releases.]')

            if obf_code == '0' and (restrict_active or assertions_active or pro_active):
                issues.append('[WARN] Obf-code=0 (off) with advanced protections: minimal obfuscation reduces effectiveness.')
                helps.append('[HELP] Increase to 1 or 2 for better synergy.]')
            if pro_active and obf_code != '2':
                helps.append('[HELP] Pro features are most effective with obf-code=2 (aggressive).]')
            if not any([self.var_mix_str.get(), self.var_private.get(), restrict_active, assertions_active, pro_active]) and obf_code in ['1', '2']:
                helps.append('[HELP] Obfuscation active but no additional protections: consider Mix strings or Private for balance.]')

        # Combine issues and helps into a single dialog
        all_msgs = issues + helps
        if all_msgs:
            lines = [f"{i:02d}) {msg}" for i, msg in enumerate(all_msgs, 1)]
            body = ('\n' + '─' * 53 + '\n').join(lines)
            title = 'Analysis Result'
            if any(msg.startswith('[ERROR]') for msg in all_msgs):
                messagebox.showerror(title, body)
            elif any(msg.startswith('[WARN]') for msg in all_msgs):
                messagebox.showwarning(title, body)
            else:
                messagebox.showinfo(title, body)
        else:
            messagebox.showinfo('Analysis Result', 'No issues found. Configuration looks solid!')

    # -------------------- Save --------------------
    def _add_flag_once(self, opts: List[str], flag: str):
        if flag not in opts:
            opts.append(flag)

    def _apply_project_build_side_effects(self, p, build_mode: str):
        build_mode = (build_mode or 'debug').lower()

        def set_if_has(attr, value):
            try:
                setattr(p, attr, value)
            except Exception:
                pass

        if build_mode == 'debug':
            set_if_has('onefile', False)
            set_if_has('clean', False)
            set_if_has('strip', False)
            set_if_has('debug', True)
            set_if_has('upx', False)
            set_if_has('noupx', True)
            set_if_has('console', True)
        else:
            set_if_has('onefile', True)
            set_if_has('clean', True)
            set_if_has('strip', True)
            set_if_has('debug', False)
            set_if_has('upx', True)
            set_if_has('noupx', False)

    def save(self):
        p = self.project

        p.script = self.e_script.get().strip()
        p.output = self.e_output.get().strip()

        if p.script and Path(p.script).suffix.lower() != '.py':
            messagebox.showerror('Error', f'Invalid script: {p.script} (must be .py)')
            return

        # Persist edition, dist mode & build_mode
        p.pyarmor_edition = self.var_edition.get()
        p.pyarmor_dist_mode = self.var_dist_mode.get()
        p.build_mode = self.var_build_mode.get()

        # Store interpreter path (both attrs for compatibility with runner)
        interp = (self.var_python_exec.get() or '').strip()
        p.python_exec_path = interp
        p.pyarmor_python_exe = interp

        # If PyArmor OFF
        if not self.var_use_pyarmor.get():
            p.use_pyarmor = False
            self._apply_project_build_side_effects(p, p.build_mode)
            self.saved = True
            self.win.destroy()
            return

        # PyArmor ON
        p.use_pyarmor = True
        p.pyarmor_use_outer_key = self.var_use_outer_key.get()
        p.pyarmor_command = (self.var_command.get() or '').strip()

        p.pyarmor_obf_code = self.var_obf_code.get()
        p.pyarmor_mix_str = self.var_mix_str.get()
        p.pyarmor_private = self.var_private.get()
        p.pyarmor_restrict = self.var_restrict.get()
        p.pyarmor_assert_import = self.var_assert_import.get()
        p.pyarmor_assert_call = self.var_assert_call.get()
        p.pyarmor_platform = self._get_platform_text()
        p.pyarmor_pack = (self.var_pack.get() or '').strip()
        p.pyarmor_expired = (self.e_expired.get() or '').strip()
        p.pyarmor_bind_device = (self.e_bind_device.get() or '').strip()

        # Pro-only persistence
        p.pyarmor_enable_rft = bool(self.var_rft.get())
        p.pyarmor_enable_bcc = bool(self.var_bcc.get())
        p.pyarmor_enable_jit = bool(self.var_jit.get())
        p.pyarmor_enable_themida = bool(self.var_themida.get())
        p.pyarmor_enable_fly = bool(self.var_fly.get())

        if p.pyarmor_command and p.pyarmor_command not in ['gen', 'pack', 'obfuscate']:
            messagebox.showerror('Error', f'Invalid PyArmor command: {p.pyarmor_command}')
            return
        if p.pyarmor_expired:
            try:
                datetime.strptime(p.pyarmor_expired, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror('Error', f'Invalid expiration date: {p.pyarmor_expired} (format: yyyy-mm-dd)')
                return
        if p.pyarmor_restrict or p.pyarmor_assert_import or p.pyarmor_assert_call:
            messagebox.showwarning('Warning', 'Restrictive PyArmor options can cause runtime errors. Use Analyze to check stability.')

        # Dist folder
        if self.var_dist_mode.get() == 'auto':
            p.pyarmor_dist_dir = str(Path(p.output) / 'dist') if p.output else 'dist'
        else:
            p.pyarmor_dist_dir = (self.e_dist_dir.get() or '').strip() or 'dist'

        # Build options (identical to the Preview logic)
        opts = self._build_options_from_ui()

        # Notice if Pro-only flags on Basic
        if (p.pyarmor_edition != 'pro') and any((p.pyarmor_enable_rft, p.pyarmor_enable_bcc, p.pyarmor_enable_jit, p.pyarmor_enable_themida, p.pyarmor_enable_fly)):
            messagebox.showwarning('Notice', 'Pro-only options are enabled, but edition is Basic. They were ignored when saving.')

        # Sync PyInstaller onefile with pack (best-effort)
        try:
            if p.pyarmor_pack == 'onefile':
                p.onefile = True
            elif p.pyarmor_pack == 'onedir':
                p.onefile = False
        except Exception:
            pass

        p.pyarmor_options = ' '.join(opts)

        # Apply Build side effects (sets e.g. onefile based on Build-Mode)
        self._apply_project_build_side_effects(p, p.build_mode)

        # Align onefile with explicit pack choice
        if p.use_pyarmor and p.pyarmor_pack in ('onefile', 'onedir'):
            try:
                p.onefile = (p.pyarmor_pack == 'onefile')
            except Exception:
                pass

        # Persist Pack Options selections
        p.pyinstaller_windowed = bool(self.var_pack_windowed.get())
        p.pyinstaller_icon_path = (self.var_pack_icon.get() or '').strip()

        self.saved = True
        self.win.destroy()


# --- Small helper: return safe filetypes (None -> All Files)
def book_filetypes(filetypes):
    return filetypes or [('All Files', '*.*')]
