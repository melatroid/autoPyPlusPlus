from __future__ import annotations  # Enables postponed evaluation of type annotations for forward references

import os  # For interacting with the operating system (e.g., file/directory handling)

import tkinter as tk  # Tkinter: main module for creating GUIs
from tkinter import ttk, filedialog, messagebox, colorchooser  # Tkinter modules for advanced GUI widgets, file dialogs, message boxes, and color pickers
from datetime import datetime  # For working with date and time

from typing import Optional  # For type hinting optional variables
from pathlib import Path  # For object-oriented filesystem paths


import threading  # For running code in separate threads (concurrent tasks)
import time  # For time-related functions (e.g., delays, measuring time)

#OWN MODULES

from .help import show_main_helper

from .about import show_about_dialog

from .debuginspector import debuginspector

from .project import Project

from .config import load_config, save_config

from .tooltip import CreateToolTip

from .parse_spec_file import parse_spec_file

from .compiler import compile_projects

from .language import LANGUAGES

from .projecteditor import ProjectEditor

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

        # -------- Sprache / Texte -------------------------------------
        self.current_language = self.config.get("language", "de")
        self.texts = LANGUAGES[self.current_language]
        self._fallback_texts()
        self.compile_mode_var = tk.StringVar(
            value=self.config.get("compile_mode", "A")
        )

        # -------- Fenstergrunddaten -----------------------------------
        master.title(self.texts["title"])
        master.geometry("1400x500")
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

        default_theme = 0 if self.config.get("dark_mode", True) else 1
        self.current_theme_index = self.config.get("theme", default_theme) % len(self.themes)
        self.themes[self.current_theme_index](self.style, master)

        # -------- Farben ----------------------------------------------
        self.color_a: str = self.config.get("color_a", "#299438")
        self.color_b: str = self.config.get("color_b", "#c85c00")
        self.color_c: str = self.config.get("color_c", "#c85c00")
        self.default_bg: str = "#ffffff"

        # -------- Thread-Anzahl (wird automatisch gespeichert) --------
        self.thread_count_var = tk.IntVar(value=self.config.get("thread_count", 1))
        self.thread_count_var.trace_add("write", self._save_thread_count)

        # -------- UI aufbauen & Projekte laden ------------------------
        self._build_ui()
        self._auto_load()
        self._register_hotkeys()
    # ------------------------- Hilfsmethoden --------------------------

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


    # ----------------------------- UI --------------------------------

    def _build_ui(self) -> None:
        if not hasattr(self, "main_frame"):
            # Nur beim ersten Aufruf die GUI erstellen
            for w in self.master.winfo_children():
                if isinstance(w, tk.Toplevel):
                    continue  # Inspector-Fenster nicht schließen!
                w.destroy()
            root = ttk.Frame(self.master, padding=10)
            root.pack(fill="both", expand=True)
            self.main_frame = root
            # Kopfzeile
            self.top_frame = ttk.Frame(root)
            self.top_frame.pack(fill="x", pady=5)

            # Sprache-Label, Combobox und INI-Button in einem linken Unter-Frame
            left_frame = ttk.Frame(self.top_frame)
            left_frame.pack(side="left", padx=5)

            self.language_label = ttk.Label(left_frame, text=self.texts["language_label"])
            self.language_label.pack(side="left", padx=5)
            
            self.language_var = tk.StringVar(value=self.current_language)
            self.language_cmb = ttk.Combobox(
                left_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()),
                state="readonly", width=10
            )
            self.language_cmb.pack(side="left", padx=5)
            self.language_cmb.bind("<<ComboboxSelected>>", self._change_language)

            self.btn_extensions = ttk.Button(left_frame, text=self.texts["extensions_btn"], command=self._show_extensions_popup)
            self.btn_extensions.pack(side="left", padx=5)
            CreateToolTip(self.btn_extensions, self.texts["tooltip_extensions_btn"])
            

            # About button
            self.btn_about = ttk.Button(
                left_frame,
                text=self.texts["about_btn"],
                command=lambda: show_about_dialog(self.master, self.style, self.themes[self.current_theme_index])
            )
            self.btn_about.pack(side="left", padx=5)
            CreateToolTip(self.btn_about, self.texts["tooltip_about_btn"])



            # Help button
            self.btn_help = ttk.Button(
                left_frame,
                text="ℹ️ Help",
                command=lambda: show_main_helper(self.master)
            )
            self.btn_help.pack(side="left", padx=5)
            CreateToolTip(self.btn_help, "Zeigt eine Hilfeseite für das Hauptfenster.")

            # Design- und Colors-Buttons rechtsbündig
            ttk.Button(self.top_frame, text="🎨 Colors", command=self._choose_colors).pack(side="right", padx=5)
            ttk.Button(self.top_frame, text="🖌️ Design", command=self._toggle_design).pack(side="right", padx=5)

            # Button-Leiste
            self.bar = ttk.Frame(root)
            self.bar.pack(fill="x", pady=5)

            # Threads Spinbox (keep on the right)
            ttk.Label(self.bar, text="::Threads").pack(side="right", padx=5)
            ttk.Spinbox(
                self.bar, from_=1, to=os.cpu_count() or 4, width=5,
                textvariable=self.thread_count_var
            ).pack(side="right")

            def _btn(txt_key, cmd, tip_key):
                b = ttk.Button(self.bar, text=self.texts[txt_key], command=cmd)
                b.pack(side="left", padx=5)  # All buttons on the left
                CreateToolTip(b, self.texts[tip_key])
                return b

            # Pack all buttons on the left in the desired order
            self.add_btn = _btn("add_btn", self._add, "tooltip_add_btn")
            self.edit_btn = _btn("edit_btn", self._edit, "tooltip_edit_btn")  # Added Edit button
            self.delete_btn = _btn("delete_btn", self._delete, "tooltip_delete_btn")  # Added Delete button

            ttk.Label(self.bar, text="|").pack(side="left", padx=5)
            self.save_btn       = _btn("save_btn",       self._save_current_file,"tooltip_save_btn")
            self.save_as_btn    = _btn("save_as_btn",    self._save_as,          "tooltip_save_as_btn")
            self.load_btn       = _btn("load_btn",       self._load,             "tooltip_load_btn")
            self.clear_btn      = _btn("clear_btn",      self._clear,            "tooltip_clear_btn")

            ttk.Label(self.bar, text="|").pack(side="left", padx=5)
            
            self.debug_btn = _btn("debug_btn", self._open_debuginspector, "tooltip_debug_btn")
            self.compile_all_btn = _btn("compile_all_btn", self.compile_all, "tooltip_compile_all_btn")
            self.clear_work_dir_btn = _btn("clear_work_dir_btn", self.clear_work_dir, "tooltip_clear_work_dir_btn")

            # Mode Checkbutton (keep on the right)
            self.mode_a_btn = ttk.Radiobutton(self.bar, text=self.texts["mode_a"], variable=self.compile_mode_var, value="A", command=self._toggle_mode)
            self.mode_b_btn = ttk.Radiobutton(self.bar, text=self.texts["mode_b"], variable=self.compile_mode_var, value="B", command=self._toggle_mode)
            self.mode_c_btn = ttk.Radiobutton(self.bar, text=self.texts["mode_c"], variable=self.compile_mode_var, value="C", command=self._toggle_mode)

            self.mode_c_btn.pack(side="right", padx=2)
            self.mode_b_btn.pack(side="right", padx=2)
            self.mode_a_btn.pack(side="right", padx=2)


            CreateToolTip(self.mode_a_btn, self.texts["tooltip_compile_mode"])
            CreateToolTip(self.mode_b_btn, self.texts["tooltip_compile_mode"])
            CreateToolTip(self.mode_c_btn, self.texts["tooltip_compile_mode"])
            #self.mode_btn.pack(side="right", padx=5)
            #CreateToolTip(self.mode_btn, self.texts["tooltip_compile_mode"])

            # Treeview with swapped columns (PyArmor before Script)
            self.tree = ttk.Treeview(
                self.main_frame,
                columns=("A", "B", "C", "Name", "PyArmor", "Nuitka", "Cython", "Script"),
                show="headings"
            )


            self.tree.heading("Nuitka", text="Nuitka", anchor="center")
            self.tree.column("Nuitka", width=80, anchor="center", stretch=False)

            self.tree.heading("PyArmor", text="PyArmor", anchor="center")
            self.tree.column("PyArmor", width=80, anchor="center", stretch=False)

            self.tree.heading("Cython", text="Cython", anchor="center")
            self.tree.column("Cython", width=80, anchor="center", stretch=False)

            self.tree.heading("A", text=self.texts["compile_a_col"])
            self.tree.heading("B", text=self.texts["compile_b_col"])
            self.tree.heading("C", text=self.texts["compile_c_col"])

            
            self.tree.heading("Name", text=self.texts["name_col"], anchor="center")
            self.tree.heading("Script", text=self.texts["script_col"], anchor="center")
            
            self.tree.column("A", width=90, anchor="center", stretch=False)
            self.tree.column("B", width=90, anchor="center", stretch=False)
            self.tree.column("C", width=90, anchor="center", stretch=False)
            
            
            self.tree.column("Name", width=120, anchor="center",stretch=False)
            self.tree.column("Script", width=600, anchor="center",stretch=False)
            
            
            self._update_tag_colors()
            self.tree.pack(fill="both", expand=True, pady=(5, 10))
            self.tree.bind("<Button-1>", self._toggle_cell)
            #self.tree.tag_configure("mode_a", background=self.color_a, foreground="white")
            #self.tree.tag_configure("mode_b", background=self.color_b, foreground="white")
            #self.tree.tag_configure("divider", background="#41578e", font=("", 10, "bold"))
            self._update_tag_colors()
            self.tree.pack(fill="both", expand=True, pady=(5, 10))
            self.tree.bind("<Button-1>", self._toggle_cell)
            self.tree.tag_configure("divider", background="#41578e", font=("", 10, "bold"))
            
            # Statuszeile
            self.status_var = tk.StringVar(value=self.texts["status_ready"])
            self.status_label = ttk.Label(
                self.main_frame,
                textvariable=self.status_var,
                relief="sunken",
                anchor="w",
                padding=5,
                font=("Helvetica", 14)
            )
            self.status_label.pack(fill="x")
        else:
            # Aktualisiere nur Texte
            self._update_ui_texts()

        # Initiales Rendern
        self._update_headings()
        self._refresh_tree()
        
    def _update_tag_colors(self):
        self.tree.tag_configure("mode_a", background=self.color_a, foreground="white")
        self.tree.tag_configure("mode_b", background=self.color_b, foreground="white")
        self.tree.tag_configure("mode_c", background=self.color_c, foreground="white")


    def _toggle_fullscreen(self):
        is_fullscreen = self.master.attributes("-fullscreen")
        self.master.attributes("-fullscreen", not is_fullscreen)

    def _register_hotkeys(self):
        hotkeys = {
            "<C>": self.compile_all,
            "<A>": self._add,
            "<D>": self._delete,
            "<Y>": self._toggle_mode,
            "<L>": self._load,
            "<S>": self._save,
            "<E>": self.clear_work_dir,
            "<T>": self._toggle_design,
            "<Shift-Q>": self.master.quit,
            "<F>": self._toggle_fullscreen,
            "<Return>": self._edit,
        }
        register_hotkeys(self.master, hotkeys)


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
        self.language_label.config(text=self.texts["language_label"])

        # About-Button
        self.btn_about.config(text=self.texts["about_btn"])
        CreateToolTip(self.btn_about, self.texts["tooltip_about_btn"])

        # Extensions-Button
        self.btn_extensions.config(text=self.texts["extensions_btn"])
        CreateToolTip(self.btn_extensions, self.texts["tooltip_extensions_btn"])

        # Modus-Radiobuttons
        self.mode_a_btn.config(text=self.texts["mode_a"])
        self.mode_b_btn.config(text=self.texts["mode_b"])
        self.mode_c_btn.config(text=self.texts["mode_c"])
        CreateToolTip(self.mode_a_btn, self.texts["tooltip_compile_mode"])
        CreateToolTip(self.mode_b_btn, self.texts["tooltip_compile_mode"])
        CreateToolTip(self.mode_c_btn, self.texts["tooltip_compile_mode"])

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
        button_mapping = [
            ("add_btn", "tooltip_add_btn"),
            ("edit_btn", "tooltip_edit_btn"),
            ("delete_btn", "tooltip_delete_btn"),
            ("save_btn", "tooltip_save_btn"),
            ("save_as_btn", "tooltip_save_as_btn"),
            ("load_btn", "tooltip_load_btn"),
            ("clear_btn", "tooltip_clear_btn"),
        ]

        # Hole alle Buttons in der linken Leiste (side="left")
        left_buttons = [
            w for w in self.bar.winfo_children()
            if isinstance(w, ttk.Button) and w.pack_info()["side"] == "left"
        ]

        for i, (key, tooltip_key) in enumerate(button_mapping):
            if i < len(left_buttons):
                left_buttons[i].config(text=self.texts[key])
                CreateToolTip(left_buttons[i], self.texts[tooltip_key])
            else:
                print(f"Warning: No button found for index {i} (key: {key})")

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
        
    
    def _save_thread_count(self, *args):  # pylint: disable=unused-argument
        self.config["thread_count"] = self.thread_count_var.get()
        save_config(self.config)

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
                if divider_iid not in existing_iids:
                    self.tree.insert(
                        "", "end", iid=divider_iid,
                        values=("", "", "", "", "", "", "", divider_text),
                        tags=("divider",)
                    )

                last_type = typ

            # PyArmor-Status
            pyarmor_status = "✔" if p.use_pyarmor else ""
            # Nuitka-Status
            nuitka_status = "✔" if p.use_nuitka else ""
            # cython-Status
            cython_status = "✔" if p.use_cython else ""

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

            values = (chk_a, chk_b, chk_c, p.name, pyarmor_status, nuitka_status, cython_status, script_name)


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
            return  # Ignoriere Klicks auf Trennzeilen

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

    def _toggle_mode(self):
        #self.mode_btn.config(text=self._mode_label())
        self.status_var.set(f"Aktiver Kompilier-Modus: {self._mode_label()}")
        self.config["compile_mode"] = self.compile_mode_var.get()
        save_config(self.config)
        self._update_tag_colors()  # <---- WICHTIG!
        self._update_headings()
        self._refresh_tree()

    def clear_work_dir(self):
        work_dir = Path.cwd()
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

        # Jetzt in Thread auslagern, wie gehabt:
        threading.Thread(target=self._delete_files, args=(targets,)).start()

    def _delete_files(self, targets):
        deleted_files = delete_files_and_dirs(targets)
        self.status_var.set(f"{deleted_files} files/folders deleted in working directory.")
        self.master.after(0, lambda: messagebox.showinfo("Done", f"{deleted_files} files/folders deleted."))


    def _save(self):
        if not self.projects:
            self.status_var.set(self.texts["error_no_entry"])
            return

        f = filedialog.asksaveasfilename(
            defaultextension=".apyscript",
            filetypes=[("apyscript", "*.apyscript"), ("Spec File", "*.spec")]
        )
        if not f:
            return

        # NEU: save_projects aus core.py
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
        file = filedialog.askopenfilename(filetypes=[("apyscript", "*.apyscript")])
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
                    p.use_nuitka = False  # Oder umgekehrt, je nach Priorität
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
            filetypes=[("apyscript", "*.apyscript"), ("Spec File", "*.spec")]
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
                
            
    def run_status_animation(self, stop_event: threading.Event, message: str = "Work...", interval: float = 0.2) -> None:
        idx = 0
        chars = ["⠁", "⠃", "⠇", "⠧", "⠷", "⠿", "⠷", "⠧", "⠇", "⠃", "⠁", " "]
        while not stop_event.is_set():
            #current_status = self.status_var.get()
            # Animation nur anzeigen, wenn der Status derzeit "bereit" oder leer ist
            self.status_var.set(chars[idx % len(chars)])
            idx += 1
            self.master.update_idletasks()
            time.sleep(interval)
        # Animation stoppen – Status nur zurücksetzen, wenn er nicht währenddessen geändert wurde
        final_status = self.status_var.get()
        if final_status in chars:
            self.master.after(0, lambda: self.status_var.set(self.texts["status_ready"]))

    def compile_all(self):
        print(f"Start compilation...")
        stop_event = threading.Event()
        animation_thread = threading.Thread(target=self.run_status_animation, args=(stop_event,), daemon=True)
        animation_thread.start()

        # Fortschrittsbalken im GUI-Thread erzeugen
        prog = tk.DoubleVar(value=0)
        pb = ttk.Progressbar(self.main_frame, variable=prog, maximum=100)
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
                    self.master.after(0, lambda: messagebox.showwarning("Error", self.texts["error_no_entry"]))
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
                    self.status_var.set(msg)

                def upd_prog(cur, total):
                    prog.set((cur / total) * 100)

                
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
                    def show_error_and_debug():
                        self.status_var.set("Kompilierung abgeschlossen (mit Fehlern).")
                        messagebox.showerror("Error", f"Kompilierung mit Fehlern: {', '.join(errors)}")
                        debuginspector(self.master, log_hdl.name, selected, self.style, self.config)
                        self._refresh_tree()  # Refresh tree after debug changes

                    self.master.after(0, show_error_and_debug)
                else:
                    self.master.after(0, lambda: (
                        self.status_var.set("Successfully Finished !!! 😊 "),
                        self.master.after(2000, lambda: self.status_var.set(self.texts["status_ready"]))
                    ))

            except Exception as e:
                self.master.after(0, lambda: (
                    self.status_var.set("Kompilierung fehlgeschlagen."),
                    messagebox.showerror("Error", f"Kompilierung fehlgeschlagen: {e}")
                ))
                with open(log_hdl.name, "a", encoding="utf-8") as log_hdl:
                    log_hdl.write(f"Compilation failed: {e}\n")
            finally:
                stop_event.set()
                self.master.after(0, pb.destroy)
                print(f"End compilation...")

            if Path(log_hdl.name).is_file() and Path(log_hdl.name).stat().st_size > 0:
                self.master.after(0, lambda: debuginspector(self.master, log_hdl.name, selected, self.style, self.config))
                self._refresh_tree()  # Refresh tree after debug changes

        threading.Thread(target=do_compile, daemon=True).start()

    def _show_extensions_popup(self):
        import configparser
        from tkinter import messagebox, filedialog
        import tkinter as tk
        from tkinter import ttk
        from pathlib import Path

        KNOWN_TOOLS = [
            "pyinstaller", "pyarmor", "nuitka", "cython",
            "cpp", "gcc", "msvc", "tcl_base"
        ]

        ini_file = Path(__file__).parent / "extensions_path.ini"
        cfg = configparser.ConfigParser()
        cfg.optionxform = str  # Groß-/Kleinschreibung bewahren
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
                cfg["paths"][k] = var.get()
            with open(ini_file, "w", encoding="utf-8") as f:
                cfg.write(f)
            self.status_var.set("INI gespeichert.")
            popup.destroy()

        ttk.Button(frame, text="Save", command=save_and_close, style="White.TButton").pack(pady=(6, 0), fill="x")

        popup.bind("<Escape>", lambda e: popup.destroy())
        popup.focus_set()
        popup.grab_set()
        popup.wait_window()

