import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional
import os
import shlex
import sys
import subprocess
import re
from dataclasses import dataclass

try:
    from .tooltip import CreateToolTip
except Exception:
    def CreateToolTip(widget, text: str):
        try:
            widget.tooltip_text = text
        except Exception:
            pass

# ======= NEU: globale UI-Parameter für konsistente Abstände =======
UI_PADX = 2          # horizontaler Außenabstand
UI_PADY = 2          # vertikaler Außenabstand
UI_SECTION_Y = 3     # Extra-Abstand zwischen Sektionen
UI_INNER = 3         # Innenabstand in LabelFrames

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


# ---------- Helpers: Lists / Bindings ----------

def _normalize_list(text: str) -> List[str]:
    if not text:
        return []
    out: List[str] = []
    for chunk in text.replace(';', ',').split(','):
        v = chunk.strip()
        if v:
            out.append(v)
    # dedupe (case-insensitive), order preserving
    seen = set()
    uniq: List[str] = []
    for v in out:
        k = v.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(v)
    return uniq


@dataclass
class DeviceBindings:
    macs: List[str]
    hdds: List[str]
    ips: List[str]
    require_all: bool = False

    def as_cli_flags(self) -> List[str]:
        """
        - AND (eine Maschine, mehrere Merkmale): ein -b "v1 v2 v3"
        - OR  (einzelne Werte): mehrere -b "v"
        """
        vals = self.macs + self.hdds + self.ips
        if not vals:
            return []
        if self.require_all:
            joined = ' '.join(vals).replace('"', r'\"')
            return ['-b', f'"{joined}"']
        flags: List[str] = []
        for v in vals:
            safe = v.replace('"', r'\"')
            flags += ['-b', f'"{safe}"']
        return flags

    def summary(self) -> str:
        logic = "AND" if self.require_all else "OR"
        parts = []
        if self.macs:
            parts.append(f"MACs[{len(self.macs)}]")
        if self.hdds:
            parts.append(f"HDDs[{len(self.hdds)}]")
        if self.ips:
            parts.append(f"IPs[{len(self.ips)}]")
        kinds = ", ".join(parts) if parts else "none"
        return f"{kinds}  • Logic: {logic}"


def _bindings_from_project(p) -> DeviceBindings:
    def _to_list(v) -> List[str]:
        if not v:
            return []
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v).replace(' ', ',')
        return _normalize_list(s)

    require_all = bool(getattr(p, 'pyarmor_bind_require_all', False))
    return DeviceBindings(
        macs=_to_list(getattr(p, 'pyarmor_bind_macs', [])),
        hdds=_to_list(getattr(p, 'pyarmor_bind_hdds', [])),
        ips=_to_list(getattr(p, 'pyarmor_bind_ips', [])),
        require_all=require_all
    )


def _bindings_to_project(p, b: DeviceBindings) -> None:
    setattr(p, 'pyarmor_bind_macs', list(b.macs))
    setattr(p, 'pyarmor_bind_hdds', list(b.hdds))
    setattr(p, 'pyarmor_bind_ips', list(b.ips))
    setattr(p, 'pyarmor_bind_require_all', bool(b.require_all))


def _parse_hdinfo_text(text: str) -> Tuple[List[str], List[str], List[str]]:
    macs, hdds, ips = [], [], []
    for line in (text or '').splitlines():
        line = line.strip()
        m = re.search(r":\s*'([^']*)'", line)
        value = m.group(1).strip() if m else ''
        if not value:
            continue
        low = line.lower()
        if 'mac address' in low:
            macs.append(value)
        elif 'harddisk serial' in low or 'hard disk serial' in low:
            hdds.append(value)
        elif 'ipv4 address' in low:
            ips.append(value)
    macs = list(dict.fromkeys(macs))
    hdds = list(dict.fromkeys(hdds))
    ips  = list(dict.fromkeys(ips))
    return macs, hdds, ips


# ---------- Mini dialog ----------

