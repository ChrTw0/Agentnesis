"""
Estado Interno del Agente Fractal (InternalAgentState).

Este estado es PRIVADO del subgrafo fractal (Planner → Executor → Critic).
NO se comparte entre agentes, solo circula dentro del ciclo cognitivo.
"""

from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import NotRequired

from src.core.states.schemas import AgentProfile, SpawnRequest


class InternalAgentState(TypedDict):
    """
    Estado privado del ciclo cognitivo de un agente fractal.

    Flujo: Planner → Executor → Critic → (loop o END)

    AISLAMIENTO GARANTIZADO:
    - Este estado NO se propaga fuera del subgrafo
    - Cada agente tiene su propia instancia
    - La comunicación externa es SOLO por el campo 'draft'
    """

    # --- INPUTS (Recibidos del GlobalState vía Universal Worker) ---
    profile: AgentProfile
    """Configuración del agente actual (incluye tools permitidas)"""

    task: str
    """Tarea asignada por el usuario o el Moderador"""

    global_context: str
    """
    Fragmento relevante del Knowledge Graph (como texto).
    Obtenido vía RAG selectivo para no saturar contexto.
    """

    feedback_history: List[str]
    """
    Feedbacks anteriores del Integrator (si fue rechazado).
    Permite al agente aprender de errores previos.
    """

    # --- BUCLE COGNITIVO (Estado Mutable Interno) ---
    plan: List[str]
    """Chain of Thought generado por el Planner"""

    current_step: int
    """Índice del paso actual en ejecución (0-indexed)"""

    scratchpad: List[str]
    """
    Logs de ejecución de tools (observaciones).
    PRIVADO: No se expone fuera del subgrafo.
    """

    draft: str
    """Borrador actual de la propuesta (texto descriptivo)."""

    structured_data: Dict[str, Any]
    """
    Datos estructurados para el Knowledge Graph.
    Sale junto con draft hacia GlobalState vía WorkerExecutionResult.
    Estructura: {"entities": {...}, "relations": [...]}
    """

    # --- CONTROL DE CALIDAD ---
    critique_count: int
    """Número de veces que el Critic rechazó internamente"""

    max_retries: int
    """
    Límite SOFT recomendado para retries (default: 3).
    Critic puede extender si justificado, pero no más allá de absolute_max_retries.
    """

    absolute_max_retries: int
    """
    Límite HARD absoluto para prevenir loops infinitos (default: 5).
    Non-negotiable - fuerza aprobación si se alcanza.
    """

    is_complete: bool
    """Flag: ¿El Critic aprobó el draft?"""

    # --- SEÑALES DE SALIDA ---
    spawn_request: NotRequired[Optional[SpawnRequest]]
    """
    Si el Executor detecta capability gap, emite esta señal.
    Se propaga al GlobalState para que Genesis procese.
    """

    confidence_score: float
    """Auto-evaluación de la calidad del draft (0.0-1.0)"""


# Exports
__all__ = ["InternalAgentState"]
