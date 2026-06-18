# Contract — Agent Tools

Tools que el agente puede invocar en modo `chat` (Principio VI: nombre, descripción,
parámetros explícitos). El loop de agente declara estas funciones al SDK `google-genai`;
cuando el modelo elige una, el **harness** la ejecuta (no el SDK), pasando antes por el
dispatcher/hook (Principio III). Cada tool declara `mutates_filesystem` para la barrera de
seguridad.

Las cuatro tools de Fase 1 escriben **solo en `.ds_harness/`** (memoria), nunca en
archivos del proyecto del usuario ⇒ `mutates_filesystem: false` ⇒ no disparan el hook. El
hook queda operativo para Fase 2, cuando existan tools con `mutates_filesystem: true`.

**Criterio de ambigüedad (fail-safe, FR-015)**: toda tool cuyo schema no declare
explícitamente `mutates_filesystem` (o lo declare con un valor no booleano) se trata como
**ambigua** y, por tanto, como destructiva — el dispatcher la bloquea hasta confirmación.
Por eso las 4 tools de Fase 1 declaran `mutates_filesystem: false` de forma explícita.

Resultado uniforme: toda tool devuelve `{ "ok": bool, "message": str, "data": object|null }`
y registra una línea en `agent_log.jsonl`. Los errores se devuelven como `ok=false` con
mensaje accionable (Principio IX), sin lanzar excepción al loop.

---

## `annotate_decision`

- **Descripción**: Guarda el "por qué" de una decisión como anotación persistente, con un
  objetivo opcional (archivo, fuente o columna) o a nivel de proyecto.
- **mutates_filesystem**: false
- **Parámetros**:

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `text` | string | sí | Razonamiento en texto libre |
| `target_type` | enum `file`/`source`/`column` | no | Tipo de objetivo; omitir = nivel proyecto |
| `target_ref` | string | no | Referencia: ruta (file), `identity` (source) o nombre (column). Requerido si `target_type` está presente |

- **Efecto**: añade una `Anotación` a `annotations.json` con `id` y `created_at` generados.
- **Errores**: `target_type` sin `target_ref` ⇒ `ok=false` ("Falta target_ref para el
  objetivo indicado"). `target_ref` que no corresponde a ningún elemento existente en
  memoria ⇒ `ok=true` con aviso (registrado como `warning`), no error — se permite
  referenciar un elemento aún no materializado (mismo patrón que el override anticipado
  del diccionario; ver data-model.md sección 6).

## `define_column`

- **Descripción**: Crea o actualiza la definición de una columna en el diccionario, global
  o como override de una fuente/dataset.
- **mutates_filesystem**: false
- **Parámetros**:

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `column` | string | sí | Nombre de la columna/feature |
| `definition` | string | sí | Significado |
| `scope` | string | no | `global` (defecto) o la `identity` de una fuente (override) |

- **Efecto**: upsert por `(column, scope)`; si existe, actualiza `definition` y añade a
  `history`. Devuelve si fue creación o actualización.
- **Errores**: `scope` que no es `global` ni una `identity` conocida ⇒ `ok=true` con aviso
  (se permite definir override anticipado), registrado como `warning`.

## `confirm_lineage`

- **Descripción**: Confirma o corrige un registro de linaje inferido (artefacto → producer
  → inputs).
- **mutates_filesystem**: false
- **Parámetros**:

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `artifact` | string | sí | Ruta del artefacto (clave del registro) |
| `action` | enum `confirm`/`correct` | sí | Confirmar lo inferido o corregirlo |
| `producer` | string | no | Nuevo producer (solo si `action=correct`) |
| `inputs` | array<string> | no | Nuevas `identity` de fuentes (solo si `action=correct`) |

- **Efecto**: `confirm` ⇒ `origin="user_confirmed"`; `correct` ⇒ aplica cambios y
  `origin="user_corrected"`. Estos registros no se sobrescriben en futuros `scan`.
- **Errores**: `artifact` inexistente en `lineage.json` ⇒ `ok=false` ("No hay linaje para
  ese artefacto; ejecuta `scan` primero").

## `query_memory`

- **Descripción**: Consulta de solo lectura sobre la memoria capturada (mapa, fuentes,
  diccionario, bitácora, linaje, anotaciones). En Fase 1 es **recuperación literal**, sin
  resumen ni interpretación (FR-017).
- **mutates_filesystem**: false
- **Parámetros**:

| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `entity` | enum `map`/`sources`/`dictionary`/`changelog`/`lineage`/`annotations` | sí | Qué entidad consultar |
| `filter` | string | no | Filtro literal simple (p. ej. nombre de columna, ruta) |

- **Efecto**: devuelve los registros que casan, tal cual están en memoria.
- **Límite (FR-017)**: NO produce conclusiones, recomendaciones ni observaciones
  descriptivas; solo devuelve lo almacenado.

---

## Declaración al SDK (forma)

Cada tool se declara con `name`, `description` y un `parameters` tipo JSON Schema
(propiedades + `required`), siguiendo la especificación de function declarations de
`google-genai`. El loop mantiene `automatic_function_calling` desactivado: el modelo
**propone** la llamada; el harness valida, pasa por el dispatcher/hook y ejecuta.
