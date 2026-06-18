<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0
Tipo de cambio: MINOR — expansión material de la guía de un principio (Principio II) y
                de la Fase 2 del flujo de desarrollo. No se elimina ni redefine ningún
                principio existente.

Principios modificados:
  - II. El agente observa y recuerda; no decide por el usuario — se añade una
    distinción explícita entre salida PERMITIDA (observaciones descriptivas computadas
    sobre datos/metadatos ya capturados, presentadas como hallazgos) y salida PROHIBIDA
    (conclusiones analíticas, de modelado o de negocio, presentadas solo como opción).
    Se reemplaza la regla previa "no inventar conclusiones nuevas". "Razón de ser"
    conservada (ampliada para explicar la distinción).

Secciones modificadas:
  - Flujo de Desarrollo y Fases de Construcción, Fase 2 — se amplía el mandato para
    incluir "señalar observaciones y hallazgos descriptivos sobre los datos".

Principios sin cambios: I, III, IV, V, VI, VII, VIII, IX.
Secciones añadidas: ninguna.
Secciones eliminadas: ninguna.

Plantillas dependientes:
  ✅ .specify/templates/plan-template.md — "Constitution Check" es genérico
     ("Gates determined based on constitution file"); no requiere edición.
  ✅ .specify/templates/spec-template.md — sin referencias a principios; alineado.
  ✅ .specify/templates/tasks-template.md — sin referencias a principios; alineado.
  ✅ .specify/templates/checklist-template.md — sin referencias a principios; alineado.

TODOs diferidos: ninguno.
-->

# DS Harness Constitution

Harness en Python que actúa como **memoria persistente de proyectos de ciencia de
datos**: observa el contexto del proyecto, lo organiza, lo recupera y lo hace
trazable, sin sustituir el juicio analítico del usuario.

## Core Principles

### I. Construcción incremental por capas

El proyecto se construye en fases ordenadas: primero la **base** (observar y recordar
el contexto del proyecto), luego las **capacidades activas** que consumen esa memoria,
y por último las **extensiones pesadas**. Reglas:

- Cada capa MUST funcionar y ser verificable antes de iniciar la siguiente.
- Ninguna fase posterior MUST requerir rehacer una anterior; las capas se apilan, no
  se reemplazan.
- Una fase incompleta o no verificada NO autoriza comenzar la siguiente.

**Razón de ser**: construir por capas verificables reduce el riesgo de retrabajo y
garantiza que siempre exista una versión funcional. Evita el "big bang" donde nada
sirve hasta el final.

### II. El agente observa y recuerda; no decide por el usuario

El harness mantiene contexto, lo organiza y lo recupera. Su valor es la **memoria y la
trazabilidad**, no el juicio analítico. Reglas:

- El agente MUST NOT tomar decisiones de modelado, de negocio o de análisis por el
  usuario.
- Cuando el contexto sugiera una decisión, el agente la **presenta como opción**, no
  la ejecuta como conclusión.

La salida del agente se distingue en dos tipos:

- **PERMITIDO — Observaciones descriptivas**: el agente MAY computar y señalar
  observaciones descriptivas sobre los datos y metadatos ya capturados o escaneados
  (p. ej. % de nulos, cardinalidad, columnas posiblemente constantes, posibles archivos
  derivados de una misma fuente, candidatos a anomalía). Se presentan como
  **hallazgos/observaciones**, MUST NOT presentarse como conclusiones, y se computan
  únicamente sobre lo que ya está en la memoria del proyecto.
