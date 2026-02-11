"""
LangChain chains para Synthesizer.

Chain reutilizable para:
- Síntesis final (KG + Proposals → SynthesisResult)
"""

import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.specialists.synthesizer.schema import SynthesisResult
from src.utils.prompt_loader import load_prompt
from src.utils.llm_invoker import invoke_llm
from src.utils.helpers import extract_json


class SynthesizerChains:
    """
    Chains de LangChain para Synthesizer.

    Encapsula la lógica de prompt + LLM + parsing.
    """

    def __init__(self, llm: ChatOpenAI):
        """
        Args:
            llm: Instancia de ChatOpenAI configurada
        """
        self.llm = llm
        self.system_prompt = load_prompt("synthesizer/system_prompt.txt")

    def synthesize(
        self,
        user_query: str,
        domain: str,
        kg_entities: str,
        kg_relations: str,
        approved_proposals: str,
        agents_list: str,
        num_iterations: int,
        output_format: str,
        include_kg_dump: bool,
        verbosity: str
    ) -> SynthesisResult:
        """
        Chain: Síntesis final del Knowledge Graph.

        Args:
            user_query: Query original del usuario
            domain: Dominio detectado
            kg_entities: Entidades del KG (formato texto)
            kg_relations: Relaciones del KG (formato texto)
            approved_proposals: Propuestas aprobadas (formato texto)
            agents_list: Lista de agentes participantes
            num_iterations: Número de iteraciones
            output_format: Formato de output (prose/structured/markdown)
            include_kg_dump: Si incluir dump del KG
            verbosity: Nivel de detalle (concise/normal/detailed)

        Returns:
            SynthesisResult con respuesta final consolidada
        """
        # Cargar prompt base
        task_base = load_prompt(
            "synthesizer/task_base.txt",
            user_query=user_query,
            domain=domain,
            kg_entities=kg_entities,
            kg_relations=kg_relations,
            approved_proposals=approved_proposals,
            agents_list=agents_list,
            num_iterations=num_iterations
        )

        # Cargar instrucciones de formato
        format_instructions = load_prompt(f"synthesizer/formats/{output_format}.txt")

        # Cargar instrucciones de verbosity
        verbosity_instructions = load_prompt(f"synthesizer/verbosity/{verbosity}.txt")

        # Componer prompt final
        task_prompt = f"{task_base}\n\n{format_instructions}\n\n{verbosity_instructions}"

        # Agregar instrucción de KG dump si es necesario
        if include_kg_dump:
            task_prompt += "\n\n## Additional Requirement\nInclude a complete dump of the Knowledge Graph at the end of your response in a clearly marked section."

        # Construir mensajes
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=task_prompt)
        ]

        # Invocar LLM
        response = invoke_llm(self.llm, messages, agent_name="Synthesizer", chain_name="synthesize")

        # Parse JSON
        try:
            data = extract_json(response.content)
            return SynthesisResult(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse SynthesisResult from LLM response.\n"
                f"Error: {e}\n"
                f"Response: {response.content}"
            )


# Export
__all__ = ["SynthesizerChains"]
