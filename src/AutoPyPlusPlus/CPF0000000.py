import subprocess
import sys
import shutil
from pathlib import Path

try:
    from .extension_paths_loader import load_extensions_paths
except ImportError:
    def load_extensions_paths(log_file):
        return {}

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

class CPF0000000:
    """
    Führt pytest aus. Erkennt sinnvolle Parameter automatisch aus dem Project-Objekt.
    """
    @staticmethod
    def run_pytest(project, log_file) -> None:
        # 1. Testziel bestimmen
        target = getattr(project, "test_file", None) or getattr(project, "test_dir", None) or "."
        target_path = Path(target).resolve()
        if not target_path.exists():
            log_error(log_file, f"Testziel {target} nicht gefunden.")
            raise FileNotFoundError(f"Testziel {target} nicht gefunden.")

        # 2. Pfad zu pytest
        pytest_path = getattr(project, "pytest_path", None)
        if not pytest_path:
            extensions_paths = load_extensions_paths(log_file)
            pytest_candidate = extensions_paths.get("pytest")
            if pytest_candidate:
                pytest_path = pytest_candidate
                setattr(project, "pytest_path", pytest_candidate)
                log_info(log_file, f"Set pytest_path from extensions: {pytest_candidate}")
        if not pytest_path:
            pytest_path = shutil.which("pytest")
            if pytest_path:
                log_info(log_file, f"Found pytest in PATH: {pytest_path}")
        if pytest_path:
            pytest_cmd = [pytest_path]
        else:
            log_warning(log_file, "Falling back to python -m pytest")
            pytest_cmd = [sys.executable, "-m", "pytest"]

        # 3. Standard-Pytest-Argumente automatisch verarbeiten
        # Folgende Felder werden automatisch übersetzt:
        argmap = [
            # (Attribut im Projektobjekt, pytest-Parameter, Wert/Format)
            ("pytest_verbose", "-v", None),         # True/False
            ("pytest_quiet", "-q", None),           # True/False
            ("pytest_maxfail", "--maxfail", "{}"),  # Zahl
            ("pytest_marker", "-m", "{}"),          # Marker-Name(n)
            ("pytest_keyword", "-k", "{}"),         # Keyword
            ("pytest_disable_warnings", "--disable-warnings", None), # True/False
            ("pytest_tb", "--tb", "{}"),            # "short"/"long"/"no"
            ("pytest_durations", "--durations", "{}"), # int
            ("pytest_capture", "--capture", "{}"),  # "no"/"sys"/...
            ("pytest_html", "--html", "{}"),        # "report.html"
            ("pytest_lf", "--lf", None),            # True/False
            ("pytest_ff", "--ff", None),            # True/False
        ]
        for attr, flag, valfmt in argmap:
            value = getattr(project, attr, None)
            if value:
                if valfmt:
                    pytest_cmd.append(flag)
                    pytest_cmd.append(valfmt.format(value))
                else:
                    pytest_cmd.append(flag)

        # Weitere freie Argumente
        pytest_args = getattr(project, "pytest_args", [])
        if isinstance(pytest_args, str):
            pytest_args = pytest_args.split()
        pytest_cmd += pytest_args

        # Testziel anhängen
        pytest_cmd.append(str(target_path))

        log_info(log_file, "Pytest-Befehl wird ausgeführt:")
        log_info(log_file, " ".join(map(str, pytest_cmd)))

        try:
            result = subprocess.run(
                pytest_cmd,
                cwd=str(target_path.parent if target_path.is_file() else target_path),
                capture_output=True,
                text=True,
                check=False
            )
            log_info(log_file, "Pytest-stdout:")
            log_info(log_file, result.stdout)
            if result.stderr:
                log_warning(log_file, "Pytest-stderr:")
                log_warning(log_file, result.stderr)
            if result.returncode != 0:
                log_warning(log_file, f"Pytest beendete sich mit Rückgabewert {result.returncode}")
        except Exception as e:
            log_error(log_file, f"Unerwarteter Fehler bei der Pytest-Ausführung: {e}")
            raise

        log_info(log_file, "Fertig. Pytest-Ausführung abgeschlossen.")

