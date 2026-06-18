<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/001-observar-recordar/plan.md` (Fase 1 — Base: Observar y Recordar).

Tech stack: Python 3.11+, `google-genai` (modelo `gemini-2.5-flash`, SDK directo, sin
frameworks), `pathspec` (.gitignore), `sqlglot` (SQL), `pytest`. Memoria persistida en
`.ds_harness/` (JSON por entidad = fuente de verdad; Markdown derivado). Módulos:
memory, scanner, lineage, git_log, hooks (pre-tool-use), tools, agent_loop, errors, cli.
Operaciones deterministas (scan/status/init) sin LLM; solo `chat` usa el modelo.
<!-- SPECKIT END -->
