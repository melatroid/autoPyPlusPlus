from __future__ import annotations
import subprocess
import sys
import configparser
from .project import Project
from .extension_paths_loader import load_extensions_paths
import shutil
from pathlib import Path

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

def load_paths_config(config_path: Path) -> dict:
    config = configparser.ConfigParser()
    if not config_path.is_file():
        return {}
    config.read(config_path, encoding="utf-8")
    if "paths" in config:
        return dict(config["paths"])
    return {}

class CPA0000000:
    @staticmethod
    def build_command(project: Project, log_file) -> list:

        pyinstaller_path = None

        # Extension-Pfade laden und pyinstaller_path setzen, falls noch nicht gesetzt
        if not hasattr(project, "pyinstaller_path") or not project.pyinstaller_path:
            extensions_paths = load_extensions_paths(log_file)  # log_file übergeben
            pyinstaller_candidate = extensions_paths.get("pyinstaller")  # korrigiert: "pyinstaller" statt "pyinstaller_path"
            if pyinstaller_candidate:
                project.pyinstaller_path = pyinstaller_candidate
                log_info(log_file, f"Set pyinstaller_path from extensions: {pyinstaller_candidate}")

        # 1. Versuch: PyInstaller-Pfad aus Config (oder Extensions) nutzen
        if hasattr(project, "pyinstaller_path") and project.pyinstaller_path:
            candidate = Path(project.pyinstaller_path)
            log_info(log_file, f"DEBUG: Checking candidate path: {candidate}")
            if candidate.is_file():
                pyinstaller_path = str(candidate)
                log_info(log_file, f"DEBUG: Found PyInstaller at: {pyinstaller_path}")
            elif candidate.is_dir():
                exe_name = "pyinstaller.exe" if sys.platform == "win32" else "pyinstaller"
                possible = candidate / exe_name
                if possible.is_file():
                    pyinstaller_path = str(possible)
                    log_info(log_file, f"DEBUG: Found PyInstaller at: {pyinstaller_path}")
                else:
                    log_warning(log_file, f"PyInstaller executable nicht gefunden im Verzeichnis: {candidate}")
            else:
                log_warning(log_file, f"PyInstaller path aus Config ungültig oder nicht gefunden: {project.pyinstaller_path}")

        # 2. Fallback: Suche pyinstaller im PATH
        if not pyinstaller_path:
            log_info(log_file, "DEBUG: Searching PyInstaller in PATH")
            pyinstaller_path = shutil.which("pyinstaller")
            if not pyinstaller_path:
                log_warning(log_file, "PyInstaller nicht im PATH gefunden.")

        # 3. Letzter Fallback: python -m pyinstaller verwenden
        if not pyinstaller_path:
            log_warning(log_file, "Falling back to python -m pyinstaller")
            commands = [sys.executable, "-m", "pyinstaller"]  # Achtung: Modulname klein!
        else:
            commands = [pyinstaller_path]

        sep = ";" if sys.platform == "win32" else ":"

        # Skript validieren
        script = Path(project.script).resolve() if project.script else None
        if not script or not script.is_file():
            log_error(log_file, f"Script {project.script} not found. Aborting!")
            raise FileNotFoundError(f"Script {project.script} not found.")
        commands.append(str(script))

        # PyArmor-Laufzeitbibliothek einbinden
        if project.include_pyarmor_runtime:
            runtime_dir = Path(project.pyarmor_runtime_dir) / "pyarmor_runtime_000000"
            if runtime_dir.is_dir():
                commands.append(f"--add-data={runtime_dir}{sep}pyarmor_runtime_000000")
                log_info(log_file, f"Added PyArmor runtime: {runtime_dir}")
            else:
                log_error(log_file, f"PyArmor runtime not found at {runtime_dir}. Aborting!")
                raise FileNotFoundError(f"PyArmor runtime not found at {runtime_dir}")

        # Name
        if project.name:
            commands.append(f"--name={project.name}")

        # Icon
        if project.icon:
            icon_path = Path(project.icon).resolve()
            if icon_path.is_file():
                commands.append(f"--icon={icon_path}")

        # Add-Data Einträge
        if project.add_data:
            for data_entry in project.add_data.split(";"):
                data_entry = data_entry.strip()
                if not data_entry:
                    continue
                if ":" not in data_entry:
                    log_warning(log_file, f"Invalid add_data entry (missing ':'): {data_entry}")
                    continue
                src, dst = data_entry.split(":", 1)
                src_path = Path(src).resolve()
                if not src_path.exists():
                    log_warning(log_file, f"Add-data src path does not exist: {src_path}")
                    continue
                commands.append(f"--add-data={src_path}{sep}{dst}")

        # Hidden Imports
        if project.hidden_imports:
            for imp in project.hidden_imports.split():
                commands.append(f"--hidden-import={imp}")

        # Version-File
        if project.version:
            version_path = Path(project.version).resolve()
            if version_path.is_file():
                commands.append(f"--version-file={version_path}")

        # Output Ordner
        if project.output:
            output_path = Path(project.output).resolve()
            commands.append(f"--distpath={output_path}")

        # Standard-Optionen
        if project.onefile:
            commands.append("--onefile")
        if not project.console:
            commands.append("--noconsole")
        if project.upx:
            commands.append("--upx-dir=upx")
        if project.debug:
            commands.append("--debug=all")
        if project.clean:
            commands.append("--clean")
        if project.strip:
            commands.append("--strip")

        # Runtime-Hook
        if project.runtime_hook:
            hook_path = Path(project.runtime_hook).resolve()
            if hook_path.is_file():
                commands.append(f"--runtime-hook={hook_path}")

        # Splash
        if project.splash:
            splash_path = Path(project.splash).resolve()
            if splash_path.is_file():
                commands.append(f"--splash={splash_path}")

        # Spec-File
        if project.spec_file:
            spec_path = Path(project.spec_file).resolve()
            if spec_path.is_file():
                commands.append(f"--specpath={spec_path}")

        # Weitere Optionen
        if project.options:
            commands.extend(project.options.split())

        return commands

    @staticmethod
    def run_pyinstaller(project: Project, log_file) -> None:
        log_info(log_file, f"Running PyInstaller for {project.name or project.script}")
        commands = CPA0000000.build_command(project, log_file)
        final_cmd = subprocess.list2cmdline(commands)
        log_info(log_file, f"PyInstaller command: {final_cmd}")
        try:
            result = subprocess.run(
                commands,
                check=True,
                text=True,
                capture_output=True,
                timeout=600,
            )
            log_info(log_file, f"PyInstaller stdout: {result.stdout}")
            log_info(log_file, f"PyInstaller stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            log_error(log_file, "PyInstaller timed out after 600 seconds")
            raise
        except subprocess.CalledProcessError as e:
            log_error(log_file, f"PyInstaller failed: {e}")
            log_error(log_file, f"PyInstaller stderr: {e.stderr}")
            raise