class DeviceBindingsDialog(tk.Toplevel):
    """
    Einfacher Dialog zur Konfiguration von Gerätebindungen (MAC/HDD/IP)
    mit hdinfo-Probe – ohne Pro-/Keyfile-Funktionen.
    """
    def __init__(self, master, current: DeviceBindings, get_python_exe_cb):
        super().__init__(master)
        self.title("Device bindings")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.get_python_exe_cb = get_python_exe_cb

        self.v_macs = tk.StringVar(value=", ".join(current.macs))
        self.v_hdds = tk.StringVar(value=", ".join(current.hdds))
        self.v_ips  = tk.StringVar(value=", ".join(current.ips))
        self.v_and  = tk.BooleanVar(value=current.require_all)

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        def row(lbl, var, tip):
            rf = ttk.Frame(frm); rf.pack(fill="x", pady=4)
            ttk.Label(rf, text=lbl, width=20).pack(side="left")
            e = ttk.Entry(rf, textvariable=var, width=56)
            e.pack(side="left", fill="x", expand=True)
            CreateToolTip(e, tip)
            return e

        self.e_hdds = row("HDD serials:", self.v_hdds, "Comma/semicolon separated (e.g. HXS2000CN2A)")
        self.e_macs = row("MAC addresses:", self.v_macs, "Comma/semicolon separated (e.g. 00:16:3e:35:19:3d)")
        self.e_ips  = row("IPv4 addresses:", self.v_ips,  "Comma/semicolon separated (e.g. 128.16.4.10)")

        chk = ttk.Checkbutton(frm, text="All bindings must match (AND)", variable=self.v_and)
        chk.pack(anchor="w", pady=(6, 2))
        CreateToolTip(chk, 'ON = one -b "mac ip hdd". OFF = many -b values (OR).')

        # HDINFO probe row
        pr = ttk.Frame(frm); pr.pack(fill="x", pady=(8, 6))
        ttk.Button(pr, text="Probe this machine (hdinfo)", command=self._probe_hdinfo).pack(side="left")
        self.lbl_probe = ttk.Label(pr, text="", foreground="#666")
        self.lbl_probe.pack(side="left", padx=8)

        # bottom buttons
        bb = ttk.Frame(frm); bb.pack(fill="x", pady=(8, 0))
        ttk.Button(bb, text="Cancel", command=self._cancel).pack(side="right", padx=(8, 0))
        ttk.Button(bb, text="OK", style="Accent.TButton", command=self._ok).pack(side="right")

        self.result: DeviceBindings | None = None
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.e_hdds.focus_set()

    def _probe_hdinfo(self):
        pyexe = self.get_python_exe_cb()
        try:
            proc = subprocess.run(
                [pyexe, "-m", "pyarmor.cli.hdinfo"],
                capture_output=True, text=True, check=True
            )
            stdout = proc.stdout or proc.stderr or ""
            macs, hdds, ips = _parse_hdinfo_text(stdout)
            cur_macs = _normalize_list(self.v_macs.get()); cur_hdds = _normalize_list(self.v_hdds.get()); cur_ips = _normalize_list(self.v_ips.get())
            new_macs = list(dict.fromkeys(cur_macs + macs))
            new_hdds = list(dict.fromkeys(cur_hdds + hdds))
            new_ips  = list(dict.fromkeys(cur_ips  + ips))
            self.v_macs.set(", ".join(new_macs))
            self.v_hdds.set(", ".join(new_hdds))
            self.v_ips.set(", ".join(new_ips))
            self.lbl_probe.configure(text="hdinfo OK")
        except Exception as e:
            self.lbl_probe.configure(text=f"hdinfo failed: {e}")

    def _ok(self):
        macs = _normalize_list(self.v_macs.get())
        hdds = _normalize_list(self.v_hdds.get())
        ips  = _normalize_list(self.v_ips.get())
        self.result = DeviceBindings(macs=macs, hdds=hdds, ips=ips, require_all=self.v_and.get())
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ---------- More Options dialog ----------

class MoreOptionsDialog(tk.Toplevel):
    """Extra pyarmor gen options (nur Basic-relevante Optionen)."""
    def __init__(self, master, current: dict):
        super().__init__(master)
        self.title("PyArmor – More Options")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # state
        self.v_recursive = tk.BooleanVar(value=bool(current.get('recursive')))
        self.v_exclude   = tk.StringVar(value=",".join(current.get('exclude', [])))
        self.v_inpkg     = tk.BooleanVar(value=bool(current.get('inpackage')))
        self.v_prefix    = tk.StringVar(value=current.get('prefix', ""))
        self.v_obfmod    = tk.StringVar(value=str(current.get('obf_module', "")))
        # REMOVED: no_wrap is now in main GUI
        self.v_binddata  = tk.StringVar(value=current.get('bind_data', ""))
        self.v_period    = tk.StringVar(value=str(current.get('period', "")))
        self.v_use_rt    = tk.StringVar(value=current.get('use_runtime', ""))

        frm = ttk.Frame(self, padding=12); frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        def row(r, label, var, width=46, browse=False, directory=False, tip=None):
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="e", padx=6, pady=4)
            f = ttk.Frame(frm); f.grid(row=r, column=1, sticky="ew")
            e = ttk.Entry(f, textvariable=var, width=width); e.grid(row=0, column=0, sticky="ew")
            if browse:
                def pick():
                    path = filedialog.askdirectory() if directory else filedialog.askopenfilename()
                    if path: var.set(path)
                ttk.Button(f, text="...", width=3, command=pick).grid(row=0, column=1, padx=6)
            if tip:
                CreateToolTip(e, tip)
            return e

        ttk.Checkbutton(frm, text="Recursive (-r / --recursive)",
                        variable=self.v_recursive).grid(row=0, column=1, sticky="w")
        CreateToolTip(frm, "Recurse into subfolders when obfuscating.")

        row(1, "Exclude pattern(s):", self.v_exclude, tip="Comma/semicolon-separated globs; each emits --exclude PATTERN")
        ttk.Checkbutton(frm, text="In-package (-i / --in-package)",
                        variable=self.v_inpkg).grid(row=2, column=1, sticky="w")
        row(3, "Prefix (--prefix):", self.v_prefix, tip="Runtime path prefix (use with -i).")
        row(4, "Obfuscate modules (--obf-module 0/1):", self.v_obfmod, width=12, tip="Leave empty to skip; 0 or 1.")
        # REMOVED ROW for --no-wrap here.
        row(5, "Bind data (--bind-data):", self.v_binddata, tip="Custom data signature to bind.")
        row(6, "Period seconds (--period):", self.v_period, width=12, tip="Positive integer; leave blank to skip.")
        row(7, "Use runtime dir (--use-runtime):", self.v_use_rt, browse=True, directory=True,
            tip="Existing runtime folder to reuse.")

        bb = ttk.Frame(frm); bb.grid(row=8, column=0, columnspan=2, pady=(10,0), sticky="e")
        ttk.Button(bb, text="Cancel", command=self._cancel).pack(side="right", padx=6)
        ttk.Button(bb, text="OK", style="Accent.TButton", command=self._ok).pack(side="right")

        self.result = None
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _ok(self):
        def _norm_list(s: str):
            return [p.strip() for p in re.split(r"[;,]", s or "") if p.strip()]

        res = {
            "recursive": bool(self.v_recursive.get()),
            "exclude": _norm_list(self.v_exclude.get()),
            "inpackage": bool(self.v_inpkg.get()),
            "prefix": (self.v_prefix.get() or "").strip(),
            "obf_module": (self.v_obfmod.get() or "").strip(),
            # no_wrap removed from more options
            "bind_data": (self.v_binddata.get() or "").strip(),
            "period": (self.v_period.get() or "").strip(),
            "use_runtime": (self.v_use_rt.get() or "").strip(),
        }
        self.result = res
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ---------- Main Editor ----------

