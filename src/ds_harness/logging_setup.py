"""Log append-only en `agent_log.jsonl` (Principio VII: trazabilidad).

Una línea JSON por evento con campos: ts, level, action, why, detail.
Nunca se reescribe el archivo; solo se añade (append).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config


class AgentLogger:
    """Escribe eventos como líneas JSON en `.ds_harness/agent_log.jsonl`."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)
        self.path = config.log_path(self.project_root)

    def log(self, level: str, action: str, why: str,
            detail: dict[str, Any] | None = None) -> dict[str, Any]:
        entry = {
            "ts": config.iso_now(),
            "level": level,
            "action": action,
            "why": why,
            "detail": detail or {},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def info(self, action: str, why: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.log("info", action, why, detail)

    def warning(self, action: str, why: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.log("warning", action, why, detail)

    def error(self, action: str, why: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.log("error", action, why, detail)


def get_logger(project_root: Path | str) -> AgentLogger:
    """Devuelve un logger configurado para el proyecto dado."""
    return AgentLogger(project_root)
