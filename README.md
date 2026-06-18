# DS Harness

  > Memoria persistente y trazable para proyectos de ciencia de datos.

  DS Harness es una herramienta CLI que observa tu proyecto de DS y recuerda su contexto: estructura de archivos,
  fuentes de datos, linaje de artefactos y decisiones de modelado. Todo guardado localmente en `.ds_harness/`.

  El modo conversacional usa **Gemini 2.5 Flash** para anotar decisiones, definir columnas y corregir linaje en lenguaje
  natural.

  ---

  ## Instalación

  ```bash
  pip install -e .

  Uso

  ds_harness init      # inicializa la memoria en tu proyecto
  ds_harness scan      # re-escanea estructura, fuentes y linaje
  ds_harness status    # muestra el estado actual del proyecto
  ds_harness chat      # anota decisiones en lenguaje natural

  Requisitos

  - Python 3.11+
  - Variable de entorno GEMINI_API_KEY (solo para el modo chat)
