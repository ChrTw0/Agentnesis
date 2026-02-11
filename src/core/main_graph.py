"""
Main Graph - Orquestación del Sistema Completo.

Flujo principal:
1. Genesis Bootstrap: Analiza dominio y crea agentes iniciales
2. Loop:
   - Moderator: Decide próximo speaker
   - Agent Turn: Universal Worker ejecuta el agente
   - Integrator: Valida propuesta
   - Check deadlock
3. Termina: FINISH (éxito) o HUMAN (deadlock/intervención)
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from src.core.states.global_state import GlobalState
from src.core.states.schemas import AgentProfile, Proposal
from src.specialists.genesis.agent import GenesisAgent
from src.specialists.genesis.schema import GenesisConfig
from src.specialists.moderator.agent import ModeratorAgent
from src.specialists.moderator.schema import ModeratorConfig
from src.specialists.integrator.agent import IntegratorAgent
from src.specialists.integrator.schema import IntegratorConfig
from src.specialists.universal_worker.agent import UniversalWorkerAgent
from src.specialists.universal_worker.schema import UniversalWorkerConfig, ContextRetrievalConfig
from src.specialists.synthesizer.agent import SynthesizerAgent
from src.specialists.synthesizer.schema import SynthesizerConfig
from src.config.llm_factory import get_llm
from src.utils.helpers import format_recent_turns


def create_main_graph(
    genesis_config: GenesisConfig,
    moderator_config: ModeratorConfig,
    integrator_config: IntegratorConfig,
    worker_config: UniversalWorkerConfig,
    context_config: ContextRetrievalConfig,
    synthesizer_config: SynthesizerConfig
) -> StateGraph:
    """
    Crea el grafo principal del sistema.

    Args:
        genesis_config: Config de Genesis
        moderator_config: Config de Moderator
        integrator_config: Config de Integrator
        worker_config: Config de Universal Worker
        context_config: Config de context retrieval
        synthesizer_config: Config de Synthesizer

    Returns:
        StateGraph del main graph
    """
    # Instanciar LLMs para cada agente según su configuración
    genesis_llm = get_llm(model=genesis_config.model_name)
    moderator_llm = get_llm(model=moderator_config.model_name)
    integrator_llm = get_llm(model=integrator_config.model_name)
    worker_llm = get_llm(model=worker_config.model_name)
    synthesizer_llm = get_llm(model=synthesizer_config.model_name)

    # Instanciar agentes
    genesis = GenesisAgent(genesis_config, genesis_llm)
    moderator = ModeratorAgent(moderator_config, moderator_llm)
    integrator = IntegratorAgent(integrator_config, integrator_llm)
    worker = UniversalWorkerAgent(worker_config, context_config, worker_llm)
    synthesizer = SynthesizerAgent(synthesizer_config, synthesizer_llm)

    # === NODOS ===

    def genesis_bootstrap_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Genesis Bootstrap - Análisis inicial y creación de agentes.

        Ejecuta solo al inicio para analizar dominio y crear agentes iniciales.
        """
        # Analizar dominio
        domain_analysis = genesis.analyze_domain(
            user_query=state["user_query"],
            num_agents=len(state.get("active_agents", []))
        )

        # Actualizar dominio
        state["domain"] = domain_analysis.domain

        # Crear agentes iniciales
        new_agents = []
        for role in domain_analysis.required_roles:
            # Mapear rol a expertise (simplificado, mejorar en futuro)
            expertise = [role]  # TODO: Lookup table rol → expertise

            agent_profile = genesis.create_agent_profile(
                role=role,
                expertise=expertise,
                spawned_by="Genesis",
                spawn_depth=1,
                existing_agents=state.get("active_agents", [])
            )
            new_agents.append(agent_profile)

        # Agregar agentes al estado
        state["active_agents"] = new_agents

        return state

    def moderator_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Moderator - Decide próximo speaker.
        """
        # Preparar datos para decisión
        agent_status_summary = _format_agent_status(state.get("active_agents", []), state.get("staging_area", {}))
        rejection_history = _format_rejection_history(state.get("staging_area", {}))
        dependency_summary = _format_dependencies(state.get("dependencies", {}))
        goal_progress = _format_goal_progress(state)
        recent_turns = format_recent_turns(state.get("turn_history", []))

        # Decidir turno
        turn_decision = moderator.decide_turn(
            current_iteration=state["iteration"],
            num_proposals_pending=len([p for p in state.get("staging_area", {}).values() if p.status == "draft"]),
            num_agents=len(state.get("active_agents", [])),
            last_speaker=state["turn_history"][-1] if state.get("turn_history") else "Genesis",
            last_action="bootstrap" if state["iteration"] == 0 else "agent_work",
            last_validation_result="none",
            agent_status_summary=agent_status_summary,
            rejection_history=rejection_history,
            dependency_summary=dependency_summary,
            goal_progress_summary=goal_progress,
            recent_turns=recent_turns
        )

        # Actualizar estado
        state["next_speaker"] = turn_decision.next_speaker
        state["turn_history"] = [turn_decision.next_speaker]

        # Setear flags según decisión (no se puede hacer en routing functions)
        if turn_decision.next_speaker == "FINISH":
            state["final_status"] = "success"
        elif turn_decision.next_speaker == "HUMAN":
            state["needs_human_input"] = True

        # Incrementar iteración
        state["iteration"] += 1

        return state

    def agent_work_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Agent Work - Universal Worker ejecuta el agente actual.
        """
        agent_name = state["next_speaker"]

        # Buscar agente
        agent_profile = next(
            (a for a in state.get("active_agents", []) if a.name == agent_name),
            None
        )

        if agent_profile is None:
            # Error: agente no encontrado
            state["final_status"] = "error"
            state["final_output"] = f"Error: Agent {agent_name} not found"
            return state

        # Ejecutar agente
        result = worker.execute_agent_work(
            agent_profile=agent_profile,
            user_query=state["user_query"],
            agent_task=f"Contribute to solving: {state['user_query']}",
            kg_entities=state["knowledge_graph"].get("entities", {}),
            kg_relations=state["knowledge_graph"].get("relations", []),
            recent_activity="\n".join(state.get("turn_history", [])[-5:])
        )

        # Crear propuesta
        proposal = Proposal(
            agent_name=agent_name,
            iteration=state["iteration"],
            content=result.draft,
            structured_data=result.structured_data,
            status="draft",
            feedback="",
            dependencies_met=True
        )

        # Agregar a staging area
        staging = state.get("staging_area", {})
        staging[agent_name] = proposal
        state["staging_area"] = staging

        # Si solicitó spawn, agregar a cola
        if result.spawn_requested and result.spawn_request:
            spawn_requests = list(state.get("spawn_requests", []))
            spawn_requests.append(result.spawn_request)
            state["spawn_requests"] = spawn_requests

        return state

    def integrator_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Integrator - Valida propuesta del staging area.
        """
        # Obtener propuesta más reciente
        staging = state.get("staging_area", {})
        if not staging:
            return state

        # Validar la última propuesta en draft
        latest_proposal = None
        latest_agent = None
        for agent_name, proposal in staging.items():
            if proposal.status == "draft":
                latest_proposal = proposal
                latest_agent = agent_name
                break

        if latest_proposal is None:
            return state

        # Buscar perfil del agente
        agent_profile = next(
            (a for a in state.get("active_agents", []) if a.name == latest_agent),
            None
        )

        if agent_profile is None:
            return state

        # Validar propuesta
        validation = integrator.validate_proposal(
            proposal=latest_proposal,
            agent_profile=agent_profile,
            kg_entities=state["knowledge_graph"].get("entities", {}),
            kg_relations=state["knowledge_graph"].get("relations", []),
            recent_approvals=[]
        )

        # Actualizar propuesta con resultado
        latest_proposal.status = validation.status
        latest_proposal.feedback = validation.feedback
        staging[latest_agent] = latest_proposal
        state["staging_area"] = staging

        # Si aprobado, actualizar Knowledge Graph
        if validation.status == "approved":
            kg_update = integrator.create_kg_update(latest_proposal, validation)

            kg = state["knowledge_graph"]
            kg["entities"].update(kg_update.entities_added)
            kg["relations"].extend(kg_update.relations_added)
            state["knowledge_graph"] = kg

        return state

    def check_deadlock_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Check Deadlock - Verifica si hay deadlock.
        """
        if not moderator.should_check_deadlock(state["iteration"]):
            return state

        # Detectar deadlock
        deadlock = moderator.detect_deadlock(
            current_iteration=state["iteration"],
            num_agents=len(state.get("active_agents", [])),
            max_agents=genesis_config.max_agents,
            rejection_history=_format_rejection_history(state.get("staging_area", {})),
            dependency_graph="{}",  # TODO: Formatear dependency graph
            spawn_request_history="[]",  # TODO: Formatear spawn requests
            agent_status_summary=_format_agent_status(state.get("active_agents", []), state.get("staging_area", {}))
        )

        if deadlock:
            state["deadlock_detected"] = True
            state["needs_human_input"] = True
            state["final_status"] = "deadlock"
            state["final_output"] = f"Deadlock detected: {deadlock.description}"

        return state

    def genesis_spawn_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Genesis Spawn - Procesa el primer SpawnRequest de la cola.
        Genesis decide: crear nuevo agente, reusar existente, o rechazar.
        """
        spawn_requests = list(state.get("spawn_requests", []))
        if not spawn_requests:
            return state

        # Tomar primer request de la cola
        request = spawn_requests.pop(0)
        state["spawn_requests"] = spawn_requests

        # Si spawn dinámico está deshabilitado, ignorar
        if not genesis_config.allow_dynamic_spawn:
            return state

        # Genesis decide
        decision = genesis.decide_spawn(
            request=request,
            num_agents=len(state.get("active_agents", [])),
            agents=state.get("active_agents", []),
            num_pending_requests=len(spawn_requests)
        )

        if decision.should_spawn:
            # Crear nuevo agente
            requester = next(
                (a for a in state.get("active_agents", []) if a.name == request.requester),
                None
            )
            new_agent = genesis.create_agent_profile(
                role=decision.agent_name or request.role,
                expertise=request.required_expertise,
                spawned_by=request.requester,
                spawn_depth=(requester.spawn_depth + 1) if requester else 1,
                existing_agents=state.get("active_agents", []),
                spawn_reason=request.justification
            )
            agents = list(state.get("active_agents", []))
            agents.append(new_agent)
            state["active_agents"] = agents

        return state

    def finalize_node(state: GlobalState) -> GlobalState:
        """
        Nodo: Finalize - Genera output final usando Synthesizer.
        """
        if state.get("final_status") == "success":
            # Sintetizar respuesta final usando Synthesizer
            synthesis_result = synthesizer.synthesize_final_output(
                user_query=state["user_query"],
                domain=state.get("domain", "general"),
                kg_entities=state["knowledge_graph"].get("entities", {}),
                kg_relations=state["knowledge_graph"].get("relations", []),
                staging_area=state.get("staging_area", {}),
                active_agents=state.get("active_agents", []),
                num_iterations=state["iteration"]
            )

            # Guardar resultado de síntesis
            state["final_output"] = synthesis_result.final_answer
            state["synthesis_metadata"] = {
                "summary": synthesis_result.summary,
                "key_decisions": synthesis_result.key_decisions,
                "entities_created": synthesis_result.entities_created,
                "agents_involved": synthesis_result.agents_involved,
                "confidence": synthesis_result.confidence
            }
        elif state.get("final_status") == "deadlock":
            # Si hubo deadlock, mantener el mensaje de error
            pass
        else:
            # Otros estados de error
            state["final_output"] = state.get("final_output", "System terminated without success.")

        return state

    # === CONDITIONAL EDGES ===

    def route_after_agent_work(state: GlobalState) -> Literal["genesis_spawn", "moderator"]:
        """
        Decide qué hacer después de agent_work.
        Si hay spawn requests pendientes, procesar primero.
        """
        if state.get("spawn_requests"):
            return "genesis_spawn"
        return "moderator"

    def route_after_moderator(state: GlobalState) -> Literal["agent_work", "integrator", "check_deadlock", "finalize"]:
        """
        Decide qué hacer después del Moderator.

        Returns:
            - "agent_work": Si next_speaker es un agente
            - "integrator": Si next_speaker es INTEGRATOR
            - "check_deadlock": Si hay propuestas pendientes de validar
            - "finalize": Si next_speaker es FINISH
        """
        next_speaker = state["next_speaker"]

        if next_speaker == "FINISH":
            return "finalize"
        elif next_speaker == "INTEGRATOR":
            return "integrator"
        elif next_speaker == "HUMAN":
            return "check_deadlock"
        else:
            # Es un agente normal
            return "agent_work"

    def route_after_integrator(state: GlobalState) -> Literal["moderator", "check_deadlock"]:
        """
        Decide qué hacer después del Integrator.

        Returns:
            - "moderator": Si debe continuar loop
            - "check_deadlock": Si debe verificar deadlock
        """
        if moderator.should_check_deadlock(state["iteration"]):
            return "check_deadlock"
        return "moderator"

    def route_after_deadlock_check(state: GlobalState) -> Literal["moderator", "finalize"]:
        """
        Decide qué hacer después de check deadlock.

        Returns:
            - "finalize": Si hay deadlock o needs_human_input
            - "moderator": Si puede continuar
        """
        if state.get("deadlock_detected") or state.get("needs_human_input"):
            return "finalize"
        return "moderator"

    # === CONSTRUIR GRAFO ===

    workflow = StateGraph(GlobalState)

    # Agregar nodos
    workflow.add_node("genesis_bootstrap", genesis_bootstrap_node)
    workflow.add_node("moderator", moderator_node)
    workflow.add_node("agent_work", agent_work_node)
    workflow.add_node("genesis_spawn", genesis_spawn_node)
    workflow.add_node("integrator", integrator_node)
    workflow.add_node("check_deadlock", check_deadlock_node)
    workflow.add_node("finalize", finalize_node)

    # Entry point
    workflow.set_entry_point("genesis_bootstrap")

    # Edges
    workflow.add_edge("genesis_bootstrap", "moderator")
    workflow.add_edge("genesis_spawn", "moderator")

    # Conditional edges
    workflow.add_conditional_edges(
        "agent_work",
        route_after_agent_work,
        {
            "genesis_spawn": "genesis_spawn",
            "moderator": "moderator"
        }
    )

    workflow.add_conditional_edges(
        "moderator",
        route_after_moderator,
        {
            "agent_work": "agent_work",
            "integrator": "integrator",
            "check_deadlock": "check_deadlock",
            "finalize": "finalize"
        }
    )

    workflow.add_conditional_edges(
        "integrator",
        route_after_integrator,
        {
            "moderator": "moderator",
            "check_deadlock": "check_deadlock"
        }
    )

    workflow.add_conditional_edges(
        "check_deadlock",
        route_after_deadlock_check,
        {
            "moderator": "moderator",
            "finalize": "finalize"
        }
    )

    workflow.add_edge("finalize", END)

    return workflow


# === HELPER FUNCTIONS ===

def _format_agent_status(agents: list[AgentProfile], staging_area: dict = {}) -> str:
    """Helper: Formatear estado de agentes con su status de propuesta."""
    if not agents:
        return "- No agents"
    lines = []
    for a in agents:
        proposal = staging_area.get(a.name)
        if proposal is None:
            status = "no_proposal"
        else:
            status = proposal.status  # approved, rejected, draft
        lines.append(f"- {a.name} ({a.role}) [status: {status}]")
    return "\n".join(lines)


def _format_rejection_history(staging: dict) -> str:
    """Helper: Formatear historial de rechazos."""
    rejections = [
        f"- {agent}: {prop.feedback}"
        for agent, prop in staging.items()
        if prop.status == "rejected"
    ]
    return "\n".join(rejections) if rejections else "- None"


def _format_dependencies(deps: dict) -> str:
    """Helper: Formatear dependencias."""
    if not deps:
        return "- No dependencies"
    lines = [f"- {agent} depends on {', '.join(dep_list)}" for agent, dep_list in deps.items()]
    return "\n".join(lines)


def _format_goal_progress(state: GlobalState) -> str:
    """Helper: Formatear progreso hacia objetivo."""
    num_approved = len([p for p in state.get("staging_area", {}).values() if p.status == "approved"])
    num_agents = len(state.get("active_agents", []))
    return f"{num_approved}/{num_agents} agents approved"




def compile_main_graph(
    genesis_config: GenesisConfig,
    moderator_config: ModeratorConfig,
    integrator_config: IntegratorConfig,
    worker_config: UniversalWorkerConfig,
    context_config: ContextRetrievalConfig,
    synthesizer_config: SynthesizerConfig
) -> StateGraph:
    """
    Compila el main graph listo para ejecución.

    Args:
        genesis_config: Config de Genesis
        moderator_config: Config de Moderator
        integrator_config: Config de Integrator
        worker_config: Config de Universal Worker
        context_config: Config de context retrieval
        synthesizer_config: Config de Synthesizer

    Returns:
        Main graph compilado
    """
    workflow = create_main_graph(
        genesis_config,
        moderator_config,
        integrator_config,
        worker_config,
        context_config,
        synthesizer_config
    )
    return workflow.compile()


# Export
__all__ = ["create_main_graph", "compile_main_graph"]
