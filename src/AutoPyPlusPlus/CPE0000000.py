import subprocess
import sys
import shutil
import re
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

def get_extension_for_target(target_type, platform="win32"):
    if platform.startswith("win"):
        if target_type == "Executable":
            return ".exe"
        elif target_type == "Python Extension":
            return ".pyd"
        elif target_type == "Shared Library":
            return ".dll"
        elif target_type == "Static Library":
            return ".lib"
        else:
            return ".out"
    elif platform == "darwin":
        if target_type == "Python Extension" or target_type == "Shared Library":
            return ".so" if target_type == "Python Extension" else ".dylib"
        elif target_type == "Static Library":
            return ".a"
        elif target_type == "Executable":
            return ".out"
        else:
            return ".out"
    else:  # Linux / Unix
        if target_type == "Python Extension" or target_type == "Shared Library":
            return ".so"
        elif target_type == "Static Library":
            return ".a"
        elif target_type == "Executable":
            return ".out"
        else:
            return ".out"

def file_contains_main(file_path, log_file=None):
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
            main_pattern = re.compile(
                r"(?:^|\s)(?:int|static\s+int|extern\s+\"C\"\s+int|extern\s+\"C\"\s+static\s+int)\s+(w?main)\s*\(",
                re.MULTILINE
            )
            found = bool(main_pattern.search(content))
            msg = f"[file_contains_main] {'main() gefunden' if found else 'KEIN main()'} in: {file_path}"
            if log_file:
                log_info(log_file, msg)
            else:
                print(msg)
            return found
    except Exception as ex:
        msg = f"[file_contains_main] Fehler beim Lesen von {file_path}: {ex}"
        if log_file:
            log_warning(log_file, msg)
        else:
            print(msg)
    return False

