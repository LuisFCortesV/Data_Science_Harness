"""Loop de agente: function-calling MANUAL contra el ToolRegistry.

El modelo solo decide QUÉ tool llamar; la ejecución la hace el registry, que pasa
por la barrera pre_tool_use. Iteramos hasta que el modelo responde en texto o se
agota el presupuesto de pasos.
"""

from __future__ import annotations

from .client import GeminiClient
from .system_prompt import SYSTEM_PROMPT

_MAX_TOOL_STEPS = 6


def run_chat_turn(user_text: str, registry, history: list | None = None,
                  client: GeminiClient | None = None, logger=None) -> tuple[str, list]:
    """Procesa un turno de chat.

    Devuelve (respuesta_texto, history_actualizado). `history` es la lista de
    `Content` del SDK; se crea perezosamente si es None. `client` se reutiliza
    entre turnos para no reabrir el SDK.
    """
    if client is None:
        client = GeminiClient(SYSTEM_PROMPT, registry.declarations())
    types = client._types

    contents = list(history or [])
    contents.append(types.Content(role="user", parts=[types.Part(text=user_text)]))

    for _step in range(_MAX_TOOL_STEPS):
        response = client.generate(contents)
        candidate = response.candidates[0] if response.candidates else None
        parts = candidate.content.parts if candidate and candidate.content else []

        calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
        if not calls:
            text = (getattr(response, "text", None) or "").strip()
            if candidate and candidate.content:
                contents.append(candidate.content)
            return text, contents

        # Registra la intención del modelo y ejecuta cada tool por el registry.
        contents.append(candidate.content)
        response_parts = []
        for call in calls:
            params = dict(call.args) if call.args else {}
            if logger:
                logger.info("chat", "El modelo solicitó una tool", {"tool": call.name})
            result = registry.dispatch(call.name, params)
            response_parts.append(types.Part.from_function_response(
                name=call.name, response={"result": result}))
        contents.append(types.Content(role="user", parts=response_parts))

    if logger:
        logger.warning("chat", "Se agotó el presupuesto de pasos de tool", {"max": _MAX_TOOL_STEPS})
    return ("No pude completar la solicitud en los pasos disponibles; "
            "intenta reformularla de forma más concreta."), contents
