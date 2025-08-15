import os
import re
import shlex
import json
from pprint import pformat
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import importlib
import importlib.util
import types
import sys
import zipfile

try:
    from importlib.metadata import entry_points as _entry_points  # Py>=3.10
except Exception:
    try:
        from importlib_metadata import entry_points as _entry_points  # Backport
    except Exception:
        _entry_points = None

try:
    from .help import show_sphinx_helper  # type: ignore
except Exception:
    def show_sphinx_helper(parent):
        messagebox.showinfo("Sphinx Help", "Sphinx configuration helper not available.")


# --- Builder & theme suggestions -------------------------------------------

BUILDER_TYPES = [
    "html", "latex", "epub", "man", "text", "dirhtml", "singlehtml", "applehelp",
    "devhelp", "json", "qthelp", "xml", "pseudoxml"
]

BUILTIN_THEMES = {
    "alabaster", "classic", "nature", "bizstyle", "scrolls", "haiku", "agogo"
}
CANDIDATE_THEMES = [
    "sphinx_rtd_theme", "furo", "pydata_sphinx_theme", "press", "sphinx_book_theme"
]


def get_installed_themes():
    """
    Liefert eine sortierte Liste verfügbarer Themes:
      - eingebaute Themes
      - optionale Kandidaten per Importprobe
      - per Entry-Points registrierte pip-Themes (sphinx.html_themes)
    """
    available = set(BUILTIN_THEMES)

    # Kandidaten weiterhin per Import-Probe (best-effort)
    for name in CANDIDATE_THEMES:
        try:
            __import__(name)
            available.add(name)
        except ImportError:
            pass

    # Moderne, robuste Erkennung: Entry Points "sphinx.html_themes"
    try:
        if _entry_points is not None:
            eps = _entry_points()
            # Py>=3.10: MappingAPI mit .select(); Backports evtl. Liste
            if hasattr(eps, "select"):
                group = eps.select(group="sphinx.html_themes")  # type: ignore[attr-defined]
            else:
                group = [ep for ep in eps if getattr(ep, "group", None) == "sphinx.html_themes"]
            for ep in group or []:
                name = getattr(ep, "name", None)
                if name:
                    available.add(name)
    except Exception:
        # EP-Erkennung ist optional – never fail
        pass

    return sorted(available)


# --- Custom theme discovery -------------------------------------------------

def discover_custom_themes(theme_paths):
    """
    Scan directories and ZIP files in theme_paths and return (names, mapping).
    names: set of theme names
    mapping: {theme_name: source_path}
    """
    names = set()
    mapping = {}

    def _add_dir(path):
        try:
            for entry in os.listdir(path):
                cand = os.path.join(path, entry)
                if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "theme.conf")):
                    names.add(entry)
                    mapping[entry] = path
        except Exception:
            pass

    def _add_zip(path):
        try:
            with zipfile.ZipFile(path) as z:
                members = set(z.namelist())
                # Robuste Suche: *jedes* Vorkommen von theme.conf finden
                norm_members = {m.replace("\\", "/") for m in members}
                theme_conf_members = [m for m in norm_members if m.endswith("/theme.conf")]
                for m in theme_conf_members:
                    # top-level Ordnername (vor dem ersten '/')
                    top = m.split("/", 1)[0] if "/" in m else m
                    if top:
                        names.add(top)
                        mapping[top] = path
                        # UX-Heuristik: foo-1.0/foo/theme.conf -> auch "foo" anbieten
                        if "-" in top:
                            base = top.split("-", 1)[0]
                            if f"{base}/theme.conf" in norm_members:
                                names.add(base)
                                mapping[base] = path
                if not theme_conf_members:
                    # Fallback: bisherige Heuristik
                    tops = {m.split("/", 1)[0] for m in norm_members if "/" in m}
                    for top in tops:
                        if f"{top}/theme.conf" in norm_members:
                            names.add(top)
                            mapping[top] = path
        except Exception:
            pass

    for p in theme_paths or []:
        ap = os.path.abspath(p)
        if os.path.isdir(ap):
            _add_dir(ap)
        elif os.path.isfile(ap) and zipfile.is_zipfile(ap):
            _add_zip(ap)

    return names, mapping


# --- Overlay/Hook mechanics -------------------------------------------------

# Name der Override-Datei/Modul
OVERRIDE_MODULE = "conf_autopy"
OVERRIDE_FILENAME = f"{OVERRIDE_MODULE}.py"

HOOK_START = "# >>> SPHINX GUI HOOK (do not remove)"
HOOK_END = "# <<< SPHINX GUI HOOK"
HOOK_BLOCK = f"""{HOOK_START}
try:
    from {OVERRIDE_MODULE} import *  # noqa: F401,F403
except Exception:
    pass
{HOOK_END}
"""


