# Phase 0 — Research: Fase 1 Base: Observar y Recordar

Resoluciones de las decisiones técnicas. La arquitectura la fijó el usuario en el input
del plan; aquí se justifican las dependencias (Principio V: una por una) y se resuelven
los "cómo" abiertos. No quedaron marcadores NEEDS CLARIFICATION en el spec.

---

## D1 — SDK del modelo y modelo a usar

- **Decisión**: SDK directo `google-genai` (paquete `google-genai`, import `from google
  import genai`), modelo `gemini-2.5-flash`. Function calling nativo del SDK para enrutar
  a las tools.
- **Rationale**: La constitución exige llamadas directas al SDK sin frameworks (Principio
  V). `google-genai` es el SDK oficial vigente de Gemini y soporta declaración de
  funciones/tools y modo de invocación controlada. `gemini-2.5-flash` ofrece baja latencia
  y costo adecuado para la única tarea LLM de Fase 1: interpretar lenguaje natural y elegir
  tool.
- **Alternativas consideradas**: LangChain/LlamaIndex (rechazado: viola Principio V, oculta
  el control del loop). Modelos más grandes (innecesarios para enrutar tools simples).
- **Notas de uso**: desactivar automatic function calling y mantener el loop explícito en
  `agent_loop/loop.py` (el harness ejecuta la tool tras pasar por el hook, no el SDK), para
  conservar el control y la barrera de seguridad. Clave de API por variable de entorno
  (`GEMINI_API_KEY`); nunca persistida en `.ds_harness/`.

## D2 — Detección de fuentes en Python (`.py`)

- **Decisión**: parseo estático con el módulo estándar `ast`. Se recorren llamadas y se
  reconocen patrones de E/S de datos comunes en DS (p. ej. `pd.read_csv`, `pd.read_parquet`,
  `open(...)`, `pl.read_*`, `np.load`, `to_csv`/`to_parquet` para escrituras), extrayendo el
  argumento de ruta cuando es un literal de cadena.
- **Rationale**: `ast` es stdlib (cero dependencias, Principio VIII), no ejecuta el código
  del usuario (FR-008/FR-004) y es robusto frente a formato. Distingue lecturas (fuentes) de
  escrituras (artefactos) por el nombre del método/función.
- **Alternativas consideradas**: regex sobre texto (frágil, falsos positivos); ejecución
  instrumentada (rechazada: el harness no ejecuta código del usuario).
- **Limitación aceptada (Fase 1)**: rutas construidas dinámicamente (variables, f-strings,
  `os.path.join` con variables) pueden no resolverse; se registran como "referencia no
  resoluble" y el usuario puede completarlas vía tool de linaje/confirmación.

## D3 — Detección en notebooks (`.ipynb`)

- **Decisión**: leer el `.ipynb` como JSON (`json` stdlib / formato nbformat v4), extraer
  las celdas `code`, concatenar su `source` y aplicar el mismo análisis `ast` de D2.
- **Rationale**: un `.ipynb` es JSON; no se requiere ejecutar el kernel. Reutiliza el
  extractor de Python. `nbformat` no es necesario para solo leer celdas, evitando una
  dependencia.
- **Alternativas consideradas**: `jupyter nbconvert` a script (dependencia y proceso extra);
  `nbformat` (innecesario para lectura simple).
- **Limitación aceptada**: celdas con magics (`%%sql`, `!cmd`) se ignoran para el análisis
  `ast`; las magics SQL podrían tratarse en una mejora futura.

## D4 — Detección en SQL (`.sql`) e identidad por tabla calificada

- **Decisión**: `sqlglot` para parsear `.sql` y extraer nombres de tabla calificados
  (`esquema.tabla`) de las cláusulas `FROM`/`JOIN` (fuentes) y de `INSERT INTO`/`CREATE
  TABLE`/`UPDATE` (artefactos/escrituras).
- **Rationale**: el parseo de SQL con regex es notoriamente frágil; `sqlglot` es una
  dependencia pura-Python, sin binarios, que normaliza identificadores y resuelve el
  esquema calificado — exactamente lo que pide la clarificación (identidad SQL = tabla
  calificada). Justifica su peso por la robustez que aporta (Principio VIII no prohíbe
  dependencias, prohíbe complejidad injustificada).
- **Alternativas consideradas**: `sqlparse` (tokeniza pero no resuelve esquema/dialecto tan
  bien); regex (frágil, descartado).
- **Notas**: dialecto por defecto genérico; el esquema por defecto (cuando la tabla no está
  calificada en el SQL) se deja sin prefijo y se marca para que el usuario lo complete.

## D5 — Mapa de estructura y exclusiones (`.gitignore`)

- **Decisión**: recorrer el árbol con `os.walk`/`pathlib`, filtrando con `pathspec`
  (gitwildmatch) cargado desde `.gitignore`, más exclusiones estándar fijas (`.git/`,
  `.ds_harness/`).
- **Rationale**: `pathspec` implementa la semántica de `.gitignore` **sin** requerir que el
  proyecto tenga git inicializado (cubre el edge case "proyecto sin git" para el escaneo).
  Reutiliza la intención del usuario ya expresada en `.gitignore` (clarificación).
- **Alternativas consideradas**: `git check-ignore`/`git ls-files` (requiere git presente;
  el escaneo debe funcionar sin git); implementar el matcher a mano (reinventar `pathspec`).
