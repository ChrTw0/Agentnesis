"""
LLM Invoker - Helper centralizado para invocar LLMs con logging condicional.

Centraliza la lógica de invocar LLMs:
- Modo developer: usa LoggingLLM (loguea prompts/responses)
- Modo producción: invoca directamente

Principios SOLID:
- Single Responsibility: Solo maneja invocación de LLMs
- DRY: Evita duplicar lógica de if/else en cada chain
"""

from typing import List
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from src.config.settings import settings
from src.utils.llm_wrapper import LoggingLLM


def invoke_llm(
    llm: ChatOpenAI,
    messages: List[BaseMessage],
    agent_name: str,
    chain_name: str
):
    """
    Invoca LLM con logging condicional según configuración.

    Args:
        llm: Instancia de ChatOpenAI
        messages: Lista de mensajes a enviar
        agent_name: Nombre del agente (para logging)
        chain_name: Nombre de la chain (para logging)

    Returns:
        Respuesta del LLM

    Example:
        >>> response = invoke_llm(
        ...     self.llm,
        ...     messages,
        ...     agent_name="Genesis",
        ...     chain_name="analyze_domain"
        ... )
    """
    if settings.developer.developer_mode:
        # Modo developer: wrapper con logging
        logging_llm = LoggingLLM(llm, agent_name=agent_name, chain_name=chain_name)
        return logging_llm.invoke(messages)
    else:
        # Modo producción: invocación directa
        return llm.invoke(messages)


# Export
__all__ = ["invoke_llm"]
