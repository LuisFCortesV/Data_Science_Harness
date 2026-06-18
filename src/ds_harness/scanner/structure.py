"""FR-001: mapa de estructura del proyecto (mapa vivo).

Excluye lo de `.gitignore` (vía pathspec) + exclusiones estándar (`.git/`,
`.ds_harness/`). Se reemplaza completo en cada scan.
"""

from __future__ import annotations

import os
from pathlib import Path

import pathspec

from .. import config
from ..memory import store


def _load_spec(project_root: Path) -> pathspec.PathSpec | None:
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        return None
    try:
        patterns = gitignore.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def _walk(project_root: Path, spec: pathspec.PathSpec | None) -> list[dict]:
    entries: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        base = Path(dirpath)
        kept = []
        for name in sorted(dirnames):
            if name in config.STANDARD_EXCLUDES:
                continue
            rel = (base / name).relative_to(project_root).as_posix()
            if spec is not None and spec.match_file(rel + "/"):
                continue
            kept.append(name)
            entries.append({"path": rel, "type": "dir"})
        dirnames[:] = kept
        for name in sorted(filenames):
            rel = (base / name).relative_to(project_root).as_posix()
            if spec is not None and spec.match_file(rel):
                continue
            entries.append({"path": rel, "type": "file"})
    return entries


def scan(project_root: Path | str, logger=None) -> dict:
    """Escanea la estructura y persiste `map.json`."""
    project_root = Path(project_root)
    spec = _load_spec(project_root)
    entries = sorted(_walk(project_root, spec), key=lambda e: e["path"])

    data = {
        "schema_version": config.SCHEMA_VERSION,
        "scanned_at": config.iso_now(),
        "root": ".",
        "excluded_rules": [".gitignore", ".git/", ".ds_harness/",
                           "venv/", ".venv/", "env/", "__pycache__/"],
        "entries": entries,
    }
    store.write_entity(project_root, "map", data)
    if logger:
        logger.info("scan", "Mapa de estructura actualizado", {"nodes": len(entries)})
    return data
