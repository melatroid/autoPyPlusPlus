import subprocess
import sys
import shutil
from pathlib import Path

from .extension_paths_loader import load_extensions_paths

def log_warning(log_file, msg):
    border = "-" * 50
    log_file.write(f"{border}\n")
    log_file.write(f"!!! WARNING: {msg}\n")
    log_file.write(f"{border}\n")
    log_file.flush()

def log_error(log_file, msg):
    border = "-" * 50
    log_file.write(f"{border}\n")
    log_file.write(f"### ERROR: {msg}\n")
    log_file.write(f"{border}\n")
    log_file.flush()

def log_info(log_file, msg):
    border = "-" * 50
    log_file.write(f"{border}\n")
    log_file.write(f"--- INFO: {msg}\n")
    log_file.write(f"{border}\n")
    log_file.flush()

class CPE0000000:
    """Kompilierklasse für C++."""

    @staticmethod
    def run_cpp(project, log_file) -> None:
        # --- Quell- und Ausgabedateien prüfen ---
        source_files = project.cpp_compile_files if project.cpp_compile_files else []
        if project.script and project.script.endswith(('.cpp', '.cc', '.cxx')):
            if project.script not in source_files:
                source_files.append(project.script)
        if not source_files:
            log_error(log_file, "Keine zu kompilierenden C++-Dateien angegeben.")
            raise ValueError("Keine zu kompilierenden C++-Dateien angegeben.")

        abs_source_files = []
        for src in source_files:
            src_path = Path(src).resolve()
            if not src_path.is_file():
                log_error(log_file, f"Quelldatei {src_path} nicht gefunden.")
                raise FileNotFoundError(f"Quelldatei {src_path} nicht gefunden.")
            abs_source_files.append(str(src_path))

        # --- Fallback-Mechanismus für Compiler-Pfad ---
        cpp_path = getattr(project, "cpp_path", None) or project.cpp_compiler_path
        if not cpp_path or cpp_path == "g++":
            extensions_paths = load_extensions_paths(log_file)
            cpp_candidate = extensions_paths.get("cpp") or extensions_paths.get("g++")
            if cpp_candidate:
                cpp_path = cpp_candidate
                setattr(project, "cpp_path", cpp_candidate)
                log_info(log_file, f"Set cpp_path from extensions: {cpp_candidate}")
        if not cpp_path or cpp_path == "g++":
            cpp_path = shutil.which("x86_64-w64-mingw32-g++") or shutil.which("g++")
            if cpp_path:
                log_info(log_file, f"Found g++ in PATH: {cpp_path}")
        if not cpp_path:
            log_error(log_file, "Kein C++-Compiler gefunden (cpp_path/g++).")
            raise FileNotFoundError("Kein C++-Compiler gefunden (cpp_path/g++).")

        # --- Kommandobau ---
        cmd = [cpp_path]

        # Build-Type (Release/Debug)
        if project.cpp_build_type and project.cpp_build_type.lower() == "debug":
            cmd.append("-g")
        elif project.cpp_build_type and project.cpp_build_type.lower() == "release":
            cmd.append("-O2")

        # Custom Compiler-Flags
        if project.cpp_compiler_flags:
            cmd.extend(project.cpp_compiler_flags.split())

        # Windowed Application Flag für Windows
        if sys.platform == "win32" and getattr(project, "cpp_windowed", False):
            cmd.append("-mwindows")

        # Include-Verzeichnisse
        for inc in project.cpp_include_dirs:
            cmd.extend(["-I", str(inc)])

        # Libraries
        for lib_dir in project.cpp_lib_dirs:
            cmd.extend(["-L", str(lib_dir)])
        for lib in project.cpp_libraries:
            if lib:
                cmd.append(f"-l{lib}")

        # Defines
        for define in project.cpp_defines:
            if define:
                cmd.append(f"-D{define}")

        # Linker-Flags
        if project.cpp_linker_flags:
            cmd.extend(project.cpp_linker_flags.split())

        # --- Output ---
        output_dir = project.cpp_output_dir or str(Path(abs_source_files[0]).parent)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        exe_name = project.name if project.name else Path(abs_source_files[0]).stem

        # Erweiterung: Erweiterung per Projektattribut setzen
        exe_ext = getattr(project, "cpp_output_extension", ".exe" if sys.platform == "win32" else "")
        output_file = str(Path(output_dir) / f"{exe_name}{exe_ext}")
        cmd.extend(["-o", output_file])

        # Quellcode-Dateien hinzufügen
        cmd.extend(abs_source_files)

        log_info(log_file, "C++-Befehl wird ausgeführt:")
        log_info(log_file, " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            log_info(log_file, result.stdout)
            if result.stderr:
                log_warning(log_file, result.stderr)
        except subprocess.CalledProcessError as e:
            log_error(log_file, "C++-Build failed:")
            log_error(log_file, e.stdout)
            log_error(log_file, e.stderr)
            raise
        except Exception as e:
            log_error(log_file, f"Unerwarteter Fehler bei der C++-Kompilierung: {e}")
            raise

        log_info(log_file, f"Fertig. Ausgabedatei: {output_file}")
