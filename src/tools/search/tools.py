"""
LangChain Tool Wrappers - Wrappers @tool para search y scrape.

Expone las funciones de infraestructura como tools LangChain
para que el LLM pueda invocarlas via tool calling.
"""

from __future__ import annotations

from langchain_core.tools import tool

from src.tools.search.searxng import search
from src.tools.search.scraper import scrape_article


@tool
async def web_search(
    query: str,
    max_results: int = 5,
    time_range: str = "week",
) -> list[dict]:
    """Search for real-world information using SearXNG.

    Use this tool when you need current information not available in the
    Knowledge Graph: recent events, news, data, regulations, prices, etc.

    Args:
        query:       Search query in English.
        max_results: Maximum number of results to return (default 5).
        time_range:  Time range for results:
                     - "day"   → last 24 hours (breaking news, today's events)
                     - "week"  → last week (default, balance of freshness and volume)
                     - "month" → last month (recent historical context)
                     - "year"  → last year (broader context)

    Returns:
        List of results with keys: title, url, content, engine.
    """
    return await search(query=query, max_results=max_results, time_range=time_range)


@tool
async def scrape_article_tool(url: str, mode: str = "simple") -> str:
    """Extract the full text content from a web article given its URL.

    Use this tool after web_search to get the complete content of the
    most relevant articles (search results only return snippets).

    Args:
        url:  URL of the article to extract.
        mode: Scraping mode:
              - "simple"   → standard sites (fast, default)
              - "stealthy" → sites with anti-bot / Cloudflare protection
              - "dynamic"  → JavaScript-heavy sites (SPA, React, etc.)

    Returns:
        Clean text content of the article, or empty string if failed.
    """
    return await scrape_article(url=url, mode=mode)  # type: ignore[arg-type]


__all__ = ["web_search", "scrape_article_tool"]
