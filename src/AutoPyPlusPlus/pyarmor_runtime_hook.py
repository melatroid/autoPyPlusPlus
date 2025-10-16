# src/hooks/pyarmor_runtime_hook.py
import sys
from pathlib import Path

def _candidate_dirs():
    base = Path(
        getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
               else Path(__file__).resolve().parent)
    )
    cand = [p for p in base.glob("pyarmor_runtime_*") if p.is_dir()]
    try:
        exe_dir = Path(sys.executable).resolve().parent
        if exe_dir != base:
            cand += [p for p in exe_dir.glob("pyarmor_runtime_*") if p.is_dir()]
    except Exception:
        pass
    return sorted(cand, key=lambda x: x.stat().st_mtime, reverse=True)

def _ensure_pyarmor_on_sys_path():
    for d in _candidate_dirs():
        sys.path.insert(0, str(d))
        return

_ensure_pyarmor_on_sys_path()
