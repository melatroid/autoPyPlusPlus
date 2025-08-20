from __future__ import annotations
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
from .CPE0000000 import CPE0000000  # C++ Compiler (GCC)
from .CPF0000000 import CPF0000000  # Pytest
from .CPG0000000 import CPG0000000  # Sphinx

def compile_single(project: Project, log_file, compiler: str = "both") -> str:
    try:
        # Debugging-Ausgabe für Konsole
        #print(f"[DEBUG] compile_single START for {project.name or project.script}")
        #print(f"[DEBUG] Compiler: {compiler}")
        #print(f"[DEBUG] use_nuitka: {project.use_nuitka}, use_pyarmor: {project.use_pyarmor}")
        #print(f"[DEBUG] use_cython: {project.use_cython}, use_cpp: {project.use_cpp}")
        #print(f"[DEBUG] Project config: {project.to_dict()}")

        log_file.write(f"--- compile_single() START for {project.name or project.script} (compiler={compiler}) ---\n")
        #log_file.write(f"Project config: {project.to_dict()}\n")
        log_file.flush()


        if getattr(project, "use_pytest_standalone", False) and getattr(project, "use_sphinx_standalone", False):
            msg = "Fehler: Sowohl Pytest- als auch Sphinx-Standalone aktiviert. Nur eins ist erlaubt!"
            log_file.write(msg + "\n")
            log_file.flush()
            return msg

        # --- 1. Pytest vor Kompilierung ---
        if getattr(project, "use_pytest", False):
            log_file.write("Running pytest before compilation...\n")
            log_file.flush()
            # Prüfe Standalone-Modus!
            if getattr(project, "use_pytest_standalone", False):
                try:
                    result = CPF0000000.run_pytest(project, log_file)
                    return f"Pytest Standalone: {result}"  # Sofortiger Return
                except Exception as e:
                    err = f"Pytest Standalone failed: {e}"
                    log_file.write(err + "\n")
                    log_file.flush()
                    return err  # Build abbrechen!
            else:
                try:
                    CPF0000000.run_pytest(project, log_file)
                except Exception as e:
                    err = f"Pytest failed for {project.name or project.script}: {e}"
                    log_file.write(err + "\n")
                    log_file.flush()
                    return err  # Build abbrechen!

        # --- 2. Sphinxy/Sphinx vor Kompilierung ---
        if getattr(project, "use_sphinx", False):
            log_file.write("Running sphinx before compilation...\n")
            log_file.flush()
            # Prüfe Standalone-Modus!
            if getattr(project, "use_sphinx_standalone", False):
                try:
                    result = CPG0000000.run_sphinx(project, log_file)
                    return f"Sphinx Standalone: {result}"  # Sofortiger Return
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

        # PyArmor if enabled
        if compiler in ("pyarmor", "both") and project.use_pyarmor:
            print("[DEBUG] Running PyArmor")
            CPB0000000.run_pyarmor(project, log_file)
            compiled = True

        # Nuitka if enabled
        if compiler in ("nuitka", "both") and project.use_nuitka:
            print("[DEBUG] Running Nuitka")
            CPC0000000.run_nuitka(project, log_file)
            compiled = True
        else:
            print(f"[DEBUG] Nuitka NOT executed (compiler={compiler}, use_nuitka={project.use_nuitka})")

        # *** CYTHON if enabled ***
        if compiler in ("cython", "both") and project.use_cython:
            print("[DEBUG] Running Cython")
            CPD0000000.run_cython(project, log_file)
            compiled = True

            if project.use_cpp:
                if not project.cpp_compiler_path or project.cpp_compiler_path.lower() == "g++":
                    msvc_path = shutil.which("cl.exe")
                    if msvc_path:
                        project.cpp_compiler_path = msvc_path
                    else:
                        project.cpp_compiler_path = "g++"  # fallback

                print(f"[DEBUG] Using C++ compiler: {project.cpp_compiler_path}")
                CPE0000000.run_cpp(project, log_file)
        else:
            print(f"[DEBUG] Cython NOT executed (compiler={compiler}, use_cython={project.use_cython})")

        # PyInstaller if no other method is active or explicitly selected
        if compiler in ("pyinstaller", "both") and not project.use_pyarmor and not project.use_nuitka and not project.use_cython:
            print("[DEBUG] Running PyInstaller")
            CPA0000000.run_pyinstaller(project, log_file)
            compiled = True
        else:
            print(f"[DEBUG] PyInstaller NOT executed (compiler={compiler}, use_pyarmor={project.use_pyarmor}, use_nuitka={project.use_nuitka}, use_cython={project.use_cython})")

        if not compiled:
            msg = (
                f"No compiler executed for {project.name or project.script} "
                f"(use_nuitka={project.use_nuitka}, use_pyarmor={project.use_pyarmor}, "
                f"use_cython={project.use_cython}, compiler={compiler})"
            )
            print(f"[DEBUG] {msg}")
            log_file.write(f"{msg}\n")
            log_file.flush()
            return msg

        print(f"[DEBUG] Completed {project.name or project.script}")
        log_file.write(f"Completed {project.name or project.script}\n")
        log_file.flush()

        # --- Zusätzliche Dateien kopieren in den Output-Ordner ---
        try:
            out_dir = Path(
                project.cython_output_dir
                or project.cpp_output_dir
                or Path(project.script).parent
            )
            for src in project.additional_files:
                src_path = Path(src)
                if src_path.is_file() and out_dir.is_dir():
                    dst = out_dir / src_path.name
                    shutil.copy2(src_path, dst)
                    log_file.write(f"Copied additional file {src_path} -> {dst}\n")
            log_file.flush()
        except Exception as e:
            print(f"[DEBUG] Fehler beim Kopieren zusätzlicher Dateien: {e}")
            log_file.write(f"Error copying additional files: {e}\n")
            log_file.flush()

        return f"{project.name or Path(project.script).stem} done."
    except Exception as e:
        msg = f"Error with {project.name or project.script}: {e}"
        print(f"[DEBUG] {msg}")
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
    Kompiliert mehrere Projekte parallel im angegebenen Modus und mit dem gewählten Compiler.
    - mode: "A", "B" oder "C" zur Auswahl der Projekte.
    - compiler: "pyarmor", "nuitka", "cython", "pyinstaller" oder "both".
    """
    print(f"[DEBUG] compile_projects START: {len(projects)} projects, thread_count={thread_count}, mode={mode}, compiler={compiler}")
    selected_projects = [
        p for p in projects
        if (mode == "A" and p.compile_a_selected)
        or (mode == "B" and p.compile_b_selected)
        or (mode == "C" and p.compile_c_selected)
    ]
    total = len(selected_projects)
    print(f"[DEBUG] Selected projects: {[p.name or p.script for p in selected_projects]}")
    print(f"[DEBUG] Total selected projects: {total}")

    log_file.write(f"--- compile_projects() START: {total} projects, thread_count={thread_count}, mode={mode}, compiler={compiler} ---\n")
    log_file.flush()

    errors: List[str] = []
    if total == 0:
        print("[DEBUG] No projects selected for compilation")
        log_file.write("No projects selected for compilation.\n")
        log_file.flush()
        return []

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = {executor.submit(compile_single, p, log_file, compiler): p for p in selected_projects}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                print(f"[DEBUG] Project {i}/{total} completed: {result}")
                log_file.write(f"Project {i}/{total} completed: {result}\n")
                log_file.flush()
                status_callback(result)
                if "Error" in result:
                    errors.append(result)
                progress_callback(i, total)
            except Exception as e:
                msg = f"Exception in future {i}: {e}"
                print(f"[DEBUG] {msg}")
                log_file.write(f"{msg}\n")
                log_file.flush()
                errors.append(msg)
            time.sleep(0.05)

    print(f"[DEBUG] compile_projects END: {len(errors)} errors")
    log_file.write(f"--- compile_projects() END: {len(errors)} errors ---\n")
    log_file.flush()

    if not any(p.debug for p in selected_projects):
        try:
            log_file.close()
            Path(log_file.name).unlink()
        except Exception as e:
            with open(log_file.name, 'a') as lf:
                lf.write(f"Failed to delete log file: {e}\n")

    return errors
