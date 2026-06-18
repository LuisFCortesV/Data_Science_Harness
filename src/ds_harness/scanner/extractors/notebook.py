"""Extrae fuentes/artefactos de notebooks `.ipynb`.

Lee el notebook como JSON (stdlib), concatena las celdas de código (ignorando
líneas con magics `%`/`!`) y reutiliza el extractor de Python. Las líneas no son
significativas tras la concatenación, por eso se reportan con `line=None`.
"""

from __future__ import annotations

import json
from pathlib import Path

from ...errors import FileParseError
from . import python_ast


def _read_code(path: Path) -> str:
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        raise FileParseError(str(path), f"notebook ilegible: {exc}") from exc

    lines: list[str] = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", [])
        if isinstance(src, list):
            src = "".join(src)
        for line in src.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("%") or stripped.startswith("!"):
                continue  # magics / shell: se ignoran sin error
            lines.append(line)
    return "\n".join(lines)


def extract(path: str | Path) -> tuple[list[tuple[str, None]], list[tuple[str, None]]]:
    """Devuelve (reads, writes) con `line=None` (ver módulo)."""
    path = Path(path)
    source = _read_code(path)
    reads, writes = python_ast.extract(source, str(path))
    # Normaliza el número de línea a None (no es significativo en notebooks).
    return ([(p, None) for p, _ in reads], [(p, None) for p, _ in writes])
