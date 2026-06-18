"""Loop de agente con llamadas directas al SDK google-genai (Principio V)."""

from __future__ import annotations

from .loop import run_chat_turn
from .system_prompt import SYSTEM_PROMPT

__all__ = ["run_chat_turn", "SYSTEM_PROMPT"]
