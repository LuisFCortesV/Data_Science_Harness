# Tasks: Fase 1 — Base: Observar y Recordar

**Input**: Design documents from `specs/001-observar-recordar/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Tests**: No incluidos (no solicitados en el spec). Escenarios de validación en `quickstart.md`.

**Organization**: Tasks agrupadas por user story para entrega y verificación independiente.
Sin tests, cada US es un incremento funcional entregable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelizable (archivos distintos, sin dependencias entre sí)
- **[Story]**: US a la que pertenece la tarea (US1..US6)
- Rutas relativas a la raíz del repo del harness.

---

## Phase 1: Setup (Infraestructura compartida)

**Purpose**: Estructura del proyecto, configuración de entorno y módulo de errores.
Sin esta fase no puede comenzar ninguna historia.

- [X] T001 Crear estructura de directorios `src/ds_harness/` con `__init__.py` en cada subpaquete según plan.md (memory/, scanner/extractors/, lineage/, git_log/, hooks/, tools/, agent_loop/) y directorio `tests/fixtures/`
- [X] T002 [P] Crear `pyproject.toml` con metadatos del paquete, dependencias (`google-genai`, `pathspec`, `sqlglot`) y grupo dev (`pytest`); editable install `pip install -e ".[dev]"`
- [X] T003 [P] Crear `src/ds_harness/config.py` con constantes: ruta de `.ds_harness/`, exclusiones estándar (`.git/`, `.ds_harness/`), nombre del log, versión del harness
- [X] T004 [P] Crear `src/ds_harness/errors.py` con jerarquía de excepciones de dominio: `DSHarnessError`, `MemoryCorruptedError`, `GitNotAvailableError`, `FileParseError`, `SourceNotLocatedWarning`, `ToolBlockedError`, `LLMError`
- [X] T005 [P] Crear `src/ds_harness/logging_setup.py`: handler JSONL append-only sobre `agent_log.jsonl`; función `get_logger()` que devuelve un logger configurado con campos `ts`, `level`, `action`, `why`, `detail`

**Checkpoint**: Estructura base lista. `python -m pytest --collect-only` sin errores de importación.

---

## Phase 2: Foundational (Prerequisitos bloqueantes)

**Purpose**: Capa de persistencia (`memory/`) y esquema de entidades. Todos los módulos
del harness leen y escriben a través de esta capa — nada de US puede implementarse sin ella.

**⚠️ CRÍTICO**: Ninguna user story puede comenzar hasta que esta fase esté completa.

- [X] T006 Crear `src/ds_harness/memory/models.py` con dataclasses de las 8 entidades: `StructureNode`, `DataSource`, `SourceRef`, `DictionaryEntry`, `DictionaryChange`, `ChangelogCommit`, `LineageRecord`, `DecisionAnnotation`, `AgentLogEntry` — según data-model.md
- [X] T007 [P] Crear `src/ds_harness/memory/store.py`: funciones `read_entity(name)` y `write_entity(name, data)` con escritura atómica (`tempfile` + `os.replace`); eleva `MemoryCorruptedError` ante JSON inválido sin sobrescribir; crea `.ds_harness/` si no existe
- [X] T008 [P] Crear `src/ds_harness/memory/views.py`: función `render_status(project_root)` que lee los 6 JSON de entidad y genera `.ds_harness/views/status.md`; secciones vacías se indican explícitamente (nunca parsea de vuelta el Markdown)
- [X] T009 Crear fixture de proyecto DS de ejemplo en `tests/fixtures/sample_ds_project/`: scripts `.py` con `pd.read_csv`, notebooks `.ipynb`, archivo `.sql` con `FROM esquema.tabla`, `.gitignore`, historial git con ≥2 commits, y subdirectorio de datos

**Checkpoint**: `from ds_harness.memory import store, models, views` sin errores; `store.write_entity` + `store.read_entity` en round-trip producen el mismo objeto; memoria corrupta eleva `MemoryCorruptedError`.

---

## Phase 3: User Story 1 — Escanear y persistir estructura y fuentes (Priority: P1) 🎯 MVP

**Goal**: `ds_harness init` y `ds_harness scan` escanean el proyecto, persisten `map.json`
y `sources.json`, y no modifican ningún archivo del proyecto del usuario.

**Independent Test** (quickstart S1): `python -m ds_harness init` en `tests/fixtures/sample_ds_project` crea `.ds_harness/` y produce `map.json` con la estructura (excluyendo `.gitignore`) y `sources.json` con fuentes reales; `git status` del fixture sin cambios.

### Implementation

- [X] T010 [P] [US1] Crear `src/ds_harness/scanner/extractors/python_ast.py`: recorre el AST del código `.py` con `ast.parse`, extrae rutas literales de lectura (`pd.read_*`, `open`, `np.load`, etc.) y escritura (`to_csv`, `to_parquet`, etc.); captura `FileParseError` por archivo sin tumbar el escaneo
- [X] T011 [P] [US1] Crear `src/ds_harness/scanner/extractors/notebook.py`: lee `.ipynb` como JSON (stdlib), extrae celdas `code`, concatena `source` y reutiliza el extractor de `python_ast`; ignora celdas con magics sin error
- [X] T012 [P] [US1] Crear `src/ds_harness/scanner/extractors/sql.py`: usa `sqlglot` para extraer tablas calificadas `esquema.tabla` de `FROM`/`JOIN` (fuentes) e `INSERT INTO`/`CREATE TABLE` (artefactos); tablas sin esquema se marcan con scope vacío y aviso en log
- [X] T013 [US1] Crear `src/ds_harness/scanner/sources.py`: orquesta los 3 extractores sobre todos los `.py`/`.ipynb`/`.sql` del árbol (salvo `.git/` y `.ds_harness/`, independiente del filtro `.gitignore`); deduplica por identidad (ruta normalizada para archivos, `esquema.tabla` para SQL); agrega `references`; resuelve `status` (located/not_located) solo para `kind=file`; persiste `sources.json` vía `store.write_entity`
- [X] T014 [US1] Crear `src/ds_harness/scanner/structure.py`: recorre el árbol con `pathlib` + `pathspec` (carga `.gitignore` si existe; si no, solo exclusiones estándar); genera lista de `StructureNode`; persiste `map.json` vía `store.write_entity`; registra `excluded_rules` para trazabilidad
- [X] T015 [US1] Crear `src/ds_harness/cli.py` con subcomando `init`: crea `.ds_harness/` con `meta.json` y archivos de entidad vacíos (schema_version inicializado); es idempotente (si ya existe, informa y sugiere `scan`); luego ejecuta el flujo de `scan`; imprime resumen (archivos mapeados, fuentes, git sí/no)
- [X] T016 [US1] Agregar subcomando `scan` a `src/ds_harness/cli.py`: invoca `structure.scan()` y `sources.scan()` en orden; registra inicio/fin y avisos en `agent_log.jsonl`; imprime diff resumido de cambios

**Checkpoint**: `python -m ds_harness init` y `python -m ds_harness scan` pasan los escenarios S1 del quickstart. 0 archivos del fixture alterados.

---

## Phase 4: User Story 2 — Barrera de seguridad (Priority: P1)

**Goal**: El dispatcher de tools bloquea toda operación con `mutates_filesystem=True` hasta
confirmación explícita del usuario por acción individual; fail-safe ante ambigüedad.

**Independent Test** (quickstart S2): validación manual con una tool de prueba marcada `mutates_filesystem=True` — queda bloqueada hasta confirmación individual; rechazar no ejecuta nada; ambigüedad = destructiva; tools no destructivas no se bloquean.

### Implementation

- [X] T017 [US2] Crear `src/ds_harness/hooks/pre_tool_use.py`: función `check_destructive(tool_name, mutates_filesystem, description)` que, si `mutates_filesystem=True` o ambigüedad, imprime descripción de la acción y pide confirmación `[s/N]`; retorna `True` si confirmado, `False` si rechazado; eleva `ToolBlockedError` ante rechazo explícito; registra la decisión en log. Criterio de ambigüedad: toda tool cuyo schema no declare explícitamente `mutates_filesystem` (o lo declare con un valor no booleano) se trata como ambigua y, por tanto, como destructiva (fail-safe, FR-015)
- [X] T018 [US2] Crear `src/ds_harness/tools/registry.py`: `ToolRegistry` con `register(tool_fn, schema)` y `dispatch(tool_name, params)`; antes de cada dispatch invoca `pre_tool_use.check_destructive` con el `mutates_filesystem` del schema; si rechazado, devuelve `{"ok": false, "message": "...", "data": null}` sin ejecutar la tool
- [X] T019 [P] [US2] Crear `tests/fixtures/sample_destructive_tool.py`: tool de prueba con `mutates_filesystem=True` para validar el hook sin tools reales destructivas (FR-018)

**Checkpoint**: El dispatcher bloquea 100% de las tools destructivas (S2); las no destructivas pasan sin prompt.

---

## Phase 5: User Story 3 — Anotar decisiones (Priority: P2)

**Goal**: El usuario puede anotar el "por qué" de una decisión en modo `chat`, asociándola
opcionalmente a un elemento de la memoria; la anotación persiste entre sesiones. El modelo
en `chat` está acotado por un system prompt que le impide emitir juicio analítico
(Principio II / FR-017).

**Independent Test** (quickstart S3, parte anotaciones): Ejecutar `chat` y anotar una decisión con y sin target; cerrar; `annotations.json` contiene ambas anotaciones. Verificar que el modelo declina dar conclusiones de modelado/negocio.

### Implementation

- [X] T020 [P] [US3] Crear `src/ds_harness/tools/annotate.py`: implementa la tool `annotate_decision` (contrato en `contracts/tools.md`); valida que `target_ref` esté presente si `target_type` lo está; **no valida la existencia de `target_ref` en memoria** (se acepta igual, con `warning` en `agent_log.jsonl` si no resuelve contra ningún elemento conocido — ver data-model.md sección 6); genera `id` y `created_at`; persiste en `annotations.json` vía `store`; devuelve `{"ok": true/false, "message": ..., "data": ...}`
- [X] T021 [US3] Crear `src/ds_harness/agent_loop/client.py`: wrapper de `google-genai` con reintento exponencial (2–3 intentos, backoff simple) solo para llamadas al modelo; eleva `LLMError` al agotar intentos; valida que `GEMINI_API_KEY` esté en entorno
- [X] T022 [P] [US3] Crear `src/ds_harness/agent_loop/system_prompt.py`: constante `SYSTEM_PROMPT` que instruye al modelo a (a) solo enrutar a las tools disponibles o responder con datos literales recuperados de la memoria, (b) NUNCA emitir conclusiones de modelado, de negocio, recomendaciones ni observaciones descriptivas computadas sobre datos (eso es Fase 2, no Fase 1), (c) si el usuario pide una opinión o conclusión analítica, declinar explícitamente explicando que esa capacidad no existe en esta fase. Referencia: Principio II, FR-017
- [X] T023 [US3] Crear `src/ds_harness/agent_loop/loop.py`: loop de agente con `automatic_function_calling` desactivado; usa `SYSTEM_PROMPT` (de `system_prompt.py`) como system instruction de la sesión con el SDK `google-genai`; obtiene las tools desde `tools.wiring.get_registry()` (ver T031) y las declara al SDK; ejecuta: recibe turno del modelo → si propone tool → dispatcher → devuelve resultado → siguiente turno; corta el loop ante `LLMError` limpiamente
- [X] T024 [US3] Agregar subcomando `chat` a `src/ds_harness/cli.py`: valida `GEMINI_API_KEY`; entra al loop con `agent_loop.loop`; registra inicio/fin de sesión en log

**Checkpoint**: `ds_harness chat` → "anota que descartamos var_99 por fuga temporal" → `annotations.json` contiene la anotación con `target.type="column"`. Persiste tras reinicio. El modelo rechaza dar conclusiones analíticas (FR-017).

---

## Phase 6: User Story 4 — Diccionario de datos (Priority: P2)

**Goal**: El usuario puede definir/actualizar el significado de columnas (global o override
por fuente) desde `chat`; el diccionario persiste con trazabilidad de cambios.

**Independent Test** (quickstart S3, parte diccionario): Definir `var_27` global y su override para `ventas.csv`; verificar `dictionary.json` con ambas entradas y que el override prevalece al consultar esa fuente.

### Implementation

- [X] T025 [P] [US4] Crear `src/ds_harness/tools/define_column.py`: implementa `define_column` (contrato en `contracts/tools.md`); upsert por `(column, scope)` con append a `history`; si `scope` no es `global` ni una `identity` conocida en `sources.json`, acepta con `ok=true` + warning en log (override anticipado, data-model.md regla); persiste `dictionary.json` vía `store`
- [X] T026 [P] [US4] Crear `src/ds_harness/tools/query_memory.py`: implementa `query_memory` (contrato en `contracts/tools.md`); consulta de solo lectura sobre cualquier entidad; aplica `filter` literal si se proporciona; devuelve datos tal cual (sin inferencia ni resumen, FR-017)

**Checkpoint**: Definir columna global + override; `query_memory` con filtro devuelve ambas entradas; override prevalece (US4.3). Sin modificar archivos del proyecto del usuario.

---

## Phase 7: User Story 5 — Bitácora y linaje (Priority: P2)

**Goal**: `scan` registra los commits del historial git en `changelog.json` e infiere el
linaje `artefacto→script→fuente` en `lineage.json`; el usuario puede confirmar/corregir
el linaje inferido desde `chat`.

**Independent Test** (quickstart S4): `scan` sobre `sample_ds_project` → `changelog.json` con ≥2 commits (id, autor, fecha, mensaje, archivos); `lineage.json` con al menos un registro `inferred`; corrección via `chat` → `origin="user_corrected"` persiste tras nuevo `scan`.

### Implementation

- [X] T027 [P] [US5] Crear `src/ds_harness/git_log/history.py`: invoca `git log` via `subprocess` con formato delimitado estable; parsea stdout a lista de `ChangelogCommit`; captura `GitNotAvailableError` si `git` no está o el directorio no es repo; persiste `changelog.json` con `git_available=true/false`
- [X] T028 [P] [US5] Crear `src/ds_harness/lineage/infer.py`: reutiliza los extractores de `scanner/`; cruza lecturas (fuentes ya catalogadas en `sources.json`) y escrituras (artefactos) por script/notebook; produce lista de `LineageRecord` con `origin="inferred"`; al persistir en `lineage.json`, NO sobrescribe registros con `origin` en `user_confirmed`/`user_corrected`
- [X] T029 [US5] Crear `src/ds_harness/tools/confirm_lineage.py`: implementa `confirm_lineage` (contrato en `contracts/tools.md`); `confirm` → `origin="user_confirmed"`; `correct` → aplica nuevos `producer`/`inputs` y `origin="user_corrected"`; eleva `ok=false` si `artifact` no existe en `lineage.json`
- [X] T030 [US5] Integrar `git_log` y `lineage` en el flujo de `scan` (`cli.py`): después de `structure` y `sources`, ejecutar `history.sync()` y `infer.sync()`; avisar si `git_available=false`; degradar sin fallar el resto
- [X] T031 [P] Crear `src/ds_harness/tools/wiring.py`: registra las 4 tools (`annotate_decision`, `define_column`, `confirm_lineage`, `query_memory`) en una instancia de `ToolRegistry` junto con su schema (nombre, descripción, parámetros, `mutates_filesystem`) tal como están definidos en `contracts/tools.md`; expone `get_registry()` para que `agent_loop/loop.py` (T023) la consuma. Depende de que las 4 tools existan (T020, T025, T026, T029). Para entrega incremental, `wiring` puede crearse antes registrando solo las tools ya disponibles y ampliarse al cerrar cada fase; esta tarea garantiza el registro completo de las 4

**Checkpoint**: S4 y S5 del quickstart pasan. Registros `user_corrected` sobreviven a re-scan. `get_registry()` devuelve las 4 tools con su schema.

---

## Phase 8: User Story 6 — Vista legible del estado (Priority: P3)

**Goal**: `ds_harness status` regenera `views/status.md` con mapa, fuentes, bitácora,
diccionario y linaje; secciones vacías indicadas; el usuario puede recontextualizarse sin
abrir código.

**Independent Test** (quickstart S6): Con memoria poblada por US1–US5, `ds_harness status` genera `views/status.md` legible con todas las secciones; una sección vacía (p. ej. sin anotaciones) se indica explícitamente; re-ejecutar actualiza el contenido.

### Implementation

- [X] T032 [US6] Completar `src/ds_harness/memory/views.py` (stub en T008): implementar `render_status` completo — sección por entidad con formato Markdown legible; secciones vacías con indicador explícito (nunca falla por sección vacía); enlaza `schema_version` y `scanned_at` en encabezado
- [X] T033 [US6] Agregar subcomando `status` a `src/ds_harness/cli.py`: invoca `views.render_status()`; escribe `views/status.md`; imprime el contenido; registra en log

**Checkpoint**: S6 del quickstart pasa. `views/status.md` con todas las secciones del fixture; sección de anotaciones vacía si no hay anotaciones.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Robustez, trazabilidad completa y validación final del quickstart.

- [X] T034 [P] Agregar fixture `tests/fixtures/sample_no_git/`: proyecto DS sin `.git` para validar degradación elegante (S5 del quickstart)
- [X] T035 [P] Agregar fixture `tests/fixtures/sample_empty/`: proyecto vacío sin fuentes ni código para validar edge cases (catálogo vacío, mapa válido)
- [X] T036 Validar cobertura de log en todos los módulos: toda acción de `scan`, `init`, `status`, `chat`, tool ejecutada y error/aviso DEBEN producir una línea en `agent_log.jsonl` con `action` y `why` (SC-005, FR-012)
- [X] T037 [P] Revisar manejo de errores en todos los módulos: ningún `except Exception` genérico; cada módulo captura sus propios fallos con excepciones de `errors.py`; un fallo no deja memoria en estado inconsistente (FR-016, Principio IX)
- [X] T038 Ejecutar suite completa del quickstart (`quickstart.md` S1–S8) sobre `sample_ds_project` y documentar resultado

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sin dependencias — comenzar de inmediato.
- **Phase 2 (Foundational)**: Requiere Phase 1 — bloquea todo lo demás.
- **Phase 3 (US1 — scan/init)**: Requiere Phase 2. Base de los extractores reutilizados por US5.
- **Phase 4 (US2 — seguridad)**: Requiere Phase 2. Independiente de US1; el dispatcher se usa a partir de Phase 5.
- **Phase 5 (US3 — anotaciones)**: Requiere Phase 2 (persistencia) y Phase 4 (dispatcher/hook). **NO depende de Phase 3** — puede ejecutarse en paralelo con US1. (`agent_log` ya está listo desde Phase 1.)
- **Phase 6 (US4 — diccionario)**: Requiere Phase 4 (dispatcher). Puede ejecutarse en paralelo con Phases 5 y 7.
- **Phase 7 (US5 — bitácora/linaje)**: Requiere Phase 3 (extractores y `sources.json`). T031 (wiring) requiere además que existan las 4 tools (T020, T025, T026, T029). Puede ejecutarse en paralelo con Phases 5 y 6 salvo por T031.
- **Phase 8 (US6 — vista legible)**: Requiere que Phases 3–7 estén completas (consolida toda la memoria).
- **Phase 9 (Polish)**: Requiere todas las fases anteriores.

> **Nota wiring (T031) ↔ loop (T023)**: el loop de US3 consume `wiring.get_registry()`. La
> versión final de `wiring` (con las 4 tools) se cierra en Phase 7; para mantener US3
> independientemente verificable (solo necesita `annotate_decision`), `wiring` puede
> introducirse temprano registrando las tools disponibles y ampliarse a medida que cada
> tool aterriza. T031 garantiza el registro completo.

### User Story Dependencies

```
Phase 1 (Setup)
  └── Phase 2 (Foundational) ──────────────────────────────┐
        ├── Phase 3 (US1: scan/init)                        │
        │     └── Phase 7 (US5: bitácora/linaje)            │
        │             └── T031 wiring (requiere las 4 tools)│
        ├── Phase 4 (US2: seguridad) ── dispatcher/hook ────┤
        │     ├── Phase 5 (US3: anotaciones)  ◄── Phase 2 + Phase 4 (no Phase 3)
        │     └── Phase 6 (US4: diccionario)
        └────────────────────────────────────────────────────
              Phase 8 (US6: vista legible)  ◄── tras US1..US5
                    Phase 9 (Polish)
