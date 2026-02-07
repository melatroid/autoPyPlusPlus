from __future__ import annotations
import os
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Callable
import shutil

from .project import Project
from .CPA0000000 import CPA0000000  # PyInstaller
from .CPB0000000 import CPB0000000  # PyArmor
from .CPC0000000 import CPC0000000  # Nuitka
from .CPD0000000 import CPD0000000  # Cython
from .CPE0000000 import CPE0000000  # C++ Compiler
from .CPF0000000 import CPF0000000  # Pytest
from .CPG0000000 import CPG0000000  # Sphinx
from .CPH0000000 import CPH0000000  # mpy-cross (MicroPython)


# =====================================================================
#                         Add-Data: Helfer
# =====================================================================

def _sanitize_path(path: str) -> str:
    """
    Entfernt kaputte Präfixe wie 'C:\\C:\\...' und normalisiert Backslashes.
    """
    if not path:
        return path
    # doppelte Laufwerksbuchstaben wie C:\C:\xxx entfernen
    m = re.match(r"^([A-Za-z]):[\\/]\1:[\\/](.*)$", path)
    if m:
        drive, rest = m.groups()
        path = f"{drive}:\\" + rest
    return os.path.normpath(path)


def _parse_add_data_any(raw: str) -> list[tuple[str, str]]:
    """
    Akzeptiert sowohl 'src:dst' (unser internes Format) als auch 'src;dst' (Windows),
    trennt Einträge über ';' ODER Zeilenumbrüche. Richtig robust dank rsplit(':', 1).
    """
    if not raw:
        return []
    pairs: list[tuple[str, str]] = []
    # Einträge dürfen mit ; oder Zeilenumbruch getrennt sein
    for token in re.split(r"[;\r\n]+", str(raw)):
        t = token.strip().strip('"').strip("'")
        if not t:
            continue

        if ";" in t and os.name == "nt" and ":" not in t:
            # windows-Variante 'src;dst' → split am letzten ';' wäre falsch, da oft nur 1 ';'
            parts = t.split(";")
            if len(parts) == 2:
                src, dst = parts[0].strip(), parts[1].strip()
            else:
                # notfall: wieder in die generische Logik
                src, dst = parts[0].strip(), ";".join(parts[1:]).strip()
        else:
            # internes Format 'src:dst' oder generisch → am letzten ':' splitten (Drive-Letter bleibt heil)
            if ":" not in t or t.endswith(":"):
                # ungültig, überspringen
                continue
            src, dst = t.rsplit(":", 1)
            src, dst = src.strip(), dst.strip()

        if not src or not dst:
            continue

        src = _sanitize_path(src)
        pairs.append((src, dst))
    return pairs


