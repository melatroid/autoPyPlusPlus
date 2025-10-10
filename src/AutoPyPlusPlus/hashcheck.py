
# hashcheck.py
from __future__ import annotations
import hashlib
import os
import sys
import subprocess
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse
# ------------------------ Defaults / Config -------------------------
DEFAULT_HASH_URL = "https://github.com/melatroid/autoPyPlusPlus/blob/main/hash.txt"
SUPPORTED = ("sha256", "sha384", "sha512", "sha3_512", "blake2b_512")
DEFAULT_EXCLUDE_DIRS = {".git", "__pycache__", "venv", ".venv", "build", "dist", "node_modules"}
DEFAULT_ALLOWED_STEMS = {
    "CPA0000000",
    "CPB0000000",
    "CPC0000000",
    "CPD0000000",
    "CPE0000000",
    "CPF0000000",
    "CPG0000000"
    #"gui",
    "core",
    "compiler",
    "hashcheck",
    #"projecteditor",
    #"pytesteditor",
    #"sphinxeditor",
    #"speceditor",
    #"nuitkaeditor",
    #"gcceditor",
    #"apyeditor"
}
DEFAULT_ALLOWED_STEMS_LOWER = {s.lower() for s in DEFAULT_ALLOWED_STEMS}

# ------------------------ Public Result Types ----------------------

@dataclass
class AlgoResult:
    algorithm: str
    expected: Optional[str]           # None, falls fehlt/ungültig
    computed: Optional[str]           # None bei Fehler
    match: bool
    first_diff: Optional[int] = None  # Index der ersten Abweichung
    error: Optional[str] = None       # Fehlermeldung, falls Berechnung scheiterte

@dataclass
class VerificationSummary:
    overall_ok: bool
    results: List[AlgoResult]
    used_algorithms: List[str]

# ------------------------ Utilities --------------------------------

