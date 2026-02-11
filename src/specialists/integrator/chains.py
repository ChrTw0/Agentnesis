"""
LangChain chains para Integrator.

Chain reutilizable para:
- Validación de propuestas (Proposal + KG → ValidationResult)
"""

import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.specialists.integrator.schema import ValidationResult
from src.utils.prompt_loader import load_prompt
from src.utils.llm_invoker import invoke_llm
from src.utils.helpers import extract_json


class IntegratorChains:
    """
    Chains de LangChain para Integrator.

    Encapsula la lógica de prompt + LLM + parsing.
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: Instancia de ChatOpenAI configurada
        """
        self.llm = llm
        self.system_prompt = load_prompt("integrator/system_prompt.txt")

    def validate_proposal(
        self,
        agent_name: str,
        agent_role: str,
        agent_expertise: List[str],
        iteration: int,
        content: str,
        structured_data: Dict[str, Any],
        kg_entities: str,
        kg_relations: str,
        recent_approvals_summary: str,
        strict_mode: bool,
        allow_property_override: bool,
        max_conflicts_per_proposal: int
    ) -> ValidationResult:
        """
        Chain: Validación de propuesta contra Knowledge Graph.

        Args:
            agent_name: Nombre del agente
            agent_role: Rol del agente
            agent_expertise: Expertise del agente
            iteration: Número de iteración
            content: Contenido textual de la propuesta
            structured_data: Datos estructurados (entities, relations)
            kg_entities: Entidades actuales del KG (formato texto)
            kg_relations: Relaciones actuales del KG (formato texto)
            recent_approvals_summary: Resumen de aprobaciones recientes
            strict_mode: Si es strict o no
            allow_property_override: Permitir override de properties
            max_conflicts_per_proposal: Máximo de conflictos a reportar

        Returns:
            ValidationResult con veredicto y feedback
        """
        # Formatear expertise
        expertise_str = ", ".join(agent_expertise) if agent_expertise else "general"

        # Formatear structured_data como JSON
        structured_data_str = json.dumps(structured_data, indent=2)

        # Cargar task prompt
        task_prompt = load_prompt(
            "integrator/task_validate_proposal.txt",
            agent_name=agent_name,
            agent_role=agent_role,
            agent_expertise=expertise_str,
            iteration=iteration,
            content=content,
            structured_data=structured_data_str,
            kg_entities=kg_entities,
            kg_relations=kg_relations,
            recent_approvals_summary=recent_approvals_summary,
            strict_mode=str(strict_mode),
            allow_property_override=str(allow_property_override),
            max_conflicts_per_proposal=max_conflicts_per_proposal
        )

        # Construir mensajes
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task_prompt)
        ]

        # Invocar LLM
        response = invoke_llm(self.llm, messages, agent_name="Integrator", chain_name="validate_proposal")

        # Parse JSON
        try:
            data = extract_json(response.content)
            return ValidationResult(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse ValidationResult from LLM response.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )


# Export
__all__ = ["IntegratorChains"]