def _validate_pairs_exist(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Filtert Paare mit nicht existierendem src heraus (Datei/Ordner).
    """
    valid: list[tuple[str, str]] = []
    for src, dst in pairs:
        try:
            if Path(src).exists():
                valid.append((src, dst))
        except Exception:
            pass
    return valid


def _add_pyarmor_runtime_if_needed(project: Project, pairs: list[tuple[str, str]], log_write: Callable[[str], None]) -> None:
    """
    Hängt den PyArmor-Runtime-Ordner (pyarmor_runtime_*) als add-data an, wenn gewünscht.
    """
    if not getattr(project, "include_pyarmor_runtime", False):
        return
    runtime_dir = (getattr(project, "pyarmor_runtime_dir", "") or "").strip()
    if not runtime_dir:
        return
    rd = Path(runtime_dir)
    if rd.exists():
        mapping = (str(rd), rd.name)
        if mapping not in pairs:
            pairs.append(mapping)
            log_write(f"--- INFO: Added PyArmor runtime: {rd} -> {rd.name}\n")


def _format_pairs_for_platform(pairs: list[tuple[str, str]]) -> list[str]:
    """
    Formatiert Paare für PyInstaller:
      - Windows: 'src;dst'
      - Unix   : 'src:dst'
    Gibt eine Liste formatierter Strings zurück (je Eintrag ein String).
    """
    sep = ";" if os.name == "nt" else ":"
    return [f"{src}{sep}{dst}" for src, dst in pairs]


def _prepare_add_data_for_pyinstaller(project: Project, log_write: Callable[[str], None]) -> tuple[str | None, str]:
    """
    Liest project.add_data (gemischt 'src:dst' / 'src;dst'), ergänzt ggf. PyArmor-Runtime,
    validiert Quellen und baut eine **zeilenweise** Darstellung auf:
        Windows: jede Zeile 'src;dst'
        Unix:    jede Zeile 'src:dst'
    Gibt (backup_add_data, prepared_string) zurück.
    """
    original = getattr(project, "add_data", "") or ""
    pairs = _parse_add_data_any(original)
    _add_pyarmor_runtime_if_needed(project, pairs, log_write)
    pairs = _validate_pairs_exist(pairs)
    formatted = _format_pairs_for_platform(pairs)
    # Zeilenweise speichern, damit äußere Trennung nicht mit innerem Separator kollidiert
    prepared = "\n".join(formatted)
    return original, prepared


# =====================================================================
#                         Build-Pipeline
# =====================================================================

def compile_single(project: Project, log_file, compiler: str = "both") -> str:
    try:
        log_file.write(f"--- compile_single() START for {project.name or project.script} (compiler={compiler}) ---\n")
        log_file.flush()

        if getattr(project, "use_pytest_standalone", False) and getattr(project, "use_sphinx_standalone", False):
            msg = "Error: Both Pytest and Sphinx standalone are enabled. Only one is allowed!"
            log_file.write(msg + "\n")
            log_file.flush()
            return msg

        # --- 1. Pytest vor der Kompilation ---
        if getattr(project, "use_pytest", False):
            log_file.write("Running pytest before compilation...\n")
            log_file.flush()
            if getattr(project, "use_pytest_standalone", False):
                try:
                    result = CPF0000000.run_pytest(project, log_file)
                    return f"Pytest Standalone: {result}"
                except Exception as e:
                    err = f"Pytest Standalone failed: {e}"
                    log_file.write(err + "\n")
                    log_file.flush()
                    return err
            else:
                try:
                    CPF0000000.run_pytest(project, log_file)
                except Exception as e:
                    err = f"Pytest failed for {project.name or project.script}: {e}"
                    log_file.write(err + "\n")
                    log_file.flush()
                    return err

        # --- 2. Sphinx vor der Kompilation ---
        if getattr(project, "use_sphinx", False):
            log_file.write("Running sphinx before compilation...\n")
            log_file.flush()
            if getattr(project, "use_sphinx_standalone", False):
                try:
                    result = CPG0000000.run_sphinx(project, log_file)
                    return f"Sphinx Standalone: {result}"
                except Exception as e:
                    err = f"Sphinx Standalone failed: {e}"
                    log_file.write(err + "\n")
                    log_file.flush()
                    return err
            else:
                try:
                    CPG0000000.run_sphinx(project, log_file)
                except Exception as e:
                    err = f"Sphinx build failed for {project.name or project.script}: {e}"
                    log_file.write(err + "\n")
                    log_file.flush()

        compiled = False

        # --- mpy-cross (MicroPython .mpy) ---
        if compiler in ("mpy", "both") and getattr(project, "use_mpycross", False):
            CPH0000000.run_mpycross(project, log_file)
            compiled = True
        else:
            pass

        # --- PyArmor ---
        if compiler in ("pyarmor", "both") and project.use_pyarmor:
            CPB0000000.run_pyarmor(project, log_file)
            compiled = True

        # --- Nuitka ---
        if compiler in ("nuitka", "both") and project.use_nuitka:
            CPC0000000.run_nuitka(project, log_file)
            compiled = True
        else:
            pass

        # --- Cython (+ optional C++) ---
        if compiler in ("cython", "both") and project.use_cython:
            CPD0000000.run_cython(project, log_file)
            compiled = True

            if project.use_cpp:
                if not project.cpp_compiler_path or project.cpp_compiler_path.lower() == "g++":
                    msvc_path = shutil.which("cl.exe")
                    project.cpp_compiler_path = msvc_path if msvc_path else "g++"
                CPE0000000.run_cpp(project, log_file)
        else:
            pass

        # --- PyInstaller (nur wenn keine der obigen Routen aktiv ist oder explizit gewählt) ---
        if (
            compiler in ("pyinstaller", "both")
            and not project.use_pyarmor
            and not project.use_nuitka
            and not project.use_cython
            and not getattr(project, "use_mpycross", False)
        ):
            # >>> Add-Data sicher und plattformrichtig aufbereiten
            backup_add_data, prepared = _prepare_add_data_for_pyinstaller(project, lambda s: log_file.write(s))
            try:
                # Temporär ersetzen (zeilenweise, damit CPA sauber splitten kann)
                project.add_data = prepared
                CPA0000000.run_pyinstaller(project, log_file)
            finally:
                # Ursprungswert wiederherstellen
                project.add_data = backup_add_data
            compiled = True
        else:
            pass

        if not compiled:
            msg = (
                f"No compiler executed for {project.name or project.script} "
                f"(use_nuitka={project.use_nuitka}, use_pyarmor={project.use_pyarmor}, "
                f"use_cython={project.use_cython}, compiler={compiler})"
            )
            log_file.write(f"{msg}\n")
            log_file.flush()
            return msg

        log_file.write(f"Completed {project.name or project.script}\n")
        log_file.flush()

        # --- Zusatzdateien in Ausgabeverzeichnis kopieren ---
        try:
            out_dir = Path(
                project.cython_output_dir
                or project.cpp_output_dir
                or Path(project.script).parent
            )
            for src in getattr(project, "additional_files", []):
                src_path = Path(src)
                if src_path.is_file() and out_dir.is_dir():
                    dst = out_dir / src_path.name
                    shutil.copy2(src_path, dst)
                    log_file.write(f"Copied additional file {src_path} -> {dst}\n")
            log_file.flush()
        except Exception as e:
            log_file.write(f"Error copying additional files: {e}\n")
            log_file.flush()

        return f"{project.name or Path(project.script).stem} done"

    except Exception as e:
        msg = f"Error with {project.name or project.script}: {e}"
        log_file.write(f"{msg}\n")
        log_file.flush()
        return msg


def compile_projects(
    projects: List[Project],
    thread_count: int,
    log_file,
    status_callback: Callable[[str], None],
    progress_callback: Callable[[int, float], None],
    mode: str = "A",
    compiler: str = "both"
) -> List[str]:
    """
    Compile multiple projects in parallel in the given mode and with the selected compiler.
    - mode: "A", "B" or "C" to select the projects.
    - compiler: "pyarmor", "nuitka", "cython", "pyinstaller", "mpy" or "both".
    """
    selected_projects = [
        p for p in projects
        if (mode == "A" and p.compile_a_selected)
        or (mode == "B" and p.compile_b_selected)
        or (mode == "C" and p.compile_c_selected)
    ]
    total = len(selected_projects)

    log_file.write(f"--- compile_projects() START: {total} projects, thread_count={thread_count}, mode={mode}, compiler={compiler} ---\n")
    log_file.flush()

    errors: List[str] = []
    if total == 0:
        log_file.write("No projects selected for compilation.\n")
        log_file.flush()
        return []

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = {executor.submit(compile_single, p, log_file, compiler): p for p in selected_projects}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                log_file.write(f"Project {i}/{total} completed: {result}\n")
                log_file.flush()
                status_callback(result)
                if "Error" in result:
                    errors.append(result)
                progress_callback(i, total)
            except Exception as e:
                msg = f"Exception in future {i}: {e}"
                log_file.write(f"{msg}\n")
                log_file.flush()
                errors.append(msg)
            time.sleep(0.05)

    log_file.write(f"--- compile_projects() END: {len(errors)} errors ---\n")
    log_file.flush()
    keep_log = (len(errors) > 0) or any(p.debug for p in selected_projects)

    try:
        log_file.close()
    except Exception:
        pass

    if not keep_log:
        try:
            Path(log_file.name).unlink()
        except Exception as e:
            with open(log_file.name, 'a') as lf:
                lf.write(f"Failed to delete log file: {e}\n")

    return errors
