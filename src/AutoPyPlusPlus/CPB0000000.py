from __future__ import annotations
import subprocess
from pathlib import Path
import sys
import shutil
import shlex

from .project import Project
from .extension_paths_loader import load_extensions_paths


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


def _strip_pack_args_for_gen(args: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "--pack":
            i += 1
            if i < len(args) and args[i] in ("onedir", "onefile"):
                i += 1
                continue
            if i < len(args) and args[i] == "-e":
                i += 1
                if i < len(args):
                    i += 1
                continue
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
    """PyArmor build stage."""

    @staticmethod
    def run_pyarmor(project: Project, log_file) -> None:
        # 1) Interpreter wählen (GUI speichert 'python_exec_path')
        python_exe = getattr(project, "python_exec_path", None)
        if python_exe:
            try:
                python_exe = str(Path(python_exe).resolve())
            except Exception:
                # falls Pfad komisch ist, einfach als String lassen
                python_exe = str(python_exe)
        if not python_exe or not Path(python_exe).exists():
            if python_exe:
                log_warning(log_file, f"Configured python interpreter does not exist: {python_exe}. "
                                      "Falling back to current process interpreter.")
            python_exe = sys.executable

        log_info(log_file, f"Selected Python interpreter: {python_exe}")

        # 2) Prüfen, ob PyArmor als Modul in DIESEM Interpreter verfügbar ist
        module_ok = _probe_python_and_pyarmor(python_exe, log_file)

        # 3) PyArmor-Binary suchen, falls Modul nicht ok
        pyarmor_path = None
        if not module_ok:
            pyarmor_path = getattr(project, "pyarmor_path", None)
            if not pyarmor_path:
                ex_paths = load_extensions_paths(log_file)
                cand = ex_paths.get("pyarmor")
                if cand:
                    pyarmor_path = cand
                    setattr(project, "pyarmor_path", cand)
                    log_info(log_file, f"Set pyarmor_path from extensions: {cand}")
            if not pyarmor_path:
                pyarmor_path = shutil.which("pyarmor")
                if pyarmor_path:
                    log_info(log_file, f"Found pyarmor in PATH: {pyarmor_path}")

            if not pyarmor_path:
                log_error(
                    log_file,
                    "PyArmor not found for this build.\n\n"
                    "Option A) Install PyArmor into the selected interpreter:\n"
                    f'   "{python_exe}" -m pip install -U pyarmor\n\n'
                    "Option B) Provide a pyarmor executable path "
                    "(extension_paths.ini → pyarmor=<full_path>)\n"
                    "Option C) Ensure 'pyarmor' is on PATH."
                )
                raise RuntimeError("PyArmor unavailable as module and binary.")

        # 4) Kommando aufbauen
        if module_ok:
            cmd: list[str] = [python_exe, "-m", "pyarmor.cli"]
        else:
            cmd = [pyarmor_path]  # type: ignore[arg-type]

        command = (project.pyarmor_command or "gen").strip()
        cmd.append(command)

        if project.pyarmor_options:
            try:
                opts = shlex.split(project.pyarmor_options, posix=False)
            except Exception:
                opts = project.pyarmor_options.split()
            cmd.extend(opts)

        if project.script:
            script_path = Path(project.script).resolve()
            if script_path.is_file():
                cmd.append(str(script_path))
            else:
                log_error(log_file, f"Script {project.script} not found. Aborting!")
                raise FileNotFoundError(f"Script {project.script} not found.")

        # 5) Pack-Args bei 'gen' entfernen
        if command == "gen":
            before = " ".join(str(x) for x in cmd)
            if module_ok:
                base = cmd[:4]  # [python, -m, pyarmor.cli, 'gen']
            else:
                base = cmd[:2]  # [pyarmor, 'gen']
            tail_script = cmd[-1:] if project.script else []
            opts_only = cmd[len(base):len(cmd) - (1 if project.script else 0)]
            cleaned = _strip_pack_args_for_gen(opts_only)
            cmd = base + cleaned + tail_script
            after = " ".join(str(x) for x in cmd)
            if before != after:
                log_info(log_file, "Sanitized pack options for 'gen' (removed --pack …).")
                log_info(log_file, f"Before: {before}")
                log_info(log_file, f"After : {after}")

        log_info(log_file, f"Running PyArmor command: {' '.join(str(x) for x in cmd)}")

        # 6) Ausführen (immer Logs)
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