class PyarmorEditor:
    """PyArmor configuration editor — Basic-Features, nur 'gen' (kein pack / kein PyInstaller)."""
    def __init__(self, master, project):
        # KEIN Pro-Lizenz-Check mehr
        self.master = master
        self.project = project
        self.win = None
        self.saved = False

        # --- Master switches ---
        self.var_use_pyarmor = tk.BooleanVar(value=getattr(project, 'use_pyarmor', False))
        self.var_build_mode = tk.StringVar(value=(getattr(project, 'build_mode', None) or 'debug'))
        self.var_dist_mode = tk.StringVar(value=getattr(project, 'pyarmor_dist_mode', 'auto'))

        # --- PyArmor state/flags ---
        self.var_use_outer_key = tk.BooleanVar(value=getattr(project, 'pyarmor_use_outer_key', False))
        self.var_obf_code = tk.StringVar(value=(getattr(project, 'pyarmor_obf_code', None) or '0'))
        self.var_mix_str = tk.BooleanVar(value=getattr(project, 'pyarmor_mix_str', False))
        self.var_private = tk.BooleanVar(value=getattr(project, 'pyarmor_private', False))
        self.var_restrict = tk.BooleanVar(value=getattr(project, 'pyarmor_restrict', False))
        self.var_assert_import = tk.BooleanVar(value=getattr(project, 'pyarmor_assert_import', False))
        self.var_assert_call = tk.BooleanVar(value=getattr(project, 'pyarmor_assert_call', False))
        # NEW: visible no-wrap toggle in main GUI
        self.var_no_wrap = tk.BooleanVar(value=getattr(project, 'pyarmor_no_wrap', False))

        # --- Usage limits toggles ---
        self.var_use_expire = tk.BooleanVar(
            value=getattr(project, 'pyarmor_use_expire', bool(getattr(project, 'pyarmor_expired', '').strip()))
        )
        self.var_use_bind_disk = tk.BooleanVar(
            value=getattr(project, 'pyarmor_use_bind_device', bool(getattr(project, 'pyarmor_bind_device', '').strip()))
        )
        self.var_use_device_bindings = tk.BooleanVar(
            value=getattr(project, 'pyarmor_use_device_bindings', True)
        )

        # --- Platform selection ---
        self.var_platform_choice = tk.StringVar(value='Current system (auto)')

        # Python interpreter
        initial_py = getattr(project, 'pyarmor_python_exe', None) or getattr(project, 'python_exec_path', '')
        self.var_python_exec = tk.StringVar(value=initial_py or '')

        # Manual preview editing
        self.var_manual_preview = tk.BooleanVar(value=False)
        self._preview_user_dirty = False

        # --- More Options (persistierbar)
        self.more_opts: dict = dict(getattr(project, "pyarmor_more_opts", {}) or {})

        # Widget refs
        self.cb_platform = None
        self.e_platform_custom = None
        self.lbl_bind_summary: Optional[ttk.Label] = None
        self._bind_row_container: Optional[ttk.Frame] = None

        self.e_expired = None
        self.e_bind_device = None

        # --- Sync: Restrict ⇒ Private (UI & CLI)
        self.var_restrict.trace_add('write', lambda *_: self._sync_restrict_private_ui())

    # ====== NEU: zentrale Padding-Helfer ======
    def _apply_uniform_padding(self, parent: tk.Misc):
        """Setzt einheitliche Außen- und Innenabstände für alle Kinder (grid & pack)."""
        for w in parent.winfo_children():
            # grid
            try:
                if w.grid_info():
                    w.grid_configure(padx=UI_PADX, pady=UI_PADY)
            except tk.TclError:
                pass
            # pack
            try:
                if w.pack_info():
                    w.pack_configure(padx=UI_PADX, pady=UI_PADY)
            except tk.TclError:
                pass
            # Innenabstand in LabelFrames
            try:
                if isinstance(w, ttk.Labelframe):
                    w.configure(padding=UI_INNER)
            except Exception:
                pass
            # Rekursiv
            self._apply_uniform_padding(w)

    def _bump_section_spacing(self, *sections: ttk.Labelframe | ttk.Frame):
        """Gibt Sektionen extra vertikalen Abstand."""
        for s in sections:
            try:
                s.grid_configure(pady=UI_SECTION_Y)
            except tk.TclError:
                pass

    @staticmethod
    def _quote_for_e(arg: str) -> str:
        if not arg:
            return arg
        if os.name == 'nt':
            a = arg.replace('"', '\\"')
            if ' ' in a or any(c in a for c in (';', ',', '(', ')')):
                return f'"{a}"'
            return a
        return shlex.quote(arg)

    def _quote_path(self, p: str) -> str:
        if not p:
            return ''
        if os.name == 'nt':
            q = p.replace('"', '\\"')
            return f'"{q}"' if ' ' in q or any(c in q for c in (';', ',', '(', ')')) else q
        return shlex.quote(p)

    # ----- python exe resolution for hdinfo -----
    def _get_python_exe_for_hdinfo(self) -> str:
        chosen = (self.var_python_exec.get() or '').strip()
        if chosen:
            return chosen
        return sys.executable

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title('PyArmor Editor')
        self.win.geometry('880x890')
        self.win.transient(self.master)
        self.win.grab_set()
        try:
            self.win.iconbitmap('autoPy++.ico')
        except Exception:
            pass

        # Stil leicht „griffiger“ machen
        style = ttk.Style(self.win)
        style.configure("TButton", padding=(10, 6))
        style.configure("TCheckbutton", padding=(4, 2))
        style.configure("TRadiobutton", padding=(4, 2))

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

        # ===== Header =====
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
        CreateToolTip(rb_dbg, 'Debug: fast iteration. Safer defaults.')
        CreateToolTip(rb_rel, 'Release: optimized distribution. Higher obfuscation.')

        cb_use = ttk.Checkbutton(header, text='Use PyArmor', variable=self.var_use_pyarmor, command=self._toggle_enabled)
        cb_use.grid(row=0, column=1, sticky='w')
        CreateToolTip(cb_use, 'Enable or disable PyArmor for this project.')

        # KEINE Edition-Auswahl mehr – Basic ist implizit

        # ===== Build targets =====
        self.targets = ttk.LabelFrame(root, text='Build Targets')
        self.targets.grid(row=1, column=0, columnspan=2, sticky='ew', pady=6)
        self.e_script = row(self.targets, 'Script (.py):', 0, getattr(self.project, 'script', ''), file_button=True, filetypes=[('Python Files', '*.py')])
        self.e_output = row(self.targets, 'Output folder:', 1, getattr(self.project, 'output', ''), directory=True)
        CreateToolTip(self.e_script, 'Entry script (.py) to obfuscate.')
        CreateToolTip(self.e_output, 'Output folder for your build artifacts.')
        self.e_output.bind('<KeyRelease>', lambda e: (self._recompute_dist_from_output(), self._rebuild_preview()))

        # --- Python interpreter picker ---
        py_row = ttk.Frame(self.targets)
        py_row.grid(row=2, column=0, columnspan=2, sticky='ew', pady=2)
        ttk.Label(py_row, text='Other python.exe ?:').grid(row=0, column=0, sticky='e', padx=5)
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
        CreateToolTip(self.e_python, 'Use this specific Python interpreter for probing/builds (optional).')
        self.targets.grid_columnconfigure(1, weight=1)

        # ===== PyArmor Dist =====
        self.build = ttk.LabelFrame(root, text='PyArmor Build (Dist)')
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

        def row_build(parent, label_text, row, default=''):
            lbl = ttk.Label(parent, text=label_text)
            lbl.grid(row=row, column=0, sticky='e', padx=5, pady=2)
            frame = ttk.Frame(parent)
            frame.grid(row=row, column=1, sticky='ew', pady=2)
            ent = ttk.Entry(frame, width=72)
            ent.grid(row=0, column=0, sticky='ew')
            ent.insert(0, default or '')
            ttk.Button(frame, text='...', command=lambda: self._choose(ent, True, None)).grid(row=0, column=1, padx=5)
            parent.grid_columnconfigure(1, weight=1)
            return ent

        self.e_dist_dir = row_build(self.build, 'PyArmor dist folder:', 1, getattr(self.project, 'pyarmor_dist_dir', ''))
        CreateToolTip(self.e_dist_dir, 'PyArmor output directory (dist).')
        self.e_dist_dir.bind('<KeyRelease>', lambda e: self._rebuild_preview())

        # ===== Security Level =====
        self.sec = ttk.LabelFrame(root, text='Security Level')
        self.sec.grid(row=3, column=0, columnspan=2, sticky='ew', pady=6)
        ttk.Button(self.sec, text='Test', command=lambda: self._preset('Test')).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(self.sec, text='Easy', command=lambda: self._preset('Easy')).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.sec, text='Medium', command=lambda: self._preset('Medium')).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(self.sec, text='Hard', command=lambda: self._preset('Hard')).grid(row=0, column=3, padx=5, pady=2)
        ttk.Button(self.sec, text='Ultra', command=lambda: self._preset('Ultra')).grid(row=0, column=4, padx=5, pady=2)

        CreateToolTip(self.sec, 'Presets set recommended combinations. Hard keep assertions OFF by default.')

        # ===== Advanced Options =====
        self.adv = ttk.LabelFrame(root, text='PyArmor – Advanced Options')
        self.adv.grid(row=4, column=0, columnspan=2, sticky='ew', pady=6, ipadx=4, ipady=2)
        self.adv.grid_columnconfigure(0, weight=1)
        self.adv.grid_columnconfigure(1, weight=1)

        # --- Obfuscation ---
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

        self.ck_mix = ttk.Checkbutton(lf_obf, text='Mix strings', variable=self.var_mix_str, command=self._rebuild_preview)
        self.ck_mix.grid(row=1, column=0, columnspan=2, sticky='w', padx=6, pady=2)

        self.ck_private = ttk.Checkbutton(lf_obf, text='Private', variable=self.var_private, command=self._rebuild_preview)
        self.ck_private.grid(row=2, column=0, columnspan=2, sticky='w', padx=6, pady=2)

        self.ck_restr = ttk.Checkbutton(lf_obf, text='Restrict', variable=self.var_restrict, command=self._rebuild_preview)
        self.ck_restr.grid(row=3, column=0, columnspan=2, sticky='w', padx=6, pady=2)

        # NEW: --no-wrap in main GUI
        self.ck_nowrap = ttk.Checkbutton(lf_obf, text='No wrap (--no-wrap)',
                                         variable=self.var_no_wrap, command=self._rebuild_preview)
        self.ck_nowrap.grid(row=4, column=0, columnspan=2, sticky='w', padx=6, pady=2)
        CreateToolTip(self.ck_nowrap,
                      'Disable wrap mode: functions stay restored (faster/compatible, slightly less secure).')

        # KEINE Pro-Hardening-Buttons (RFT/BCC/JIT/Themida) mehr

        # More Options button
        more_row = ttk.Frame(lf_obf)
        more_row.grid(row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=(6, 10))
        ttk.Button(more_row, text="More Options…", command=self._open_more_options).pack(side="right")
        CreateToolTip(more_row, "Open extra PyArmor gen options (recursive, exclude, in-package, prefix, obf-module, bind-data, period, use-runtime).")

        # -- Right: Runtime checks --
        lf_runtime = ttk.LabelFrame(self.adv, text='Runtime checks')
        lf_runtime.grid(row=0, column=1, sticky='nsew', padx=(3, 6), pady=6)
        lf_runtime.grid_columnconfigure(0, weight=1)

        self.ck_ai = ttk.Checkbutton(lf_runtime, text='Assert import', variable=self.var_assert_import, command=self._rebuild_preview)
        self.ck_ai.grid(row=0, column=0, sticky='w', padx=6, pady=2)

        self.ck_ac = ttk.Checkbutton(lf_runtime, text='Assert call', variable=self.var_assert_call, command=self._rebuild_preview)
        self.ck_ac.grid(row=1, column=0, sticky='w', padx=6, pady=2)

        self.ck_outer = ttk.Checkbutton(lf_runtime, text='Use outer key', variable=self.var_use_outer_key, command=self._rebuild_preview)
        self.ck_outer.grid(row=2, column=0, sticky='w', padx=6, pady=(2, 6))

        # Separator
        ttk.Separator(self.adv, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky='ew', padx=6, pady=(0, 6))

        # -- Target platform --
        lf_platform = ttk.LabelFrame(self.adv, text='Target platform')
        lf_platform.grid(row=2, column=0, columnspan=2, sticky='ew', padx=6, pady=(0, 6))
        lf_platform.grid_columnconfigure(1, weight=1)

        ttk.Label(lf_platform, text='Platform(s):').grid(row=0, column=0, sticky='e', padx=6, pady=4)
        plat_row = ttk.Frame(lf_platform); plat_row.grid(row=0, column=1, sticky='ew')
        plat_row.grid_columnconfigure(0, weight=0)
        plat_row.grid_columnconfigure(1, weight=1)

        self.cb_platform = ttk.Combobox(plat_row, textvariable=self.var_platform_choice, values=PLATFORM_CHOICES, state='readonly', width=28)
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

        self.var_use_expire.trace_add('write', lambda *_: self._toggle_usage_controls())
        cb_exp = ttk.Checkbutton(lf_limit, text='Use Expire (YYYY-MM-DD):', variable=self.var_use_expire, command=self._rebuild_preview)
        cb_exp.grid(row=0, column=0, sticky='e', padx=6, pady=4)
        self.e_expired = ttk.Entry(lf_limit)
        self.e_expired.grid(row=0, column=1, sticky='ew', padx=(0, 12), pady=4)
        self.e_expired.insert(0, getattr(self.project, 'pyarmor_expired', '') or '')
        self.e_expired.bind('<KeyRelease>', lambda e: self._rebuild_preview())

        self.var_use_bind_disk.trace_add('write', lambda *_: self._toggle_usage_controls())
        cb_bind = ttk.Checkbutton(lf_limit, text='Use bind device (legacy):', variable=self.var_use_bind_disk, command=self._rebuild_preview)
        cb_bind.grid(row=0, column=2, sticky='e', padx=6, pady=4)
        self.e_bind_device = ttk.Entry(lf_limit)
        self.e_bind_device.grid(row=0, column=3, sticky='ew', pady=4)
        self.e_bind_device.insert(0, getattr(self.project, 'pyarmor_bind_device', '') or '')
        self.e_bind_device.bind('<KeyRelease>', lambda e: self._rebuild_preview())
        CreateToolTip(self.e_bind_device, 'Optional single binding via --bind-disk. Prefer the Device bindings dialog below.')

        self.var_use_device_bindings.trace_add('write', lambda *_: self._toggle_usage_controls())
        bind_head = ttk.Frame(lf_limit)
        bind_head.grid(row=1, column=0, columnspan=4, sticky='w', pady=(8, 0))
        cb_use_b = ttk.Checkbutton(bind_head, text='Use Device bindings', variable=self.var_use_device_bindings, command=self._rebuild_preview)
        cb_use_b.pack(side='left', padx=(0, 8))

        self._bind_row_container = ttk.Frame(lf_limit)
        self._bind_row_container.grid(row=2, column=0, columnspan=4, sticky='ew', pady=(4, 2))
        ttk.Label(self._bind_row_container, text="Bindings:").pack(side="left")
        self.lbl_bind_summary = ttk.Label(self._bind_row_container, text="", foreground="#444")
        self.lbl_bind_summary.pack(side="left", padx=(6, 10))
        ttk.Button(self._bind_row_container, text="Edit…", command=self._edit_device_bindings).pack(side="left")

        # ===== Preview =====
        self.preview = ttk.LabelFrame(root, text='Preview')
        self.preview.grid(row=6, column=0, columnspan=2, sticky='nsew', pady=(6, 4))
        root.grid_rowconfigure(6, weight=1)

        head = ttk.Frame(self.preview); head.pack(fill='x', padx=6, pady=(6, 0))
        ttk.Button(head, text='Reset to Auto', command=self._reset_preview_auto).pack(side='left', padx=(8, 0))

        self.txt_preview = scrolledtext.ScrolledText(self.preview, width=80, height=4)
        self.txt_preview.pack(fill='both', expand=True, padx=6, pady=(6, 2))
        self.txt_preview.bind('<<Modified>>', self._on_preview_modified)

        self.lbl_interpreter = ttk.Label(self.preview, text='', foreground='#7a7a7a')
        self.lbl_interpreter.pack(anchor='w', padx=8, pady=(0, 6))

        self._set_preview('(PyArmor disabled)' if not self.var_use_pyarmor.get() else '')
        self._on_toggle_manual_preview()

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
        self._refresh_bind_summary_from_project()
        self._toggle_usage_controls()
        self._rebuild_preview()

        # Sync Restrict ⇒ Private nach dem Aufbau der Widgets
        self._sync_restrict_private_ui()

        # ===== NEU: globale Abstände einmal anwenden =====
        self._apply_uniform_padding(root)
        self._bump_section_spacing(self.targets, self.build, self.sec, self.adv, self.preview, btns)

        if self.win and self.win.winfo_exists():
            self.win.wait_window()
        return self.saved

    # -------------------- Internals --------------------
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
        self.btn_analyze.configure(state=('normal' if enabled else 'disabled'))
        if not enabled:
            self._set_preview('(PyArmor disabled)')
        else:
            self._rebuild_preview()

    def _toggle_usage_controls(self):
        try:
            self.e_expired.configure(state=('normal' if self.var_use_expire.get() else 'disabled'))
        except Exception:
            pass
        try:
            self.e_bind_device.configure(state=('normal' if self.var_use_bind_disk.get() else 'disabled'))
        except Exception:
            pass
        try:
            state = ('normal' if self.var_use_device_bindings.get() else 'disabled')
            for ch in self._bind_row_container.winfo_children():
                try:
                    ch.configure(state=state)
                except tk.TclError:
                    pass
        except Exception:
            pass

    # --- Restrict ⇒ Private (UI sperren & Preview aktualisieren) ---
    def _sync_restrict_private_ui(self):
        try:
            if self.var_restrict.get():
                self.var_private.set(False)
                try:
                    self.ck_private.configure(state='disabled')
                except Exception:
                    pass
            else:
                try:
                    self.ck_private.configure(state='normal')
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self._rebuild_preview()
        except Exception:
            pass

    # --- Presets ---
    def _preset(self, level: str):
        # --- Baseline: alles aus / minimaler Schutz
        self.var_obf_code.set('0')
        self.var_mix_str.set(False)
        self.var_private.set(False)
        self.var_restrict.set(False)
        self.var_assert_import.set(False)
        self.var_assert_call.set(False)
        self.var_use_outer_key.set(False)
        self.var_no_wrap.set(True)  # Wrap AUS = schneller/robuster Default

        if level == 'Test':
            self.var_obf_code.set('0')
            self.var_no_wrap.set(True)

        elif level == 'Easy':
            self.var_obf_code.set('1')
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_no_wrap.set(True)

        elif level == 'Medium':
            self.var_obf_code.set('2')
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_assert_import.set(True)
            self.var_assert_call.set(True)
            self.var_no_wrap.set(True)

        elif level == 'Hard':
            self.var_obf_code.set('2')
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_restrict.set(True)
            self.var_assert_import.set(True)
            self.var_assert_call.set(True)
            self.var_use_outer_key.set(False)
            self.var_no_wrap.set(False)

        elif level == 'Ultra':
            self.var_obf_code.set('2')
            self.var_mix_str.set(True)
            self.var_private.set(True)
            self.var_restrict.set(True)
            self.var_assert_import.set(True)
            self.var_assert_call.set(True)
            self.var_use_outer_key.set(True)
            self.var_no_wrap.set(False)
        else:
            try:
                messagebox.showinfo('Info', f'Unknown preset: {level}')
            except Exception:
                pass

        self._apply_build_mode()
        self._sync_restrict_private_ui()

    def _apply_build_mode(self, init: bool = False):
        mode = (self.var_build_mode.get() or 'debug').lower()
        if mode == 'release' and self.var_obf_code.get() in ('0', '1'):
            self.var_obf_code.set('2')
        self._rebuild_preview()

    # ---------- Device Bindings integration ----------
    def _edit_device_bindings(self):
        cur = _bindings_from_project(self.project)
        dlg = DeviceBindingsDialog(self.win, cur, self._get_python_exe_for_hdinfo)
        self.win.wait_window(dlg)
        if dlg.result is None:
            self._refresh_bind_summary_from_project()
            self._rebuild_preview()
            return

        _bindings_to_project(self.project, dlg.result)
        self._refresh_bind_summary_from_project()
        self._rebuild_preview()

    def _refresh_bind_summary_from_project(self):
        if not self.lbl_bind_summary:
            return
        cur = _bindings_from_project(self.project)
        self.lbl_bind_summary.configure(text=cur.summary())

    # ---------- Preview helpers ----------
    def _get_preview_text(self) -> str:
        return (self.txt_preview.get('1.0', 'end') or '').strip()

    def _set_preview(self, text: str, *, force: bool = False):
        if self.var_manual_preview.get() and not force:
            return
        try:
            self.txt_preview.configure(state='normal')
            self.txt_preview.delete('1.0', 'end')
            self.txt_preview.insert('1.0', text or '')
        finally:
            if not self.var_manual_preview.get():
                self.txt_preview.configure(state='disabled')

    def _on_toggle_manual_preview(self):
        try:
            self.txt_preview.configure(state='normal' if self.var_manual_preview.get() else 'disabled')
        except tk.TclError:
            pass
        if not self.var_manual_preview.get():
            self._preview_user_dirty = False
            self._rebuild_preview()

    def _reset_preview_auto(self):
        self.var_manual_preview.set(False)
        self._on_toggle_manual_preview()

    def _on_preview_modified(self, event=None):
        if self.var_manual_preview.get():
            self._preview_user_dirty = True
        try:
            self.txt_preview.edit_modified(False)
        except Exception:
            pass

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
        choice = (self.var_platform_choice.get() or '').strip()
        if choice == 'Current system (auto)':
            return ''
        if choice == 'Custom...':
            return (self.e_platform_custom.get() or '').strip()
        return choice

    def _init_platform_choice_from_project(self):
        self.var_platform_choice.set('Current system (auto)')
        self._on_platform_selected()
        try:
            setattr(self.project, 'pyarmor_platform', '')
        except Exception:
            pass

    def _get_global_flags(self) -> List[str]:
        return ['-d'] if (self.var_build_mode.get() or 'debug').lower() == 'debug' else []

    def _open_more_options(self):
        dlg = MoreOptionsDialog(self.win, self.more_opts or {})
        self.win.wait_window(dlg)
        if dlg.result is not None:
            self.more_opts = dlg.result
            om = str(self.more_opts.get("obf_module", "")).strip()
            if om not in ("0", "1", ""):
                self.more_opts["obf_module"] = ""
            per = str(self.more_opts.get("period", "")).strip()
            if per and not per.isdigit():
                self.more_opts["period"] = ""
            self._rebuild_preview()

    def _build_options_from_ui(self) -> List[str]:
        if not self.var_use_pyarmor.get():
            return []

        opts: List[str] = []

        # --- Common PyArmor options ---
        obf = (self.var_obf_code.get() or '').strip()
        if obf:
            opts += ['--obf-code', obf]
        if self.var_mix_str.get():
            opts += ['--mix-str']

        if self.var_restrict.get():
            opts += ['--restrict']
        elif self.var_private.get():
            opts += ['--private']

        if self.var_assert_import.get():
            opts += ['--assert-import']
        if self.var_assert_call.get():
            opts += ['--assert-call']
        if self.var_use_outer_key.get():
            opts += ['--outer']

        # NEW: add --no-wrap from main GUI
        if self.var_no_wrap.get():
            opts.append('--no-wrap')

        platform_txt = self._get_platform_text()
        if platform_txt:
            opts += ['--platform', platform_txt]

        # Usage toggles
        expired = (self.e_expired.get() or '').strip() if self.e_expired else ''
        if self.var_use_expire.get() and expired:
            opts += ['--expired', expired]

        bind_device = (self.e_bind_device.get() or '').strip() if self.e_bind_device else ''
        if self.var_use_bind_disk.get() and bind_device:
            opts += ['--bind-disk', bind_device]

        # Device bindings (-b) nur einfache Projekt-Bindings
        if self.var_use_device_bindings.get():
            db = _bindings_from_project(self.project)
            vals = [v for v in (db.macs + db.hdds + db.ips) if v]
            if vals:
                if db.require_all:
                    joined = ' '.join(vals).replace('"', r'\"')
                    opts += ['-b', f'"{joined}"']
                else:
                    for v in vals:
                        safe = v.replace('"', r'\"')
                        opts += ['-b', f'"{safe}"']

        # ---- More Options → CLI ----
        mo = self.more_opts or {}
        if mo.get("recursive"):
            opts.append("-r")
        for pat in (mo.get("exclude") or []):
            if pat:
                opts += ["--exclude", pat]
        if mo.get("inpackage"):
            opts.append("-i")
        if mo.get("prefix"):
            opts += ["--prefix", mo["prefix"]]
        om = str(mo.get("obf_module", "")).strip()
        if om in ("0", "1"):
            opts += ["--obf-module", om]
        if mo.get("bind_data"):
            opts += ["--bind-data", mo["bind_data"]]
        per = str(mo.get("period", "")).strip()
        if per.isdigit() and int(per) > 0:
            opts += ["--period", per]
        if mo.get("use_runtime"):
            opts += ["--use-runtime", self._quote_path(mo["use_runtime"])]

        # Dist dir
        if self.var_dist_mode.get() == 'auto':
            output = (self.e_output.get() or '').strip()
            dist_dir = str(Path(output) / 'dist') if output else 'dist'
        else:
            dist_dir = (self.e_dist_dir.get() or '').strip() or 'dist'

        if '--output' not in opts:
            opts += ['--output', self._quote_path(dist_dir)]

        return opts

    def _rebuild_preview(self):
        if not self.var_use_pyarmor.get():
            self._set_preview('(PyArmor disabled)')
            self.lbl_interpreter.configure(text='')
            return

        if self.var_manual_preview.get():
            interp = (self.var_python_exec.get() or '').strip()
            self.lbl_interpreter.configure(
                text=(f'Interpreter: {interp}' if interp else 'Interpreter: (system default / PATH)')
            )
            return

        opts = self._build_options_from_ui()
        cmd_cli = 'gen'

        script = (self.e_script.get() or '').strip()
        script_arg = self._quote_path(script) if script else ''

        pieces = self._get_global_flags() + [cmd_cli] + opts + ([script_arg] if script_arg else [])

        preview = ' '.join(pieces).strip()

        self._set_preview(preview if preview else '(no options)')
        interp = (self.var_python_exec.get() or '').strip()
        self.lbl_interpreter.configure(
            text=(f'Interpreter: {interp}' if interp else 'Interpreter: (system default / PATH)')
        )

    def _analyze(self):
        issues: List[str] = []
        helps: List[str] = []

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

        if self.var_use_pyarmor.get():
            expired = (self.e_expired.get() or '').strip()
            dist_dir = (self.e_dist_dir.get() or '').strip()
            platform = (self._get_platform_text() or '').strip().lower()
            obf_code = (self.var_obf_code.get() or '').strip()
            bind_device = (self.e_bind_device.get() or '').strip()

            if not obf_code:
                issues.append('[ERROR] Obfuscation code is empty.')
                helps.append('[HELP] Select 0/1/2 from the dropdown.')
            elif obf_code not in ['0', '1', '2']:
                issues.append(f'[ERROR] Invalid obf-code: {obf_code} (must be 0, 1, or 2)')
                helps.append('[HELP] Use the combobox to select a valid level.')

            if not dist_dir:
                issues.append('[WARN] Dist folder is empty.')
                helps.append('[HELP] Use auto mode (relative to output) or specify a manual path.')

            if self.var_use_expire.get() and expired:
                try:
                    datetime.strptime(expired, '%Y-%m-%d')
                except ValueError:
                    issues.append(f'[ERROR] Invalid expiration date: {expired} (format: yyyy-mm-dd)')
                    helps.append('[HELP] Use YYYY-MM-DD format, e.g., 2025-12-31.')

            if self.var_use_bind_disk.get() and bind_device:
                serial_like = bind_device.replace('-', '').replace(':', '')
                if len(bind_device) < 5 or not serial_like.isalnum():
                    issues.append(f"[WARN] Bind device '{bind_device}' looks invalid.")
                    helps.append('[HELP] Use a device/disk serial number; test with --bind-disk to verify.')

            if platform:
                platforms = [p.strip().lower() for p in platform.split(',')]
                invalid_platforms = [p for p in platforms if not any(kw in p for kw in ['windows', 'linux', 'darwin', 'android']) and p != '']
                if invalid_platforms:
                    issues.append(f"[WARN] Invalid platform tag(s): {', '.join(invalid_platforms)}")
                    helps.append("Use tags like 'windows.x86_64' or comma-separated lists; see PyArmor docs.")
            else:
                helps.append("'Current system (auto)' uses host platform; specify for cross-compilation.")

            assertions_active = self.var_assert_import.get() or self.var_assert_call.get()
            if assertions_active and not self.var_restrict.get():
                issues.append('[WARN] Assertions without Restrict: inconsistent setup.')
                helps.append('Enable Restrict or disable assertions.')

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
    def _apply_project_build_side_effects(self, p, build_mode: str):
        build_mode = (build_mode or 'debug').lower()

        def set_if_has(attr, value):
            try:
                setattr(p, attr, value)
            except Exception:
                pass

    def _parse_manual_cmd(self, s: str):
        try:
            parts = shlex.split(s)
        except Exception:
            parts = s.strip().split()

        if not parts:
            return [], None

        if parts[0].lower() == 'gen':
            parts = parts[1:]

        script = None
        if parts and parts[-1].lower().endswith('.py'):
            script = parts[-1]
            parts = parts[:-1]

        return parts, script

    def save(self):
        p = self.project

        p.script = self.e_script.get().strip()
        p.output = self.e_output.get().strip()

        if p.script and Path(p.script).suffix.lower() != '.py':
            messagebox.showerror('Error', f'Invalid script: {p.script} (must be .py)')
            return

        # Edition ist implizit Basic
        p.pyarmor_edition = 'basic'
        p.pyarmor_dist_mode = self.var_dist_mode.get()
        p.build_mode = self.var_build_mode.get()

        interp = (self.var_python_exec.get() or '').strip()
        p.python_exec_path = interp
        p.pyarmor_python_exe = interp

        if not self.var_use_pyarmor.get():
            p.use_pyarmor = False
            self._apply_project_build_side_effects(p, p.build_mode)
            self.saved = True
            self.win.destroy()
            return

        p.use_pyarmor = True
        p.pyarmor_use_outer_key = self.var_use_outer_key.get()
        p.pyarmor_command = 'gen'

        p.pyarmor_obf_code = self.var_obf_code.get()
        p.pyarmor_mix_str = self.var_mix_str.get()
        p.pyarmor_private = self.var_private.get()
        p.pyarmor_restrict = self.var_restrict.get()
        p.pyarmor_assert_import = self.var_assert_import.get()
        p.pyarmor_assert_call = self.var_assert_call.get()
        p.pyarmor_platform = self._get_platform_text()
        p.pyarmor_no_wrap = bool(self.var_no_wrap.get())  # persist

        # Persist usage fields + toggles
        p.pyarmor_expired = (self.e_expired.get() or '').strip()
        p.pyarmor_bind_device = (self.e_bind_device.get() or '').strip()
        p.pyarmor_use_expire = bool(self.var_use_expire.get())
        p.pyarmor_use_bind_device = bool(self.var_use_bind_disk.get())
        p.pyarmor_use_device_bindings = bool(self.var_use_device_bindings.get())

        # Persist More Options (restliche Optionen)
        p.pyarmor_more_opts = dict(self.more_opts or {})

        if p.pyarmor_use_expire and p.pyarmor_expired:
            try:
                datetime.strptime(p.pyarmor_expired, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror('Error', f'Invalid expiration date: {p.pyarmor_expired} (format: yyyy-mm-dd)')
                return
        if p.pyarmor_restrict or p.pyarmor_assert_import or p.pyarmor_assert_call:
            messagebox.showwarning('Warning', 'Restrictive PyArmor options can cause runtime errors. Use Analyze to check stability.')

        if self.var_dist_mode.get() == 'auto':
            p.pyarmor_dist_dir = str(Path(p.output) / 'dist') if p.output else 'dist'
        else:
            p.pyarmor_dist_dir = (self.e_dist_dir.get() or '').strip() or 'dist'

        if self.var_manual_preview.get():
            manual_line = self._get_preview_text()
            if manual_line:
                opts_list, manual_script = self._parse_manual_cmd(manual_line)
                if manual_script:
                    p.script = manual_script.strip()
                    if p.script and Path(p.script).suffix.lower() != '.py':
                        messagebox.showerror('Error', f'Invalid script: {p.script} (must be .py)')
                        return
                p.pyarmor_options = ' '.join(opts_list).strip()
                self._apply_project_build_side_effects(p, p.build_mode)
                self.saved = True
                self.win.destroy()
                return

        opts = self._build_options_from_ui()
        p.pyarmor_options = ' '.join(opts).strip()

        self._apply_project_build_side_effects(p, p.build_mode)

        self.saved = True
        self.win.destroy()


# --- Small helper: return safe filetypes (None -> All Files)
def book_filetypes(filetypes):
    return filetypes or [('All Files', '*.*')]
