"""
SearXNG Client - Búsqueda web via instancia self-hosted.

Portado desde TradingAgent. Dependencias internas:
- src.utils.retry (async_retry)
- src.utils.url_utils (filter_urls)
- src.config.settings (SEARXNG_URL)
"""

from __future__ import annotations

import logging

import aiohttp

from src.config.settings import settings
from src.utils.retry import async_retry
from src.utils.url_utils import filter_urls

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    if not settings.tools.searxng_url:
        raise RuntimeError("SEARXNG_URL not configured. Add it to your .env file.")
    return settings.tools.searxng_url


@async_retry(max_attempts=3, delay_seconds=1.0)
async def search(
    query: str,
    max_results: int = 10,
    engines: list[str] | None = None,
    time_range: str = "week",
    categories: str = "general",
) -> list[dict]:
    """Busca información en SearXNG self-hosted.

    Args:
        query:        Término de búsqueda.
        max_results:  Número máximo de resultados a devolver.
        engines:      Lista de motores específicos (None = usa defaults).
        time_range:   Rango temporal: "day" | "week" | "month" | "year".
        categories:   Categorías SearXNG: "general" | "news" | "news,general".

    Returns:
        Lista de dicts con keys: title, url, content, engine.
    """
    _default_engines = ["bing", "duckduckgo", "brave"]

    params: dict = {
        "q": query,
        "format": "json",
        "language": "en",
        "time_range": time_range,
        "categories": categories,
        "engines": ",".join(engines if engines else _default_engines),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{_get_base_url()}/search",
            params=params,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

    results = data.get("results", [])

    filtered = []
    for r in results:
        url = r.get("url", "")
        urls_ok = filter_urls([url])
        if urls_ok:
            filtered.append({
                "title": r.get("title", ""),
                "url": urls_ok[0],
                "content": r.get("content", ""),
                "engine": r.get("engine", ""),
            })

    logger.debug("SearXNG: query=%r → %d/%d results kept", query, len(filtered), len(results))
    return filtered[:max_results]


__all__ = ["search"]
