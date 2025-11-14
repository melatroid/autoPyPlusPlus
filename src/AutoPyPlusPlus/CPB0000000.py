from __future__ import annotations
import subprocess
from pathlib import Path
import sys
import shutil
import shlex
import os

from .project import Project


def log_warning(log_file, msg):
    border = "-" * 50
    log_file.write(f"{border}\n!!! WARNING: {msg}\n{border}\n")
    log_file.flush()


def log_error(log_file, msg):
    border = "-" * 50
    log_file.write(f"{border}\n### ERROR: {msg}\n{border}\n")
    log_file.flush()


def log_info(log_file, msg):
    border = "-" * 50
    log_file.write(f"{border}\n--- INFO: {msg}\n{border}\n")
    log_file.flush()


def _strip_pack_options(args: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "--pack":
            i += 1
            if i < len(args) and args[i] in ("onedir", "onefile"):
                i += 1
            # evtl. Alt-Embed "-e <payload>" konsumieren
            if i < len(args) and args[i] == "-e":
                i += 1
                if i < len(args):
                    i += 1
            continue
        if tok == "-e":
            i += 1  # payload überspringen
            if i < len(args):
                i += 1
            continue

        if tok in ("--onefile", "--onedir", "--windowed", "--console"):
            i += 1
            continue

        if tok in ("--icon", "--distpath", "--workpath", "--specpath"):
            i += 1
            if i < len(args):
                i += 1
            continue

        out.append(tok)
        i += 1
    return out


def _probe_python_and_pyarmor(pyexe: str, log_file) -> bool:
    try:
        p = subprocess.run(
            [pyexe, "-c",
             "import sys,platform; "
             "print(platform.python_version()); "
             "print(platform.architecture()[0]); "
             "print(sys.executable)"],
            capture_output=True, text=True, check=True
        )
        lines = [ln.strip() for ln in (p.stdout or "").splitlines() if ln.strip()]
        if len(lines) >= 3:
            log_info(log_file, f"Python probe → version={lines[0]}, arch={lines[1]}, exe={lines[2]}")
        else:
            log_info(log_file, f"Python probe raw output:\n{p.stdout}")
    except Exception as e:
        log_warning(log_file, f"Python probe failed for {pyexe}: {e}")

    try:
        p = subprocess.run([pyexe, "-m", "pyarmor.cli", "--version"],
                           capture_output=True, text=True, check=True)
        msg = (p.stdout or p.stderr or "").strip()
        log_info(log_file, f"PyArmor --version (module) → {msg}")
        return True
    except subprocess.CalledProcessError as e:
        log_warning(log_file, "PyArmor is not available in this interpreter (python -m pyarmor.cli --version failed).")
        if e.stdout:
            log_warning(log_file, f"STDOUT:\n{e.stdout}")
        if e.stderr:
            log_warning(log_file, f"STDERR:\n{e.stderr}")
        return False
    except Exception as e:
        log_warning(log_file, f"PyArmor module probe raised: {e}")
        return False


class CPB0000000:
    """PyArmor build stage — nur 'gen' (Basic)."""

    @staticmethod
    def run_pyarmor(project: Project, log_file) -> None:
        # 1) Interpreter wählen
        python_exe = getattr(project, "python_exec_path", None)
        if python_exe:
            try:
                python_exe = str(Path(python_exe).resolve())
            except Exception:
                python_exe = str(python_exe)
        if not python_exe or not Path(python_exe).exists():
            if python_exe:
                log_warning(
                    log_file,
                    f"Configured python interpreter does not exist: {python_exe}. "
                    "Falling back to current process interpreter."
                )
            python_exe = sys.executable
        log_info(log_file, f"Selected Python interpreter: {python_exe}")

        # 2) PyArmor probe
        module_ok = _probe_python_and_pyarmor(python_exe, log_file)

        # 3) pyarmor executable fallback
        pyarmor_path = None
        if not module_ok:
            pyarmor_path = getattr(project, "pyarmor_path", None)
            if not pyarmor_path:
                pyarmor_path = shutil.which("pyarmor")
                if pyarmor_path:
                    log_info(log_file, f"Found pyarmor in PATH: {pyarmor_path}")
            if not pyarmor_path:
                log_error(
                    log_file,
                    "PyArmor not found for this build.\n\n"
                    f'Option A) "{python_exe}" -m pip install -U pyarmor\n'
                    "Option B) extension_paths.ini → pyarmor=<full_path>\n"
                    "Option C) Ensure 'pyarmor' is on PATH."
                )
                raise RuntimeError("PyArmor unavailable as module and binary.")

        # 4) base command → IMMER 'gen'
        base_cmd: list[str] = [python_exe, "-m", "pyarmor.cli"] if module_ok else [pyarmor_path]  # type: ignore[arg-type]
        cmd: list[str] = base_cmd + ["gen"]

        # 5) UI-Optionen laden und PACK-Müll rauswerfen
        user_options_raw = project.pyarmor_options or ""
        try:
            user_opts = shlex.split(user_options_raw, posix=False) if user_options_raw else []
        except Exception:
            user_opts = (user_options_raw or "").split()

        sanitized_opts = _strip_pack_options(user_opts)
        if sanitized_opts != user_opts:
            log_info(log_file, "Removed pack/pyinstaller options (forcing pure 'gen').")

        cmd += sanitized_opts

        # 6) Script anhängen
        if project.script:
            script_path = Path(project.script).resolve()
            if script_path.is_file():
                cmd.append(str(script_path))
            else:
                log_error(log_file, f"Script {project.script} not found. Aborting!")
                raise FileNotFoundError(f"Script {project.script} not found.")

        log_info(log_file, f"Running PyArmor command: {' '.join(str(x) for x in cmd)}")

        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            log_info(log_file, f"PyArmor return code: {res.returncode}")
            if res.stdout:
                log_info(log_file, f"STDOUT:\n{res.stdout}")
            if res.stderr:
                log_warning(log_file, f"STDERR:\n{res.stderr}")

            if res.returncode != 0:
                raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout, stderr=res.stderr)
        except subprocess.CalledProcessError as e:
            log_error(log_file, f"PyArmor failed (returncode {e.returncode})")
            if e.output:
                log_error(log_file, f"STDOUT:\n{e.output}")
            if e.stderr:
                log_error(log_file, f"STDERR:\n{e.stderr}")
            raise
        except Exception as e:
            log_error(log_file, f"Unexpected error during PyArmor execution: {str(e)}")
            raise
