"""Lectura del historial de git para la bitácora (FR-006)."""

from __future__ import annotations

from .history import scan_git_log

__all__ = ["scan_git_log"]
