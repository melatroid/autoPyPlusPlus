import json
from pathlib import Path
from .project import Project
from .spec_parser import generate_spec_file 

def save_projects(projects, file_path):
    """Speichert die Projektliste als JSON oder als .spec-Datei."""
    file_path = Path(file_path)  # 💡 Immer als Path-Objekt behandeln
    if file_path.suffix.lower() == ".spec":
        # Wir nehmen an: nur ein Projekt wird als .spec-Datei exportiert
        if not projects:
            return
        proj = projects[0]
        spec_text = generate_spec_file(proj)
        file_path.write_text(spec_text, encoding="utf-8")
    else:
        # Standard: .apyscript (JSON)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([vars(p) for p in projects], f, ensure_ascii=False, indent=2)

def load_projects(file_path):
    """Lädt Projekte aus einer JSON-Datei als Liste von Project-Objekten."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    projects = []
    for item in data:
        project_data = item.copy()
        use_pyarmor = project_data.get('use_pyarmor', False)
        use_nuitka = project_data.get('use_nuitka', False)
        # Korrigiere inkonsistente Zustände: Nur ein Compiler kann aktiviert sein
        if use_pyarmor and use_nuitka:
            use_nuitka = False  # PyArmor hat Vorrang, kann angepasst werden
        
        # Definiere die erwarteten Parameter für __init__
        init_params = {
            'script': project_data.get('script', ''),
            'name': project_data.get('name', ''),
            'spec_file': project_data.get('spec_file', ''),
            'compile_selected': project_data.get('compile_selected', False),
            'compile_a_selected': project_data.get('compile_a_selected'),
            'compile_b_selected': project_data.get('compile_b_selected'),
            'use_pyarmor': use_pyarmor,
            'use_nuitka': use_nuitka
        }
        
        # Erstelle das Project-Objekt mit den gültigen Parametern
        project = Project(**init_params)
        
        # Setze die restlichen Attribute nach der Initialisierung
        for key, value in project_data.items():
            if key not in init_params and hasattr(project, key):
                setattr(project, key, value)
        
        projects.append(project)
    return projects
