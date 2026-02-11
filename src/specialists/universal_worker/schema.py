"""
Schemas específicos del Universal Worker (Agente Polimórfico).

Universal Worker es responsable de:
- Ejecutar cualquier rol de agente dinámicamente
- Invocar el subgrafo fractal con aislamiento
- Extraer contexto relevante del Knowledge Graph
"""

from typing import Optional
from pydantic import BaseModel, Field

from src.core.states.schemas import SpawnRequest


class WorkerExecutionResult(BaseModel):
    """
    Resultado de la ejecución del Universal Worker.

    Encapsula el output del subgrafo fractal.
    """
    agent_name: str = Field(..., description="Agente que ejecutó")
    draft: str = Field(..., description="Propuesta generada por el agente")
    structured_data: dict = Field(
        default_factory=dict,
        description="Datos estructurados extraídos del draft"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Auto-evaluación de calidad (0-1)"
    )
    internal_iterations: int = Field(
        default=0,
        ge=0,
        description="Número de iteraciones internas (Planner→Executor→Critic)"
    )
    spawn_requested: bool = Field(
        default=False,
        description="Si el agente solicitó spawn de otro agente"
    )
    spawn_request: Optional[SpawnRequest] = Field(
        default=None,
        description="Datos de la SpawnRequest (si spawn_requested=True)"
    )
    error: Optional[str] = Field(
        None,
        description="Mensaje de error si la ejecución falló"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "BackendDev_001",
                "draft": "Implementé el endpoint POST /users con FastAPI...",
                "structured_data": {
                    "entities": {
                        "endpoint_users": {"type": "API_Endpoint", "properties": {}}
                    },
                    "relations": []
                },
                "confidence_score": 0.85,
                "internal_iterations": 3,
                "spawn_requested": False,
                "error": None
            }
        }


class ContextRetrievalConfig(BaseModel):
    """
    Configuración para la recuperación de contexto del Knowledge Graph.

    Controla el RAG selectivo para no saturar contexto del LLM.
    """
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Máximo número de items a recuperar del KG"
    )
    use_embeddings: bool = Field(
        default=False,
        description="Usar embeddings para retrieval semántico (vs. top-k simple)"
    )
    min_relevance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Score mínimo de relevancia (solo si use_embeddings=True)"
    )
    include_relations: bool = Field(
        default=True,
        description="Incluir relaciones en el contexto (además de entidades)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "top_k": 10,
                "use_embeddings": False,
                "min_relevance_score": 0.5,
                "include_relations": True
            }
        }


class UniversalWorkerConfig(BaseModel):
    """
    Configuración de comportamiento del Universal Worker.

    Controla timeouts y manejo de errores.
    """
    model_name: Optional[str] = Field(
        default=None,
        description="Modelo LLM default para agentes spawneados (None = usa default global)"
    )
    execution_timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Timeout en segundos para la ejecución del subgrafo"
    )
    max_retries_on_error: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Número de reintentos si el subgrafo falla"
    )
    cache_subgraphs: bool = Field(
        default=True,
        description="Cachear subgrafos compilados por perfil"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "execution_timeout": 120,
                "max_retries_on_error": 1,
                "cache_subgraphs": True
            }
        }


# Exports
__all__ = [
    "WorkerExecutionResult",
    "ContextRetrievalConfig",
    "UniversalWorkerConfig"
]
