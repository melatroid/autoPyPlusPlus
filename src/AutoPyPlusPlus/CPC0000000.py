import subprocess
import sys
from pathlib import Path
import shutil

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

class CPC0000000:
    """Kompilierklasse für Nuitka."""

    @staticmethod
    def run_nuitka(project, log_file) -> None:
        if not project.script:
            log_error(log_file, "Kein Skript angegeben.")
            raise ValueError("Kein Skript angegeben.")

        script_path = Path(project.script).resolve()
        if not script_path.is_file():
            log_error(log_file, f"Skript {project.script} nicht gefunden.")
            raise FileNotFoundError(f"Skript {project.script} nicht gefunden.")

        # 1. Fallback: Pfad im Projekt
        nuitka_path = getattr(project, "nuitka_path", None)

        # 2. Fallback: extension_paths.ini
        if not nuitka_path:
            extensions_paths = load_extensions_paths(log_file)
            nuitka_candidate = extensions_paths.get("nuitka")
            if nuitka_candidate:
                nuitka_path = nuitka_candidate
                setattr(project, "nuitka_path", nuitka_candidate)
                log_info(log_file, f"Set nuitka_path from extensions: {nuitka_candidate}")

        # 3. Fallback: PATH
        if not nuitka_path:
            nuitka_path = shutil.which("nuitka")
            if nuitka_path:
                log_info(log_file, f"Found nuitka in PATH: {nuitka_path}")

        # 4. Fallback: python -m nuitka
        if nuitka_path:
            nuitka_cmd = [nuitka_path]
        else:
            log_warning(log_file, "Falling back to python -m nuitka")
            nuitka_cmd = [sys.executable, "-m", "nuitka"]

        # Optionen wie gehabt:
        if project.nuitka_standalone:
            nuitka_cmd.append("--standalone")
        if project.nuitka_onefile:
            nuitka_cmd.append("--onefile")
        if project.nuitka_output_dir:
            output_dir = str(Path(project.nuitka_output_dir).resolve())
            nuitka_cmd.append(f"--output-dir={output_dir}")
        else:
            output_dir = str(script_path.parent)

        if project.nuitka_follow_imports:
            nuitka_cmd.append("--follow-imports")
        if project.nuitka_follow_stdlib:
            nuitka_cmd.append("--follow-stdlib")

        plugins_list = []
        if project.nuitka_plugins:
            plugins_list = [p.strip() for p in project.nuitka_plugins.split(",") if p.strip()]

        if getattr(project, "nuitka_tkinter_plugin", False):
            if not any(p == "--enable-plugin=tk-inter" or p == "tk-inter" for p in plugins_list):
                plugins_list.append("--enable-plugin=tk-inter")

        for plugin in plugins_list:
            if plugin.startswith("--enable-plugin="):
                nuitka_cmd.append(plugin)
            else:
                nuitka_cmd.append(f"--enable-plugin={plugin}")

        if project.nuitka_lto:
            nuitka_cmd.append(f"--lto={project.nuitka_lto}")
        if getattr(project, "nuitka_jobs", 1) > 1:
            nuitka_cmd.append(f"--jobs={project.nuitka_jobs}")

        if project.nuitka_show_progress:
            nuitka_cmd.append("--show-progress")
        if project.nuitka_show_memory:
            nuitka_cmd.append("--show-memory")
        if project.nuitka_show_scons:
            nuitka_cmd.append("--show-scons")
        if project.nuitka_windows_uac_admin:
            nuitka_cmd.append("--windows-uac-admin")
        if project.nuitka_windows_icon:
            nuitka_cmd.append(f"--windows-icon-from-ico={project.nuitka_windows_icon}")
        if project.nuitka_windows_splash:
            nuitka_cmd.append(f"--windows-splash-screen={project.nuitka_windows_splash}")

        if project.nuitka_extra_opts:
            nuitka_cmd.extend(project.nuitka_extra_opts.split())

        # Letzter Parameter ist das Skript selbst
        nuitka_cmd.append(str(script_path))

        # Logging
        log_info(log_file, "Nuitka-Befehl wird ausgeführt:")
        log_info(log_file, " ".join(nuitka_cmd))

        try:
            result = subprocess.run(
                nuitka_cmd,
                cwd=str(script_path.parent),  # Arbeitsverzeichnis setzen
                capture_output=True,
                text=True,
                check=True
            )
            log_info(log_file, result.stdout)
            if result.stderr:
                log_warning(log_file, result.stderr)
        except subprocess.CalledProcessError as e:
            log_error(log_file, "Nuitka failed:")
            log_error(log_file, e.stdout)
            log_error(log_file, e.stderr)
            raise
        except Exception as e:
            log_error(log_file, f"Unerwarteter Fehler bei der Nuitka-Ausführung: {e}")
            raise

        # Optional: nuitka-run.bat starten (z. B. bei Standalone-Builds ohne Onefile)
        nuitka_run_path = Path(output_dir) / "nuitka-run.bat"
        if nuitka_run_path.is_file():
            try:
                log_info(log_file, f"Starte nuitka-run: {nuitka_run_path}")
                run_result = subprocess.run(
                    [str(nuitka_run_path)],
                    cwd=output_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                log_info(log_file, run_result.stdout)
                if run_result.stderr:
                    log_warning(log_file, run_result.stderr)
            except Exception as e:
                log_error(log_file, f"Fehler beim Start von nuitka-run.bat: {e}")
        else:
            log_info(log_file, f"nuitka-run.bat nicht gefunden. Eventuell durch Onefile-Modus erwartet.")

        # Abschließend: Hinweis auf EXE
        if project.nuitka_onefile:
            exe_name = script_path.stem + ".exe"
            exe_path = Path(output_dir) / exe_name
            log_info(log_file, f"Fertig. EXE-Datei (Onefile): {exe_path}")
        else:
            dist_dir = Path(output_dir) / script_path.stem
            log_info(log_file, f"Fertig. Ordner mit EXE: {dist_dir}")
