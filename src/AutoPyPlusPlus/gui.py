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

#OWN MODULES

from .help import show_main_helper

from .about import show_about_dialog

from .simplex_api import SimplexAPIWatcher

from .debuginspector import debuginspector

from .project import Project

from .config import load_config, save_config

from .tooltip import CreateToolTip

from .parse_spec_file import parse_spec_file

from .compiler import compile_projects

from .language import LANGUAGES

from .projecteditor import ProjectEditor

from .apyeditor import ApyEditor

from .core import (
    save_projects, load_projects,
    export_extensions_ini, load_extensions_ini,
    find_cleanup_targets, delete_files_and_dirs
)

from .hotkeys import register_hotkeys

from .themes import (
    set_dark_mode, set_light_mode, set_arcticblue_mode, set_sunset_mode,
    set_forest_mode, set_retro_mode, set_pastel_mode, set_galaxy_mode,
    set_autumn_mode, set_candy_mode, set_inferno_mode,
    set_cyberpunk_mode, set_obsidian_mode, set_nebula_mode, set_midnight_forest_mode,
    set_phantom_mode, set_deep_space_mode, set_onyx_mode, set_lava_flow_mode,
)


class AutoPyPlusPlusGUI:
    """GUI mit zwei Checkbox-Spalten: *Kompilieren A* und *Kompilieren B*."""

    # ------------------------------ init -------------------------------
    def __init__(self, master: tk.Tk):
        
        self.current_apyscript: Optional[Path] = Path("myProject.apyscript")
        self.master = master
        self.config = load_config()
        self.projects: list[Project] = []
        self.working_dir = Path(self.config.get("working_dir")) if self.config.get("working_dir") else Path(__file__).parent.parent
        self.legacy_gui_mode = bool(self.config.get("legacy_gui_mode", False))

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
            "Pastel", "Autumn", "Candy", "Inferno", "Cyberpunk", "Obsidian",
            "Nebula", "Midnight Forest", "Phantom", "Deep Space", "Onyx", "Lava Flow"
        ]
        
        default_theme = 1  # Index 1 = set_light_mode
        self.current_theme_index = self.config.get("theme", default_theme) % len(self.themes)
        self.themes[self.current_theme_index](self.style, master)
        
            
        # -------- Farben ----------------------------------------------
        self.color_a: str = self.config.get("color_a", "#43d6b5")   
        self.color_b: str = self.config.get("color_b", "#4a1aae")   
        self.color_c: str = self.config.get("color_c", "#cd146c")   
        self.default_bg: str = "#ffffff"
        self.pb_style_name = "Compile.Horizontal.TProgressbar"
        self._apply_progressbar_style()
        # -------- Thread-Anzahl (wird automatisch gespeichert) --------
        self.max_threads = max(1, (os.cpu_count() or 1))
        init_threads = int(self.config.get("thread_count", self.max_threads) or self.max_threads)
        init_threads = max(1, min(self.max_threads, init_threads))

        self.thread_count_var = tk.IntVar(value=init_threads)
        self.thread_count_var.trace_add("write", self._save_thread_count)
        # -------- UI aufbauen & Projekte laden ------------------------
        self.status_var = tk.StringVar(value=self.texts["status_ready"])
        self._status_lock = threading.Lock()
        self._last_user_status = self.texts["status_ready"]
        self._hold_until_ts = 0.0        
        self._default_hold_ms = int(self.config.get("status_hold_ms", 2000))
        
        self._build_ui()        
        self._auto_load()
        self._register_hotkeys()
        show_about_dialog(self.master, self.style, self.themes[self.current_theme_index])
        
        # --- Simplex API Watcher ---
        ini_path = (self.working_dir / "simplexAPI.ini")
        self._simplex_watcher = SimplexAPIWatcher(self, ini_path, poll_interval=1.0)
        self._simplex_watcher.start()

        def _on_close():
            try:
                if hasattr(self, "_simplex_watcher"):
                    self._simplex_watcher.stop()
            except Exception:
                pass
            self.master.quit()

        self.master.protocol("WM_DELETE_WINDOW", _on_close)
                        
        
    # ------------------------- Hilfsmethoden --------------------------

    def _build_ui(self):
        # vorhandene Widgets (außer Toplevels) entfernen, dann alles neu aufbauen
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

        # Linke Buttons (immer erstellen)
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

        _Spinbox = getattr(ttk, "Spinbox", tk.Spinbox)  # Fallback, falls ttk.Spinbox fehlt
        self.thread_spin = _Spinbox(
            self.bar,
            from_=1,
            to=self.max_threads,
            textvariable=self.thread_count_var,
            width=3,
            justify="center",
        )
        self.thread_spin.pack(side="right", padx=6)

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

    def _select_language(self, lang):
        self.language_var.set(lang)
        self._change_language()
            
    def _set_theme_from_menu(self, idx):
        self.current_theme_index = idx
        self.themes[idx](self.style, self.master)
        self.config["theme"] = idx
        save_config(self.config)
        self.status_var.set(f"Theme gewechselt: {self.theme_names[idx]}")
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
        self.project_menu.add_command(label=self.texts.get("menu_edit", "Edit"), command=self._edit)
        self.project_menu.add_command(label=self.texts.get("menu_delete", "Delete"), command=self._delete)
        self.project_menu.add_command(label=self.texts.get("menu_duplicate", "Duplicate"), command=self._duplicate)
        self.project_menu.add_command(label=self.texts.get("menu_rename", "Rename"), command=self._rename_project)

        # ----- Tools -----
        self.tools_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_tools", "Tools"), menu=self.tools_menu)
        self.tools_menu.add_command(label=self.texts.get("menu_inspector", "Inspector"), command=self._open_debuginspector)
        self.tools_menu.add_command(label=self.texts.get("menu_apyeditor", "ApyEditor"), command=self._open_apy_editor)
        self.tools_menu.add_command(label=self.texts.get("menu_extensions", "Extensions"), command=self._show_extensions_popup)

        # ----- Build -----
        self.build_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_build", "Build"), menu=self.build_menu)
        self.build_menu.add_command(label=self.texts.get("menu_compile_all", "🚀 Compile All"), command=self.compile_all)
        self.build_menu.add_separator()
        self.build_menu.add_command(label=self.texts.get("menu_clean_workdir", "🧹 Clean Working Directory"), command=self.clear_work_dir)

        # ----- Settings -----
        self.settings_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label=self.texts.get("menu_settings", "General Settings"), menu=self.settings_menu)

        self.language_submenu = tk.Menu(self.settings_menu, tearoff=False)
        for lang in LANGUAGES.keys():
            self.language_submenu.add_command(label=lang, command=lambda l=lang: self._select_language(l))
        self.settings_menu.add_cascade(label=self.texts.get("menu_language", "Language"), menu=self.language_submenu)

        self.theme_submenu = tk.Menu(self.settings_menu, tearoff=False)
        for idx, theme_name in enumerate(self.theme_names):
            self.theme_submenu.add_command(label=theme_name, command=lambda i=idx: self._set_theme_from_menu(i))
        self.settings_menu.add_cascade(label=self.texts.get("menu_themes", "Themes"), menu=self.theme_submenu)

        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.texts.get("menu_autopy_general", "AutoPy++ General"), command=self._open_general_settings)
        self.settings_menu.add_command(label=self.texts.get("menu_colors", "Colors"), command=self._choose_colors)
        self.settings_menu.add_command(label=self.texts.get("menu_toggle_fullscreen", "Toggle Fullscreen"), command=self._toggle_fullscreen)
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
            "<T>": self._toggle_design,
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
        from .general_settings import show_general_settings
        show_general_settings(self.master, self.config, self.style, self.themes[self.current_theme_index])
        
    def _add_empty_project(self):
        from .project import Project
        name = simpledialog.askstring("Empty Project", "Name:")
        if not name:
            return
        p = Project(name=name)  # nur Name, keine Datei
        p.compile_a_selected = True
        self.projects.append(p)
        self._refresh_tree()
        self.status_var.set(f"Leeres Projekt '{name}' hinzugefügt.")

    def _open_debuginspector(self):
        # Wenn ein compile_*.log existiert, den neuesten nehmen
        logs = sorted(Path.cwd().glob("compile_*.log"), reverse=True)
        if not logs:
            messagebox.showinfo("Info", "Keine Logdatei gefunden.")
            return

        latest_log = logs[0]
        debuginspector(self.master, str(latest_log), self.projects, self.style, self.config)


    def _update_ui_texts(self) -> None:
        print("Updating UI texts...")

        # Fenstertitel
        self.master.title(self.texts["title"])

        # Sprache-Label
        #self.language_label.config(text=self.texts["language_label"])

        # About-Button
        #self.btn_about.config(text=self.texts["about_btn"])
        #CreateToolTip(self.btn_about, self.texts["tooltip_about_btn"])

        # Extensions-Button
        #self.btn_extensions.config(text=self.texts["extensions_btn"])
        #CreateToolTip(self.btn_extensions, self.texts["tooltip_extensions_btn"])

        # Modus-Radiobuttons
        #self.mode_a_btn.config(text=self.texts["mode_a"])
        #self.mode_b_btn.config(text=self.texts["mode_b"])
        #self.mode_c_btn.config(text=self.texts["mode_c"])
        #CreateToolTip(self.mode_a_btn, self.texts["tooltip_compile_mode"])
        #CreateToolTip(self.mode_b_btn, self.texts["tooltip_compile_mode"])
        #CreateToolTip(self.mode_c_btn, self.texts["tooltip_compile_mode"])

        # Treeview-Spaltenüberschriften
        self.tree.heading("A", text=self.texts["compile_a_col"])
        self.tree.heading("B", text=self.texts["compile_b_col"])
        self.tree.heading("C", text=self.texts["compile_c_col"])
        self.tree.heading("Name", text=self.texts["name_col"])
        self.tree.heading("Script", text=self.texts["script_col"])
        self.tree.heading("PyArmor", text="PyArmor")
        self.tree.heading("Cython", text="Cython")
        self.tree.heading("Nuitka", text="Nuitka")

        # Statusleiste
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
            messagebox.showwarning("Fehler", self.texts.get("error_no_entry", "Kein Eintrag ausgewählt."))
            return

        try:
            idx = int(sel[0].split("_")[1])
            proj = self.projects[idx]
        except (ValueError, IndexError):
            messagebox.showerror("Fehler", "Ungültige Projekt-ID.")
            return

        new_name = simpledialog.askstring(
            self.texts.get("rename_title", "Projekt umbenennen"),
            self.texts.get("rename_prompt", "Neuer Name:"),
            initialvalue=proj.name,
            parent=self.master
        )
        if new_name is None:
            return  # Abbruch
        new_name = new_name.strip()
        if not new_name:
            messagebox.showerror("Fehler", self.texts.get("rename_empty", "Bitte einen Namen eingeben."))
            return

        # Kollisionen automatisch vermeiden
        new_name = self._unique_name(new_name)

        old_name = proj.name
        proj.name = new_name
        self._refresh_tree()
        self.tree.selection_set(f"proj_{idx}")
        self.tree.see(f"proj_{idx}")

        try:
            self._save_current_file()
        except Exception:
            pass

        self.status_var.set(self.texts.get("status_renamed", "Umbenannt.").format(old=old_name, new=new_name))

        
    def _unique_name(self, base: str) -> str:
        existing = {p.name for p in self.projects}
        if base not in existing:
            return base
        i = 2
        while True:
            candidate = f"{base} {i}"
            if candidate not in existing:
                return candidate
            i += 1

    
    def _duplicate(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Error", self.texts.get("error_no_entry", "No entry selected."))
            return

        row_id = sel[0]
        if not row_id.startswith("proj_"):
            return

        try:
            idx = int(row_id.split("_")[1])
            original: Project = self.projects[idx]
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Ungültige Projekt-ID.")
            return

        # Tief kopieren
        try:
            new_p: Project = copy.deepcopy(original)
        except Exception:
            # Fallback: flacher Kopierer — falls deepcopy wegen exotischer Felder scheitert
            new_p = Project()
            for k, v in vars(original).items():
                setattr(new_p, k, copy.deepcopy(v) if isinstance(v, (dict, list, set, tuple)) else v)

        # Neuen Namen vergeben
        base_name = f"{original.name} (Kopie)"
        new_p.name = self._unique_name(base_name)

        # Optional: Checkboxen zurücksetzen/übernehmen (hier: übernehmen)
        # new_p.compile_a_selected = original.compile_a_selected
        # new_p.compile_b_selected = original.compile_b_selected
        # new_p.compile_c_selected = original.compile_c_selected

        # Direkt unter dem Original einfügen
        insert_at = idx + 1
        self.projects.insert(insert_at, new_p)

        # UI aktualisieren & Auswahl auf die Kopie setzen
        self._refresh_tree()
        self.tree.selection_set(f"proj_{insert_at}")
        self.tree.see(f"proj_{insert_at}")

        # Speichern (optional): aktuelle Datei überschreiben, wenn vorhanden
        try:
            self._save_current_file()
        except Exception:
            pass

        self.status_var.set(f"Projekt „{new_p.name}“ erstellt (Duplikat).")

    
    def _save_thread_count(self, *args):  # pylint: disable=unused-argument
        try:
            val = int(self.thread_count_var.get())
        except Exception:
            val = 1
        val = max(1, min(self.max_threads, val))
        if self.thread_count_var.get() != val:
            # falls Nutzer Text eingibt, normalisieren
            self.thread_count_var.set(val)
        self.config["thread_count"] = val
        save_config(self.config)
        # dezentes Feedback
        self.status_var.set(self.texts.get("status_threads_saved", "Threads: {n}").format(n=val))


    def _choose_colors(self):
        color_a = colorchooser.askcolor(title="Farbe für Modus A wählen", color=self.color_a)[1]
        if color_a:
            self.color_a = color_a
            self.config["color_a"] = color_a
        color_b = colorchooser.askcolor(title="Farbe für Modus B wählen", color=self.color_b)[1]
        if color_b:
            self.color_b = color_b
            self.config["color_b"] = color_b
        color_c = colorchooser.askcolor(title="Farbe für Modus C wählen", color=self.color_c)[1]
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
            key=lambda t: not (t[1].spec_file and t[1].spec_file.lower().endswith(".spec"))
        )
        existing_iids = set(self.tree.get_children())
        new_iids = set()

        last_type = None
        for idx, p in sorted_projects:
            if p is None:
                continue
            script_name = p.script or p.spec_file or ""
            is_spec = bool(p.spec_file and p.spec_file.lower().endswith(".spec"))
            typ = "spec" if is_spec else "py"

            # Trennzeile hinzufügen, wenn Typ wechselt
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

            pyarmor_status = "🛡" if p.use_pyarmor else ""
            nuitka_status  = "⚡" if p.use_nuitka else ""
            cython_status  = "🧩" if p.use_cython else ""

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

            # Checkboxen für Kompiliermodus A/B
            chk_a = "☑" if p.compile_a_selected else "☐"
            chk_b = "☑" if p.compile_b_selected else "☐"
            chk_c = "☑" if p.compile_c_selected else "☐"
            
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
            return  

        if row_id.startswith("proj_"):
            proj_index = int(row_id.split("_")[1])
        else:
            return

        p = self.projects[proj_index]

        if col == "#1":
            p.compile_a_selected = not p.compile_a_selected
        elif col == "#2":
            p.compile_b_selected = not p.compile_b_selected
        elif col == "#3":
            p.compile_c_selected = not p.compile_c_selected
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
            p = Project(script=path)  # Default to Python script for .py or other files

        if p is not None:
            p.compile_a_selected, p.compile_b_selected, p.compile_c_selected = True, False, False
            self.projects.append(p)
            self._refresh_tree()
            self.status_var.set(self.texts["status_project_added"].format(name=p.name))
        else:
            self.status_var.set("Projekt konnte nicht hinzugefügt werden (parse_spec_file gab None zurück)")
            

    def _edit(self) -> None:
        stop_event = threading.Event()
        animation_thread = threading.Thread(target=self.run_status_animation, args=(stop_event,), daemon=True)
        animation_thread.start()
    
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Error", self.texts["error_no_entry"])
            return

        row_id = sel[0]
        if not row_id.startswith("proj_"):
            return

        try:
            proj_index = int(row_id.split("_")[1])
            proj: Project = self.projects[proj_index]
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Ungültige Projekt-ID.")
            return

        if proj.spec_file and proj.spec_file.lower().endswith(".spec"):
            try:
                from .speceditor import SpecEditor
            except ImportError as err:
                messagebox.showerror(
                    "Import-Fehler",
                    f"SpecEditor-Modul konnte nicht geladen werden:\n{err}",
                )
                return

            editor = SpecEditor(self.master, proj, self.texts)
            if editor.show():
                self._refresh_tree()
                self._save_current_file()
                self.status_var.set(f"Spec-Projekt „{proj.name}“ aktualisiert.")
        else:
            editor = ProjectEditor(self.master, proj, self.texts, self)

            if editor.show():
                self._refresh_tree()
                self._save_current_file()  # <-- hier fehlte es bisher!
                self.status_var.set(self.texts["status_entry_edited"].format(name=proj.name))
        stop_event.set()
        
    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Error", self.texts["error_no_entry"])
            return
        row_id = sel[0]
        if not row_id.startswith("proj_"):
            return
        proj_index = int(row_id.split("_")[1])
        name = self.projects[proj_index].name
        del self.projects[proj_index]
        self._refresh_tree()
        self.status_var.set(f"Projekt {name} gelöscht.")

    def _clear(self):
        self.projects.clear()
        self._refresh_tree()
        self.status_var.set("Alle Projekte gelöscht.")

    def _change_language(self, *_):
        new_language = self.language_var.get()
        print(f"Selected language: {new_language}")
        if new_language not in LANGUAGES:
            print(f"Error: Language {new_language} not found in LANGUAGES")
            messagebox.showerror("Error", f"Language {new_language} not supported.")
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

    def _toggle_design(self):
        self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)
        selected_theme = self.themes[self.current_theme_index]
        selected_theme(self.style, self.master)
        self.config["theme"] = self.current_theme_index
        save_config(self.config)
        self.status_var.set(f"Theme gewechselt: {selected_theme.__name__}")
        self._update_tag_colors()
        self._refresh_tree()
        self._apply_progressbar_style()

    def _toggle_mode(self):
        #self.mode_btn.config(text=self._mode_label())
        self.status_var.set(f"Aktiver Kompilier-Modus: {self._mode_label()}")
        self.config["compile_mode"] = self.compile_mode_var.get()
        save_config(self.config)
        self._update_tag_colors() 
        self._update_headings()
        self._refresh_tree()
        self._apply_progressbar_style()

    def clear_work_dir(self):
        work_dir = Path(__file__).parent.parent
        work_dir = self.working_dir 
        files, folders = find_cleanup_targets(work_dir)
        targets = files + folders

        if not targets:
            messagebox.showinfo("Nothing to delete", "No matching files or folders found.")
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
        # nur Statusleiste, kein Popup
        self.master.after(0, lambda: self.set_status(f"{deleted_files} files/folders deleted.", hold_ms=3000))



    def _save(self):
        if not self.projects:
            self.status_var.set(self.texts["error_no_entry"])
            return

        f = filedialog.asksaveasfilename(
            defaultextension=".apyscript",
            filetypes=[("apyscript", "*.apyscript"), ("Spec File", "*.spec")],
            initialdir=str(self.current_apyscript.parent) if self.current_apyscript else os.getcwd()
        )
        if not f:
            return

        if f.lower().endswith(".apyscript"):
            save_projects(self.projects, f)
            self.status_var.set(f"Alle Projekte gespeichert: {f}")
        elif f.lower().endswith(".spec"):
            sel = self.tree.selection()
            if not sel:
                messagebox.showerror("Fehler", "Kein Projekt ausgewählt, um als .spec zu exportieren.")
                return
            row_id = sel[0]
            if not row_id.startswith("proj_"):
                messagebox.showerror("Fehler", "Nur Projekte können als .spec exportiert werden.")
                return
            idx = int(row_id.split("_")[1])
            save_projects([self.projects[idx]], f)
            self.status_var.set(f"{self.projects[idx].name} als .spec exportiert: {f}")
        else:
            messagebox.showerror("Fehler", "Unbekanntes Exportformat!")


    def _export_ini(self):
        ini_path = Path(__file__).parent / "extensions_path.ini"
        # User wählt nur den Zielordner, nicht den Dateinamen
        folder = filedialog.askdirectory(title="Zielordner wählen")
        if not folder:
            return
        target = Path(folder) / "extensions_path.ini"
        try:
            export_extensions_ini(ini_path, target)
            self.status_var.set(f"extensions_path.ini exportiert: {target}")
        except Exception as e:
            messagebox.showerror("Fehler beim Exportieren", str(e))


    def _load_ini(self):
        file_path = filedialog.askopenfilename(
            title="INI-Datei auswählen",
            filetypes=[("INI-Dateien", "*.ini"), ("Alle Dateien", "*.*")]
        )
        if not file_path:
            return
        target_file = Path(__file__).parent / "extensions_path.ini"
        try:
            load_extensions_ini(Path(file_path), target_file)
            self.status_var.set(f"INI-Datei {file_path} geladen und überschrieben.")
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))


    def update_treeview(self):
        self._refresh_tree()

    def _load(self):
        file = filedialog.askopenfilename(
            filetypes=[("apyscript", "*.apyscript")],
            initialdir=str(self.current_apyscript.parent) if self.current_apyscript else os.getcwd()
        )
        if not file:
            return
        if not file.lower().endswith(".apyscript"):
            messagebox.showerror("Fehler", "Nur .apyscript-Dateien sind erlaubt!")
            return
        try:
            self.projects = load_projects(file)
            self.current_apyscript = Path(file)
            # Korrigiere potenzielle inkonsistente Zustände
            for p in self.projects:
                if p.use_pyarmor and p.use_nuitka:
                    p.use_nuitka = False
            self._refresh_tree()
            self.status_var.set(f"{file} geladen.")
        except Exception as err:
            messagebox.showerror("Error", f"Laden fehlgeschlagen: {err}")

    def _auto_load(self):
        default_file = Path("myProject.apyscript")
        if default_file.is_file():
            try:
                self.projects = load_projects(default_file)
                self.current_apyscript = default_file
                # Korrigiere potenzielle inkonsistente Zustände
                for p in self.projects:
                    if p.use_pyarmor and p.use_nuitka:
                        p.use_nuitka = False  # Oder umgekehrt
                self._refresh_tree()
                self.status_var.set(f"{default_file} automatisch geladen.")
            except Exception as e:
                self.status_var.set(f"Fehler beim automatischen Laden von {default_file}: {e}")


    def _save_current_file(self):
        """Speichert Projekte in der zuletzt verwendeten .apyscript-Datei (wie STRG+S)."""
        if not self.projects:
            self.status_var.set(self.texts["error_no_entry"])
            return

        if not self.current_apyscript or not str(self.current_apyscript).lower().endswith(".apyscript"):
            # Wenn keine gültige Datei gesetzt → "Speichern unter..."
            self._save_as()
            return

        save_projects(self.projects, self.current_apyscript)
        self.status_var.set(f"{self.current_apyscript} gespeichert.")
        
        
    def _save_as(self):
        """Speichern unter... – fragt nach Dateiname."""
        if not self.projects:
            self.status_var.set(self.texts["error_no_entry"])
            return

        f = filedialog.asksaveasfilename(
            defaultextension=".apyscript",
            filetypes=[("apyscript", "*.apyscript"), ("Spec File", "*.spec")],
            initialdir=str(self.current_apyscript.parent) if self.current_apyscript else os.getcwd()  # <- hier ergänzen!
        )
        if not f:
            return

        # Speichern und merken!
        if f.lower().endswith(".apyscript"):
            save_projects(self.projects, f)
            self.current_apyscript = Path(f)
            self.status_var.set(f"Alle Projekte gespeichert: {f}")
        elif f.lower().endswith(".spec"):
            sel = self.tree.selection()
            if not sel:
                messagebox.showerror("Fehler", "Kein Projekt ausgewählt, um als .spec zu exportieren.")
                return
            row_id = sel[0]
            if not row_id.startswith("proj_"):
                messagebox.showerror("Fehler", "Nur Projekte können als .spec exportiert werden.")
                return
            idx = int(row_id.split("_")[1])
            save_projects([self.projects[idx]], f)
            self.status_var.set(f"{self.projects[idx].name} als .spec exportiert: {f}")
        else:
            messagebox.showerror("Fehler", "Unbekanntes Exportformat!")

                
    def run_status_animation(self, stop_event: threading.Event, interval: float = 0.15) -> None:
        idx = 0
        frames = ["⠁","⠃","⠇","⠧","⠷","⠿","⠷","⠧","⠇","⠃","⠁"]
        while not stop_event.is_set():
            now = time.time()
            with self._status_lock:
                # Nur animieren, wenn die Schutzzeit vorbei ist
                if now >= self._hold_until_ts:
                    base = self._last_user_status or self.texts.get("status_ready","Ready")
                    spinner = frames[idx % len(frames)]
                    # Nur anhängen, nicht überschreiben
                    self.status_var.set(f"{base}  {spinner}")
                # Falls noch Schutzzeit: nichts tun (User-Text bleibt stehen)
            idx += 1
            self.master.update_idletasks()
            time.sleep(interval)


    def compile_all(self):
        print("Start compilation...")
        stop_event = threading.Event()
        threading.Thread(target=self.run_status_animation, args=(stop_event,), daemon=True).start()

        # Fortschrittsbalken im GUI-Thread erzeugen
        prog = tk.DoubleVar(value=0)
        self._apply_progressbar_style()
        pb = ttk.Progressbar(self.main_frame, variable=prog, maximum=100, style=self.pb_style_name)
        pb.pack(fill="x", pady=5)


        def do_compile():
            try:
                mode = self.compile_mode_var.get()
                selected = [
                    p for p in self.projects
                    if (mode == "A" and p.compile_a_selected)
                    or (mode == "B" and p.compile_b_selected)
                    or (mode == "C" and p.compile_c_selected)
                ]
                
                if not selected:
                    self.master.after(0, lambda: self.set_status(self.texts["error_no_entry"], hold_ms=2500))
                    return
                
                if selected:
                    proj_name = selected[0].name.replace(" ", "_")
                    if len(selected) > 1:
                        proj_name = f"{proj_name}_and_{len(selected)-1}_more"
                else:
                    proj_name = "no_project"

                log_hdl = Path(f"compile_{proj_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.log").open("a", encoding="utf-8")

                log_hdl.write(f"Starting compilation at {datetime.now()}\n")
                log_hdl.flush()

                def upd_status(msg):
                    self.master.after(0, lambda: self.set_status(msg, hold_ms=2000))

                def upd_prog(cur, total):
                    prog.set((cur / total) * 100)

                
                compiler_mode = "pyinstaller" 

                if all(p.use_pyarmor and not p.use_nuitka and not p.use_cython for p in selected):
                    compiler_mode = "pyarmor"
                elif all(p.use_nuitka and not p.use_pyarmor and not p.use_cython for p in selected):
                    compiler_mode = "nuitka"
                elif all(p.use_cython and not p.use_pyarmor and not p.use_nuitka for p in selected):
                    compiler_mode = "cython"
                elif all(not p.use_pyarmor and not p.use_nuitka and not p.use_cython for p in selected):
                    compiler_mode = "pyinstaller"
                                    
                    
                print(f"[DEBUG] Selected compiler_mode: {compiler_mode}")
                log_hdl.write(f"Selected compiler_mode: {compiler_mode}\n")
                log_hdl.flush()

                errors = compile_projects(
                    selected,
                    thread_count=self.thread_count_var.get(),
                    log_file=log_hdl,
                    status_callback=lambda msg: self.master.after(0, lambda: upd_status(msg)),
                    progress_callback=lambda cur, total: self.master.after(0, lambda: upd_prog(cur, total)),
                    compiler=compiler_mode,
                    mode=mode,
                )

                if errors:
                    def show_debuginspector_only():
                        self.status_var.set("Kompilierung abgeschlossen (mit Fehlern).")
                        debuginspector(self.master, log_hdl.name, selected, self.style, self.config)
                        self._refresh_tree()
                    self.master.after(0, show_debuginspector_only)
                else:
                    self.master.after(0, lambda: (
                        self.status_var.set("Successfully Finished !!! 😊 "),
                        self.master.after(2000, lambda: self.status_var.set(self.texts["status_ready"]))
                    ))

            except Exception as e:
                def _on_fail():
                    self.status_var.set("Kompilierung fehlgeschlagen.")
                    # ins Log schreiben (falls vorhanden)
                    try:
                        with open(log_hdl.name, "a", encoding="utf-8") as _hdl:
                            _hdl.write(f"Compilation failed: {e}\n")
                    except Exception:
                        pass
                    # Popup ENTFERNT – direkt Inspector öffnen, wenn es ein Log gibt
                    if 'log_hdl' in locals():
                        debuginspector(self.master, log_hdl.name, [], self.style, self.config)
                self.master.after(0, _on_fail)


            finally:
                stop_event.set()
                self.master.after(0, pb.destroy)
                print(f"End compilation...")
                
        threading.Thread(target=do_compile, daemon=True).start()

    def _show_extensions_popup(self):
        import configparser
        from tkinter import messagebox, filedialog
        import tkinter as tk
        from tkinter import ttk
        from pathlib import Path

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

        # White-on-dark Theme für Labels und Buttons

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
                messagebox.showinfo("Toolset is full", "No more free tools.")
                return

            # Auswahl per Combobox in eigenem Dialogfenster
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
            self.status_var.set("INI gespeichert.")
            popup.destroy()

        ttk.Button(frame, text="Save", command=save_and_close, style="White.TButton").pack(pady=(6, 0), fill="x")

        popup.bind("<Escape>", lambda e: popup.destroy())
        popup.focus_set()
        popup.grab_set()
        popup.wait_window()

