"""Fixture: tool DESTRUCTIVA de prueba (mutates_filesystem=True).

En Fase 1 no existen tools destructivas reales (FR-018). Este fixture sirve solo
para validar que la barrera pre_tool_use bloquea/confirma una tool así. NO debe
registrarse en `wiring.py`.
"""

from __future__ import annotations

from pathlib import Path

SCHEMA = {
    "name": "delete_file",
    "description": "Elimina un archivo del proyecto (DESTRUCTIVA, solo para pruebas de la barrera).",
    "mutates_filesystem": True,
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Ruta a eliminar"}},
        "required": ["path"],
    },
}


def delete_file(params: dict, project_root, logger=None) -> dict:
    # Si la barrera funciona, esto solo se ejecuta tras confirmación explícita.
    target = Path(project_root) / params["path"]
    return {"ok": True, "message": f"(simulado) eliminaría {target}", "data": None}
