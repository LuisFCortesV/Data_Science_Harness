"""Ensambla el ToolRegistry con las 4 tools de Fase 1.

Única fuente del registry que consume `agent_loop/loop.py`. Evita que cada tool
se registre por su cuenta.
"""

from __future__ import annotations

from .annotate import SCHEMA as ANNOTATE_SCHEMA, annotate_decision
from .confirm_lineage import SCHEMA as CONFIRM_SCHEMA, confirm_lineage
from .define_column import SCHEMA as DEFINE_SCHEMA, define_column
from .query_memory import SCHEMA as QUERY_SCHEMA, query_memory
from .registry import ToolRegistry

_TOOLS = [
    (annotate_decision, ANNOTATE_SCHEMA),
    (define_column, DEFINE_SCHEMA),
    (confirm_lineage, CONFIRM_SCHEMA),
    (query_memory, QUERY_SCHEMA),
]


def get_registry(project_root=None, logger=None, confirm_fn=None) -> ToolRegistry:
    """Devuelve un ToolRegistry con las 4 tools registradas."""
    reg = ToolRegistry(project_root=project_root, logger=logger, confirm_fn=confirm_fn)
    for fn, schema in _TOOLS:
        reg.register(fn, schema)
    return reg
