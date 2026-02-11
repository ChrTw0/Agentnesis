"""
Core States Module

Exporta todos los estados y schemas del sistema:
- GlobalState: Estado principal que circula por el grafo
- AgentProfile, Proposal, SpawnRequest: Schemas compartidos
- Reducers: merge_staging_area, merge_knowledge_graph
"""

from .global_state import GlobalState
from .schemas import AgentProfile, Proposal, SpawnRequest
from .reducers import merge_staging_area, merge_knowledge_graph

__all__ = [
    # Estados
    "GlobalState",
    # Schemas
    "AgentProfile",
    "Proposal",
    "SpawnRequest",
    # Reducers
    "merge_staging_area",
    "merge_knowledge_graph",
]
