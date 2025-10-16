from __future__ import annotations
import subprocess
import sys
import configparser
from .project import Project
from .extension_paths_loader import load_extensions_paths
import shutil
from pathlib import Path
import re
import os


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


# ---------------------- Add-Data Parser ----------------------

def _iter_add_data_pairs(add_data_raw: str):
    """
    Robuster Parser für add_data.
    Akzeptiert:
        - Trennung per ';' oder Zeilenumbruch
        - src:dst (internes Format)
        - src;dst (Windows-Format)
        - Nur src -> automatisch dst = basename(src)
    """
    if not add_data_raw:
        return
    for token in re.split(r"[;\r\n]+", str(add_data_raw)):
        t = token.strip().strip('"').strip("'")
        if not t:
            continue

        src, dst = None, None
        # Am letzten ':' trennen, aber C:\... erhalten
        if ":" in t and not t.endswith(":"):
            parts = t.rsplit(":", 1)
            src, dst = parts[0].strip(), parts[1].strip()
        elif ";" in t:
            parts = t.split(";", 1)
            src, dst = parts[0].strip(), parts[1].strip()
        else:
            src, dst = t, Path(t).name or "."

        if src and dst:
            yield os.path.normpath(src), dst.strip()


class CPA0000000:
    @staticmethod
    def _resolve_pyarmor_runtime(base_or_runtime: str, log_file) -> Path:
        """
        Returns the actual 'pyarmor_runtime_*' directory.
        Accepts either the runtime folder itself or a parent folder.
        Picks the most recently modified if multiple exist.
        Raises FileNotFoundError if none found.
        """
        if not base_or_runtime:
            raise FileNotFoundError("PyArmor runtime path not provided.")
        p = Path(base_or_runtime)

        # User provided the runtime folder directly
        if p.is_dir() and p.name.startswith("pyarmor_runtime_"):
            return p

        # User provided a parent folder; search within it
        if p.is_dir():
            candidates = [d for d in p.glob("pyarmor_runtime_*") if d.is_dir()]
            if candidates:
                candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return candidates[0]

        raise FileNotFoundError(
            f"PyArmor runtime not found in/under: {base_or_runtime} "
            f"(expected a folder named 'pyarmor_runtime_*')."
        )

    @staticmethod
    def build_command(project: Project, log_file) -> list:
        pyinstaller_path = None

        # Load extension paths and set pyinstaller_path if missing
        if not getattr(project, "pyinstaller_path", None):
            extensions_paths = load_extensions_paths(log_file)
            pyinstaller_candidate = extensions_paths.get("pyinstaller")
            if pyinstaller_candidate:
                project.pyinstaller_path = pyinstaller_candidate
                log_info(log_file, f"Set pyinstaller_path from extensions: {pyinstaller_candidate}")

        # 1) Try configured/extension path
        if getattr(project, "pyinstaller_path", None):
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
                    log_warning(log_file, f"PyInstaller executable not found in directory: {candidate}")
            else:
                log_warning(log_file, f"Configured PyInstaller path invalid/not found: {project.pyinstaller_path}")

        # 2) Fallback: PATH
        if not pyinstaller_path:
            log_info(log_file, "DEBUG: Searching PyInstaller in PATH")
            pyinstaller_path = shutil.which("pyinstaller")
            if not pyinstaller_path:
                log_warning(log_file, "PyInstaller not found in PATH.")

        # 2.5) NEW: Probe Scripts next to the active python.exe
        if not pyinstaller_path:
            scripts_dir = Path(sys.executable).with_name("Scripts")
            exe_name = "pyinstaller.exe" if sys.platform == "win32" else "pyinstaller"
            possible2 = scripts_dir / exe_name
            log_info(log_file, f"DEBUG: Probing {possible2}")
            if possible2.is_file():
                pyinstaller_path = str(possible2)
                log_info(log_file, f"DEBUG: Found PyInstaller at: {pyinstaller_path}")

        # 3) Final fallback: python -m PyInstaller  (capital P!)
        if not pyinstaller_path:
            log_warning(log_file, "Falling back to python -m PyInstaller")
            commands = [sys.executable, "-m", "PyInstaller"]
        else:
            commands = [pyinstaller_path]

        sep = ";" if sys.platform == "win32" else ":"

        # Script validation
        script = Path(project.script).resolve() if project.script else None
        if not script or not script.is_file():
            log_error(log_file, f"Script {project.script} not found. Aborting!")
            raise FileNotFoundError(f"Script {project.script} not found.")
        commands.append(str(script))

        # Include PyArmor runtime
        if getattr(project, "include_pyarmor_runtime", False):
            try:
                runtime_dir = CPA0000000._resolve_pyarmor_runtime(
                    getattr(project, "pyarmor_runtime_dir", ""), log_file
                )
                mapping = f"{runtime_dir}{sep}pyarmor_runtime"
                commands.append(f"--add-data={mapping}")
                log_info(log_file, f"Added PyArmor runtime: {runtime_dir} -> pyarmor_runtime")
            except FileNotFoundError as e:
                log_error(log_file, f"{e} Aborting!")
                raise

        # Name
        if project.name:
            commands.append(f"--name={project.name}")

        # Icon
        if project.icon:
            icon_path = Path(project.icon).resolve()
            if icon_path.is_file():
                commands.append(f"--icon={icon_path}")

        # Add-data
        if project.add_data:
            seen = set()
            for src, dst in _iter_add_data_pairs(project.add_data):
                src_path = Path(src).resolve()
                if not src_path.exists():
                    log_warning(log_file, f"Add-data src path does not exist: {src_path}")
                    continue
                key = (str(src_path), dst)
                if key in seen:
                    continue
                seen.add(key)
                commands.append(f"--add-data={src_path}{sep}{dst}")
                log_info(log_file, f"Added data mapping: {src_path} -> {dst}")

        # Hidden imports
        if project.hidden_imports:
            for imp in project.hidden_imports.split():
                commands.append(f"--hidden-import={imp}")

        # Version file
        if project.version:
            version_path = Path(project.version).resolve()
            if version_path.is_file():
                commands.append(f"--version-file={version_path}")

        # Output folder
        if project.output:
            output_path = Path(project.output).resolve()
            commands.append(f"--distpath={output_path}")

        # Standard options
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

        # Runtime hook (optional)
        if project.runtime_hook:
            hook_path = Path(project.runtime_hook).resolve()
            if hook_path.is_file():
                commands.append(f"--runtime-hook={hook_path}")

        # Splash
        if project.splash:
            splash_path = Path(project.splash).resolve()
            if splash_path.is_file():
                commands.append(f"--splash={splash_path}")

        # Spec file
        if project.spec_file:
            spec_path = Path(project.spec_file).resolve()
            if spec_path.is_file():
                commands.append(f"--specpath={spec_path.parent}")
            elif spec_path.is_dir():
                commands.append(f"--specpath={spec_path}")

        # Additional options
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
