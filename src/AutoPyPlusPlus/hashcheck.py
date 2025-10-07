#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import os
import sys
import subprocess
from urllib.parse import urlparse
from typing import List, Dict

# ------------------------ Configuration -------------------------

HASH_URL = "https://github.com/melatroid/autoPyPlusPlus/blob/main/hash.txt"

SUPPORTED = ("sha256", "sha384", "sha512", "sha3_512", "blake2b_512")
EXCLUDE_DIRS = {".git", "__pycache__", "venv", ".venv", "build", "dist", "node_modules"}
ALLOWED_STEMS = {
    "CPA0000000",
    "CPB0000000",
    "CPC0000000",
    "CPD0000000",
    "CPE0000000",
    "CPF0000000",
    "CPG0000000"
    #"gui",
    #"core",
    #"compiler",
    #"projecteditor",
    #"pytesteditor",
    #"sphinxeditor",
    #"speceditor",
    #"nuitkaeditor",
    #"gcceditor",
    #"hashcheck",
    #"apyeditor"
}
ALLOWED_STEMS_LOWER = {s.lower() for s in ALLOWED_STEMS}

# ------------------------ Execution directory -------------------

def get_execution_dir() -> str:
    """
    Always use the directory where this script/executable resides,
    regardless of where the process was launched from.
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return base

# ------------------------ Hash logic ----------------------------

def _open_binary(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

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

def list_valid_py_files(root: str, validate_syntax: bool = True) -> List[str]:
    root_abs = os.path.abspath(root)
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_abs):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            stem, ext = os.path.splitext(fn)
            if ext.lower() == ".py" and (stem in ALLOWED_STEMS or stem.lower() in ALLOWED_STEMS_LOWER):
                full = os.path.join(dirpath, fn)
                if not validate_syntax or _is_valid_python_source(full):
                    files.append(full)
    files.sort(key=lambda p: os.path.relpath(p, root_abs).replace(os.sep, "/"))
    return files

def _make_hasher(name: str):
    if name == "blake2b_512":
        return hashlib.blake2b(digest_size=64)
    try:
        return hashlib.new(name)
    except Exception as e:
        raise ValueError(f"Unsupported algorithm: {name}") from e

def compute_dir_hash(root: str, algorithm: str = "sha512", validate_syntax: bool = True) -> str:
    if algorithm not in SUPPORTED:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    files = list_valid_py_files(root, validate_syntax=validate_syntax)
    h = _make_hasher(algorithm)
    root_abs = os.path.abspath(root)
    for path in files:
        rel = os.path.relpath(path, root_abs).replace(os.sep, "/")
        header = f"FILE:{rel}\n".encode("utf-8")
        content = _open_binary(path)
        h.update(header)
        h.update(content)
        h.update(b"\n")
    return h.hexdigest()

# ------------------------ Fetch & parse via curl ----------------

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

def fetch_text_via_curl_fixed(timeout_sec: int = 20) -> str:
    raw_url = _to_raw_github(HASH_URL)
    try:
        res = subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout_sec), raw_url],
            check=True, capture_output=True, text=True
        )
        return res.stdout
    except FileNotFoundError:
        raise RuntimeError("curl not found. Please install curl.")
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() if e.stderr else f"Exit {e.returncode}"
        raise RuntimeError(f"curl error while fetching: {err}")

def parse_only_algo_lines(text: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ":" not in ln:
            continue
        key, val = ln.split(":", 1)
        alg = key.strip().lower()
        if alg not in SUPPORTED:
            continue
        hexstr = "".join(val.strip().lower().split())
        mapping[alg] = hexstr
    return mapping

def _norm_hex(s: str) -> str:
    return "".join((s or "").strip().lower().split())

# ------------------------ CLI Main ---------------------------------------------

def main() -> int:
    project_root = get_execution_dir()
    try:
        txt = fetch_text_via_curl_fixed()
    except Exception as e:
        print(f"[ERROR] Could not load reference file: {e}", file=sys.stderr)
        return 1

    ref_hashes = parse_only_algo_lines(txt)
    if not ref_hashes:
        print("[ERROR] No algorithm lines found in the reference file.", file=sys.stderr)
        return 1

    algos = [a for a in SUPPORTED if a in ref_hashes]
    if not algos:
        print("[ERROR] No supported algorithms present in the reference file.", file=sys.stderr)
        return 1

    overall_ok = True
    for alg in algos:
        expected = _norm_hex(ref_hashes.get(alg, ""))
        if not expected or any(c not in "0123456789abcdef" for c in expected):
            print(f"[{alg}] ERROR: Invalid reference hash.")
            overall_ok = False
            continue

        try:
            computed = compute_dir_hash(project_root, algorithm=alg, validate_syntax=True)
        except Exception as e:
            print(f"[{alg}] ERROR during computation: {e}")
            overall_ok = False
            continue

        computed_norm = _norm_hex(computed)
        if computed_norm == expected:
            print(f"[{alg}] OK  – hashes match")
        else:
            total = max(len(expected), len(computed_norm))
            first_diff = next((i for i in range(total)
                               if (expected[i] if i < len(expected) else None) !=
                                  (computed_norm[i] if i < len(computed_norm) else None)), -1)
            if first_diff < 0 and len(expected) != len(computed_norm):
                first_diff = min(len(expected), len(computed_norm))
            print(f"[{alg}] MISMATCH – first difference at position {first_diff}")
            print(f"   expected: {expected}")
            print(f"   computed: {computed_norm}")
            overall_ok = False

    print()
    if overall_ok:
        print("RESULT: ✅ All verified hashes match.")
        return 0
    else:
        print("RESULT: ❌ At least one hash does not match.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
