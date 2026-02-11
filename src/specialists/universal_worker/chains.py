"""
LangChain chains para Universal Worker.

Universal Worker es especial: no tiene chain directo, sino que
orquesta la invocación del subgrafo fractal (Planner → Executor → Critic).

Este archivo define helpers para preparar inputs al subgrafo.
"""

from typing import List, Dict, Any
from src.core.states.schemas import AgentProfile
from src.utils.prompt_loader import load_prompt


class UniversalWorkerChains:
    """
    Helpers para Universal Worker.

    No usa chains típicos (system+user prompt → LLM → parse).
    En cambio, prepara contexto para el subgrafo fractal.
    """

    def __init__(self):
        """
        Universal Worker no necesita LLM propio.
        Delega todo al subgrafo fractal.
        """
        self.system_prompt = load_prompt("universal_worker/system_prompt.txt")

    def prepare_execution_context(
        self,
        agent_profile: AgentProfile,
        user_query: str,
        agent_task: str,
        kg_entities: str,
        kg_relations: str,
        recent_activity: str,
        dependencies_status: str,
        execution_timeout: int,
        max_retries_on_error: int
    ) -> Dict[str, Any]:
        """
        Prepara contexto para ejecutar el subgrafo fractal.

        Args:
            agent_profile: Perfil del agente (con system_prompt inner layer)
            user_query: Query original del usuario
            agent_task: Tarea específica asignada a este agente
            kg_entities: Entidades del Knowledge Graph
            kg_relations: Relaciones del Knowledge Graph
            recent_activity: Actividad reciente del sistema
            dependencies_status: Estado de dependencias
            execution_timeout: Timeout en segundos
            max_retries_on_error: Número de reintentos

        Returns:
            Dict con todo el contexto formateado para el subgrafo
        """
        # Formatear expertise
        expertise_str = ", ".join(agent_profile.expertise) if agent_profile.expertise else "general"

        # Formatear KG context
        kg_context = f"Entities:\n{kg_entities}\n\nRelations:\n{kg_relations}"

        # Cargar task prompt (OUTER LAYER)
        task_prompt = load_prompt(
            "universal_worker/task_execute_work.txt",
            agent_name=agent_profile.name,
            agent_role=agent_profile.role,
            agent_expertise=expertise_str,
            spawn_depth=agent_profile.spawn_depth,
            spawned_by=agent_profile.spawned_by,
            agent_system_prompt=agent_profile.system_prompt,  # INNER LAYER
            user_query=user_query,
            agent_task=agent_task,
            kg_context=kg_context,
            kg_entities=kg_entities,
            kg_relations=kg_relations,
            recent_activity=recent_activity,
            dependencies_status=dependencies_status,
            execution_timeout=execution_timeout,
            max_retries_on_error=max_retries_on_error
        )

        return {
            "system_prompt": self.system_prompt,
            "task_prompt": task_prompt,
            "agent_profile": agent_profile,
            "user_query": user_query,
            "agent_task": agent_task,
            "kg_context": f"{kg_entities}\n\n{kg_relations}",
            "execution_timeout": execution_timeout,
            "max_retries_on_error": max_retries_on_error
        }

    def extract_kg_context(
        self,
        kg_entities: Dict[str, Any],
        kg_relations: List[Dict[str, str]],
        agent_profile: AgentProfile,
        top_k: int = 10
    ) -> tuple[str, str]:
        """
        Extrae contexto relevante del Knowledge Graph para el agente.

        Args:
            kg_entities: Entidades del KG
            kg_relations: Relaciones del KG
            agent_profile: Perfil del agente (para filtrar relevancia)
            top_k: Máximo número de items a incluir

        Returns:
            Tuple (entities_str, relations_str) formateados como texto
        """
        # TODO: Implementar RAG inteligente basado en expertise
        # Por ahora, retornar todo (o top_k items)

        # Formatear entities
        entities_lines = []
        for entity_id, entity_data in list(kg_entities.items())[:top_k]:
            entities_lines.append(f"- {entity_id}: {entity_data}")
        entities_str = "\n".join(entities_lines) if entities_lines else "- None"

        # Formatear relations
        relations_lines = []
        for rel in kg_relations[:top_k]:
            relations_lines.append(
                f"- {rel.get('source')} --[{rel.get('rel')}]--> {rel.get('target')}"
            )
        relations_str = "\n".join(relations_lines) if relations_lines else "- None"

        return entities_str, relations_str


# Export
__all__ = ["UniversalWorkerChains"]