def get_execution_dir() -> str:
    """Verzeichnis, in dem dieses Script/Executable liegt."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return base

def _norm_hex(s: str) -> str:
    return "".join((s or "").strip().lower().split())

def _to_raw_github(url: str) -> str:
    try:
        u = urlparse(url)
    except Exception:
        return url
    if u.netloc == "raw.githubusercontent.com":
        return url
    if u.netloc == "github.com":
        parts = u.path.lstrip("/").split("/")
        if len(parts) >= 5 and parts[2] == "blob":
            owner, repo, _blob, branch, *rest = parts
            raw_path = "/".join(rest)
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{raw_path}"
    return url

# ------------------------ File listing / parsing -------------------

def _is_valid_python_source(path: str) -> bool:
    try:
        text = open(path, "r", encoding="utf-8").read()
    except UnicodeDecodeError:
        return False
    try:
        compile(text, path, "exec")
        return True
    except SyntaxError:
        return False

def list_valid_py_files(
    root: str,
    validate_syntax: bool = True,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    allowed_stems: Iterable[str] = DEFAULT_ALLOWED_STEMS,
) -> List[str]:
    """Gibt deterministisch sortierte Liste passender .py-Dateien zurück."""
    allowed_stems = set(allowed_stems)
    allowed_stems_lower = {s.lower() for s in allowed_stems}

    root_abs = os.path.abspath(root)
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_abs, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fn in filenames:
            stem, ext = os.path.splitext(fn)
            if ext.lower() == ".py" and (stem in allowed_stems or stem.lower() in allowed_stems_lower):
                full = os.path.join(dirpath, fn)
                if not validate_syntax or _is_valid_python_source(full):
                    files.append(full)
    files.sort(key=lambda p: os.path.relpath(p, root_abs).replace(os.sep, "/"))
    return files

# ------------------------ Hashing ----------------------------------

def _make_hasher(name: str):
    if name == "blake2b_512":
        return hashlib.blake2b(digest_size=64)
    try:
        return hashlib.new(name)
    except Exception as e:
        raise ValueError(f"Unsupported algorithm: {name}") from e

def _update_hasher_with_file(h, path: str, chunk_size: int = 1024 * 1024) -> None:
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)

def compute_dir_hash(
    root: str,
    algorithm: str = "sha512",
    validate_syntax: bool = True,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    allowed_stems: Iterable[str] = DEFAULT_ALLOWED_STEMS,
) -> str:
    """Berechnet den Verzeichnis-Hash (deterministische Reihenfolge, Streaming)."""
    if algorithm not in SUPPORTED:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    files = list_valid_py_files(
        root,
        validate_syntax=validate_syntax,
        exclude_dirs=exclude_dirs,
        allowed_stems=allowed_stems,
    )
    h = _make_hasher(algorithm)
    root_abs = os.path.abspath(root)
    for path in files:
        rel = os.path.relpath(path, root_abs).replace(os.sep, "/")
        h.update(f"FILE:{rel}\n".encode("utf-8"))
        _update_hasher_with_file(h, path)
        h.update(b"\n")
    return h.hexdigest()

# ------------------------ Reference loading -----------------------

def parse_reference_hashes(text: str) -> Dict[str, str]:
    """
    Erwartet Zeilen im Format: <algo>: <hex>
    Ignoriert unbekannte Algos, normalisiert Leerzeichen/Case.
    """
    mapping: Dict[str, str] = {}
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ":" not in ln:
            continue
        key, val = ln.split(":", 1)
        alg = key.strip().lower()
        if alg not in SUPPORTED:
            continue
        hexstr = _norm_hex(val)
        mapping[alg] = hexstr
    return mapping

def fetch_reference_text(
    source: str = DEFAULT_HASH_URL,
    timeout_sec: int = 20,
    retries: int = 1,
    backoff: float = 0.6,
) -> str:
    """
    Lädt Referenztext.
    - Wenn 'source' ein existierender Pfad ist -> lokale Datei lesen.
    - Sonst HTTP holen (bevorzugt curl; Fallback urllib).
    """
    if os.path.exists(source):
        return open(source, "r", encoding="utf-8").read()

    raw_url = _to_raw_github(source)
    last_err: Optional[str] = None
    for attempt in range(retries + 1):
        # Versuch mit curl
        try:
            out = subprocess.run(
                ["curl", "-fsSL", "--max-time", str(timeout_sec), raw_url],
                check=True, capture_output=True, text=True
            ).stdout
            return out
        except FileNotFoundError:
            # Fallback auf urllib
            try:
                import urllib.request
                with urllib.request.urlopen(raw_url, timeout=timeout_sec) as r:
                    return r.read().decode("utf-8")
            except Exception as e:
                last_err = f"urllib error: {e}"
        except subprocess.CalledProcessError as e:
            last_err = (e.stderr.strip() if e.stderr else f"curl exit {e.returncode}")
        # Backoff
        if attempt < retries:
            import time
            time.sleep(backoff * (2 ** attempt))
    raise RuntimeError(f"Failed to fetch reference from {source}: {last_err or 'unknown error'}")

# ------------------------ Core Verification API -------------------

def verify_against_reference(
    project_root: str,
    reference_source: str = DEFAULT_HASH_URL,
    algorithms: Optional[Sequence[str]] = None,
    validate_syntax: bool = True,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    allowed_stems: Iterable[str] = DEFAULT_ALLOWED_STEMS,
) -> VerificationSummary:
    """
    Haupt-API: Prüft, ob berechnete Hashes zu den Referenz-Hashes passen.

    Returns:
        VerificationSummary mit per-Algorithmus-Ergebnissen und overall_ok.
    Raises:
        RuntimeError, wenn Referenzquelle nicht lesbar/parsbar ist.
        ValueError, wenn Algorithmen ungültig sind.
    """
    ref_text = fetch_reference_text(reference_source)
    ref_hashes = parse_reference_hashes(ref_text)
    if not ref_hashes:
        raise RuntimeError("No algorithm lines found in reference source.")

    algos = list(algorithms) if algorithms else [a for a in SUPPORTED if a in ref_hashes]
    if not algos:
        raise ValueError("No supported algorithms present in the reference source.")

    results: List[AlgoResult] = []
    overall_ok = True

    for alg in algos:
        expected = ref_hashes.get(alg)
        if not expected or any(c not in "0123456789abcdef" for c in expected):
            results.append(AlgoResult(
                algorithm=alg, expected=expected, computed=None, match=False,
                error="Invalid or missing reference hash"
            ))
            overall_ok = False
            continue

        try:
            computed = compute_dir_hash(
                project_root,
                algorithm=alg,
                validate_syntax=validate_syntax,
                exclude_dirs=exclude_dirs,
                allowed_stems=allowed_stems,
            )
        except Exception as e:
            results.append(AlgoResult(
                algorithm=alg, expected=expected, computed=None, match=False, error=str(e)
            ))
            overall_ok = False
            continue

        comp_norm = _norm_hex(computed)
        exp_norm = _norm_hex(expected)
        if comp_norm == exp_norm:
            results.append(AlgoResult(
                algorithm=alg, expected=exp_norm, computed=comp_norm, match=True
            ))
        else:
            total = max(len(exp_norm), len(comp_norm))
            first_diff = next((i for i in range(total)
                               if (exp_norm[i] if i < len(exp_norm) else None) !=
                                  (comp_norm[i] if i < len(comp_norm) else None)), -1)
            if first_diff < 0 and len(exp_norm) != len(comp_norm):
                first_diff = min(len(exp_norm), len(comp_norm))
            results.append(AlgoResult(
                algorithm=alg, expected=exp_norm, computed=comp_norm, match=False, first_diff=first_diff
            ))
            overall_ok = False

    return VerificationSummary(overall_ok=overall_ok, results=results, used_algorithms=algos)

# ------------------------ Optional: CLI wrapper -------------------

def _main_cli(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Verify directory hashes against reference file/URL.")
    p.add_argument("--root", default=get_execution_dir(), help="Projektwurzel (Default: Script-Verzeichnis)")
    p.add_argument("--algo", choices=SUPPORTED, action="append", help="Algorithmen (mehrfach möglich)")
    p.add_argument("--no-syntax-check", action="store_true", help="Syntax-Check deaktivieren")
    p.add_argument("--hash-source", default=DEFAULT_HASH_URL, help="Pfad/URL zu Referenz-Hashes")
    args = p.parse_args(argv)

    try:
        summary = verify_against_reference(
            project_root=args.root,
            reference_source=args.hash_source,
            algorithms=args.algo,
            validate_syntax=not args.no_syntax_check,
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    for r in summary.results:
        if r.error:
            print(f"[{r.algorithm}] ERROR: {r.error}")
        elif r.match:
            print(f"[{r.algorithm}] OK  – hashes match")
        else:
            print(f"[{r.algorithm}] MISMATCH – first difference at position {r.first_diff}")
            print(f"   expected: {r.expected}")
            print(f"   computed: {r.computed}")

    print()
    if summary.overall_ok:
        print("RESULT: ✅ All verified hashes match.")
        return 0
    else:
        print("RESULT: ❌ At least one hash does not match.")
        return 1

if __name__ == "__main__":
    sys.exit(_main_cli())
