# Contract — Memory JSON Schemas

Esquemas de los archivos JSON de `.ds_harness/` (fuente de verdad). Rutas y formas
**estables** para el futuro índice multi-proyecto (FR-011). Todos llevan `schema_version`.
Fechas en ISO-8601 UTC. Las rutas de archivo son **relativas al `project_root`** y
normalizadas (separador `/`).

## `meta.json`

```json
{
  "schema_version": 1,
  "harness_version": "0.1.0",
  "created_at": "2026-06-16T10:00:00Z",
  "project_root": "."
}
```

## `map.json`

```json
{
  "schema_version": 1,
  "scanned_at": "2026-06-16T10:00:00Z",
  "root": ".",
  "excluded_rules": [".gitignore", ".git/", ".ds_harness/"],
  "entries": [
    { "path": "src/train.py", "type": "file" },
    { "path": "data", "type": "dir" }
  ]
}
```

## `sources.json`

```json
{
  "schema_version": 1,
  "sources": [
    {
      "kind": "file",
      "identity": "data/raw/ventas.csv",
      "status": "located",
      "references": [
        { "code_file": "src/clean.py", "line": 12 },
        { "code_file": "notebooks/eda.ipynb", "line": null }
      ]
    },
    {
      "kind": "sql",
      "identity": "ventas.transacciones",
      "status": null,
      "references": [
        { "code_file": "sql/extract.sql", "line": 3 }
      ]
    }
  ]
}
```

Reglas: `identity` única; `status` ∈ {`located`,`not_located`} solo si `kind=file`, en otro
caso `null`. `references` agrega todas las apariciones.

## `dictionary.json`

```json
{
  "schema_version": 1,
  "entries": [
    {
      "column": "var_27",
      "scope": "global",
      "definition": "Días desde la última compra",
      "history": [
        { "definition": "Días desde la última compra", "changed_at": "2026-06-16T10:05:00Z" }
      ]
    },
    {
      "column": "var_27",
      "scope": "data/raw/ventas.csv",
      "definition": "Recencia en semanas (override para este dataset)",
      "history": [
        { "definition": "Recencia en semanas (override para este dataset)", "changed_at": "2026-06-16T10:06:00Z" }
      ]
    }
  ]
}
```

Reglas: clave `(column, scope)`; re-registrar la misma clave ⇒ nueva definición +
append a `history`. Resolución: override por fuente prevalece sobre `global`.

## `changelog.json`

```json
{
  "schema_version": 1,
  "git_available": true,
  "commits": [
    {
      "id": "a1b2c3d",
      "author": "Ana Dev",
      "date": "2026-06-15T18:30:00Z",
      "message": "Añade limpieza de ventas",
      "files": ["src/clean.py", "data/raw/ventas.csv"]
    }
  ]
}
```

Sin git: `{ "schema_version": 1, "git_available": false, "commits": [] }`.

## `lineage.json`

```json
{
  "schema_version": 1,
  "records": [
    {
      "artifact": "data/processed/ventas_clean.parquet",
      "producer": "src/clean.py",
      "inputs": ["data/raw/ventas.csv"],
      "origin": "inferred"
    }
  ]
}
```

Reglas: `origin` ∈ {`inferred`,`user_confirmed`,`user_corrected`}; los `user_*` no se
sobrescriben por re-inferencia.

## `annotations.json`

```json
{
  "schema_version": 1,
  "annotations": [
    {
      "id": "ann-0001",
      "text": "Descartamos var_99 por fuga de información temporal",
      "target": { "type": "column", "ref": "var_99" },
      "created_at": "2026-06-16T10:10:00Z"
    },
    {
      "id": "ann-0002",
      "text": "El proyecto prioriza recall sobre precisión por el caso de uso",
      "target": null,
      "created_at": "2026-06-16T10:11:00Z"
    }
  ]
}
```

`target.type` ∈ {`file`,`source`,`column`}; `null` = nivel proyecto.

## `agent_log.jsonl` (una línea JSON por evento)

```json
{"ts":"2026-06-16T10:00:00Z","level":"info","action":"scan","why":"Usuario ejecutó `scan`","detail":{"files":124,"sources":7}}
{"ts":"2026-06-16T10:00:01Z","level":"warning","action":"scan","why":"Fuente referenciada no localizada en disco","detail":{"identity":"data/raw/old.csv"}}
```

## Convenciones de evolución (FR-011)

- Cambios retro-compatibles (añadir campos opcionales) **no** suben `schema_version`.
- Cambios incompatibles suben `schema_version` y deben documentar una migración.
- Las rutas de archivo dentro de `.ds_harness/` son estables; un índice multi-proyecto
  podrá leer `meta.json` + cada entidad sin conocer la implementación del harness.
