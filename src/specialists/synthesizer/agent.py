"""
Synthesizer Agent - Generador de Respuesta Final.

Responsabilidades:
1. Consolidar Knowledge Graph en respuesta coherente
2. Formatear output según dominio y configuración
3. Generar resumen ejecutivo para el usuario
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI

from src.core.states.schemas import Proposal
from src.specialists.synthesizer.schema import SynthesisResult, SynthesizerConfig
from src.specialists.synthesizer.chains import SynthesizerChains


class SynthesizerAgent:
    """
    Synthesizer - Agente de síntesis final.

    Orquesta la chain del Synthesizer y formatea el output final.
    """

    def __init__(self, config: SynthesizerConfig, llm: ChatOpenAI):
        """
        Args:
            config: Configuración del Synthesizer
            llm: LLM configurado (OpenAI/OpenRouter)
        """
        self.config = config
        self.llm = llm
        self.name = "Synthesizer"

        # Inicializar chains
        self.chains = SynthesizerChains(llm)

    def synthesize_final_output(
        self,
        user_query: str,
        domain: str,
        kg_entities: Dict[str, Any],
        kg_relations: List[Dict[str, str]],
        staging_area: Dict[str, Proposal],
        active_agents: List,
        num_iterations: int
    ) -> SynthesisResult:
        """
        Sintetiza el Knowledge Graph en respuesta final.

        Args:
            user_query: Query original del usuario
            domain: Dominio detectado
            kg_entities: Entidades del Knowledge Graph
            kg_relations: Relaciones del Knowledge Graph
            staging_area: Área de staging con propuestas
            active_agents: Lista de agentes activos
            num_iterations: Número de iteraciones

        Returns:
            SynthesisResult con respuesta consolidada
        """
        # Formatear KG como texto
        kg_entities_str = self._format_entities(kg_entities)
        kg_relations_str = self._format_relations(kg_relations)

        # Formatear propuestas aprobadas
        approved_proposals_str = self._format_approved_proposals(staging_area)

        # Formatear lista de agentes
        agents_list_str = self._format_agents(active_agents)

        # Invocar chain
        return self.chains.synthesize(
            user_query=user_query,
            domain=domain,
            kg_entities=kg_entities_str,
            kg_relations=kg_relations_str,
            approved_proposals=approved_proposals_str,
            agents_list=agents_list_str,
            num_iterations=num_iterations,
            output_format=self.config.output_format,
            include_kg_dump=self.config.include_kg_dump,
            verbosity=self.config.verbosity
        )

    def _format_entities(self, entities: Dict[str, Any]) -> str:
        """Helper: Formatear entidades del KG."""
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
        """Helper: Formatear relaciones del KG."""
        if not relations:
            return "- None"

        lines = []
        for rel in relations:
            source = rel.get("source", "?")
            rel_type = rel.get("rel", "?")
            target = rel.get("target", "?")
            lines.append(f"- {source} --[{rel_type}]--> {target}")

        return "\n".join(lines)

    def _format_approved_proposals(self, staging: Dict[str, Proposal]) -> str:
        """Helper: Formatear propuestas aprobadas."""
        approved = [
            f"- {agent}: {proposal.content}"
            for agent, proposal in staging.items()
            if proposal.status == "approved"
        ]
        return "\n".join(approved) if approved else "- None"

    def _format_agents(self, agents: List) -> str:
        """Helper: Formatear lista de agentes."""
        if not agents:
            return "- None"

        lines = [f"- {agent.name} ({agent.role})" for agent in agents]
        return "\n".join(lines)


# Export
__all__ = ["SynthesizerAgent"]
