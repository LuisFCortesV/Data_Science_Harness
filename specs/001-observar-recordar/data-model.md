# Phase 1 — Data Model: Fase 1 Base: Observar y Recordar

Modelo de datos de la memoria persistida. Cada entidad vive en su propio archivo JSON
dentro de `.ds_harness/` (fuente de verdad); la vista `views/status.md` se deriva de
ellos. Todos los archivos incluyen `schema_version` (entero) para evolución futura sin
rediseño (FR-011). Mapeo a esquemas JSON concretos: ver `contracts/memory-schemas.md`.

## Diseño de almacenamiento

```text
.ds_harness/
├── meta.json            # schema_version global, created_at, harness_version, project_root
├── map.json             # Mapa de estructura
├── sources.json         # Catálogo de fuentes de datos
├── dictionary.json      # Diccionario de datos (entradas globales + overrides)
├── changelog.json       # Bitácora de commits
├── lineage.json         # Registros de linaje
├── annotations.json     # Anotaciones de decisión
├── agent_log.jsonl      # Log append-only de acciones/avisos del agente
└── views/
    └── status.md        # Vista legible derivada (NO es fuente de verdad)
```

Regla transversal: el JSON es la fuente de verdad; `status.md` se regenera completo y
nunca se parsea de vuelta (Principio IV).

---

## Entidades

### 1. Mapa de estructura — `map.json`

Representación persistida de la organización del proyecto, actualizable (mapa "vivo").

| Campo | Tipo | Reglas |
|-------|------|--------|
| `schema_version` | int | Requerido |
| `scanned_at` | str (ISO-8601) | Momento del último escaneo |
| `root` | str | Ruta raíz del proyecto (relativa = `.`) |
| `entries` | lista de nodos | Árbol o lista plana de rutas relativas incluidas |
| `excluded_rules` | lista de str | Reglas aplicadas (`.gitignore` + estándar) para trazabilidad |

- Nodo: `{ "path": str (relativa, normalizada), "type": "file"|"dir" }`.
- **Exclusiones** (FR-001): se omite lo que casa con `.gitignore` + `.git/` + `.ds_harness/`.
- Se **reemplaza** completo en cada `scan` (refleja el estado actual; escenario US1.2).

### 2. Fuente de datos — `sources.json`

Catálogo de fuentes de datos referenciadas en el código. Identidad dependiente del tipo.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `schema_version` | int | Requerido |
| `sources` | lista de Fuente | Catálogo |

Objeto **Fuente**:

| Campo | Tipo | Reglas |
|-------|------|--------|
| `kind` | enum `"file"`/`"sql"` | Tipo de fuente |
| `identity` | str | **file** → ruta normalizada; **sql** → tabla calificada `esquema.tabla`. **Clave única** dentro del catálogo |
| `references` | lista de Ref | Dónde se referencia (agregada si varios la usan) |
| `status` | enum `"located"`/`"not_located"`/`null` | Solo para `kind=file`; `null`/ausente para `sql` |

- **Ref**: `{ "code_file": str (relativa), "line": int|null }`.
- **Unicidad** (clarif.): una entrada por `identity`. Varias referencias → se **agregan** en
  `references` (US1.4).
- `status` aplica **solo** a `kind=file` (clarif.); las `sql` no se comprueban en disco.
- Solo fuentes **referenciadas** (FR-002/FR-003); no se descubren fuentes externas.
- La detección lee el contenido del código con independencia de las exclusiones del mapa
  (FR-002, desacople explícito).

### 3. Entrada de diccionario de datos — `dictionary.json`

Significado de columnas/features. Modelo **híbrido**: definición global por defecto +
overrides por fuente/dataset (la override prevalece).

| Campo | Tipo | Reglas |
|-------|------|--------|
| `schema_version` | int | Requerido |
| `entries` | lista de EntradaDic | — |

Objeto **EntradaDic**:

| Campo | Tipo | Reglas |
|-------|------|--------|
| `column` | str | Nombre de la columna/feature |
| `scope` | str | `"global"` o la `identity` de una fuente (override) |
| `definition` | str | Significado actual |
| `history` | lista de Cambio | Trazabilidad de cambios |

- **Cambio**: `{ "definition": str, "changed_at": str (ISO-8601) }`.
- **Identidad de la entrada** = `(column, scope)` (clarif.). Registrar la misma `(column,
  scope)` ⇒ **actualización** con entrada en `history`, no duplicado (edge case). Mismo
  `column` con `scope` distinto ⇒ entradas separadas (global vs override).
- **Excepción de validez de `scope`**: a diferencia de `target.ref` en Anotación (que
  apunta a una `identity` ya existente), `scope` en una entrada de diccionario NO
  requiere que la `identity` referenciada exista todavía en `sources.json`. Se permite
  un override "anticipado" —documentar una columna de una fuente que aún no ha sido
  catalogada por `scan`— para no bloquear al usuario que conoce su dataset antes de
  escanear. La tool `define_column` acepta esto con `ok=true` y un aviso (`warning` en
  `agent_log.jsonl`), no como error. Si un `scan` posterior cataloga una fuente con
  identity distinta a la escrita a mano (p. ej. por una ruta mal tipeada), el override
  queda "huérfano" — sigue persistido y consultable bajo su `scope` original, pero no
  se resuelve contra ninguna fuente real (mismo tratamiento de huérfanos que en la
  sección "Relaciones": no se borra sin confirmación).
