"""
Scraper - Extracción de contenido web via Scrapling.

Portado desde TradingAgent. Sin dependencias internas.

Modos:
    simple   → AsyncFetcher: HTTP curl_cffi, TLS spoofing, ultra rápido.
    stealthy → StealthyFetcher: Camoufox stealth Chromium, Cloudflare bypass.
    dynamic  → DynamicFetcher: Playwright Chromium, sitios JS-heavy.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from scrapling import AsyncFetcher, StealthyFetcher, DynamicFetcher

logger = logging.getLogger(__name__)

FetcherMode = Literal["simple", "stealthy", "dynamic"]


async def scrape_article(url: str, mode: FetcherMode = "simple") -> str:
    """Extrae el texto limpio de un artículo web dado su URL.

    Args:
        url:  URL del artículo a extraer.
        mode: Modo de scraping (simple | stealthy | dynamic).

    Returns:
        Texto limpio del artículo, o string vacío si falla.
    """
    try:
        if mode == "simple":
            page = await AsyncFetcher.get(url, stealthy_headers=True, follow_redirects=True)
        elif mode == "stealthy":
            page = await StealthyFetcher.async_fetch(url, headless=True, disable_resources=True)
        else:
            page = await DynamicFetcher.async_fetch(url, headless=True, disable_resources=True)

        text = page.get_all_text(
            ignore_tags=("script", "style", "nav", "footer", "header"),
            strip=True
        )
        logger.debug("Scraped %s — %d chars", url, len(text))
        return text

    except Exception as e:
        logger.warning("Scrape failed [%s] %s: %s", mode, url, e)
        return ""


async def scrape_batch(
    urls: list[str],
    mode: FetcherMode = "simple",
    max_concurrent: int = 5,
) -> list[str]:
    """Extrae artículos en paralelo con límite de concurrencia.

    Args:
        urls:           Lista de URLs a extraer.
        mode:           Modo de scraping para todas las URLs.
        max_concurrent: Máximo de requests simultáneos.

    Returns:
        Lista de textos en el mismo orden que las URLs.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _fetch(url: str) -> str:
        async with semaphore:
            return await scrape_article(url, mode)

    return await asyncio.gather(*[_fetch(url) for url in urls])


__all__ = ["scrape_article", "scrape_batch", "FetcherMode"]
