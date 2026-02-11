"""
Estado Global del Sistema (Blackboard Pattern).

Define el GlobalState que circula por todo el grafo principal.
Utiliza TypedDict con Annotated para LangGraph.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated, Literal
from typing_extensions import NotRequired
import operator

from .schemas import AgentProfile, Proposal, SpawnRequest
from .reducers import merge_active_agents


class GlobalState(TypedDict):
    """
    Estado compartido por todo el sistema (Blackboard Pattern).

    Este estado circula por el grafo principal conectando:
    Genesis → Moderator → Universal Worker → Integrator

    Campos con Annotated usan reducers custom para merge inteligente:
    - active_agents: merge_active_agents (agrega sin duplicar por name)
    - spawn_requests: operator.add (append solicitudes)
    - staging_area: merge_staging_area (update sin sobrescribir)
    - knowledge_graph: merge_knowledge_graph (merge inteligente)
    - turn_history: operator.add (append turnos)
    """

    # --- INPUT DEL USUARIO ---
    user_query: str
    """Consulta original del usuario"""

    domain: str
    """Dominio detectado por Genesis (ej: 'Software Engineering', 'Legal')"""

    # --- META-COGNICIÓN (GENESIS) ---
    active_agents: Annotated[List[AgentProfile], merge_active_agents]
    """
    Lista de agentes activos en el sistema.
    Usa merge_active_agents que deduplica por name:
    - Agentes nuevos se agregan
    - Agentes existentes se reemplazan (actualización de perfil)
    - Genesis puede agregar agentes dinámicamente sin duplicar
    """

    dependencies: Dict[str, List[str]]
    """
    Mapa de dependencias entre agentes.
    Ejemplo: {"Frontend": ["Backend", "DBAdmin"]}
    El Moderator usa esto para bloquear agentes hasta que sus deps estén aprobadas.
    """

    spawn_requests: Annotated[List[SpawnRequest], operator.add]
    """
    Cola de solicitudes de nuevos agentes.
    Procesada por Genesis en cada turno.
    """

    # --- MEMORIA (BLACKBOARD & STAGING) ---
    knowledge_graph: Annotated[Dict[str, Any], "merge_knowledge_graph"]
    """
    Knowledge Graph del sistema.
    CRÍTICO: Usa reducer custom 'merge_knowledge_graph' (ver reducers.py)

    Estructura:
    {
        "entities": {
            "entity_id": {"type": "...", "properties": {...}}
        },
        "relations": [
            {"source": "...", "rel": "...", "target": "..."}
        ]
    }
    """

    staging_area: Annotated[Dict[str, Proposal], "merge_staging_area"]
    """
    Área de staging para propuestas de agentes.
    CRÍTICO: Usa reducer custom 'merge_staging_area' (ver reducers.py)

    Key: agent_name
    Value: última propuesta de ese agente
    """

    # --- ORQUESTACIÓN (MODERADOR) ---
    turn_history: Annotated[List[str], operator.add]
    """
    Log de turnos ejecutados.
    Ejemplo: ["Genesis", "BackendDev", "Integrator", "BackendDev", ...]
    """

    next_speaker: str
    """
    Quién tiene el turno actual.
    Valores especiales: "INTEGRATOR", "HUMAN", "FINISH"
    """

    iteration: int
    """Contador global de turnos (incrementa en cada ciclo)"""

    max_iterations: int
    """Límite de iteraciones para detectar deadlock (default: 20)"""

    # --- CONTROL DE FLUJO ---
    deadlock_detected: bool
    """Flag que indica si se detectó un deadlock"""

    needs_human_input: bool
    """Si se requiere intervención humana"""

    human_feedback: NotRequired[Optional[str]]
    """Input del humano (solo si needs_human_input=True)"""

    # --- SALIDA FINAL ---
    final_output: str
    """Resultado consolidado del sistema (generado al END)"""

    final_status: Literal["success", "deadlock", "error", "incomplete"]
    """Estado final de la ejecución"""


# Type hint para facilitar imports
__all__ = ["GlobalState"]
