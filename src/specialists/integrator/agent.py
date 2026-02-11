"""
Integrator Agent - Validador de Coherencia.

Responsabilidades:
1. Validar propuestas contra Knowledge Graph
2. Detectar conflictos
3. Actualizar Knowledge Graph con propuestas aprobadas
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI

from src.core.states.schemas import AgentProfile, Proposal
from src.specialists.integrator.schema import ValidationResult, IntegratorConfig, KnowledgeGraphUpdate
from src.specialists.integrator.chains import IntegratorChains


class IntegratorAgent:
    """
    Integrator - Guardián de la coherencia del Knowledge Graph.

    Orquesta las chains del Integrator y maneja la lógica de negocio:
    - Validación de propuestas
    - Detección de conflictos
    - Actualización del KG
    """

    def __init__(self, config: IntegratorConfig, llm: ChatOpenAI):
        """
        Args:
            config: Configuración del Integrator
            llm: LLM configurado (OpenAI/OpenRouter)
        """
        self.config = config
        self.llm = llm
        self.name = "Integrator"

        # Inicializar chains
        self.chains = IntegratorChains(llm)

    def validate_proposal(
        self,
        proposal: Proposal,
        agent_profile: AgentProfile,
        kg_entities: Dict[str, Any],
        kg_relations: List[Dict[str, str]],
        recent_approvals: List[str]
    ) -> ValidationResult:
        """
        Valida una propuesta contra el Knowledge Graph.

        Args:
            proposal: Propuesta del agente
            agent_profile: Perfil del agente que hizo la propuesta
            kg_entities: Entidades actuales del KG
            kg_relations: Relaciones actuales del KG
            recent_approvals: Resumen de aprobaciones recientes

        Returns:
            ValidationResult con veredicto y feedback
        """
        # Rechazar propuestas vacías antes de consultar al LLM
        has_content = bool(proposal.content and proposal.content.strip())
        has_structured = bool(
            proposal.structured_data.get("entities") or proposal.structured_data.get("relations")
        )
        if not has_content and not has_structured:
            return ValidationResult(
                agent_name=proposal.agent_name,
                is_valid=False,
                status="rejected",
                feedback="Proposal contains no content and no structured data. Agent must provide at least a draft or entities/relations.",
                conflicts=["empty_proposal"],
                confidence=1.0
            )

        # Formatear KG como texto
        kg_entities_str = self._format_entities(kg_entities)
        kg_relations_str = self._format_relations(kg_relations)
        recent_approvals_str = "\n".join(recent_approvals) if recent_approvals else "- None"

        return self.chains.validate_proposal(
            agent_name=proposal.agent_name,
            agent_role=agent_profile.role,
            agent_expertise=agent_profile.expertise,
            iteration=proposal.iteration,
            content=proposal.content,
            structured_data=proposal.structured_data,
            kg_entities=kg_entities_str,
            kg_relations=kg_relations_str,
            recent_approvals_summary=recent_approvals_str,
            strict_mode=self.config.strict_mode,
            allow_property_override=self.config.allow_property_override,
            max_conflicts_per_proposal=self.config.max_conflicts_per_proposal
        )

    def create_kg_update(
        self,
        proposal: Proposal,
        validation: ValidationResult
    ) -> KnowledgeGraphUpdate:
        """
        Crea un KnowledgeGraphUpdate a partir de una propuesta aprobada.

        Args:
            proposal: Propuesta aprobada
            validation: Resultado de validación

        Returns:
            KnowledgeGraphUpdate para commitear al KG
        """
        if validation.status != "approved":
            raise ValueError("Cannot create KG update from rejected proposal")

        # Extraer entities y relations del structured_data
        structured_data = proposal.structured_data
        entities_added = structured_data.get("entities", {})
        relations_added = structured_data.get("relations", [])

        return KnowledgeGraphUpdate(
            entities_added=entities_added,
            entities_updated={},  # TODO: Detectar updates vs adds
            relations_added=relations_added,
            source_agent=proposal.agent_name
        )

    def _format_entities(self, entities: Dict[str, Any]) -> str:
        """Helper: Formatear entidades del KG como texto."""
        if not entities:
            return "- None"

        lines = []
        for entity_id, entity_data in entities.items():
            entity_type = entity_data.get("type", "Unknown")
            properties = entity_data.get("properties", {})
            props_str = ", ".join([f"{k}={v}" for k, v in properties.items()])
            lines.append(f"- {entity_id} (type={entity_type}, props=[{props_str}])")

        return "\n".join(lines)

    def _format_relations(self, relations: List[Dict[str, str]]) -> str:
        """Helper: Formatear relaciones del KG como texto."""
        if not relations:
            return "- None"

        lines = []
        for rel in relations:
            source = rel.get("source", "?")
            rel_type = rel.get("rel", "?")
            target = rel.get("target", "?")
            lines.append(f"- {source} --[{rel_type}]--> {target}")

        return "\n".join(lines)


# Export
__all__ = ["IntegratorAgent"]
