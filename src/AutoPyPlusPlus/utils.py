import os
import json
import re
from datetime import datetime
from pathlib import Path

def is_valid_file(path):
    """
    Prüft, ob der Pfad existiert und eine Datei ist.
    """
    p = Path(path)
    return p.exists() and p.is_file()

def is_valid_dir(path):
    """
    Prüft, ob der Pfad existiert und ein Verzeichnis ist.
    """
    p = Path(path)
    return p.exists() and p.is_dir()

def sanitize_filename(filename):
    """
    Entfernt problematische Zeichen aus Dateinamen.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def timestamp_now():
    """
    Gibt den aktuellen Zeitstempel zurück (YYYYMMDD_HHMMSS).
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def load_json(file_path):
    """
    Lädt JSON-Daten aus einer Datei.
    """
    p = Path(file_path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, file_path):
    """
    Speichert JSON-Daten in eine Datei.
    """
    p = Path(file_path)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def create_temp_dir(base_dir="C:/Temp/AutoPyTemp"):
    """
    Erstellt ein temporäres Verzeichnis (nur falls nicht vorhanden).
    """
    temp_dir = Path(base_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(temp_dir)
    os.environ["TEMP"] = str(temp_dir)
    return temp_dir
