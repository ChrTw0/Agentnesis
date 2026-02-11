"""
Reducers personalizados para el merge de estados en LangGraph.

Estos reducers se usan con Annotated en GlobalState para evitar
que los updates sobrescriban completamente los campos.

Ejemplo de uso en GlobalState:
    staging_area: Annotated[Dict[str, Proposal], merge_staging_area]
    knowledge_graph: Annotated[Dict[str, Any], merge_knowledge_graph]
"""

from typing import Dict, Any, List
from .schemas import Proposal, AgentProfile


def merge_staging_area(
    existing: Dict[str, Proposal],
    new: Dict[str, Proposal]
) -> Dict[str, Proposal]:
    """
    Merge inteligente del Staging Area.

    Comportamiento:
    - Si un agente envía nueva propuesta → ACTUALIZA su entrada
    - Si es un agente nuevo → AGREGA la entrada
    - NO borra propuestas de otros agentes

    Args:
        existing: Staging area actual del estado
        new: Nuevas propuestas a mergear

    Returns:
        Dict mergeado con todas las propuestas actualizadas

    Ejemplo:
        existing = {
            "Agent_A": Proposal(content="v1", status="draft"),
            "Agent_B": Proposal(content="v1", status="approved")
        }
        new = {
            "Agent_A": Proposal(content="v2", status="draft")
        }
        result = merge_staging_area(existing, new)
        # result = {
        #     "Agent_A": Proposal(content="v2", status="draft"),  # Actualizado
        #     "Agent_B": Proposal(content="v1", status="approved") # Preservado
        # }
    """
    # Copia defensiva del estado actual
    merged = dict(existing) if existing else {}

    # Mergear nuevas propuestas
    for agent_name, proposal in (new or {}).items():
        merged[agent_name] = proposal

    return merged


def merge_knowledge_graph(
    existing: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge inteligente del Knowledge Graph.

    Comportamiento:
    - Agrega nuevas entidades (evita duplicados por ID)
    - Agrega nuevas relaciones (evita duplicados por tripla)
    - Preserva entidades y relaciones existentes
    - Si una entidad ya existe, mergea sus propiedades

    Estructura esperada:
    {
        "entities": {
            "entity_id": {"type": "...", "properties": {...}}
        },
        "relations": [
            {"source": "...", "rel": "...", "target": "..."}
        ]
    }

    Args:
        existing: Knowledge Graph actual
        new: Nuevos datos a mergear

    Returns:
        Knowledge Graph mergeado

    Ejemplo:
        existing = {
            "entities": {
                "backend": {"type": "Service", "properties": {"lang": "Python"}}
            },
            "relations": [
                {"source": "backend", "rel": "uses", "target": "fastapi"}
            ]
        }
        new = {
            "entities": {
                "backend": {"type": "Service", "properties": {"version": "3.11"}},
                "db": {"type": "Database", "properties": {"engine": "PostgreSQL"}}
            },
            "relations": [
                {"source": "backend", "rel": "connects_to", "target": "db"}
            ]
        }
        result = merge_knowledge_graph(existing, new)
        # result = {
        #     "entities": {
        #         "backend": {
        #             "type": "Service",
        #             "properties": {"lang": "Python", "version": "3.11"}  # Merged
        #         },
        #         "db": {"type": "Database", "properties": {"engine": "PostgreSQL"}}
        #     },
        #     "relations": [
        #         {"source": "backend", "rel": "uses", "target": "fastapi"},
        #         {"source": "backend", "rel": "connects_to", "target": "db"}
        #     ]
        # }
    """
    # Inicializar estructura si existing está vacío
    merged = {
        "entities": dict(existing.get("entities", {}) if existing else {}),
        "relations": list(existing.get("relations", []) if existing else [])
    }

    # Si new está vacío, retornar existing
    if not new:
        return merged

    # --- MERGE ENTIDADES ---
    new_entities = new.get("entities", {})
    for entity_id, entity_data in new_entities.items():
        if entity_id not in merged["entities"]:
            # Nueva entidad → agregar completa
            merged["entities"][entity_id] = entity_data
        else:
            # Entidad existente → mergear properties
            existing_entity = merged["entities"][entity_id]

            # Mantener type (el primero tiene precedencia)
            merged_type = existing_entity.get("type", entity_data.get("type"))

            # Mergear properties
            existing_props = existing_entity.get("properties", {})
            new_props = entity_data.get("properties", {})
            merged_props = {**existing_props, **new_props}

            merged["entities"][entity_id] = {
                "type": merged_type,
                "properties": merged_props
            }

    # --- MERGE RELACIONES (evitar duplicados) ---
    # Crear set de relaciones existentes para búsqueda rápida
    existing_rels_set = set(
        (r["source"], r["rel"], r["target"])
        for r in merged["relations"]
    )

    # Agregar nuevas relaciones si no existen
    new_relations = new.get("relations", [])
    for rel in new_relations:
        rel_tuple = (rel["source"], rel["rel"], rel["target"])
        if rel_tuple not in existing_rels_set:
            merged["relations"].append(rel)
            existing_rels_set.add(rel_tuple)

    return merged


def merge_active_agents(
    existing: List[AgentProfile],
    new: List[AgentProfile]
) -> List[AgentProfile]:
    """
    Merge inteligente de la lista de agentes activos.

    Comportamiento:
    - Si un agente ya existe (por name) → REEMPLAZA su perfil
    - Si es un agente nuevo → AGREGA
    - NO duplica agentes aunque los nodos retornen la lista completa

    Args:
        existing: Lista de agentes actual
        new: Nueva lista de agentes a mergear

    Returns:
        Lista mergeada sin duplicados por name
    """
    merged = {agent.name: agent for agent in (existing or [])}
    for agent in (new or []):
        merged[agent.name] = agent
    return list(merged.values())


# Exports
__all__ = ["merge_staging_area", "merge_knowledge_graph", "merge_active_agents"]
