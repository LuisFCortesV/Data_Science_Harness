"""Vista legible derivada (`views/status.md`).

Se genera SIEMPRE a partir de los JSON de entidad; nunca se parsea de vuelta
(Principio IV). Las secciones vacías se indican explícitamente (US6.3).
"""

from __future__ import annotations

from pathlib import Path

from .. import config
from . import store


def _section_empty(title: str, hint: str) -> str:
    return f"## {title}\n\n_(vacío — {hint})_\n"


def _rel(path_str: str, project_root: Path) -> str:
    """Devuelve ruta relativa desde project_root con separadores /; si falla, solo el nombre."""
    try:
        return Path(path_str).relative_to(project_root).as_posix()
    except ValueError:
        p = Path(path_str)
        parent = p.parent.name
        return f"{parent}/{p.name}" if parent and parent != "." else p.name


def _render_map(data: dict | None) -> str:
    if not data or not data.get("entries"):
        return _section_empty("Mapa de estructura", "aún no se ha escaneado el proyecto")
    lines = [f"## Mapa de estructura", "",
             f"- Escaneado: {data.get('scanned_at') or 'n/d'}",
             f"- Exclusiones: {', '.join(data.get('excluded_rules', [])) or 'n/d'}",
             f"- Total nodos: {len(data['entries'])}", ""]
    for node in data["entries"]:
        marker = "/" if node.get("type") == "dir" else ""
        lines.append(f"- `{node['path']}{marker}`")
    return "\n".join(lines) + "\n"


def _render_sources(data: dict | None, project_root: Path) -> str:
    if not data or not data.get("sources"):
        return _section_empty("Fuentes de datos", "no se detectaron fuentes referenciadas")
    lines = ["## Fuentes de datos", "", "| Tipo | Identidad | Estado | Referencias |",
             "|------|-----------|--------|-------------|"]
    for s in data["sources"]:
        refs = ", ".join(
            f"{r['code_file']}:{r['line']}" if r.get("line") else r["code_file"]
            for r in s.get("references", [])
        )
        identity = _rel(s["identity"], project_root)
        lines.append(f"| {s['kind']} | `{identity}` | {s.get('status') or '—'} | {refs} |")
    return "\n".join(lines) + "\n"


def _render_changelog(data: dict | None) -> str:
    if not data or not data.get("git_available"):
        return _section_empty("Bitácora (git)", "git no disponible o sin commits")
    commits = data.get("commits", [])
    if not commits:
        return _section_empty("Bitácora (git)", "el historial no tiene commits")
    lines = ["## Bitácora (git)", ""]
    for c in commits:
        files = ", ".join(c.get("files", []))
        lines.append(f"- `{c['id']}` — {c['author']} — {c['date']}: {c['message']}"
                     + (f" ({files})" if files else ""))
    return "\n".join(lines) + "\n"


def _render_dictionary(data: dict | None) -> str:
    if not data or not data.get("entries"):
        return _section_empty("Diccionario de datos", "sin definiciones registradas")
    lines = ["## Diccionario de datos", "", "| Columna | Alcance | Definición |",
             "|---------|---------|------------|"]
    for e in data["entries"]:
        lines.append(f"| `{e['column']}` | {e['scope']} | {e['definition']} |")
    return "\n".join(lines) + "\n"


def _render_lineage(data: dict | None, project_root: Path) -> str:
    if not data or not data.get("records"):
        return _section_empty("Linaje de artefactos", "sin linaje inferido o registrado")
    lines = ["## Linaje de artefactos", "", "| Artefacto | Producer | Fuentes | Origen |",
             "|-----------|----------|---------|--------|"]
    for r in data["records"]:
        inputs = ", ".join(_rel(i, project_root) for i in r.get("inputs", []))
        artifact = _rel(r["artifact"], project_root)
        lines.append(f"| `{artifact}` | `{r['producer']}` | {inputs} | {r['origin']} |")
    return "\n".join(lines) + "\n"


def _render_annotations(data: dict | None) -> str:
    if not data or not data.get("annotations"):
        return _section_empty("Anotaciones de decisión", "sin anotaciones registradas")
    lines = ["## Anotaciones de decisión", ""]
    for a in data["annotations"]:
        target = a.get("target")
        tgt = f" → {target['type']}:`{target['ref']}`" if target else " → (proyecto)"
        lines.append(f"- [{a['id']}] {a['text']}{tgt} _({a['created_at']})_")
    return "\n".join(lines) + "\n"


def render_status(project_root: Path | str) -> str:
    """Lee los JSON de entidad, genera `views/status.md` y devuelve su contenido.

    Tolerante a secciones vacías; nunca falla por una entidad ausente.
    """
    project_root = Path(project_root)
    meta = store.read_entity(project_root, "meta") or {}

    header = [
        "# Estado del proyecto — DS Harness",
        "",
        f"- Harness: v{meta.get('harness_version', config.HARNESS_VERSION)}"
        f" · schema_version {meta.get('schema_version', config.SCHEMA_VERSION)}",
        f"- Generado: {config.iso_now()}",
        "",
        "> Vista legible derivada de la memoria en `.ds_harness/`. Fuente de verdad: los JSON.",
        "",
    ]

    sections = [
        _render_map(store.read_entity(project_root, "map")),
        _render_sources(store.read_entity(project_root, "sources"), project_root),
        _render_changelog(store.read_entity(project_root, "changelog")),
        _render_dictionary(store.read_entity(project_root, "dictionary")),
        _render_lineage(store.read_entity(project_root, "lineage"), project_root),
        _render_annotations(store.read_entity(project_root, "annotations")),
    ]

    content = "\n".join(header) + "\n".join(sections)

    out_path = config.status_view_path(project_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return content