- **Importante (desacople FR-002)**: la **detección de fuentes** (D2–D4) lee el contenido de
  los archivos de código del proyecto con independencia de las exclusiones del mapa; es
  decir, el filtro `.gitignore` aplica al **mapa de estructura**, no a qué código se analiza
  en busca de fuentes. El conjunto de archivos de código a analizar = todos los `.py`/
  `.ipynb`/`.sql` del árbol salvo `.git/` y `.ds_harness/`.

## D6 — Lectura del historial git (bitácora)

- **Decisión**: `subprocess` invocando `git log` con un formato delimitado estable (p. ej.
  `--pretty=format:%H%x1f%an%x1f%aI%x1f%s` y `--name-only`) y parseo del stdout.
- **Rationale**: cero dependencias frente a GitPython (Principio VIII); `git` ya es un
  requisito de esta capacidad. Solo lee commits del historial (clarificación: no working
  tree). Si `git` no está o el directorio no es repo, se captura y se eleva
  `GitNotAvailableError` → degradación con aviso (FR-006 edge case).
- **Alternativas consideradas**: GitPython/pygit2 (dependencia pesada/ binarios para algo
  que `git log` resuelve); leer `.git/` a mano (frágil).
- **Notas**: ejecución idempotente; la bitácora se reconstruye desde el historial en cada
  `scan`, evitando estado divergente.

## D7 — Persistencia: JSON por entidad + escritura atómica + Markdown derivado

- **Decisión**: un archivo JSON por entidad en `.ds_harness/` (fuente de verdad). Escritura
  **atómica**: escribir a un archivo temporal en el mismo directorio y `os.replace()` sobre
  el destino. La vista `views/status.md` se **regenera** completa desde los JSON (nunca se
  parsea de vuelta).
- **Rationale**: atomicidad evita corrupción/estado inconsistente ante fallos (FR-016).
  Separar JSON (máquina) de Markdown (humano) cumple Principio IV. Un archivo por entidad
  mantiene difs pequeños y facilita el futuro índice multi-proyecto (FR-011).
- **Alternativas consideradas**: un único `memory.json` (difs grandes, más riesgo de
  corrupción total); SQLite (innecesario para este volumen; menos portable/legible).
- **Versionado de esquema**: cada JSON incluye `schema_version` para permitir evolución sin
  rediseño (FR-011).

## D8 — Logging (trazabilidad)

- **Decisión**: `agent_log.jsonl` (JSON Lines) **append-only** en `.ds_harness/`. Una línea
  por evento: acción del agente, resultado, y avisos/errores. Se usa el módulo `logging`
  con un handler de archivo que serializa a JSON por línea.
- **Rationale**: append-only es simple, robusto y consultable cronológicamente (Principio
  VII). JSONL es legible por máquina y por humano, y se presta a un futuro índice.
- **Alternativas consideradas**: log de texto plano (menos consultable); base de datos
  (sobreingeniería).

## D9 — Barrera de seguridad (hook pre-tool-use)

- **Decisión**: un dispatcher de tools que, antes de ejecutar cualquier tool marcada como
  potencialmente destructiva (`mutates_filesystem=True` en su contrato), invoca el hook
  `pre_tool_use`. El hook bloquea y pide confirmación interactiva por la **acción
  individual**; sin confirmación afirmativa explícita, no ejecuta. Clasificación
  desconocida/ambigua ⇒ tratada como destructiva (fail-safe).
- **Rationale**: cumple FR-013..015 y Principio III. Centralizar la decisión en el
  dispatcher evita que una tool se salte la barrera. En Fase 1 ninguna tool real muta el
  filesystem (FR-018), pero el hook queda operativo y testeado para Fase 2.
- **Alternativas consideradas**: confirmaciones por lote (prohibido por FR-014); permitir
  que cada tool gestione su confirmación (riesgo de inconsistencia / bypass).
- **Notas**: el mecanismo de confirmación en CLI es un prompt sí/no por acción; las tools de
  Fase 1 (anotar, definir columna, confirmar linaje, consultar) escriben en `.ds_harness/`,
  no en archivos del proyecto, por lo que NO disparan el hook (no son destructivas sobre el
  proyecto).

## D10 — Reintentos y manejo de errores

- **Decisión**: `errors.py` con excepciones específicas (`MemoryCorruptedError`,
  `GitNotAvailableError`, `FileParseError`, `SourceNotLocatedWarning`, `ToolBlockedError`,
  `LLMError`). Reintento con backoff simple (2–3 intentos) **solo** para llamadas al SDK de
  Gemini (errores transitorios de red/cuota). Sin reintento para lecturas locales/git.
- **Rationale**: Principio IX: captura específica, mensajes accionables, un fallo no tumba
  el proceso. Reintentar solo lo que puede resolverse solo (red), no lo que no (archivo
  ausente).
- **Alternativas consideradas**: `except Exception` genérico (prohibido); librería de retry
  (innecesaria para un backoff trivial).

---

## Resumen de dependencias externas (justificación 1 a 1 — Principio V)

| Dependencia | Para qué | Por qué se justifica | Alternativa rechazada |
|-------------|----------|----------------------|-----------------------|
| `google-genai` | Acceso al modelo (modo `chat`) | SDK oficial directo; cumple Principio V | LangChain (viola Principio V) |
| `pathspec` | Respetar `.gitignore` sin git | Semántica gitignore correcta, sin requerir git | `git check-ignore` (requiere git) |
| `sqlglot` | Extraer tablas calificadas de `.sql` | Parseo SQL robusto, pure-Python | regex / `sqlparse` (frágiles) |
| `pytest` (dev) | Tests | Estándar de facto | unittest (más verboso) |

Stdlib usado sin dependencia: `ast`, `json`, `subprocess`, `pathlib`, `logging`, `os`.
