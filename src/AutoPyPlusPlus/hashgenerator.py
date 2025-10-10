#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import os
import sys
from typing import List

# ------------------------ Einstellungen ------------------------
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

FIXED_ROOT: str | None = None  

# ------------------------ Hash-Logik ------------------------

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
            if ext.lower() == ".py" and stem in ALLOWED_STEMS:
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
    return h.hexdigest(), files

# ------------------------ Main (keine CLI) ------------------------

def main() -> int:
    try:
        root = FIXED_ROOT or os.getcwd()
        validate = True  # immer Syntax-Check an
        # einmal Dateien sammeln (für Count-Ausgabe)
        files = list_valid_py_files(root, validate_syntax=validate)

        print(f"# Root: {os.path.abspath(root)}")
        print(f"# Syntax-Check: {'ON' if validate else 'OFF'}")
        print(f"# Dateien: {len(files)}")
        if not files:
            print("# WARN: Keine passenden Dateien gefunden.")

        # alle Hashes aus SUPPORTED berechnen
        for alg in SUPPORTED:
            digest, _ = compute_dir_hash(root, algorithm=alg, validate_syntax=validate)
            print(f"{alg}: {digest}")

        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
