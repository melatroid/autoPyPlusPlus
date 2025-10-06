# simplex_api.py
from __future__ import annotations
import configparser
import threading
import time
from pathlib import Path
from typing import Callable

# Accept a flexible set of boolean spellings (both EN/DE allowed for convenience).
TRUTHY = {"1", "true", "on", "yes", "y", "an", "ein", "aktiv", "start"}
FALSY  = {"0", "false", "off", "no", "n", "aus", "stop"}

def _to_bool(s: str | None) -> bool:
    """Convert string to bool using TRUTHY/FALSY sets. Empty/None -> False."""
    if s is None:
        return False
    s = s.strip().lower()
    if s in TRUTHY: return True
    if s in FALSY:  return False
    # Fallback: non-empty string -> True
    return bool(s)

class SimplexAPIWatcher(threading.Thread):
    """
    Periodically reads simplexAPI.ini and triggers GUI actions on rising edges (OFF->ON).
    Supported flags (section [Simplex]):
      - Compile_all : triggers gui.compile_all()
      - Inspector   : opens the debug inspector via gui._open_debuginspector()
      - DeleteLogs  : deletes compile_*.log files in CWD

    Optional keys:
      - Mode        : "A" | "B" | "C" (sets gui.compile_mode_var before actions)
      - ThreadCount : integer, clamped to [1..gui.max_threads] (sets gui.thread_count_var)
      - AutoReset   : bool, if true rewrite flags back to OFF after a trigger

    Notes:
      * All GUI interactions are scheduled via Tk's main thread using master.after(0, ...).
      * Any exceptions are surfaced in the GUI status bar but do not kill the watcher loop.
    """
    daemon = True

    def __init__(self, gui, ini_path: Path, poll_interval: float = 1.0):
        super().__init__(name="SimplexAPIWatcher")
        self.gui = gui
        self.ini_path = Path(ini_path)
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._last = {
            "compile_all": False,
            "inspector": False,
            "deletelogs": False,
        }

    def stop(self):
        """Request the watcher to stop on the next loop iteration."""
        self._stop.set()

    def run(self):
        """Main polling loop. Reads INI, checks flags, triggers actions on rising edges."""
        while not self._stop.is_set():
            try:
                if self.ini_path.is_file():
                    cfg = configparser.ConfigParser()
                    cfg.optionxform = str  # keep case of keys
                    cfg.read(self.ini_path, encoding="utf-8")

                    section = "Simplex"
                    get = lambda k, d=None: (cfg[section].get(k, d) if cfg.has_section(section) else d)

                    # Optional: set Mode (A/B/C) before actions
                    mode = (get("Mode") or "").strip().upper()
                    if mode in {"A", "B", "C"} and mode != self.gui.compile_mode_var.get():
                        self.gui.master.after(0, lambda m=mode: self._set_mode(m))

                    # Optional: set ThreadCount
                    tc = get("ThreadCount")
                    if tc and tc.isdigit():
                        val = max(1, min(int(tc), self.gui.max_threads))
                        if val != int(self.gui.thread_count_var.get()):
                            self.gui.master.after(0, lambda v=val: self.gui.thread_count_var.set(v))

                    auto_reset = _to_bool(get("AutoReset", "true"))

                    # Check actions with rising-edge detection (OFF -> ON)
                    self._check_action(
                        key="Compile_all",
                        current=_to_bool(get("Compile_all")),
                        trigger=self._trigger_compile_all,
                        reset=lambda: self._reset_flag(cfg, section, "Compile_all") if auto_reset else None,
                    )

                    self._check_action(
                        key="Inspector",
                        current=_to_bool(get("Inspector")),
                        trigger=self._trigger_inspector,
                        reset=lambda: self._reset_flag(cfg, section, "Inspector") if auto_reset else None,
                    )

                    self._check_action(
                        key="DeleteLogs",
                        current=_to_bool(get("DeleteLogs")),
                        trigger=self._trigger_delete_logs,
                        reset=lambda: self._reset_flag(cfg, section, "DeleteLogs") if auto_reset else None,
                    )

                    # If AutoReset is enabled, write back potential flag changes
                    if auto_reset and cfg.has_section(section):
                        with open(self.ini_path, "w", encoding="utf-8") as f:
                            cfg.write(f)

                time.sleep(self.poll_interval)
            except Exception as e:
                # Report errors to the GUI status bar; keep the loop alive.
                self.gui.master.after(0, lambda: self.gui.set_status(f"SimplexAPI error: {e}", hold_ms=2500))
                time.sleep(self.poll_interval)

    def _check_action(self, key: str, current: bool, trigger: Callable[[], None], reset: Callable[[], None] | None):
        """Fire trigger on rising edge (last False -> current True)."""
        last = self._last.get(key.lower(), False)
        if current and not last:
            trigger()
            if reset:
                reset()
        self._last[key.lower()] = current

    def _set_mode(self, mode: str):
        """Apply compile mode in GUI safely on the Tk thread."""
        self.gui.compile_mode_var.set(mode)
        self.gui._toggle_mode()

    # ---- Triggers scheduled on the Tk main thread ----
    def _trigger_compile_all(self):
        self.gui.master.after(0, lambda: self.gui.compile_all())

    def _trigger_inspector(self):
        self.gui.master.after(0, lambda: self.gui._open_debuginspector())

    def _trigger_delete_logs(self):
        def _do():
            count = 0
            for p in Path.cwd().glob("compile_*.log"):
                try:
                    p.unlink()
                    count += 1
                except Exception:
                    pass
            self.gui.set_status(f"Logs deleted: {count} file(s).", hold_ms=2500)
        self.gui.master.after(0, _do)

    def _reset_flag(self, cfg: configparser.ConfigParser, section: str, key: str):
        """Write a single flag back to OFF in the config object."""
        if not cfg.has_section(section):
            cfg.add_section(section)
        cfg[section][key] = "OFF"
