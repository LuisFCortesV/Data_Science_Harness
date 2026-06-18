"""Registro y dispatch de tools.

Antes de ejecutar cualquier tool, pasa por la barrera `pre_tool_use` con el
`mutates_filesystem` de su schema. Resultado uniforme:
`{"ok": bool, "message": str, "data": object|null}`.
"""

from __future__ import annotations

from typing import Callable

from ..errors import DSHarnessError, ToolBlockedError
from ..hooks import pre_tool_use


class ToolRegistry:
    def __init__(self, project_root=None, logger=None, confirm_fn: Callable[[str], str] | None = None) -> None:
        self._tools: dict[str, tuple[Callable, dict]] = {}
        self.project_root = project_root
        self.logger = logger
        self.confirm_fn = confirm_fn

    def register(self, fn: Callable, schema: dict) -> None:
        self._tools[schema["name"]] = (fn, schema)

    def names(self) -> list[str]:
        return list(self._tools)

    def declarations(self) -> list[dict]:
        """Declaraciones (name/description/parameters) para el SDK."""
        out = []
        for _fn, schema in self._tools.values():
            out.append({k: schema[k] for k in ("name", "description", "parameters") if k in schema})
        return out

    def dispatch(self, tool_name: str, params: dict) -> dict:
        if tool_name not in self._tools:
            return {"ok": False, "message": f"Tool desconocida: {tool_name}", "data": None}
        fn, schema = self._tools[tool_name]

        try:
            pre_tool_use.check_destructive(
                tool_name, schema.get("mutates_filesystem"),
                schema.get("description", ""), self.confirm_fn, self.logger)
        except ToolBlockedError as exc:
            return {"ok": False, "message": str(exc), "data": None}

        try:
            result = fn(params or {}, self.project_root, self.logger)
        except DSHarnessError as exc:
            if self.logger:
                self.logger.error(tool_name, "La tool falló con error de dominio", {"error": str(exc)})
            return {"ok": False, "message": str(exc), "data": None}

        if not isinstance(result, dict) or "ok" not in result:
            return {"ok": True, "message": "OK", "data": result}
        return result