def ensure_gui_hook(conf_path: str):
    """
    Hängt den Import-Hook idempotent an das Ende von conf.py an.
    Repariert auch „halb kaputte“ Blöcke (nur START oder nur END vorhanden).
    """
    if not os.path.isfile(conf_path):
        raise FileNotFoundError(conf_path)
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()

    # evtl. vorhandenen Hook-Block (auch unvollständig) entfernen
    pattern = re.compile(
        r"(?s)\n?\s*#\s*>>> SPHINX GUI HOOK.*?#\s*<<< SPHINX GUI HOOK\s*\n?",
        re.MULTILINE
    )
    content = re.sub(pattern, "\n", content)

    # Falls nur Start oder nur Ende unglücklich existiert, ebenfalls bereinigen
    content = re.sub(r"(?m)^.*#\s*>>> SPHINX GUI HOOK.*\n?", "", content)
    content = re.sub(r"(?m)^.*#\s*<<< SPHINX GUI HOOK.*\n?", "", content)

    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + HOOK_BLOCK

    with open(conf_path, "w", encoding="utf-8") as f:
        f.write(content)


def write_conf_overrides(conf_dir: str, overrides: dict) -> str:
    """Write conf_autopy.py mit nur den Keys aus `overrides` (valide Python)."""
    os.makedirs(conf_dir, exist_ok=True)
    out_path = os.path.join(conf_dir, OVERRIDE_FILENAME)

    lines = [
        "# Auto-generated by SphinxEditor GUI.\n",
        "# Only keys present here are overlaid. Delete this file to revert.\n\n",
    ]
    for k, v in overrides.items():
        if isinstance(v, (dict, list, tuple, set)):
            lines.append(f"{k} = {pformat(v, width=88, indent=2)}\n")
        elif isinstance(v, str):
            lines.append(f"{k} = {v!r}\n")
        elif v is not None:
            lines.append(f"{k} = {repr(v)}\n")
        # None -> nicht schreiben

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return out_path


# --- Optional: build helper -------------------------------------------------

def build_sphinx(project):
    """Convenience wrapper to call sphinx-build using project values."""
    sphinx_build = getattr(project, "tool_paths", {}).get("sphinx-build", "sphinx-build")
    src = getattr(project, "sphinx_source", "docs")
    out = getattr(project, "sphinx_build", "_build/html")
    bld = getattr(project, "sphinx_builder", "html")
    doct = getattr(project, "sphinx_doctrees", "") or os.path.join(os.path.dirname(out) or ".", "doctrees")

    cmd = [sphinx_build, "-b", bld, "-j", str(getattr(project, "sphinx_parallel", 1))]

    if getattr(project, "sphinx_warning_is_error", False):
        cmd.append("-W")
    if getattr(project, "sphinx_keep_going", False):
        cmd.append("--keep-going")
    if doct:
        cmd += ["-d", doct]

    # Simple -D overrides (optional)
    for key in ("project", "author", "html_theme"):
        val = None
        if key == "project":
            val = getattr(project, "sphinx_project", None)
        elif key == "author":
            val = getattr(project, "sphinx_author", None)
        elif key == "html_theme":
            val = getattr(project, "sphinx_theme", None)
        if val:
            cmd += ["-D", f"{key}={val}"]

    cmd += getattr(project, "sphinx_args", [])
    cmd += [src, out]

    subprocess.run(cmd, check=True)


# --- Common extensions & presets -------------------------------------------

# (Label, module name)
COMMON_EXTS = [
    # Core
    ("Autodoc", "sphinx.ext.autodoc"),
    ("Autosummary", "sphinx.ext.autosummary"),
    ("Napoleon", "sphinx.ext.napoleon"),
    ("Viewcode", "sphinx.ext.viewcode"),
    ("Intersphinx", "sphinx.ext.intersphinx"),
    ("Todo", "sphinx.ext.todo"),
    ("Doctest", "sphinx.ext.doctest"),
    ("MathJax", "sphinx.ext.mathjax"),
    ("Graphviz", "sphinx.ext.graphviz"),
    ("ImgConverter", "sphinx.ext.imgconverter"),
    ("Extlinks", "sphinx.ext.extlinks"),
    ("Autosectionlabel", "sphinx.ext.autosectionlabel"),
    ("Ifconfig", "sphinx.ext.ifconfig"),
    ("Coverage", "sphinx.ext.coverage"),
    ("Duration", "sphinx.ext.duration"),
    ("GitHub Pages", "sphinx.ext.githubpages"),
    # Popular third-party
    ("MyST (Markdown)", "myst_parser"),
    ("Copybutton", "sphinx_copybutton"),
    ("Design", "sphinx_design"),
    ("Tabs", "sphinx_tabs.tabs"),
    ("Inline Tabs", "sphinx_inline_tabs"),
    ("OpenGraph", "sphinxext.opengraph"),
    ("Mermaid", "sphinxcontrib.mermaid"),
    ("PlantUML", "sphinxcontrib.plantuml"),
    ("Autodoc Typehints", "sphinx_autodoc_typehints"),
    ("HTTP domain", "sphinxcontrib.httpdomain"),
    ("Program Output", "sphinxcontrib.programoutput"),
    ("Spelling", "sphinxcontrib.spelling"),
    ("Breathe (Doxygen)", "breathe"),
    ("nbsphinx (Jupyter)", "nbsphinx"),
    ("MyST-NB", "myst_nb"),
    ("OpenAPI", "sphinxcontrib.openapi"),
]

