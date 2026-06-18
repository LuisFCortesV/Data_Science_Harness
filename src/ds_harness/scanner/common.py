"""Utilidades compartidas por el escaneo de fuentes y la inferencia de linaje."""

from __future__ import annotations

import os
from pathlib import Path

from .. import config


def normalize_ref(path: str) -> str:
    """Normaliza una ruta literal referenciada en el código (separador `/`)."""
    p = path.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def iter_code_files(project_root: Path | str):
    """Itera (ruta_absoluta, ruta_relativa_posix) de archivos de código.

    Recorre `.py`/`.ipynb`/`.sql` del árbol, saltando solo las exclusiones
    estándar (`.git/`, `.ds_harness/`). Es independiente de `.gitignore`:
    la detección de fuentes opera sobre el contenido del código aunque ese
    archivo esté excluido del mapa (FR-002, desacople explícito).
    """
    project_root = Path(project_root)
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in config.STANDARD_EXCLUDES]
        base = Path(dirpath)
        for name in sorted(filenames):
            if name.endswith(config.CODE_EXTENSIONS):
                full = base / name
                rel = full.relative_to(project_root).as_posix()
                yield full, rel
