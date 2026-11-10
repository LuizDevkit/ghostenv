import json
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .scanner import scan_project
from .envfile import parse_env_file
from .analyzer import analyze, fake_value

console = Console()

@click.group()
@click.version_option("0.1.0", prog_name="ghostenv")
def main():
    """GhostEnv - cacador de variaveis fantasmas."""

@main.command()
@click.argument("path", default=".")
@click.option("--json", "as_json", is_flag=True, help="Saida em JSON para CI")
@click.option("--fail-on-ghost", is_flag=True, help="Exit 1 se houver fantasma (pra CI)")
def scan(path, as_json, fail_on_ghost):
    root = Path(path)
    result = scan_project(root)
    env = parse_env_file(root / ".env")
    example = parse_env_file(root / ".env.example")
    if not (root / ".env.example").exists() and (root / ".env.sample").exists():
        example = parse_env_file(root / ".env.sample")
    data = analyze(result, env, example)
    if as_json:
        click.echo(json.dumps({"files_scanned": result["files_scanned"], **data}, indent=2, ensure_ascii=False))
        raise SystemExit(1 if fail_on_ghost and any(g["status"] in ("missing", "missing_in_env") for g in data["ghosts"]) else 0)
    console.print(Panel(f"GhostEnv - {result['files_scanned']} arquivos escaneados | {data['total_code']} vars no codigo | {len(env)} no .env | {len(example)} no .env.example", style="bold magenta"))
    if not data["ghosts"] and not data["dead"]:
        console.print("[green]Nenhum fantasma! Seu .env esta em dia.[/green]")
        return
    table = Table(title="Variaveis encontradas no codigo")
    table.add_column("Variavel", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Usos")
    table.add_column("Onde")
    table.add_column("Segredo?")
    for g in data["ghosts"]:
        emoji = {"missing": "FALTANDO", "missing_in_env": "Falta no .env", "undocumented": "Sem doc no .example", "ok": "OK"}[g["status"]]
        style = "red" if g["status"] == "missing" else "yellow" if g["status"] != "ok" else "green"
        table.add_row(g["name"], f"[{style}]{emoji}[/{style}]", str(g["count"]), f"{g['first_file']}:{g['first_line']}", "sim" if g["is_secret"] else "-")
    console.print(table)
    if data["dead"]:
        console.print("\n[dim]Variaveis mortas (no .env mas nunca usadas):[/dim]")
        for d in data["dead"]:
            console.print(f"  - {d['name']} ({d['source']})")
    console.print("\n[dim]Dica: rode ghostenv fix para gerar um .env.example perfeito[/dim]")
    if fail_on_ghost and any(g["status"] in ("missing", "missing_in_env") for g in data["ghosts"]):
        raise SystemExit(1)

@main.command()
@click.argument("path", default=".")
@click.option("--force", is_flag=True, help="Sobrescreve .env.example existente")
def fix(path, force):
    root = Path(path)
    result = scan_project(root)
    env = parse_env_file(root / ".env")
    example = parse_env_file(root / ".env.example")
    data = analyze(result, env, example)
    out = root / ".env.example"
    if out.exists() and not force:
        console.print("[yellow].env.example ja existe. Use --force para sobrescrever.[/yellow]")
        return
    lines = ["# Gerado por GhostEnv - NAO coloque segredos reais aqui", "# Rode: ghostenv scan para verificar fantasmas", ""]
    for g in sorted(data["ghosts"], key=lambda x: x["name"]):
        lines.append(f"# Usada em {g['first_file']}:{g['first_line']} ({g['count']}x)" + ("  # tem default" if g["has_default"] else ""))
        lines.append(f"{g['name']}={fake_value(g['name'])}")
    for d in data["dead"]:
        if d["source"] == ".env.example":
            lines.append(f"# Morta? {d['name']} estava no .example mas nao e usada")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[green].env.example gerado com {len(data['ghosts'])} variaveis em {out}[/green]")

@main.command()
@click.argument("path", default=".")
def doctor(path):
    root = Path(path)
    result = scan_project(root)
    env = parse_env_file(root / ".env")
    example = parse_env_file(root / ".env.example")
    data = analyze(result, env, example)
    missing = [g for g in data["ghosts"] if g["status"] in ("missing", "missing_in_env")]
    if not missing:
        console.print("[green]Seu .env ja cobre tudo. Nada para curar.[/green]")
        return
    target = root / ".env"
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    with target.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n# Adicionado por ghostenv doctor (valores FAKE - troque antes de usar de verdade)\n")
        for g in missing:
            f.write(f"{g['name']}={fake_value(g['name'])}\n")
    console.print(f"[green]Doctor: adicionou {len(missing)} variaveis FAKE no .env. Troque os segredos reais![/green]")
    for g in missing:
        console.print(f"  - {g['name']}")

if __name__ == "__main__":
    main()
