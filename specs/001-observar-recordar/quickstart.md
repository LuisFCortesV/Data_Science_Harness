# Quickstart — Validación Fase 1: Base: Observar y Recordar

Guía para verificar end-to-end que la Fase 1 funciona. Cada escenario mapea a una user
story / criterio de éxito del spec. No incluye código de implementación (eso va en
`tasks.md`). Referencias: [spec](./spec.md), [data-model](./data-model.md),
[contracts](./contracts/).

## Prerrequisitos

- Python 3.11+ (entorno local: 3.14).
- `git` en el PATH (para la bitácora; su ausencia se valida en S5).
- Dependencias instaladas: `google-genai`, `pathspec`, `sqlglot`, `pytest` (dev).
- Para el modo `chat`: variable de entorno `GEMINI_API_KEY`.
- Un proyecto de DS de ejemplo en `tests/fixtures/` (con código `.py`/`.ipynb`/`.sql`,
  `.gitignore`, e historial git).

## Setup

```bash
# desde la raíz del repo del harness
python -m pip install -e ".[dev]"

# operar sobre un proyecto de ejemplo
cd tests/fixtures/sample_ds_project
python -m ds_harness init
```

Resultado esperado: se crea `.ds_harness/` con `meta.json`, archivos de entidad y
`views/status.md`; se imprime un resumen (archivos, fuentes, git sí/no). **Verificar**:
ningún archivo del proyecto de ejemplo cambió (SC-001).

---

## Escenario S1 — Escaneo de estructura y fuentes (US1, SC-001)

```bash
python -m ds_harness scan
```

- **Esperado**: `map.json` lista la estructura **excluyendo** lo de `.gitignore`, `.git/` y
  `.ds_harness/`. `sources.json` contiene las fuentes referenciadas en el código.
- **Verificar identidad/dedup (US1.4)**: una fuente referenciada por dos archivos aparece
  como **una** entrada con dos `references`.
- **Verificar SQL**: una tabla `esquema.tabla` en un `.sql` aparece con `kind="sql"`,
  `identity="esquema.tabla"`, `status=null`.
- **Verificar desacople (FR-002)**: una fuente referenciada en código cuyo archivo de datos
  está en `.gitignore` **sí** se cataloga.
- **Verificar no-mutación (SC-001)**: `git status` del proyecto de ejemplo sin cambios.

## Escenario S2 — Barrera de seguridad (US2, SC-002)

Como en Fase 1 no hay tools destructivas reales (FR-018), se valida manualmente con la tool
de prueba `tests/fixtures/sample_destructive_tool.py` (marcada `mutates_filesystem: true`),
invocando el dispatcher desde un intérprete de Python:

```python
# Sesión interactiva (python), desde la raíz del repo
from ds_harness.tools.registry import ToolRegistry
from tests.fixtures.sample_destructive_tool import destructive_tool, SCHEMA

reg = ToolRegistry()
reg.register(destructive_tool, SCHEMA)        # mutates_filesystem: true

# 1) Acción destructiva: debe pedir confirmación [s/N]
reg.dispatch("destructive_tool", {})          # responder "n" → bloqueada
# 2) Repetir y responder "s" → autoriza UNA acción
# 3) Una segunda invocación vuelve a pedir confirmación (no hay lote)
```

Pasos a verificar manualmente:

1. **Bloqueo**: la invocación se detiene y pide confirmación explícita antes de ejecutar.
2. **Por acción, no por lotes**: responder "s" autoriza **una** acción; la siguiente
   invocación vuelve a preguntar.
3. **Rechazo**: responder "n" devuelve `{"ok": false, ...}` y no ejecuta nada (estado
   intacto).
4. **Fail-safe (ambigüedad)**: registrar una tool **sin** `mutates_filesystem` en su schema
   y comprobar que el dispatcher la trata como destructiva (pide confirmación).
5. **No destructivas**: registrar una tool con `mutates_filesystem: false` y comprobar que
   se ejecuta sin prompt.
6. **Trazabilidad**: cada decisión (bloqueo/confirmación/rechazo) aparece en
   `.ds_harness/agent_log.jsonl`.

## Escenario S3 — Anotaciones y diccionario (US3, US4, SC-003)

