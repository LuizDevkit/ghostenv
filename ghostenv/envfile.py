import re
from pathlib import Path

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")

def parse_env_file(path):
    p = Path(path)
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE.match(line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out

def is_secret_name(name: str) -> bool:
    n = name.upper()
    return any(k in n for k in ["SECRET","TOKEN","KEY","PASSWORD","PASSWD","PRIVATE","AUTH","CREDENTIAL","DSN","API_"])
