"""
LLM Wrapper con logging automático para modo developer.

Envuelve llamadas a LLM para loguear automáticamente prompts y responses
cuando DEVELOPER_MODE=true.
"""

from typing import List, Any
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from src.utils.dev_logger import dev_logger


class LoggingLLM:
    """
    Wrapper para ChatOpenAI que loguea llamadas en modo developer.

    Usage:
        llm = LoggingLLM(base_llm, agent_name="Genesis", chain_name="analyze_domain")
        response = llm.invoke(messages)
    """

    def __init__(
        self,
        base_llm: ChatOpenAI,
        agent_name: str,
        chain_name: str
    ):
        """
        Args:
            base_llm: LLM base (ChatOpenAI)
            agent_name: Nombre del agente que usa este LLM
            chain_name: Nombre de la chain que usa este LLM
        """
        self.base_llm = base_llm
        self.agent_name = agent_name
        self.chain_name = chain_name

    def invoke(self, messages: List[BaseMessage], **kwargs) -> Any:
        """
        Invoca el LLM y loguea la interacción.

        Args:
            messages: Lista de mensajes (SystemMessage, HumanMessage, etc.)
            **kwargs: Argumentos adicionales para el LLM

        Returns:
            Respuesta del LLM
        """
        # Formatear prompt para logging
        prompt_str = self._format_messages(messages)

        # Invocar LLM base
        response = self.base_llm.invoke(messages, **kwargs)

        # Loguear si developer mode activo
        dev_logger.log_llm_call(
            agent_name=self.agent_name,
            chain_name=self.chain_name,
            model=self.base_llm.model_name,
            prompt=prompt_str,
            response=response.content,
            metadata={
                "temperature": self.base_llm.temperature,
                "max_tokens": self.base_llm.max_tokens,
                **kwargs
            }
        )

        return response

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """Helper: Formatear mensajes como string legible."""
        formatted = []
        for msg in messages:
            role = msg.__class__.__name__.replace("Message", "")
            formatted.append(f"[{role}]\n{msg.content}\n")
        return "\n".join(formatted)


# Export
__all__ = ["LoggingLLM"]