```bash
export GEMINI_API_KEY=...   # requerido para chat
python -m ds_harness chat
# > "Anota que descartamos var_99 por fuga temporal"      → annotate_decision (target column)
# > "var_27 significa días desde la última compra"         → define_column (global)
# > "en ventas.csv, var_27 es recencia en semanas"         → define_column (override)
```

- **Esperado**: `annotations.json` y `dictionary.json` reflejan las entradas; el override
  por fuente coexiste con la global y **prevalece** al consultar esa fuente (US4.3).
- **Persistencia (SC-003)**: cerrar y reabrir; `python -m ds_harness status` sigue
  mostrando todo.

## Escenario S4 — Bitácora y linaje (US5, SC-004)

```bash
python -m ds_harness scan
python -m ds_harness status
```

- **Esperado bitácora**: `changelog.json` tiene una entrada por commit (id, autor, fecha,
  mensaje, archivos); el working tree sin commitear **no** genera entradas.
- **Esperado linaje**: un script que lee `X` y escribe `Y` produce un registro
  `artifact=Y, producer=script, inputs=[X], origin="inferred"`.
- **Corrección de usuario (US5.3)**:
  ```bash
  python -m ds_harness chat
  # > "el linaje de Y es incorrecto, la fuente real es Z"   → confirm_lineage (correct)
  ```
  El registro pasa a `origin="user_corrected"` y **no** se sobrescribe en el siguiente
  `scan`.

## Escenario S5 — Degradación sin git (US5.4, SC-006)

```bash
cd tests/fixtures/sample_no_git    # proyecto sin .git
python -m ds_harness init
```

- **Esperado**: aviso claro de que la bitácora no está disponible (`git_available=false`),
  pero estructura, fuentes, diccionario y anotaciones **siguen** operando. El proceso no
  falla (degradación elegante).

## Escenario S6 — Vista legible (US6, SC-004)

```bash
python -m ds_harness status
```

- **Esperado**: `views/status.md` reúne mapa, fuentes, bitácora, diccionario y linaje en un
  documento legible; las secciones vacías se indican explícitamente (US6.3). Permite
  reconstruir "en qué punto está" el proyecto sin abrir el código.

## Escenario S7 — Manejo de errores (SC-006, FR-016)

Validación manual de la robustez de la memoria y del escaneo:

```bash
# 1) Memoria corrupta: ensuciar un JSON de entidad a mano
echo "{ esto no es json válido" > .ds_harness/sources.json
python -m ds_harness status
# Esperado: error claro y accionable (MemoryCorruptedError); el archivo NO se sobrescribe
cat .ds_harness/sources.json   # sigue conteniendo el texto inválido, intacto

# 2) Archivo de código no parseable: introducir un .py con sintaxis inválida
printf 'def (:\n' > tests/fixtures/sample_ds_project/broken.py
cd tests/fixtures/sample_ds_project && python -m ds_harness scan
# Esperado: el scan registra FileParseError para broken.py y CONTINÚA con los demás
grep FileParseError .ds_harness/agent_log.jsonl
```

Pasos a verificar manualmente:

1. **JSON corrupto**: leer una entidad corrupta eleva `MemoryCorruptedError` con mensaje
   accionable y **no** sobrescribe el archivo.
2. **Código no parseable**: un `.py` inválido durante `scan` registra `FileParseError` para
   ese archivo y el escaneo continúa con los demás (un fallo no tumba el proceso).
3. **Atomicidad**: una escritura de memoria interrumpida no deja el JSON a medias (se usa
   archivo temporal + `os.replace`).

> Restaurar los archivos modificados (`git checkout` del fixture, borrar `broken.py`) tras
> la validación.

## Escenario S8 — Trazabilidad (SC-005, FR-012)

```bash
cat .ds_harness/agent_log.jsonl
```

- **Esperado**: una línea JSON por acción ejecutada (scan, init, anotaciones, etc.) y por
  aviso/error, con `action` y `why` (qué hizo y por qué). El 100% de las acciones del
  agente quedan registradas.

---

## Validación completa de la fase

Esta fase no incluye una suite de tests automatizada (no solicitada en el spec). La
aceptación se valida ejecutando manualmente los escenarios S1–S8 sobre los fixtures:

```bash
# Recorrer S1–S8 en orden sobre tests/fixtures/sample_ds_project (y sample_no_git para S5)
```

Criterio de aceptación de la fase: S1–S8 se verifican manualmente con éxito y los criterios
SC-001..SC-006 del spec son observables con los comandos/pasos anteriores.
