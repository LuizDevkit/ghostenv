from .envfile import is_secret_name

def analyze(scan_result, env_dict, example_dict):
    code_vars = scan_result["vars"]
    ghosts = []
    for name, occs in code_vars.items():
        has_default = any(o.get("has_default") for o in occs)
        in_env = name in env_dict
        in_example = name in example_dict
        if not in_env and not in_example:
            status = "missing"
        elif not in_env and in_example:
            status = "missing_in_env"
        elif in_env and not in_example:
            status = "undocumented"
        else:
            status = "ok"
        ghosts.append({"name": name, "status": status, "occurrences": occs, "count": len(occs), "has_default": has_default, "is_secret": is_secret_name(name), "first_file": occs[0]["file"] if occs else "", "first_line": occs[0]["line"] if occs else 0})
    dead = []
    for src, label in [(env_dict, ".env"), (example_dict, ".env.example")]:
        for name in src:
            if name not in code_vars:
                dead.append({"name": name, "source": label})
    order = {"missing": 0, "missing_in_env": 1, "undocumented": 2, "ok": 3}
    ghosts.sort(key=lambda x: (order[x["status"]], -x["count"]))
    return {"ghosts": ghosts, "dead": dead, "total_code": len(code_vars)}

def fake_value(name: str) -> str:
    n = name.upper()
    if "URL" in n or "DSN" in n:
        return "postgresql://user:password@localhost:5432/db"
    if "PORT" in n:
        return "8000"
    if "DEBUG" in n or "ENABLE" in n:
        return "false"
    if "SECRET" in n or "TOKEN" in n or "KEY" in n or "PASSWORD" in n:
        return "change-me-in-production"
    if "EMAIL" in n:
        return "dev@example.com"
    if "HOST" in n:
        return "localhost"
    return "your-value-here"
