"""
Schemas específicos de Genesis (Meta-Cognición y Spawning).

Genesis es responsable de:
- Analizar el dominio del problema
- Crear agentes iniciales
- Procesar spawn requests dinámicamente
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class DomainAnalysis(BaseModel):
    """
    Resultado del análisis de dominio por Genesis.

    Genesis analiza user_query para determinar qué agentes crear.
    """
    domain: str = Field(..., description="Dominio identificado (ej: 'Software Engineering', 'Legal')")
    complexity: str = Field(..., description="Nivel de complejidad: 'simple', 'medium', 'complex'")
    required_roles: List[str] = Field(
        default_factory=list,
        description="Roles necesarios identificados (ej: ['Backend Dev', 'DB Admin'])"
    )
    reasoning: str = Field(..., description="Razonamiento del análisis")

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "Software Engineering",
                "complexity": "medium",
                "required_roles": ["Backend Developer", "Database Administrator"],
                "reasoning": "El usuario solicita crear una API REST con base de datos, requiere expertise en backend y bases de datos."
            }
        }


class SpawnDecision(BaseModel):
    """
    Decisión inteligente de Genesis sobre una SpawnRequest.

    Genesis considera contexto completo:
    - Saturación del sistema (num agentes, requests pendientes)
    - Spawn depth del requester (prevenir recursión)
    - Existencia de agentes con expertise similar (reutilización)
    - Necesidad real vs redundancia

    Decisiones posibles:
    1. should_spawn=True → Crear nuevo agente (agent_name proporcionado)
    2. should_spawn=False + existing_agent → Reusar agente existente
    3. should_spawn=False + existing_agent=None → Rechazar (saturación/innecesario)
    """
    should_spawn: bool = Field(..., description="Si debe crear el agente")
    agent_name: Optional[str] = Field(
        None,
        description="Nombre del agente a crear (si should_spawn=True)"
    )
    existing_agent: Optional[str] = Field(
        None,
        description="Nombre del agente existente que puede hacer el trabajo (si reutilización)"
    )
    reasoning: str = Field(..., description="Justificación detallada de la decisión")
    spawn_depth: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Profundidad del nuevo agente en árbol de spawning"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "should_spawn": False,
                "agent_name": None,
                "existing_agent": "LegalAdvisor_001",
                "reasoning": "Ya existe LegalAdvisor_001 con expertise en GDPR. Reutilizar ese agente.",
                "spawn_depth": 0
            }
        }


class GenesisConfig(BaseModel):
    """
    Configuración de comportamiento de Genesis.

    Controla los límites y políticas de spawning inteligente.
    """
    model_name: Optional[str] = Field(
        default=None,
        description="Modelo LLM para Genesis (None = usa default global)"
    )
    max_agents: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Máximo número de agentes permitidos en el sistema"
    )
    max_spawn_depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Límite hard de spawn depth (guardrail de emergencia). None = Genesis decide inteligentemente"
    )
    allow_dynamic_spawn: bool = Field(
        default=True,
        description="Permitir spawning dinámico durante ejecución"
    )
    spawn_cooldown: int = Field(
        default=0,
        ge=0,
        description="Turnos mínimos entre spawns consecutivos"
    )
    enable_agent_reuse: bool = Field(
        default=True,
        description="Intentar reusar agentes existentes antes de crear nuevos"
    )
    saturation_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Umbral de saturación (% de max_agents) para rechazar spawns no críticos"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "max_agents": 10,
                "max_spawn_depth": None,
                "allow_dynamic_spawn": True,
                "spawn_cooldown": 0,
                "enable_agent_reuse": True,
                "saturation_threshold": 0.8
            }
        }


# Exports
__all__ = ["DomainAnalysis", "SpawnDecision", "GenesisConfig"]
