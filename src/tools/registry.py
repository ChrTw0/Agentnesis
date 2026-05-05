"""
Tool Registry - Mapa centralizado de nombre → instancia tool.

Responsabilidad única: resolver nombres de tools (strings del AgentProfile)
a instancias LangChain invocables.

Uso:
    from src.tools.registry import get_tools
    tools = get_tools(["web_search", "scrape_article"])
"""

from __future__ import annotations

import logging
from langchain_core.tools import BaseTool

from src.tools.search.tools import web_search, scrape_article_tool

logger = logging.getLogger(__name__)

# Registro global: nombre → instancia tool
TOOL_REGISTRY: dict[str, BaseTool] = {
    "web_search": web_search,
    "scrape_article": scrape_article_tool,
}


def get_tools(names: list[str]) -> list[BaseTool]:
    """Resuelve una lista de nombres a instancias tool LangChain.

    Nombres desconocidos se ignoran con un warning (no fallan).

    Args:
        names: Lista de nombres de tools del AgentProfile.tools

    Returns:
        Lista de instancias BaseTool listas para tool calling.
    """
    resolved = []
    for name in names:
        tool = TOOL_REGISTRY.get(name)
        if tool is None:
            logger.warning("Tool '%s' not found in registry — skipping", name)
        else:
            resolved.append(tool)
    return resolved


__all__ = ["TOOL_REGISTRY", "get_tools"]
