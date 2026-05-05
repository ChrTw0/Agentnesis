"""
Universal Worker Agent - Ejecutor Polimórfico.

Responsabilidades:
1. Ejecutar cualquier rol de agente dinámicamente
2. Invocar el subgrafo fractal con aislamiento
3. Extraer contexto relevante del Knowledge Graph
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI

from src.core.states.schemas import AgentProfile, SpawnRequest
from src.specialists.universal_worker.schema import (
    WorkerExecutionResult,
    UniversalWorkerConfig,
    ContextRetrievalConfig
)
from src.specialists.universal_worker.chains import UniversalWorkerChains
from src.specialists.fractal_agent.schema import InternalAgentState
from src.specialists.fractal_agent.subgraph import compile_fractal_subgraph
from src.tools.registry import get_tools
from src.utils.helpers import get_temporal_anchor
from src.config.settings import settings


class UniversalWorkerAgent:
    """
    Universal Worker - Ejecutor polimórfico de roles dinámicos.

    NO ejecuta LLM directamente. En cambio:
    1. Prepara contexto del KG
    2. Invoca el subgrafo fractal (Planner → Executor → Critic)
    3. Retorna el resultado estructurado
    """

    def __init__(
        self,
        config: UniversalWorkerConfig,
        context_config: ContextRetrievalConfig,
        llm: ChatOpenAI
    ):
        """
        Args:
            config: Configuración del Universal Worker
            context_config: Configuración de context retrieval (RAG)
            llm: LLM configurado (para el subgrafo fractal)
        """
        self.config = config
        self.context_config = context_config
        self.llm = llm
        self.name = "UniversalWorker"

        # Inicializar chains (helpers)
        self.chains = UniversalWorkerChains()

        # Compilar subgrafo fractal sin tools (cache genérico sin tools)
        # Agentes con tools reciben un subgrafo fresco con sus tools en _invoke_fractal_subgraph
        self.fractal_subgraph = compile_fractal_subgraph(llm) if config.cache_subgraphs else None

    def execute_agent_work(
        self,
        agent_profile: AgentProfile,
        user_query: str,
        agent_task: str,
        kg_entities: Dict[str, Any],
        kg_relations: List[Dict[str, str]],
        recent_activity: str = ""
    ) -> WorkerExecutionResult:
        """
        Ejecuta el trabajo del agente invocando el subgrafo fractal.

        Args:
            agent_profile: Perfil del agente (con inner layer prompt)
            user_query: Query original del usuario
            agent_task: Tarea específica asignada
            kg_entities: Entidades del Knowledge Graph
            kg_relations: Relaciones del Knowledge Graph
            recent_activity: Actividad reciente del sistema

        Returns:
            WorkerExecutionResult con draft y structured_data
        """
        # Extraer contexto relevante del KG (RAG selectivo)
        kg_entities_str, kg_relations_str = self.chains.extract_kg_context(
            kg_entities=kg_entities,
            kg_relations=kg_relations,
            agent_profile=agent_profile,
            top_k=self.context_config.top_k
        )

        # Preparar contexto completo para el subgrafo
        execution_context = self.chains.prepare_execution_context(
            agent_profile=agent_profile,
            user_query=user_query,
            agent_task=agent_task,
            kg_entities=kg_entities_str,
            kg_relations=kg_relations_str,
            recent_activity=recent_activity,
            dependencies_status="All dependencies met",  # TODO: Verificar dependencias
            execution_timeout=self.config.execution_timeout,
            max_retries_on_error=self.config.max_retries_on_error
        )

        # Inyectar temporal anchor en el KG context
        temporal_anchor = get_temporal_anchor()
        kg_context_with_time = f"{execution_context['kg_context']}\n\n{temporal_anchor}"

        # Resolver tools del AgentProfile contra el registry (solo si tools están habilitadas)
        resolved_tools = []
        if settings.tools.tools_enabled and agent_profile.tools:
            resolved_tools = get_tools(agent_profile.tools)

        # Invocar el subgrafo fractal
        try:
            result = self._invoke_fractal_subgraph(
                agent_profile=agent_profile,
                task=agent_task,
                kg_context=kg_context_with_time,
                feedback_history=[],
                tools=resolved_tools
            )
            return result
        except Exception as e:
            # Error en ejecución del subgrafo
            return WorkerExecutionResult(
                agent_name=agent_profile.name,
                draft="",
                structured_data={"entities": {}, "relations": []},
                confidence_score=0.0,
                internal_iterations=0,
                spawn_requested=False,
                error=f"Fractal subgraph error: {str(e)}"
            )

    def _invoke_fractal_subgraph(
        self,
        agent_profile: AgentProfile,
        task: str,
        kg_context: str,
        feedback_history: List[str],
        tools: list | None = None
    ) -> WorkerExecutionResult:
        """
        Invoca el subgrafo fractal (Planner → Executor → Critic).

        Args:
            agent_profile: Perfil del agente
            task: Tarea asignada
            kg_context: Contexto del KG
            feedback_history: Historial de feedback

        Returns:
            WorkerExecutionResult del subgrafo
        """
        # Obtener o compilar subgrafo
        # Si el agente tiene tools, siempre compilar subgrafo fresco con sus tools
        if tools:
            subgraph = compile_fractal_subgraph(self.llm, tools=tools)
        elif self.fractal_subgraph is None:
            subgraph = compile_fractal_subgraph(self.llm)
        else:
            subgraph = self.fractal_subgraph

        # Preparar estado inicial
        initial_state: InternalAgentState = {
            "profile": agent_profile,
            "task": task,
            "global_context": kg_context,
            "feedback_history": feedback_history,
            "plan": [],
            "current_step": 0,
            "scratchpad": [],
            "draft": "",
            "structured_data": {"entities": {}, "relations": []},
            "critique_count": 0,
            "max_retries": 3,  # TODO: Obtener de config
            "absolute_max_retries": 5,  # TODO: Obtener de config
            "is_complete": False,
            "spawn_request": None,
            "confidence_score": 0.0
        }

        # Invocar subgrafo
        final_state = subgraph.invoke(initial_state)

        # Extraer resultado
        raw_spawn = final_state.get("spawn_request")
        spawn_request = SpawnRequest(**raw_spawn) if isinstance(raw_spawn, dict) else raw_spawn

        return WorkerExecutionResult(
            agent_name=agent_profile.name,
            draft=final_state["draft"],
            structured_data=final_state.get("structured_data", {"entities": {}, "relations": []}),
            confidence_score=final_state["confidence_score"],
            internal_iterations=final_state["critique_count"],
            spawn_requested=spawn_request is not None,
            spawn_request=spawn_request,
            error=None
        )


# Export
__all__ = ["UniversalWorkerAgent"]
