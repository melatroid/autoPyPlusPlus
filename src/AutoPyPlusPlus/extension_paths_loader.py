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

    def is_executable_path(path_obj: Path, key: str) -> bool:
        if path_obj.is_file():
            return True
        if path_obj.is_dir():
            if key == "cpp":
                exe_names = [
                    "g++.exe",
                    "mingw32-g++.exe",
                    "mingw64-g++.exe",
                    "x86_64-w64-mingw32-g++.exe",
                    "clang++.exe",
                    "cl.exe",
                ] if sys.platform == "win32" else [
                    "g++",
                    "clang++",
                ]
                for exe_name in exe_names:
                    candidate = path_obj / exe_name
                    if candidate.is_file():
                        return True
            elif key == "gcc":
                exe_names = [
                    "gcc.exe",
                    "mingw32-gcc.exe",
                    "mingw64-gcc.exe",
                    "x86_64-w64-mingw32-gcc.exe",
                    "clang.exe",
                ] if sys.platform == "win32" else [
                    "gcc",
                    "clang",
                ]
                for exe_name in exe_names:
                    candidate = path_obj / exe_name
                    if candidate.is_file():
                        return True
            else:
                exe_names = {
                    "pyinstaller": ["pyinstaller.exe"] if sys.platform == "win32" else ["pyinstaller"],
                    "pyarmor": ["pyarmor.exe"] if sys.platform == "win32" else ["pyarmor"],
                    "nuitka": ["nuitka.exe"] if sys.platform == "win32" else ["nuitka"],
                    "cython": ["cython.exe"] if sys.platform == "win32" else ["cython"],
                }.get(key, [])
                for exe_name in exe_names:
                    candidate = path_obj / exe_name
                    if candidate.is_file():
                        return True
        return False

    try:
        if not path_file.exists():
            raise FileNotFoundError(f"{path_file} not found.")

        config = configparser.ConfigParser()
        config.read(path_file, encoding="utf-8")

        if "paths" not in config:
            raise ValueError("Missing [paths] section in extensions_path.ini")

        paths: dict[str, str] = {}
        required_keys = ["pyinstaller", "pyarmor", "nuitka", "cython", "cpp", "gcc", "tcl_base"]

        for key in required_keys:
            if key not in config["paths"]:
                raise ValueError(f"Missing key: {key} in [paths] section")

            value = config["paths"].get(key, "").strip()
            if not value:
                raise ValueError(f"Empty path for key: {key}")

            path_obj = Path(value)
            if key == "tcl_base":
                if not path_obj.is_dir():
                    raise FileNotFoundError(f"Tcl base directory '{value}' not found.")
                paths[key] = value
            else:
                if not is_executable_path(path_obj, key):
                    raise FileNotFoundError(f"Executable or file '{value}' for key '{key}' not found.")
                if path_obj.is_dir():
                    if key == "cpp":
                        exe_names = [
                            "g++.exe",
                            "mingw32-g++.exe",
                            "mingw64-g++.exe",
                            "x86_64-w64-mingw32-g++.exe",
                            "clang++.exe",
                            "cl.exe",
                        ] if sys.platform == "win32" else [
                            "g++",
                            "clang++",
                        ]
                        for exe_name in exe_names:
                            candidate = path_obj / exe_name
                            if candidate.is_file():
                                value = str(candidate)
                                break
                        else:
                            raise FileNotFoundError(f"Kein bekannter Compiler in '{path_obj}' für Schlüssel '{key}' gefunden.")
                    elif key == "gcc":
                        exe_names = [
                            "gcc.exe",
                            "mingw32-gcc.exe",
                            "mingw64-gcc.exe",
                            "x86_64-w64-mingw32-gcc.exe",
                            "clang.exe",
                        ] if sys.platform == "win32" else [
                            "gcc",
                            "clang",
                        ]
                        for exe_name in exe_names:
                            candidate = path_obj / exe_name
                            if candidate.is_file():
                                value = str(candidate)
                                break
                        else:
                            raise FileNotFoundError(f"Kein bekannter C-Compiler in '{path_obj}' für Schlüssel '{key}' gefunden.")
                    else:
                        exe_names = {
                            "pyinstaller": "pyinstaller.exe" if sys.platform == "win32" else "pyinstaller",
                            "pyarmor": "pyarmor.exe" if sys.platform == "win32" else "pyarmor",
                            "nuitka": "nuitka.exe" if sys.platform == "win32" else "nuitka",
                            "cython": "cython.exe" if sys.platform == "win32" else "cython",
                        }
                        exe_name = exe_names.get(key)
                        value = str(path_obj / exe_name)
                paths[key] = value

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
