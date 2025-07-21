import json
from pathlib import Path
CONFIG_FILE = Path(__file__).parent / "config.json"

# Unterstützte Sprachen (synchron mit language.py)
SUPPORTED_LANGUAGES = ["de", "en"]

def load_config():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(config):
    # Standardwerte setzen
    config["language"] = config.get("language", "de")
    config["dark_mode"] = config.get("dark_mode", True)

    # Validierung des language-Werts
    if config["language"] not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Ungültige Sprache: {config['language']}. Unterstützte Sprachen: {', '.join(SUPPORTED_LANGUAGES)}")

    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        # Fehler wird geworfen, um in gui.py abgefangen zu werden
        raise OSError(f"Fehler beim Speichern der Konfiguration: {e}")