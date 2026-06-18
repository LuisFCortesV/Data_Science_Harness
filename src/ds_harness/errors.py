"""Excepciones de dominio (Principio IX: manejo de errores claro y específico).

Nunca se usa `except Exception` genérico en el resto del código; cada módulo
captura estas excepciones específicas.
"""

from __future__ import annotations


class DSHarnessError(Exception):
    """Raíz de toda la jerarquía de errores del harness."""


class MemoryCorruptedError(DSHarnessError):
    """La memoria persistida (un JSON de entidad) es ilegible o inválida.

    No se sobrescribe el archivo: el usuario decide cómo recuperarlo.
    """

    def __init__(self, path: str, detail: str = "") -> None:
        self.path = path
        self.detail = detail
        msg = f"Memoria corrupta o ilegible: {path}."
        if detail:
            msg += f" Detalle: {detail}."
        msg += " No se sobrescribió; revisa o restaura el archivo manualmente."
        super().__init__(msg)


class GitNotAvailableError(DSHarnessError):
    """git no está instalado o el directorio no es un repositorio."""


class FileParseError(DSHarnessError):
    """Un archivo de código no se pudo parsear durante el escaneo.

    El escaneo registra el fallo y continúa con los demás archivos.
    """

    def __init__(self, file_path: str, detail: str = "") -> None:
        self.file_path = file_path
        self.detail = detail
        msg = f"No se pudo parsear '{file_path}'"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class SourceNotLocatedWarning(DSHarnessError):
    """Marca informativa: una fuente basada en archivo no existe en disco.

    No se eleva para tumbar el escaneo; se cataloga con `status=not_located`.
    """


class ToolBlockedError(DSHarnessError):
    """La barrera pre-tool-use bloqueó una acción por falta de confirmación."""


class LLMError(DSHarnessError):
    """Fallo al invocar el modelo (config ausente, SDK ausente o error transitorio agotado)."""
