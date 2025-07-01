from __future__ import annotations
import subprocess
from pathlib import Path
import sys
import shutil

from .project import Project
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

class CPB0000000:
    """Klasse für die PyArmor-Kompilierstufe."""

    @staticmethod
    def run_pyarmor(project: Project, log_file) -> None:
        # 1. Fallback: Expliziter Pfad aus Project-Attribut nehmen
        pyarmor_path = getattr(project, "pyarmor_path", None)

        # 2. Fallback: Aus extension_paths.ini laden, falls nötig
        if not pyarmor_path:
            extensions_paths = load_extensions_paths(log_file)
            pyarmor_candidate = extensions_paths.get("pyarmor")
            if pyarmor_candidate:
                pyarmor_path = pyarmor_candidate
                setattr(project, "pyarmor_path", pyarmor_candidate)
                log_info(log_file, f"Set pyarmor_path from extensions: {pyarmor_candidate}")

        # 3. Fallback: Im PATH suchen
        if not pyarmor_path:
            pyarmor_path = shutil.which("pyarmor")
            if pyarmor_path:
                log_info(log_file, f"Found pyarmor in PATH: {pyarmor_path}")

        # 4. Fallback: python -m pyarmor verwenden
        pyarmor_cmd = []
        if pyarmor_path:
            pyarmor_cmd.append(pyarmor_path)
        else:
            log_warning(log_file, "Falling back to python -m pyarmor")
            pyarmor_cmd = [sys.executable, "-m", "pyarmor"]

        # Befehl (gen, pack, obfuscate …)
        pyarmor_cmd.append(project.pyarmor_command or "gen")

        # Alle Optionen aus dem Editor (inkl. --output, --no-runtime-key etc.)
        if project.pyarmor_options:
            pyarmor_cmd.extend(project.pyarmor_options.split())

        # Skript (muss zuletzt stehen)
        if project.script:
            script_path = Path(project.script).resolve()
            if script_path.is_file():
                pyarmor_cmd.append(str(script_path))
            else:
                log_error(log_file, f"Script {project.script} not found. Aborting!")
                raise FileNotFoundError(f"Script {project.script} not found.")

        log_info(log_file, f"Running PyArmor command: {' '.join(str(x) for x in pyarmor_cmd)}")

        try:
            result = subprocess.run(pyarmor_cmd, capture_output=True, text=True, check=True)
            log_info(log_file, result.stdout)
            if result.stderr:
                log_warning(log_file, result.stderr)
        except subprocess.CalledProcessError as e:
            log_error(log_file, f"PyArmor failed: {e.stderr}")
            raise
        except Exception as e:
            log_error(log_file, f"Unexpected error during PyArmor execution: {str(e)}")
            raise
