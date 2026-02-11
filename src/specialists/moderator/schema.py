"""
Schemas específicos del Moderator (Gestor de Turnos).

Moderator es responsable de:
- Decidir quién habla en cada turno
- Detectar deadlocks
- Gestionar prioridades y dependencias
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class TurnDecision(BaseModel):
    """
    Decisión del Moderator sobre el próximo turno.

    Resultado del análisis de prioridades y estado actual.
    """
    next_speaker: str = Field(..., description="Quién tiene el turno ('INTEGRATOR', 'HUMAN', 'FINISH', o nombre de agente)")
    reason: str = Field(..., description="Razón de la decisión")
    priority: Literal["critical", "high", "normal", "low"] = Field(
        default="normal",
        description="Prioridad de este turno"
    )
    blocked_agents: List[str] = Field(
        default_factory=list,
        description="Agentes bloqueados por dependencias"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "next_speaker": "BackendDev_001",
                "reason": "Agente rechazado anteriormente, tiene prioridad para corregir",
                "priority": "high",
                "blocked_agents": ["Frontend_001"]
            }
        }


class DeadlockInfo(BaseModel):
    """
    Información sobre un deadlock detectado.

    Usado para solicitar intervención humana.
    """
    deadlock_type: Literal["max_iterations", "rejection_loop", "circular_dependency", "spawn_failure"]
    description: str = Field(..., description="Descripción del deadlock")
    involved_agents: List[str] = Field(default_factory=list, description="Agentes involucrados")
    suggested_action: str = Field(..., description="Acción sugerida para resolver")

    class Config:
        json_schema_extra = {
            "example": {
                "deadlock_type": "rejection_loop",
                "description": "BackendDev_001 ha sido rechazado 3 veces consecutivas",
                "involved_agents": ["BackendDev_001"],
                "suggested_action": "Revisar feedback del Integrator y ajustar propuesta manualmente"
            }
        }


class ModeratorConfig(BaseModel):
    """
    Configuración de comportamiento del Moderator.

    Controla límites y políticas de orquestación.
    """
    model_name: Optional[str] = Field(
        default=None,
        description="Modelo LLM para Moderator (None = usa default global)"
    )
    max_iterations: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Máximo de iteraciones antes de deadlock"
    )
    rejection_loop_threshold: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Número de rechazos consecutivos antes de deadlock"
    )
    enable_human_override: bool = Field(
        default=True,
        description="Permitir intervención humana en deadlocks"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "max_iterations": 20,
                "rejection_loop_threshold": 3,
                "enable_human_override": True
            }
        }


# Exports
__all__ = ["TurnDecision", "DeadlockInfo", "ModeratorConfig"]
