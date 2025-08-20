import subprocess
import shutil
from pathlib import Path
import sys
import os
import shlex
import importlib.util

def _ensure_log_handle(log_file):
    """Nimmt Pfad oder File-Objekt. Gibt (handle, must_close) zurück."""
    if hasattr(log_file, "write"):  # bereits ein offenes File-Objekt
        return log_file, False
    p = Path(log_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    f = open(p, "a", encoding="utf-8", buffering=1)  # zeilen-gepuffert
    return f, True

def _format_cmd_for_log(cmd_list):
    """Exakte Darstellung des Kommandos wie ausgeführt (mit korrekten Quotes)."""
    if os.name == "nt":
        return subprocess.list2cmdline(list(map(str, cmd_list)))
    return shlex.join(list(map(str, cmd_list)))

def _sanitize_exe_path(p: str) -> str:
    if p is None:
        return None
    p = p.strip()
    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
        p = p[1:-1]
    p = os.path.expandvars(os.path.expanduser(p))
    return os.path.normpath(p)

def _is_python_exe(path_obj: Path) -> bool:
    return path_obj.name.lower() in {"python.exe", "python", "py.exe", "py"}

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

class CPG0000000:
    """
    Baut Sphinx-Dokumentation mit allen wichtigen Parametern aus einem Project-Objekt.
    """
    @staticmethod
    def run_sphinx(project, log_file) -> None:
        # Log-Handle sicherstellen (Pfad ODER File-Objekt möglich)
        log_file, _must_close = _ensure_log_handle(log_file)
        try:
            # 1. Quell- und Zielverzeichnis bestimmen
            source = getattr(project, "sphinx_source", None) or "docs"
            build = getattr(project, "sphinx_build", None) or "_build/html"
            source_path = Path(source).resolve()
            build_path = Path(build).resolve()
            if not source_path.exists():
                log_error(log_file, f"Quellordner {source} nicht gefunden.")
                raise FileNotFoundError(f"Quellordner {source} nicht gefunden.")

            # Build-Ordner (Parent) sicherstellen
            try:
                build_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                log_error(log_file, f"Build-Ordner konnte nicht angelegt werden: {e}")
                raise

            # 2. Pfad zu sphinx-build / oder python -m sphinx
            sphinx_cmd = None
            custom = getattr(project, "sphinx_build_path", None)

            if custom:
                cleaned = _sanitize_exe_path(str(custom))
                P = Path(cleaned)
                log_info(log_file, f"sphinx_build_path (raw): {repr(custom)}")
                log_info(log_file, f"sphinx_build_path (clean): {cleaned}")

                if P.is_dir():
                    # In Ordner nach möglicher Executable suchen
                    for cand in ("sphinx-build.exe", "sphinx-build.cmd", "sphinx-build.bat",
                                 "sphinx-build-3", "sphinx-build3", "sphinx-build"):
                        q = P / cand
                        if q.exists():
                            sphinx_cmd = [str(q)]
                            log_info(log_file, f"Nutze sphinx-build aus Ordner: {q}")
                            break
                elif P.exists() and P.is_file():
                    if _is_python_exe(P):
                        sphinx_cmd = [str(P), "-m", "sphinx"]
                        log_info(log_file, f"Nutze Python-Interpreter für Sphinx: {P} -m sphinx")
                    else:
                        sphinx_cmd = [str(P)]
                        log_info(log_file, f"Nutze spezifisches sphinx-build: {P}")
                else:
                    found = shutil.which(cleaned)
                    if found:
                        sphinx_cmd = [found]
                        log_info(log_file, f"Gefunden per PATH-Auflösung: {found}")

            if not sphinx_cmd:
                # Prefer: im aktuellen Interpreter installiert?
                if importlib.util.find_spec("sphinx") is not None:
                    sphinx_cmd = [sys.executable, "-m", "sphinx"]
                    log_info(log_file, f"Sphinx im aktuellen Interpreter gefunden: {sys.executable} -m sphinx")
                else:
                    # Fallback: PATH
                    for cand in ("sphinx-build", "sphinx-build.exe", "sphinx-build-3", "sphinx-build3"):
                        p = shutil.which(cand)
                        if p:
                            sphinx_cmd = [p]
                            log_info(log_file, f"Found sphinx-build in PATH: {p}")
                            break

            if not sphinx_cmd:
                log_error(log_file, "sphinx-build nicht gefunden!")
                raise FileNotFoundError("sphinx-build nicht gefunden!")

            # 2a. Builder-Default sicher setzen
            builder = getattr(project, "sphinx_builder", None) or "html"
            sphinx_cmd += ["-b", str(builder)]

            # 2b. conf.py-Verzeichnis korrekt an -c übergeben
            conf_dir = getattr(project, "sphinx_conf_path", None)
            if conf_dir:
                p = Path(conf_dir)
                if p.is_file() and p.name == "conf.py":
                    conf_dir = str(p.parent)
                sphinx_cmd += ["-c", str(conf_dir)]

            # 2c. Doctrees-Default sicher setzen
            doctrees = getattr(project, "sphinx_doctrees", None)
            if not doctrees:
                doctrees = str(build_path.parent / "doctrees")
            sphinx_cmd += ["-d", doctrees]

            # 3. Weitere Build-Parameter (ohne -b/-c/-d)
            argmap = [
                ("sphinx_parallel", "-j", "{}"),              # parallele Jobs
                ("sphinx_warning_is_error", "-W", None),      # Warnings as errors
                ("sphinx_quiet", "-q", None),                 # Quiet
                ("sphinx_verbose", "-v", None),               # Verbose
                ("sphinx_very_verbose", "-vv", None),         # Very verbose
                ("sphinx_keep_going", "--keep-going", None),  # Bei Fehlern weitermachen
                ("sphinx_tags", "-t", "{}"),                  # Tags für bedingte Blöcke
                # ("sphinx_define", "-D", "{}"),              # SPEZIALBEHANDLUNG unten!
                ("sphinx_new_build", "-E", None),             # Alles neu bauen (kein Cache)
                ("sphinx_all_files", "-a", None),             # Alle Dateien neu bauen
                ("sphinx_logfile", "-w", "{}"),               # Logfile (Sphinx-intern)
                ("sphinx_nitpicky", "-n", None),              # Warnung bei fehlenden Referenzen
                ("sphinx_color", "--color", None),            # Farbausgabe erzwingen
                ("sphinx_no_color", "--no-color", None),      # Farbausgabe deaktivieren
            ]

            for attr, flag, valfmt in argmap:
                value = getattr(project, attr, None)
                if value:
                    if isinstance(value, bool):
                        if value:
                            sphinx_cmd.append(flag)
                    elif valfmt:
                        if isinstance(value, (list, tuple)):
                            for v in value:
                                sphinx_cmd.append(flag)
                                sphinx_cmd.append(valfmt.format(v))
                        else:
                            sphinx_cmd.append(flag)
                            sphinx_cmd.append(valfmt.format(value))
                    else:
                        sphinx_cmd.append(flag)

            # 3a. -D (Define) mit Dict/Listen/Strings unterstützen
            define_val = getattr(project, "sphinx_define", None)
            if define_val is not None:
                if isinstance(define_val, dict):
                    for k, v in define_val.items():
                        sphinx_cmd += ["-D", f"{k}={v}"]
                elif isinstance(define_val, (list, tuple)):
                    for item in define_val:
                        sphinx_cmd += ["-D", str(item)]
                else:
                    sphinx_cmd += ["-D", str(define_val)]

            # 3b. Color-Flags konfliktfrei priorisieren (--no-color gewinnt)
            if "--color" in sphinx_cmd and "--no-color" in sphinx_cmd:
                sphinx_cmd = [x for x in sphinx_cmd if x != "--color"]

            # 4. Weitere freie Argumente
            sphinx_args = getattr(project, "sphinx_args", [])
            if isinstance(sphinx_args, str):
                sphinx_args = sphinx_args.split()
            sphinx_cmd += sphinx_args

            # 5. Quell- und Zielverzeichnis anhängen
            sphinx_cmd.append(str(source_path))
            sphinx_cmd.append(str(build_path))

            # Exakt ausgeführten Befehl loggen (korrekt gequotet)
            cmd_pretty = _format_cmd_for_log(sphinx_cmd)
            log_info(log_file, "Sphinx-Befehl wird ausgeführt:")
            log_info(log_file, cmd_pretty)

            # Sidecar mit kompletter Kommandozeile
            try:
                (build_path.parent / "sphinx_cmdline.txt").write_text(cmd_pretty + "\n", encoding="utf-8")
            except Exception as e:
                log_warning(log_file, f"CMD-Line-Sidecar konnte nicht geschrieben werden: {e}")

            # 6. Timeout (Standard 600s, über project.sphinx_timeout konfigurierbar)
            timeout_s = getattr(project, "sphinx_timeout", None)
            if not isinstance(timeout_s, (int, float)) or timeout_s <= 0:
                timeout_s = 600

            # stdout/stderr zusätzlich spiegeln
            stdout_file = build_path.parent / "sphinx_stdout.log"
            stderr_file = build_path.parent / "sphinx_stderr.log"

            try:
                result = subprocess.run(
                    sphinx_cmd,
                    cwd=str(source_path),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=timeout_s
                )
                log_info(log_file, "Sphinx stdout:")
                log_info(log_file, result.stdout if result.stdout else "(kein stdout)")
                log_warning(log_file, "Sphinx stderr:")
                log_warning(log_file, result.stderr if result.stderr else "(kein stderr)")

                # Sidecar-Logs schreiben
                try:
                    stdout_file.write_text(result.stdout or "", encoding="utf-8")
                    stderr_file.write_text(result.stderr or "", encoding="utf-8")
                except Exception as e:
                    log_warning(log_file, f"stdout/stderr Sidecar konnte nicht geschrieben werden: {e}")

                if result.returncode != 0:
                    log_error(log_file, f"Sphinx-Build fehlgeschlagen (rc={result.returncode})")
                    raise RuntimeError(f"sphinx-build failed (rc={result.returncode})")

            except subprocess.TimeoutExpired as e:
                log_error(log_file, f"Sphinx-Build Timeout nach {timeout_s} Sekunden.")
                if e.stdout:
                    log_warning(log_file, "Partielles stdout (Timeout):")
                    log_warning(log_file, e.stdout)
                if e.stderr:
                    log_warning(log_file, "Partielles stderr (Timeout):")
                    log_warning(log_file, e.stderr)
                # Sidecar auch bei Timeout
                try:
                    stdout_file.write_text(e.stdout or "", encoding="utf-8")
                    stderr_file.write_text(e.stderr or "", encoding="utf-8")
                except Exception:
                    pass
                raise

            except Exception as e:
                log_error(log_file, f"Unerwarteter Fehler beim Sphinx-Build: {e}")
                raise

            log_info(log_file, "Fertig. Sphinx-Build abgeschlossen.")
        finally:
            if _must_close:
                try:
                    log_file.close()
                except Exception:
                    pass
