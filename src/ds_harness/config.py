"""Constantes y rutas de la memoria del harness (`.ds_harness/`).

Sin dependencias internas: lo importan todos los demás módulos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

# Versiones
HARNESS_VERSION = "0.1.0"
SCHEMA_VERSION = 1

# Nombres dentro de la carpeta de memoria
DS_DIR_NAME = ".ds_harness"
VIEWS_DIR_NAME = "views"
STATUS_VIEW_NAME = "status.md"
LOG_NAME = "agent_log.jsonl"

# Exclusiones estándar del escaneo (siempre, independientes de .gitignore).
# Los directorios de venv son infraestructura, no código del usuario.
STANDARD_EXCLUDES = {".git", DS_DIR_NAME, "venv", ".venv", "env", ".env",
                     "node_modules", "__pycache__"}

# Extensiones de código sobre las que opera el análisis estático (FR-002)
CODE_EXTENSIONS = (".py", ".ipynb", ".sql")

# Archivo JSON por entidad de memoria (fuente de verdad)
ENTITY_FILES = {
    "meta": "meta.json",
    "map": "map.json",
    "sources": "sources.json",
    "dictionary": "dictionary.json",
    "changelog": "changelog.json",
    "lineage": "lineage.json",
    "annotations": "annotations.json",
}

# Esqueleto inicial de cada entidad (creado por `init`)
EMPTY_ENTITIES = {
    "map": {"schema_version": SCHEMA_VERSION, "scanned_at": None, "root": ".",
            "excluded_rules": [], "entries": []},
    "sources": {"schema_version": SCHEMA_VERSION, "sources": []},
    "dictionary": {"schema_version": SCHEMA_VERSION, "entries": []},
    "changelog": {"schema_version": SCHEMA_VERSION, "git_available": False, "commits": []},
    "lineage": {"schema_version": SCHEMA_VERSION, "records": []},
    "annotations": {"schema_version": SCHEMA_VERSION, "annotations": []},
}


def iso_now() -> str:
    """Marca de tiempo ISO-8601 en UTC (sufijo Z)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ds_dir(project_root: Path | str) -> Path:
    return Path(project_root) / DS_DIR_NAME


def entity_path(project_root: Path | str, name: str) -> Path:
    return ds_dir(project_root) / ENTITY_FILES[name]


def log_path(project_root: Path | str) -> Path:
    return ds_dir(project_root) / LOG_NAME


def views_dir(project_root: Path | str) -> Path:
    return ds_dir(project_root) / VIEWS_DIR_NAME


def status_view_path(project_root: Path | str) -> Path:
    return views_dir(project_root) / STATUS_VIEW_NAME


def meta_path(project_root: Path | str) -> Path:
    return entity_path(project_root, "meta")