```

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 paralelizables entre sí (archivos distintos).
- **Phase 2**: T007 y T008 paralelizables; T009 (fixture) independiente.
- **Phases 3, 4 y 5**: paralelizables entre sí — US1 (scan), US2 (hook) y US3 (anotaciones) no dependen unas de otras (US3 solo requiere Phase 2 + Phase 4).
- **Phases 6 y 7**: paralelizables con Phase 5 una vez disponibles sus dependencias (Phase 4 para US4; Phase 3 para US5).
- **Dentro de US1**: T010, T011, T012 (extractores) en paralelo; T013 y T014 secuenciales tras ellos.
- **Dentro de US3**: T022 (system_prompt) en paralelo con T020/T021 (archivos distintos); T023 (loop) tras T021/T022 y `wiring`.
- **Dentro de US5**: T027 y T028 en paralelo; T029 y T030 tras ellos; T031 tras las 4 tools.

---

## Parallel Example: Phase 3 (US1)

```
# En paralelo (archivos distintos):
T010: scanner/extractors/python_ast.py
T011: scanner/extractors/notebook.py
T012: scanner/extractors/sql.py

# Secuencial (usa los extractores):
T013: scanner/sources.py   → después de T010–T012
T014: scanner/structure.py → puede ir con T013 (archivos distintos)
T015: cli.py (init)        → después de T013–T014
T016: cli.py (scan)        → después de T015
```

---

## Implementation Strategy

### MVP First (US1 + US2 — scan seguro)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational
3. Completar Phase 3: US1 (scan/init)
4. Completar Phase 4: US2 (barrera de seguridad)
5. **STOP & VALIDATE**: `ds_harness init` + `ds_harness scan` sin tocar archivos del usuario; hook bloquea tools destructivas.
6. Demostrar SC-001 y SC-002 del spec.

### Incremental Delivery

- US1 + US2 → scan seguro del proyecto (MVP)
- + US3 → anotar decisiones desde `chat` (arranca en paralelo con US1; solo requiere Phase 2 + Phase 4)
- + US4 → diccionario de datos persistente
- + US5 → bitácora git + linaje inferido y corregible (incluye T031 wiring que completa el registry)
- + US6 → vista legible del estado completo
- + Polish → robustez y cobertura de log total

### Parallel Opportunity (un desarrollador)

Con un solo desarrollador, el orden recomendado para maximizar velocidad:
- Setup → Foundational → **US1, US2 y US3 en paralelo** (extractores deterministas + hook + anotaciones) → US4 + US5 → US6 → Polish. (US3 ya no espera a US1.)

---

## Notes

- `[P]` = paralelizable (archivos distintos, sin dependencias incompletas).
- `[USn]` = traza la tarea a su user story para cobertura en `/speckit-analyze`.
- Ninguna tarea modifica archivos del proyecto del usuario (FR-004); toda escritura va a `.ds_harness/`.
- La tool `query_memory` (T026) es de solo lectura; NO requiere pasar por el hook de seguridad.
- El system prompt (T022) acota la salida conversacional del modelo a captura/recuperación (Principio II / FR-017); las tools ya son de captura.
- `agent_log.jsonl` es append-only en todos los módulos; nunca se reescribe.
- Las correcciones de linaje del usuario (`user_corrected`) sobreviven a re-scans — implementar verificación explícita en T028.
- Los overrides anticipados del diccionario (T025) se aceptan con warning, no error (data-model.md); el mismo patrón aplica a `target_ref` de anotaciones (T020).
- `wiring.py` (T031) es la única fuente del registry que consume el loop; evita que cada tool se registre por su cuenta.
- Validar al final con la suite completa del quickstart (T038).
