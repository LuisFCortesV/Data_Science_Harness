"""FR-006: bitácora de cambios a partir del historial de git.

Lee commits con `git log` (el historial, no el working tree). Degrada con aviso
si el proyecto no tiene git inicializado o `git` no está disponible (Principio IX:
sin reintento; un fallo local no se resuelve solo). No ejecuta nada del usuario.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .. import config
from ..errors import GitNotAvailableError
from ..memory import store

# Separadores improbables en mensajes de commit, para un parseo robusto.
_FIELD = "\x1f"  # entre campos
_RECORD = "\x1e"  # entre commits
_FORMAT = _FIELD.join(["%H", "%an", "%aI", "%s"]) + _RECORD


def _run_git(project_root: Path, args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(project_root),
            capture_output=True, text=True, encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise GitNotAvailableError("el ejecutable `git` no está disponible en el PATH") from exc
    except OSError as exc:
        raise GitNotAvailableError(f"no se pudo ejecutar git: {exc}") from exc
    if proc.returncode != 0:
        raise GitNotAvailableError((proc.stderr or "git terminó con error").strip())
    return proc.stdout


def _parse_commits(raw: str) -> list[dict]:
    commits: list[dict] = []
    for record in raw.split(_RECORD):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split(_FIELD)
        if len(parts) < 4:
            continue
        full_hash, author, date, message = parts[0], parts[1], parts[2], parts[3]
        commits.append({
            "id": full_hash[:10], "full_hash": full_hash,
            "author": author, "date": date, "message": message, "files": [],
        })
    return commits


def _attach_files(project_root: Path, commits: list[dict]) -> None:
    for c in commits:
        try:
            out = _run_git(project_root, ["show", "--name-only", "--pretty=format:", c["full_hash"]])
        except GitNotAvailableError:
            continue
        c["files"] = [ln.strip() for ln in out.splitlines() if ln.strip()]


def scan_git_log(project_root: Path | str, logger=None, max_commits: int = 100) -> dict:
    """Persiste `changelog.json`. `git_available=False` (degradado) si no hay git."""
    project_root = Path(project_root)
    try:
        _run_git(project_root, ["rev-parse", "--git-dir"])
        raw = _run_git(project_root, ["log", f"-n{max_commits}", f"--pretty=format:{_FORMAT}"])
    except GitNotAvailableError as exc:
        data = {"schema_version": config.SCHEMA_VERSION, "git_available": False, "commits": []}
        store.write_entity(project_root, "changelog", data)
        if logger:
            logger.warning("git_log", "git no disponible; bitácora degradada", {"detail": str(exc)})
        return data

    commits = _parse_commits(raw)
    _attach_files(project_root, commits)
    data = {"schema_version": config.SCHEMA_VERSION, "git_available": True, "commits": commits}
    store.write_entity(project_root, "changelog", data)
    if logger:
        logger.info("git_log", "Bitácora de git actualizada", {"commits": len(commits)})
    return data
