"""Barrera de seguridad pre-tool-use (FR-013..015, Principio III).

Bloquea toda acción destructiva (o ambigua) hasta confirmación explícita del
usuario, por acción individual. Fail-safe: si el schema no declara
`mutates_filesystem` como booleano, se trata como destructiva.
"""

from __future__ import annotations

from typing import Callable

from ..errors import ToolBlockedError

_AFFIRMATIVE = {"s", "si", "sí", "y", "yes"}


def is_ambiguous(mutates_filesystem) -> bool:
    """Ambiguo = no declarado como booleano explícito (fail-safe, FR-015)."""
    return not isinstance(mutates_filesystem, bool)


def _default_confirm(prompt: str) -> str:
    return input(prompt)


def check_destructive(tool_name: str, mutates_filesystem, description: str = "",
                      confirm_fn: Callable[[str], str] | None = None, logger=None) -> bool:
    """Autoriza o bloquea una acción.

    Devuelve True si la acción está permitida (no destructiva, o confirmada).
    Eleva ToolBlockedError si la acción es destructiva/ambigua y el usuario no
    confirma. Registra la decisión en el log.
    """
    confirm_fn = confirm_fn or _default_confirm
    ambiguous = is_ambiguous(mutates_filesystem)
    destructive = ambiguous or mutates_filesystem is True

    if not destructive:
        return True

    reason = "clasificación ambigua (fail-safe)" if ambiguous else "operación destructiva"
    prompt = (f"\n[seguridad] La tool '{tool_name}' requiere confirmación ({reason}).\n"
              f"  {description}\n"
              f"¿Autorizar ESTA acción? [s/N]: ")
    answer = confirm_fn(prompt)
    approved = str(answer).strip().lower() in _AFFIRMATIVE

    if logger:
        logger.log("info" if approved else "warning", "pre_tool_use",
                   f"{'Autorizada' if approved else 'Bloqueada'} acción '{tool_name}' ({reason})",
                   {"tool": tool_name, "approved": approved, "ambiguous": ambiguous})

    if not approved:
        raise ToolBlockedError(
            f"Acción '{tool_name}' bloqueada: el usuario no confirmó la operación.")
    return True
