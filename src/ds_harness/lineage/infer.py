"""FR-008: infiere linaje por análisis estático, sin ejecutar código del usuario.

Para cada script/notebook, lo escrito (writes) es un artefacto producido; lo leído
(reads) son sus fuentes. Reutiliza los extractores del scanner. Las correcciones del
usuario (origin user_confirmed/user_corrected) se preservan entre escaneos: la
re-inferencia no pisa lo que el usuario ya confirmó o corrigió.
"""

from __future__ import annotations

from pathlib import Path

from .. import config
from ..errors import FileParseError
from ..memory import store
from ..scanner.common import iter_code_files, normalize_ref
from ..scanner.extractors import notebook, python_ast, sql

_USER_ORIGINS = ("user_confirmed", "user_corrected")


def _records_from_file(rel: str, reads, writes) -> list[dict]:
    sources = sorted({normalize_ref(p) for p, _ in reads})
    records = []
    for path, _line in writes:
        artifact = normalize_ref(path)
        records.append({
            "artifact": artifact, "producer": rel,
            "inputs": list(sources), "origin": "inferred",
        })
    return records


def infer_lineage(project_root: Path | str, logger=None) -> dict:
    project_root = Path(project_root)

    # Preserva los registros que el usuario ya confirmó/corrigió.
    previous = store.read_entity(project_root, "lineage") or {}
    preserved = {r["artifact"]: r for r in previous.get("records", [])
                 if r.get("origin") in _USER_ORIGINS}

    inferred: dict[str, dict] = {}
    for full, rel in iter_code_files(project_root):
        try:
            if rel.endswith(".py"):
                reads, writes = python_ast.extract(full.read_text(encoding="utf-8", errors="replace"), rel)
            elif rel.endswith(".ipynb"):
                reads, writes = notebook.extract(full)
            elif rel.endswith(".sql"):
                src, artifacts = sql.extract(full.read_text(encoding="utf-8", errors="replace"), rel)
                reads = [(s, None) for s, _ in src]
                writes = [(a, None) for a, _ in artifacts]
            else:
                continue
        except FileParseError as exc:
            if logger:
                logger.error("lineage", "Archivo no parseable; se omite", {"file": rel, "detail": exc.detail})
            continue

        for rec in _records_from_file(rel, reads, writes):
            existing = inferred.get(rec["artifact"])
            if existing is None:
                inferred[rec["artifact"]] = rec
            else:
                existing["inputs"] = sorted(set(existing["inputs"]) | set(rec["inputs"]))

    # El registro del usuario gana sobre la inferencia para el mismo artefacto.
    merged = {**inferred, **preserved}
    records = sorted(merged.values(), key=lambda r: r["artifact"])
    data = {"schema_version": config.SCHEMA_VERSION, "records": records}
    store.write_entity(project_root, "lineage", data)
    if logger:
        logger.info("lineage", "Linaje inferido actualizado",
                    {"records": len(records), "preserved": len(preserved)})
    return data
