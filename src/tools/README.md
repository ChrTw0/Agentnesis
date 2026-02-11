# Tools Module (Phase 2)

This directory will contain external tool implementations for agent execution.

## Planned Tools

### Web & Research
- `web_search.py` - Web search integration (Tavily, SerpAPI, DuckDuckGo)
- `web_scraper.py` - Structured web scraping (BeautifulSoup, Playwright)
- `pdf_parser.py` - PDF text extraction and parsing

### Code Execution
- `python_repl.py` - Python REPL for code execution
- `sandbox.py` - Sandboxed execution environment (Docker, E2B)

### File Operations
- `file_operations.py` - File read/write/manipulation tools

## Implementation Status

**Current (v0.1.0):** No external tools - agents use LLM knowledge only

**Next (v0.2.0):** Tool integration with dynamic binding per agent role

## Architecture Notes

Tools will be:
1. Assigned to agents at spawn time based on role (not global pool)
2. Isolated per agent via LangChain tool binding
3. Validated by Integrator when used in proposals

See `docs/ARQUITECTURA_STATES_CORREGIDA.md` Section 11.5 for details.
