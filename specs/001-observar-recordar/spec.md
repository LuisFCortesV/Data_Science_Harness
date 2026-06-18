# Feature Specification: Fase 1 — Base: Observar y Recordar

**Feature Branch**: `001-observar-recordar`

**Created**: 2026-06-16

**Status**: Draft

**Input**: User description: "Fase 1 del DS Harness — Base: Observar y Recordar. Capa fundacional que captura y persiste el contexto de un proyecto de ciencia de datos en una memoria local, trazable y consultable, con una barrera de seguridad operativa desde el día uno."

## Clarifications

### Session 2026-06-16

- Q: Linaje de artefactos: ¿cómo se determina la relación script/notebook → archivo
  generado → fuente? → A: Detección estática del código (lecturas = fuentes, escrituras
  = artefactos) con corrección/confirmación del usuario; el harness no ejecuta el código
  del usuario.
- Q: ¿Sobre qué tipos de archivo opera el análisis estático (detección de fuentes y
  linaje) en Fase 1? → A: Python (`.py`), notebooks (`.ipynb`) y SQL (`.sql`).
- Q: Bitácora de cambios vía git: ¿qué cambios registra? → A: Solo los commits del
  historial (cada commit = una entrada: autor, fecha, mensaje, archivos afectados); el
  estado sin commitear no genera entradas de bitácora.
- Q: Alcance del escaneo de estructura: ¿qué se excluye del mapa? → A: Lo ignorado por
  `.gitignore`, más exclusiones estándar (`.git/`, `.ds_harness/`).
- Q: Diccionario de datos: ¿el significado de una columna es global o por dataset? → A:
  Híbrido — definición global por defecto, con posibilidad de sobrescribir el significado
  por dataset/fuente.

### Session 2026-06-16 (segunda ronda)

- Q: Identidad de una fuente de datos: ¿cómo se deduplica si varios scripts referencian
  el mismo archivo? → A: Una entrada por ruta normalizada; múltiples referencias se
  agregan a la misma entrada (lista de dónde se referencia).
- Q: Anotación de decisión: ¿a qué "contexto" se asocia? → A: Texto libre + objetivo
  opcional — el usuario puede vincular la anotación a un elemento de la memoria (archivo,
  fuente, columna) o dejarla a nivel proyecto.
- Q: Identidad de las fuentes SQL: ¿ruta de archivo también? → A: No — para fuentes SQL
  la identidad es el nombre de tabla calificado (`esquema.tabla`); el estado
  `localizada/no localizada` aplica solo a fuentes basadas en archivo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escanear y persistir estructura y fuentes de datos (Priority: P1)

Como desarrollador de DS, al iniciar el harness en mi proyecto quiero que escanee la
estructura del proyecto y catalogue las fuentes de datos ya referenciadas en el código,
y que ese mapa quede persistido, para no perder de vista qué hay sin tener que
reconstruirlo mentalmente cada vez.

**Why this priority**: Es el cimiento de toda la memoria. Sin un mapa persistido de
estructura y fuentes, ninguna otra capacidad (linaje, diccionario, vista legible) tiene
de qué partir. Entrega valor por sí sola: un inventario consultable del proyecto.

**Independent Test**: Ejecutar el escaneo sobre un proyecto de DS de ejemplo y verificar
que se genera y persiste un mapa de la estructura y un catálogo de fuentes de datos
referenciadas en el código, sin que ningún archivo del proyecto haya sido modificado.

**Acceptance Scenarios**:

1. **Given** un proyecto de DS con scripts/notebooks que leen archivos de datos, **When**
   el usuario inicia el escaneo, **Then** el harness produce un mapa persistido de la
   estructura del proyecto y un catálogo de las fuentes de datos referenciadas en el
   código, sin alterar ningún archivo del proyecto.
2. **Given** un escaneo previo persistido, **When** cambia la estructura del proyecto
   (se añaden o quitan archivos) y el usuario vuelve a escanear, **Then** el mapa
   persistido se actualiza para reflejar el estado actual (mapa "vivo").