PRESETS = {
    "Minimal": [
        "sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"
    ],
    "API + Markdown": [
        "sphinx.ext.autodoc", "sphinx.ext.autosummary", "sphinx.ext.napoleon",
        "sphinx.ext.viewcode", "myst_parser", "sphinx_copybutton", "sphinx_design"
    ],
    "Diagrams": [
        "sphinx.ext.graphviz", "sphinxcontrib.mermaid", "sphinxcontrib.plantuml"
    ],
    "Web Ready": [
        "sphinxext.opengraph", "sphinx_copybutton", "sphinx_design", "sphinx_inline_tabs"
    ],
}


# --- GUI --------------------------------------------------------------------

class SphinxEditor:
    def __init__(self, master: tk.Tk, project, texts=None):
        self.master = master
        self.project = project
        self.texts = texts or {}
        self.saved = False
        self._custom_theme_map = {}

    def show(self) -> bool:
        self.win = tk.Toplevel(self.master)
        self.win.title("Sphinx Configuration")
        self.win.geometry("1040x700")
        self.win.transient(self.master)
        self.win.grab_set()

        form = ttk.Frame(self.win, padding=14)
        form.pack(fill="both", expand=True)

        # --- Source/Build ---
        ttk.Label(form, text="Source directory:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.e_source = ttk.Entry(form, width=45)
        self.e_source.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        self.e_source.insert(0, getattr(self.project, "sphinx_source", "docs"))
        ttk.Button(form, text="...", command=lambda: self._choose_dir(self.e_source)).grid(row=0, column=2, padx=5)

        ttk.Label(form, text="Build directory:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.e_build = ttk.Entry(form, width=45)
        self.e_build.grid(row=1, column=1, padx=5, pady=4, sticky="ew")
        self.e_build.insert(0, getattr(self.project, "sphinx_build", "_build/html"))
        ttk.Button(form, text="...", command=lambda: self._choose_dir(self.e_build)).grid(row=1, column=2, padx=5)

        # --- Builder ---
        ttk.Label(form, text="Builder:").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.builder_var = tk.StringVar()
        self.builder_combo = ttk.Combobox(form, textvariable=self.builder_var, values=BUILDER_TYPES, width=22, state="readonly")
        self.builder_combo.grid(row=2, column=1, sticky="w", padx=5, pady=4)
        current_builder = getattr(self.project, "sphinx_builder", "html")
        self.builder_combo.set(current_builder if current_builder in BUILDER_TYPES else BUILDER_TYPES[0])
        ttk.Button(form, text="?", command=lambda: messagebox.showinfo("Builder Info", ", ".join(BUILDER_TYPES))).grid(row=2, column=2, padx=5)

        # --- conf.py path ---
        ttk.Label(form, text="conf.py path:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.e_conf = ttk.Entry(form, width=45)
        self.e_conf.grid(row=3, column=1, padx=5, pady=4, sticky="ew")
        self.e_conf.insert(0, getattr(self.project, "sphinx_conf_path", "docs/conf.py"))
        ttk.Button(form, text="...", command=lambda: self._choose_file(self.e_conf, [("Python files", "*.py")])).grid(row=3, column=2, padx=5)

        # --- doctrees ---
        ttk.Label(form, text="Doctrees directory (optional):").grid(row=4, column=0, sticky="e", padx=5, pady=0)
        self.e_doctrees = ttk.Entry(form, width=45)
        self.e_doctrees.grid(row=4, column=1, padx=5, pady=(0, 0), sticky="ew")
        self.e_doctrees.insert(0, getattr(self.project, "sphinx_doctrees", ""))
        # dezenter Hinweis (optisch minimal)
        ttk.Label(form, text="(leer = <build parent>/doctrees)", foreground="#666").grid(row=5, column=1, sticky="w", padx=5, pady=(0, 6))

        # --- Project meta ---
        sep = ttk.Separator(form, orient="horizontal")
        sep.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(8, 8))

        ttk.Label(form, text="Project:").grid(row=7, column=0, sticky="e", padx=5, pady=4)
        self.e_proj = ttk.Entry(form, width=45)
        self.e_proj.grid(row=7, column=1, padx=5, pady=4, sticky="ew")
        self.e_proj.insert(0, getattr(self.project, "sphinx_project", "Your Project"))

        ttk.Label(form, text="Author:").grid(row=8, column=0, sticky="e", padx=5, pady=4)
        self.e_author = ttk.Entry(form, width=45)
        self.e_author.grid(row=8, column=1, padx=5, pady=4, sticky="ew")
        self.e_author.insert(0, getattr(self.project, "sphinx_author", "Your Name"))

        ttk.Label(form, text="Release:").grid(row=9, column=0, sticky="e", padx=5, pady=4)
        self.e_release = ttk.Entry(form, width=45)
        self.e_release.grid(row=9, column=1, padx=5, pady=4, sticky="ew")
        self.e_release.insert(0, getattr(self.project, "sphinx_release", ""))

        ttk.Label(form, text="Language (e.g. en, de):").grid(row=10, column=0, sticky="e", padx=5, pady=4)
        self.e_lang = ttk.Entry(form, width=45)
        self.e_lang.grid(row=10, column=1, padx=5, pady=4, sticky="ew")
        self.e_lang.insert(0, getattr(self.project, "sphinx_language", ""))

        # --- Theme ---
        ttk.Label(form, text="Theme:").grid(row=11, column=0, sticky="e", padx=5, pady=4)
        self.theme_var = tk.StringVar()
        themes = get_installed_themes()
        self.theme_combo = ttk.Combobox(
            form, textvariable=self.theme_var, values=themes, width=26, state="readonly"
        )
        self.theme_combo.grid(row=11, column=1, sticky="w", padx=5, pady=4)
        current_theme = getattr(self.project, "sphinx_theme", "alabaster")
        self.theme_combo.set(current_theme if current_theme in themes else (themes[0] if themes else "alabaster"))

        def show_theme_help():
            import webbrowser
            from tkinter import Toplevel, Label, Button, Frame, LEFT, W

            help_win = Toplevel(self.win)  # parent sauber setzen
            help_win.title("Sphinx Theme Installation Guide")
            help_win.geometry("540x470")
            help_win.transient(form.winfo_toplevel())
            help_win.grab_set()

            def open_themes_site():
                webbrowser.open("https://sphinx-themes.org/")

            instructions = (
                "📄 How to install and use Sphinx themes:\n\n"
                "1.️Built-in themes:\n"
                "   • Already included with Sphinx (e.g. alabaster, classic)\n"
                "   • Just select them from the list – no extra steps.\n\n"
                "2.️pip-installed themes:\n"
                "   • Install with:\n"
                "       pip install <theme-name>\n"
                "   • Example:\n"
                "       pip install furo\n"
                "   • Restart this tool so the new theme appears in the list.\n"
                "   • No need to copy the theme into your project.\n\n"
                "3.  Local or ZIP themes:\n"
                "   • Create a folder or ZIP containing a 'theme.conf'\n"
                "   • Place it in: docs/_themes/\n"
                "   • In conf.py set:\n"
                "       html_theme = '<theme-folder-name>'\n"
                "       html_theme_path = ['_themes']\n"
                "   • This works without pip and can be committed to your repo.\n\n"
                "🌐 For a gallery of available themes, visit sphinx-themes.org"
            )

            Label(help_win, text=instructions, justify=LEFT, anchor=W, font=("Segoe UI", 10))\
                .pack(padx=12, pady=10, fill="both", expand=True)

            btn_frame = Frame(help_win); btn_frame.pack(pady=10)
            Button(btn_frame, text="Open sphinx-themes.org", command=open_themes_site).pack(side=LEFT, padx=5)
            Button(btn_frame, text="Close", command=help_win.destroy).pack(side=LEFT, padx=5)

        help_btn = ttk.Button(form, text="Help…", command=show_theme_help)
        help_btn.grid(row=11, column=2, padx=5)

        # --- Extensions (one per line) ---
        ttk.Label(form, text="Extensions (one per line):").grid(row=12, column=0, sticky="ne", padx=5, pady=4)
        self.txt_ext = scrolledtext.ScrolledText(form, width=45, height=5, font=("Segoe UI", 10))
        self.txt_ext.grid(row=12, column=1, padx=5, pady=4, sticky="ew")
        ttk.Button(form, text="Pick…", command=self._pick_extensions_dialog)\
            .grid(row=12, column=2, padx=5, sticky="n")

        # --- Theme options (JSON or Python literal) ---
        ttk.Label(form, text="html_theme_options (JSON/Python):").grid(row=13, column=0, sticky="ne", padx=5, pady=4)
        self.txt_theme_opts = scrolledtext.ScrolledText(form, width=45, height=5, font=("Segoe UI", 10))
        self.txt_theme_opts.grid(row=13, column=1, padx=5, pady=4, sticky="ew")

        # Prefill from conf.py (after widgets exist)
        self._prefill_from_conf()
        # After prefill, refresh theme list to include custom themes automatically
        self._refresh_theme_list(auto_add_default=True)

        # --- Parallel jobs & flags ---
        ttk.Label(form, text="Parallel jobs (-j):").grid(row=14, column=0, sticky="e", padx=5, pady=4)
        self.e_parallel = ttk.Entry(form, width=8)
        self.e_parallel.grid(row=14, column=1, sticky="w", padx=5, pady=4)
        self.e_parallel.insert(0, str(getattr(self.project, "sphinx_parallel", 1)))

        cb_frame = ttk.Frame(form)
        cb_frame.grid(row=15, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self.var_warning_is_error = tk.BooleanVar(value=getattr(self.project, "sphinx_warning_is_error", False))
        self.var_keep_going = tk.BooleanVar(value=getattr(self.project, "sphinx_keep_going", False))
        self.var_standalone = tk.BooleanVar(value=getattr(self.project, "use_sphinx_standalone", False))
        ttk.Checkbutton(cb_frame, text="Treat warnings as errors (-W)", variable=self.var_warning_is_error).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Checkbutton(cb_frame, text="Keep going (--keep-going)", variable=self.var_keep_going).grid(row=0, column=1, padx=5, sticky="w")
        ttk.Checkbutton(cb_frame, text="Sphinx Standalone Mode", variable=self.var_standalone).grid(row=0, column=2, padx=5, sticky="w")

        # Build-safe: drop missing extensions automatically
        self.var_ext_buildsafe = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            cb_frame,
            text="Build-safe: drop missing extensions automatically",
            variable=self.var_ext_buildsafe
        ).grid(row=0, column=3, padx=5, sticky="w")

        # --- Additional args ---
        ttk.Label(form, text="Additional Sphinx arguments:").grid(row=16, column=0, sticky="ne", padx=5, pady=4)
        self.txt_args = scrolledtext.ScrolledText(form, width=45, height=3, font=("Segoe UI", 10))
        self.txt_args.grid(row=16, column=1, padx=5, pady=4, sticky="ew")
        self.txt_args.insert(tk.END, " ".join(getattr(self.project, "sphinx_args", [])))

        # --- Buttons ---
        button_frame = ttk.Frame(form)
        button_frame.grid(row=17, column=0, columnspan=4, pady=16)
        ttk.Button(button_frame, text="Cancel", command=self.win.destroy).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save", command=self._save).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="❓Help", command=lambda: show_sphinx_helper(self.win)).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Sphinx Quickstart", command=self._handle_quickstart).grid(row=0, column=3, padx=5)

        form.columnconfigure(1, weight=1)
        self.master.wait_window(self.win)
        return self.saved

    # --- Internals -----------------------------------------------------------

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

    def _run_quickstart(self, src_dir):
        quickstart_path = getattr(self.project, "tool_paths", {}).get("sphinx-quickstart", "sphinx-quickstart")
        args = [
            quickstart_path, src_dir, "-q",
            "--project", getattr(self.project, "sphinx_project", "MyProject"),
            "--author", getattr(self.project, "sphinx_author", "Author"),
        ]
        try:
            subprocess.run(args, check=True)
            messagebox.showinfo("Sphinx", "Sphinx project successfully initialized in: " + src_dir)
            return True
        except Exception as e:
            messagebox.showerror("Quickstart Error", f"Error running sphinx-quickstart:\n{e}")
            return False

    def _handle_quickstart(self):
        src = self.e_source.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showerror("Error", "Please select a valid source directory first!")
            return
        conf_path = os.path.join(src, "conf.py")
        if os.path.isfile(conf_path):
            messagebox.showinfo("Info", f"conf.py already exists in '{src}'.")
            return
        if messagebox.askyesno("Sphinx Quickstart", f"Initialize Sphinx project in '{src}'?\n(conf.py will be created)"):
            if self._run_quickstart(src):
                self.e_conf.delete(0, tk.END)
                self.e_conf.insert(0, conf_path)

    # --- Load values from conf.py (base file, without overrides) -------------

    def _load_conf_namespace(self, conf_path: str) -> dict | None:
        """Execute conf.py in an isolated namespace, masking conf_autopy."""
        if not conf_path or not os.path.isfile(conf_path):
            return None
        conf_dir = os.path.dirname(os.path.abspath(conf_path))
        old_cwd = os.getcwd()
        # conf_autopy temporär maskieren, damit nur die Basiswerte aus conf.py gelesen werden
        had_ov = OVERRIDE_MODULE in importlib.sys.modules
        old_ov = importlib.sys.modules.get(OVERRIDE_MODULE)
        importlib.sys.modules[OVERRIDE_MODULE] = types.ModuleType(OVERRIDE_MODULE)
        try:
            os.chdir(conf_dir)
            ns: dict = {"__file__": conf_path, "__name__": "__sphinx_conf_gui_loader__"}
            with open(conf_path, "r", encoding="utf-8") as f:
                code = f.read()
            exec(compile(code, conf_path, "exec"), ns, ns)
            return ns
        except Exception as e:
            messagebox.showwarning("conf.py load", f"Could not read base conf.py:\n{e}")
            return None
        finally:
            # Masking wiederherstellen
            if had_ov:
                importlib.sys.modules[OVERRIDE_MODULE] = old_ov  # type: ignore
            else:
                import importlib as _il
                try:
                    del _il.sys.modules[OVERRIDE_MODULE]
                except KeyError:
                    pass
            os.chdir(old_cwd)

    def _prefill_from_conf(self):
        """Populate UI and self.project from base conf.py if available."""
        conf_path = self.e_conf.get().strip()
        ns = self._load_conf_namespace(conf_path)
        if not ns:
            # No conf read; still try default _themes next to conf if it exists
            self._maybe_set_default_theme_path(conf_path)
            return

        # Pull values safely
        project = ns.get("project")
        author = ns.get("author")
        release = ns.get("release")
        language = ns.get("language")
        html_theme = ns.get("html_theme")
        html_theme_options = ns.get("html_theme_options")
        extensions = ns.get("extensions")
        html_theme_path = ns.get("html_theme_path")

        # Update project object
        if isinstance(project, str):
            self.project.sphinx_project = project
        if isinstance(author, str):
            self.project.sphinx_author = author
        if isinstance(release, str):
            self.project.sphinx_release = release
        if isinstance(language, str):
            self.project.sphinx_language = language
        if isinstance(html_theme, str):
            self.project.sphinx_theme = html_theme
        if isinstance(html_theme_options, dict):
            self.project.sphinx_theme_options = html_theme_options
        if isinstance(extensions, (list, tuple)):
            ext_list = [str(x).strip() for x in extensions if str(x).strip()]
            self.project.sphinx_extensions = ext_list

        # html_theme_path handling
        if isinstance(html_theme_path, (list, tuple)):
            conf_dir = os.path.dirname(os.path.abspath(conf_path))
            norm = []
            for x in html_theme_path:
                if not isinstance(x, str):
                    continue
                norm.append(os.path.abspath(os.path.join(conf_dir, x)))
            if norm:
                self.project.sphinx_theme_path = norm
        else:
            # If not set in conf, auto-add default "_themes" if exists
            self._maybe_set_default_theme_path(conf_path)

        # Update UI widgets
        if isinstance(project, str):
            self.e_proj.delete(0, tk.END); self.e_proj.insert(0, project)
        if isinstance(author, str):
            self.e_author.delete(0, tk.END); self.e_author.insert(0, author)
        if isinstance(release, str):
            self.e_release.delete(0, tk.END); self.e_release.insert(0, release)
        if isinstance(language, str):
            self.e_lang.delete(0, tk.END); self.e_lang.insert(0, language)
        if isinstance(html_theme, str):
            if html_theme in self.theme_combo["values"]:
                self.theme_combo.set(html_theme)
            else:
                self.theme_var.set(html_theme)
        if isinstance(html_theme_options, dict):
            try:
                self.txt_theme_opts.delete("1.0", tk.END)
                self.txt_theme_opts.insert(tk.END, json.dumps(html_theme_options, ensure_ascii=False, indent=2))
            except Exception:
                self.txt_theme_opts.delete("1.0", tk.END)
                self.txt_theme_opts.insert(tk.END, pformat(html_theme_options))
        if isinstance(extensions, (list, tuple)):
            self.txt_ext.delete("1.0", tk.END)
            cleaned = []
            for x in extensions:
                s = str(x).split("#", 1)[0].strip()
                if s:
                    cleaned.append(s)
            self.txt_ext.insert(tk.END, "\n".join(cleaned))

    def _maybe_set_default_theme_path(self, conf_path: str):
        """If no html_theme_path is set, automatically consider '<conf_dir>/_themes' if present."""
        if not conf_path:
            return
        conf_dir = os.path.dirname(os.path.abspath(conf_path))
        default_dir = os.path.join(conf_dir, "_themes")
        if os.path.isdir(default_dir):
            current = list(getattr(self.project, "sphinx_theme_path", []) or [])
            if default_dir not in current:
                current.append(default_dir)
            self.project.sphinx_theme_path = current

    def _refresh_theme_list(self, auto_add_default=False):
        """Refresh theme dropdown with built-ins, installed candidates and custom (from html_theme_path or default)."""
        if auto_add_default:
            # If user typed or selected a conf, consider default _themes next to it
            self._maybe_set_default_theme_path(self.e_conf.get().strip())

        themes = set(get_installed_themes())
        paths = getattr(self.project, "sphinx_theme_path", [])
        found, mapping = discover_custom_themes(paths)
        self._custom_theme_map = mapping  # keep for debugging / future features
        themes.update(found)

        # Sicherstellen, dass der aktuell konfigurierte Theme-Name nicht verloren geht
        current_sel = (self.theme_var.get() or getattr(self.project, "sphinx_theme", "") or "").strip()
        if current_sel:
            themes.add(current_sel)

        values = sorted(themes) if themes else ["alabaster"]
        self.theme_combo["values"] = values

        # preserve selection if possible
        if current_sel in values:
            self.theme_combo.set(current_sel)
        elif values:
            self.theme_combo.set(values[0])

    # --- Extensions parsing/validation/picker --------------------------------

    def _parse_extensions(self, text: str):
        """Robust parser: supports commas, one-per-line, and inline comments."""
        exts = []
        for line in text.splitlines():
            line = line.split('#', 1)[0]  # strip inline comments
            s = line.strip()
            if not s:
                continue
            for p in s.split(','):
                mod = p.strip()
                if mod:
                    exts.append(mod)
        # de-duplicate while preserving order
        seen, out = set(), []
        for x in exts:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def _ext_importable(self, modname: str) -> bool:
        return importlib.util.find_spec(modname) is not None

    def _validate_extensions(self, exts):
        missing = [e for e in exts if not self._ext_importable(e)]
        return (len(missing) == 0, missing)

    def _current_extensions(self):
        return self._parse_extensions(self.txt_ext.get("1.0", tk.END))

    def _pick_extensions_dialog(self):
        dlg = tk.Toplevel(self.win)
        dlg.title("Select Sphinx extensions")
        dlg.transient(self.win)
        dlg.grab_set()

        frm = ttk.Frame(dlg, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Select common extensions (you can still type custom ones below):")\
            .grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Presets
        pfrm = ttk.Frame(frm)
        pfrm.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(pfrm, text="Presets:").grid(row=0, column=0, padx=(0, 6))
        col = 1
        for name, mods in PRESETS.items():
            def _apply_preset(ms=mods):
                for _, m in COMMON_EXTS:
                    self._pick_vars[m].set(m in ms)
            ttk.Button(pfrm, text=name, command=_apply_preset).grid(row=0, column=col, padx=3)
            col += 1

        # Checkboxes
        self._pick_vars = {}
        cur = set(self._current_extensions())
        cols = 3
        for idx, (label, mod) in enumerate(COMMON_EXTS):
            var = tk.BooleanVar(value=(mod in cur))
            self._pick_vars[mod] = var
            r, c = divmod(idx, cols)
            ttk.Checkbutton(frm, text=f"{label} — {mod}", variable=var)\
                .grid(row=2 + r, column=c, sticky="w", padx=4, pady=2)

        # Footer buttons
        btm = ttk.Frame(frm)
        btm.grid(row=3 + (len(COMMON_EXTS) + cols - 1) // cols, column=0, columnspan=3, pady=(12, 0), sticky="we")

        def _all(state: bool):
            for v in self._pick_vars.values():
                v.set(state)

        ttk.Button(btm, text="All on", command=lambda: _all(True)).grid(row=0, column=0, padx=4)
        ttk.Button(btm, text="All off", command=lambda: _all(False)).grid(row=0, column=1, padx=4)

        def _apply():
            selected = [m for m, v in self._pick_vars.items() if v.get()]
            free = [x for x in self._current_extensions() if x not in selected]
            merged = [m for _, m in COMMON_EXTS if m in selected] + free  # stable, readable order
            self.txt_ext.delete("1.0", tk.END)
            self.txt_ext.insert(tk.END, "\n".join(merged))
            dlg.destroy()

        ttk.Button(btm, text="Apply", command=_apply).grid(row=0, column=2, padx=8)
        ttk.Button(btm, text="Cancel", command=dlg.destroy).grid(row=0, column=3, padx=4)

    # --- Save ----------------------------------------------------------------

    def _parse_theme_options(self, text: str):
        if not text.strip():
            return None
        # 1) Try JSON
        try:
            val = json.loads(text)
            if isinstance(val, dict):
                return val
        except Exception:
            pass
        # 2) Try Python literal (ast)
        try:
            import ast
            val = ast.literal_eval(text)
            if isinstance(val, dict):
                return val
        except Exception:
            pass
        messagebox.showerror("Invalid theme options", "Please provide a JSON or Python dict for html_theme_options.")
        return None

    def _sanitize_args(self, raw: str) -> list[str]:
        """
        Entfernt Flags, die programmatisch gesetzt werden (-b, -c, -d, -j, -W, --keep-going,
        -E, -a, -w <file>, -n, --color, --no-color). Reihenfolge der übrigen bleibt erhalten.
        """
        if not raw.strip():
            return []
        tokens = shlex.split(raw)
        out = []
        skip_next = 0

        # Flags, die einen Wert erwarten:
        takes_value = {"-b", "-c", "-d", "-j", "-w"}
        # Alle zu filternden Flags (auch solche ohne Wert)
        blacklist = {"-b", "-c", "-d", "-j", "-W", "--keep-going", "-E", "-a", "-w", "-n", "--color", "--no-color"}

        i = 0
        while i < len(tokens):
            t = tokens[i]
            if skip_next:
                skip_next -= 1
                i += 1
                continue

            if t in blacklist:
                if t in takes_value:
                    # den nächsten Token (Wert) mitüberspringen, falls vorhanden
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                        skip_next = 1
                i += 1
                continue

            out.append(t)
            i += 1

        return out

    def _save(self):
        src = self.e_source.get().strip()
        build = self.e_build.get().strip()
        builder = self.builder_var.get().strip()
        conf = self.e_conf.get().strip()
        doctrees = self.e_doctrees.get().strip()

        proj = self.e_proj.get().strip()
        author = self.e_author.get().strip()
        release = self.e_release.get().strip()
        language = self.e_lang.get().strip()

        theme = self.theme_var.get().strip()
        ext_text = self.txt_ext.get("1.0", tk.END)
        theme_opts_text = self.txt_theme_opts.get("1.0", tk.END)
        args_raw = self.txt_args.get("1.0", tk.END).strip()

        # 1. Source dir must exist
        if not src or not os.path.isdir(src):
            messagebox.showerror("Error", "The source directory must exist!")
            return

        # 2. conf.py must exist (akzeptiere Ordner oder Datei)
        if not conf:
            messagebox.showerror("Error", "Please select conf.py or its directory!")
            return
        conf_path = conf
        if os.path.isdir(conf_path):
            candidate = os.path.join(conf_path, "conf.py")
            if os.path.isfile(candidate):
                conf_path = candidate
            else:
                messagebox.showerror("Error", f"No conf.py found in '{conf}'.")
                return
        elif not os.path.isfile(conf_path):
            messagebox.showerror("Error", f"The selected conf.py was not found:\n{conf}\nPlease select the correct file or its folder.")
            return

        # 3. Build dir not empty
        if not build:
            messagebox.showerror("Error", "Build directory cannot be empty!")
            return

        # 4. Builder valid (+ Normalisierung)
        if not builder:
            messagebox.showerror("Error", "Builder (e.g. html, latex) must be set!")
            return
        builder_lc = builder.lower()
        if builder_lc not in BUILDER_TYPES:  # whitespace fix below
            if not messagebox.askyesno("Warning", f"Unusual builder '{builder}' selected.\nContinue anyway?"):
                return
        builder = builder_lc  # normalisiert verwenden

        # 5. Parallel
        try:
            n = int(getattr(self, "e_parallel").get().strip())
            if n < 1 or n > 128:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Please enter a valid number for parallel jobs (1-128)!")
            return

        # 6. Theme
        if not theme:
            messagebox.showerror("Error", "Theme must be set!")
            return

        # 6a. Warnung, wenn conf_dir != source_dir (Erklärung zu -c)
        conf_dir = os.path.dirname(os.path.abspath(conf_path))
        src_dir = os.path.abspath(src)
        if os.path.normcase(conf_dir) != os.path.normcase(src_dir):
            cont = messagebox.askyesno(
                "Note",
                "conf.py liegt nicht im Source-Verzeichnis.\n"
                "Das ist okay – der Build nutzt dann 'sphinx-build -c <conf_dir>'\n"
                "und findet die Konfiguration trotzdem.\n\n"
                "Weiter speichern?"
            )
            if not cont:
                return

        # --- Save values into project ---
        self.project.sphinx_source = src
        self.project.sphinx_build = build
        self.project.sphinx_builder = builder
        self.project.sphinx_conf_path = conf_path  # ggf. korrigiert
        self.project.sphinx_doctrees = doctrees
        self.project.sphinx_theme = theme
        self.project.sphinx_parallel = n
        self.project.sphinx_warning_is_error = self.var_warning_is_error.get()
        self.project.sphinx_keep_going = self.var_keep_going.get()
        self.project.use_sphinx_standalone = self.var_standalone.get()

        # 6b. Zusätzliche Argumente säubern (Safety)
        self.project.sphinx_args = self._sanitize_args(args_raw)

        # Persisted meta fields
        if proj:
            self.project.sphinx_project = proj
        if author:
            self.project.sphinx_author = author
        if release:
            self.project.sphinx_release = release
        if language:
            self.project.sphinx_language = language

        # Extensions: parse + validate
        extensions = self._parse_extensions(ext_text)
        if extensions:
            ok, missing = self._validate_extensions(extensions)
            if not ok:
                if self.var_ext_buildsafe.get():
                    keep = [e for e in extensions if e not in missing]
                    if not keep:
                        messagebox.showerror("Extensions", "No valid extensions remain (all are missing).")
                        return
                    messagebox.showinfo("Extensions", "These extensions were dropped (not importable):\n- " + "\n- ".join(missing))
                    extensions = keep
                else:
                    msg = "These extensions are not importable:\n\n- " + "\n- ".join(missing) + \
                          "\n\nRemove and continue?"
                    if not messagebox.askyesno("Extensions", msg):
                        return
                    extensions = [e for e in extensions if e not in missing]
            self.project.sphinx_extensions = extensions

        # Theme options
        theme_opts = self._parse_theme_options(theme_opts_text)
        if theme_opts is not None:
            self.project.sphinx_theme_options = theme_opts

        # Falls ein Custom-Theme gewählt ist, html_theme_path automatisch ergänzen
        try:
            theme_paths = list(getattr(self.project, "sphinx_theme_path", []) or [])
            if self.project.sphinx_theme in getattr(self, "_custom_theme_map", {}):
                src_path = self._custom_theme_map[self.project.sphinx_theme]
                if src_path not in theme_paths:
                    theme_paths.append(src_path)
            self.project.sphinx_theme_path = theme_paths or None
        except Exception:
            # still proceed; not critical for saving
            pass

        # --- Overlay file + hook ---
        try:
            ensure_gui_hook(conf_path)

            conf_dir = os.path.dirname(conf_path)

            # make html_theme_path relative to conf_dir for portability
            theme_paths = getattr(self.project, "sphinx_theme_path", None)
            if theme_paths:
                rel_paths = []
                for p in theme_paths:
                    try:
                        rel_paths.append(os.path.relpath(p, conf_dir))
                    except ValueError:
                        rel_paths.append(p)
            else:
                rel_paths = None

            # Only write keys we actually want to set
            overrides = {
                # Strings
                "project": getattr(self.project, "sphinx_project", None),
                "author": getattr(self.project, "sphinx_author", None),
                "release": getattr(self.project, "sphinx_release", None),
                "language": getattr(self.project, "sphinx_language", None),
                "html_theme": self.project.sphinx_theme,
                # Complex types
                "extensions": getattr(self.project, "sphinx_extensions", None),
                "html_theme_options": getattr(self.project, "sphinx_theme_options", None),
                "html_theme_path": rel_paths,
            }
            # Drop None values
            overrides = {k: v for k, v in overrides.items() if v is not None}

            write_conf_overrides(conf_dir, overrides)
        except Exception as e:
            messagebox.showerror("conf.py Error", f"Error updating overlay/hook:\n{e}")
            return

        self.saved = True
        self.win.destroy()
