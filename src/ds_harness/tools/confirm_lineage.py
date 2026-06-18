"""Tool `confirm_lineage` (contracts/tools.md)."""

from __future__ import annotations

from pathlib import Path

from ..memory import store

SCHEMA = {
    "name": "confirm_lineage",
    "description": "Confirma o corrige un registro de linaje inferido (artefacto -> producer -> inputs).",
    "mutates_filesystem": False,
    "parameters": {
        "type": "object",
        "properties": {
            "artifact": {"type": "string", "description": "Ruta del artefacto (clave del registro)"},
            "action": {"type": "string", "enum": ["confirm", "correct"]},
            "producer": {"type": "string", "description": "Nuevo producer (solo si action=correct)"},
            "inputs": {"type": "array", "items": {"type": "string"},
                       "description": "Nuevas identidades de fuentes (solo si action=correct)"},
        },
        "required": ["artifact", "action"],
    },
}


def confirm_lineage(params: dict, project_root, logger=None) -> dict:
    artifact = (params.get("artifact") or "").strip()
    action = params.get("action")
    if not artifact or action not in ("confirm", "correct"):
        return {"ok": False, "message": "Requiere 'artifact' y 'action' ('confirm' o 'correct').", "data": None}

    project_root = Path(project_root)
    data = store.read_entity(project_root, "lineage") or {"schema_version": 1, "records": []}
    rec = next((r for r in data.get("records", []) if r["artifact"] == artifact), None)
    if rec is None:
        return {"ok": False,
                "message": "No hay linaje para ese artefacto; ejecuta `scan` primero.", "data": None}

    if action == "confirm":
        rec["origin"] = "user_confirmed"
    else:
        if params.get("producer"):
            rec["producer"] = params["producer"]
        if params.get("inputs") is not None:
            rec["inputs"] = list(params["inputs"])
        rec["origin"] = "user_corrected"
    store.write_entity(project_root, "lineage", data)

    if logger:
        logger.info("confirm_lineage", f"Linaje {action}", {"artifact": artifact, "origin": rec["origin"]})
    return {"ok": True, "message": f"Linaje '{artifact}' marcado como {rec['origin']}.", "data": rec}
