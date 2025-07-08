
import os
import sys
import configparser
from pathlib import Path

def load_extensions_paths(log_file=None) -> dict:
    base_dir = Path(__file__).parent
    path_file = base_dir / "extensions_path.ini"

    if log_file is not None:
        log_file.write("--- load_extensions_paths() START ---\n")
        log_file.write(f"Erwarteter Pfad: {path_file.resolve()}\n")
        log_file.write(f"Exists: {path_file.exists()}\n")
        log_file.write(f"CWD: {os.getcwd()}\n")
        log_file.flush()

    def is_cpp_exe(filename: str) -> bool:
        if sys.platform == "win32":
            return filename.lower() in [
                "g++.exe", "mingw32-g++.exe", "mingw64-g++.exe",
                "x86_64-w64-mingw32-g++.exe", "clang++.exe", "cl.exe"
            ]
        else:
            return filename in ["g++", "clang++"]

    def is_gcc_exe(filename: str) -> bool:
        if sys.platform == "win32":
            return filename.lower() in [
                "gcc.exe", "mingw32-gcc.exe", "mingw64-gcc.exe",
                "x86_64-w64-mingw32-gcc.exe", "clang.exe"
            ]
        else:
            return filename in ["gcc", "clang"]

    def is_other_tool_exe(filename: str, key: str) -> bool:
        if key == "nuitka":
            valid = ["nuitka.exe", "nuitka", "nuitka.cmd"] if sys.platform == "win32" else ["nuitka"]
            return filename.lower() in valid
        table = {
            "pyinstaller": ["pyinstaller.exe", "pyinstaller"],
            "pyarmor": ["pyarmor.exe", "pyarmor"],
            "cython": ["cython.exe", "cython"],
            "msvc": ["cl.exe"],
        }
        valid = table.get(key, [])
        return filename.lower() in valid

    def find_compiler_in_dir(dir_path: Path, key: str) -> str | None:
        if key == "cpp":
            exe_names = [
                "g++.exe", "mingw32-g++.exe", "mingw64-g++.exe", "x86_64-w64-mingw32-g++.exe",
                "clang++.exe", "cl.exe"
            ] if sys.platform == "win32" else [
                "g++", "clang++"
            ]
        elif key == "gcc":
            exe_names = [
                "gcc.exe", "mingw32-gcc.exe", "mingw64-gcc.exe", "x86_64-w64-mingw32-gcc.exe", "clang.exe"
            ] if sys.platform == "win32" else [
                "gcc", "clang"
            ]
        else:
            exe_names = {
                "pyinstaller": ["pyinstaller.exe"] if sys.platform == "win32" else ["pyinstaller"],
                "pyarmor": ["pyarmor.exe"] if sys.platform == "win32" else ["pyarmor"],
                "nuitka": ["nuitka.exe"] if sys.platform == "win32" else ["nuitka"],
                "cython": ["cython.exe"] if sys.platform == "win32" else ["cython"],
            }.get(key, [])
        for exe in exe_names:
            candidate = dir_path / exe
            if candidate.is_file():
                return str(candidate)
        return None

    try:
        if not path_file.exists():
            raise FileNotFoundError(f"{path_file} not found.")

        config = configparser.ConfigParser()
        config.read(path_file, encoding="utf-8")

        if "paths" not in config:
            raise ValueError("Missing [paths] section in extensions_path.ini")

        paths: dict[str, str] = {}
        required_key = "pyinstaller"
        optional_keys = ["pyarmor", "nuitka", "cython", "cpp", "gcc", "tcl_base", "msvc"]

        # Prüfung von pyinstaller (zwingend erforderlich)
        if required_key not in config["paths"]:
            raise ValueError(f"Missing required key: {required_key} in [paths] section")

        value = config["paths"].get(required_key, "").strip()
        if not value:
            raise ValueError(f"Empty path for required key: {required_key}")

        path_obj = Path(value)
        if path_obj.is_file():
            filename = path_obj.name
            if not is_other_tool_exe(filename, required_key):
                raise FileNotFoundError(f"Ungültiger Executable-Dateiname für '{required_key}': {filename}")
            paths[required_key] = str(path_obj)
        elif path_obj.is_dir():
            exe_path = find_compiler_in_dir(path_obj, required_key)
            if not exe_path:
                raise FileNotFoundError(f"Kein passender Executable in '{path_obj}' für Schlüssel '{required_key}' gefunden.")
            paths[required_key] = exe_path
        else:
            raise FileNotFoundError(f"Kein gültiger Pfad/Datei für Schlüssel '{required_key}': {value}")

        # Prüfung der optionalen Schlüssel
        for key in optional_keys:
            if key not in config["paths"]:
                if log_file is not None:
                    log_file.write(f"Warning: Missing key: {key} in [paths] section\n")
                continue

            value = config["paths"].get(key, "").strip()
            if not value:
                if log_file is not None:
                    log_file.write(f"Warning: Empty path for key: {key}\n")
                continue

            try:
                path_obj = Path(value)

                # Tcl-Base immer als Verzeichnis
                if key == "tcl_base":
                    if not path_obj.is_dir():
                        if log_file is not None:
                            log_file.write(f"Warning: Tcl base directory '{value}' not found.\n")
                        continue
                    paths[key] = value
                    continue

                # Direkter Dateipfad
                if path_obj.is_file():
                    filename = path_obj.name
                    valid = False
                    if key == "cpp":
                        valid = is_cpp_exe(filename)
                    elif key == "gcc":
                        valid = is_gcc_exe(filename)
                    else:
                        valid = is_other_tool_exe(filename, key)
                    if not valid:
                        if log_file is not None:
                            log_file.write(f"Warning: Ungültiger Executable-Dateiname für '{key}': {filename}\n")
                        continue
                    paths[key] = str(path_obj)
                    continue

                # Verzeichnis: Compiler/Tool suchen
                if path_obj.is_dir():
                    exe_path = find_compiler_in_dir(path_obj, key)
                    if not tiros:
                        if log_file is not None:
                            log_file.write(f"Warning: Kein passender Executable in '{path_obj}' für Schlüssel '{key}' gefunden.\n")
                        continue
                    paths[key] = exe_path
                    continue

                # Ungültiger Pfad
                if log_file is not None:
                    log_file.write(f"Warning: Kein gültiger Pfad/Datei für Schlüssel '{key}': {value}\n")
                continue

            except Exception as e:
                if log_file is not None:
                    log_file.write(f"Warning: Fehler bei der Verarbeitung von '{key}': {e}\n")
                continue

        if log_file is not None:
            log_file.write(f"Parsed paths: {paths}\n")
            log_file.write("--- load_extensions_paths() SUCCESS ---\n")
            log_file.flush()
        return paths

    except Exception as e:
        if log_file is not None:
            log_file.write(f"Exception in load_extensions_paths: {e}\n")
            log_file.write("--- load_extensions_paths() FAILED ---\n")
            log_file.flush()
        raise
