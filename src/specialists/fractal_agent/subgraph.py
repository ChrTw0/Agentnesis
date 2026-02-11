"""
Subgrafo Fractal - Bucle Cognitivo Interno (Planner → Executor → Critic).

Este subgrafo es PRIVADO y ejecuta aislado dentro de cada agente.
NO comparte estado con el grafo principal.

Flujo:
1. Planner: Genera plan de ejecución
2. Executor: Ejecuta plan y genera draft
3. Critic: Valida draft
   - Si aprueba → END (retorna draft)
   - Si rechaza → loop back to Planner (con feedback)
   - Si max retries → FORCE_APPROVE → END
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from src.specialists.fractal_agent.schema import InternalAgentState
from src.specialists.fractal_agent.chains import FractalAgentChains


def create_fractal_subgraph(llm: ChatOpenAI) -> StateGraph:
    """
    Crea el subgrafo fractal (Planner → Executor → Critic).

    Args:
        llm: LLM configurado para las chains

    Returns:
        StateGraph compilado del subgrafo fractal
    """
    # Inicializar chains
    chains = FractalAgentChains(llm)

    # Definir nodos
    def planner_node(state: InternalAgentState) -> InternalAgentState:
        """Nodo: Planner - Genera plan de ejecución."""
        result = chains.plan(state)

        # Actualizar estado
        state["plan"] = result["plan"]
        state["current_step"] = 0

        return state

    def executor_node(state: InternalAgentState) -> InternalAgentState:
        """Nodo: Executor - Ejecuta plan y genera draft."""
        result = chains.execute(state)

        # Actualizar estado
        state["draft"] = result["draft"]
        state["structured_data"] = result["structured_data"]
        state["scratchpad"].extend(result.get("scratchpad", []))
        state["spawn_request"] = result.get("spawn_request")
        state["confidence_score"] = result["confidence_score"]

        # Avanzar step
        state["current_step"] += 1

        return state

    def critic_node(state: InternalAgentState) -> InternalAgentState:
        """Nodo: Critic - Valida draft y decide aprobar/revisar."""
        result = chains.critique(state)

        # Actualizar estado
        state["is_complete"] = result["is_complete"]

        # Si rechazó, agregar feedback para próxima iteración
        if not result["is_complete"]:
            feedback_msg = f"Iteration {state['critique_count'] + 1}: {result['feedback']}"
            state["feedback_history"].append(feedback_msg)
            state["critique_count"] += 1

        return state

    def should_continue(state: InternalAgentState) -> Literal["continue", "end"]:
        """
        Conditional edge: Decide si continuar loop o terminar.

        Returns:
            "continue" si debe revisar (loop back to planner)
            "end" si está completo (aprobado o force approved)
        """
        # Si Critic aprobó, terminar
        if state["is_complete"]:
            return "end"

        # Si alcanzó el límite absoluto, forzar aprobación
        if state["critique_count"] >= state["absolute_max_retries"]:
            state["is_complete"] = True
            return "end"

        # Continuar loop
        return "continue"

    # Construir grafo
    workflow = StateGraph(InternalAgentState)

    # Agregar nodos
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("critic", critic_node)

    # Definir edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "critic")

    # Conditional edge desde critic
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "continue": "planner",  # Loop back
            "end": END  # Terminar
        }
    )

    return workflow


def compile_fractal_subgraph(llm: ChatOpenAI) -> StateGraph:
    """
    Compila el subgrafo fractal listo para ejecución.

    Args:
        llm: LLM configurado

    Returns:
        Subgrafo compilado
    """
    workflow = create_fractal_subgraph(llm)
    return workflow.compile()


# Export
__all__ = ["create_fractal_subgraph", "compile_fractal_subgraph"]
