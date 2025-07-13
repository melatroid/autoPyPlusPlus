import subprocess
import shutil
from pathlib import Path

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

class SphinxBuilder:
    """
    Baut Sphinx-Dokumentation mit allen wichtigen Parametern aus einem Project-Objekt.
    """
    @staticmethod
    def run_sphinx(project, log_file) -> None:
        # 1. Quell- und Zielverzeichnis bestimmen
        source = getattr(project, "sphinx_source", None) or "docs"
        build = getattr(project, "sphinx_build", None) or "_build/html"
        source_path = Path(source).resolve()
        build_path = Path(build).resolve()
        if not source_path.exists():
            log_error(log_file, f"Quellordner {source} nicht gefunden.")
            raise FileNotFoundError(f"Quellordner {source} nicht gefunden.")

        # 2. Pfad zu sphinx-build
        sphinx_build_path = getattr(project, "sphinx_build_path", None)
        if not sphinx_build_path:
            sphinx_build_path = shutil.which("sphinx-build")
            if sphinx_build_path:
                log_info(log_file, f"Found sphinx-build in PATH: {sphinx_build_path}")
            else:
                log_error(log_file, "sphinx-build nicht gefunden!")
                raise FileNotFoundError("sphinx-build nicht gefunden!")

        sphinx_cmd = [sphinx_build_path]

        # 3. Mögliche Build-Parameter
        argmap = [
            ("sphinx_builder", "-b", "{}"),               # html, latex, man, etc.
            ("sphinx_conf_path", "-c", "{}"),             # conf.py directory
            ("sphinx_doctrees", "-d", "{}"),              # doctrees directory
            ("sphinx_parallel", "-j", "{}"),              # parallele Jobs
            ("sphinx_warning_is_error", "-W", None),      # Warnings as errors
            ("sphinx_quiet", "-q", None),                 # Quiet
            ("sphinx_verbose", "-v", None),               # Verbose
            ("sphinx_very_verbose", "-vv", None),         # Very verbose
            ("sphinx_keep_going", "--keep-going", None),  # Bei Fehlern weitermachen
            ("sphinx_tags", "-t", "{}"),                  # Tags für bedingte Blöcke
            ("sphinx_define", "-D", "{}"),                # Konfigwerte überschreiben
            ("sphinx_new_build", "-E", None),             # Alles neu bauen (kein Cache)
            ("sphinx_all_files", "-a", None),             # Alle Dateien neu bauen
            ("sphinx_logfile", "-w", "{}"),               # Logfile
            ("sphinx_nitpicky", "-n", None),              # Warnung bei fehlenden Referenzen
            ("sphinx_color", "--color", None),            # Farbausgabe erzwingen
            ("sphinx_no_color", "--no-color", None),      # Farbausgabe deaktivieren
        ]
        for attr, flag, valfmt in argmap:
            value = getattr(project, attr, None)
            if value:
                # für boolsche Optionen
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

        # Weitere freie Argumente wie z.B. "--keep-going"
        sphinx_args = getattr(project, "sphinx_args", [])
        if isinstance(sphinx_args, str):
            sphinx_args = sphinx_args.split()
        sphinx_cmd += sphinx_args

        # Quell- und Zielverzeichnis anhängen
        sphinx_cmd.append(str(source_path))
        sphinx_cmd.append(str(build_path))

        log_info(log_file, "Sphinx-Befehl wird ausgeführt:")
        log_info(log_file, " ".join(map(str, sphinx_cmd)))

        try:
            result = subprocess.run(
                sphinx_cmd,
                cwd=str(source_path),
                capture_output=True,
                text=True,
                check=False
            )
            log_info(log_file, "Sphinx stdout:")
            log_info(log_file, result.stdout)
            if result.stderr:
                log_warning(log_file, "Sphinx stderr:")
                log_warning(log_file, result.stderr)
            if result.returncode != 0:
                log_warning(log_file, f"Sphinx-Build beendet mit Rückgabewert {result.returncode}")
        except Exception as e:
            log_error(log_file, f"Unerwarteter Fehler beim Sphinx-Build: {e}")
            raise

        log_info(log_file, "Fertig. Sphinx-Build abgeschlossen.")
