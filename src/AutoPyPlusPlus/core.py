import json
from pathlib import Path
from typing import List, Tuple
import shutil

from .project import Project
from .spec_parser import generate_spec_file

# === Projekte speichern/laden ===

def save_projects(projects: List[Project], file_path: str | Path) -> None:
    """Speichert die Projektliste als JSON (.apyscript) oder als .spec-Datei."""
    file_path = Path(file_path)
    if file_path.suffix.lower() == ".spec":
        # Nur das erste Projekt als .spec-Datei exportieren
        if not projects:
            return
        proj = projects[0]
        spec_text = generate_spec_file(proj)
        file_path.write_text(spec_text, encoding="utf-8")
    else:
        # Standard: als JSON-Liste
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() if hasattr(p, "to_dict") else vars(p) for p in projects], f, ensure_ascii=False, indent=2)

def load_projects(file_path: str | Path) -> List[Project]:
    """Lädt Projekte aus einer JSON-Datei als Liste von Project-Objekten."""
    file_path = Path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    projects = []
    for item in data:
        # Kompatibilität mit alten oder neuen Feldnamen
        project_data = dict(item)
        # Fix für Compiler-Status: Immer nur einer aktiv!
        use_pyarmor = project_data.get('use_pyarmor', False)
        use_nuitka = project_data.get('use_nuitka', False)
        use_cython = project_data.get('use_cython', False)
        if sum([bool(use_pyarmor), bool(use_nuitka), bool(use_cython)]) > 1:
            # Priorität: PyArmor > Nuitka > Cython
            if use_pyarmor:
                use_nuitka = use_cython = False
            elif use_nuitka:
                use_cython = False
        # Alle init-Parameter sauber extrahieren
        init_params = {
            'script': project_data.get('script', ''),
            'name': project_data.get('name', ''),
            'spec_file': project_data.get('spec_file', ''),
            'compile_selected': project_data.get('compile_selected', False),
            'compile_a_selected': project_data.get('compile_a_selected', False),
            'compile_b_selected': project_data.get('compile_b_selected', False),
            'compile_c_selected': project_data.get('compile_c_selected', False),
            'use_pyarmor': use_pyarmor,
            'use_nuitka': use_nuitka,
            'use_cython': use_cython,
        }
        project = Project(**init_params)
        # Setze übrige Attribute (sofern im Model vorhanden)
        for k, v in project_data.items():
            if k not in init_params and hasattr(project, k):
                setattr(project, k, v)
        projects.append(project)
    return projects

# === INI-Dateien laden/speichern ===

def export_extensions_ini(src_ini: Path, dest_ini: Path) -> None:
    """Exportiert eine extensions_path.ini an einen Zielort."""
    shutil.copyfile(src_ini, dest_ini)

def load_extensions_ini(src_ini: Path, dest_ini: Path) -> None:
    """Überschreibt extensions_path.ini mit einer ausgewählten Datei."""
    content = Path(src_ini).read_text(encoding="utf-8")
    Path(dest_ini).write_text(content, encoding="utf-8")

# === Workdir-Cleanup ===

def find_cleanup_targets(work_dir: Path) -> Tuple[list, list]:
    """
    Liefert zwei Listen zurück:
    - zu löschende Dateien (Logfiles, .spec)
    - zu löschende Ordner (build, dist, __pycache__)
    """
    files = []
    folders = []
    for f in work_dir.iterdir():
        if f.is_file() and (f.name.startswith("compile_") or f.suffix == ".spec"):
            files.append(f)
    for d in ["build", "dist", "AutoPyplusplus/__pycache__"]:
        dir_path = work_dir / d
        if dir_path.exists():
            folders.append(dir_path)
    return files, folders

def delete_files_and_dirs(targets: List[Path]) -> int:
    """Löscht alle übergebenen Dateien/Ordner. Gibt die Anzahl der gelöschten Objekte zurück."""
    deleted = 0
    for t in targets:
        try:
            if t.is_file():
                t.unlink()
                deleted += 1
            elif t.is_dir():
                shutil.rmtree(t)
                deleted += 1
        except Exception as e:
            print(f"[ERROR] Konnte {t} nicht löschen: {e}")
    return deleted

# === Projekt-Konsistenzprüfung ===

def fix_project_consistency(projects: List[Project]) -> None:
    """
    Stellt sicher, dass pro Projekt nur einer der Compiler aktiv ist.
    Modifiziert die Liste in-place!
    """
    for p in projects:
        flags = [p.use_pyarmor, p.use_nuitka, getattr(p, "use_cython", False)]
        if sum(flags) > 1:
            # Priorität PyArmor > Nuitka > Cython
            if p.use_pyarmor:
                p.use_nuitka = False
                if hasattr(p, "use_cython"):
                    p.use_cython = False
            elif p.use_nuitka:
                if hasattr(p, "use_cython"):
                    p.use_cython = False

# === JSON Hilfsfunktionen (optional) ===

def save_json(obj, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