3. **Given** una fuente de datos no referenciada en ningún código del proyecto, **When**
   se ejecuta el escaneo, **Then** esa fuente NO aparece en el catálogo (solo se
   catalogan fuentes referenciadas).
4. **Given** dos archivos de código que referencian la misma fuente (la misma ruta de
   archivo, o la misma tabla calificada `esquema.tabla`), **When** se ejecuta el escaneo,
   **Then** el catálogo contiene una sola entrada para esa identidad con ambas
   referencias agregadas.

---

### User Story 2 - Barrera de seguridad ante acciones destructivas (Priority: P1)

Como desarrollador de DS, quiero la certeza de que ningún archivo de mi proyecto se
modifica, mueve o elimina sin que yo lo confirme explícitamente, una acción a la vez,
para poder confiar en el harness sin miedo a perder trabajo.

**Why this priority**: Es un requisito constitucional (Principio III) y condición de
confianza. La barrera debe existir y estar operativa desde Fase 1, aun cuando las
acciones que mueven/borran lleguen en Fase 2. Sin esta garantía, el usuario no puede
adoptar el harness con seguridad.

**Independent Test**: Simular cualquier operación que pretenda modificar, mover o
eliminar un archivo del proyecto y verificar que queda bloqueada hasta una confirmación
explícita del usuario, y que la confirmación aplica a esa sola acción (no a un lote).

**Acceptance Scenarios**:

1. **Given** el harness en ejecución, **When** se intenta una operación que modifica,
   mueve o elimina un archivo del proyecto, **Then** la operación queda bloqueada antes
   de ejecutarse y se solicita confirmación explícita del usuario.
2. **Given** una operación destructiva bloqueada, **When** el usuario confirma
   explícitamente, **Then** solo esa operación queda autorizada; una operación
   destructiva posterior vuelve a requerir confirmación (no hay aprobación por lotes).
3. **Given** una operación destructiva bloqueada, **When** el usuario no confirma o
   rechaza, **Then** la operación no se ejecuta y el estado del proyecto permanece
   intacto.
4. **Given** cualquier operación de solo lectura (escanear, leer), **When** se ejecuta,
   **Then** no requiere confirmación porque no altera archivos del proyecto.

---

### User Story 3 - Anotar el "por qué" de decisiones (Priority: P2)

Como desarrollador de DS, quiero anotar por qué tomé una decisión y que quede guardada,
asociada a su contexto y trazable, para no perder el razonamiento detrás de las
decisiones del proyecto.

**Why this priority**: Ataca la dilución del contexto (D1) y la falta de trazabilidad
de decisiones (D4). Aporta valor independiente: un registro consultable del "por qué".

**Independent Test**: Registrar una anotación de decisión con su contexto, cerrar y
reabrir el harness, y verificar que la anotación persiste y es consultable.

**Acceptance Scenarios**:

1. **Given** el harness en ejecución, **When** el usuario anota el porqué de una decisión
   y la vincula a un elemento concreto (archivo, fuente o columna), **Then** la anotación
   queda persistida y asociada a ese objetivo.
2. **Given** el harness en ejecución, **When** el usuario anota una decisión sin
   especificar objetivo, **Then** la anotación queda persistida a nivel de proyecto.
3. **Given** anotaciones persistidas, **When** el usuario reabre el harness en otra
   sesión, **Then** las anotaciones siguen disponibles y son consultables.

---

### User Story 4 - Diccionario de datos alimentado por el usuario (Priority: P2)

Como desarrollador de DS, quiero registrar el significado de una columna críptica (p. ej.
`var_27`) en un diccionario de datos que persista entre sesiones, para recuperar el
significado de features/columnas sin depender de mi memoria.

**Why this priority**: Ataca el significado perdido de columnas crípticas (D7). Es
independiente y de alto valor cotidiano, aunque depende del usuario para alimentarse.

