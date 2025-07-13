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

class CPD0000000:
    """Kompilierklasse für Cython."""

    @staticmethod
    def run_cython(project, log_file) -> None:
        if not project.script:
            log_error(log_file, "Kein Skript angegeben.")
            raise ValueError("Kein Skript angegeben.")

        script_path = Path(project.script).resolve()
        if not script_path.is_file():
            log_error(log_file, f"Skript {project.script} nicht gefunden.")
            raise FileNotFoundError(f"Skript {project.script} nicht gefunden.")

        # Zielverzeichnis für Ausgabe bestimmen
        output_dir = project.cython_output_dir or str(script_path.parent)

        # 1. Expliziter Pfad im Project
        cython_path = getattr(project, "cython_path", None)

        # 2. extension_paths.ini
        if not cython_path:
            extensions_paths = load_extensions_paths(log_file)
            cython_candidate = extensions_paths.get("cython")
            if cython_candidate:
                cython_path = cython_candidate
                setattr(project, "cython_path", cython_candidate)
                log_info(log_file, f"Set cython_path from extensions: {cython_candidate}")

        # 3. Im PATH suchen
        if not cython_path:
            cython_path = shutil.which("cython")
            if cython_path:
                log_info(log_file, f"Found cython in PATH: {cython_path}")

        # 4. python -m cython fallback
        if cython_path:
            cython_cmd = [cython_path]
        else:
            log_warning(log_file, "Falling back to python -m cython")
            cython_cmd = [sys.executable, "-m", "cython"]

        # Direktiv-Optionen
        directives = []
        if project.cython_boundscheck:
            directives.append("boundscheck=True")
        if project.cython_wraparound:
            directives.append("wraparound=True")
        if project.cython_nonecheck:
            directives.append("nonecheck=True")
        if not project.cython_cdivision:
            directives.append("cdivision=False")
        if getattr(project, "cython_initializedcheck", False):
            directives.append("initializedcheck=True")
        if getattr(project, "cython_profile", False):
            directives.append("profile=True")
        if getattr(project, "cython_linemap", False):
            directives.append("linetrace=True")
        if getattr(project, "cython_gdb", False):
            directives.append("gdb_debug=True")
        if getattr(project, "cython_embedsignature", False):
            directives.append("embedsignature=True")
        if getattr(project, "cython_cplus_exceptions", False):
            directives.append("cplus_exceptions=True")
        if getattr(project, "cython_cpp_locals", False):
            directives.append("cpp_locals=True")
        if getattr(project, "cython_annotate", False):
            cython_cmd.append("--annotate")
        if getattr(project, "cython_language_level", None):
            directives.append(f"language_level={project.cython_language_level}")

        # Custom directives
        if getattr(project, "cython_directives", None):
            for k, v in project.cython_directives.items():
                directives.append(f"{k}={v}")

        # Direktiven als Option übergeben
        if directives:
            cython_cmd.append("--directive=" + ",".join(directives))

        # Include-Dirs
        if getattr(project, "cython_include_dirs", None):
            for inc in project.cython_include_dirs:
                cython_cmd.extend(["-I", inc])

        # Compile-Time Env
        if getattr(project, "cython_compile_time_env", None):
            for k, v in project.cython_compile_time_env.items():
                cython_cmd.append(f"--compile-time-env={k}={v}")

        # Sprache (C oder C++)
        if getattr(project, "cython_language", "c") in ("cpp", "c++"):
            cython_cmd.append("--cplus")
            output_file = Path(output_dir) / (script_path.stem + ".cpp")
        else:
            output_file = Path(output_dir) / (script_path.stem + ".c")

        if str(getattr(project, "cython_target_type", "")).lower() in ["standalone exe", "standalone", "exe"]:
            cython_cmd.append("--embed")
            log_info(log_file, "Setze --embed, da Standalone EXE als Ziel ausgewählt ist.")

        # Ausgabeverzeichnis setzen
        cython_cmd.extend(["-o", str(output_file)])

        # Zu kompilierende Datei
        cython_cmd.append(str(script_path))

        log_info(log_file, "Cython-Befehl wird ausgeführt:")
        log_info(log_file, " ".join(map(str, cython_cmd)))

        try:
            result = subprocess.run(
                cython_cmd,
                cwd=str(script_path.parent),
                capture_output=True,
                text=True,
                check=True
            )
            log_info(log_file, result.stdout)
            if result.stderr:
                log_warning(log_file, result.stderr)
        except subprocess.CalledProcessError as e:
            log_error(log_file, "Cython failed:")
            log_error(log_file, e.stdout)
            log_error(log_file, e.stderr)
            raise
        except Exception as e:
            log_error(log_file, f"Unerwarteter Fehler bei der Cython-Ausführung: {e}")
            raise

        # Build (gcc oder setup.py)
        try:
            setup_path = Path(script_path.parent) / "setup.py"
            if setup_path.is_file() and getattr(project, "cython_build_with_setup", True):
                build_cmd = [sys.executable, str(setup_path), "build_ext", "--inplace"]
                log_info(log_file, f"Starte Build mit setup.py: {' '.join(build_cmd)}")
                build_result = subprocess.run(
                    build_cmd,
                    cwd=str(script_path.parent),
                    capture_output=True,
                    text=True,
                    check=True
                )
                log_info(log_file, build_result.stdout)
                if build_result.stderr:
                    log_warning(log_file, build_result.stderr)
            else:
                log_warning(log_file, "Kein setup.py gefunden oder build_with_setup deaktiviert, kein automatischer Build der .so/.pyd-Datei!")
        except Exception as e:
            log_error(log_file, f"Build-Fehler: {e}")

        if not getattr(project, "cython_keep_pyx", True):
            try:
                script_path.unlink()
                log_info(log_file, f"Quelldatei {script_path} gelöscht (cython_keep_pyx=False).")
            except Exception as e:
                log_warning(log_file, f"Fehler beim Löschen der .pyx-Datei: {e}")

        log_info(log_file, f"Fertig. Cython-Kompilierung für {script_path} abgeschlossen.")
