"""
LangChain chains para Moderator.

Chains reutilizables para:
1. Decisión de turno (State → TurnDecision)
2. Detección de deadlock (State → DeadlockInfo)
"""

import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.specialists.moderator.schema import TurnDecision, DeadlockInfo
from src.utils.prompt_loader import load_prompt
from src.utils.llm_invoker import invoke_llm
from src.utils.helpers import extract_json


class ModeratorChains:
    """
    Chains de LangChain para Moderator.

    Encapsula la lógica de prompt + LLM + parsing.
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: Instancia de ChatOpenAI configurada
        """
        self.llm = llm
        self.system_prompt = load_prompt("moderator/system_prompt.txt")

    def decide_turn(
        self,
        current_iteration: int,
        max_iterations: int,
        num_proposals_pending: int,
        num_agents: int,
        last_speaker: str,
        last_action: str,
        last_validation_result: str,
        agent_status_summary: str,
        rejection_history: str,
        dependency_summary: str,
        goal_progress_summary: str,
        rejection_loop_threshold: int,
        recent_turns: str
    ) -> TurnDecision:
        """
        Chain: Decisión de próximo turno.

        Args:
            current_iteration: Iteración actual
            max_iterations: Máximo de iteraciones
            num_proposals_pending: Propuestas sin validar
            num_agents: Número de agentes activos
            last_speaker: Último que habló
            last_action: Última acción
            last_validation_result: Resultado última validación
            agent_status_summary: Estado de agentes
            rejection_history: Historial de rechazos
            dependency_summary: Estado de dependencias
            goal_progress_summary: Progreso hacia objetivo
            rejection_loop_threshold: Umbral de loop

        Returns:
            TurnDecision con next_speaker y reasoning
        """
        # Cargar task prompt
        task_prompt = load_prompt(
            "moderator/task_turn_decision.txt",
            current_iteration=current_iteration,
            max_iterations=max_iterations,
            num_proposals_pending=num_proposals_pending,
            num_agents=num_agents,
            last_speaker=last_speaker,
            last_action=last_action,
            last_validation_result=last_validation_result,
            agent_status_summary=agent_status_summary,
            rejection_history=rejection_history,
            dependency_summary=dependency_summary,
            rejection_loop_threshold=rejection_loop_threshold,
            goal_progress_summary=goal_progress_summary,
            recent_turns=recent_turns
        )

        # Construir mensajes
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task_prompt)
        ]

        # Invocar LLM
        response = invoke_llm(self.llm, messages, agent_name="Moderator", chain_name="decide_turn")

        # Parse JSON
        try:
            data = extract_json(response.content)
            return TurnDecision(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse TurnDecision from LLM response.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )

    def detect_deadlock(
        self,
        current_iteration: int,
        max_iterations: int,
        num_agents: int,
        max_agents: int,
        rejection_history: str,
        dependency_graph: str,
        spawn_request_history: str,
        agent_status_summary: str,
        rejection_loop_threshold: int
    ) -> DeadlockInfo | None:
        """
        Chain: Detección de deadlock.

        Args:
            current_iteration: Iteración actual
            max_iterations: Máximo permitido
            num_agents: Agentes activos
            max_agents: Máximo de agentes
            rejection_history: Historial de rechazos
            dependency_graph: Grafo de dependencias
            spawn_request_history: Historial de spawn requests
            agent_status_summary: Estado de agentes
            rejection_loop_threshold: Umbral de loop

        Returns:
            DeadlockInfo si detecta deadlock, None si no
        """
        # Cargar task prompt
        task_prompt = load_prompt(
            "moderator/task_detect_deadlock.txt",
            current_iteration=current_iteration,
            max_iterations=max_iterations,
            num_agents=num_agents,
            max_agents=max_agents,
            rejection_history=rejection_history,
            dependency_graph=dependency_graph,
            spawn_request_history=spawn_request_history,
            agent_status_summary=agent_status_summary,
            rejection_loop_threshold=rejection_loop_threshold
        )

        # Construir mensajes
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task_prompt)
        ]

        # Invocar LLM
        response = invoke_llm(self.llm, messages, agent_name="Moderator", chain_name="detect_deadlock")

        # Parse JSON
        try:
            data = extract_json(response.content)

            # Si deadlock_type es null, no hay deadlock
            if data.get("deadlock_type") is None:
                return None

            return DeadlockInfo(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse DeadlockInfo from LLM response.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )


# Export
__all__ = ["ModeratorChains"]