**Independent Test**: Registrar la definición de una columna, reabrir el harness y
verificar que la definición persiste y se puede consultar.

**Acceptance Scenarios**:

1. **Given** el harness en ejecución, **When** el usuario registra el significado global
   de una columna/feature, **Then** la definición queda persistida en el diccionario de
   datos.
2. **Given** una definición ya registrada, **When** el usuario la actualiza, **Then** el
   diccionario refleja el nuevo significado conservando la trazabilidad del cambio.
3. **Given** una columna con definición global, **When** el usuario registra un
   significado distinto para esa columna en un dataset/fuente concreto, **Then** ese
   override coexiste con la definición global y prevalece al consultar esa fuente.
4. **Given** definiciones persistidas, **When** el usuario consulta el diccionario en una
   sesión posterior, **Then** las definiciones (globales y overrides) siguen disponibles.

---

### User Story 5 - Bitácora de cambios y linaje de artefactos (Priority: P2)

Como desarrollador de DS, quiero que el harness lleve automáticamente una bitácora de
los cambios del proyecto detectados vía git y registre el linaje de los artefactos de
datos (qué script/notebook generó qué archivo, a partir de qué fuente), para entender la
evolución y el origen de cada artefacto.

**Why this priority**: Ataca la falta de trazabilidad de cambios (D4) y el linaje
desconocido de artefactos (D6). Depende del escaneo base (US1) para tener artefactos y
fuentes que relacionar.

**Independent Test**: Sobre un proyecto con historial git y scripts que generan
archivos, verificar que la bitácora refleja los cambios detectados y que el linaje asocia
artefactos generados con su script/notebook de origen y su fuente.

**Acceptance Scenarios**:

1. **Given** un proyecto con control de versiones git, **When** se registran commits en
   el historial, **Then** el harness los detecta y crea una entrada de bitácora por
   commit (autor, fecha, mensaje, archivos afectados), sin registrar cambios sin
   commitear.
2. **Given** un script/notebook que lee una fuente y escribe un archivo, **When** el
   harness analiza estáticamente el código (sin ejecutarlo), **Then** infiere y registra
   la relación artefacto → script/notebook de origen → fuente.
3. **Given** un linaje inferido incorrecto o incompleto, **When** el usuario lo corrige o
   confirma, **Then** el harness persiste la relación corregida/confirmada.
4. **Given** un proyecto sin git inicializado, **When** el usuario inicia el harness,
   **Then** el harness informa que la bitácora automática no está disponible y continúa
   operando el resto de capacidades sin fallar.

---

### User Story 6 - Vista legible del estado capturado (Priority: P3)

Como desarrollador de DS, al volver al proyecto tras semanas, quiero leer una vista
legible para humanos del estado capturado (mapa, fuentes, bitácora, diccionario,
linaje), para retomar sabiendo en qué punto está sin recontextualizarme desde cero.

**Why this priority**: Ataca el costo de recontextualización (D8) a nivel de lectura del
estado capturado. Depende de que las capas anteriores hayan capturado información. Es la
"cara visible" de la memoria, pero no aporta valor hasta que hay algo que mostrar.

**Independent Test**: Con memoria ya poblada por las historias anteriores, generar la
vista legible y verificar que presenta de forma comprensible el mapa, las fuentes, la
bitácora, el diccionario y el linaje.

**Acceptance Scenarios**:

1. **Given** memoria del proyecto poblada, **When** el usuario solicita la vista legible,
   **Then** se presenta un documento legible para humanos que reúne mapa, fuentes,
   bitácora, diccionario y linaje.
2. **Given** que la memoria se actualiza, **When** el usuario regenera la vista, **Then**
   la vista refleja el estado capturado más reciente.
3. **Given** una sección de la memoria aún vacía (p. ej. diccionario sin entradas),
   **When** se genera la vista, **Then** la vista indica claramente que esa sección está
   vacía sin fallar.

---

### Edge Cases

