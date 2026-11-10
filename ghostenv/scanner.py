import ast, re
from pathlib import Path
from collections import defaultdict

PY_EXTS = {".py"}
JS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
JS_PATTERNS = [
    re.compile(r"process\.env\.([A-Z_][A-Z0-9_]*)"),
    re.compile(r"process\.env\[\s*['\"]([A-Z_][A-Z0-9_]*)['\"]\s*\]"),
    re.compile(r"import\.meta\.env\.([A-Z_][A-Z0-9_]*)"),
    re.compile(r"Bun\.env\.([A-Z_][A-Z0-9_]*)"),
]
SKIP_DIRS = {".git","node_modules",".venv","venv","__pycache__",".next","dist","build",".idea",".vscode","coverage"}

def _iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in PY_EXTS | JS_EXTS:
            yield p

def _scan_python_file(path: Path, root: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}
    found = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            is_getenv = isinstance(f, ast.Attribute) and f.attr in ("getenv","get") and isinstance(f.value, ast.Attribute) and f.value.attr in ("environ",)
            is_os_getenv = isinstance(f, ast.Attribute) and f.attr == "getenv" and isinstance(f.value, ast.Name) and f.value.id == "os"
            if (is_getenv or is_os_getenv) and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                name = node.args[0].value
                has_default = len(node.args) >= 2 or len(node.keywords) > 0
                found[name].append({"file": str(path.relative_to(root)), "line": node.lineno, "has_default": has_default, "kind": "getenv"})
        if isinstance(node, ast.Subscript):
            v = node.value
            if isinstance(v, ast.Attribute) and v.attr == "environ" and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                found[node.slice.value].append({"file": str(path.relative_to(root)), "line": node.lineno, "has_default": False, "kind": "environ[]"})
    return dict(found)

def _scan_js_file(path: Path, root: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    found = defaultdict(list)
    for pat in JS_PATTERNS:
        for m in pat.finditer(text):
            name = m.group(1)
            line = text.count("\n", 0, m.start()) + 1
            found[name].append({"file": str(path.relative_to(root)), "line": line, "has_default": False, "kind": "process.env"})
    return dict(found)

def scan_project(root="."):
    root = Path(root).resolve()
    all_vars = defaultdict(list)
    files_scanned = 0
    for p in _iter_files(root):
        files_scanned += 1
        res = _scan_python_file(p, root) if p.suffix.lower() in PY_EXTS else _scan_js_file(p, root)
        for k, v in res.items():
            all_vars[k].extend(v)
    return {"root": str(root), "files_scanned": files_scanned, "vars": dict(all_vars)}
