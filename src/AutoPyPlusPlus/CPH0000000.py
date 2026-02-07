from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path
import shlex

from .extension_paths_loader import load_extensions_paths
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


def _format_cmd(cmd: list[str]) -> str:
    """Schöne Darstellung für Logs (mit korrektem Quoting)."""
    if os.name == "nt":
        return subprocess.list2cmdline(list(map(str, cmd)))
    return shlex.join(list(map(str, cmd)))


class CPH0000000:
    """
    MicroPython mpy-cross Stage.

    Erwartete Project-Felder (alles optional, außer script/dir):
      - script: str                           # einzelne .py Datei
      - mpy_compile_dir: str | None           # falls gesetzt: alle .py rekursiv kompilieren
      - mpy_output_dir: str | None            # Output-Ordner (Default: neben Script)
      - mpy_cross_path: str | None            # expliziter Pfad zu mpy-cross / mpy-cross.exe
      - mpy_arch: str | None                  # z.B. "xtensa", "armv6m", "armv7m", "rv32imc" (wird zu -march=...)
      - mpy_opt: int | None                   # 0..3 -> -O0..-O3
      - mpy_extra_opts: str | None            # weitere Flags als String, z.B. "--emit-llvm" (wenn unterstützt)
      - mpy_exclude_glob: str | None          # z.B. "tests/*" bei compile_dir
    """

    @staticmethod
    def _resolve_mpy_cross(project: Project, log_file) -> str:
        # 1) Explizit im Project
        mpy = getattr(project, "mpy_cross_path", None)
        if mpy:
            p = Path(str(mpy)).expanduser()
            if p.is_dir():
                exe = "mpy-cross.exe" if sys.platform == "win32" else "mpy-cross"
                cand = p / exe
                if cand.is_file():
                    log_info(log_file, f"Found mpy-cross in directory: {cand}")
                    return str(cand)
            if p.is_file():
                log_info(log_file, f"Using configured mpy-cross: {p}")
                return str(p)
            log_warning(log_file, f"Configured mpy_cross_path invalid/not found: {mpy}")

        # 2) extension_paths.ini
        extensions_paths = load_extensions_paths(log_file)
        cand = extensions_paths.get("mpy-cross") or extensions_paths.get("mpycross")
        if cand:
            p = Path(str(cand)).expanduser()
            if p.is_dir():
                exe = "mpy-cross.exe" if sys.platform == "win32" else "mpy-cross"
                q = p / exe
                if q.is_file():
                    log_info(log_file, f"Set mpy-cross from extensions dir: {q}")
                    return str(q)
            if p.is_file():
                log_info(log_file, f"Set mpy-cross from extensions: {p}")
                return str(p)
            log_warning(log_file, f"extensions_paths mpy-cross invalid: {cand}")

        # 3) PATH
        which = shutil.which("mpy-cross")
        if which:
            log_info(log_file, f"Found mpy-cross in PATH: {which}")
            return which

        log_error(
            log_file,
            "mpy-cross not found.\n"
            "Option A) Set project.mpy_cross_path\n"
            "Option B) extension_paths.ini -> mpy-cross=<full_path>\n"
            "Option C) Put mpy-cross on PATH"
        )
        raise FileNotFoundError("mpy-cross not found.")

    @staticmethod
    def _iter_sources(project: Project, log_file):
        # compile_dir hat Vorrang, sonst project.script
        compile_dir = getattr(project, "mpy_compile_dir", None)
        exclude_glob = getattr(project, "mpy_exclude_glob", None)

        if compile_dir:
            base = Path(str(compile_dir)).resolve()
            if not base.exists():
                log_error(log_file, f"mpy_compile_dir not found: {base}")
                raise FileNotFoundError(f"mpy_compile_dir not found: {base}")
            if not base.is_dir():
                log_error(log_file, f"mpy_compile_dir is not a directory: {base}")
                raise NotADirectoryError(f"mpy_compile_dir is not a directory: {base}")

            for py in base.rglob("*.py"):
                if exclude_glob and py.match(exclude_glob):
                    continue
                yield py, base
            return

        script = getattr(project, "script", None)
        if not script:
            log_error(log_file, "No project.script provided and no mpy_compile_dir set.")
            raise ValueError("No input specified for mpy-cross stage.")

        p = Path(str(script)).resolve()
        if not p.is_file():
            log_error(log_file, f"Script not found: {p}")
            raise FileNotFoundError(f"Script not found: {p}")

        yield p, p.parent

    @staticmethod
    def run_mpycross(project: Project, log_file) -> None:
        mpy_cross = CPH0000000._resolve_mpy_cross(project, log_file)

        # Output dir bestimmen
        out_dir_raw = getattr(project, "mpy_output_dir", None)
        out_dir = Path(str(out_dir_raw)).resolve() if out_dir_raw else None

        arch = getattr(project, "mpy_arch", None)
        opt = getattr(project, "mpy_opt", None)
        extra = getattr(project, "mpy_extra_opts", None) or ""

        # extra opts robust splitten
        try:
            extra_opts = shlex.split(extra, posix=(os.name != "nt")) if extra else []
        except Exception:
            extra_opts = extra.split() if extra else []

        compiled = 0

        for src, base_dir in CPH0000000._iter_sources(project, log_file):
            # default output: neben src oder in output_dir (mit Struktur)
            if out_dir:
                rel = src.relative_to(base_dir)
                target_path = (out_dir / rel).with_suffix(".mpy")
                target_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                target_path = src.with_suffix(".mpy")

            cmd: list[str] = [mpy_cross]

            if arch:
                cmd.append(f"-march={arch}")

            if isinstance(opt, int):
                # mpy-cross akzeptiert üblicherweise -O0..-O3
                cmd.append(f"-O{max(0, min(3, opt))}")

            # Output file
            cmd += ["-o", str(target_path)]

            # Extra opts (unvalidated passthrough)
            cmd += extra_opts

            # Source file
            cmd.append(str(src))

            log_info(log_file, f"mpy-cross compiling: {src}")
            log_info(log_file, f"Command: {_format_cmd(cmd)}")

            try:
                res = subprocess.run(
                    cmd,
                    cwd=str(src.parent),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if res.stdout:
                    log_info(log_file, f"stdout:\n{res.stdout}")
                if res.stderr:
                    # mpy-cross schreibt gerne alles nach stderr; daher WARNING statt ERROR
                    log_warning(log_file, f"stderr:\n{res.stderr}")

                if res.returncode != 0:
                    log_error(log_file, f"mpy-cross failed (rc={res.returncode}) for: {src}")
                    raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout, stderr=res.stderr)

                compiled += 1
                log_info(log_file, f"OK: {target_path}")

            except Exception as e:
                log_error(log_file, f"Unexpected error during mpy-cross: {e}")
                raise

        log_info(log_file, f"Finished. Compiled {compiled} file(s) with mpy-cross.")
