"""Extrae rutas de lectura (fuentes) y escritura (artefactos) de código Python.

Análisis estático con `ast` (NO ejecuta el código, US5.2). Solo capta argumentos
que son literales string. Eleva FileParseError ante código no parseable.
"""

from __future__ import annotations

import ast

from ...errors import FileParseError

# Funciones/métodos de lectura (la ruta es el primer arg string)
READ_FUNCS = {
    "read_csv", "read_parquet", "read_table", "read_excel", "read_json",
    "read_feather", "read_pickle", "read_hdf", "read_orc", "read_stata",
    "read_sas", "read_spss", "read_fwf", "read_html", "read_xml",
    "load", "loadtxt", "genfromtxt", "load_workbook", "imread",
}

# Funciones/métodos de escritura
WRITE_FUNCS = {
    "to_csv", "to_parquet", "to_excel", "to_json", "to_feather", "to_pickle",
    "to_hdf", "to_stata", "to_orc", "to_xml", "to_html",
    "save", "savez", "savez_compressed", "savetxt", "imwrite", "dump",
}


def _func_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _const_str(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _looks_like_path(s: str) -> bool:
    """Filtra strings que no parecen rutas de archivo.

    Una ruta real casi siempre tiene separador de directorio o extensión.
    Descarta modos de open ('r','w','a'), nombres de entidad ('sources','map'),
    y otras constantes internas.
    """
    return "/" in s or "\\" in s or "." in s


def _first_str_arg(call: ast.Call) -> str | None:
    for arg in call.args:
        s = _const_str(arg)
        if s is not None and _looks_like_path(s):
            return s
    for kw in call.keywords:
        if kw.arg in {"path", "filepath", "filepath_or_buffer", "path_or_buf",
                      "fname", "file", "filename", "buf"}:
            s = _const_str(kw.value)
            if s is not None and _looks_like_path(s):
                return s
    return None


def _open_path_mode(call: ast.Call) -> tuple[str | None, str]:
    path = _const_str(call.args[0]) if call.args else None
    if path is None:
        for kw in call.keywords:
            if kw.arg in {"file", "name"}:
                path = _const_str(kw.value)
    mode = "r"
    if len(call.args) >= 2:
        mode = _const_str(call.args[1]) or "r"
    for kw in call.keywords:
        if kw.arg == "mode":
            mode = _const_str(kw.value) or mode
    return path, mode


def extract(source: str, filename: str = "<unknown>") -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Devuelve (reads, writes) como listas de (ruta_literal, n_linea)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise FileParseError(filename, f"SyntaxError: {exc}") from exc
    except (ValueError, RecursionError) as exc:  # p. ej. nul bytes / código patológico
        raise FileParseError(filename, str(exc)) from exc

    reads: list[tuple[str, int]] = []
    writes: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = _func_name(node.func)
        if fname is None:
            continue
        line = getattr(node, "lineno", 0)

        if fname == "open":
            # Solo el builtin open(path, mode), no path.open() de pathlib.
            if isinstance(node.func, ast.Attribute):
                continue
            path, mode = _open_path_mode(node)
            if path is None:
                continue
            if any(m in mode for m in ("w", "a", "x")):
                writes.append((path, line))
            else:
                reads.append((path, line))
            continue

        is_read = fname in READ_FUNCS or fname.startswith("read_")
        is_write = fname in WRITE_FUNCS or fname.startswith("to_")
        if not (is_read or is_write):
            continue
        path = _first_str_arg(node)
        if path is None:
            continue
        (reads if is_read else writes).append((path, line))

    return reads, writes
