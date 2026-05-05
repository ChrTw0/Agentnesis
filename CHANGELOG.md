# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.2.0] - 2026-05-04

### Added

- **Sistema de Tools externas** (`src/tools/`):
  - `registry.py` — registro centralizado `name → BaseTool` con `get_tools()` para resolver nombres a instancias LangChain.
  - `search/tools.py` — tools `web_search` y `scrape_article_tool` basadas en SearXNG + Scrapling.
  - `search/searxng.py` — cliente async para SearXNG (búsqueda web local, sin APIs de pago).
  - `search/scraper.py` — scraper async con Scrapling para extraer contenido de páginas web.
  - Activación controlada por `TOOLS_ENABLED=false` (deshabilitado por defecto). Requiere SearXNG corriendo localmente.

- **`invoke_llm_with_tools()`** en `src/utils/llm_invoker.py`:
  - Ciclo completo de tool calling: `bind_tools` → ejecuta tool calls → repite hasta respuesta final.
  - Soporte para tools async (`ainvoke`) con compatibilidad de event loop.

- **`get_temporal_anchor()`** en `src/utils/helpers.py`:
  - Inyecta bloque `[TEMPORAL ANCHOR]` en prompts para evitar alucinaciones de fecha basadas en el knowledge cutoff del LLM.
  - Usado en Genesis (domain analysis) y UniversalWorker (KG context).

- **`format_tools_for_prompt()`** en `src/utils/helpers.py`:
  - Formatea lista de tools disponibles para inyección en el prompt del Executor.

- **`ToolsConfig`** en `src/config/settings.py`:
  - Nuevas variables `TOOLS_ENABLED` y `SEARXNG_URL` en `.env.example`.

- **`assign_tools_for_role()`** en `GenesisChains` (`src/specialists/genesis/chains.py`):
  - Chain LLM que decide qué tools necesita un rol spawneado dinámicamente (usado en spawns mid-execution desde `SpawnRequest`).

- **`src/utils/retry.py`** — lógica de reintentos con backoff exponencial.
- **`src/utils/url_utils.py`** — utilidades de normalización y validación de URLs.

### Changed

- **`UniversalWorkerAgent`** (`src/specialists/universal_worker/agent.py`):
  - Resuelve tools del `AgentProfile` contra el registry antes de invocar el subgrafo fractal.
  - Agentes con tools reciben un subgrafo fresco (no cacheado) con sus tools inyectadas.
  - Inyecta `temporal_anchor` en el KG context antes de cada ejecución.

- **`compile_fractal_subgraph` / `create_fractal_subgraph`** (`src/specialists/fractal_agent/subgraph.py`):
  - Acepta parámetro opcional `tools: List[BaseTool]` y lo propaga a `FractalAgentChains`.

- **`main_graph.py`** (`src/core/main_graph.py`):
  - Genesis asigna `tools_per_role` a cada `AgentProfile` en la creación inicial.
  - Spawns dinámicos (desde `SpawnRequest`) llaman a `assign_tools_for_role()` antes de crear el perfil.

- **Prompts reescritos** para reducir sesgo y mejorar precisión:
  - `fractal_agent/prompts/planner.txt`, `executor.txt`, `critic.txt`
  - `genesis/task_domain_analysis.txt` (añade `tools_per_role` al schema de salida)
  - `genesis/task_spawn_decision.txt`
  - `universal_worker/task_execute_work.txt` y `system_prompt.txt`
  - `integrator/task_validate_proposal.txt` y `system_prompt.txt`
  - `moderator/task_detect_deadlock.txt`
  - `synthesizer/task_synthesize.txt`

- **`pyproject.toml`**: añadidas dependencias `aiohttp>=3.9.0` y `scrapling[all]>=0.2.9`.

---

## [0.1.0] - 2026-03-25

### Added

- Lanzamiento inicial — Agentnesis v0.1.0.
- Genesis: análisis de dominio y generación dinámica de agentes especializados.
- Arquitectura fractal: ciclo Planificar → Ejecutar → Criticar por agente (DeepAgent).
- Knowledge Graph con validación de conflictos por el Integrador.
- Moderador: orquestación de turnos y detección de deadlocks.
- Sintetizador: consolidación de la respuesta final.
- Licencia Apache 2.0.
