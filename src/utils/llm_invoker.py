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
from langchain_core.tools import BaseTool
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


def invoke_llm_with_tools(
    llm: ChatOpenAI,
    messages: List[BaseMessage],
    tools: List[BaseTool],
    agent_name: str,
    chain_name: str
):
    """
    Invoca LLM con tool calling habilitado.

    Vincula las tools al LLM y ejecuta el ciclo de tool calling
    hasta que el LLM produzca una respuesta final (sin más tool calls).

    Args:
        llm: Instancia de ChatOpenAI
        messages: Lista de mensajes a enviar
        tools: Lista de BaseTool disponibles para el LLM
        agent_name: Nombre del agente (para logging)
        chain_name: Nombre de la chain (para logging)

    Returns:
        Respuesta final del LLM (tras resolver todos los tool calls)
    """
    from langchain_core.messages import ToolMessage

    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    current_messages = list(messages)

    while True:
        if settings.developer.developer_mode:
            logging_llm = LoggingLLM(llm_with_tools, agent_name=agent_name, chain_name=chain_name)
            response = logging_llm.invoke(current_messages)
        else:
            response = llm_with_tools.invoke(current_messages)

        # Si no hay tool calls, es la respuesta final
        if not response.tool_calls:
            return response

        # Ejecutar tool calls y agregar resultados
        current_messages.append(response)
        for tool_call in response.tool_calls:
            tool = tool_map.get(tool_call["name"])
            if tool is None:
                result = f"Error: tool '{tool_call['name']}' not found"
            else:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(tool.ainvoke(tool_call["args"]))
                except RuntimeError:
                    result = asyncio.run(tool.ainvoke(tool_call["args"]))

            current_messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_call["id"])
            )


# Export
__all__ = ["invoke_llm", "invoke_llm_with_tools"]
