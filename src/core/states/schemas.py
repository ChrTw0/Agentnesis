"""
Schemas compartidos entre todos los componentes del sistema.

Define las estructuras de datos fundamentales:
- AgentProfile: Configuración de un agente
- Proposal: Unidad de trabajo en el Staging Area
- SpawnRequest: Solicitud de creación de nuevo agente
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AgentProfile(BaseModel):
    """
    Configuración de un agente instanciado por Genesis.

    Atributos:
        name: Identificador único del agente (ej: "BackendDev_001")
        role: Rol semántico (ej: "Python Expert", "Legal Advisor")
        expertise: Lista de áreas de expertise específicas
        system_prompt: Instrucciones específicas del rol
        tools: Lista de nombres de herramientas disponibles
        dependencies: Lista de nombres de agentes de los que depende
        spawn_depth: Profundidad en el árbol de spawning (0=Genesis, 1=spawneado por Genesis, etc)
        spawned_by: Nombre del agente que lo spawneó ("Genesis" si es inicial)
        spawn_reason: Razón por la que fue creado (si fue vía REQUEST_SPAWN)
    """
    name: str = Field(..., description="Identificador único del agente")
    role: str = Field(..., description="Rol semántico del agente")
    expertise: List[str] = Field(
        default_factory=list,
        description="Áreas específicas de expertise (ej: ['FastAPI', 'PostgreSQL'])"
    )
    system_prompt: str = Field(..., description="System prompt específico del agente")
    tools: List[str] = Field(default_factory=list, description="Lista de tools disponibles")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Agentes de los que depende este agente"
    )
    spawn_depth: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Profundidad de spawn (0=Genesis, máx 3 para prevenir recursión)"
    )
    spawned_by: str = Field(
        default="Genesis",
        description="Nombre del agente que lo spawneó"
    )
    spawn_reason: Optional[str] = Field(
        None,
        description="Razón por la que fue spawneado (si aplica)"
    )

    class Config:
        frozen = False  # Permite modificación si es necesario
        json_schema_extra = {
            "example": {
                "name": "BackendDev_001",
                "role": "Python Backend Expert",
                "expertise": ["FastAPI", "SQLAlchemy", "REST APIs"],
                "system_prompt": "Eres un experto en FastAPI y Python...",
                "tools": ["python_repl", "file_write"],
                "dependencies": ["DBAdmin_001"],
                "spawn_depth": 1,
                "spawned_by": "Genesis",
                "spawn_reason": None
            }
        }


class Proposal(BaseModel):
    """
    Unidad de trabajo que los agentes publican en el Staging Area.

    Sigue el protocolo RFC (Request For Comments):
    draft → staging → validation → approved/rejected

    Atributos:
        agent_name: Quién creó la propuesta
        iteration: En qué turno se generó
        content: Texto de la propuesta (output del agente)
        structured_data: Datos estructurados para el Knowledge Graph
        status: Estado actual de la propuesta
        feedback: Feedback del Integrator o Self-Critic
        dependencies_met: Si las dependencias están resueltas
    """
    agent_name: str = Field(..., description="Nombre del agente que creó esta propuesta")
    iteration: int = Field(..., ge=0, description="Número de iteración global")
    content: str = Field(..., description="Contenido textual de la propuesta")
    structured_data: dict = Field(
        default_factory=dict,
        description="Datos estructurados: {entities: {...}, relations: [...]}"
    )
    status: Literal["draft", "rejected", "approved", "error"] = Field(
        default="draft",
        description="Estado de la propuesta"
    )
    feedback: str = Field(
        default="",
        description="Feedback del Integrator o mensaje de error"
    )
    dependencies_met: bool = Field(
        default=True,
        description="Si las dependencias del agente están satisfechas"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "BackendDev_001",
                "iteration": 3,
                "content": "Implementé el endpoint POST /users con FastAPI",
                "structured_data": {
                    "entities": {
                        "endpoint_users": {
                            "type": "API_Endpoint",
                            "properties": {"method": "POST", "path": "/users"}
                        }
                    },
                    "relations": [
                        {"source": "Backend", "rel": "implements", "target": "endpoint_users"}
                    ]
                },
                "status": "draft",
                "feedback": "",
                "dependencies_met": True
            }
        }


class SpawnRequest(BaseModel):
    """
    Señal que un agente emite cuando detecta falta de competencia.

    Procesada por Genesis para decidir: spawn/reusar/rechazar.

    Genesis considera:
    - ¿Ya existe agente con expertise similar?
    - ¿Hay saturación? (demasiados agentes/requests)
    - ¿Profundidad de spawn es segura? (prevenir bucles)

    Atributos:
        requester: Nombre del agente que solicita ayuda
        role: Rol del experto necesario
        required_expertise: Lista de expertise específico requerido
        justification: Por qué se necesita este experto
        context: Contexto del problema que requiere expertise
        priority: Nivel de urgencia
    """
    requester: str = Field(..., description="Agente que solicita el spawn")
    role: str = Field(..., description="Rol del experto requerido")
    required_expertise: List[str] = Field(
        default_factory=list,
        description="Expertise específico necesario (ej: ['GDPR', 'Data Privacy'])"
    )
    justification: str = Field(..., description="Justificación detallada de la solicitud")
    context: str = Field(
        default="",
        description="Contexto adicional del problema"
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Prioridad de la solicitud"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "requester": "BackendDev_001",
                "role": "Legal Expert",
                "required_expertise": ["GDPR", "Data Privacy Law"],
                "justification": "Need to verify GDPR compliance for user data storage implementation",
                "context": "Implementing personal data storage with encryption",
                "priority": "high"
            }
        }
