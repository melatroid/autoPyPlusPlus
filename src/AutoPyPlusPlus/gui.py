from __future__ import annotations  # Enables postponed evaluation of type annotations for forward references

import os  # For interacting with the operating system (e.g., file/directory handling)
import copy # Deep Copy
import tkinter as tk  # Tkinter: main module for creating GUIs
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog  # Tkinter modules for advanced GUI widgets, file dialogs, message boxes, and color pickers
from datetime import datetime  # For working with date and time
from typing import Optional  # For type hinting optional variables
from pathlib import Path  # For object-oriented filesystem paths
import threading  # For running code in separate threads (concurrent tasks)
import time  # For time-related functions (e.g., delays, measuring time)
import configparser 
import subprocess # For update function
import sys, shutil # for python venv terminal

from .help import show_main_helper  # Open the main in-app help window

from .language import LANGUAGES  # Localized UI strings

from .hotkeys import register_hotkeys  # Register global app hotkeys

from .about import show_about_dialog  # “About” dialog with app info

from .feedback import show_feedback_dialog, feedback_is_done # Feedback

from .general_settings import show_general_settings  # General settings dialog

from .simplex_api import SimplexAPIWatcher  # Watches simplexAPI.ini and reacts to changes

from .projecteditor import ProjectEditor  # Editor UI for regular projects

from .debuginspector import debuginspector  # Viewer for compile logs & diagnostics

from .compiler import compile_projects  # Orchestrates the compilation pipeline

from .project import Project  # Data model for a build/project entry

from . import hashcheck  # Check developer/compiler hashes

from .config import ( # Read/write application configuration
    load_config, save_config,
    get_last_apyscript, set_last_apyscript
)  

from .tooltip import CreateToolTip  # Tooltip helper for Tk widgets

from .parse_spec_file import parse_spec_file  # Parse .spec files into Project objects

from .speceditor import SpecEditor  # Editor UI for .spec-based projects

from .apyeditor import ApyEditor  # Editor for .apyscript bundle files

from .core import (   # Persistence & housekeeping utilities
    save_projects, load_projects,
    export_extensions_ini, load_extensions_ini,
    find_cleanup_targets, delete_files_and_dirs
) 

from .themes import (  # Built-in theme setup functions
    set_dark_mode, set_light_mode, set_arcticblue_mode, set_sunset_mode,
    set_forest_mode, set_retro_mode, set_pastel_mode, set_galaxy_mode,
    set_autumn_mode, set_candy_mode, set_inferno_mode,
    set_cyberpunk_mode, set_obsidian_mode, set_nebula_mode, set_midnight_forest_mode,
    set_phantom_mode, set_deep_space_mode, set_onyx_mode, set_lava_flow_mode,
)

TEXT = "\ufe0e"         
CHECKED  = "⬛" + TEXT     
UNCHECKED = "⬜" + TEXT   

