"""Lectura/escritura atómica de la memoria (JSON por entidad = fuente de verdad).

Escritura atómica: archivo temporal + os.replace (FR-016). Lectura de JSON inválido
eleva MemoryCorruptedError SIN sobrescribir el archivo.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .. import config
from ..errors import MemoryCorruptedError


def ensure_memory_dir(project_root: Path | str) -> Path:
    """Crea `.ds_harness/` si no existe y devuelve su ruta."""
    d = config.ds_dir(project_root)
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_entity(project_root: Path | str, name: str) -> dict[str, Any] | None:
    """Lee una entidad de memoria. Devuelve None si el archivo no existe.

    Eleva MemoryCorruptedError si el JSON es inválido (no se sobrescribe).
    """
    path = config.entity_path(project_root, name)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        raise MemoryCorruptedError(str(path), str(exc)) from exc


def write_entity(project_root: Path | str, name: str, data: dict[str, Any]) -> Path:
    """Escribe una entidad de memoria de forma atómica."""
    path = config.entity_path(project_root, name)
    _atomic_write_json(path, data)
    return path


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        # Limpia el temporal ante cualquier fallo; no deja JSON a medias.
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
