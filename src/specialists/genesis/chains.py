"""
LangChain chains para Genesis.

Chains reutilizables para:
1. Análisis de dominio (user_query → DomainAnalysis)
2. Decisión de spawn (SpawnRequest → SpawnDecision)
"""

import json
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.core.states.schemas import AgentProfile, SpawnRequest
from src.specialists.genesis.schema import DomainAnalysis, SpawnDecision
from src.utils.prompt_loader import load_prompt
from src.utils.llm_invoker import invoke_llm
from src.utils.helpers import extract_json


class GenesisChains:
    """
    Chains de LangChain para Genesis.

    Encapsula la lógica de prompt + LLM + parsing.
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: Instancia de ChatOpenAI configurada
        """
        self.llm = llm
        self.system_prompt = load_prompt("genesis/system_prompt.txt")

    def analyze_domain(self, user_query: str, num_agents: int, max_agents: int) -> DomainAnalysis:
        """
        Chain: Análisis de dominio del problema.

        Args:
            user_query: Query del usuario
            num_agents: Número actual de agentes
            max_agents: Máximo de agentes permitidos

        Returns:
            DomainAnalysis con dominio, complejidad, roles requeridos
        """
        # Cargar task prompt
        task_prompt = load_prompt(
            "genesis/task_domain_analysis.txt",
            user_query=user_query,
            max_agents=max_agents,
            num_agents=num_agents
        )

        # Construir mensajes
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task_prompt)
        ]

        # Invocar LLM
        response = invoke_llm(self.llm, messages, agent_name="Genesis", chain_name="analyze_domain")

        # Parse JSON
        try:
            data = extract_json(response.content)
            return DomainAnalysis(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse DomainAnalysis from LLM response.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )

    def decide_spawn(
        self,
        request: SpawnRequest,
        num_agents: int,
        max_agents: int,
        agents: List[AgentProfile],
        num_pending_requests: int,
        saturation_threshold: float,
        max_spawn_depth: int | None
    ) -> SpawnDecision:
        """
        Chain: Decisión sobre SpawnRequest.

        Args:
            request: SpawnRequest del agente
            num_agents: Número actual de agentes
            max_agents: Máximo permitido
            agents: Lista de agentes existentes
            num_pending_requests: Requests pendientes
            saturation_threshold: Umbral de saturación (0-1)
            max_spawn_depth: Límite de spawn depth (None = sin límite)

        Returns:
            SpawnDecision con veredicto
        """
        # Obtener info del requester
        requester = next((a for a in agents if a.name == request.requester), None)
        requester_spawn_depth = requester.spawn_depth if requester else 0
        requester_spawned_by = requester.spawned_by if requester else "Unknown"

        # Calcular saturación
        saturation_percent = (num_agents / max_agents) * 100

        # Formatear resumen de agentes
        agents_summary = self._format_agents_summary(agents)

        # Cargar task prompt
        task_prompt = load_prompt(
            "genesis/task_spawn_decision.txt",
            requester=request.requester,
            role=request.role,
            required_expertise=", ".join(request.required_expertise),
            justification=request.justification,
            context=request.context,
            priority=request.priority,
            num_agents=num_agents,
            max_agents=max_agents,
            saturation_percent=f"{saturation_percent:.1f}",
            num_pending_requests=num_pending_requests,
            requester_spawn_depth=requester_spawn_depth,
            requester_spawned_by=requester_spawned_by,
            agents_summary=agents_summary,
            max_spawn_depth=max_spawn_depth or "None (use judgment)",
            enable_agent_reuse="true",
            saturation_threshold=f"{saturation_threshold * 100:.0f}"
        )

        # Construir mensajes
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task_prompt)
        ]

        # Invocar LLM
        response = invoke_llm(self.llm, messages, agent_name="Genesis", chain_name="decide_spawn")

        # Parse JSON
        try:
            data = extract_json(response.content)
            return SpawnDecision(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse SpawnDecision from LLM response.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )

    def _format_agents_summary(self, agents: List[AgentProfile]) -> str:
        """Helper: Formatear lista de agentes."""
        if not agents:
            return "- None"

        lines = []
        for agent in agents:
            expertise_str = ", ".join(agent.expertise) if agent.expertise else "general"
            lines.append(
                f"- {agent.name} ({agent.role}) [depth={agent.spawn_depth}, expertise={expertise_str}]"
            )
        return "\n".join(lines)


# Export
__all__ = ["GenesisChains"]
