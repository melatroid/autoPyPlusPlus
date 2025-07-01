import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .extension_paths_loader import load_extensions_paths
from pathlib import Path
import shutil
import subprocess
import sys
import os
import re
from typing import cast, Iterable, Optional

class GCCEditor:
    def __init__(self, master, project):
        self.master = master
        self.project = project
        self.saved = False
        self.win = None
        self.e_cpp_include_dirs: Optional[ttk.Entry] = None
        self.e_cpp_lib_dirs: Optional[ttk.Entry] = None
        self.e_cpp_libraries: Optional[ttk.Entry] = None
        self.e_cpp_defines: Optional[ttk.Entry] = None
        self.e_cpp_linker_flags: Optional[ttk.Entry] = None
        self.default_values = {
            "cpp_compiler_path": "g++",
            "cpp_output_dir": "",
            "cpp_output_file": "",  # leer, wird dynamisch bestimmt
            "cpp_build_type": "Release",
            "cpp_standard": "c++23",
            "cpp_target_type": "CHANGE!",
            "cpp_compiler_flags": "",
            "cpp_linker_flags": "",
            "cpp_generate_deps": False,
            "cpp_verbose_compile": False,
            "cpp_compile_files": [],
            "cpp_include_dirs": [],
            "cpp_lib_dirs": [],
            "cpp_libraries": [],
            "cpp_defines": [],
            "cpp_windowed": False,
            "cpp_language": "cpp",
        }
        self.extensions_paths = {}

    def _get_default_output_file(self) -> str:
        base = "name"
        target_type = self.var_target_type.get() if hasattr(self, "var_target_type") else self.default_values["cpp_target_type"]
        if sys.platform == "win32":
            if target_type == "Executable":
                return base + ".exe"
            elif target_type == "Static Library":
                return base + ".lib"
            elif target_type == "Shared Library":
                return base + ".dll"
            elif target_type == "Python Extension":
                return base + ".pyd"
        elif sys.platform == "darwin":
            if target_type == "Shared Library":
                return "lib" + base + ".dylib"
            elif target_type == "Python Extension":
                return base + ".so"
        else:
            if target_type == "Static Library":
                return "lib" + base + ".a"
            elif target_type == "Shared Library":
                return "lib" + base + ".so"
            elif target_type == "Python Extension":
                return base + ".so"
        return base + ".out"
    
    def get_ext_for_target(self, target_type, target_platform):
        if target_platform == "Windows":
            ext_map = {
                "Executable": ".exe",
                "Static Library": ".lib",
                "Shared Library": ".dll",
                "Python Extension": ".pyd"
            }
        elif target_platform == "macOS":
            ext_map = {
                "Executable": ".out",
                "Static Library": ".a",
                "Shared Library": ".dylib",
                "Python Extension": ".so"
            }
        else: # Linux
            ext_map = {
                "Executable": ".out",
                "Static Library": ".a",
                "Shared Library": ".so",
                "Python Extension": ".so"
            }
        return ext_map.get(target_type, ".out")

    def update_python_extension_flags(self):
        # Aktuelle Flags holen und splitten
        flags = self.e_cpp_compiler_flags.get().strip().split()
        target_type = self.var_target_type.get()
        target_platform = self.var_target_platform.get()
        modified = False

        if target_type == "Python Extension":
            if "-shared" not in flags:
                flags.append("-shared")
                modified = True
            if target_platform == "Windows" and "-DMS_WIN64" not in flags:
                flags.append("-DMS_WIN64")
                modified = True
            if target_platform != "Windows" and "-DMS_WIN64" in flags:
                flags.remove("-DMS_WIN64")
                modified = True
        else:
            if "-shared" in flags:
                flags.remove("-shared")
                modified = True
            if "-DMS_WIN64" in flags:
                flags.remove("-DMS_WIN64")
                modified = True

        if modified:
            self.e_cpp_compiler_flags.delete(0, tk.END)
            self.e_cpp_compiler_flags.insert(0, " ".join(flags))

    


    def add_adv_entry(self, label_text: str, row: int, init_value: str, tooltip: Optional[str] = None) -> ttk.Entry:
        label = ttk.Label(self.adv_frame, text=label_text)
        label.grid(row=row, column=0, sticky="e", pady=5, padx=(0, 5))
        entry = ttk.Entry(self.adv_frame, width=40)
        entry.grid(row=row, column=1, sticky="ew", pady=5)
        entry.insert(0, init_value)
        if tooltip:
             self._create_tooltip(label, tooltip)
        return entry

    def show(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("GCC/GPP Settings")
        self.win.geometry("1300x700")
        self.win.transient(self.master)
        self.win.grab_set()
        self.win.minsize(800, 500)
        #self.win = tk.Toplevel(self.master)
        
        main_frame = ttk.Frame(self.win, padding=15)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure((0, 1), weight=1)

        general_frame = ttk.LabelFrame(main_frame, text="General Settings", padding=10)
        general_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        general_frame.columnconfigure(1, weight=1)

        self.extensions_paths = load_extensions_paths(None)

        lang_default = cast(str, getattr(self.project, "cpp_language", self.default_values["cpp_language"]))
        self.var_language = tk.StringVar(value=lang_default)

        ttk.Label(general_frame, text="Language:").grid(row=0, column=0, sticky="e", pady=5, padx=(0, 5))
        self.combo_language = ttk.Combobox(
            general_frame,
            textvariable=self.var_language,
            values=["cpp", "c"],
            state="readonly",
            width=15,
        )
        self.combo_language.grid(row=0, column=1, sticky="w", pady=5)
        self.combo_language.bind("<<ComboboxSelected>>", lambda e: self.on_language_changed())

        # Compiler path + buttons
        self.e_cpp_compiler_path = ttk.Entry(general_frame, width=40)
        self.e_cpp_compiler_path.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(general_frame, text="Set Compiler", command=lambda: self._choose_file(self.e_cpp_compiler_path)).grid(row=0, column=2, padx=5)
        ttk.Button(general_frame, text="Find any Compiler",  command=self.auto_detect_gcc).grid(row=0, column=3, padx=5)
        ttk.Button(general_frame, text="Check Compiler", command=self.check_current_compiler).grid(row=0, column=4, padx=5)

        # Set default compiler path
        if lang_default == "c":
            default_compiler_path = self.extensions_paths.get("gcc", "gcc")
        else:
            default_compiler_path = self.extensions_paths.get("cpp", "g++")
        self.e_cpp_compiler_path.insert(0, default_compiler_path)

        ttk.Label(general_frame, text="Output Folder:").grid(row=1, column=0, sticky="e", pady=5, padx=(0, 5))
        output_dir_default = cast(str, getattr(self.project, "cpp_output_dir", self.default_values["cpp_output_dir"]))
        self.e_cpp_output_dir = ttk.Entry(general_frame, width=40)
        self.e_cpp_output_dir.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(general_frame, text="Browse", command=lambda: self._choose_dir(self.e_cpp_output_dir)).grid(row=1, column=2, padx=5)
        self.e_cpp_output_dir.insert(0, output_dir_default)

        ttk.Label(general_frame, text="Output File Name:").grid(row=2, column=0, sticky="e", pady=5, padx=(0, 5))
        output_file_default = cast(str, getattr(self.project, "cpp_output_file", ""))
        if not output_file_default:
            output_file_default = self._get_default_output_file()
        self.e_cpp_output_file = ttk.Entry(general_frame, width=40)
        self.e_cpp_output_file.grid(row=2, column=1, sticky="ew", pady=5)
        self.e_cpp_output_file.insert(0, output_file_default)
        

        build_type_default = cast(str, getattr(self.project, "cpp_build_type", self.default_values["cpp_build_type"]))
        self.var_build_type = tk.StringVar(value=build_type_default)
        ttk.Label(general_frame, text="Build Type:").grid(row=3, column=0, sticky="e", pady=5, padx=(0, 5))
        self.combo_build_type = ttk.Combobox(
            general_frame, textvariable=self.var_build_type,
            values=["Release", "Debug"], state="readonly", width=15
        )
        self.combo_build_type.grid(row=3, column=1, sticky="w", pady=5)

        cpp_standard_default = cast(str, getattr(self.project, "cpp_standard", self.default_values["cpp_standard"]))
        self.var_cpp_standard = tk.StringVar(value=cpp_standard_default)
        ttk.Label(general_frame, text="C++ Standard:").grid(row=4, column=0, sticky="e", pady=5, padx=(0, 5))
        self.combo_cpp_standard = ttk.Combobox(
            general_frame, textvariable=self.var_cpp_standard,
            values=["c++11", "c++14", "c++17", "c++20", "c++23"], state="readonly", width=15
        )
        self.combo_cpp_standard.grid(row=4, column=1, sticky="w", pady=5)

        target_type_default = cast(str, getattr(self.project, "cpp_target_type", self.default_values["cpp_target_type"]))
        self.var_target_type = tk.StringVar(value=target_type_default)
        ttk.Label(general_frame, text="Target Type:").grid(row=5, column=0, sticky="e", pady=5, padx=(0, 5))
        self.combo_target_type = ttk.Combobox(
            general_frame,
            textvariable=self.var_target_type,
            values=["Executable", "Static Library", "Shared Library", "Python Extension"],
            state="readonly",
            width=15,
        )
        self.combo_target_type.grid(row=5, column=1, sticky="w", pady=5)
        self.combo_target_type.bind("<<ComboboxSelected>>", self.on_target_type_or_platform_changed)



        # Zielplattform auswählen
        target_platform_default = getattr(self.project, "cpp_target_platform", "Windows")
        self.var_target_platform = tk.StringVar(value=target_platform_default)
        ttk.Label(general_frame, text="Target Platform:").grid(row=5, column=2, sticky="e", pady=5, padx=(0, 5))
        self.combo_target_platform = ttk.Combobox(
            general_frame,
            textvariable=self.var_target_platform,
            values=["Windows", "Linux", "macOS"],
            state="readonly",
            width=15,
        )
        self.combo_target_platform.grid(row=5, column=3, sticky="w", pady=5)
        self.combo_target_platform.bind("<<ComboboxSelected>>", self.on_target_type_or_platform_changed)

        
        
        windowed_default = cast(bool, getattr(self.project, "cpp_windowed", self.default_values.get("cpp_windowed", False)))
        self.var_cpp_windowed = tk.BooleanVar(value=windowed_default)

        self.var_debug_mode = tk.BooleanVar(value=getattr(self.project, "debug", False))
        ttk.Checkbutton(general_frame, text="Debug Mode (Keep Log)", variable=self.var_debug_mode).grid(row=6, column=1, sticky="w", pady=5)

        # Windows only: windowed checkbox, but controlled
        self.windowed_checkbox = None
        if sys.platform == "win32":
            self.windowed_checkbox = ttk.Checkbutton(
                general_frame,
                text="Windowed Application (-mwindows)",
                variable=self.var_cpp_windowed,
            )
            self.windowed_checkbox.grid(row=7, column=1, sticky="w", pady=5)

        compiler_flags_default = cast(str, getattr(self.project, "cpp_compiler_flags", self.default_values["cpp_compiler_flags"]))
        ttk.Label(general_frame, text="Compiler Flags:").grid(row=7, column=0, sticky="e", pady=5, padx=(0, 5))
        self.e_cpp_compiler_flags = ttk.Entry(general_frame, width=40)
        self.e_cpp_compiler_flags.grid(row=7, column=1, sticky="ew", pady=5)
        self.e_cpp_compiler_flags.insert(0, compiler_flags_default)
        ttk.Button(general_frame, text="Add Flags", command=self.add_example_flags).grid(row=7, column=2, padx=5)

        ttk.Label(general_frame, text="Compile Files:").grid(row=8, column=0, sticky="ne", pady=5, padx=(0, 5))
        self.compile_files_listbox = tk.Listbox(general_frame, height=8, width=40, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(general_frame, orient="vertical", command=self.compile_files_listbox.yview)
        self.compile_files_listbox.configure(yscrollcommand=scrollbar.set)
        self.compile_files_listbox.grid(row=8, column=1, sticky="nsew", pady=5)
        scrollbar.grid(row=8, column=2, sticky="ns", pady=5)
        compile_files_default = cast(Iterable[str], getattr(self.project, "cpp_compile_files", self.default_values["cpp_compile_files"]))
        for f in compile_files_default:
            self.compile_files_listbox.insert(tk.END, f)

        file_btn_frame = ttk.Frame(general_frame)
        file_btn_frame.grid(row=9, column=1, sticky="ew", pady=5)
        ttk.Button(file_btn_frame, text="Add Files", command=self.add_compile_files).pack(side="left", padx=5)
        ttk.Button(file_btn_frame, text="Remove Selected", command=self.remove_selected_files).pack(side="left", padx=5)
        ttk.Button(file_btn_frame, text="Autosearch C++", command=self.auto_detect_files).pack(side="left", padx=5)
        general_frame.rowconfigure(8, weight=1)

        # Nach file_btn_frame/rowconfigure(8, weight=1):
        self.adv_frame = ttk.LabelFrame(main_frame, text="Advanced Options", padding=10)
        self.adv_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        self.adv_frame.columnconfigure(1, weight=1)

        include_dirs_default = cast(Iterable[str], getattr(self.project, "cpp_include_dirs", self.default_values["cpp_include_dirs"]))
        self.e_cpp_include_dirs = self.add_adv_entry(
            "Include Dirs (comma-separated):", 0,
            ", ".join(include_dirs_default),
            "Directories for headers (-I)"
        )

        lib_dirs_default = cast(Iterable[str], getattr(self.project, "cpp_lib_dirs", self.default_values["cpp_lib_dirs"]))
        self.e_cpp_lib_dirs = self.add_adv_entry(
            "Library Dirs (comma-separated):", 1,
            ", ".join(lib_dirs_default),
            "Directories for libraries (-L)"
        )
        libraries_default = cast(Iterable[str], getattr(self.project, "cpp_libraries", self.default_values["cpp_libraries"]))
        self.e_cpp_libraries = self.add_adv_entry(
            "Libraries (comma-separated):", 2,
            ", ".join(libraries_default),
            "Libraries to link (e.g., m for -lm)"
        )
        defines_default = cast(Iterable[str], getattr(self.project, "cpp_defines", self.default_values["cpp_defines"]))
        self.e_cpp_defines = self.add_adv_entry(
            "Defines (comma-separated):", 3,
            ", ".join(defines_default),
            "Preprocessor definitions (e.g., DEBUG=1)"
        )
        linker_flags_default = cast(str, getattr(self.project, "cpp_linker_flags", self.default_values["cpp_linker_flags"]))
        self.e_cpp_linker_flags = self.add_adv_entry(
            "Linker Flags:", 4,
            linker_flags_default,
            "Flags for the linker (e.g., -Wl,--as-needed)"
        )

        generate_deps_default = cast(bool, getattr(self.project, "cpp_generate_deps", self.default_values["cpp_generate_deps"]))
        self.var_generate_deps = tk.BooleanVar(value=generate_deps_default)
        ttk.Checkbutton(self.adv_frame, text="Generate Dependencies (-MMD)", variable=self.var_generate_deps).grid(row=5, column=1, sticky="w", pady=5)

        verbose_compile_default = cast(bool, getattr(self.project, "cpp_verbose_compile", self.default_values["cpp_verbose_compile"]))
        self.var_verbose_compile = tk.BooleanVar(value=verbose_compile_default)
        ttk.Checkbutton(self.adv_frame, text="Verbose Compilation (-v)", variable=self.var_verbose_compile).grid(row=6, column=1, sticky="w", pady=5)


        ttk.Label(main_frame, text="Compilation Command Preview:").grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        self.command_preview = tk.Text(main_frame, height=3, wrap="word")
        self.command_preview.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.command_preview.config(state="disabled")
        ttk.Button(main_frame, text="Update Preview", command=self.update_command_preview).grid(row=3, column=0, columnspan=2, pady=5)

        button_frame = ttk.Frame(self.win, padding=(10, 5))
        button_frame.pack(fill="x", side="bottom")
        ttk.Button(button_frame, text="Reset to Default", command=self.reset_to_default).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side="right", padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.update_command_preview()
        self.win.wait_window(self.win)
        return self.saved


    def on_target_type_or_platform_changed(self, *_):
        target_type = self.var_target_type.get()
        target_platform = self.var_target_platform.get()
        base_name = Path(self.e_cpp_output_file.get()).stem or "name"
        new_ext = self.get_ext_for_target(target_type, target_platform)
        self.e_cpp_output_file.delete(0, tk.END)
        self.e_cpp_output_file.insert(0, base_name + new_ext)

        # Windowed-Checkbox je nach Zielplattform und Typ
        if hasattr(self, "windowed_checkbox"):
            if target_platform == "Windows" and target_type == "Executable":
                self.windowed_checkbox.config(state="normal")
            else:
                self.windowed_checkbox.config(state="disabled")
                self.var_cpp_windowed.set(False)

        self.update_python_extension_flags()
        self.update_command_preview()



    def on_language_changed(self):
        lang = self.var_language.get()

        gcc_path = self.extensions_paths.get("gcc", "gcc")
        gpp_path = self.extensions_paths.get("cpp", "g++")

        current_compiler_path = self.e_cpp_compiler_path.get().strip()
        current_compiler_name = Path(current_compiler_path).name if current_compiler_path else ""

        if current_compiler_name in ("gcc", "g++", ""):
            if lang == "c":
                new_compiler_path = gcc_path
            else:
                new_compiler_path = gpp_path
            self.e_cpp_compiler_path.delete(0, tk.END)
            self.e_cpp_compiler_path.insert(0, new_compiler_path)

        output_file = self.e_cpp_output_file.get().strip()
        base_name = Path(output_file).stem if output_file else "name"
        ext = Path(output_file).suffix.lower() if output_file else ""
        target_type = self.var_target_type.get()

        if target_type == "Executable":
            if sys.platform == "win32":
                new_ext = ".exe"
            else:
                new_ext = ".out"
        elif target_type == "Static Library":
            if sys.platform == "win32":
                new_ext = ".lib"
            else:
                new_ext = ".a"
        elif target_type == "Shared Library":
            if sys.platform == "win32":
                new_ext = ".dll"
            elif sys.platform == "darwin":
                new_ext = ".dylib"
            else:
                new_ext = ".so"
        else:
            new_ext = ".out"

        if ext != new_ext:
            self.e_cpp_output_file.delete(0, tk.END)
            self.e_cpp_output_file.insert(0, base_name + new_ext)

        self.update_command_preview()

    def _create_tooltip(self, widget, text):
        def enter(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 20}+{event.y_root + 20}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip

        def leave(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def check_compiler_validity(self, path: str) -> tuple[bool, str]:
        p = Path(path)
        if not p.is_file():
            return False, "Compiler file does not exist."
        if sys.platform != "win32" and not os.access(str(p), os.X_OK):
            return False, "Compiler is not executable."

        try:
            result = subprocess.run([str(p), "--version"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and ("g++" in result.stdout or "clang" in result.stdout or "gcc" in result.stdout):
                return True, f"Succesfully, Compiler found: {result.stdout.splitlines()[0]}"
            return False, "File is not a valid g++, gcc or clang compiler."
        except Exception as e:
            return False, f"Error Compiler :: {e}"

    def check_current_compiler(self):
        path = self.e_cpp_compiler_path.get().strip()
        valid, msg = self.check_compiler_validity(path)
        if valid:
            messagebox.showinfo("Compiler Check", msg)
        else:
            messagebox.showerror("Compiler Check", msg)

    def add_example_flags(self):
        categories = {
            "Optimization": [
                "-O0 (No optimization)",
                "-O1 (Optimize)",
                "-O2 (More optimization)",
                "-O3 (Maximum optimization)",
                "-march=native (Optimize for host CPU)",
                "-funroll-loops (Unroll loops)",
                "-flto (Link-time optimization)"
            ],
            "Warnings": [
                "-Wall (Enable all warnings)",
                "-Wextra (Extra warnings)",
                "-Wpedantic (Strict standard compliance)"
            ],
            "Debugging": [
                "-g (Debug information)",
                "-fsanitize=address (AddressSanitizer)",
                "-fsanitize=undefined (UndefinedBehaviorSanitizer)"
            ],
            "Linker": [
                "-Wl,--as-needed (Link only needed libraries)",
                "-Wl,-rpath=. (Set runtime library path)",
                "-fuse-ld=lld (Use LLVM lld linker)"
            ],
            "Platform-specific": []
        }

        if sys.platform == "win32":
            categories["Platform-specific"] = [
                "/EHsc (Enable C++ exceptions - MSVC)",
                "/MD (Multi-threaded DLL runtime - MSVC)",
                "/W3 (Warning level 3 - MSVC)",
            ]
        elif sys.platform == "darwin":
            categories["Platform-specific"] = [
                "-framework Cocoa (macOS Cocoa framework)",
                "-framework OpenGL (macOS OpenGL framework)",
                "-pthread (POSIX threads)"
            ]
        else:
            categories["Platform-specific"] = [
                "-pthread (POSIX threads)",
                "-fPIC (Position Independent Code)"
            ]

        popup = tk.Toplevel(self.win)
        popup.title("Select Compiler Flags")
        popup.geometry("340x900")
        popup.resizable(False, True)
        popup.transient(self.win)
        popup.grab_set()

        container = ttk.Frame(popup, padding=10)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def insert_flag(flag_text: str):
            flag = flag_text.split()[0]
            current = self.e_cpp_compiler_flags.get()
            if current and not current.endswith(" "):
                self.e_cpp_compiler_flags.insert(tk.END, " ")
            self.e_cpp_compiler_flags.insert(tk.END, flag + " ")
            self.update_command_preview()

        for category, flags in categories.items():
            if not flags:
                continue
            cat_label = ttk.Label(scrollable_frame, text=category, font=("Segoe UI", 10, "bold"))
            cat_label.pack(anchor="w", pady=(10, 0))
            for flag in flags:
                btn = ttk.Button(scrollable_frame, text=flag, width=50, command=lambda f=flag: insert_flag(f))
                btn.pack(anchor="w", pady=2)

        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

    def add_compile_files(self):
        paths = filedialog.askopenfilenames(
            title="Select files to compile",
            filetypes=[("C++ source files", "*.c *.cpp *.cc *.cxx"), ("All files", "*.*")]
        )
        for path in paths:
            if path not in self.compile_files_listbox.get(0, tk.END):
                self.compile_files_listbox.insert(tk.END, path)
        self.update_command_preview()

    def remove_selected_files(self):
        selected = list(self.compile_files_listbox.curselection())
        for i in reversed(selected):
            self.compile_files_listbox.delete(i)
        self.update_command_preview()

    def auto_detect_files(self):
        project_dir = filedialog.askdirectory(title="Select Project Directory")
        if not project_dir:
            return
        project_path = Path(project_dir)
        source_extensions = (".cpp", ".cc", ".cxx", ".c")
        include_dirs = set()
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith(source_extensions):
                    file_path = str(Path(root) / file)
                    if file_path not in self.compile_files_listbox.get(0, tk.END):
                        self.compile_files_listbox.insert(tk.END, file_path)
                if file.endswith((".h", ".hpp")):
                    include_dirs.add(str(Path(root)))
        if self.e_cpp_include_dirs is not None:
            self.e_cpp_include_dirs.delete(0, tk.END)
            self.e_cpp_include_dirs.insert(0, ", ".join(str(s) for s in include_dirs))
        self.update_command_preview()
        messagebox.showinfo("Auto-detect", f"Found {self.compile_files_listbox.size()} source files and {len(include_dirs)} include directories.")

    def reset_to_default(self):
        # Setze Compilerpfad basierend auf Sprache korrekt zurück
        lang_default = self.default_values.get("cpp_language", "cpp")
        self.var_language.set(lang_default)
        if lang_default == "c":
            default_compiler_path = self.extensions_paths.get("gcc", "gcc")
        else:
            default_compiler_path = self.extensions_paths.get("cpp", "g++")

        self.e_cpp_compiler_path.delete(0, tk.END)
        self.e_cpp_compiler_path.insert(0, default_compiler_path)

        self.e_cpp_output_dir.delete(0, tk.END)
        self.e_cpp_output_dir.insert(0, self.default_values["cpp_output_dir"])

        output_file_default = cast(str, getattr(self.project, "cpp_output_file", ""))
        if not output_file_default:
            output_file_default = self._get_default_output_file()
        self.e_cpp_output_file.delete(0, tk.END)
        self.e_cpp_output_file.insert(0, output_file_default)

        self.var_build_type.set(self.default_values["cpp_build_type"])
        self.var_cpp_standard.set(self.default_values["cpp_standard"])
        self.var_target_type.set(self.default_values["cpp_target_type"])

        self.e_cpp_compiler_flags.delete(0, tk.END)
        self.e_cpp_compiler_flags.insert(0, self.default_values["cpp_compiler_flags"])

        self.e_cpp_linker_flags.delete(0, tk.END)
        self.e_cpp_linker_flags.insert(0, self.default_values["cpp_linker_flags"])

        self.var_generate_deps.set(bool(self.default_values["cpp_generate_deps"]))
        self.var_verbose_compile.set(bool(self.default_values["cpp_verbose_compile"]))

        self.compile_files_listbox.delete(0, tk.END)
        for f in self.default_values["cpp_compile_files"]:
            self.compile_files_listbox.insert(tk.END, f)

        if self.e_cpp_include_dirs is not None:
            self.e_cpp_include_dirs.delete(0, tk.END)
            include_dirs = cast(Iterable[str], self.default_values["cpp_include_dirs"])
            self.e_cpp_include_dirs.insert(0, ", ".join(str(s) for s in include_dirs))

        if self.e_cpp_lib_dirs is not None:
            self.e_cpp_lib_dirs.delete(0, tk.END)
            lib_dirs = cast(Iterable[str], self.default_values["cpp_lib_dirs"])
            self.e_cpp_lib_dirs.insert(0, ", ".join(str(s) for s in lib_dirs))

        if self.e_cpp_libraries is not None:
            self.e_cpp_libraries.delete(0, tk.END)
            libs = cast(Iterable[str], self.default_values["cpp_libraries"])
            self.e_cpp_libraries.insert(0, ", ".join(str(s) for s in libs))

        if self.e_cpp_defines is not None:
            self.e_cpp_defines.delete(0, tk.END)
            defines = cast(Iterable[str], self.default_values["cpp_defines"])
            self.e_cpp_defines.insert(0, ", ".join(str(s) for s in defines))

        self.var_cpp_windowed.set(bool(self.default_values.get("cpp_windowed", False)))

        self.on_language_changed()
        self.update_command_preview()

    def auto_detect_gcc(self):
        lang = self.var_language.get()
        if lang == "c":
            gcc_path = shutil.which("gcc")
            compiler_name = "gcc"
        else:
            gcc_path = shutil.which("g++")
            compiler_name = "g++"

        if gcc_path:
            self.e_cpp_compiler_path.delete(0, tk.END)
            self.e_cpp_compiler_path.insert(0, gcc_path)
            valid, msg = self.check_compiler_validity(gcc_path)
            if valid:
                messagebox.showinfo("Auto-detect", f"{compiler_name} gefunden:\n{msg}")
            else:
                messagebox.showwarning("Auto-detect", f"{compiler_name} gefunden, aber Problem:\n{msg}")
        else:
            messagebox.showwarning("Auto-detect", f"{compiler_name} nicht im PATH gefunden.")
        self.update_command_preview()

    def update_command_preview(self):
        self.command_preview.config(state="normal")
        self.command_preview.delete("1.0", tk.END)
        command = self._build_command()
        self.command_preview.insert("1.0", " ".join(command))
        self.command_preview.config(state="disabled")

    def _build_command(self):
        lang = self.var_language.get()
        compile_files = self.compile_files_listbox.get(0, tk.END)

        if lang == "c":
            compiler_cmd = "gcc"
        else:
            compiler_cmd = "g++"

        compiler_path = self.e_cpp_compiler_path.get().strip()
        if compiler_path:
            compiler_cmd = compiler_path

        command = [compiler_cmd]

        if lang == "cpp":
            command.append(f"-std={self.var_cpp_standard.get()}")

        if "cl.exe" in compiler_cmd.lower():
            command.extend(["/MD", "/EHsc"])
        elif "g++" in compiler_cmd.lower() or "clang" in compiler_cmd.lower() or "gcc" in compiler_cmd.lower():
            command.extend(["-Wall", "-Wextra", "-pedantic"])

        if self.var_generate_deps.get():
            command.append("-MMD")
        if self.var_verbose_compile.get():
            command.append("-v")

        if self.var_target_type.get() == "Static Library":
            output_file = self.e_cpp_output_file.get().strip()
            if self.e_cpp_output_dir.get().strip():
                output_file = str(Path(self.e_cpp_output_dir.get().strip()) / output_file)
            command = ["ar", "rcs", output_file]
            command.extend(compile_files)
            return command

        if self.var_target_type.get() == "Shared Library":
            command.append("-shared")

        if sys.platform == "win32" and getattr(self, "var_cpp_windowed", None) and self.var_cpp_windowed.get():
            command.append("-mwindows")


        compiler_flags = self.e_cpp_compiler_flags.get().strip()
        if compiler_flags:
            command.extend(compiler_flags.split())

        linker_flags = self.e_cpp_linker_flags.get().strip()
        if linker_flags:
            command.extend(linker_flags.split())

        output_dir = self.e_cpp_output_dir.get().strip()
        output_file = self.e_cpp_output_file.get().strip()

        if output_file:
            ext = Path(output_file).suffix.lower()
            target_type = self.var_target_type.get()
            if sys.platform == "win32" and target_type == "Executable" and ext != ".exe":
                output_file = Path(output_file).stem + ".exe"

        if output_dir and output_file:
            command.append(f"-o {Path(output_dir) / output_file}")


        if self.e_cpp_include_dirs is not None:
            for include_dir in [s.strip() for s in self.e_cpp_include_dirs.get().split(",") if s.strip()]:
                command.append(f"-I{include_dir}")

        if self.e_cpp_lib_dirs is not None:
            for lib_dir in [s.strip() for s in self.e_cpp_lib_dirs.get().split(",") if s.strip()]:
                command.append(f"-L{lib_dir}")

        if self.e_cpp_libraries is not None:
            for lib in [s.strip() for s in self.e_cpp_libraries.get().split(",") if s.strip()]:
                command.append(f"-l{lib}")

        if self.e_cpp_defines is not None:
            for define in [s.strip() for s in self.e_cpp_defines.get().split(",") if s.strip()]:
                command.append(f"-D{define}")

        command.extend(compile_files)
        return command

    def save(self):
        compiler_path = self.e_cpp_compiler_path.get().strip()
        if not compiler_path:
            messagebox.showerror("Error", "Path to compiler is missing!")
            return
        if not Path(compiler_path).is_file():
            messagebox.showerror("Error", f"Compiler not found:\n{compiler_path}")
            return

        output_dir = self.e_cpp_output_dir.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "Output directory is missing!")
            return
        output_path = Path(output_dir)
        if not output_path.exists():
            messagebox.showerror("Error", f"Output directory does not exist:\n{output_dir}")
            return
        if not output_path.is_dir():
            messagebox.showerror("Error", f"Output path is not a directory:\n{output_dir}")
            return
        try:
            testfile = output_path / ".write_test"
            with open(testfile, "w", encoding="utf-8") as f:
                f.write("test")
            testfile.unlink()
        except Exception:
            messagebox.showerror("Error", f"Output directory is not writable:\n{output_dir}")
            return

        output_file = self.e_cpp_output_file.get().strip()
        if not output_file:
            messagebox.showerror("Error", "Output file name is missing!")
            return
        if any(c in output_file for c in "/\\:"):
            messagebox.showerror("Error", "Invalid characters in output file name!")
            return

        if self.var_build_type.get() not in ["Release", "Debug"]:
            messagebox.showerror("Error", "Invalid build type selected.")
            return
        if self.var_language.get() == "cpp" and self.var_cpp_standard.get() not in ["c++11", "c++14", "c++17", "c++20", "c++23"]:
            messagebox.showerror("Error", "Invalid C++ standard selected.")
            return
        if self.var_target_type.get() not in ["Executable", "Static Library", "Shared Library", "Python Extension"]:
            messagebox.showerror("Error", "Invalid target type selected.")
            return

        include_dirs = [s.strip() for s in (self.e_cpp_include_dirs.get() if self.e_cpp_include_dirs else "").split(",") if s.strip()]
        for dir in include_dirs:
            if not Path(dir).is_dir():
                messagebox.showerror("Error", f"Include directory does not exist:\n{dir}")
                return

        lib_dirs = [s.strip() for s in (self.e_cpp_lib_dirs.get() if self.e_cpp_lib_dirs else "").split(",") if s.strip()]
        for dir in lib_dirs:
            if not Path(dir).is_dir():
                messagebox.showerror("Error", f"Library directory does not exist:\n{dir}")
                return

        libraries = [s.strip() for s in (self.e_cpp_libraries.get() if self.e_cpp_libraries else "").split(",") if s.strip()]
        for lib in libraries:
            if not re.match(r"^[a-zA-Z0-9_]+$", lib):
                messagebox.showerror("Error", f"Invalid library name:\n{lib}")
                return

        defines = [s.strip() for s in (self.e_cpp_defines.get() if self.e_cpp_defines else "").split(",") if s.strip()]
        for define in defines:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(=.*)?$", define):
                messagebox.showerror("Error", f"Invalid define:\n{define}")
                return

        compile_files = list(self.compile_files_listbox.get(0, tk.END))
        if not compile_files:
            messagebox.showerror("Error", "No source files selected for compilation!")
            return
        for file in compile_files:
            if not Path(file).is_file():
                messagebox.showerror("Error", f"Source file does not exist:\n{file}")
                return

        p = self.project
        p.cpp_compiler_path = compiler_path
        p.cpp_output_dir = output_dir
        p.cpp_output_file = output_file
        p.cpp_build_type = self.var_build_type.get()
        p.cpp_standard = self.var_cpp_standard.get()
        p.cpp_target_type = self.var_target_type.get()
        p.cpp_compiler_flags = self.e_cpp_compiler_flags.get().strip()
        p.cpp_linker_flags = self.e_cpp_linker_flags.get().strip()
        p.cpp_generate_deps = self.var_generate_deps.get()
        p.cpp_verbose_compile = self.var_verbose_compile.get()
        p.cpp_compile_files = compile_files
        p.cpp_include_dirs = include_dirs
        p.cpp_lib_dirs = lib_dirs
        p.cpp_libraries = libraries
        p.cpp_defines = defines
        p.cpp_windowed = self.var_cpp_windowed.get()
        p.cpp_language = self.var_language.get()
        p.debug = self.var_debug_mode.get()
        self.saved = True
        self.win.destroy()

    def on_cancel(self):
        self.saved = False
        self.win.destroy()

    def _choose_file(self, entry):
        path = filedialog.askopenfilename()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
            self.update_command_preview()

    def _choose_dir(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
            self.update_command_preview()