- **Proyecto sin git**: la bitácora automática de cambios no puede operar; el harness lo
  informa y el resto de capacidades sigue funcionando (degradación elegante).
- **Proyecto vacío o sin fuentes referenciadas**: el escaneo produce un mapa válido y un
  catálogo de fuentes vacío, sin error.
- **Proyecto sin `.gitignore`**: el escaneo aplica solo las exclusiones estándar
  (`.git/`, `.ds_harness/`) y mapea el resto, sin error.
- **Fuente de archivo referenciada en código pero inexistente en disco**: se cataloga
  como referenciada y se marca como `no localizada`, sin fallar el escaneo. (El estado
  `localizada/no localizada` no aplica a fuentes SQL, que se catalogan por tabla
  calificada sin comprobación en disco.)
- **Acción destructiva sobre un archivo fuera del proyecto**: queda fuera del alcance de
  la barrera (la barrera protege archivos del proyecto); debe quedar claro qué se
  considera "del proyecto".
- **Fallo al leer/parsear un archivo durante el escaneo**: el escaneo registra el fallo
  de ese archivo y continúa con los demás (un fallo no tumba el proceso completo).
- **Memoria persistida corrupta o ilegible al reabrir**: el harness lo reporta de forma
  clara y accionable sin sobrescribir silenciosamente la memoria existente.
- **Definición de columna duplicada**: registrar una columna ya existente en el mismo
  alcance (global, o la misma fuente/dataset) se trata como actualización con
  trazabilidad, no como entrada duplicada; un mismo nombre en alcances distintos sí son
  entradas separadas (global vs. override por fuente).

## Requirements *(mandatory)*

### Functional Requirements

**Observar y mapear**

- **FR-001**: El sistema MUST escanear la estructura del proyecto y persistir un mapa de
  esa estructura que pueda actualizarse en escaneos posteriores (mapa vivo). El escaneo
  MUST excluir los archivos/carpetas ignorados por `.gitignore`, más exclusiones estándar
  (`.git/`, `.ds_harness/`).
- **FR-002**: El sistema MUST detectar y catalogar las fuentes de datos referenciadas en
  el código del proyecto, persistiendo el catálogo. El análisis estático opera sobre
  archivos Python (`.py`), notebooks (`.ipynb`) y SQL (`.sql`). La identidad de una fuente
  depende de su tipo: las fuentes **basadas en archivo** se identifican por su ruta
  normalizada (una entrada por ruta); las fuentes **SQL** se identifican por el nombre de
  tabla calificado (`esquema.tabla`). Cuando varios archivos de código referencian la
  misma fuente (misma ruta o misma tabla calificada), las referencias se agregan en la
  misma entrada. Esta detección opera sobre el contenido de los archivos de código,
  independientemente de si esos archivos —o las rutas que referencian— están excluidos del
  mapa de estructura (FR-001).
- **FR-003**: El sistema MUST NOT descubrir ni catalogar fuentes de datos externas no
  referenciadas en el código.
- **FR-004**: El sistema MUST NOT modificar, mover ni eliminar archivos del proyecto
  durante el escaneo o el mapeo (operaciones de solo observación).
- **FR-005**: Los usuarios MUST be able to mantener un diccionario de datos
  (columnas/features y su significado) que el usuario alimenta, persistido entre
  sesiones, soportando creación y actualización de entradas. El diccionario MUST soportar
  un modelo híbrido: una definición global por nombre de columna por defecto, con la
  posibilidad de sobrescribir ese significado por dataset/fuente; cuando exista un
  override para una fuente, prevalece sobre la definición global.

**Registrar y recordar**

- **FR-006**: El sistema MUST detectar automáticamente los cambios del proyecto mediante
  integración con git y registrarlos en una bitácora persistida. Cada commit del
  historial constituye una entrada de bitácora (autor, fecha, mensaje, archivos
  afectados); los cambios sin commitear del working tree NO generan entradas de bitácora.
