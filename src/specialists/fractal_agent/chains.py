"""
LangChain chains para Fractal Agent (Planner/Executor/Critic).

Chains reutilizables para el bucle cognitivo interno:
1. Planner: Genera plan de ejecución
2. Executor: Ejecuta plan y genera draft
3. Critic: Valida draft y decide aprobar/revisar
"""

import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.specialists.fractal_agent.schema import InternalAgentState
from src.utils.prompt_loader import load_prompt
from src.utils.llm_invoker import invoke_llm
from src.utils.helpers import extract_json


class FractalAgentChains:
    """
    Chains para el subgrafo fractal (bucle cognitivo interno).

    Cada chain corresponde a una fase:
    - Planner: State → plan
    - Executor: State + plan → draft
    - Critic: State + draft → decisión (aprobar/revisar)
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: Instancia de ChatOpenAI configurada
        """
        self.llm = llm

    def plan(self, state: InternalAgentState) -> Dict[str, Any]:
        """
        Chain: Planner - Genera plan de ejecución.

        Args:
            state: InternalAgentState con profile, task, global_context

        Returns:
            Dict con 'plan' (List[str])
        """
        # Cargar prompt del Planner
        planner_prompt = load_prompt(
            "fractal_agent/prompts/planner.txt",
            agent_name=state["profile"].name,
            agent_role=state["profile"].role,
            agent_expertise=", ".join(state["profile"].expertise) if state["profile"].expertise else "general",
            agent_tools=", ".join(state["profile"].tools) if state["profile"].tools else "none",
            task=state["task"],
            global_context=state["global_context"],
            feedback_history="\n".join(state["feedback_history"]) if state["feedback_history"] else "- None"
        )

        # Invocar LLM
        messages = [HumanMessage(content=planner_prompt)]
        response = invoke_llm(self.llm, messages, agent_name="FractalAgent", chain_name="plan")

        # Parse JSON
        try:
            data = extract_json(response.content)
            return {"plan": data["plan"]}
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError(
                f"Failed to parse plan from Planner.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )

    def execute(self, state: InternalAgentState) -> Dict[str, Any]:
        """
        Chain: Executor - Ejecuta plan y genera draft.

        Args:
            state: InternalAgentState con plan y task

        Returns:
            Dict con 'draft', 'structured_data', 'scratchpad', 'spawn_requested', 'spawn_request', 'confidence_score'
        """
        # Cargar prompt del Executor
        executor_prompt = load_prompt(
            "fractal_agent/prompts/executor.txt",
            agent_name=state["profile"].name,
            agent_role=state["profile"].role,
            agent_expertise=", ".join(state["profile"].expertise) if state["profile"].expertise else "general",
            agent_tools=", ".join(state["profile"].tools) if state["profile"].tools else "none",
            task=state["task"],
            plan="\n".join(state["plan"]) if state["plan"] else "- No plan",
            global_context=state["global_context"],
            scratchpad="\n".join(state["scratchpad"]) if state["scratchpad"] else "- Empty",
            current_step=state["current_step"]
        )

        # Invocar LLM
        messages = [HumanMessage(content=executor_prompt)]
        response = invoke_llm(self.llm, messages, agent_name="FractalAgent", chain_name="execute")

        # Parse JSON
        try:
            data = extract_json(response.content)

            return {
                "draft": data["draft"],
                "structured_data": data["structured_data"],
                "scratchpad": data.get("scratchpad", []),
                "spawn_requested": data.get("spawn_requested", False),
                "spawn_request": data.get("spawn_request"),
                "confidence_score": data.get("confidence_score", 0.0)
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError(
                f"Failed to parse execution result from Executor.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )

    def critique(self, state: InternalAgentState) -> Dict[str, Any]:
        """
        Chain: Critic - Valida draft y decide aprobar/revisar.

        Args:
            state: InternalAgentState con draft, plan, critique_count

        Returns:
            Dict con 'is_complete', 'feedback', 'suggested_improvements', 'force_approved'
        """
        # Cargar prompt del Critic
        critic_prompt = load_prompt(
            "fractal_agent/prompts/critic.txt",
            agent_name=state["profile"].name,
            agent_role=state["profile"].role,
            agent_expertise=", ".join(state["profile"].expertise) if state["profile"].expertise else "general",
            task=state["task"],
            draft=state["draft"],
            structured_data=json.dumps(state["structured_data"], indent=2),
            confidence_score=state["confidence_score"],
            global_context=state["global_context"],
            feedback_history="\n".join(state["feedback_history"]) if state["feedback_history"] else "- None",
            critique_count=state["critique_count"],
            max_retries=state["max_retries"],
            absolute_max_retries=state["absolute_max_retries"],
            spawn_requested=state.get("spawn_requested", False)
        )

        # Invocar LLM
        messages = [HumanMessage(content=critic_prompt)]
        response = invoke_llm(self.llm, messages, agent_name="FractalAgent", chain_name="critique")

        # Parse JSON
        try:
            data = extract_json(response.content)

            return {
                "is_complete": data["is_complete"],
                "feedback": data.get("feedback", ""),
                "suggested_improvements": data.get("suggested_improvements", []),
                "force_approved": data.get("force_approved", False)
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError(
                f"Failed to parse critique from Critic.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )


# Export
__all__ = ["FractalAgentChains"]
