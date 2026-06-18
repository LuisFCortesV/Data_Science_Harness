"""Envoltorio mínimo del SDK google-genai (gemini-2.5-flash), sin frameworks.

Import perezoso: `google-genai` solo se carga en el camino `chat`. Así los comandos
deterministas (`init`, `scan`, `status`) funcionan sin tener el SDK instalado.
Reintento controlado (backoff simple, 2-3 intentos) SOLO para la llamada al modelo
(Principio IX); sin reintento para fallos locales.
"""

from __future__ import annotations

import os
import time

from ..errors import LLMError

MODEL_NAME = "gemini-2.5-flash"
_API_KEY_ENVS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
_MAX_ATTEMPTS = 3
_BASE_BACKOFF = 1.5  # segundos


def _api_key() -> str:
    for env in _API_KEY_ENVS:
        val = os.environ.get(env)
        if val:
            return val
    raise LLMError(
        "Falta la API key del modelo. Define la variable de entorno "
        f"{_API_KEY_ENVS[0]} (o {_API_KEY_ENVS[1]}) y reintenta.")


def _import_sdk():
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except ImportError as exc:
        raise LLMError(
            "El paquete `google-genai` no está instalado. Instálalo con "
            "`pip install google-genai` para usar el modo chat.") from exc
    return genai, types


class GeminiClient:
    """Cliente de chat con function-calling MANUAL (sin orquestación automática)."""

    def __init__(self, system_prompt: str, declarations: list[dict]):
        genai, types = _import_sdk()
        self._types = types
        self._client = genai.Client(api_key=_api_key())
        tools = [types.Tool(function_declarations=[
            types.FunctionDeclaration(**d) for d in declarations])] if declarations else None
        # automatic_function_calling DESACTIVADO: nosotros despachamos las tools por el
        # registry (que pasa por la barrera pre_tool_use). El SDK no debe ejecutarlas.
        self._config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    def generate(self, contents: list):
        """Una llamada al modelo, con reintento por error transitorio."""
        last_exc = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                return self._client.models.generate_content(
                    model=MODEL_NAME, contents=contents, config=self._config)
            except Exception as exc:  # noqa: BLE001 — frontera con SDK externo
                last_exc = exc
                if attempt < _MAX_ATTEMPTS:
                    time.sleep(_BASE_BACKOFF * attempt)
                    continue
        raise LLMError(f"El modelo no respondió tras {_MAX_ATTEMPTS} intentos: {last_exc}")
