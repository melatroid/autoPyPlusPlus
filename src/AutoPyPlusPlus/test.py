import io
from pathlib import Path
import pytest
import shutil

from AutoPyPlusPlus.CPA0000000 import CPA0000000
from AutoPyPlusPlus.CPB0000000 import CPB0000000
from AutoPyPlusPlus.CPC0000000 import CPC0000000
from AutoPyPlusPlus.CPD0000000 import CPD0000000
from AutoPyPlusPlus.CPE0000000 import CPE0000000

# Universelle Project-Klasse für alle Compiler
class Project:
    def __init__(self, script, **kwargs):
        self.script = script
        # PyInstaller
        self.include_pyarmor_runtime = False
        self.name = ""
        self.icon = None
        self.add_data = ""
        self.hidden_imports = ""
        self.version = None
        self.output = ""
        self.onefile = True
        self.console = True
        self.upx = False
        self.debug = False
        self.clean = False
        self.strip = False
        self.runtime_hook = None
        self.splash = None
        self.spec_file = None
        self.options = ""
        self.pyinstaller_path = None
        self.pyarmor_runtime_dir = ""
        # PyArmor
        self.pyarmor_path = None
        self.pyarmor_command = None
        self.pyarmor_options = ""
        # Nuitka
        self.nuitka_path = None
        self.nuitka_standalone = False
        self.nuitka_onefile = False
        self.nuitka_output_dir = None
        self.nuitka_follow_imports = False
        self.nuitka_follow_stdlib = False
        self.nuitka_plugins = ""
        self.nuitka_tkinter_plugin = False
        self.nuitka_lto = None
        self.nuitka_jobs = 1
        self.nuitka_show_progress = False
        self.nuitka_show_memory = False
        self.nuitka_show_scons = False
        self.nuitka_windows_uac_admin = False
        self.nuitka_windows_icon = None
        self.nuitka_windows_splash = None
        self.nuitka_extra_opts = ""
        # Cython
        self.cython_path = None
        self.cython_output_dir = None
        self.cython_boundscheck = False
        self.cython_wraparound = False
        self.cython_nonecheck = False
        self.cython_cdivision = True
        self.cython_initializedcheck = False
        self.cython_profile = False
        self.cython_linemap = False
        self.cython_gdb = False
        self.cython_embedsignature = False
        self.cython_cplus_exceptions = False
        self.cython_cpp_locals = False
        self.cython_annotate = False
        self.cython_language_level = None
        self.cython_directives = None
        self.cython_include_dirs = None
        self.cython_compile_time_env = None
        self.cython_language = "c"
        self.cython_target_type = ""
        self.cython_build_with_setup = False
        self.cython_keep_pyx = True
        # C++
        self.cpp_compile_files = []
        self.cpp_target_type = "Executable"
        self.cpp_path = None
        self.cpp_compiler_path = None
        self.cpp_output_dir = None
        self.cpp_output_extension = None
        self.cpp_include_dirs = []
        self.cpp_lib_dirs = []
        self.cpp_libraries = []
        self.cpp_defines = []
        self.cpp_build_type = None
        self.cpp_standard = None
        self.cpp_windowed = False
        self.cpp_compiler_flags = None
        self.cpp_linker_flags = None
        for k, v in kwargs.items():
            setattr(self, k, v)

# ------------------ CPA (PyInstaller) ------------------
def make_dummy_project_cpa(tmp_path):
    script_file = tmp_path / "testscript.py"
    script_file.write_text("print('hello')")
    return Project(
        script=str(script_file),
        name="MeinTestApp",
        output=str(tmp_path / "dist"),
        onefile=True,
        console=False,
    )

def test_build_command_cpa_minimal(tmp_path, monkeypatch):
    log_file = io.StringIO()
    project = make_dummy_project_cpa(tmp_path)
    monkeypatch.setattr(
        "AutoPyPlusPlus.CPA0000000.load_extensions_paths",
        lambda log: {}
    )
    monkeypatch.setattr(shutil, "which", lambda exe: "/usr/bin/pyinstaller")
    # Patch is_file so that the script is found
    monkeypatch.setattr(Path, "is_file", lambda self: str(self).endswith("testscript.py"))
    commands = CPA0000000.build_command(project, log_file)
    assert commands[0] == "/usr/bin/pyinstaller"
    assert commands[1].endswith("testscript.py")
    assert "--name=MeinTestApp" in commands
    assert "--onefile" in commands
    assert "--noconsole" in commands
    assert any(cmd.startswith("--distpath=") for cmd in commands)

