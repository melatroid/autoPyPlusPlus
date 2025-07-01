# spec_parser.py
"""
Smarter AST-Parser für PyInstaller-.spec-Dateien (Korrektur).

- Die beiden visit_Assign-Methoden wurden zu einer zusammengefasst.
- Statt super().visit_Assign(node) wird nun self.generic_visit(node) verwendet,
  um innerhalb des Assign-Knotens weiter zu traversieren.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path
from typing import Any, Optional

from .project import Project


# --------------------------------------------------------------------------- #
# AST-Hilfsfunktionen
# --------------------------------------------------------------------------- #
def _literal(node: ast.AST) -> Any | None:
    """Versucht, einen AST-Knoten in ein echtes Python-Literal zu evaluieren."""
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _bool(node: ast.AST, default: bool = False) -> bool:
    """Konvertiert einen AST-Knoten in bool, falls möglich."""
    val = _literal(node)
    return bool(val) if val is not None else default


# --------------------------------------------------------------------------- #
# Smarter Parser-Klasse
# --------------------------------------------------------------------------- #
class _SpecVisitor(ast.NodeVisitor):
    """
    Liest .spec-AST in zwei Schritten:
      1. Symboltabelle aufbauen (Konstanten & einfache for-append-Listen)
      2. Analysis/EXE/pyarmor_config auflösen
    """

    def __init__(self) -> None:
        self.symbols: dict[str, Any] = {}
        self.analysis_calls: list[ast.Call] = []
        self.exe_calls: list[ast.Call] = []
        self.pyarmor_dict: Optional[ast.Dict] = None

    # -------- 1. Runde: konstante Zuweisungen & for-append-Schleifen --------
    def visit_Assign(self, node: ast.Assign) -> None:
        # 1a) Konstantenzuweisung: name = <literal>
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            val = _literal(node.value)
            if val is not None:
                self.symbols[name] = val

        # 1b) Einfache for-append-Schleifen erkennen:
        #     for x in [..]: liste.append(x)
        #     → sammle Literal-Liste in self.symbols[liste]
        if isinstance(node.targets[0], ast.Name):
            # wir lassen die For-Schleife separat laufen, aber
            # hier prüfen wir nur pyarmor_config
            if (
                node.targets[0].id == "pyarmor_config"
                and isinstance(node.value, ast.Dict)
            ):
                self.pyarmor_dict = node.value

        # Innerhalb des Assign-Knotens weiter traversieren (z. B. For im Wert)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        # Unterstützt: for elem in ['a','b']: mylist.append(elem)
        if (
            isinstance(node.target, ast.Name)
            and isinstance(node.iter, (ast.List, ast.Tuple))
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Call)
        ):
            call = node.body[0].value
            if (
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "append"
                and isinstance(call.func.value, ast.Name)
            ):
                list_name = call.func.value.id
                const_seq = _literal(node.iter)
                if const_seq is not None:
                    self.symbols.setdefault(list_name, []).extend(const_seq)

        # Body weiter untersuchen (z. B. verschachtelte Ifs)
        self.generic_visit(node)

    # -------- 2. Runde: Analysis / EXE-Calls sammeln ------------------------
    def visit_Call(self, node: ast.Call) -> None:
        # func kann Name (Analysis, EXE) oder Attribute (.Analysis)
        func_name = getattr(node.func, "id", "")
        if not func_name and isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name == "Analysis":
            self.analysis_calls.append(node)
        elif func_name == "EXE":
            self.exe_calls.append(node)

        # auch in den Unter-Knoten weiter suchen
        self.generic_visit(node)


# --------------------------------------------------------------------------- #
# 1)  .spec  ➜  Project
# --------------------------------------------------------------------------- #
def parse_spec_file(spec_file: str | Path) -> Project:
    """
    Liest eine PyInstaller-.spec-Datei *sicher* (ohne Ausführung) ein
    und gibt ein `Project`-Objekt zurück.
    """
    src = Path(spec_file).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(spec_file))

    visitor = _SpecVisitor()
    visitor.visit(tree)

    proj = Project(script="")
    proj.spec_file = str(spec_file)

    # ---------- Analysis-Block (wir nehmen den erste gefundene Call) ------------
    if visitor.analysis_calls:
        call = visitor.analysis_calls[0]
        for kw in call.keywords:
            val_node = kw.value
            # Variable → ersetze durch das Literal in visitor.symbols
            if isinstance(val_node, ast.Name) and val_node.id in visitor.symbols:
                literal_value = visitor.symbols[val_node.id]
                # AST neu erzeugen, damit _literal später funktioniert
                val_node = ast.parse(repr(literal_value)).body[0].value

            match kw.arg:
                case "scripts":
                    seq = _literal(val_node) or []
                    proj.display_script = seq[0] if seq else ""
                case "hiddenimports":
                    proj.hidden_imports = _literal(val_node) or []
                case "datas":
                    datas = _literal(val_node) or []
                    proj.datas = [(src, dst) for src, dst in datas]
                case "runtime_hooks":
                    rh = _literal(val_node) or []
                    proj.runtime_hook = rh[0] if rh else ""
                case "pathex":
                    proj.pathex = _literal(val_node) or []

    # ---------- EXE-Block ----------------------------------------------------
    if visitor.exe_calls:
        call = visitor.exe_calls[0]
        for kw in call.keywords:
            val_node = kw.value
            if isinstance(val_node, ast.Name) and val_node.id in visitor.symbols:
                literal_value = visitor.symbols[val_node.id]
                val_node = ast.parse(repr(literal_value)).body[0].value

            match kw.arg:
                case "name":
                    proj.name = _literal(val_node) or proj.name
                case "icon":
                    proj.icon = _literal(val_node) or ""
                case "console":
                    proj.console = _bool(val_node, True)
                case "exclude_binaries":
                    proj.onefile = not _bool(val_node, False)
                case "debug":
                    proj.debug = _bool(val_node)
                case "strip":
                    proj.strip = _bool(val_node)
                case "upx":
                    proj.upx = _bool(val_node)
                case "upx_exclude":
                    proj.upx_exclude = _literal(val_node) or []
                case "splash" | "splash_image":
                    proj.splash = _literal(val_node) or ""
                case "version":
                    proj.version = _literal(val_node) or ""
                case "clean":
                    proj.clean = _bool(val_node)

    # ---------- PyArmor-Dict ------------------------------------------------
    if visitor.pyarmor_dict:
        for key_node, val_node in zip(visitor.pyarmor_dict.keys, visitor.pyarmor_dict.values):
            key = _literal(key_node)
            match key:
                case "use_pyarmor":
                    proj.use_pyarmor = _bool(val_node)
                case "pyarmor_dist_dir":
                    proj.pyarmor_dist_dir = _literal(val_node) or ""
                case "no_runtime_key":
                    proj.no_runtime_key = _bool(val_node)

    return proj


# --------------------------------------------------------------------------- #
# 2)  Project  ➜  .spec-Datei
# --------------------------------------------------------------------------- #
def generate_spec_file(project: Project) -> str:
    """
    Baut den Text einer .spec-Datei aus den Feldern eines Project-Objekts.
    """
    def _list_to_py(seq: list[Any]) -> str:
        return "[" + ", ".join(f"'{item}'" for item in seq) + "]" if seq else "[]"

    datas_py = "[" + ", ".join(f"('{src}', '{dst}')" for src, dst in project.datas) + "]"
    hidden_py = _list_to_py(project.hidden_imports)
    runtime_hooks_py = _list_to_py([project.runtime_hook] if project.runtime_hook else [])
    pathex_py = _list_to_py(project.pathex)
    upx_excl_py = _list_to_py(project.upx_exclude)

    splash_part = f", splash='{project.splash}'" if project.splash else ""
    version_part = f", version='{project.version}'" if project.version else ""

    analysis_block = textwrap.dedent(f"""
        # -*- mode: python ; coding: utf-8 -*-
        block_cipher = None

        a = Analysis(
            ['{project.script}'],
            pathex={pathex_py},
            binaries=[],
            datas={datas_py},
            hiddenimports={hidden_py},
            hookspath=[],
            runtime_hooks={runtime_hooks_py},
            excludes=[],
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=block_cipher,
            noarchive=False
        )

        pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
    """)

    exe_block = textwrap.dedent(f"""
        exe = EXE(
            pyz,
            a.scripts,
            [],
            exclude_binaries={'False' if project.onefile else 'True'},
            name='{project.name}',
            debug={project.debug},
            bootloader_ignore_signals=False,
            strip={project.strip},
            upx={project.upx},
            upx_exclude={upx_excl_py},
            console={project.console},
            icon='{project.icon}'{version_part}{splash_part}
        )
    """)

    collect_block = ""
    if not project.onefile:
        collect_block = textwrap.dedent(f"""
            coll = COLLECT(
                exe,
                a.binaries,
                a.zipfiles,
                a.datas,
                strip={project.strip},
                upx={project.upx},
                upx_exclude={upx_excl_py},
                name='{project.name}'
            )
        """)

    return (analysis_block + exe_block + collect_block).strip()