- **Resolución de consulta**: al consultar `column` para una fuente, si existe entrada con
  `scope = identity` de esa fuente, prevalece; si no, cae a `scope="global"` (US4.3).
- Alimentado por el usuario (FR-005); el harness no infiere significados.

### 4. Entrada de bitácora — `changelog.json`

Commits del historial git (no working tree).

| Campo | Tipo | Reglas |
|-------|------|--------|
| `schema_version` | int | Requerido |
| `git_available` | bool | `false` ⇒ bitácora vacía + aviso (FR-006 edge) |
| `commits` | lista de Commit | — |

Objeto **Commit**: `{ "id": str (hash), "author": str, "date": str (ISO-8601), "message":
str, "files": [str, ...] }` (autor, fecha, mensaje, archivos afectados — clarif.).

- Se reconstruye desde `git log` en cada `scan`. Sin git ⇒ `git_available=false`, `commits=[]`,
  el resto sigue operando (degradación elegante).

### 5. Registro de linaje — `lineage.json`

Relaciones artefacto → script/notebook → fuente, inferidas por análisis estático y
corregibles por el usuario.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `schema_version` | int | Requerido |
| `records` | lista de Linaje | — |

Objeto **Linaje**:

| Campo | Tipo | Reglas |
|-------|------|--------|
| `artifact` | str | Ruta normalizada del archivo generado (escritura detectada) |
| `producer` | str | Script/notebook que lo genera (ruta relativa) |
| `inputs` | lista de str | `identity` de fuentes leídas por el producer |
| `origin` | enum `"inferred"`/`"user_confirmed"`/`"user_corrected"` | Procedencia del registro |

- Inferencia estática: lecturas = `inputs` (fuentes), escrituras = `artifact` (FR-008); sin
  ejecutar código (US5.2).
- El usuario puede confirmar/corregir ⇒ `origin` cambia y se persiste (US5.3). Las
  correcciones del usuario **prevalecen** sobre re-inferencias en `scan`.

### 6. Anotación de decisión — `annotations.json`

El "por qué" de decisiones; texto libre + objetivo opcional.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `schema_version` | int | Requerido |
| `annotations` | lista de Anotación | — |

Objeto **Anotación**:

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | str | Identificador estable |
| `text` | str | Razonamiento (texto libre) |
| `target` | objeto/null | Objetivo opcional; `null` = nivel proyecto |
| `created_at` | str (ISO-8601) | Momento |

- **target**: `{ "type": "file"|"source"|"column", "ref": str }` (clarif.). `file`→ruta;
  `source`→`identity` de fuente; `column`→nombre (+ scope opcional). Ausente ⇒ proyecto
  (US3.1/US3.2).
- **Validación de `target.ref`**: igual que el `scope` anticipado del diccionario (sección
  3), `target.ref` NO requiere que la `identity`/ruta/columna referenciada exista ya en
  memoria al momento de crear la anotación. Se acepta como válida (con `warning` en
  `agent_log.jsonl` si no resuelve contra ningún elemento conocido); si nunca se
  materializa, queda huérfana (mismo tratamiento que en la sección "Relaciones": no se
  borra sin confirmación).

### 7. Registro de acción del agente — `agent_log.jsonl`

Trazabilidad append-only. Una línea JSON por evento.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `ts` | str (ISO-8601) | Momento |
| `level` | enum `"info"`/`"warning"`/`"error"` | Severidad |
| `action` | str | Qué hizo (p. ej. `scan`, `annotate`, `define_column`) |
| `why` | str | Motivo/contexto (qué y por qué — FR-012) |
| `detail` | objeto | Datos adicionales (p. ej. error, archivo afectado) |

- Append-only; nunca se reescribe (Principio VII). Incluye éxitos **y** avisos/errores.

### 8. Meta — `meta.json`

`{ "schema_version": int, "harness_version": str, "created_at": str, "project_root": str }`.
Ancla para el futuro índice multi-proyecto (FR-011).

---

## Relaciones

```text
Fuente.identity  ◄── Linaje.inputs[]            (qué fuentes alimentan un artefacto)
Fuente.identity  ◄── EntradaDic.scope (override) (significado por dataset)
Fuente.identity  ◄── Anotación.target.ref (source)
Mapa.entries[].path ◄── Anotación.target.ref (file), Linaje.artifact/producer
Commit           — independiente (historial git)
```

Integridad: las referencias por `identity`/`path` son **débiles** (no se borra en cascada).
Si un `scan` ya no encuentra una fuente/artefacto, la entrada de memoria del usuario
(diccionario, anotación, linaje corregido) **se conserva** y puede marcarse como "huérfana"
en la vista; nunca se elimina sin pasar por la barrera de seguridad (Principio III).

## Reglas de validación (derivadas de requisitos)

1. `sources.json`: `identity` única por catálogo; `status` presente solo si `kind=file` (FR-002).
2. `dictionary.json`: `(column, scope)` única; toda actualización añade a `history` (FR-005).
3. `changelog.json`: si `git_available=false`, `commits` vacío (FR-006).
4. `lineage.json`: registros con `origin=user_*` no se sobrescriben por re-inferencia (FR-008).
5. Toda escritura es atómica (temp + `os.replace`); ante JSON corrupto al leer ⇒
   `MemoryCorruptedError`, sin sobrescribir (FR-016, edge case).
6. Ninguna operación de memoria modifica archivos del proyecto del usuario (FR-004).
