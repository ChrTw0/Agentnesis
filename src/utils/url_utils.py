"""
URL Utils - Filtrado y normalización de URLs.

Portado desde TradingAgent. Sin dependencias internas.
"""

from __future__ import annotations

from urllib.parse import urlparse

# Dominios bloqueados siempre (redes sociales, trackers, redirects)
BLOCKED_DOMAINS: frozenset[str] = frozenset({
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "reddit.com",
    "t.co",
    "bit.ly",
    "tinyurl.com",
})


def normalize_url(url: str) -> str:
    """Elimina fragmentos y parámetros de tracking comunes."""
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


def extract_domain(url: str) -> str:
    """Devuelve el dominio base sin 'www.'"""
    host = urlparse(url).netloc.lower()
    return host.removeprefix("www.")


def is_blocked(url: str) -> bool:
    """True si el dominio está explícitamente bloqueado."""
    domain = extract_domain(url)
    return any(domain == d or domain.endswith(f".{d}") for d in BLOCKED_DOMAINS)


def filter_urls(urls: list[str]) -> list[str]:
    """Filtra una lista de URLs eliminando dominios bloqueados y normalizando."""
    return [normalize_url(url) for url in urls if not is_blocked(url)]


__all__ = ["normalize_url", "extract_domain", "is_blocked", "filter_urls", "BLOCKED_DOMAINS"]
