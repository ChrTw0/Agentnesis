"""
LLM Factory - Instancia LLMs según configuración.

Soporta OpenAI y OpenRouter (compatible con OpenAI SDK).
Permite testing con cualquier modelo vía OpenRouter.

Uso:
    from src.config.llm_factory import get_llm
    llm = get_llm()  # Usa settings global
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from os import getenv
from dotenv import load_dotenv

from src.config.settings import settings

# Cargar .env
load_dotenv()


class LLMFactory:
    """
    Factory para instanciar LLMs con configuración validada.

    Centraliza la creación de LLMs. Soporta:
    - OpenAI directo (GPT-4, GPT-3.5, etc.)
    - OpenRouter (Claude, Gemini, Llama, etc. vía API compatible OpenAI)
    """

    @staticmethod
    def create_openai(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        use_openrouter: bool = False
    ) -> ChatOpenAI:
        """
        Crea instancia de ChatOpenAI (directo u OpenRouter).

        Args:
            model: Nombre del modelo (default: desde settings)
            temperature: Temperatura (default: desde settings)
            max_tokens: Max tokens (default: desde settings)
            api_key: API key (default: desde .env según use_openrouter)
            base_url: Base URL (default: OpenAI o OpenRouter según flag)
            use_openrouter: Si True, usa OpenRouter; si False, OpenAI directo

        Returns:
            ChatOpenAI configurado

        Raises:
            ValueError: Si API key no está configurada
        """
        # Determinar API key y base URL según provider
        if use_openrouter:
            api_key = api_key or getenv("OPENROUTER_API_KEY")
            base_url = base_url or "https://openrouter.ai/api/v1"
            if not api_key:
                raise ValueError(
                    "OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env"
                )
        else:
            api_key = api_key or settings.llm.openai_api_key
            if not api_key:
                raise ValueError(
                    "OpenAI API key not configured. Set OPENAI_API_KEY in .env"
                )

        # Configuración común
        config = {
            "model": model or settings.llm.openai_model,
            "temperature": temperature if temperature is not None else settings.llm.llm_temperature,
            "max_tokens": max_tokens or settings.llm.llm_max_tokens,
            "api_key": api_key
        }

        # Si usa OpenRouter, agregar base_url y headers
        if use_openrouter:
            config["base_url"] = base_url
            config["default_headers"] = {
                "HTTP-Referer": getenv("YOUR_SITE_URL", ""),  # Opcional para rankings
                "X-Title": getenv("YOUR_SITE_NAME", "")  # Opcional para rankings
            }

        return ChatOpenAI(**config)

    @classmethod
    def create(
        cls,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_openrouter: bool = False
    ) -> ChatOpenAI:
        """
        Crea LLM según configuración.

        Args:
            model: Nombre del modelo (default: desde settings)
            temperature: Temperatura (default: desde settings)
            max_tokens: Max tokens (default: desde settings)
            use_openrouter: Si True, usa OpenRouter (default: False, usa OpenAI)

        Returns:
            ChatOpenAI configurado

        Raises:
            ValueError: Si falta API key
        """
        return cls.create_openai(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            use_openrouter=use_openrouter
        )


# Convenience functions
def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    use_openrouter: Optional[bool] = None
) -> ChatOpenAI:
    """
    Create LLM instance with configuration.

    Args:
        model: Model name (defaults to settings)
        temperature: Temperature parameter (defaults to settings)
        max_tokens: Maximum tokens (defaults to settings)
        use_openrouter: Use OpenRouter API (auto-detects if None)

    Returns:
        Configured ChatOpenAI instance
    """
    if use_openrouter is None:
        effective_model = model or settings.llm.openai_model
        use_openrouter = "/" in effective_model

    return LLMFactory.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        use_openrouter=use_openrouter
    )


# Exports
__all__ = ["LLMFactory", "get_llm"]
