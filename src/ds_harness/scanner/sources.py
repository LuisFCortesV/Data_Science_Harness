"""FR-002: cataloga las fuentes de datos referenciadas en el código.

Recorre `.py`/`.ipynb`/`.sql`, deduplica por identidad (ruta normalizada para
archivos; `esquema.tabla` para SQL), agrega referencias, resuelve `status` solo
para fuentes basadas en archivo, y persiste `sources.json`. Un archivo no
parseable registra `FileParseError` y el escaneo continúa.
"""

from __future__ import annotations

from pathlib import Path

from .. import config
from ..errors import FileParseError
from ..memory import store
from .common import iter_code_files, normalize_ref
from .extractors import notebook, python_ast, sql


def _located(project_root: Path, identity: str, code_dir: Path) -> str:
    """located/not_located para fuentes basadas en archivo."""
    candidates = [project_root / identity, code_dir / identity]
    for c in candidates:
        try:
            if c.exists():
                return "located"
        except OSError:
            continue
    return "not_located"


def scan(project_root: Path | str, logger=None) -> dict:
    project_root = Path(project_root)
    # identity -> entrada de fuente
    catalog: dict[str, dict] = {}

    def add_file_source(identity: str, code_file: str, line, code_dir: Path) -> None:
        identity = normalize_ref(identity)
        entry = catalog.get(identity)
        if entry is None:
            entry = {"kind": "file", "identity": identity,
                     "status": _located(project_root, identity, code_dir),
                     "references": []}
            catalog[identity] = entry
        _add_ref(entry, code_file, line)

    def add_sql_source(identity: str, qualified: bool, code_file: str) -> None:
        entry = catalog.get(identity)
        if entry is None:
            entry = {"kind": "sql", "identity": identity, "status": None, "references": []}
            catalog[identity] = entry
        _add_ref(entry, code_file, None)
        if not qualified and logger:
            logger.warning("scan", "Tabla SQL sin esquema calificado",
                           {"identity": identity, "code_file": code_file})

    for full, rel in iter_code_files(project_root):
        code_dir = full.parent
        try:
            if rel.endswith(".py"):
                reads, _writes = python_ast.extract(full.read_text(encoding="utf-8", errors="replace"), rel)
                for path, line in reads:
                    add_file_source(path, rel, line, code_dir)
            elif rel.endswith(".ipynb"):
                reads, _writes = notebook.extract(full)
                for path, line in reads:
                    add_file_source(path, rel, line, code_dir)
            elif rel.endswith(".sql"):
                src_tables, _artifacts = sql.extract(full.read_text(encoding="utf-8", errors="replace"), rel)
                for identity, qualified in src_tables:
                    add_sql_source(identity, qualified, rel)
        except FileParseError as exc:
            if logger:
                logger.error("scan", "Archivo de código no parseable; se omite y continúa",
                             {"file": rel, "detail": exc.detail})
            continue

    sources = sorted(catalog.values(), key=lambda s: (s["kind"], s["identity"]))
    data = {"schema_version": config.SCHEMA_VERSION, "sources": sources}
    store.write_entity(project_root, "sources", data)

    not_located = [s["identity"] for s in sources if s.get("status") == "not_located"]
    if logger:
        logger.info("scan", "Catálogo de fuentes actualizado",
                    {"sources": len(sources), "not_located": len(not_located)})
        for identity in not_located:
            logger.warning("scan", "Fuente referenciada no localizada en disco",
                           {"identity": identity})
    return data


def _add_ref(entry: dict, code_file: str, line) -> None:
    for ref in entry["references"]:
        if ref["code_file"] == code_file and ref["line"] == line:
            return
    entry["references"].append({"code_file": code_file, "line": line})
