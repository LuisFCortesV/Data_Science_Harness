"""Extrae tablas calificadas de archivos `.sql` con sqlglot.

Fuentes = tablas de FROM/JOIN. Artefactos = destino de INSERT INTO / CREATE TABLE.
Identidad = `esquema.tabla`. Tablas sin esquema se devuelven con `qualified=False`
para que el orquestador registre un aviso.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from ...errors import FileParseError

# (identity, qualified)
Table = tuple[str, bool]


def _identity(table: exp.Table) -> Table:
    name = table.name
    schema = table.db  # esquema (puede ser "")
    if schema:
        return f"{schema}.{name}", True
    return name, False


def extract(sql_text: str, filename: str = "<unknown>") -> tuple[list[Table], list[Table]]:
    """Devuelve (sources, artifacts)."""
    try:
        statements = sqlglot.parse(sql_text)
    except SqlglotError as exc:
        raise FileParseError(filename, f"SQL no parseable: {exc}") from exc

    sources: list[Table] = []
    artifacts: list[Table] = []

    for stmt in statements:
        if stmt is None:
            continue

        artifact_ids: set[int] = set()
        for create in stmt.find_all(exp.Create):
            tbl = create.find(exp.Table)
            if tbl is not None:
                artifact_ids.add(id(tbl))
        for insert in stmt.find_all(exp.Insert):
            target = insert.this.find(exp.Table) if insert.this else None
            if target is not None:
                artifact_ids.add(id(target))

        for table in stmt.find_all(exp.Table):
            ident = _identity(table)
            if id(table) in artifact_ids:
                artifacts.append(ident)
            else:
                sources.append(ident)

    return sources, artifacts