# ------------------ CPB (PyArmor) ------------------
def make_dummy_project_cpb(tmp_path):
    script_file = tmp_path / "dummyscript.py"
    script_file.write_text("print('obfuscate')")
    return Project(
        script=str(script_file),
        pyarmor_command="gen",
        pyarmor_options="--output dist/ --no-runtime-key"
    )

def test_run_pyarmor_build_command(tmp_path, monkeypatch):
    log_file = io.StringIO()
    project = make_dummy_project_cpb(tmp_path)
    monkeypatch.setattr(
        "AutoPyPlusPlus.CPB0000000.load_extensions_paths",
        lambda log: {}
    )
    monkeypatch.setattr(shutil, "which", lambda exe: "/usr/bin/pyarmor")
    def fake_run(cmd, capture_output, text, check):
        assert cmd[0] == "/usr/bin/pyarmor"
        assert cmd[1] == "gen"
        assert any("--output" in x for x in cmd)
        assert any("--no-runtime-key" in x for x in cmd)
        assert cmd[-1].endswith("dummyscript.py")
        FakeResult = type("FakeResult", (), {})
        fake = FakeResult()
        fake.stdout = "PyArmor OK"
        fake.stderr = ""
        fake.returncode = 0
        return fake
    monkeypatch.setattr("subprocess.run", fake_run)
    CPB0000000.run_pyarmor(project, log_file)
    out = log_file.getvalue()
    assert "Running PyArmor command:" in out
    assert "PyArmor OK" in out

# ------------------ CPC (Nuitka) ------------------
def make_dummy_project_cpc(tmp_path):
    script_file = tmp_path / "nuitka_testscript.py"
    script_file.write_text("print('compiled by nuitka')")
    return Project(
        script=str(script_file),
        nuitka_standalone=True,
        nuitka_onefile=True,
        nuitka_output_dir=str(tmp_path / "nuitka_dist"),
        nuitka_plugins="",
        nuitka_tkinter_plugin=True,
        nuitka_lto="yes",
        nuitka_jobs=2,
        nuitka_show_progress=True,
        nuitka_show_memory=True,
        nuitka_show_scons=True,
        nuitka_windows_uac_admin=True,
        nuitka_windows_icon=None,
        nuitka_windows_splash=None,
        nuitka_extra_opts="--nofollow-import-to=unittest"
    )

def test_run_nuitka_build_command(tmp_path, monkeypatch):
    log_file = io.StringIO()
    project = make_dummy_project_cpc(tmp_path)
    monkeypatch.setattr(
        "AutoPyPlusPlus.CPC0000000.load_extensions_paths",
        lambda log: {}
    )
    monkeypatch.setattr(shutil, "which", lambda exe: "/usr/bin/nuitka")
    # Patch is_file so that the script is found
    monkeypatch.setattr(Path, "is_file", lambda self: str(self).endswith("nuitka_testscript.py"))
    def fake_run(cmd, **kwargs):
        assert cmd[0] == "/usr/bin/nuitka"
        assert "--standalone" in cmd
        assert "--onefile" in cmd
        assert f"--output-dir={project.nuitka_output_dir}" in cmd
        assert "--enable-plugin=tk-inter" in cmd
        assert "--lto=yes" in cmd
        assert "--jobs=2" in cmd
        assert "--show-progress" in cmd
        assert "--show-memory" in cmd
        assert "--show-scons" in cmd
        assert "--windows-uac-admin" in cmd
        assert "--nofollow-import-to=unittest" in cmd
        assert cmd[-1].endswith("nuitka_testscript.py")
        FakeResult = type("FakeResult", (), {})
        fake = FakeResult()
        fake.stdout = "Nuitka OK"
        fake.stderr = ""
        fake.returncode = 0
        return fake
    monkeypatch.setattr("subprocess.run", fake_run)
    CPC0000000.run_nuitka(project, log_file)
    out = log_file.getvalue()
    assert "Nuitka-Befehl wird ausgeführt:" in out
    assert "Nuitka OK" in out
    assert "nuitka-run.bat nicht gefunden" in out

