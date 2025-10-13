import json
import copy
from pathlib import Path
from typing import Optional, Union, List

CONFIG_FILE = Path(__file__).parent / "config.json"

SUPPORTED_LANGUAGES = ["de", "en"]

DEFAULTS = {
    "language": "de",
    "dark_mode": True,
    "load_last_on_start": True,     # Beim Start letztes Projekt laden?
    "last_apyscript": None,         # Pfad als String oder None
    "recent_apyscripts": [],        # Liste der letzten Dateien
}

def load_config():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    # Defaults mergen (mutables deep-copied)
    for k, v in DEFAULTS.items():
        data.setdefault(k, copy.deepcopy(v))

    # Sprache validieren
    if data["language"] not in SUPPORTED_LANGUAGES:
        data["language"] = DEFAULTS["language"]

    return data

def save_config(config):
    # Defaults sicherstellen
    for k, v in DEFAULTS.items():
        config.setdefault(k, copy.deepcopy(v))

    # Sprache validieren
    if config["language"] not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Ungültige Sprache: {config['language']}. "
            f"Unterstützte Sprachen: {', '.join(SUPPORTED_LANGUAGES)}"
        )

    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# -------- Convenience-API: zuletzt geöffnet / Recents --------

def get_last_apyscript(config) -> Optional[Path]:
    s = config.get("last_apyscript")
    return Path(s) if s else None

def set_last_apyscript(
    config,
    path: Union[str, Path],
    *,
    update_recent: bool = True,
    max_recent: int = 10
) -> None:
    p = Path(path)
    config["last_apyscript"] = str(p)

    if update_recent:
        lst = list(config.get("recent_apyscripts", []))
        sp = str(p)
        if sp in lst:
            lst.remove(sp)
        lst.insert(0, sp)
        del lst[max_recent:]
        config["recent_apyscripts"] = lst

    save_config(config)

def get_recent_apyscripts(config) -> List[Path]:
    return [Path(s) for s in config.get("recent_apyscripts", [])]
