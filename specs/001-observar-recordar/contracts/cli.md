# Contract — CLI Commands

Punto de entrada `ds_harness` (módulo `cli.py`). Interfaz **híbrida**: subcomandos
deterministas (sin LLM) + modo `chat` (con LLM). Salidas a stdout legibles; errores a
stderr con mensaje accionable (Principio IX). Código de salida `0` éxito, `≠0` fallo.

Convención: todos operan sobre el **proyecto actual** (cwd) salvo `--path`. Ninguno
modifica archivos del proyecto del usuario (FR-004); solo escriben dentro de `.ds_harness/`.

---

## `ds_harness init`

- **Propósito**: Inicializa `.ds_harness/` en el proyecto y dispara el primer escaneo.
- **LLM**: no.
- **Opciones**: `--path <dir>` (raíz del proyecto; defecto cwd).
- **Efecto**: crea `.ds_harness/` con `meta.json` y archivos de entidad vacíos
  (`schema_version` inicializado), luego ejecuta el flujo de `scan`. Idempotente: si ya
  existe, no sobrescribe la memoria; informa y sugiere `scan`.
- **Salida**: resumen (archivos mapeados, fuentes detectadas, git disponible sí/no).
- **Errores**: sin permisos de escritura ⇒ mensaje accionable; `.ds_harness/` corrupto ⇒
  `MemoryCorruptedError` sin sobrescribir.

## `ds_harness scan`

- **Propósito**: Re-ejecuta escaneo de estructura (FR-001) y fuentes (FR-002), reconstruye
  bitácora (FR-006) y re-infiere linaje (FR-008) preservando correcciones del usuario.
- **LLM**: no (100% determinista).
- **Opciones**: `--path <dir>`.
- **Efecto**: actualiza `map.json`, `sources.json`, `changelog.json`, `lineage.json`
  (atómico). No toca `dictionary.json` ni `annotations.json` (los alimenta el usuario).
- **Salida**: diff resumido (p. ej. "+3 archivos, +1 fuente, 12 commits, 2 linajes
  inferidos").
- **Degradación**: sin git ⇒ aviso y `git_available=false`; archivo no parseable ⇒ se
  registra `FileParseError` para ese archivo y continúa (edge cases).

## `ds_harness status`

- **Propósito**: Regenera y muestra la vista legible del estado capturado (FR-009).
- **LLM**: no.
- **Opciones**: `--path <dir>`, `--no-open` (solo regenerar, sin imprimir).
- **Efecto**: regenera `views/status.md` desde los JSON y lo imprime. Secciones vacías se
  indican explícitamente (US6.3).
- **Errores**: memoria ausente ⇒ sugiere `init`; JSON corrupto ⇒ `MemoryCorruptedError`.

## `ds_harness chat`

- **Propósito**: Modo conversacional para anotar decisiones, definir columnas del
  diccionario y confirmar/corregir linaje, interpretando lenguaje natural (Principios II/V).
- **LLM**: sí (`google-genai`, `gemini-2.5-flash`).
- **Requisitos**: variable de entorno `GEMINI_API_KEY`. Sin ella ⇒ mensaje accionable y
  salida `≠0` (no entra al modo).
- **Tools disponibles**: `annotate_decision`, `define_column`, `confirm_lineage`,
  `query_memory` (ver `contracts/tools.md`).
- **Comportamiento**: el modelo propone una tool; el harness valida → dispatcher/hook →
  ejecuta → registra en `agent_log.jsonl`. En Fase 1 ninguna tool es destructiva sobre el
  proyecto, así que el hook no bloquea; queda operativo para Fase 2.
- **Límite (FR-017)**: el agente NO emite conclusiones de modelado/negocio ni observaciones
  descriptivas; solo captura y recupera.
- **Errores LLM**: reintento con backoff (2–3) ante fallo transitorio; agotado ⇒ `LLMError`
  con mensaje accionable, sesión continúa o cierra limpiamente.

---

## Comportamiento transversal

- **Logging**: toda invocación registra inicio/fin y avisos en `agent_log.jsonl` (FR-012).
- **Consulta de trazabilidad**: el usuario puede leer `agent_log.jsonl` directamente; la
  vista `status.md` referencia las últimas acciones.
- **Seguridad**: cualquier futura tool/comando que pretenda modificar archivos del proyecto
  pasará por el hook pre-tool-use; en Fase 1 no existen (FR-018).
