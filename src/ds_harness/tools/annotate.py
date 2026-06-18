"""Tool `annotate_decision` (contracts/tools.md)."""

from __future__ import annotations

from pathlib import Path

from .. import config
from ..memory import store

SCHEMA = {
    "name": "annotate_decision",
    "description": ("Guarda el 'por qué' de una decisión como anotación persistente, "
                    "con un objetivo opcional (archivo, fuente o columna) o a nivel proyecto."),
    "mutates_filesystem": False,
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Razonamiento en texto libre"},
            "target_type": {"type": "string", "enum": ["file", "source", "column"],
                            "description": "Tipo de objetivo; omitir = nivel proyecto"},
            "target_ref": {"type": "string",
                           "description": "Referencia del objetivo (requerido si target_type está presente)"},
        },
        "required": ["text"],
    },
}


def _resolves(project_root: Path, ttype: str, ref: str) -> bool:
    if ttype == "source":
        data = store.read_entity(project_root, "sources") or {}
        return any(s["identity"] == ref for s in data.get("sources", []))
    if ttype == "file":
        data = store.read_entity(project_root, "map") or {}
        return any(n["path"] == ref for n in data.get("entries", []))
    if ttype == "column":
        data = store.read_entity(project_root, "dictionary") or {}
        return any(e["column"] == ref for e in data.get("entries", []))
    return False


def annotate_decision(params: dict, project_root, logger=None) -> dict:
    text = (params.get("text") or "").strip()
    if not text:
        return {"ok": False, "message": "Falta 'text' (el razonamiento de la decisión).", "data": None}

    ttype = params.get("target_type")
    tref = params.get("target_ref")
    if ttype and not tref:
        return {"ok": False, "message": "Falta target_ref para el objetivo indicado.", "data": None}

    project_root = Path(project_root)
    data = store.read_entity(project_root, "annotations") or dict(config.EMPTY_ENTITIES["annotations"])
    data.setdefault("annotations", [])

    new_id = f"ann-{len(data['annotations']) + 1:04d}"
    target = {"type": ttype, "ref": tref} if ttype else None
    entry = {"id": new_id, "text": text, "target": target, "created_at": config.iso_now()}
    data["annotations"].append(entry)
    store.write_entity(project_root, "annotations", data)

    warn = None
    if target and not _resolves(project_root, ttype, tref):
        warn = "target_ref no resuelto contra la memoria; anotación aceptada (huérfana)"
        if logger:
            logger.warning("annotate_decision", warn, {"target": target})

    if logger:
        logger.info("annotate_decision", "Anotación de decisión guardada", {"id": new_id})

    message = "Anotación guardada." + (f" Aviso: {warn}." if warn else "")
    return {"ok": True, "message": message, "data": entry}