class CPE0000000:
    """Kompilierklasse für C++."""

    @staticmethod
    def run_cpp(project, log_file) -> None:
        # --- Quell- und Ausgabedateien prüfen ---
        source_files = project.cpp_compile_files if project.cpp_compile_files else []
        if getattr(project, "script", None) and project.script.endswith(('.cpp', '.cc', '.cxx')):
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

        # --- Target-Type prüfen: Executable braucht main()! ---
        target_type = getattr(project, "cpp_target_type", "Executable")
        if target_type == "Executable":
            main_found = any(file_contains_main(f) for f in abs_source_files)
            if not main_found:
                log_error(log_file, "No() in Source-Files! ")
                raise RuntimeError("No main() in Source-Files!")

        # --- Fallback-Mechanismus für Compiler-Pfad ---
        cpp_path = getattr(project, "cpp_path", None) or getattr(project, "cpp_compiler_path", None)
        if not cpp_path or cpp_path.lower() in ("g++", "cl.exe"):
            extensions_paths = load_extensions_paths(log_file)
            cpp_candidate = extensions_paths.get("cpp") or extensions_paths.get("g++") or extensions_paths.get("cl")
            if cpp_candidate:
                cpp_path = cpp_candidate
                setattr(project, "cpp_path", cpp_candidate)
                log_info(log_file, f"Set cpp_path from extensions: {cpp_candidate}")
        if not cpp_path or cpp_path.lower() in ("g++", "cl.exe"):
            cpp_path = shutil.which("cl.exe") or shutil.which("x86_64-w64-mingw32-g++") or shutil.which("g++")
            if cpp_path:
                log_info(log_file, f"Found compiler in PATH: {cpp_path}")
        if not cpp_path:
            log_error(log_file, "Kein C++-Compiler gefunden (cpp_path/g++/cl.exe).")
            raise FileNotFoundError("Kein C++-Compiler gefunden (cpp_path/g++/cl.exe).")

        # --- Kommandobau ---
        is_msvc = str(cpp_path).lower().endswith("cl.exe")

        # Output & Namen bestimmen
        output_dir = getattr(project, "cpp_output_dir", None) or str(Path(abs_source_files[0]).parent)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        exe_name = getattr(project, "name", None) or Path(abs_source_files[0]).stem

        # Erweiterung nach Plattform und Target Type
        exe_ext = getattr(project, "cpp_output_extension", None)
        if not exe_ext:
            exe_ext = get_extension_for_target(target_type, sys.platform)
        output_file = str(Path(output_dir) / f"{exe_name}{exe_ext}")

        if is_msvc:
            cmd = [cpp_path]
            cmd.extend([str(Path(f)) for f in abs_source_files])

            # Output file
            cmd.append(f"/Fe{output_file}")

            # Include-Verzeichnisse
            for inc in getattr(project, "cpp_include_dirs", []):
                cmd.append(f"/I{inc}")

            # Defines
            for define in getattr(project, "cpp_defines", []):
                cmd.append(f"/D{define}")

            # Build-Type
            build_type = getattr(project, "cpp_build_type", "").lower()
            if build_type == "debug":
                cmd.append("/Zi")
                cmd.append("/DEBUG")
            else:
                cmd.append("/O2")

            # C++ Standard (ab MSVC 2015): /std:c++17 usw.
            cpp_std = getattr(project, "cpp_standard", None)
            if cpp_std and cpp_std.startswith("c++"):
                std_map = {
                    "c++11": "c++11",
                    "c++14": "c++14",
                    "c++17": "c++17",
                    "c++20": "c++20",
                    "c++23": "c++latest"
                }
                std_flag = std_map.get(cpp_std)
                if std_flag:
                    cmd.append(f"/std:{std_flag}")

            # Target-spezifische Flags für Python Extension / Shared Lib
            if target_type == "Python Extension" or target_type == "Shared Library":
                if "/LD" not in cmd and not any(flag.lower() == "/ld" for flag in cmd):
                    cmd.append("/LD")

            # Windowed (nur für Windows-GUI)
            if getattr(project, "cpp_windowed", False):
                cmd.append("/SUBSYSTEM:WINDOWS")

            # Custom Flags
            if getattr(project, "cpp_compiler_flags", None):
                cmd.extend(str(project.cpp_compiler_flags).split())

            # Libdirs und Linker-Flags
            link_args = []
            for lib_dir in getattr(project, "cpp_lib_dirs", []):
                link_args.append(f"/LIBPATH:{lib_dir}")
            for lib in getattr(project, "cpp_libraries", []):
                if not lib.lower().endswith(".lib"):
                    link_args.append(f"{lib}.lib")
                else:
                    link_args.append(lib)
            if getattr(project, "cpp_linker_flags", None):
                link_args.extend(str(project.cpp_linker_flags).split())

            if link_args:
                cmd.append("/link")
                cmd.extend(link_args)

        else:
            cmd = [cpp_path]

            # Build-Type (Release/Debug)
            build_type = getattr(project, "cpp_build_type", "").lower()
            if build_type == "debug":
                cmd.append("-g")
            elif build_type == "release":
                cmd.append("-O2")

            cpp_std = getattr(project, "cpp_standard", None)
            if cpp_std and cpp_std.startswith("c++"):
                cmd.append(f"-std={cpp_std}")

            # Target-spezifische Flags für Shared Library / Python Extension
            if target_type == "Python Extension" or target_type == "Shared Library":
                if "-shared" not in cmd:
                    cmd.append("-shared")

            # Custom Compiler-Flags
            if getattr(project, "cpp_compiler_flags", None):
                cmd.extend(str(project.cpp_compiler_flags).split())

            # Windowed Application Flag für Windows
            if sys.platform == "win32" and getattr(project, "cpp_windowed", False):
                cmd.append("-mwindows")

            # Include-Verzeichnisse
            for inc in getattr(project, "cpp_include_dirs", []):
                cmd.extend(["-I", str(inc)])

            # Libraries
            for lib_dir in getattr(project, "cpp_lib_dirs", []):
                cmd.extend(["-L", str(lib_dir)])
            for lib in getattr(project, "cpp_libraries", []):
                if lib:
                    cmd.append(f"-l{lib}")

            # Defines
            for define in getattr(project, "cpp_defines", []):
                if define:
                    cmd.append(f"-D{define}")

            # Linker-Flags
            if getattr(project, "cpp_linker_flags", None):
                cmd.extend(str(project.cpp_linker_flags).split())

            # Output File
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
                check=True,
                encoding="mbcs",
                errors="replace"
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
