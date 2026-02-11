"""
Schemas específicos del Integrator (Validador de Coherencia).

Integrator es responsable de:
- Validar propuestas
- Detectar conflictos
- Actualizar el Knowledge Graph
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """
    Resultado de validación de una propuesta por el Integrator.

    Contiene el veredicto y feedback detallado.
    """
    agent_name: str = Field(..., description="Agente cuya propuesta se validó")
    is_valid: bool = Field(..., description="Si la propuesta es válida")
    status: Literal["approved", "rejected"] = Field(..., description="Decisión final")
    feedback: str = Field(default="", description="Feedback para el agente")
    conflicts: List[str] = Field(
        default_factory=list,
        description="Lista de conflictos detectados (si rejected)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confianza en la validación (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "BackendDev_001",
                "is_valid": False,
                "status": "rejected",
                "feedback": "Conflicto detectado: DBAdmin ya aprobó PostgreSQL pero propuesta usa MongoDB",
                "conflicts": ["database_choice"],
                "confidence": 0.95
            }
        }


class ConflictReport(BaseModel):
    """
    Reporte detallado de un conflicto detectado.

    Usado para debugging y feedback específico.
    """
    conflict_type: Literal["technical", "semantic", "temporal", "scope"]
    description: str = Field(..., description="Descripción del conflicto")
    involved_entities: List[str] = Field(
        default_factory=list,
        description="Entidades del KG involucradas"
    )
    severity: Literal["critical", "high", "medium", "low"] = Field(
        default="medium",
        description="Severidad del conflicto"
    )
    suggested_resolution: Optional[str] = Field(
        None,
        description="Sugerencia para resolver el conflicto"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conflict_type": "technical",
                "description": "Backend propone Python 3.12 pero DevOps soporta solo 3.9",
                "involved_entities": ["backend_runtime", "deployment_env"],
                "severity": "high",
                "suggested_resolution": "Usar Python 3.10 como compromiso o actualizar ambiente de deployment"
            }
        }


class KnowledgeGraphUpdate(BaseModel):
    """
    Update estructurado del Knowledge Graph.

    Representa cambios aprobados para commitear.
    """
    entities_added: Dict[str, Any] = Field(
        default_factory=dict,
        description="Nuevas entidades agregadas"
    )
    entities_updated: Dict[str, Any] = Field(
        default_factory=dict,
        description="Entidades existentes modificadas"
    )
    relations_added: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Nuevas relaciones agregadas"
    )
    source_agent: str = Field(..., description="Agente que generó estos cambios")

    class Config:
        json_schema_extra = {
            "example": {
                "entities_added": {
                    "endpoint_users": {
                        "type": "API_Endpoint",
                        "properties": {"method": "POST", "path": "/users"}
                    }
                },
                "entities_updated": {},
                "relations_added": [
                    {"source": "backend", "rel": "implements", "target": "endpoint_users"}
                ],
                "source_agent": "BackendDev_001"
            }
        }


class IntegratorConfig(BaseModel):
    """
    Configuración de comportamiento del Integrator.

    Controla strictness y políticas de validación.
    """
    model_name: Optional[str] = Field(
        default=None,
        description="Modelo LLM para Integrator (None = usa default global)"
    )
    strict_mode: bool = Field(
        default=False,
        description="Si True, rechaza propuestas ante mínima inconsistencia"
    )
    allow_property_override: bool = Field(
        default=True,
        description="Permitir que propuestas sobrescriban properties de entidades existentes"
    )
    max_conflicts_per_proposal: int = Field(
        default=5,
        ge=1,
        description="Máximo de conflictos a reportar por propuesta"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strict_mode": False,
                "allow_property_override": True,
                "max_conflicts_per_proposal": 5
            }
        }


# Exports
__all__ = [
    "ValidationResult",
    "ConflictReport",
    "KnowledgeGraphUpdate",
    "IntegratorConfig"
]
