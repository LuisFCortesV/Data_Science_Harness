# Implementation Plan: Fase 1 — Base: Observar y Recordar

**Branch**: `001-observar-recordar` | **Date**: 2026-06-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-observar-recordar/spec.md`

## Summary

Capa fundacional del DS Harness: un agente en Python que **observa y recuerda** el
contexto de un proyecto de ciencia de datos en una memoria local persistente y trazable,
con una barrera de seguridad operativa desde el día uno. La memoria se guarda en
`.ds_harness/` con JSON por entidad como fuente de verdad y una vista Markdown derivada.

Enfoque técnico: arquitectura **modular** (memory, scanner, lineage, git_log, hooks,
tools, agent_loop, errors, cli) con separación estricta por responsabilidad. Las
operaciones deterministas (escaneo de estructura/fuentes, generación de la vista, lectura
de git) **no** pasan por el modelo; el modelo (Gemini vía SDK directo `google-genai`)
solo interpreta lenguaje natural en el modo `chat` para decidir qué tool invocar (anotar
decisión, definir columna, confirmar linaje). Toda escritura de memoria es atómica;
cualquier operación destructiva sobre archivos del proyecto pasa por un hook pre-tool-use
que la bloquea hasta confirmación explícita por acción.

## Technical Context

**Language/Version**: Python 3.11+ (entorno local: 3.14)

**Primary Dependencies**:
- `google-genai` (SDK directo del modelo; modelo `gemini-2.5-flash`) — único acceso al LLM.
- `pathspec` (interpretación de `.gitignore` sin depender de git).
- `sqlglot` (parseo de SQL para extraer tablas calificadas `esquema.tabla`).
- Stdlib: `ast` (parseo `.py`), `json` (`.ipynb` y memoria), `subprocess` (git), `pathlib`,
  `tomllib`/`dataclasses`, `logging`.
- Sin LangChain ni frameworks de orquestación (Principio V).

**Storage**: Sistema de archivos local. Memoria en `.ds_harness/` — un JSON por entidad
(fuente de verdad) + vista Markdown derivada + log JSONL append-only.

**Testing**: validación manual vía quickstart.md (escenarios S1-S8); pytest se mantiene
únicamente como dependencia de desarrollo para `--collect-only` (verificación de que el
paquete importa sin errores), no para una suite de tests automatizados en esta fase.

**Target Platform**: CLI multiplataforma (Windows/macOS/Linux); desarrollado en Windows 11.

**Project Type**: Single project — aplicación CLI con loop de agente.

**Performance Goals**: Interactivo. Operaciones deterministas (`scan`, `status`) sobre un
proyecto típico de DS (cientos–miles de archivos de código) en pocos segundos; sin meta
de throughput de servidor. Las llamadas al LLM solo en `chat`.

**Constraints**:
- Offline-capable para todo lo determinista (scan/status/git/memoria); solo `chat`
  requiere red.
- Las operaciones de observación NUNCA modifican archivos del proyecto (FR-004).
- Escritura de memoria atómica para no dejar estado inconsistente (FR-016).
- Estructura de memoria estable y portable para un futuro índice multi-proyecto (FR-011).

**Scale/Scope**: Un proyecto de DS por instancia; memoria de orden KB–MB. 9 módulos, 4
subcomandos CLI, 6 entidades de memoria, 4 tools.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitución v1.1.0. Evaluación por principio:

| Principio | Cómo lo cumple el plan | Estado |
|-----------|------------------------|--------|
| I. Construcción incremental por capas | Esta es la Fase 1 (base). Las entidades y rutas de memoria quedan diseñadas para que Fase 2 (capacidades activas) las consuma sin rehacer. User stories priorizadas e independientemente entregables. | ✅ |
| II. El agente observa y recuerda; no decide | FR-017 explícito: sin conclusiones ni insights descriptivos en Fase 1. El LLM solo enruta a tools de captura; el escaneo es determinista. | ✅ |
| III. Seguridad ante acciones destructivas | Módulo `hooks/` pre-tool-use bloquea toda modificación/movimiento/borrado hasta confirmación por acción; fail-safe ante ambigüedad (FR-013..015). | ✅ |
| IV. Memoria persistente, estructurada y portable | `.ds_harness/` con JSON por entidad (fuente de verdad) + Markdown derivado; esquemas/rutas estables (FR-010, FR-011). | ✅ |
| V. Llamadas directas al SDK, sin frameworks | `agent_loop/` usa `google-genai` directo; sin LangChain. Cada dependencia justificada en research.md. | ✅ |
| VI. Modularidad y tools con contrato claro | 9 módulos separados; tools con schema (nombre, descripción, parámetros) en `contracts/`. | ✅ |
| VII. Trazabilidad y observabilidad | `agent_log.jsonl` append-only registra acciones y avisos; `git_log/` detecta cambios vía git (FR-006, FR-012). | ✅ |
| VIII. Simplicidad del código | Operaciones deterministas sin LLM; subprocess para git en vez de lib pesada; sin abstracciones prematuras. | ✅ |
| IX. Manejo de errores claro y explícito | `errors.py` con excepciones de dominio; sin `except` genérico; reintento solo para el SDK; escritura atómica (FR-016). | ✅ |

**Resultado del gate (pre-research)**: PASS. Sin violaciones → tabla de Complexity
Tracking vacía.

## Project Structure

### Documentation (this feature)

```text
specs/001-observar-recordar/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0 (/speckit-plan)
├── data-model.md        # Fase 1 (/speckit-plan)
├── quickstart.md        # Fase 1 (/speckit-plan)
├── contracts/           # Fase 1 (/speckit-plan)
│   ├── memory-schemas.md    # Esquemas JSON de cada entidad de memoria
│   ├── tools.md             # Contratos de las tools del agente
│   └── cli.md               # Contratos de los subcomandos CLI
├── checklists/
│   └── requirements.md  # Checklist de calidad del spec
└── tasks.md             # Fase 2 (/speckit-tasks - NO creado aquí)
```

### Source Code (repository root)

```text
src/ds_harness/
├── __init__.py
├── cli.py                 # Punto de entrada: init | scan | status | chat
├── errors.py              # Excepciones de dominio (Principio IX)
├── config.py              # Rutas de .ds_harness/, constantes, exclusiones estándar
├── memory/
│   ├── __init__.py
│   ├── store.py           # Lectura/escritura atómica de JSON por entidad
│   ├── models.py          # Dataclasses de las entidades de memoria
│   └── views.py           # Deriva .ds_harness/views/status.md desde los JSON
├── scanner/
│   ├── __init__.py
│   ├── structure.py       # FR-001: mapa de estructura (pathspec + exclusiones)
│   ├── sources.py         # FR-002: detección de fuentes (.py/.ipynb/.sql)
│   └── extractors/        # Parsers por tipo: python_ast, notebook, sql
│       ├── __init__.py
│       ├── python_ast.py
│       ├── notebook.py
│       └── sql.py
├── lineage/
│   ├── __init__.py
│   └── infer.py           # FR-008: artefacto→script→fuente (lecturas/escrituras)
├── git_log/
│   ├── __init__.py
│   └── history.py         # FR-006: lee commits vía subprocess; degrada sin git
├── hooks/
│   ├── __init__.py
│   └── pre_tool_use.py    # FR-013..015: barrera de seguridad, confirmación por acción
├── tools/
│   ├── __init__.py
│   ├── registry.py        # Registro y dispatch de tools con su schema
│   ├── annotate.py        # Tool: anotar decisión
│   ├── define_column.py   # Tool: definir/override columna en diccionario
│   ├── confirm_lineage.py # Tool: confirmar/corregir linaje inferido
│   └── query_memory.py    # Tool: consultar memoria
├── agent_loop/
│   ├── __init__.py
│   ├── loop.py            # Loop de agente; llamadas directas a google-genai
│   └── client.py          # Wrapper del SDK con reintento (backoff) solo para LLM
└── logging_setup.py       # agent_log.jsonl append-only

tests/
└── fixtures/              # Proyectos de DS de ejemplo (con/sin git, con SQL, etc.)
```

**Structure Decision**: Single project (Opción 1) con paquete `src/ds_harness/`. Cada
responsabilidad del spec/usuario es un subpaquete (Principio VI), evitando el monolito.
`.ds_harness/` es la carpeta de memoria **dentro del proyecto del usuario** (no del repo
del harness), creada por `cli.py init`.

## Complexity Tracking

> Sin violaciones de la constitución. Tabla intencionalmente vacía.

No hay desviaciones que justificar: todas las dependencias externas (`google-genai`,
`pathspec`, `sqlglot`) están justificadas una a una en `research.md`, y la arquitectura
respeta modularidad, simplicidad y manejo explícito de errores.
