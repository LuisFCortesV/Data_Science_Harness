"""Dataclasses de las 8 entidades de memoria (data-model.md).

Las entidades de nivel superior (las que tienen su propio archivo JSON) son 8:
Mapa, Fuente, EntradaDic, Commit (bitácora), Linaje, Anotación, registro de log y meta.
Se modelan aquí con 9 dataclasses porque `SourceRef` y `DictionaryChange` son
sub-objetos anidados, no entidades con archivo propio.

Los modelos son convenientes para construir y validar en memoria; la capa `store`
serializa/deserializa los dicts JSON directamente (ver `contracts/memory-schemas.md`).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class StructureNode:
    """Nodo del mapa de estructura."""
    path: str
    type: str  # "file" | "dir"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceRef:
    """Dónde se referencia una fuente (sub-objeto de DataSource)."""
    code_file: str
    line: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DataSource:
    """Fuente de datos referenciada en el código."""
    kind: str  # "file" | "sql"
    identity: str
    references: list[SourceRef] = field(default_factory=list)
    status: str | None = None  # "located" | "not_located" | None (solo kind=file)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "identity": self.identity,
            "status": self.status,
            "references": [r.to_dict() for r in self.references],
        }


@dataclass
class DictionaryChange:
    """Cambio histórico de una definición (sub-objeto de DictionaryEntry)."""
    definition: str
    changed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DictionaryEntry:
    """Entrada del diccionario de datos. Clave: (column, scope)."""
    column: str
    scope: str  # "global" o la identity de una fuente
    definition: str
    history: list[DictionaryChange] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "column": self.column,
            "scope": self.scope,
            "definition": self.definition,
            "history": [h.to_dict() for h in self.history],
        }


@dataclass
class ChangelogCommit:
    """Entrada de bitácora = un commit del historial git."""
    id: str
    author: str
    date: str
    message: str
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LineageRecord:
    """Relación artefacto -> producer -> fuentes."""
    artifact: str
    producer: str
    inputs: list[str] = field(default_factory=list)
    origin: str = "inferred"  # inferred | user_confirmed | user_corrected

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DecisionAnnotation:
    """El 'por qué' de una decisión; texto libre + objetivo opcional."""
    id: str
    text: str
    created_at: str
    target: dict | None = None  # {"type": ..., "ref": ...} o None (proyecto)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentLogEntry:
    """Una línea del agent_log.jsonl."""
    ts: str
    level: str
    action: str
    why: str
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
