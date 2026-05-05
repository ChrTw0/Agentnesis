"""
Retry - Decorador async con reintentos y backoff exponencial.

Portado desde TradingAgent. Sin dependencias internas.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Callable, Type

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorador async con reintentos y backoff exponencial.

    Args:
        max_attempts:   Número máximo de intentos (incluye el primero).
        delay_seconds:  Espera inicial entre reintentos.
        backoff_factor: Multiplicador del delay en cada reintento.
        exceptions:     Excepciones que disparan el reintento.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = delay_seconds
            last_exc: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    logger.warning(
                        "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                        func.__name__, attempt, max_attempts, exc, delay,
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            logger.error("%s failed after %d attempts: %s", func.__name__, max_attempts, last_exc)
            raise last_exc  # type: ignore[misc]

        return wrapper
    return decorator


__all__ = ["async_retry"]