class AutoPyPlusPlusGUI:
    # ------------------------------ init -------------------------------
    def __init__(self, master: tk.Tk):
    
        self.current_apyscript: Optional[Path] = Path("myProject.apyscript")
        self.master = master
        self.config = load_config()
        # --- Simplex API toggle (default OFF) ---
        self.enable_simplex_api_var = tk.BooleanVar(
            value=bool(self.config.get("enable_simplex_api", False))
        )
        
        # --- Hash-Check Setting (Default: on) ---
        self.config.setdefault("enable_hashcheck", True)
        self.enable_hashcheck_var = tk.BooleanVar(value=bool(self.config.get("enable_hashcheck", True)))

        # --- Pipeline Cooldown (Sekunden) ---
        self.config.setdefault("pipeline_cooldown_s", 0)
        try:
            self.pipeline_cooldown_s = int(self.config.get("pipeline_cooldown_s", 0))
        except Exception:
            self.pipeline_cooldown_s = 3

        self.projects: list[Project] = []
        self.working_dir = Path(self.config.get("working_dir")) if self.config.get("working_dir") else Path(__file__).parent.parent

        # -------- Sprache / Texte -------------------------------------
        self.current_language = self.config.get("language", "de")
        self.language_var = tk.StringVar(value=self.current_language)
        self.texts = LANGUAGES[self.current_language]
        self._fallback_texts()
        self.compile_mode_var = tk.StringVar(
            value=self.config.get("compile_mode", "A")
        )

        # -------- Fenstergrunddaten -----------------------------------
        master.title(self.texts["title"])
       
        master.geometry("1450x500")
        master.minsize(1350, 250)
        icon = Path(__file__).parent / "autoPy++.ico"
        if icon.exists():
            master.iconbitmap(icon)

        # -------- Theme & Style ---------------------------------------
        self.style = ttk.Style()
        self.themes = [
            set_dark_mode, set_light_mode, set_arcticblue_mode, set_galaxy_mode,
            set_sunset_mode, set_forest_mode, set_retro_mode, set_pastel_mode,
            set_autumn_mode, set_candy_mode, set_inferno_mode,
            set_cyberpunk_mode, set_obsidian_mode, set_nebula_mode, set_midnight_forest_mode,
            set_phantom_mode, set_deep_space_mode, set_onyx_mode, set_lava_flow_mode,
        ]

        self.theme_names = [
            "Dark", "Light", "Arctic Blue", "Galaxy", "Sunset", "Forest", "Retro",
            "Pastel", "Autumn", "Candy", "Inferno Red", "Cyberpunk", "Obsidian",
            "Nebula", "Midnight Forest", "Phantom", "Developer", "Onyx Grey", "Lava Flow"
        ]
        
        default_theme = 1
        self.current_theme_index = self.config.get("theme", default_theme) % len(self.themes)
        self.themes[self.current_theme_index](self.style, master)

        
        def _startup_modals():
            def open_about():
                show_about_dialog(self.master, self.style, self.themes[self.current_theme_index])

            def log_problem(msg):
                try:
                    from tkinter import messagebox
                    messagebox.showwarning("Startup", msg)
                except Exception:
                    print("[Startup]", msg)

            try:
                if feedback_is_done():
                    open_about()
                    return

                shown = show_feedback_dialog(
                    self.master,
                    style=self.style,
                    theme_func=self.themes[self.current_theme_index]
                )

                def _poll_flag():
                    try:
                        if feedback_is_done():
                            open_about()
                        else:
                            self.master.after(1000, _poll_flag)
                    except Exception as e:
                        log_problem(f"Polling error: {e}")
                        self.master.after(1000, _poll_flag)

                if shown:
                    _poll_flag()
            except TypeError as e:
                log_problem(f"About dialog error: {e}\nCheck show_about_dialog signature.")
            except Exception as e:
                log_problem(f"Startup modals error: {e}")

        self.master.after(0, _startup_modals)


                            
        # -------- Farben ----------------------------------------------
        self.color_a: str = self.config.get("color_a", "#43d6b5")   
        self.color_b: str = self.config.get("color_b", "#4a1aae")   
        self.color_c: str = self.config.get("color_c", "#cd146c")   
        self.default_bg: str = "#ffffff"
        self.pb_style_name = "Compile.Horizontal.TProgressbar"
        self._apply_progressbar_style()
        
        # -------- UI aufbauen & Projekte laden ------------------------
        self.status_var = tk.StringVar(value=self.texts["status_ready"])
        self._status_lock = threading.Lock()
        self._last_user_status = self.texts["status_ready"]
        self._hold_until_ts = 0.0        
        self._default_hold_ms = int(self.config.get("status_hold_ms", 2000))
        
        self._build_ui()        
        self._auto_load()
        self._register_hotkeys()
        
        def _on_close():
            try:
                if getattr(self, "_simplex_watcher", None):
                    self._simplex_watcher.stop()
            except Exception:
                pass
            self.master.quit()
            
        self.master.protocol("WM_DELETE_WINDOW", _on_close) 
        # --- Simplex API Watcher ---
        self._simplex_watcher = None
        ini_path = (self.working_dir / "simplexAPI.ini")
        if self.enable_simplex_api_var.get():
            self._simplex_watcher = SimplexAPIWatcher(self, ini_path, poll_interval=1.0)
            self._simplex_watcher.start()


    # ------------------------- Hilfsmethoden --------------------------

    def _build_ui(self):
        for w in self.master.winfo_children():
            if isinstance(w, tk.Toplevel):
                continue
            w.destroy()

        # Menüleiste
        self._build_menubar()

        # Haupt-Container
        self.main_frame = ttk.Frame(self.master, padding=10)
        self.main_frame.pack(fill="both", expand=True)

        # --- Toolbar ---
        self.bar = ttk.Frame(self.main_frame)
        self.bar.pack(fill="x", pady=5)

        def _btn(txt_key, cmd, tip_key):
            b = ttk.Button(self.bar, text=self.texts[txt_key], command=cmd)
            b.pack(side="left", padx=5)
            CreateToolTip(b, self.texts[tip_key])
            return b

        self.add_btn       = _btn("add_btn",       self._add,             "tooltip_add_btn")
        self.edit_btn      = _btn("edit_btn",      self._edit,            "tooltip_edit_btn")
        self.delete_btn    = _btn("delete_btn",    self._delete,          "tooltip_delete_btn")
        self.duplicate_btn = _btn("duplicate_btn", self._duplicate,       "tooltip_duplicate_btn")
        self.rename_btn    = _btn("rename_btn",    self._rename_project,  "tooltip_rename_btn")

        self.up_btn = ttk.Button(self.bar, text="⮝", width=2, command=self._move_project_up)
        self.up_btn.pack(side="left", padx=(8,2))

        self.down_btn = ttk.Button(self.bar, text="⮟", width=2, command=self._move_project_down)
        self.down_btn.pack(side="left", padx=(2,8))

        ttk.Label(self.bar, text="|").pack(side="left", padx=5)

        self.save_btn      = _btn("save_btn",      self._save_current_file, "tooltip_save_btn")
        self.save_as_btn   = _btn("save_as_btn",   self._save_as,           "tooltip_save_as_btn")
        self.load_btn      = _btn("load_btn",      self._load,              "tooltip_load_btn")
        self.clear_btn     = _btn("clear_btn",     self._clear,             "tooltip_clear_btn")

        # Rechte Buttons
        self.compile_all_btn    = _btn("compile_all_btn", self.compile_all,       "tooltip_compile_all_btn")
        self.debug_btn          = _btn("debug_btn",       self._open_debuginspector, "tooltip_debug_btn")
        self.clear_work_dir_btn = _btn("clear_work_dir_btn", self.clear_work_dir, "tooltip_clear_work_dir_btn")

        # Kompiliermodus (rechts)
        self.mode_menu = ttk.OptionMenu(
            self.bar,
            self.compile_mode_var,
            self.compile_mode_var.get(),
            "A", "B", "C",
            command=lambda _: self._toggle_mode()
        )
        self.mode_menu.pack(side="right", padx=6)
        self.mode_menu.config(width=2)
        CreateToolTip(self.mode_menu, self.texts["tooltip_compile_mode"])

        # --- Treeview ---
        cols = ("A","B","C","Name","Pytest","PyArmor","Nuitka","Cython","Sphinx","Script")
        self.tree = ttk.Treeview(self.main_frame, columns=cols, show="headings", style="BigEmoji.Treeview")

        # Spalten-Header
        self.tree.heading("A", text=self.texts["compile_a_col"])
        self.tree.heading("B", text=self.texts["compile_b_col"])
        self.tree.heading("C", text=self.texts["compile_c_col"])
        self.tree.heading("Name", text=self.texts["name_col"], anchor="center")
        self.tree.heading("Script", text=self.texts["script_col"], anchor="center")
        self.tree.heading("PyArmor", text="PyArmor", anchor="center")
        self.tree.heading("Nuitka", text="Nuitka", anchor="center")
        self.tree.heading("Cython", text="Cython", anchor="center")
        self.tree.heading("Pytest", text="Pytest", anchor="center")
        self.tree.heading("Sphinx", text="Sphinx", anchor="center")

        # Spalten-Breiten
        self.tree.column("A", width=90, anchor="center", stretch=False)
        self.tree.column("B", width=90, anchor="center", stretch=False)
        self.tree.column("C", width=90, anchor="center", stretch=False)
        self.tree.column("Name", width=120, anchor="center", stretch=False)
        self.tree.column("Script", width=600, anchor="center", stretch=False)
        self.tree.column("PyArmor", width=80, anchor="center", stretch=False)
        self.tree.column("Nuitka", width=80, anchor="center", stretch=False)
        self.tree.column("Cython", width=80, anchor="center", stretch=False)
        self.tree.column("Pytest", width=70, anchor="center", stretch=False)
        self.tree.column("Sphinx", width=70, anchor="center", stretch=False)

        self._update_tag_colors()
        self.tree.pack(fill="both", expand=True, pady=(5, 10))
        self.tree.bind("<Button-1>", self._toggle_cell)
        self.tree.tag_configure("divider", background="#41578e", font=("", 10, "bold"))

        # --- Statusleiste ---
        self.status_label = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=5,
            font=("Helvetica", 14),
        )
        self.status_label.pack(fill="x")

        # Initial render
        self._update_headings()
        self._refresh_tree()


    def _fallback_texts(self) -> None:
        fb = {
            "title": "AutoPy++ GUI",
            "name_col": "Name",
            "script_col": "Skriptpfad",
            "compile_a_col": "Modus A",
            "compile_b_col": "Modus B",
            "compile_c_col": "Modus C",
            "mode_a": "Modus A",
            "mode_b": "Modus B",
            "mode_c": "Modus C",
            "duplicate_btn": "Duplicate",
            "tooltip_duplicate_btn": "Duplicate",
            "rename_btn": "Rename",
            "tooltip_rename_btn": "Change name",
            "rename_title": "Rename Project",
            "rename_prompt": "New name:",
            "rename_empty": "Please enter a name.",
            "status_renamed": "Project “{old}” → “{new}” renamed.",
            "tooltip_add_divider_btn": "Insert a labeled separator row",
            "menu_add_divider": "❌ Add Divider",
        }
        for k, v in fb.items():
            self.texts.setdefault(k, v)

    def _mode_label(self) -> str:
        if self.compile_mode_var.get() == "B":
            return self.texts["mode_b"]
        elif self.compile_mode_var.get() == "C":
            return self.texts["mode_c"]
        else:
            return self.texts["mode_a"]

    def set_status(self, msg: str, hold_ms: int | None = None) -> None:
        """Setzt den Status-Text und schützt ihn für hold_ms Millisekunden vor der Animation."""
        if hold_ms is None:
            hold_ms = self._default_hold_ms
        now = time.time()
        with self._status_lock:
            self._last_user_status = msg
            self._hold_until_ts = now + (hold_ms / 1000.0)
            self.status_var.set(msg)
            self.master.update_idletasks()

    def status_info(self, msg: str, hold_ms: int = 2000) -> None:
        self.set_status(f"ℹ {msg}", hold_ms=hold_ms)

    def status_ok(self, msg: str, hold_ms: int = 2000) -> None:
        self.set_status(f"✅ {msg}", hold_ms=hold_ms)

    def status_warn(self, msg: str, hold_ms: int = 2500) -> None:
        self.set_status(f"⚠ {msg}", hold_ms=hold_ms)

    def status_err(self, msg: str, hold_ms: int = 3000) -> None:
        self.set_status(f"❌ {msg}", hold_ms=hold_ms)

    def _select_language(self, lang):
        self.language_var.set(lang)
        self._change_language()
            
    def _get_thread_count(self) -> int:
        try:
            cpu_max = max(1, (os.cpu_count() or 1))
            v = int(self.config.get("thread_count", cpu_max))
            return max(1, min(cpu_max, v))
        except Exception:
            return max(1, (os.cpu_count() or 1))

    def _set_theme_from_menu(self, idx):
        self.current_theme_index = idx
        self.themes[idx](self.style, self.master)
        self.config["theme"] = idx
        save_config(self.config)
        self.status_var.set(f"Theme changed: {self.theme_names[idx]} 🎨")
        self._update_tag_colors()
        self._refresh_tree()
        self._apply_progressbar_style()

    def _move_project_up(self):
        sel = self.tree.selection()
        if not sel or not sel[0].startswith("proj_"):
            return
        idx = int(sel[0].split("_")[1])
        if idx > 0:
            # Projekte im Speicher tauschen
            self.projects[idx - 1], self.projects[idx] = self.projects[idx], self.projects[idx - 1]
            self._refresh_tree()
            # Auswahl behalten
            self.tree.selection_set(f"proj_{idx-1}")

    def _move_project_down(self):
        sel = self.tree.selection()
        if not sel or not sel[0].startswith("proj_"):
            return
        idx = int(sel[0].split("_")[1])
        if idx < len(self.projects) - 1:
            self.projects[idx + 1], self.projects[idx] = self.projects[idx], self.projects[idx + 1]
            self._refresh_tree()
            self.tree.selection_set(f"proj_{idx+1}")

    
    def _build_menubar(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # ----- Projects / File -----
        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_projects", "Projects"), menu=self.file_menu)
        self.file_menu.add_command(label=self.texts.get("menu_open", "Open"), command=self._load)
        self.file_menu.add_command(label=self.texts.get("menu_new", "New"), command=self._clear)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.texts.get("menu_save", "Save"), command=self._save_current_file)
        self.file_menu.add_command(label=self.texts.get("menu_save_as", "Save As..."), command=self._save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.texts.get("menu_exit", "Exit"), command=self.master.quit)

        # ----- Scripts -----
        self.project_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_scripts", "Scripts"), menu=self.project_menu)
        self.project_menu.add_command(label=self.texts.get("menu_add_empty", "Add Empty"), command=self._add_empty_project)
        self.project_menu.add_command(label=self.texts.get("menu_add_file", "Add File"), command=self._add)
        # --- DIVIDER ---
        self.project_menu.add_command(label=self.texts.get("menu_add_divider", "Add Divider"), command=self._add_divider)
        # ---------------
        self.project_menu.add_command(label=self.texts.get("menu_edit", "Edit"), command=self._edit)
        self.project_menu.add_command(label=self.texts.get("menu_delete", "Delete"), command=self._delete)
        self.project_menu.add_command(label=self.texts.get("menu_duplicate", "Duplicate"), command=self._duplicate)
        self.project_menu.add_command(label=self.texts.get("menu_rename", "Rename"), command=self._rename_project)

        # ----- Tools -----
        self.tools_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_tools", "Tools"), menu=self.tools_menu)
        self.tools_menu.add_command(label=self.texts.get("menu_inspector", "Inspector"), command=self._open_debuginspector)
        self.tools_menu.add_command(label=self.texts.get("menu_apyeditor", "ApyEditor"), command=self._open_apy_editor)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="🐍 Python Terminal",command=self._open_python_terminal)

        # ----- Build -----
        self.build_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_build", "Build"), menu=self.build_menu)
        self.build_menu.add_command(label=self.texts.get("menu_compile_all", "🚀 Compile All"), command=self.compile_all)
        self.build_menu.add_separator()
        self.build_menu.add_command(label=self.texts.get("menu_clean_workdir", "🧹 Clean Working Directory"), command=self.clear_work_dir)

        # ----- Settings -----
        self.settings_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_settings", "Settings"), menu=self.settings_menu)

        # Sprache
        self.language_submenu = tk.Menu(self.settings_menu, tearoff=False)
        for lang in LANGUAGES.keys():
            self.language_submenu.add_command(label=lang, command=lambda l=lang: self._select_language(l))
        self.settings_menu.add_cascade(label=self.texts.get("menu_language", "Language"), menu=self.language_submenu)

        # Themes
        self.theme_submenu = tk.Menu(self.settings_menu, tearoff=False)
        for idx, theme_name in enumerate(self.theme_names):
            self.theme_submenu.add_command(label=theme_name, command=lambda i=idx: self._set_theme_from_menu(i))
        self.settings_menu.add_cascade(label=self.texts.get("menu_themes", "Themes"), menu=self.theme_submenu)

        # Weitere Settings
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.texts.get("menu_extensions", "Extensions"), command=self._show_extensions_popup)
        self.settings_menu.add_command(label=self.texts.get("menu_autopy_general", "Advanced"), command=self._open_general_settings)
        self.settings_menu.add_command(label=self.texts.get("menu_colors", "Mode Colors"), command=self._choose_colors)
        self.settings_menu.add_command(label=self.texts.get("menu_toggle_fullscreen", "Toggle Fullscreen"), command=self._toggle_fullscreen)

        # --- Update ---
        self.update_submenu = tk.Menu(self.settings_menu, tearoff=False)
        self.update_submenu.add_command(
            label=self.texts.get("menu_run_windows_update", "Update"),
            command=self._run_windows_update
        )
        self.update_submenu.add_command(
            label=self.texts.get("menu_run_windows_update_admin", "Update as Admin"),
            command=lambda: self._run_windows_update(as_admin=True)
        )
        self.settings_menu.add_cascade(label=self.texts.get("menu_update", "Update"), menu=self.update_submenu)

        # Hilfe & About
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.texts.get("menu_show_helper", "Show Helper"), command=lambda: show_main_helper(self.master))
        self.settings_menu.add_command(label=self.texts.get("menu_about", "About"), command=lambda: show_about_dialog(self.master, self.style, self.themes[self.current_theme_index]))

    def _toggle_mode_by_display_name(self, display_name, mode_names):
        rev = {v: k for k, v in mode_names.items()}
        self.compile_mode_var.set(rev[display_name])
        self._toggle_mode()

    def _update_tag_colors(self):
        self.tree.tag_configure("mode_a", background=self.color_a, foreground="white")
        self.tree.tag_configure("mode_b", background=self.color_b, foreground="white")
        self.tree.tag_configure("mode_c", background=self.color_c, foreground="white")

    def _apply_progressbar_style(self):
        mode = self.compile_mode_var.get()
        mode_color = {"A": self.color_a, "B": self.color_b, "C": self.color_c}.get(mode, self.color_a)
        try:
            trough = self.style.lookup("TFrame", "background")
            if not trough:
                trough = self.default_bg
        except Exception:
            trough = self.default_bg

        try:
            self.style.configure(self.pb_style_name,
                                 background=mode_color, 
                                 troughcolor=trough)     
        except Exception:
            self.style.configure(self.pb_style_name, background=mode_color)


    def _initial_dir(self) -> str:
        try:
            if self.current_apyscript:
                return str(Path(self.current_apyscript).parent)
            last = get_last_apyscript(self.config)
            if last:
                return str(last.parent)
            wd = self.config.get("working_dir")
            if wd:
                return str(Path(wd))
        except Exception:
            pass
        return os.getcwd()
    

    def _info_toast(self, title: str, message: str, *, ms: int = 1400) -> None:
        try:
            toast = tk.Toplevel(self.master)
            toast.overrideredirect(True)          # borderless
            try:
                toast.attributes("-topmost", True)
            except Exception:
                pass

            # Content
            frame = ttk.Frame(toast, padding=12)
            frame.pack(fill="both", expand=True)
            ttk.Label(frame, text=title, font=("", 11, "bold")).pack(anchor="w")
            ttk.Label(frame, text=message, wraplength=360, justify="left").pack(anchor="w", pady=(4, 0))

            # Position bottom-right of main window
            self.master.update_idletasks()
            mx, my = self.master.winfo_rootx(), self.master.winfo_rooty()
            mw, mh = self.master.winfo_width(), self.master.winfo_height()

            toast.update_idletasks()
            tw, th = toast.winfo_width(), toast.winfo_height()
            x = mx + mw - tw - 24
            y = my + mh - th - 24
            toast.geometry(f"+{max(0, x)}+{max(0, y)}")

            # Auto-close
            toast.after(ms, toast.destroy)
        except Exception:
            # Fallback: just update status
            self.set_status(message, hold_ms=ms)

    def _check_hashes_before_build(self) -> bool:
        """
        Check local source checksums against a trusted reference before building.
        Returns True to proceed, False to abort.
        Skips the check if 'enable_hashcheck' is disabled or the 'hashcheck' module is unavailable.
        """
        # 1) Globally disabled by setting? -> proceed
        if not bool(self.enable_hashcheck_var.get()):
            return True

        # 2) Module not available? -> proceed (without check)
        if hashcheck is None:
            self.set_status("Hash check skipped (module not available).", hold_ms=1500)
            return True

        try:
            project_root = str(self.working_dir)
            # 3) Reference source (robust if the constant is missing)
            reference = getattr(hashcheck, "DEFAULT_HASH_URL", None)

            summary = hashcheck.verify_against_reference(
                project_root=project_root,
                reference_source=reference,   # may be None if your function supports it
                algorithms=None,              # defaults
                validate_syntax=True,         # optional: run syntax check
            )
        except Exception as e:
            # On verification error: be safe and abort
            self.status_err(f"Hash check failed: {e}")
            return False


        if getattr(summary, "overall_ok", False):
            # Short non-blocking info window that auto-closes
            self._info_toast(
                "Hash ✅",
                "All source hashes match the reference. Safe to build.",
                ms=3400,
            )
            return True

        # Build a concise, informative mismatch summary
        lines = []
        for r in getattr(summary, "results", []):
            if getattr(r, "error", None):
                lines.append(f"[{getattr(r, 'algorithm', '?')}] ERROR: {r.error}")
            elif not getattr(r, "match", True):
                first = getattr(r, "first_diff", None)
                where = f"(first difference at pos {first})" if first is not None else ""
                lines.append(f"[{getattr(r, 'algorithm', '?')}] MISMATCH {where}")

        details = "\n".join(lines) if lines else "Unknown mismatch."
        msg = (
            "Source checksums do not match the trusted reference:\n\n"
            f"{details}\n\n"
            "Proceed anyway?"
        )

        proceed = messagebox.askyesno("Warning – hash mismatch", msg, icon="warning", default="no")
        if not proceed:
            self.set_status("Build aborted (hash mismatch).", hold_ms=2500)
            return False

        self.set_status("Continuing despite hash mismatch …", hold_ms=1500)
        return True

    def _toggle_fullscreen(self):
        is_fullscreen = self.master.attributes("-fullscreen")
        self.master.attributes("-fullscreen", not is_fullscreen)

    def _register_hotkeys(self):
        hotkeys = {
            "<C>": self.compile_all,
            "<A>": self._add,
            "<D>": self._delete,
            "<Y>": self._cycle_compile_mode,
            "<L>": self._load,
            "<S>": self._save_current_file,    
            "<Shift-S>": self._save_as,       
            "<E>": self.clear_work_dir,
            "<T>": self._cycle_theme,
            "<Shift-Q>": self.master.quit,
            "<F>": self._toggle_fullscreen,
            "<Return>": self._edit,
        }
        register_hotkeys(self.master, hotkeys)

    def _cycle_compile_mode(self, *_):
        modes = ["A", "B", "C"]
        cur = self.compile_mode_var.get()
        idx = modes.index(cur)
        new_mode = modes[(idx + 1) % len(modes)]
        self.compile_mode_var.set(new_mode)
        self._toggle_mode()
        
    def _open_apy_editor(self):
        apy_path = str(self.current_apyscript) if self.current_apyscript else ""
        apyeditor_window = ApyEditor(self.master, apyscript_file=apy_path, style=self.style)
        apyeditor_window.show()
        
    def _open_general_settings(self):
        show_general_settings(self.master, self.config, self.style, self.themes[self.current_theme_index])
        
    def _add_empty_project(self):
        name = simpledialog.askstring("Empty Project", "Name:")
        if not name:
            return
        p = Project(name=name)  # nur Name, keine Datei
        p.compile_a_selected = True
        self.projects.append(p)
        self._refresh_tree()
        self.status_var.set(f"Empty project '{name}' added. ➕")

    def _open_debuginspector(self):
        # If any compile_*.log exists, open the newest
        logs = sorted(Path.cwd().glob("compile_*.log"), reverse=True)
        if not logs:
            self.set_status("No log file found. 📄🚫", hold_ms=2500)
            return

        latest_log = logs[0]
        debuginspector(self.master, str(latest_log), self.projects, self.style, self.config)


    def _update_ui_texts(self) -> None:
        print("Updating UI texts...")
        self.master.title(self.texts["title"])
        self.tree.heading("A", text=self.texts["compile_a_col"])
        self.tree.heading("B", text=self.texts["compile_b_col"])
        self.tree.heading("C", text=self.texts["compile_c_col"])
        self.tree.heading("Name", text=self.texts["name_col"])
        self.tree.heading("Script", text=self.texts["script_col"])
        self.tree.heading("PyArmor", text="PyArmor")
        self.tree.heading("Cython", text="Cython")
        self.tree.heading("Nuitka", text="Nuitka")
        self.status_var.set(self.texts["status_ready"])

        # Buttons links (Add, Edit, Delete, Save, Save As, Load, Clear)
        button_attr_and_keys = [
            (self.add_btn, "add_btn", "tooltip_add_btn"),
            (self.edit_btn, "edit_btn", "tooltip_edit_btn"),
            (self.delete_btn, "delete_btn", "tooltip_delete_btn"),
            (self.save_btn, "save_btn", "tooltip_save_btn"),
            (self.save_as_btn, "save_as_btn", "tooltip_save_as_btn"),
            (self.load_btn, "load_btn", "tooltip_load_btn"),
            (self.clear_btn, "clear_btn", "tooltip_clear_btn"),
        ]
        for btn, key, tip_key in button_attr_and_keys:
            btn.config(text=self.texts[key])
            CreateToolTip(btn, self.texts[tip_key])

        # Buttons rechts (Clear Logs, Inspector, Start Export)
        right_buttons = [
            (self.compile_all_btn, "compile_all_btn", "tooltip_compile_all_btn"),
            (self.debug_btn, "debug_btn", "tooltip_debug_btn"),
            (self.clear_work_dir_btn, "clear_work_dir_btn", "tooltip_clear_work_dir_btn"),
        ]
        for btn, text_key, tooltip_key in right_buttons:
            btn.config(text=self.texts[text_key])
            CreateToolTip(btn, self.texts[tooltip_key])

        # Erzwinge ein Update der GUI
        self.master.update_idletasks()

        print("UI texts updated.")
    
    def _rename_project(self):
        sel = self.tree.selection()
        if not sel or not sel[0].startswith("proj_"):
            self.set_status("No entry selected. ⚠", hold_ms=2500)
            return

        try:
            idx = int(sel[0].split("_")[1])
            proj = self.projects[idx]
        except (ValueError, IndexError):
            self.set_status("Invalid project ID. 🆔❌", hold_ms=2500)
            return
        
        new_name = simpledialog.askstring(
            self.texts.get("rename_title", "Projekt umbenennen"),
            self.texts.get("rename_prompt", "Neuer Name:"),
            initialvalue=(getattr(proj, "divider_label", None) if getattr(proj, "is_divider", False) else proj.name),
            parent=self.master
        )
        if new_name is None:
            return  # Abbruch
        new_name = new_name.strip()
        if not new_name:
            self.status_warn(self.texts.get("rename_empty", "Please enter a name."))
            return

        # Kollisionen automatisch vermeiden (nur für echte Projekte relevant)
        if not getattr(proj, "is_divider", False):
            new_name = self._unique_name(new_name)

        old_name = proj.name
        proj.name = new_name
        # --- DIVIDER ---
        if getattr(proj, "is_divider", False):
            setattr(proj, "divider_label", new_name)
        # ---------------
        self._refresh_tree()
        self.tree.selection_set(f"proj_{idx}")
        self.tree.see(f"proj_{idx}")

        try:
            self._save_current_file()
        except Exception:
            pass

        self.status_var.set(self.texts.get("status_renamed", "Umbenannt.").format(old=old_name, new=new_name))

        
    def _unique_name(self, base: str) -> str:
        existing = {p.name for p in self.projects if not getattr(p, "is_divider", False)}
        if base not in existing:
            return base
        i = 2
        while True:
            candidate = f"{base} {i}"
            if candidate not in existing:
                return candidate
            i += 1

    # --- DIVIDER ---
    def _add_divider(self):
        label = simpledialog.askstring("Add divider", "Label:", parent=self.master)
        if label is None:
            self.status_info("Canceled.")
            return
        label = label.strip()
        if not label:
            self.status_warn("Please enter a label.")
            return

        p = Project(name=label)
        p.is_divider = True
        p.divider_label = label

        for a in ("compile_a_selected","compile_b_selected","compile_c_selected",
                  "use_pyarmor","use_nuitka","use_cython",
                  "use_pytest","use_pytest_standalone",
                  "use_sphinx","use_sphinx_standalone"):
            setattr(p, a, False)
        for a in ("script","spec_file","cython_output_dir","cpp_output_dir"):
            setattr(p, a, "")

        sel = self.tree.selection()
        if sel and sel[0].startswith("proj_"):
            idx = int(sel[0].split("_")[1])
            insert_at = max(0, min(len(self.projects), idx))
            self.projects.insert(insert_at, p)
            select_iid = f"proj_{insert_at}"
        else:
            self.projects.append(p)
            select_iid = f"proj_{len(self.projects)-1}"

        self._refresh_tree()
        try:
            self.tree.selection_set(select_iid)
            self.tree.see(select_iid)
        except Exception:
            pass
        try:
            self._save_current_file()
        except Exception:
            pass

        self.status_ok(f'Divider "{label}" added. ➕')
    
    def _duplicate(self):
        sel = self.tree.selection()
        if not sel:
            self.status_warn(self.texts.get("error_no_entry", "No entry selected."))
            return

        row_id = sel[0]
        if not row_id.startswith("proj_"):
            self.status_warn("Select a project row.")
            return

        try:
            idx = int(row_id.split("_")[1])
            original: Project = self.projects[idx]
        except (ValueError, IndexError):
            self.status_err("Invalid project ID.")
            return

        try:
            new_p: Project = copy.deepcopy(original)
        except Exception:
            new_p = Project()
            for k, v in vars(original).items():
                setattr(new_p, k, copy.deepcopy(v) if isinstance(v, (dict, list, set, tuple)) else v)

        if getattr(original, "is_divider", False):
            base_name = f"{getattr(original, 'divider_label', original.name)} (copy)"
            new_p.name = base_name
            setattr(new_p, "divider_label", base_name)
            setattr(new_p, "is_divider", True)
            for attr in ("compile_a_selected","compile_b_selected","compile_c_selected",
                         "use_pyarmor","use_nuitka","use_cython","use_pytest","use_sphinx",
                         "use_pytest_standalone","use_sphinx_standalone"):
                try: setattr(new_p, attr, False)
                except Exception: pass
        else:
            base_name = f"{original.name} (copy)"
            new_p.name = self._unique_name(base_name)

        insert_at = idx + 1
        self.projects.insert(insert_at, new_p)
        self._refresh_tree()
        self.tree.selection_set(f"proj_{insert_at}")
        self.tree.see(f"proj_{insert_at}")

        try:
            self._save_current_file()
        except Exception:
            pass

        self.status_ok(f'Project "{new_p.name}" duplicated. 📄➕')

    def _choose_colors(self):
        color_a = colorchooser.askcolor(title="Pick color for Mode A 🎨", color=self.color_a)[1]
        if color_a:
            self.color_a = color_a
            self.config["color_a"] = color_a
        color_b = colorchooser.askcolor(title="Pick color for Mode B 🎨", color=self.color_b)[1]
        if color_b:
            self.color_b = color_b
            self.config["color_b"] = color_b
        color_c = colorchooser.askcolor(title="Pick color for Mode C 🎨", color=self.color_c)[1]
        if color_c:
            self.color_c = color_c
            self.config["color_c"] = color_c
        save_config(self.config)
        self._update_tag_colors()
        self._refresh_tree()
        self._apply_progressbar_style() 

    def _update_headings(self):
        mode = self.compile_mode_var.get()
        
        self.tree.heading("A",text=f'{"🚀 " if mode == "A" else ""}{self.texts["compile_a_col"]}{" 🚀" if mode == "A" else ""}')
        self.tree.heading("B",text=f'{"🚀 " if mode == "B" else ""}{self.texts["compile_b_col"]}{" 🚀" if mode == "B" else ""}')
        self.tree.heading("C",text=f'{"🚀 " if mode == "C" else ""}{self.texts["compile_c_col"]}{" 🚀" if mode == "C" else ""}')
        
    def _refresh_tree(self):
        """
        Aktualisiert die Treeview-Einträge (Checkboxen, PyArmor- und Nuitka-Status, etc.).
        """
        mode = self.compile_mode_var.get()
        # Sortiere Projekte: SPEC-Dateien unten
        sorted_projects = sorted(
            enumerate(self.projects),
            key=lambda t: not (getattr(t[1], "spec_file", "") and str(getattr(t[1], "spec_file", "")).lower().endswith(".spec"))
        )
        existing_iids = set(self.tree.get_children())
        new_iids = set()

        last_type = None
        for idx, p in sorted_projects:
            if p is None:
                continue

            if getattr(p, "is_divider", False):
                iid = f"proj_{idx}"
                new_iids.add(iid)
                label = getattr(p, "divider_label", p.name) or "—"
                values = ("", "", "", f"— {label} —", "", "", "", "", "", "")
                if iid in existing_iids:
                    self.tree.item(iid, values=values, tags=("divider",))
                else:
                    self.tree.insert("", "end", iid=iid, values=values, tags=("divider",))
                # Wichtig: last_type NICHT ändern, damit automatische Typ-Trenner stabil bleiben
                continue
            # ------------------------------------------------------------

            script_name = p.script or getattr(p, "spec_file", "") or ""
            is_spec = bool(getattr(p, "spec_file", "") and str(getattr(p, "spec_file")).lower().endswith(".spec"))
            typ = "spec" if is_spec else "py"

            if typ != last_type:
                divider_iid = f"divider_{typ}"
                new_iids.add(divider_iid)
                divider_text = "──── SPEC FILES ────" if typ == "spec" else "──── PYTHON FILES ────"
                divider_values = ("", "", "", "", "", "", "", "", "", divider_text)
                if divider_iid not in existing_iids:
                    self.tree.insert(
                        "", "end", iid=divider_iid,
                        values=divider_values,
                        tags=("divider",)
                    )
                last_type = typ

            pyarmor_status = "🛡" if getattr(p, "use_pyarmor", False) else ""
            nuitka_status  = "⚡" if getattr(p, "use_nuitka", False) else ""
            cython_status  = "🧩" if getattr(p, "use_cython", False) else ""

            pytest_status  = (
                "🧪🔒" if getattr(p, "use_pytest_standalone", False)
                else "🧪" if getattr(p, "use_pytest", False)
                else ""
            )
            sphinx_status  = (
                "📚🔒" if getattr(p, "use_sphinx_standalone", False)
                else "📚" if getattr(p, "use_sphinx", False)
                else ""
            )
            
            chk_a = CHECKED if getattr(p, "compile_a_selected", False) else UNCHECKED
            chk_b = CHECKED if getattr(p, "compile_b_selected", False) else UNCHECKED
            chk_c = CHECKED if getattr(p, "compile_c_selected", False) else UNCHECKED

            
            if mode == "A":
                tags = ("mode_a",)
            elif mode == "B":
                tags = ("mode_b",)
            elif mode == "C":
                tags = ("mode_c",)
            else:
                tags: tuple = ()

            # Treeview-Eintrag aktualisieren oder einfügen
            iid = f"proj_{idx}"
            new_iids.add(iid)

            values = (
                chk_a, chk_b, chk_c, p.name,
                pytest_status,   
                pyarmor_status,  
                nuitka_status,   
                cython_status, 
                sphinx_status,
                script_name    
            )

            if iid in existing_iids:
                self.tree.item(
                    iid,
                    values=values,
                    tags=tags
                )
            else:
                self.tree.insert(
                    "", "end", iid=iid,
                    values=values,
                    tags=tags
                )

        # Entferne nicht mehr benötigte Einträge
        for iid in existing_iids - new_iids:
            self.tree.delete(iid)



    def _toggle_cell(self, e):
        col = self.tree.identify_column(e.x)
        row_id = self.tree.identify_row(e.y)
        if not row_id:
            return

        tags = self.tree.item(row_id, "tags")
        if "divider" in tags:
            return  # Trennerzeilen sind nicht klick-/umschaltbar

        if row_id.startswith("proj_"):
            proj_index = int(row_id.split("_")[1])
        else:
            return

        p = self.projects[proj_index]

        if col == "#1":
            p.compile_a_selected = not getattr(p, "compile_a_selected", False)
        elif col == "#2":
            p.compile_b_selected = not getattr(p, "compile_b_selected", False)
        elif col == "#3":
            p.compile_c_selected = not getattr(p, "compile_c_selected", False)
        else:
            return
        self._refresh_tree()

    def _add(self):
        path = filedialog.askopenfilename(filetypes=[
            ("Python Files (*.py)", "*.py"),
            ("Cython Files (*.pyx)", "*.pyx"),
            ("Spec Files", "*.spec")
        ])
        if not path:
            return

        # Handle different file types
        if path.lower().endswith(".spec"):
            p = parse_spec_file(path)
        elif path.lower().endswith(".pyx"):
            p = Project(script=path, use_cython=True)  # Explicitly set use_cython to True for .pyx files
        else:
            p = Project(script=path)

        if p is not None:
            p.compile_a_selected, p.compile_b_selected, p.compile_c_selected = True, False, False
            self.projects.append(p)
            self._refresh_tree()
            self.status_var.set(self.texts["status_project_added"].format(name=p.name))
        else:
            self.status_var.set("Project could not be added (parse_spec_file returned None)")

    def _edit(self) -> None:
        # --- IMPROVED: No thread for short operations like edit – use static status only ---
        sel = self.tree.selection()
        if not sel:
            self.status_warn(self.texts["error_no_entry"])
            return

        row_id = sel[0]
        if not row_id.startswith("proj_"):
            self.status_warn("Select a project row.")
            return

        try:
            proj_index = int(row_id.split("_")[1])
            proj: Project = self.projects[proj_index]
        except (ValueError, IndexError):
            self.status_err("Invalid project ID.")
            return

        # --- Set static status before blocking dialog (no animation/thread) ---
        self.set_status("Editing project...", hold_ms=None)

        # --- SPEC-Projekt? ---
        if getattr(proj, "spec_file", None) and str(proj.spec_file).lower().endswith(".spec"):
            try:
                from .speceditor import SpecEditor  # Ensure import succeeds
            except ImportError as e:
                messagebox.showerror(
                    "Import Error",
                    f"SpecEditor module could not be loaded: {e}"
                )
                return

            editor = SpecEditor(self.master, proj, self.texts)
            if editor.show():
                self._refresh_tree()
                self._save_current_file()
                self.set_status(f'Spec project "{proj.name}" updated. 🔧', hold_ms=2000)
            return  # Early return for spec

        # --- Normales Projekt ---
        editor = ProjectEditor(self.master, proj, self.texts, self)
        if editor.show():
            self._refresh_tree()
            self._save_current_file()
            self.set_status(f'Project "{proj.name}" updated. ✅', hold_ms=2000)
        # No thread to stop – clean and safe
        
    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            self.status_warn(self.texts["error_no_entry"])
            return
        row_id = sel[0]
        if not row_id.startswith("proj_"):
            self.status_warn("Select a project row.")
            return
        proj_index = int(row_id.split("_")[1])
        name = self.projects[proj_index].name
        del self.projects[proj_index]
        self._refresh_tree()
        self.status_ok(f'Project "{name}" deleted. 🗑')


    def _clear(self):
        self.projects.clear()
        self._refresh_tree()
        self.status_var.set("All projects removed. 🧹")

    def _change_language(self, *_):
        new_language = self.language_var.get()
        print(f"Selected language: {new_language}")
        if new_language not in LANGUAGES:
            self.status_err(f"Language {new_language} not supported.")
            return
        self.current_language = new_language
        self.texts = LANGUAGES[self.current_language]
        #print(f"Loaded texts for {self.current_language}: {self.texts}")
        self._fallback_texts()
        self._build_menubar()
        self._update_ui_texts()
        self._refresh_tree()
        self.config["language"] = self.current_language
        save_config(self.config)
        print(f"Config saved with language: {self.config['language']}")

    def _cycle_theme(self, step: int = 1):
        """Cycle through available themes (no Light/Dark toggle; only themes)."""
        self.current_theme_index = (self.current_theme_index + step) % len(self.themes)
        self.themes[self.current_theme_index](self.style, self.master)
        self.config["theme"] = self.current_theme_index
        save_config(self.config)
        self.set_status(f"Theme: {self.theme_names[self.current_theme_index]} 🎨", hold_ms=1600)
        self._update_tag_colors()
        self._refresh_tree()
        self._apply_progressbar_style()
        
    def _toggle_mode(self):
        #self.mode_btn.config(text=self._mode_label())
        self.status_var.set(f"Active compile mode: {self._mode_label()} 🚦")
        self.config["compile_mode"] = self.compile_mode_var.get()
        save_config(self.config)
        self._update_tag_colors() 
        self._update_headings()
        self._refresh_tree()
        self._apply_progressbar_style()

    def clear_work_dir(self):
        #work_dir = Path(__file__).parent.parent
        work_dir = self.working_dir 
        files, folders = find_cleanup_targets(work_dir)
        targets = files + folders

        if not targets:
            self.status_info("Nothing to delete. 🧺")
            return

        file_list = ""
        if files:
            file_list += "Files to delete:\n" + "\n".join(f"- {f.name}" for f in files) + "\n\n"
        if folders:
            file_list += "Folders to delete:\n" + "\n".join(f"- {f.name}" for f in folders)

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the following files and folders?\n\n{file_list}"
        )

        if not confirm:
            return

        threading.Thread(target=self._delete_files, args=(targets,)).start()

    def _delete_files(self, targets):
        deleted_files = delete_files_and_dirs(targets)
        self.master.after(0, lambda: self.set_status(f"{deleted_files} files/folders deleted. 🧹", hold_ms=3000))
        
    def _save(self):
        if not self.projects:
            self.status_warn(self.texts["error_no_entry"])
            return

        f = filedialog.asksaveasfilename(
            defaultextension=".apyscript",
            filetypes=[("apyscript", "*.apyscript"), ("Spec File", "*.spec")],
            initialdir=str(self.current_apyscript.parent) if self.current_apyscript else os.getcwd()
        )
        if not f:
            self.status_info("Save canceled.")
            return

        if f.lower().endswith(".apyscript"):
            save_projects(self.projects, f)
            self.status_ok(f"Saved all projects → {f} 💾")

        elif f.lower().endswith(".spec"):
            sel = self.tree.selection()
            if not sel:
                self.status_warn("No project selected to export as .spec.")
                return
            row_id = sel[0]
            if not row_id.startswith("proj_"):
                self.status_warn("Only projects can be exported as .spec.")
                return
            try:
                idx = int(row_id.split("_")[1])
            except Exception:
                self.status_err("Invalid project ID.")
                return
            save_projects([self.projects[idx]], f)
            self.status_ok(f'Exported "{self.projects[idx].name}" as .spec → {f} 📦')

        else:
            self.status_err("Unknown export format. ❓")

    def _export_ini(self):
        ini_path = Path(__file__).parent / "extensions_path.ini"
        folder = filedialog.askdirectory(title="Choose destination folder")
        if not folder:
            self.status_info("Export canceled.")
            return
        target = Path(folder) / "extensions_path.ini"
        try:
            export_extensions_ini(ini_path, target)
            self.status_ok(f"Exported extensions_path.ini → {target} 📤")
        except Exception as e:
            self.status_err(f"Export error: {e}")

    def _load(self):
        file = filedialog.askopenfilename(
            title="Open .apyscript",
            filetypes=[("apyscript files", "*.apyscript")],
            initialdir=self._initial_dir()
        )
        if not file:
            self.status_info("Open canceled.")
            return

        if not file.lower().endswith(".apyscript"):
            self.status_err("Only .apyscript files are allowed. 🚫")
            return

        try:
            self.projects = load_projects(file)
            self.current_apyscript = Path(file)                  
            set_last_apyscript(self.config, self.current_apyscript) 

            # Fix potential inconsistent states
            for p in self.projects:
                if getattr(p, "use_pyarmor", False) and getattr(p, "use_nuitka", False):
                    p.use_nuitka = False
                if not hasattr(p, "is_divider"):
                    setattr(p, "is_divider", False)
                if getattr(p, "is_divider", False) and not hasattr(p, "divider_label"):
                    setattr(p, "divider_label", p.name)

            self._refresh_tree()
            self.status_ok(f"Loaded: {file} 📂")
        except Exception as err:
            self.status_err(f"Load failed: {err}")



    def update_treeview(self):
        self._refresh_tree()
    def _auto_load(self):
        # 1) optional: letztes Projekt laden
        if bool(self.config.get("load_last_on_start", True)):
            last = get_last_apyscript(self.config)
            if last and last.is_file():
                try:
                    self.projects = load_projects(last)
                    self.current_apyscript = last
                    for p in self.projects:
                        if getattr(p, "use_pyarmor", False) and getattr(p, "use_nuitka", False):
                            p.use_nuitka = False
                        if not hasattr(p, "is_divider"):
                            setattr(p, "is_divider", False)
                        if getattr(p, "is_divider", False) and not hasattr(p, "divider_label"):
                            setattr(p, "divider_label", p.name)
                    self._refresh_tree()
                    self.set_status(f"Auto-loaded last project: {last} 📂", hold_ms=2000)
                    return
                except Exception as e:
                    self.set_status(f"Auto-load last failed: {e} ❌", hold_ms=3500)

        # 2) Fallback: myProject.apyscript
        default_file = Path("myProject.apyscript")
        if default_file.is_file():
            try:
                self.projects = load_projects(default_file)
                self.current_apyscript = default_file
                for p in self.projects:
                    if getattr(p, "use_pyarmor", False) and getattr(p, "use_nuitka", False):
                        p.use_nuitka = False
                    if not hasattr(p, "is_divider"):
                        setattr(p, "is_divider", False)
                    if getattr(p, "is_divider", False) and not hasattr(p, "divider_label"):
                        setattr(p, "divider_label", p.name)
                self._refresh_tree()
                self.set_status(f"Auto-loaded {default_file} 📂", hold_ms=2000)
            except Exception as e:
                self.set_status(f"Auto-load failed for {default_file}: {e} ❌", hold_ms=3500)


    def _save_current_file(self):
        """Speichert Projekte in der zuletzt verwendeten .apyscript-Datei (wie STRG+S)."""
        if not self.projects:
            self.status_warn(self.texts["error_no_entry"])
            return

        if not self.current_apyscript or not str(self.current_apyscript).lower().endswith(".apyscript"):
            self._save_as()
            return

        save_projects(self.projects, self.current_apyscript)
        self.status_var.set(f"Saved: {self.current_apyscript} 💾")
        try:
            set_last_apyscript(self.config, self.current_apyscript)
        except Exception:
            pass
        
    def _save_as(self):
        if not self.projects:
            self.status_warn("No entries to save.")
            return

        f = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".apyscript",
            filetypes=[("apyscript", "*.apyscript"), ("Spec File", "*.spec")],
            initialdir=self._initial_dir()
        )

        if not f:
            self.status_info("Save canceled.")
            return

        if f.lower().endswith(".apyscript"):
            save_projects(self.projects, f)
            self.current_apyscript = Path(f)
            set_last_apyscript(self.config, self.current_apyscript)  # << hinzufügen
            self.status_ok(f"Saved all projects → {f} 💾")


        elif f.lower().endswith(".spec"):
            sel = self.tree.selection()
            if not sel:
                self.status_warn("Select a project to export as .spec.")
                return
            row_id = sel[0]
            if not row_id.startswith("proj_"):
                self.status_warn("Only regular projects can be exported as .spec.")
                return
            try:
                idx = int(row_id.split("_")[1])
            except Exception:
                self.status_err("Invalid project ID.")
                return
            save_projects([self.projects[idx]], f)
            self.status_ok(f'Exported "{self.projects[idx].name}" → {f} 📦')

        else:
            self.status_err("Unsupported export format. 🚫")
                
    def run_status_animation(self, stop_event: threading.Event, interval: float = 0.15) -> None:
        idx = 0
        frames = ["⠁","⠃","⠇","⠧","⠷","⠿","⠷","⠧","⠇","⠃","⠁"," "]
        while not stop_event.is_set():
            now = time.time()
            with self._status_lock:
                if now >= self._hold_until_ts:
                    base = self._last_user_status or self.texts.get("status_ready","Ready")
                    spinner = frames[idx % len(frames)]
                    self.status_var.set(f"{base}  {spinner}")
            idx += 1
            self.master.update_idletasks()
            time.sleep(interval)

    def _get_pipeline_cooldown_s(self) -> int:
        try:
            return max(0, int(self.config.get("pipeline_cooldown_s", getattr(self, "pipeline_cooldown_s", 0))))
        except Exception:
            return 0




    def _open_python_terminal(self):
        """
        Öffnet unter Windows ein Terminal im aktuellen Python-Setting (inkl. venv),
        so dass 'python' und 'pip' zuverlässig dieses Environment nutzen.
        """
        try:
            if os.name != "nt":
                self.status_err("Dieses Terminal ist aktuell nur für Windows implementiert.")
                return

            py = sys.executable
            # Falls working_dir nicht existiert, ins aktuelle Verzeichnis wechseln
            cwd = str(self.working_dir if Path(self.working_dir).exists() else Path.cwd())
            env = os.environ.copy()

            scripts_dir = str(Path(py).parent)
            env["PATH"] = scripts_dir + os.pathsep + env.get("PATH", "")
            
            cmdline = (
                f'title AutoPy🐍🐍& '
                f'echo AutoPy🐍🐍& '
                f'echo launching in virtual environment& '
                f'"{py}" -V & '
                f'doskey pip="{py}" -m pip $* & '
                f'doskey python="{py}" $* & '
                f'cd /d "{cwd}"'
            )

            creation = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

            # Bevorzugt Windows Terminal
            if shutil.which("wt.exe"):
                subprocess.Popen(["wt.exe", "cmd", "/k", cmdline], cwd=cwd, env=env, creationflags=creation)
                self.status_ok("🐍.")
                return

            # Fallback: klassisches CMD
            subprocess.Popen(["cmd.exe", "/k", cmdline], cwd=cwd, env=env, creationflags=creation)
            self.status_ok("🐍.")

        except Exception as e:
            self.status_err(f"Error with Terminal: {e}")


    def _run_windows_update(self, as_admin: bool = False) -> None:
        """
        Startet windows_update.ps1 mit sichtbarem Konsolenfenster
        und schließt anschließend AutoPy++.
        """
        try:
            root = Path(__file__).resolve().parent.parent
            ps1 = root / "windows_update.ps1"

            if not ps1.exists():
                messagebox.showerror("Datei nicht gefunden", f"windows_update.ps1 nicht gefunden:\n{ps1}")
                return

            self.status_info("Starte Windows-Update …")

            # Sichtbares Konsolenfenster für nicht-admin Run
            creationflags_normal = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

            if as_admin:
                # Erhöht starten: das ELEVATED-Fenster ist sichtbar (WindowStyle Normal).
                # Die nicht-erhöhte Helfer-PowerShell halten wir unsichtbar (kein doppeltes Blinken).
                arglist = f'-NoProfile -ExecutionPolicy Bypass -File "{ps1}"'
                ps_cmd = (
                    f'Start-Process -Verb RunAs -FilePath "powershell.exe" '
                    f'-ArgumentList {arglist!r} -WindowStyle Normal'
                )

                subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    cwd=str(root),
                    creationflags=subprocess.CREATE_NO_WINDOW  # nur die Helfer-PS verstecken
                )
            else:
                # Normal (sichtbares Konsolenfenster)
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
                    cwd=str(root),
                    creationflags=creationflags_normal
                )

            self.status_ok("Update gestartet. AutoPy++ wird jetzt geschlossen …")
            self.master.after(200, self.master.quit)

        except Exception as e:
            self.status_err(f"Fehler beim Starten: {e}")


    def compile_all(self):
        self.status_var.set("Start Export 📦")
        if not self._check_hashes_before_build():
            return  # Abbruch

        stop_event = threading.Event()
        threading.Thread(target=self.run_status_animation, args=(stop_event,), daemon=True).start()

        prog = tk.DoubleVar(value=0)
        self._apply_progressbar_style()
        pb = ttk.Progressbar(self.main_frame, variable=prog, maximum=100, style=self.pb_style_name)
        pb.pack(fill="x", pady=5)

        def do_compile():
            
            log_path = None  # wir arbeiten nur mit dem Pfad und öffnen bei Bedarf
            try:
                def upd_status(msg: str):
                    self.master.after(0, lambda: self.set_status(msg, hold_ms=2000))

                def set_prog(val: float):
                    self.master.after(0, lambda: prog.set(val))

                # --- aktiven Modus lesen und Auswahl bilden ---
                active_mode = self.compile_mode_var.get()
                selected = [
                    p for p in self.projects
                    if not getattr(p, "is_divider", False) and (
                        (active_mode == "A" and getattr(p, "compile_a_selected", False)) or
                        (active_mode == "B" and getattr(p, "compile_b_selected", False)) or
                        (active_mode == "C" and getattr(p, "compile_c_selected", False))
                    )
                ]
                if not selected:
                    self.master.after(0, lambda: self.set_status(self.texts["error_no_entry"], hold_ms=2500))
                    return

                first_name = selected[0].name.replace(" ", "_")
                suffix = f"_and_{len(selected)-1}_more" if len(selected) > 1 else ""
                log_path = Path(f"compile_{first_name}{suffix}_{datetime.now().strftime('%Y%m%d_%H%M')}.log")

                def log(line: str):
                    with open(log_path, "a", encoding="utf-8") as fh:
                        fh.write(line)
                        if not line.endswith("\n"):
                            fh.write("\n")

                sequential = bool(self.config.get("sequential_build", False))
                if hasattr(self, "sequential_build_var"):
                    try:
                        sequential = bool(self.sequential_build_var.get())
                    except Exception:
                        pass

                threads = 1 if sequential else self._get_thread_count()
                cooldown_s = self._get_pipeline_cooldown_s() if sequential else 0


                print(f"[DEBUG] Pipeline (Top/Down): {sequential} -> threads={threads}, cooldown={cooldown_s}s")
                log(f"Starting compilation at {datetime.now()}")
                log(f"Pipeline (Top/Down): {sequential} -> threads={threads}, cooldown={cooldown_s}s")

                errors = []

                # ================== SEQUENTIAL: nur aktiver Modus, in Listenreihenfolge ==================
                if sequential:
                    total = len(selected)
                    done = 0

                    for i, proj in enumerate(selected):
                        # pro Projekt den gewünschten Compiler ableiten
                        if getattr(proj, "use_pyarmor", False) and not getattr(proj, "use_nuitka", False) and not getattr(proj, "use_cython", False):
                            per_compiler = "pyarmor"
                        elif getattr(proj, "use_nuitka", False) and not getattr(proj, "use_pyarmor", False) and not getattr(proj, "use_cython", False):
                            per_compiler = "nuitka"
                        elif getattr(proj, "use_cython", False) and not getattr(proj, "use_pyarmor", False) and not getattr(proj, "use_nuitka", False):
                            per_compiler = "cython"
                        elif (not getattr(proj, "use_pyarmor", False)
                              and not getattr(proj, "use_nuitka", False)
                              and not getattr(proj, "use_cython", False)):
                            per_compiler = "pyinstaller"
                        else:
                            per_compiler = "pyinstaller"

                        log(f"[{i+1}/{total}] Start: {proj.name} (compiler={per_compiler}, mode={active_mode})")
                        
                        def overall_progress(cur, tot, _done=done, _total=total):
                            portion = (_done + (cur / max(1, tot))) / max(1, _total)
                            set_prog(portion * 100)

                        with open(log_path, "a", encoding="utf-8") as job_log:
                            err = compile_projects(
                                [proj],
                                thread_count=1,
                                log_file=job_log,
                                status_callback=lambda msg, _i=i: self.master.after(
                                    0, lambda: upd_status(f"[{_i+1}/{total}] {msg}")
                                ),
                                progress_callback=lambda cur, tot: overall_progress(cur, tot),
                                compiler=per_compiler,
                                mode=active_mode,
                            )
                        if err:
                            errors.extend(err)

                        done += 1

                        # Cooldown
                        if i < total - 1 and cooldown_s > 0:
                            for remaining in range(cooldown_s, 0, -1):
                                self.master.after(0, lambda r=remaining: self.set_status(f"🕒 Cooldown {r}s …", hold_ms=900))
                                time.sleep(1)

                # ================== PARALLEL: wie gehabt, nur aktiver Modus ==================
                else:
                    # einheitlichen Compiler nur dann erzwingen, wenn ALLE gleich konfiguriert sind
                    compiler_mode = "pyinstaller"
                    if all(getattr(p, "use_pyarmor", False) and not getattr(p, "use_nuitka", False) and not getattr(p, "use_cython", False) for p in selected):
                        compiler_mode = "pyarmor"
                    elif all(getattr(p, "use_nuitka", False) and not getattr(p, "use_pyarmor", False) and not getattr(p, "use_cython", False) for p in selected):
                        compiler_mode = "nuitka"
                    elif all(getattr(p, "use_cython", False) and not getattr(p, "use_pyarmor", False) and not getattr(p, "use_nuitka", False) for p in selected):
                        compiler_mode = "cython"
                    elif all(not getattr(p, "use_pyarmor", False) and not getattr(p, "use_nuitka", False) and not getattr(p, "use_cython", False) for p in selected):
                        compiler_mode = "pyinstaller"

                    print(f"[DEBUG] Compile Projects: {len(selected)} projects, thread_count={threads}, mode={active_mode}, compiler={compiler_mode}")
                    log(f"Compile Projects: {len(selected)} projects, thread_count={threads}, mode={active_mode}, compiler={compiler_mode}")

                    with open(log_path, "a", encoding="utf-8") as run_log:
                        errors = compile_projects(
                            selected,
                            thread_count=threads,
                            log_file=run_log,
                            status_callback=lambda msg: self.master.after(0, lambda: upd_status(msg)),
                            progress_callback=lambda cur, total: self.master.after(0, lambda: prog.set((cur / max(1, total)) * 100)),
                            compiler=compiler_mode,
                            mode=active_mode,
                        )

                if errors:
                    def show_debug():
                        self.status_var.set("Successfully Finished (with Errors).")
                        debuginspector(self.master, str(log_path), selected, self.style, self.config)
                        self._refresh_tree()
                    self.master.after(0, show_debug)
                else:
                    self.master.after(0, lambda: (
                        self.status_var.set("Successfully Finished 😊 "),
                        self.master.after(2000, lambda: self.status_var.set(self.texts["status_ready"]))
                    ))

            except Exception as e:
                def _on_fail(err=e, lp=log_path):
                    try:
                        if lp:
                            with open(lp, "a", encoding="utf-8") as fh:
                                fh.write(f"Compilation failed: {err}\n")
                    except Exception:
                        pass
                    if lp and Path(lp).exists():
                        debuginspector(self.master, str(lp), [], self.style, self.config)
                self.master.after(0, _on_fail)
            finally:
                stop_event.set()
                self.master.after(0, pb.destroy)

        threading.Thread(target=do_compile, daemon=True).start()



    def _show_extensions_popup(self):
        KNOWN_TOOLS = [
            "pyinstaller", "pyarmor", "nuitka", "cython",
            "cpp", "gcc", "msvc", "tcl_base", "pytest", "sphinx-quickstart", "sphinx-build", "pylint", "pyreverse"
        ]

        ini_file = Path(__file__).parent / "extensions_path.ini"
        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read(ini_file, encoding="utf-8")

        if "paths" not in cfg:
            cfg["paths"] = {}

        paths = dict(cfg["paths"])
        entries = {}

        popup = tk.Toplevel(self.master)
        popup.title("Extensions")
        popup.transient(self.master)
        popup.resizable(False, False)
        popup.geometry("+%d+%d" % (self.master.winfo_rootx() + 200, self.master.winfo_rooty() + 80))
        popup.configure(background="#222222")

        frame = ttk.Frame(popup, padding=12, style="White.TFrame")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="extensions_path.ini", font=("", 13, "bold"), style="White.TLabel").pack(pady=(0, 12))

        container = ttk.Frame(frame, style="White.TFrame")
        container.pack(fill="both", expand=True)

        def render_entries():
            for child in container.winfo_children():
                child.destroy()

            for key, val in sorted(paths.items()):
                row = ttk.Frame(container, style="White.TFrame")
                row.pack(fill="x", pady=2)

                ttk.Label(row, text=key, width=14, style="White.TLabel").pack(side="left", padx=(0, 6))

                var = tk.StringVar(value=val)
                entries[key] = var

                entry = ttk.Entry(row, textvariable=var, width=52, style="White.TEntry")
                entry.pack(side="left", fill="x", expand=True)

                def make_browse(var, key):
                    def _browse():
                        if "dir" in key.lower() or key.endswith("_base"):
                            p = filedialog.askdirectory(title=f"{key} wählen")
                        else:
                            p = filedialog.askopenfilename(title=f"{key} wählen")
                        if p:
                            var.set(p)
                    return _browse

                ttk.Button(row, text="...", width=3, command=make_browse(var, key), style="White.TButton").pack(side="left", padx=4)

                def make_remove(k):
                    def _remove():
                        if k in paths:
                            del paths[k]
                        if k in entries:
                            del entries[k]
                        render_entries()
                    return _remove

                ttk.Button(row, text="🗑", width=2, command=make_remove(key), style="White.TButton").pack(side="left", padx=2)

        render_entries()

        def add_entry():
            used_keys = set(paths.keys())
            free_keys = [k for k in KNOWN_TOOLS if k not in used_keys]

            if not free_keys:
                self.status_info("Toolset is full – no more free tools.")
                return

            dialog = tk.Toplevel(popup)
            dialog.title("Tool auswählen")
            dialog.resizable(False, False)
            dialog.grab_set()
            dialog.transient(popup)
            dialog.configure(background="#222222")

            ttk.Label(dialog, text="Choose Extension:", font=("", 11), style="White.TLabel").pack(padx=10, pady=(10, 4))
            selected_key = tk.StringVar(value=free_keys[0])
            combo = ttk.Combobox(dialog, values=free_keys, textvariable=selected_key, state="readonly", width=30)
            combo.pack(padx=10, pady=4)

            def confirm():
                key = selected_key.get()
                paths[key] = ""
                dialog.destroy()
                render_entries()

            ttk.Button(dialog, text="OK", command=confirm, style="White.TButton").pack(pady=(8, 10))
            dialog.bind("<Return>", lambda e: confirm())

        ttk.Button(frame, text="+ Add Tool", command=add_entry, style="White.TButton").pack(pady=(10, 0), fill="x")

        def save_and_close():
            cfg["paths"] = {}
            for k, var in entries.items():
                val = var.get()
                if os.name == "nt":
                    val = val.replace("/", "\\")
                cfg["paths"][k] = val
            with open(ini_file, "w", encoding="utf-8") as f:
                cfg.write(f)
            self.status_ok("INI saved 💾.")
            popup.destroy()

        ttk.Button(frame, text="Save", command=save_and_close, style="White.TButton").pack(pady=(6, 0), fill="x")

        popup.bind("<Escape>", lambda e: popup.destroy())
        popup.focus_set()
        popup.grab_set()
        popup.wait_window()
