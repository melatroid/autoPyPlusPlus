# spec_parser.py
from pathlib import Path
import ast
from .project import Project

def parse_spec_file(spec_file: str) -> Project | None:
    try:
        spec_path = Path(spec_file)
        with spec_path.open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(spec_path))

        project = Project(script="")
        project.spec_file = str(spec_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "a" and isinstance(node.value, ast.Call):
                        if getattr(node.value.func, "id", None) == "Analysis":
                            for keyword in node.value.keywords:
                                if keyword.arg == "scripts" and hasattr(keyword.value, "elts") and keyword.value.elts:
                                    elt = keyword.value.elts[0]
                                    project.script = getattr(elt, "s", getattr(elt, "value", ""))
                                elif keyword.arg == "hiddenimports" and hasattr(keyword.value, "elts"):
                                    project.hidden_imports = ",".join(
                                        getattr(elt, "s", getattr(elt, "value", ""))
                                        for elt in keyword.value.elts
                                    )
                                elif keyword.arg == "datas" and hasattr(keyword.value, "elts"):
                                    project.add_data = ";".join(
                                        f"{getattr(elt.elts[0], 's', getattr(elt.elts[0], 'value', ''))}:{getattr(elt.elts[1], 's', getattr(elt.elts[1], 'value', ''))}"
                                        for elt in keyword.value.elts
                                    )
                                elif keyword.arg == "runtime_hooks" and hasattr(keyword.value, "elts") and keyword.value.elts:
                                    elt = keyword.value.elts[0]
                                    project.runtime_hook = getattr(elt, "s", getattr(elt, "value", ""))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "EXE":
                for keyword in node.keywords:
                    if keyword.arg == "name" and keyword.value:
                        project.name = getattr(keyword.value, "s", getattr(keyword.value, "value", ""))
                    elif keyword.arg == "icon" and keyword.value:
                        project.icon = getattr(keyword.value, "s", getattr(keyword.value, "value", ""))
                    elif keyword.arg == "console" and keyword.value:
                        project.console = getattr(keyword.value, "value", True) if isinstance(keyword.value, (ast.NameConstant, ast.Constant)) else True
                    elif keyword.arg == "debug" and keyword.value:
                        project.debug = getattr(keyword.value, "value", False) if isinstance(keyword.value, (ast.NameConstant, ast.Constant)) else False
                    elif keyword.arg == "strip" and keyword.value:
                        project.strip = getattr(keyword.value, "value", False) if isinstance(keyword.value, (ast.NameConstant, ast.Constant)) else False
                    elif keyword.arg == "upx" and keyword.value:
                        project.upx = getattr(keyword.value, "value", False) if isinstance(keyword.value, (ast.NameConstant, ast.Constant)) else False
                    elif keyword.arg == "splash" and keyword.value:
                        project.splash = getattr(keyword.value, "s", getattr(keyword.value, "value", ""))
        return project
    except Exception as e:
        print(f"Error parsing .spec file: {e}")
        return None

def generate_spec_file(project):
    datas = []
    if project.add_data:
        for entry in project.add_data.split(';'):
            if ':' in entry:
                src, dest = entry.split(':', 1)
                datas.append(f"('{src.strip()}', '{dest.strip()}')")

    datas_str = f"[{', '.join(datas)}]" if datas else "[]"
    hidden_imports = project.hidden_imports.split(',') if project.hidden_imports else []
    hidden_imports_str = "[" + ", ".join(f"'{m.strip()}'" for m in hidden_imports) + "]" if hidden_imports else "[]"
    runtime_hooks = f"[\"{project.runtime_hook}\"]" if project.runtime_hook else "[]"

    splash_part = f", splash='{project.splash}'" if project.splash else ""
    version_part = f", version='{project.version}'" if project.version else ""

    content = f"""
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['{project.script}'],
    pathex=[],
    binaries=[],
    datas={datas_str},
    hiddenimports={hidden_imports_str},
    hookspath=[],
    runtime_hooks={runtime_hooks},
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{project.name}',
    debug={project.debug},
    bootloader_ignore_signals=False,
    strip={project.strip},
    upx={project.upx},
    console={project.console},
    icon='{project.icon}'{version_part}{splash_part}
)
"""

    if not project.onefile:
        content += f"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip={project.strip},
    upx={project.upx},
    upx_exclude=[],
    name='{project.name}'
)
"""
    return content.strip()
