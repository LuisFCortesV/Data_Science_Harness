Herramienta CLI que actúa como memoria persistente y trazable para proyectos de ciencia de datos.

  Observa la estructura del proyecto, detecta fuentes de datos y linaje automáticamente, y permite anotar decisiones y
  definir columnas mediante lenguaje natural (Gemini 2.5 Flash).

  ## Instalación

  pip install -e .

  ## Uso

  ds_harness init    # inicializa la memoria en el proyecto
  ds_harness scan    # re-escanea estructura, fuentes y linaje
  ds_harness status  # muestra el estado actual
  ds_harness chat    # modo conversacional para anotar contexto