- **FR-007**: El sistema MUST permitir al usuario anotar el "por qué" de decisiones como
  texto libre y persistirla. Cada anotación MUST poder asociarse opcionalmente a un
  elemento de la memoria (archivo del mapa, fuente de datos o columna del diccionario) o
  quedar a nivel de proyecto cuando no se especifica objetivo.
- **FR-008**: El sistema MUST registrar el linaje de artefactos de datos, asociando cada
  artefacto generado con el script/notebook que lo generó y la(s) fuente(s) de origen.
  El linaje se infiere mediante detección estática del código (lecturas de archivos =
  fuentes; escrituras de archivos = artefactos), sin ejecutar el código del usuario, y el
  usuario MUST poder corregir o confirmar las relaciones inferidas.
- **FR-009**: El sistema MUST generar una vista legible para humanos del estado capturado
  que reúna mapa, fuentes, bitácora, diccionario y linaje.

**Memoria, trazabilidad y seguridad**

- **FR-010**: El sistema MUST persistir la memoria del proyecto en una estructura
  predecible dentro del proyecto, usando JSON como fuente de verdad y generando la vista
  legible en Markdown derivada de ese JSON.
- **FR-011**: La estructura de memoria MUST quedar diseñada de forma que un índice
  central multi-proyecto pueda leerla en el futuro sin rediseño (esquemas y rutas
  estables y documentadas).
- **FR-012**: El sistema MUST registrar (log) las acciones del agente sobre el proyecto,
  incluyendo qué hizo y por qué, de forma consultable por el usuario en todo momento.
- **FR-013**: El sistema MUST bloquear cualquier operación que modifique, mueva o elimine
  archivos del proyecto hasta recibir confirmación explícita del usuario, mediante una
  validación previa a la ejecución.
- **FR-014**: La confirmación de una acción destructiva MUST aplicar únicamente a esa
  acción individual; el sistema MUST NOT autorizar acciones destructivas por lotes con
  una sola confirmación.
- **FR-015**: Ante una operación de clasificación ambigua sobre si es destructiva, el
  sistema MUST tratarla como destructiva y requerir confirmación (comportamiento
  fail-safe).
- **FR-016**: El sistema MUST manejar de forma explícita y específica los fallos de
  operaciones que puedan fallar (lectura/parseo de archivos, comandos de git, lectura de
  la memoria persistida), de modo que el fallo de una parte no deje la memoria ni el
  proyecto en estado inconsistente y produzca un mensaje claro y accionable.

**Límites de alcance (constitucionales)**

- **FR-017**: El sistema MUST NOT emitir conclusiones de modelado, de negocio o de
  análisis; en Fase 1 tampoco señala observaciones descriptivas computadas sobre los
  datos (diferido a Fase 2).
- **FR-018**: El sistema MUST NOT ejecutar reorganización del directorio ni mover/borrar
  archivos en Fase 1; en esta fase solo existe la barrera de seguridad, no la acción.

### Key Entities *(include if feature involves data)*

- **Mapa de estructura**: representación persistida de la organización del proyecto
  (carpetas y archivos relevantes) que se actualiza en cada escaneo.
- **Fuente de datos**: archivo o tabla de datos referenciado en el código. La identidad
  depende del tipo: fuentes **basadas en archivo** → **ruta normalizada**; fuentes
  **SQL** → **nombre de tabla calificado** (`esquema.tabla`). Atributos: tipo
  (archivo / SQL), identidad (ruta normalizada o tabla calificada según el tipo), lista de
  referencias (dónde —archivo/línea— se referencia, agregando múltiples scripts), y estado
  `localizada / no localizada` que aplica **solo a fuentes basadas en archivo**.
- **Entrada de diccionario de datos**: columna/feature con su significado; atributos:
  nombre de la columna, alcance (global o una fuente/dataset específico), definición e
  historial de cambios para trazabilidad. Una columna puede tener una entrada global y
  cero o más entradas override por fuente/dataset.
