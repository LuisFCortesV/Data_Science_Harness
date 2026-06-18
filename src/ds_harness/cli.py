"""Punto de entrada CLI con subcomandos `init`, `scan`, `status`, `chat`.

Operaciones deterministas (init/scan/status) NO usan el modelo (menor costo y
latencia). Solo `chat` carga el SDK (import perezoso en su handler).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from .errors import DSHarnessError, LLMError
from .git_log import scan_git_log
from .lineage import infer_lineage
from .logging_setup import get_logger
from .memory import store, views
from .scanner import sources, structure


def _meta(project_root: Path) -> dict:
    return {
        "schema_version": config.SCHEMA_VERSION,
        "harness_version": config.HARNESS_VERSION,
        "project_root": str(project_root.resolve()),
        "initialized_at": config.iso_now(),
    }


def _do_scan(project_root: Path, logger) -> None:
    """Escaneo determinista completo: estructura, fuentes, git y linaje."""
    structure.scan(project_root, logger)
    sources.scan(project_root, logger)
    scan_git_log(project_root, logger)
    infer_lineage(project_root, logger)
    views.render_status(project_root)


def cmd_init(args) -> int:
    project_root = Path(args.path).resolve()
    if not project_root.is_dir():
        print(f"error: la ruta no es un directorio: {project_root}", file=sys.stderr)
        return 2
    store.ensure_memory_dir(project_root)
    logger = get_logger(project_root)

    if store.read_entity(project_root, "meta") is None:
        store.write_entity(project_root, "meta", _meta(project_root))
    for name, skeleton in config.EMPTY_ENTITIES.items():
        if store.read_entity(project_root, name) is None:
            store.write_entity(project_root, name, dict(skeleton))

    logger.info("init", "Memoria .ds_harness/ inicializada", {"root": str(project_root)})
    print(f"Inicializado .ds_harness/ en {project_root}")
    _do_scan(project_root, logger)
    print("Primer escaneo completado. Usa `ds_harness status` para ver el estado.")
    return 0


def cmd_scan(args) -> int:
    project_root = Path(args.path).resolve()
    if store.read_entity(project_root, "meta") is None:
        print("error: el proyecto no está inicializado. Ejecuta `ds_harness init` primero.",
              file=sys.stderr)
        return 2
    logger = get_logger(project_root)
    _do_scan(project_root, logger)
    print("Escaneo completado (estructura, fuentes, git, linaje).")
    return 0


def cmd_status(args) -> int:
    project_root = Path(args.path).resolve()
    if store.read_entity(project_root, "meta") is None:
        print("error: el proyecto no está inicializado. Ejecuta `ds_harness init` primero.",
              file=sys.stderr)
        return 2
    views.render_status(project_root)  # actualiza el .md
    from .memory.terminal import render_terminal
    terminal_out = render_terminal(project_root)
    print(terminal_out if terminal_out else views.render_status(project_root))
    return 0


def cmd_chat(args) -> int:
    project_root = Path(args.path).resolve()
    if store.read_entity(project_root, "meta") is None:
        print("error: el proyecto no está inicializado. Ejecuta `ds_harness init` primero.",
              file=sys.stderr)
        return 2
    logger = get_logger(project_root)

    # Import perezoso: el SDK solo se necesita en el modo chat.
    from .agent_loop.loop import run_chat_turn
    from .tools.wiring import get_registry

    registry = get_registry(project_root=project_root, logger=logger, confirm_fn=None)

    print("Modo chat del DS Harness. Escribe tu mensaje; 'salir' para terminar.\n")
    history: list = []
    client = None
    while True:
        try:
            user_text = input("tú> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text.lower() in {"salir", "exit", "quit"}:
            break
        try:
            if client is None:
                from .agent_loop.client import GeminiClient
                from .agent_loop.system_prompt import SYSTEM_PROMPT
                client = GeminiClient(SYSTEM_PROMPT, registry.declarations())
            reply, history = run_chat_turn(user_text, registry, history, client, logger)
        except LLMError as exc:
            print(f"[modelo] {exc}", file=sys.stderr)
            logger.error("chat", "Fallo en la llamada al modelo", {"error": str(exc)})
            continue
        print(f"\nharness> {reply}\n")
    print("Sesión de chat finalizada.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ds_harness",
        description="Memoria persistente y trazable para proyectos de ciencia de datos.")
    parser.add_argument("--version", action="version",
                        version=f"ds_harness {config.HARNESS_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, handler, help_text in (
        ("init", cmd_init, "Inicializa .ds_harness/ y ejecuta el primer escaneo."),
        ("scan", cmd_scan, "Re-escanea estructura, fuentes, git y linaje (sin LLM)."),
        ("status", cmd_status, "Regenera y muestra la vista legible del estado."),
        ("chat", cmd_chat, "Modo conversacional: anotar, definir columnas, confirmar linaje."),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("path", nargs="?", default=".", help="Ruta del proyecto (por defecto: .)")
        p.set_defaults(func=handler)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except DSHarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
