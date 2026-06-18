"""Renderizado colorido para el terminal (`ds_harness status`).

El archivo .md sigue siendo la fuente de verdad; este módulo solo formatea
la salida en pantalla con colores ANSI para facilitar la lectura.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .. import config
from . import store
from .views import _rel

# ── Colores ANSI ─────────────────────────────────────────────────────────────
R  = "\033[0m"   # reset
B  = "\033[1m"   # bold
D  = "\033[2m"   # dim
CY = "\033[36m"  # cyan  → títulos de sección
GR = "\033[32m"  # green → ok / located
YE = "\033[33m"  # yellow → advertencia / inferred
MG = "\033[35m"  # magenta → nombres de columna
WH = "\033[97m"  # white brillante → artefactos


def _enable_windows_ansi() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    _enable_windows_ansi()
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _sec(title: str) -> str:
    bar = "─" * max(0, 50 - len(title))
    return f"\n{B}{CY}── {title} {bar}{R}\n"


def _empty(hint: str) -> str:
    return f"  {D}(vacío — {hint}){R}\n"


# ── Secciones ────────────────────────────────────────────────────────────────

def _map(data: dict | None) -> str:
    out = _sec("ESTRUCTURA")
    if not data or not data.get("entries"):
        return out + _empty("aún no escaneado")

    entries = data["entries"]
    dirs  = [e for e in entries if e.get("type") == "dir"]
    files = [e for e in entries if e.get("type") != "dir"]
    out += f"  {D}{data.get('scanned_at', '')[:19].replace('T', ' ')} · {len(entries)} nodos  "
    out += f"({len(dirs)} carpetas, {len(files)} archivos){R}\n\n"

    top_dirs  = [e for e in dirs  if "/" not in e["path"].strip("/")]
    top_files = [e for e in files if "/" not in e["path"]]

    if top_dirs:
        out += "  " + "   ".join(f"{CY}📁 {e['path']}{R}" for e in top_dirs) + "\n"
    for e in top_files:
        out += f"  {e['path']}\n"
    return out


def _sources(data: dict | None, project_root: Path) -> str:
    out = _sec("FUENTES DE DATOS")
    if not data or not data.get("sources"):
        return out + _empty("no se detectaron fuentes referenciadas")

    for s in data["sources"]:
        identity = _rel(s["identity"], project_root)
        ok = s.get("status") == "located"
        icon = f"{GR}✓" if ok else f"{YE}?"
        out += f"  {icon} {B}{identity}{R}\n"
        refs = [
            f"{r['code_file']}:{r['line']}" if r.get("line") else r["code_file"]
            for r in s.get("references", [])
        ]
        if refs:
            out += f"    {D}→ {', '.join(refs)}{R}\n"
        out += "\n"
    return out


def _changelog(data: dict | None) -> str:
    out = _sec("BITÁCORA GIT")
    if not data or not data.get("git_available"):
        return out + _empty("git no disponible o sin commits")
    commits = data.get("commits", [])
    if not commits:
        return out + _empty("sin commits aún")
    for c in commits:
        date = (c.get("date") or "")[:10]
        out += (f"  {D}{c['id'][:8]}{R}  {B}{c['author']}{R}"
                f"  {D}{date}{R}  {c['message']}\n")
    return out + "\n"


def _dictionary(data: dict | None) -> str:
    out = _sec("DICCIONARIO DE DATOS")
    if not data or not data.get("entries"):
        return out + _empty("sin definiciones registradas")

    entries = data["entries"]
    col_w = max(len(e["column"]) for e in entries)
    for e in entries:
        col = e["column"].ljust(col_w)
        scope = f" {D}[{e['scope']}]{R}" if e["scope"] != "global" else ""
        out += f"  {MG}{B}{col}{R}{scope}  {e['definition']}\n"
    return out + "\n"


def _lineage(data: dict | None, project_root: Path) -> str:
    out = _sec("LINAJE DE ARTEFACTOS")
    if not data or not data.get("records"):
        return out + _empty("sin linaje inferido o registrado")

    for r in data["records"]:
        artifact = _rel(r["artifact"], project_root)
        origin = r["origin"]
        if origin == "user_confirmed":
            badge = f"{GR}[confirmado]{R}"
        elif origin == "user_corrected":
            badge = f"{YE}[corregido]{R}"
        else:
            badge = f"{D}[inferido]{R}"
        out += f"  {WH}{B}{artifact}{R}  {badge}\n"
        out += f"    {D}producer → {r['producer']}{R}\n"
        inputs = [_rel(i, project_root) for i in r.get("inputs", [])]
        if inputs:
            out += f"    {D}fuentes  → {', '.join(inputs)}{R}\n"
        out += "\n"
    return out


def _annotations(data: dict | None) -> str:
    out = _sec("ANOTACIONES DE DECISIÓN")
    if not data or not data.get("annotations"):
        return out + _empty("sin anotaciones registradas")

    for a in data["annotations"]:
        target = a.get("target")
        if target:
            tgt = f"  {D}[{target['type']}: {target['ref']}]{R}"
        else:
            tgt = f"  {D}[proyecto]{R}"
        date = (a.get("created_at") or "")[:10]
        out += f"  {D}{a['id']}{R}  {a['text']}{tgt}  {D}{date}{R}\n"
    return out + "\n"


# ── Entrada pública ──────────────────────────────────────────────────────────

def render_terminal(project_root: Path | str) -> str:
    project_root = Path(project_root)
    meta = store.read_entity(project_root, "meta") or {}

    if not _supports_color():
        # Sin color: devolver cadena vacía para que cli.py use el Markdown plano
        return ""

    version = meta.get("harness_version", config.HARNESS_VERSION)
    schema  = meta.get("schema_version", config.SCHEMA_VERSION)
    now     = config.iso_now()[:19].replace("T", " ")
    name    = project_root.name

    width = 54
    header = (
        f"\n{B}{CY}{'═' * width}{R}\n"
        f"{B}{CY}  DS Harness  ·  {name}{R}\n"
        f"{B}{CY}{'═' * width}{R}\n"
        f"  {D}v{version} · schema v{schema} · {now} UTC{R}\n"
    )

    body = "".join([
        _map(store.read_entity(project_root, "map")),
        _sources(store.read_entity(project_root, "sources"), project_root),
        _changelog(store.read_entity(project_root, "changelog")),
        _dictionary(store.read_entity(project_root, "dictionary")),
        _lineage(store.read_entity(project_root, "lineage"), project_root),
        _annotations(store.read_entity(project_root, "annotations")),
    ])

    footer = f"\n{D}Vista guardada en .ds_harness/views/status.md{R}\n"
    return header + body + footer
