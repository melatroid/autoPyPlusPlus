import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import re
import json
from tkinter import Text

class ApyEditor:
    def __init__(self, master: tk.Tk, apyscript_file: str = "", style=None):
        self.master = master
        self.apyscript_file = apyscript_file or ""
        self.saved = False
        self.style = style or ttk.Style()
        # KEYWORDS-LISTE nur einmal pflegen!
        self.json_keywords = [
            "script", "display_script", "name", "compile_selected", "compile_a_selected",
            "compile_b_selected", "compile_c_selected", "pyinstaller_path", "pyarmor_path",
            "nuitka_path", "cython_path", "icon", "add_data", "hidden_imports", "version",
            "output", "onefile", "console", "upx", "noupx", "debug", "clean", "strip",
            "runtime_hook", "splash", "spec_file", "options", "use_pyarmor", "use_nuitka",
            "no_runtime_key", "exclude_tcl", "include_pyarmor_runtime", "pyarmor_command",
            "pyarmor_options", "pyarmor_obf_code", "pyarmor_mix_str", "pyarmor_private",
            "pyarmor_restrict", "pyarmor_assert_import", "pyarmor_assert_call",
            "pyarmor_platform", "pyarmor_pack", "pyarmor_expired", "pyarmor_bind_device",
            "pyarmor_runtime_dir", "nuitka_tkinter_plugin", "nuitka_extra_opts",
            "nuitka_standalone", "nuitka_onefile", "nuitka_output_dir", "nuitka_follow_imports",
            "nuitka_follow_stdlib", "nuitka_plugins", "nuitka_show_progress", "nuitka_lto",
            "nuitka_jobs", "nuitka_show_memory", "nuitka_show_scons", "nuitka_windows_uac_admin",
            "nuitka_windows_icon", "nuitka_windows_splash", "use_cython", "cython_build_with_setup",
            "cython_target_type", "cython_boundscheck", "cython_wraparound", "cython_nonecheck",
            "cython_cdivision", "cython_language_level", "cython_initializedcheck",
            "cython_output_dir", "cython_keep_pyx", "cython_language", "cython_profile",
            "cython_linemap", "cython_gdb", "cython_embedsignature", "cython_cplus_exceptions",
            "cython_cpp_locals", "cython_directives", "cython_annotate", "cython_include_dirs",
            "cython_compile_time_env", "additional_files", "use_cpp", "cpp_output_file",
            "use_msvc", "cpp_filename", "cpp_windowed", "cpp_compiler_path", "cpp_compiler_flags",
            "cpp_linker_flags", "cpp_include_dirs", "cpp_lib_dirs", "cpp_libraries",
            "cpp_defines", "cpp_output_dir", "cpp_build_type", "cpp_compile_files",
            "cpp_target_type", "cpp_target_platform", "pytest_path", "use_pytest",
            "use_pytest_standalone", "test_file", "test_dir", "pytest_verbose", "pytest_quiet",
            "pytest_maxfail", "pytest_marker", "pytest_keyword", "pytest_disable_warnings",
            "pytest_tb", "pytest_durations", "pytest_capture", "pytest_html", "pytest_lf",
            "pytest_ff", "pytest_args", "use_sphinx", "use_sphinx_standalone", "sphinx_source",
            "sphinx_build", "sphinx_build_path", "sphinx_builder", "sphinx_conf_path",
            "sphinx_doctrees", "sphinx_parallel", "sphinx_warning_is_error", "sphinx_quiet",
            "sphinx_verbose", "sphinx_very_verbose", "sphinx_keep_going", "sphinx_tags",
            "sphinx_define", "sphinx_new_build", "sphinx_all_files", "sphinx_logfile",
            "sphinx_nitpicky", "sphinx_color", "sphinx_no_color", "sphinx_args", "pyarmor_dist_dir"
        ]

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("Apyscript Editor")
        self.win.geometry("1200x600")
        self.win.transient(self.master)
        self.win.grab_set()
        self.win.minsize(1200, 600)

        # Haupt-Frame mit Padding
        form = ttk.Frame(self.win, padding=10)
        form.pack(fill="both", expand=True)

        # Statusleiste
        self.status_var = tk.StringVar(value="Bereit")
        status_bar = ttk.Label(form, textvariable=self.status_var, anchor="w", padding=5, background="#f0f0f0")
        status_bar.pack(side="bottom", fill="x")

        # Menü-Buttons für Load/Save Apyscript
        menu_frame = ttk.Frame(form)
        menu_frame.pack(fill="x", padx=10, pady=(0,5))
        ttk.Button(menu_frame, text="Load Apyscript", command=self._menu_load_apyscript).pack(side="left", padx=5)
        ttk.Button(menu_frame, text="Save Apyscript", command=self._menu_save_apyscript).pack(side="left", padx=5)
        # >>> Search/Replace-Button hinzufügen <<<
        ttk.Button(menu_frame, text="Search/Replace Key...", command=self._search_replace_dialog).pack(side="left", padx=5)

        # Feld für Apyscript-Datei
        file_frame = ttk.Frame(form)
        file_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(file_frame, text="Apyscript file:").pack(side="left", padx=5)
        self.e_file = ttk.Entry(file_frame, width=50, font=("Segoe UI", 10))
        self.e_file.pack(side="left", fill="x", expand=True, padx=5)
        self.e_file.insert(0, self.apyscript_file)
    

        # Frame für Zeilennummern und Textfeld
        text_frame = ttk.Frame(form)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Label(text_frame, text="Apyscript content:").pack(anchor="nw", padx=0, pady=5)

        # Zeilennummern
        self.line_numbers = Text(text_frame, width=4, padx=3, takefocus=0, border=0, background="#2b2b2b", foreground="#888888", font=("Consolas", 12))
        self.line_numbers.pack(side="left", fill="y")
        self.line_numbers.config(state="disabled")

        # Textfeld für Datei-Inhalt
        self.txt_content = scrolledtext.ScrolledText(
            text_frame, width=80, height=25, font=("Consolas", 12), wrap="word",
            bg="#2b2b2b", fg="#ffffff", insertbackground="white", undo=True
        )
        self.txt_content.pack(side="left", fill="both", expand=True)

        # Kontextmenü
        self.context_menu = tk.Menu(self.txt_content, tearoff=0)
        self.context_menu.add_command(label="Copy", command=lambda: self.txt_content.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Paste", command=lambda: self.txt_content.event_generate("<<Paste>>"))
        self.context_menu.add_command(label="Cutout", command=lambda: self.txt_content.event_generate("<<Cut>>"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Choose all", command=lambda: self.txt_content.event_generate("<<SelectAll>>"))
        self.txt_content.bind("<Button-3>", self._show_context_menu)

        # Syntax-Highlighting und Zeilennummern aktualisieren
        self._init_syntax_highlighting()
        self._update_line_numbers()

        # Initial: Inhalt laden
        if self.apyscript_file and self._is_apyscript(self.apyscript_file):
            self._load_content(self.apyscript_file)
            self._highlight_all_lines()

        # Buttons (unten)
        btn_frame = ttk.Frame(form)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side="right", padx=10)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="right", padx=10)

        # Flexible Größenänderung
        form.columnconfigure(0, weight=1)
        form.rowconfigure(1, weight=1)

        self.master.wait_window(self.win)
        return self.saved

    def _show_context_menu(self, event):
        """Zeigt das Kontextmenü bei Rechtsklick."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _update_line_numbers(self, event=None):
        """Aktualisiert die Zeilennummern basierend auf dem Textinhalt."""
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", tk.END)
        line_count = int(self.txt_content.index("end-1c").split(".")[0])
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert("1.0", line_numbers)
        self.line_numbers.config(state="disabled")

    def _sync_scroll(self, *args):
        """Synchronisiert das Scrollen der Zeilennummern mit dem Text-Widget."""
        self.line_numbers.yview_moveto(args[0])

    def _init_syntax_highlighting(self):
        """JSON-spezifisches Syntax-Highlighting für Schlüsselwörter, Strings, Pfade, Booleans, Null und Zahlen."""
        self.txt_content.tag_configure("keyword", foreground="#ff79c6")  # Rosa für JSON-Schlüssel
        self.txt_content.tag_configure("string", foreground="#f1fa8c")   # Gelb für Strings
        self.txt_content.tag_configure("path", foreground="#8be9fd")     # Cyan für Pfade
        self.txt_content.tag_configure("boolean", foreground="#bd93f9")  # Lila für true/false
        self.txt_content.tag_configure("null", foreground="#ff5555")     # Rot für null
        self.txt_content.tag_configure("number", foreground="#50fa7b")   # Grün für Zahlen

        # Syntax-Highlighting für aktuelle Zeile
        self.txt_content.bind("<KeyRelease>", self.highlight_current_line)
        for key in ("<Up>", "<Down>", "<Return>", "<Tab>", "<BackSpace>", "<<Paste>>"):
            self.txt_content.bind(key, self.highlight_current_line)
        self.txt_content.bind("<MouseWheel>", lambda e: [self._update_line_numbers(), self.line_numbers.yview_scroll(int(-e.delta/120), "units")])
        self.txt_content.bind("<Button-4>", lambda e: [self._update_line_numbers(), self.line_numbers.yview_scroll(-1, "units")])
        self.txt_content.bind("<Button-5>", lambda e: [self._update_line_numbers(), self.line_numbers.yview_scroll(1, "units")])
        # Scrollbar-Sync
        self.txt_content.config(yscrollcommand=self._sync_scroll)

    def highlight_current_line(self, event=None):
        try:
            # Zeilennummer herausfinden
            cursor_index = self.txt_content.index("insert")
            line_index = cursor_index.split('.')[0]
            start = f"{line_index}.0"
            end = f"{line_index}.end"
            line_text = self.txt_content.get(start, end)

            # Vorherige Tags in dieser Zeile löschen
            for tag in ("keyword", "string", "path", "boolean", "null", "number"):
                self.txt_content.tag_remove(tag, start, end)

            # Keywords (Key)
            for word in self.json_keywords:
                pattern = rf'("{word}")\s*:'
                for match in re.finditer(pattern, line_text):
                    s, e = match.start(1), match.end(1)
                    self.txt_content.tag_add("keyword", f"{line_index}.{s}", f"{line_index}.{e}")

            # Strings
            string_pattern = r'"(?:\\.|[^"\\])*"'
            for match in re.finditer(string_pattern, line_text):
                s, e = match.start(), match.end()
                self.txt_content.tag_add("string", f"{line_index}.{s}", f"{line_index}.{e}")

            # Pfade
            path_pattern = r'"(?:[A-Za-z]:[\\\/][^"]*|[\\\/][^"]*)"'
            for match in re.finditer(path_pattern, line_text):
                s, e = match.start(), match.end()
                self.txt_content.tag_add("path", f"{line_index}.{s}", f"{line_index}.{e}")

            # Booleans (true/false) und Null
            for word, tag in [("true", "boolean"), ("false", "boolean"), ("null", "null")]:
                for match in re.finditer(rf'\b{word}\b', line_text):
                    s, e = match.start(), match.end()
                    # Sicherstellen, dass das Wort nicht im String ist
                    ranges = self.txt_content.tag_ranges("string")
                    in_string = False
                    for i in range(0, len(ranges), 2):
                        if f"{line_index}.{s}" >= str(ranges[i]) and f"{line_index}.{e}" <= str(ranges[i+1]):
                            in_string = True
                            break
                    if not in_string:
                        self.txt_content.tag_add(tag, f"{line_index}.{s}", f"{line_index}.{e}")

            # Zahlen (negativ, Dezimal, Exponential)
            number_pattern = r'\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b'
            for match in re.finditer(number_pattern, line_text):
                s, e = match.start(), match.end()
                # Nicht in Strings highlighten
                ranges = self.txt_content.tag_ranges("string")
                in_string = False
                for i in range(0, len(ranges), 2):
                    if f"{line_index}.{s}" >= str(ranges[i]) and f"{line_index}.{e}" <= str(ranges[i+1]):
                        in_string = True
                        break
                if not in_string:
                    self.txt_content.tag_add("number", f"{line_index}.{s}", f"{line_index}.{e}")

            self._update_line_numbers()
            self._validate_json()
        except Exception as e:
            self.status_var.set(f"Highlighting-Fehler: {e}")

    def _highlight_all_lines(self):
        line_count = int(self.txt_content.index("end-1c").split(".")[0])
        for i in range(1, line_count + 1):
            cursor_backup = self.txt_content.index("insert")
            self.txt_content.mark_set("insert", f"{i}.0")
            self.highlight_current_line()
            self.txt_content.mark_set("insert", cursor_backup)

    def _choose_file(self):
        path = filedialog.askopenfilename(
            title="Choose .apyscript file...",
            filetypes=[("Apyscript files", "*.apyscript")]
        )
        if path:
            self.e_file.delete(0, tk.END)
            self.e_file.insert(0, path)
            self._load_content(path)
            self.apyscript_file = path
            self.status_var.set(f"Datei geladen: {path}")
            self._highlight_all_lines()

    def _is_apyscript(self, filename):
        return str(filename).lower().endswith(".apyscript")

    def _load_content(self, filepath):
        """Lädt den Inhalt der gewählten .apyscript-Datei ins Textfeld."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.txt_content.delete("1.0", tk.END)
            # JSON formatieren für bessere Lesbarkeit
            try:
                json_content = json.loads(content)
                formatted_content = json.dumps(json_content, indent=2)
                self.txt_content.insert("1.0", formatted_content)
            except json.JSONDecodeError:
                self.txt_content.insert("1.0", content)  # Fallback, wenn kein gültiges JSON
            self.status_var.set("Inhalt erfolgreich geladen")
            self._update_line_numbers()
        except Exception as e:
            self.txt_content.delete("1.0", tk.END)
            self.txt_content.insert("1.0", f"Fehler beim Laden: {e}")
            self.status_var.set(f"Fehler: {e}")

    def _save(self):
        file_path = self.e_file.get().strip()
        if file_path and self._is_apyscript(file_path):
            content = self.txt_content.get("1.0", tk.END).rstrip()
            # JSON-Validierung vor Speichern
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                messagebox.showerror("Ungültiges JSON", f"Der Inhalt ist kein gültiges JSON:\n{e}")
                self.status_var.set("Fehler: Ungültiges JSON")
                return
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content + "\n")
                self.status_var.set(f"Datei gespeichert: {file_path}")
                self.saved = True
                self.win.destroy()
            except Exception as e:
                messagebox.showerror("Fehler beim Speichern", f"Datei konnte nicht gespeichert werden:\n{e}")
                self.status_var.set(f"Fehler beim Speichern: {e}")
        else:
            messagebox.showwarning("Ungültige Datei", "Bitte wählen Sie eine gültige .apyscript-Datei.")
            self.status_var.set("Ungültige Datei ausgewählt")

    def _validate_json(self):
        """Validiert den JSON-Inhalt und aktualisiert die Statusleiste."""
        try:
            json.loads(self.txt_content.get("1.0", tk.END).rstrip())
            self.status_var.set("Gültiges JSON")
        except json.JSONDecodeError:
            self.status_var.set("Ungültiges JSON")

    def _menu_load_apyscript(self):
        """Neues Menü für 'Load Apyscript'."""
        path = filedialog.askopenfilename(
            title="Load .apyscript file...",
            filetypes=[("Apyscript files", "*.apyscript")]
        )
        if path:
            self.e_file.delete(0, tk.END)
            self.e_file.insert(0, path)
            self._load_content(path)
            self.apyscript_file = path
            self.status_var.set(f"Datei geladen: {path}")
            self._highlight_all_lines()

    def _menu_save_apyscript(self):
        """Neues Menü für 'Save Apyscript'."""
        file_path = filedialog.asksaveasfilename(
            title="Save .apyscript as...",
            defaultextension=".apyscript",
            filetypes=[("Apyscript files", "*.apyscript")]
        )
        if file_path:
            content = self.txt_content.get("1.0", tk.END).rstrip()
            # JSON-Validierung vor Speichern
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                messagebox.showerror("Ungültiges JSON", f"Der Inhalt ist kein gültiges JSON:\n{e}")
                self.status_var.set("Fehler: Ungültiges JSON")
                return
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content + "\n")
                self.status_var.set(f"Datei gespeichert: {file_path}")
                self.e_file.delete(0, tk.END)
                self.e_file.insert(0, file_path)
                self.apyscript_file = file_path
            except Exception as e:
                messagebox.showerror("Fehler beim Speichern", f"Datei konnte nicht gespeichert werden:\n{e}")
                self.status_var.set(f"Fehler beim Speichern: {e}")

    # >>> SEARCH & REPLACE FÜR KEYS <<<

    def _search_replace_dialog(self):
        """Opens a dialog for searching and replacing predefined JSON keys."""
        win = tk.Toplevel(self.win)
        win.title("Search and Replace Key")
        win.geometry("430x200")
        win.transient(self.win)
        win.grab_set()
        win.resizable(False, False)

        # Frame für Zentrierung
        main = ttk.Frame(win, padding=18)
        main.pack(fill="both", expand=True)

        # Find key
        ttk.Label(main, text="Find key:").pack(anchor="w", pady=(0,2))
        search_var = tk.StringVar()
        cb = ttk.Combobox(main, textvariable=search_var, values=sorted(self.json_keywords), state="readonly", width=34)
        cb.pack(fill="x", pady=(0,10))

        # Replace with
        ttk.Label(main, text="Replace with (new key):").pack(anchor="w", pady=(0,2))
        replace_var = tk.StringVar()
        ttk.Entry(main, textvariable=replace_var, width=36).pack(fill="x", pady=(0,14))

        # Buttons nebeneinander, zentriert
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=(4,0))

        def do_replace():
            old_key = search_var.get().strip()
            new_key = replace_var.get().strip()
            if not old_key or not new_key:
                messagebox.showwarning("Missing Key", "Please select a key and provide a replacement.")
                return
            count = self._replace_key_in_content(old_key, new_key)
            self.status_var.set(f"Replaced {count} occurrence(s) of \"{old_key}\".")
            win.destroy()

        ttk.Button(btn_frame, text="Replace", command=do_replace, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy, width=12).pack(side="left", padx=10)
        win.wait_window()


    def _replace_key_in_content(self, old_key, new_key):
        """Ersetzt alle Vorkommen eines Schlüssels im JSON-Content."""
        pattern = rf'"{re.escape(old_key)}"\s*:'
        replacement = f'"{new_key}":'
        content = self.txt_content.get("1.0", tk.END)
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            self.txt_content.delete("1.0", tk.END)
            self.txt_content.insert("1.0", new_content)
            self._highlight_all_lines()
        return count

if __name__ == "__main__":
    root = tk.Tk()
    editor = ApyEditor(root)
    editor.show()
    root.mainloop()
