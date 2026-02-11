"""
Moderator Agent - Gestión de Turnos y Orquestación.

Responsabilidades:
1. Decidir quién habla en cada turno
2. Detectar deadlocks y solicitar intervención humana
3. Gestionar prioridades y dependencias
"""

from typing import Optional
from langchain_openai import ChatOpenAI

from src.specialists.moderator.schema import TurnDecision, DeadlockInfo, ModeratorConfig
from src.specialists.moderator.chains import ModeratorChains


class ModeratorAgent:
    """
    Moderator - Orquestador del flujo del sistema.

    Orquesta las chains del Moderator y maneja la lógica de negocio:
    - Decisiones de turno
    - Detección de deadlocks
    - Gestión de prioridades
    """

    def __init__(self, config: ModeratorConfig, llm: ChatOpenAI):
        """
        Args:
            config: Configuración del Moderator
            llm: LLM configurado (OpenAI/OpenRouter)
        """
        self.config = config
        self.llm = llm
        self.name = "Moderator"

        # Inicializar chains
        self.chains = ModeratorChains(llm)

    def decide_turn(
        self,
        current_iteration: int,
        num_proposals_pending: int,
        num_agents: int,
        last_speaker: str,
        last_action: str,
        last_validation_result: str,
        agent_status_summary: str,
        rejection_history: str,
        dependency_summary: str,
        goal_progress_summary: str,
        recent_turns: str
    ) -> TurnDecision:
        """
        Decide quién debe hablar en el próximo turno.

        Args:
            current_iteration: Iteración actual
            num_proposals_pending: Propuestas sin validar
            num_agents: Número de agentes activos
            last_speaker: Último que habló
            last_action: Última acción
            last_validation_result: Resultado última validación
            agent_status_summary: Estado de agentes
            rejection_history: Historial de rechazos
            dependency_summary: Estado de dependencias
            goal_progress_summary: Progreso hacia objetivo
            recent_turns: Últimos turnos del historial

        Returns:
            TurnDecision con next_speaker y reasoning
        """
        return self.chains.decide_turn(
            current_iteration=current_iteration,
            max_iterations=self.config.max_iterations,
            num_proposals_pending=num_proposals_pending,
            num_agents=num_agents,
            last_speaker=last_speaker,
            last_action=last_action,
            last_validation_result=last_validation_result,
            agent_status_summary=agent_status_summary,
            rejection_history=rejection_history,
            dependency_summary=dependency_summary,
            goal_progress_summary=goal_progress_summary,
            rejection_loop_threshold=self.config.rejection_loop_threshold,
            recent_turns=recent_turns
        )

    def detect_deadlock(
        self,
        current_iteration: int,
        num_agents: int,
        max_agents: int,
        rejection_history: str,
        dependency_graph: str,
        spawn_request_history: str,
        agent_status_summary: str
    ) -> Optional[DeadlockInfo]:
        """
        Detecta si el sistema está en deadlock.

        Args:
            current_iteration: Iteración actual
            num_agents: Agentes activos
            max_agents: Máximo de agentes
            rejection_history: Historial de rechazos
            dependency_graph: Grafo de dependencias
            spawn_request_history: Historial de spawn requests
            agent_status_summary: Estado de agentes

        Returns:
            DeadlockInfo si detecta deadlock, None si no
        """
        return self.chains.detect_deadlock(
            current_iteration=current_iteration,
            max_iterations=self.config.max_iterations,
            num_agents=num_agents,
            max_agents=max_agents,
            rejection_history=rejection_history,
            dependency_graph=dependency_graph,
            spawn_request_history=spawn_request_history,
            agent_status_summary=agent_status_summary,
            rejection_loop_threshold=self.config.rejection_loop_threshold
        )

    def should_check_deadlock(self, current_iteration: int) -> bool:
        """
        Determina si se debe verificar deadlock en esta iteración.

        Args:
            current_iteration: Iteración actual

        Returns:
            True si debe verificar, False si no
        """
        # Verificar cada 3 iteraciones o cerca del límite
        return (
            current_iteration % 3 == 0 or
            current_iteration >= self.config.max_iterations - 2
        )


# Export
__all__ = ["ModeratorAgent"]