# ------------------ CPD (Cython) ------------------
def make_dummy_project_cpd(tmp_path):
    script_file = tmp_path / "cython_testscript.py"
    script_file.write_text("print('compiled by cython')")
    return Project(
        script=str(script_file),
        cython_output_dir=str(tmp_path / "cython_dist"),
        cython_boundscheck=True,
        cython_wraparound=True,
        cython_nonecheck=True,
        cython_cdivision=False,
        cython_initializedcheck=True,
        cython_profile=True,
        cython_linemap=True,
        cython_gdb=True,
        cython_embedsignature=True,
        cython_cplus_exceptions=True,
        cython_cpp_locals=True,
        cython_annotate=True,
        cython_language_level=3,
        cython_language="cpp",
        cython_target_type="exe",
        cython_include_dirs=[str(tmp_path)],
        cython_compile_time_env={"TESTENV": 1},
        cython_build_with_setup=False,
        cython_keep_pyx=True,
        cython_directives={"binding": True},
    )

def test_run_cython_build_command(tmp_path, monkeypatch):
    log_file = io.StringIO()
    project = make_dummy_project_cpd(tmp_path)
    monkeypatch.setattr(
        "AutoPyPlusPlus.CPD0000000.load_extensions_paths",
        lambda log: {}
    )
    monkeypatch.setattr(shutil, "which", lambda exe: "/usr/bin/cython")
    # Patch is_file so that the script is found
    monkeypatch.setattr(Path, "is_file", lambda self: str(self).endswith("cython_testscript.py"))
    def fake_run(cmd, **kwargs):
        assert cmd[0] == "/usr/bin/cython"
        assert "--annotate" in cmd
        assert "--cplus" in cmd
        assert "--embed" in cmd
        assert "--directive=" in " ".join(cmd)
        assert "-o" in cmd
        assert cmd[-2].endswith(".cpp")
        assert cmd[-1].endswith("cython_testscript.py")
        FakeResult = type("FakeResult", (), {})
        fake = FakeResult()
        fake.stdout = "Cython OK"
        fake.stderr = ""
        fake.returncode = 0
        return fake
    monkeypatch.setattr("subprocess.run", fake_run)
    CPD0000000.run_cython(project, log_file)
    out = log_file.getvalue()
    assert "Cython-Befehl wird ausgeführt:" in out
    assert "Cython OK" in out
    assert "Kein setup.py gefunden" in out or "kein automatischer Build" in out

# ------------------ CPE (C++/g++) ------------------
def make_dummy_project_cpe(tmp_path):
    cpp_file = tmp_path / "dummy.cpp"
    cpp_file.write_text("int main() { return 0; }")
    return Project(
        script=str(cpp_file),
        cpp_compile_files=[str(cpp_file)],
        name="DummyExe",
        cpp_output_dir=str(tmp_path / "cpp_dist"),
        cpp_target_type="Executable",
        cpp_standard="c++17",
        cpp_build_type="Release",
        cpp_include_dirs=[str(tmp_path)],
        cpp_lib_dirs=[],
        cpp_libraries=["stdc++"],
        cpp_defines=["MYDEF"],
        cpp_compiler_flags="-Wall",
        cpp_linker_flags="-static",
        cpp_windowed=True,
    )

def test_run_cpp_build_command(tmp_path, monkeypatch):
    log_file = io.StringIO()
    project = make_dummy_project_cpe(tmp_path)
    monkeypatch.setattr(
        "AutoPyPlusPlus.CPE0000000.load_extensions_paths",
        lambda log: {}
    )
    monkeypatch.setattr(shutil, "which", lambda exe: "/usr/bin/g++")
    # Patch is_file so that the script is found
    monkeypatch.setattr(Path, "is_file", lambda self: str(self).endswith("dummy.cpp"))
    def fake_run(cmd, **kwargs):
        assert cmd[0] == "/usr/bin/g++"
        assert "-o" in cmd
        assert any(x.endswith("dummy.cpp") for x in cmd)
        assert "-Wall" in cmd
        assert "-static" in cmd
        assert "-O2" in cmd
        # Akzeptiere -std=c++17 als Flag, falls dein Compiler/Toolchain das hinzufügt
        assert any(x.startswith("-std=c++") or x.startswith("/std:") for x in cmd) or "-std=c++17" in " ".join(cmd) or "/std:c++17" in " ".join(cmd)
        assert "-D" in " ".join(cmd)
        assert "-lstdc++" in cmd
        FakeResult = type("FakeResult", (), {})
        fake = FakeResult()
        fake.stdout = "C++ OK"
        fake.stderr = ""
        fake.returncode = 0
        return fake
    monkeypatch.setattr("subprocess.run", fake_run)
    CPE0000000.run_cpp(project, log_file)
    out = log_file.getvalue()
    assert "C++-Befehl wird ausgeführt:" in out
    assert "C++ OK" in out
    assert "Fertig. Ausgabedatei:" in out
