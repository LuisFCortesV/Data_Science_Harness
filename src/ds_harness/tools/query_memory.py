"""Tool `query_memory` (contracts/tools.md).

Recuperación LITERAL de la memoria (FR-017): sin resumen ni interpretación.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..memory import store

_ENTITY_LIST_FIELD = {
    "map": "entries",
    "sources": "sources",
    "dictionary": "entries",
    "changelog": "commits",
    "lineage": "records",
    "annotations": "annotations",
}

SCHEMA = {
    "name": "query_memory",
    "description": ("Consulta de solo lectura sobre la memoria capturada. Devuelve lo "
                    "almacenado tal cual, sin conclusiones ni observaciones."),
    "mutates_filesystem": False,
    "parameters": {
        "type": "object",
        "properties": {
            "entity": {"type": "string",
                       "enum": list(_ENTITY_LIST_FIELD.keys())},
            "filter": {"type": "string", "description": "Filtro literal simple (substring)"},
        },
        "required": ["entity"],
    },
}


def query_memory(params: dict, project_root, logger=None) -> dict:
    entity = params.get("entity")
    if entity not in _ENTITY_LIST_FIELD:
        return {"ok": False, "message": f"Entidad inválida: {entity}.", "data": None}

    project_root = Path(project_root)
    data = store.read_entity(project_root, entity)
    if data is None:
        return {"ok": False, "message": f"No hay datos para '{entity}'; ejecuta `init`/`scan`.", "data": None}

    flt = params.get("filter")
    if flt:
        field = _ENTITY_LIST_FIELD[entity]
        needle = str(flt).lower()
        items = data.get(field, [])
        matched = [it for it in items if needle in json.dumps(it, ensure_ascii=False).lower()]
        data = {**data, field: matched}

    if logger:
        logger.info("query_memory", "Consulta literal de memoria", {"entity": entity, "filter": flt})
    return {"ok": True, "message": "OK", "data": data}
