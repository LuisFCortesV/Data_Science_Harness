"""Tool `define_column` (contracts/tools.md)."""

from __future__ import annotations

from pathlib import Path

from .. import config
from ..memory import store

SCHEMA = {
    "name": "define_column",
    "description": ("Crea o actualiza la definición de una columna en el diccionario, "
                    "global o como override de una fuente/dataset."),
    "mutates_filesystem": False,
    "parameters": {
        "type": "object",
        "properties": {
            "column": {"type": "string", "description": "Nombre de la columna/feature"},
            "definition": {"type": "string", "description": "Significado"},
            "scope": {"type": "string",
                      "description": "'global' (defecto) o la identity de una fuente (override)"},
        },
        "required": ["column", "definition"],
    },
}


def _source_exists(project_root: Path, scope: str) -> bool:
    data = store.read_entity(project_root, "sources") or {}
    return any(s["identity"] == scope for s in data.get("sources", []))


def define_column(params: dict, project_root, logger=None) -> dict:
    column = (params.get("column") or "").strip()
    definition = (params.get("definition") or "").strip()
    if not column or not definition:
        return {"ok": False, "message": "Faltan 'column' y/o 'definition'.", "data": None}
    scope = (params.get("scope") or "global").strip() or "global"

    project_root = Path(project_root)
    data = store.read_entity(project_root, "dictionary") or dict(config.EMPTY_ENTITIES["dictionary"])
    data.setdefault("entries", [])

    now = config.iso_now()
    found = next((e for e in data["entries"] if e["column"] == column and e["scope"] == scope), None)
    if found is not None:
        found["definition"] = definition
        found.setdefault("history", []).append({"definition": definition, "changed_at": now})
        action = "actualizada"
    else:
        data["entries"].append({
            "column": column, "scope": scope, "definition": definition,
            "history": [{"definition": definition, "changed_at": now}],
        })
        action = "creada"
    store.write_entity(project_root, "dictionary", data)

    warn = None
    if scope != "global" and not _source_exists(project_root, scope):
        warn = "override anticipado: el scope no existe (aún) en sources.json"
        if logger:
            logger.warning("define_column", warn, {"scope": scope})

    if logger:
        logger.info("define_column", f"Definición {action}", {"column": column, "scope": scope})

    message = f"Definición {action} para '{column}' (scope={scope})." + (f" Aviso: {warn}." if warn else "")
    return {"ok": True, "message": message, "data": {"column": column, "scope": scope, "action": action}}