- **PROHIBIDO — Conclusiones analíticas**: el agente MUST NOT emitir conclusiones de
  modelado, de negocio o de análisis (p. ej. "elimina esta feature", "esta es la más
  predictiva", "el modelo sobreajustará"). Cuando el contexto las sugiera, el agente las
  **presenta como opción**, nunca como conclusión; la decisión sigue siendo del usuario.

**Razón de ser**: la confianza en una herramienta de memoria depende de que no
contamine el trabajo con opiniones propias. El usuario sigue siendo el analista. La
distinción entre describir lo que los datos ya muestran y juzgar qué hacer con ellos
preserva ese espíritu mientras habilita hallazgos descriptivos útiles.

### III. Seguridad ante acciones destructivas

Ninguna acción que modifique, mueva o elimine archivos del proyecto se ejecuta sin
confirmación explícita del usuario, paso a paso. Reglas:

- Toda operación sobre el sistema de archivos MUST pasar por un hook de validación
  previo (pre-tool-use) que bloquee operaciones destructivas no aprobadas.
- La confirmación MUST ser explícita y por cada acción; una aprobación no se extiende
  a acciones futuras ni a lotes.
- Ante la duda sobre si una operación es destructiva, el hook MUST bloquear y pedir
  confirmación (fail-safe).

**Razón de ser**: una memoria de proyecto que pueda borrar trabajo real es un riesgo
inaceptable. La barrera de confirmación protege el activo más valioso del usuario.

### IV. Memoria persistente, estructurada y portable

El contexto del proyecto se guarda en una estructura predecible dentro del proyecto, en
la carpeta `.ds_harness/`. Reglas:

- Formato dual: **JSON como fuente de verdad** para el agente; **Markdown legible**
  generado para el usuario.
- El Markdown se deriva del JSON; el JSON nunca se deriva del Markdown.
- La estructura MUST permitir que un índice central multi-proyecto la lea en el futuro
  sin rediseño (esquemas y rutas estables y documentadas).

**Razón de ser**: separar la fuente de verdad (máquina) de la vista (humano) evita
ambigüedad y permite crecer hacia un índice multi-proyecto sin romper lo existente.

### V. Llamadas directas al SDK, sin frameworks pesados

El harness usa llamadas directas al SDK del modelo. Reglas:

- MUST NOT depender de frameworks de orquestación de agentes (LangChain o similares).
- El loop de agente, el sistema de tools y los hooks se implementan y controlan
  directamente en el código del proyecto.
- Cada dependencia externa MUST justificarse individualmente antes de añadirse.

**Razón de ser**: el objetivo del proyecto es **entender y controlar cada parte de la
arquitectura**. Los frameworks pesados ocultan ese control y dificultan el aprendizaje
y la depuración.

### VI. Modularidad y tools con contrato claro

Cada herramienta (tool) tiene un contrato explícito y el código está modularizado.
Reglas:

- Cada tool MUST documentar un schema con nombre, descripción y parámetros explícitos.
- El código se organiza en módulos separados (tools, hooks, loop, memoria) a medida que
  crece; MUST NOT consolidarse en un único archivo monolítico.
- Un cambio en el contrato de una tool MUST reflejarse en su schema documentado.

**Razón de ser**: contratos claros hacen las tools predecibles para el modelo y para el
desarrollador, y la separación en módulos mantiene el sistema mantenible al crecer.

### VII. Trazabilidad y observabilidad

Las acciones del agente sobre el proyecto quedan registradas y son consultables.
Reglas:

- Las acciones del agente sobre el proyecto MUST registrarse (logging).
- Los cambios en el proyecto SHOULD detectarse mediante integración con git.
- El usuario MUST poder consultar en todo momento qué hizo el agente y por qué.

**Razón de ser**: una memoria sin auditoría no es confiable. La trazabilidad permite
revisar, revertir y entender el comportamiento del agente.

### VIII. Simplicidad del código

Se prefiere la solución más simple que resuelva el problema presente. Reglas:

- MUST NOT introducirse abstracciones prematuras, capas de indirección innecesarias ni
  "ingeniería para el futuro" sin una necesidad presente que la justifique.
- El código MUST poder leerse sin esfuerzo: nombres claros, funciones cortas con una
  sola responsabilidad, y preferencia por lo explícito sobre lo implícito.
- Si una solución requiere un comentario para explicar por qué es complicada, primero
  MUST evaluarse si puede ser más simple.

**Razón de ser**: la simplicidad es la base de la mantenibilidad y del aprendizaje. La
complejidad no justificada es deuda técnica disfrazada.

### IX. Manejo de errores claro y explícito

Ninguna operación que pueda fallar se deja sin manejo de error. Reglas:

- Toda operación con riesgo de fallo (llamadas a la API, lectura/escritura de archivos,
  parseo de datos, comandos de git) MUST capturar errores de forma **específica**, no
  genérica.
- Los mensajes de error MUST ser claros y accionables, tanto para el usuario como para
  el agente cuando recibe el resultado de una tool.
- El fallo de una parte (p. ej. la API no responde) MUST NOT tumbar todo el programa ni
  dejarlo en un estado inconsistente.
- Los errores recuperables SHOULD reintentarse de forma controlada; los no recuperables
  MUST reportarse explicando qué pasó y qué se puede hacer.

**Razón de ser**: un harness de memoria debe ser robusto. Errores silenciosos o
genéricos corrompen la confianza en el estado del proyecto y son difíciles de depurar.

## Restricciones Técnicas y de Arquitectura

- **Lenguaje**: Python.
- **Persistencia**: carpeta `.ds_harness/` dentro del proyecto; JSON como fuente de
  verdad, Markdown derivado para lectura humana.
- **Integración con SDK**: llamadas directas al SDK del modelo; sin frameworks de
  orquestación (ver Principio V).
- **Componentes nucleares**: loop de agente, sistema de tools, hooks (incluido el
  pre-tool-use de validación destructiva) y módulo de memoria, separados en módulos.
- **Integración con git**: usada para detectar cambios en el proyecto (Principio VII).
- **Dependencias externas**: se añaden una por una, con justificación explícita.

## Flujo de Desarrollo y Fases de Construcción

El desarrollo sigue las capas del Principio I:

1. **Base — Observar y recordar**: capturar y persistir el contexto del proyecto en
   `.ds_harness/` (JSON + Markdown), con logging y hook de seguridad operativos.
2. **Capacidades activas**: tools que consumen la memoria para recuperar, resumir y
   responder sobre el contexto del proyecto, y para **señalar observaciones y hallazgos
   descriptivos sobre los datos** (en los términos permitidos por el Principio II).
3. **Extensiones pesadas**: integraciones adicionales (p. ej. índice multi-proyecto)
   construidas sobre las capas anteriores sin rediseñarlas.

Cada fase se cierra solo cuando es funcional y verificable. La planificación
(`/speckit-plan`) y las tareas (`/speckit-tasks`) MUST respetar este orden y la
verificación de la capa previa.

## Governance

- Esta constitución **supersede** cualquier otra práctica del proyecto. Ante conflicto,
  prevalecen estos principios.
- **Enmiendas**: toda modificación MUST documentarse en este archivo, incluir su
  justificación y actualizar la versión y las fechas. Las plantillas dependientes
  (`plan-template.md`, `spec-template.md`, `tasks-template.md`) MUST revisarse para
  mantener la consistencia.
- **Versionado** (semántico):
  - **MAJOR**: cambios incompatibles — eliminación o redefinición de principios o de
    reglas de gobernanza.
  - **MINOR**: adición de un principio/sección o expansión material de una guía.
  - **PATCH**: aclaraciones, redacción, correcciones no semánticas.
- **Cumplimiento**: todo plan, spec y revisión MUST verificar conformidad con estos
  principios. Las violaciones se documentan y justifican (p. ej. en la tabla
  "Complexity Tracking" del plan) o se corrigen antes de avanzar.

**Version**: 1.1.0 | **Ratified**: 2026-06-16 | **Last Amended**: 2026-06-16
