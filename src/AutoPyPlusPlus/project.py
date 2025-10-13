import json
from pathlib import Path
from typing import Any

class Project:
    """
    Project-Datencontainer.
    """

    def __init__(
        self,
        script: str = "",
        name: str = "",
        *,
        spec_file: str = "",
        compile_selected:   bool = False,
        compile_a_selected: bool | None = None,
        compile_b_selected: bool | None = None,
        compile_c_selected: bool | None = None, 
        use_pyarmor: bool = False,
        use_nuitka:  bool = False,
        use_cython:  bool = False,
        use_cpp:     bool  = False,
        use_msvc:    bool = False,
        is_divider:  bool = False,
        divider_label: str = "",
    ) -> None:
        # -------- Basisdaten --------
        self.script: str = script
        self.display_script: str = ""  # für .spec
        self.name: str = name or (Path(script).stem if script else "")
        self.spec_file = spec_file

        # -------- Divider-Persistenz --------
        self.is_divider: bool = is_divider
        self.divider_label: str = divider_label or self.name

        # -------- Auswahl-Flags --------
        self.compile_selected: bool = compile_selected
        self.compile_a_selected: bool = (
            compile_a_selected if compile_a_selected is not None else compile_selected
        )
        self.compile_b_selected: bool = (
            compile_b_selected if compile_b_selected is not None else False
        )
        self.compile_c_selected: bool = (
            compile_c_selected if compile_c_selected is not None else False
        )

        # -------- Compiler-Zustand setzen --------
        self._set_compiler(use_pyarmor, use_nuitka, use_cython, use_cpp)

        # ── Pfad-Attribute für Tools ──────────────
        self.pyinstaller_path: str | None = None
        self.pyarmor_path: str     | None = None
        self.nuitka_path: str      | None = None
        self.cython_path: str      | None = None
        self.cpp_path: str         | None = None
        
        self.icon: str = ""
        self.add_data: str = ""
        self.hidden_imports: str = ""
        self.version: str = ""
        self.output: str = ""
        self.onefile: bool = False
        self.console: bool = True
        self.upx: bool = False
        self.noupx: bool = False
        self.debug: bool = False
        self.clean: bool = True
        self.strip: bool = False
        self.runtime_hook: str = ""
        self.splash: str = ""
        self.options: str = ""
        self.pyarmor_dist_dir: str = ""
        self.no_runtime_key: bool = True
        self.exclude_tcl: bool = False

        # ── PyArmor generisch ──────────────────────
        self.pyarmor_command: str = "gen"
        self.pyarmor_options: str = ""

        # ── PyArmor erweiterte Optionen ────────────
        self.pyarmor_obf_code: str = "1"
        self.pyarmor_mix_str: bool = False
        self.pyarmor_private: bool = False
        self.pyarmor_restrict: bool = False
        self.pyarmor_assert_import: bool = False
        self.pyarmor_assert_call: bool = False
        self.pyarmor_platform: str = ""
        self.pyarmor_pack: str = ""
        self.pyarmor_expired: str = ""
        self.pyarmor_bind_device: str = ""
        self.include_pyarmor_runtime = False
        self.pyarmor_runtime_dir = ""

        # ── Nuitka-Build-Optionen ─────────
        self.nuitka_extra_opts: str = ""
        self.nuitka_standalone: bool = False
        self.nuitka_onefile: bool = False
        self.nuitka_output_dir: str = ""
        self.nuitka_follow_imports: bool = True
        self.nuitka_tkinter_plugin: bool = False
        self.nuitka_follow_stdlib: bool = False
        self.nuitka_plugins: str = ""
        self.nuitka_show_progress: bool = False
        self.nuitka_lto: str = "auto"        # "auto", "yes", "no"
        self.nuitka_jobs: int = 1
        self.nuitka_show_memory: bool = False
        self.nuitka_show_scons: bool = False
        self.nuitka_windows_uac_admin: bool = False
        self.nuitka_windows_icon: str = ""
        self.nuitka_windows_splash: str = ""
        
        # ── Cython-Optionen ───────────────────────────
        self.use_cython: bool = use_cython 
        self.cython_build_with_setup: bool = True
        self.cython_target_type: str = "Python Extension"
        self.cython_boundscheck: bool = False
        self.cython_wraparound: bool = False
        self.cython_nonecheck: bool = False
        self.cython_cdivision: bool = True
        self.cython_language_level: int = 3
        self.cython_initializedcheck: bool = False
        self.cython_output_dir: str = ""
        self.cython_keep_pyx: bool = True
        self.cython_language: str = "c++"
        self.cython_profile: bool = False
        self.cython_linemap: bool = False
        self.cython_gdb: bool = False
        self.cython_embedsignature: bool = False
        self.cython_cplus_exceptions: bool = False
        self.cython_cpp_locals: bool = False
        self.cython_directives: dict | None = None
        self.cython_annotate: bool = False
        self.cython_include_dirs: list[str] = []
        self.cython_compile_time_env: dict | None = None
        self.additional_files: list[str] = []
        
        # ── C++-Compiler Optionen ───────────────────────
        self.use_cpp: bool  = use_cpp
        self.use_msvc = use_msvc
        self.cpp_language: str = "cpp"
        self.cpp_filename: str = "" 
        self.cpp_output_file: str = ""
        self.cpp_windowed: bool = False
        self.cpp_compiler_path: str = "g++"
        self.cpp_compiler_flags: str = "" 
        self.cpp_linker_flags: str = ""
        self.cpp_include_dirs: list[str] = []
        self.cpp_lib_dirs: list[str] = []
        self.cpp_libraries: list[str] = []
        self.cpp_defines: list[str] = []
        self.cpp_output_dir: str = ""
        self.cpp_build_type: str = "Release" 
        self.cpp_compile_files: list[str] = []
        self.cpp_target_type: str = "Executable"
        self.cpp_target_platform: str = "Windows"
        
        # ---- Pytest-Optionen ----
        self.use_pytest: bool = False
        self.use_pytest_standalone: bool = False
        self.pytest_path: str | None = None
        self.test_file: str = ""
        self.test_dir: str = ""
        self.pytest_verbose: bool = False
        self.pytest_quiet: bool = False
        self.pytest_maxfail: int | None = None
        self.pytest_marker: str = ""
        self.pytest_keyword: str = ""
        self.pytest_disable_warnings: bool = False
        self.pytest_tb: str = ""
        self.pytest_durations: int | None = None
        self.pytest_capture: str = ""
        self.pytest_html: str = ""
        self.pytest_lf: bool = False
        self.pytest_ff: bool = False
        self.pytest_args: list[str] | str = []
        
        # ---- Sphinx-Optionen ----
        self.use_sphinx: bool = False
        self.use_sphinx_standalone: bool = False
        self.sphinx_source: str = "docs"
        self.sphinx_build: str = "_build/html"
        self.sphinx_build_path: str | None = None
        self.sphinx_builder: str = "html"
        self.sphinx_conf_path: str = ""
        self.sphinx_doctrees: str = ""
        self.sphinx_parallel: int = 1
        self.sphinx_warning_is_error: bool = False
        self.sphinx_quiet: bool = False
        self.sphinx_verbose: bool = False
        self.sphinx_very_verbose: bool = False
        self.sphinx_keep_going: bool = False
        self.sphinx_tags: list[str] = []
        self.sphinx_define: list[str] = []
        self.sphinx_new_build: bool = False
        self.sphinx_all_files: bool = False
        self.sphinx_logfile: str = ""
        self.sphinx_nitpicky: bool = False
        self.sphinx_color: bool = False
        self.sphinx_no_color: bool = False
        self.sphinx_args: list[str] = []

    def _set_compiler(self, use_pyarmor=False, use_nuitka=False, use_cython=False, use_cpp=False):
        """Setzt den Compiler-Zustand, erlaubt Kombination von Cython und C++."""
        if use_pyarmor:
            self.use_pyarmor = True
            self.use_nuitka = False
            self.use_cython = False
            self.use_cpp = False
        elif use_nuitka:
            self.use_pyarmor = False
            self.use_nuitka = True
            self.use_cython = False
            self.use_cpp = False
        else:
            self.use_pyarmor = False
            self.use_nuitka = False
            self.use_cython = use_cython or use_cpp
            self.use_cpp = use_cpp

    def to_dict(self) -> dict[str, Any]:
        data = {
            "script": self.script,
            "display_script": self.display_script,
            "name": self.name,
            "compile_selected": self.compile_selected,
            "compile_a_selected": self.compile_a_selected,
            "compile_b_selected": self.compile_b_selected,
            "compile_c_selected": self.compile_c_selected,
            "pyinstaller_path": self.pyinstaller_path,
            "pyarmor_path": self.pyarmor_path,
            "nuitka_path": self.nuitka_path,
            "cython_path": self.cython_path,
            # ── Pyinstaller-Optionen ──────────────
            "icon": self.icon,
            "add_data": self.add_data,
            "hidden_imports": self.hidden_imports,
            "version": self.version,
            "output": self.output,
            "onefile": self.onefile,
            "console": self.console,
            "upx": self.upx,
            "noupx": self.noupx,
            "debug": self.debug,
            "clean": self.clean,
            "strip": self.strip,
            "runtime_hook": self.runtime_hook,
            "splash": self.splash,
            "spec_file": self.spec_file,
            "options": self.options,
            "use_pyarmor": self.use_pyarmor,
            "use_nuitka": self.use_nuitka,
            "is_divider": self.is_divider,
            "divider_label": self.divider_label,
            "no_runtime_key": self.no_runtime_key,
            "exclude_tcl": self.exclude_tcl,
            # ── PyArmor-Optionen ──────────────
            "include_pyarmor_runtime": self.include_pyarmor_runtime,
            "pyarmor_command": self.pyarmor_command,
            "pyarmor_options": self.pyarmor_options,
            "pyarmor_obf_code": self.pyarmor_obf_code,
            "pyarmor_mix_str": self.pyarmor_mix_str,
            "pyarmor_private": self.pyarmor_private,
            "pyarmor_restrict": self.pyarmor_restrict,
            "pyarmor_assert_import": self.pyarmor_assert_import,
            "pyarmor_assert_call": self.pyarmor_assert_call,
            "pyarmor_platform": self.pyarmor_platform,
            "pyarmor_pack": self.pyarmor_pack,
            "pyarmor_expired": self.pyarmor_expired,
            "pyarmor_bind_device": self.pyarmor_bind_device,
            "pyarmor_runtime_dir": self.pyarmor_runtime_dir,
            # ── Nuitka-Optionen ──────────────
            "nuitka_tkinter_plugin": self.nuitka_tkinter_plugin,  
            "nuitka_extra_opts": self.nuitka_extra_opts,
            "nuitka_standalone": self.nuitka_standalone,
            "nuitka_onefile": self.nuitka_onefile,
            "nuitka_output_dir": self.nuitka_output_dir,
            "nuitka_follow_imports": self.nuitka_follow_imports,
            "nuitka_follow_stdlib": self.nuitka_follow_stdlib,
            "nuitka_plugins": self.nuitka_plugins,
            "nuitka_show_progress": self.nuitka_show_progress,
            "nuitka_lto": self.nuitka_lto,
            "nuitka_jobs": self.nuitka_jobs,
            "nuitka_show_memory": self.nuitka_show_memory,
            "nuitka_show_scons": self.nuitka_show_scons,
            "nuitka_windows_uac_admin": self.nuitka_windows_uac_admin,
            "nuitka_windows_icon": self.nuitka_windows_icon,
            "nuitka_windows_splash": self.nuitka_windows_splash,
            # ── Cython-Optionen ──────────────
            "use_cython": self.use_cython,
            "cython_build_with_setup": self.cython_build_with_setup,
            "cython_target_type": self.cython_target_type,
            "cython_boundscheck": self.cython_boundscheck,
            "cython_wraparound": self.cython_wraparound,
            "cython_nonecheck": self.cython_nonecheck,
            "cython_cdivision": self.cython_cdivision,
            "cython_language_level": self.cython_language_level,
            "cython_initializedcheck": self.cython_initializedcheck,
            "cython_output_dir": self.cython_output_dir,
            "cython_keep_pyx": self.cython_keep_pyx,
            "cython_language": self.cython_language,
            "cython_profile": self.cython_profile,
            "cython_linemap": self.cython_linemap,
            "cython_gdb": self.cython_gdb,
            "cython_embedsignature": self.cython_embedsignature,
            "cython_cplus_exceptions": self.cython_cplus_exceptions,
            "cython_cpp_locals": self.cython_cpp_locals,
            "cython_directives": self.cython_directives if self.cython_directives is not None else {},
            "cython_annotate": self.cython_annotate,
            "cython_include_dirs": self.cython_include_dirs,
            "cython_compile_time_env": self.cython_compile_time_env if self.cython_compile_time_env is not None else {},
            "additional_files": self.additional_files,
            # ── CPP-Optionen ──────────────
            "use_cpp": self.use_cpp,
            "cpp_output_file": self.cpp_output_file,
            "use_msvc": self.use_msvc,
            "cpp_filename": self.cpp_filename,
            "cpp_windowed": self.cpp_windowed,
            "cpp_compiler_path": self.cpp_compiler_path,
            "cpp_compiler_flags": self.cpp_compiler_flags,
            "cpp_linker_flags": self.cpp_linker_flags,
            "cpp_include_dirs": self.cpp_include_dirs,
            "cpp_lib_dirs": self.cpp_lib_dirs,
            "cpp_libraries": self.cpp_libraries,
            "cpp_defines": self.cpp_defines,
            "cpp_output_dir": self.cpp_output_dir,
            "cpp_build_type": self.cpp_build_type,
            "cpp_compile_files": self.cpp_compile_files,
            "cpp_target_type": self.cpp_target_type,
            "cpp_target_platform": self.cpp_target_platform,
            # ---- Pytest-Optionen ----
            "pytest_path": self.pytest_path,
            "use_pytest": self.use_pytest,
            "use_pytest_standalone": self.use_pytest_standalone,
            "test_file": self.test_file,
            "test_dir": self.test_dir,
            "pytest_verbose": self.pytest_verbose,
            "pytest_quiet": self.pytest_quiet,
            "pytest_maxfail": self.pytest_maxfail,
            "pytest_marker": self.pytest_marker,
            "pytest_keyword": self.pytest_keyword,
            "pytest_disable_warnings": self.pytest_disable_warnings,
            "pytest_tb": self.pytest_tb,
            "pytest_durations": self.pytest_durations,
            "pytest_capture": self.pytest_capture,
            "pytest_html": self.pytest_html,
            "pytest_lf": self.pytest_lf,
            "pytest_ff": self.pytest_ff,
            "pytest_args": self.pytest_args,
            # ---- Sphinx-Optionen ----
            "use_sphinx": self.use_sphinx,
            "use_sphinx_standalone": self.use_sphinx_standalone,
            "sphinx_source": self.sphinx_source,
            "sphinx_build": self.sphinx_build,
            "sphinx_build_path": self.sphinx_build_path,
            "sphinx_builder": self.sphinx_builder,
            "sphinx_conf_path": self.sphinx_conf_path,
            "sphinx_doctrees": self.sphinx_doctrees,
            "sphinx_parallel": self.sphinx_parallel,
            "sphinx_warning_is_error": self.sphinx_warning_is_error,
            "sphinx_quiet": self.sphinx_quiet,
            "sphinx_verbose": self.sphinx_verbose,
            "sphinx_very_verbose": self.sphinx_very_verbose,
            "sphinx_keep_going": self.sphinx_keep_going,
            "sphinx_tags": self.sphinx_tags,
            "sphinx_define": self.sphinx_define,
            "sphinx_new_build": self.sphinx_new_build,
            "sphinx_all_files": self.sphinx_all_files,
            "sphinx_logfile": self.sphinx_logfile,
            "sphinx_nitpicky": self.sphinx_nitpicky,
            "sphinx_color": self.sphinx_color,
            "sphinx_no_color": self.sphinx_no_color,
            "sphinx_args": self.sphinx_args,
        }

        # Nur wenn PyArmor aktiv, pyarmor_dist_dir auch speichern
        data["pyarmor_dist_dir"] = self.pyarmor_dist_dir if self.use_pyarmor else ""
        return data

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Project":
        p = cls(
            script=d.get("script", ""),
            name=d.get("name", ""),
            compile_selected=d.get("compile_selected", False),
            compile_a_selected=d.get("compile_a_selected"),
            compile_b_selected=d.get("compile_b_selected"),
            compile_c_selected=d.get("compile_c_selected"),
            spec_file=d.get("spec_file", ""),
            use_pyarmor=d.get("use_pyarmor", False),
            use_nuitka=d.get("use_nuitka", False),
            use_cython=d.get("use_cython", False),
            use_cpp=d.get("use_cpp", False),
            use_msvc=d.get("use_msvc", True),
            is_divider=bool(d.get("is_divider", False)),
            divider_label=d.get("divider_label", d.get("name", "")),
        )
        p.additional_files = d.get("additional_files", [])  # außerhalb des Konstruktors

        # Korrigiere potenzielle inkonsistente Compiler-Zustände
        if p.use_pyarmor and p.use_nuitka:
            p.use_nuitka = False  # PyArmor hat Vorrang

        # ── Pfad-Attribute aus dict laden ──────────────
        p.pyinstaller_path = d.get("pyinstaller_path")
        p.pyarmor_path = d.get("pyarmor_path")
        p.nuitka_path = d.get("nuitka_path")
        p.cython_path = d.get("cython_path")

        # ── Pyinstaller-Optionen laden ──────────────
        p.display_script = d.get("display_script", "")
        p.icon = d.get("icon", "")
        p.add_data = d.get("add_data", "")
        p.hidden_imports = d.get("hidden_imports", "")
        p.version = d.get("version", "")
        p.output = d.get("output", "")
        p.onefile = d.get("onefile", False)
        p.console = d.get("console", True)
        p.upx = d.get("upx", False)
        p.noupx = d.get("noupx", False)
        p.debug = d.get("debug", False)
        p.clean = d.get("clean", True)
        p.strip = d.get("strip", False)
        p.runtime_hook = d.get("runtime_hook", "")
        p.splash = d.get("splash", "")
        p.options = d.get("options", "")
        p.no_runtime_key = d.get("no_runtime_key", False)
        p.exclude_tcl = d.get("exclude_tcl", False)

        # ── PyArmor-Optionen laden ──────────────
        p.include_pyarmor_runtime = d.get("include_pyarmor_runtime", False)
        p.pyarmor_command = d.get("pyarmor_command", "gen")
        p.pyarmor_options = d.get("pyarmor_options", "")
        p.pyarmor_obf_code = d.get("pyarmor_obf_code", "1")
        p.pyarmor_mix_str = d.get("pyarmor_mix_str", False)
        p.pyarmor_private = d.get("pyarmor_private", False)
        p.pyarmor_restrict = d.get("pyarmor_restrict", False)
        p.pyarmor_assert_import = d.get("pyarmor_assert_import", False)
        p.pyarmor_assert_call = d.get("pyarmor_assert_call", False)
        p.pyarmor_platform = d.get("pyarmor_platform", "")
        p.pyarmor_pack = d.get("pyarmor_pack", "")
        p.pyarmor_expired = d.get("pyarmor_expired", "")
        p.pyarmor_bind_device = d.get("pyarmor_bind_device", "")
        p.pyarmor_runtime_dir = d.get("pyarmor_runtime_dir", "")
        p.pyarmor_dist_dir = d.get("pyarmor_dist_dir", "") if p.use_pyarmor else ""

        # ── Nuitka-Optionen laden ──────────────
        p.nuitka_tkinter_plugin = d.get("nuitka_tkinter_plugin", False)
        p.nuitka_extra_opts = d.get("nuitka_extra_opts", "")
        p.nuitka_standalone = d.get("nuitka_standalone", False)
        p.nuitka_onefile = d.get("nuitka_onefile", False)
        p.nuitka_output_dir = d.get("nuitka_output_dir", "")
        p.nuitka_follow_imports = d.get("nuitka_follow_imports", True)
        p.nuitka_follow_stdlib = d.get("nuitka_follow_stdlib", False)
        p.nuitka_plugins = d.get("nuitka_plugins", "")
        p.nuitka_show_progress = d.get("nuitka_show_progress", False)
        p.nuitka_lto = d.get("nuitka_lto", "auto")
        p.nuitka_jobs = d.get("nuitka_jobs", 1)
        p.nuitka_show_memory = d.get("nuitka_show_memory", False)
        p.nuitka_show_scons = d.get("nuitka_show_scons", False)
        p.nuitka_windows_uac_admin = d.get("nuitka_windows_uac_admin", False)
        p.nuitka_windows_icon = d.get("nuitka_windows_icon", "")
        p.nuitka_windows_splash = d.get("nuitka_windows_splash", "")
        
        # ── Cython-Optionen laden ──────────────
        p.use_cython = d.get("use_cython", False)
        p.cython_build_with_setup = d.get("cython_build_with_setup", True)
        p.cython_target_type = d.get("cython_target_type", "Python Extension") 
        p.cython_boundscheck = d.get("cython_boundscheck", False)
        p.cython_wraparound = d.get("cython_wraparound", False)
        p.cython_nonecheck = d.get("cython_nonecheck", False)
        p.cython_cdivision = d.get("cython_cdivision", True)
        p.cython_language_level = d.get("cython_language_level", 3)
        p.cython_initializedcheck = d.get("cython_initializedcheck", False)
        p.cython_output_dir = d.get("cython_output_dir", "")
        p.cython_keep_pyx = d.get("cython_keep_pyx", True)
        p.cython_language = d.get("cython_language", "c++")
        p.cython_profile = d.get("cython_profile", False)
        p.cython_linemap = d.get("cython_linemap", False)
        p.cython_gdb = d.get("cython_gdb", False)
        p.cython_embedsignature = d.get("cython_embedsignature", False)
        p.cython_cplus_exceptions = d.get("cython_cplus_exceptions", False)
        p.cython_cpp_locals = d.get("cython_cpp_locals", False)
        p.cython_directives = d.get("cython_directives", {}) if d.get("cython_directives") is not None else {}
        p.cython_annotate = d.get("cython_annotate", False)
        p.cython_include_dirs = d.get("cython_include_dirs", [])
        p.cython_compile_time_env = d.get("cython_compile_time_env", {}) if d.get("cython_compile_time_env") is not None else {}

        # ── CPP-Optionen ──────────────
        p.cpp_language = d.get("cpp_language", "cpp")
        p.use_msvc = d.get("use_msvc", True)
        p.cpp_output_file = d.get("cpp_output_file", "")
        p.cpp_windowed = d.get("cpp_windowed", False)
        p.cpp_compiler_path = d.get("cpp_compiler_path", "g++")
        p.cpp_compiler_flags = d.get("cpp_compiler_flags", "")
        p.cpp_linker_flags = d.get("cpp_linker_flags", "")
        p.cpp_include_dirs = d.get("cpp_include_dirs", [])
        p.cpp_lib_dirs = d.get("cpp_lib_dirs", [])
        p.cpp_libraries = d.get("cpp_libraries", [])
        p.cpp_defines = d.get("cpp_defines", [])
        p.cpp_output_dir = d.get("cpp_output_dir", "")
        p.cpp_build_type = d.get("cpp_build_type", "Release")
        p.cpp_compile_files = d.get("cpp_compile_files", [])
        p.cpp_target_type = d.get("cpp_target_type", "Executable")
        p.cpp_target_platform = d.get("cpp_target_platform", "Windows")
        p.cpp_filename = d.get("cpp_filename", "")
        
        # ---- Pytest-Optionen ----
        p.use_pytest = d.get("use_pytest", False)
        p.use_pytest_standalone = d.get("use_pytest_standalone", False)
        p.pytest_path = d.get("pytest_path")
        p.test_file = d.get("test_file", "")
        p.test_dir = d.get("test_dir", "")
        p.pytest_verbose = d.get("pytest_verbose", False)
        p.pytest_quiet = d.get("pytest_quiet", False)
        p.pytest_maxfail = d.get("pytest_maxfail")
        p.pytest_marker = d.get("pytest_marker", "")
        p.pytest_keyword = d.get("pytest_keyword", "")
        p.pytest_disable_warnings = d.get("pytest_disable_warnings", False)
        p.pytest_tb = d.get("pytest_tb", "")
        p.pytest_durations = d.get("pytest_durations")
        p.pytest_capture = d.get("pytest_capture", "")
        p.pytest_html = d.get("pytest_html", "")
        p.pytest_lf = d.get("pytest_lf", False)
        p.pytest_ff = d.get("pytest_ff", False)
        p.pytest_args = d.get("pytest_args", [])
        
        # ---- Sphinx-Optionen ----
        p.use_sphinx = d.get("use_sphinx", False)
        p.use_sphinx_standalone = d.get("use_sphinx_standalone", False)
        p.sphinx_source = d.get("sphinx_source", "docs")
        p.sphinx_build = d.get("sphinx_build", "_build/html")
        p.sphinx_build_path = d.get("sphinx_build_path", None)
        p.sphinx_builder = d.get("sphinx_builder", "html")
        p.sphinx_conf_path = d.get("sphinx_conf_path", "")
        p.sphinx_doctrees = d.get("sphinx_doctrees", "")
        p.sphinx_parallel = d.get("sphinx_parallel", 1)
        p.sphinx_warning_is_error = d.get("sphinx_warning_is_error", False)
        p.sphinx_quiet = d.get("sphinx_quiet", False)
        p.sphinx_verbose = d.get("sphinx_verbose", False)
        p.sphinx_very_verbose = d.get("sphinx_very_verbose", False)
        p.sphinx_keep_going = d.get("sphinx_keep_going", False)
        p.sphinx_tags = d.get("sphinx_tags", [])
        p.sphinx_define = d.get("sphinx_define", [])
        p.sphinx_new_build = d.get("sphinx_new_build", False)
        p.sphinx_all_files = d.get("sphinx_all_files", False)
        p.sphinx_logfile = d.get("sphinx_logfile", "")
        p.sphinx_nitpicky = d.get("sphinx_nitpicky", False)
        p.sphinx_color = d.get("sphinx_color", False)
        p.sphinx_no_color = d.get("sphinx_no_color", False)
        p.sphinx_args = d.get("sphinx_args", [])

        # Fallback-Sanity
        if p.is_divider and not p.divider_label:
            p.divider_label = p.name

        p._set_compiler(
            use_pyarmor=p.use_pyarmor,
            use_nuitka=p.use_nuitka,
            use_cython=p.use_cython,
            use_cpp=p.use_cpp,
        )
        return p

    @staticmethod
    def to_dict_list(projects: list["Project"]) -> str:
        return json.dumps([p.to_dict() for p in projects], indent=2, ensure_ascii=False)