- **Entrada de bitácora**: commit del historial git; atributos: identificador del commit,
  autor, fecha, mensaje y archivos afectados.
- **Anotación de decisión**: el "por qué" de una decisión; atributos: texto del
  razonamiento, objetivo opcional (referencia a un archivo del mapa, una fuente de datos
  o una columna del diccionario; ausente = anotación a nivel de proyecto), momento.
- **Registro de linaje**: relación entre un artefacto generado, el script/notebook que lo
  generó y su(s) fuente(s) de origen.
- **Registro de acción del agente (log)**: acción ejecutada por el agente sobre el
  proyecto; atributos: qué acción, por qué, momento.
- **Memoria del proyecto**: contenedor persistente y predecible que agrupa las entidades
  anteriores como fuente de verdad y del que se deriva la vista legible.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un proyecto de DS de ejemplo, el usuario obtiene un mapa de estructura y
  un catálogo de fuentes referenciadas persistidos en una sola ejecución de escaneo, sin
  que ningún archivo del proyecto cambie (verificable comparando el proyecto antes y
  después: 0 archivos alterados).
- **SC-002**: El 100% de las operaciones que modifican, mueven o eliminan archivos del
  proyecto quedan bloqueadas hasta confirmación explícita, y cada confirmación autoriza
  exactamente una acción (0 acciones destructivas ejecutadas sin confirmación individual).
- **SC-003**: Toda la información capturada (mapa, fuentes, bitácora, diccionario,
  anotaciones, linaje) sigue disponible y consultable tras cerrar y reabrir el harness
  (persistencia verificable entre sesiones).
- **SC-004**: Tras semanas sin abrir el proyecto, el usuario puede leer la vista legible
  y reconstruir en qué punto está (qué hay, qué cambió, qué significan las columnas, de
  dónde viene cada artefacto) sin abrir el código, en una sola lectura.
- **SC-005**: En todo momento el usuario puede consultar el registro de qué hizo el
  agente y por qué (cobertura: el 100% de las acciones del agente sobre el proyecto
  quedan registradas).
- **SC-006**: El fallo de una parte (p. ej. un archivo ilegible, git no inicializado) no
  interrumpe el resto de capacidades ni deja la memoria en estado inconsistente; el
  usuario recibe un mensaje claro de qué pasó y qué puede hacer.

## Assumptions

- **Alcance "del proyecto"**: la barrera de seguridad y el escaneo operan sobre los
  archivos contenidos en el directorio del proyecto donde se inicializa el harness; los
  archivos fuera de ese directorio quedan fuera de su alcance.
- **Persistencia local**: la memoria se guarda localmente dentro del proyecto, en una
  carpeta dedicada del harness (`.ds_harness/`, según la constitución), con JSON como
  fuente de verdad y Markdown legible derivado.
- **Git disponible**: la bitácora automática de cambios asume un proyecto con git
  inicializado; sin git, esa capacidad se degrada con aviso y el resto sigue operando.
- **Fuentes "referenciadas en el código"**: se consideran referencias a datos las que
  aparecen explícitamente en archivos Python (`.py`), notebooks (`.ipynb`) y SQL
  (`.sql`) del proyecto; el descubrimiento de fuentes no referenciadas, y el análisis de
  otros lenguajes (p. ej. R), quedan fuera de alcance en Fase 1.
- **El diccionario lo alimenta el usuario**: el harness no infiere el significado de
  columnas; solo persiste y recupera lo que el usuario registra.
- **Confirmación explícita**: se asume un mecanismo interactivo por el cual el usuario
  aprueba o rechaza cada acción destructiva individualmente.
- **Compatibilidad futura**: la estructura de memoria se diseña pensando en un índice
  multi-proyecto futuro (Fase 3), pero ese índice no se construye en esta fase.
- **Sin capacidades activas de Fase 2**: recuperación/resumen inteligente, respuesta a
  preguntas, resumen narrativo de "dónde quedé" e insights descriptivos quedan fuera de
  esta fase.
