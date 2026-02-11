"""
Schemas específicos del Synthesizer (Generador de Respuesta Final).

Synthesizer es responsable de:
- Consolidar Knowledge Graph en respuesta coherente
- Formatear output según el dominio
- Generar resumen ejecutivo para el usuario
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class SynthesisResult(BaseModel):
    """
    Resultado de la síntesis final.

    Contiene la respuesta consolidada y metadata.
    """
    final_answer: str = Field(..., description="Respuesta consolidada para el usuario")
    summary: str = Field(..., description="Resumen ejecutivo (2-3 párrafos)")
    key_decisions: list[str] = Field(
        default_factory=list,
        description="Decisiones clave tomadas por el sistema"
    )
    entities_created: int = Field(
        default=0,
        ge=0,
        description="Número de entidades en el Knowledge Graph"
    )
    agents_involved: list[str] = Field(
        default_factory=list,
        description="Nombres de agentes que participaron"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confianza en la respuesta (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "final_answer": "Sistema completado exitosamente. Se diseñó una API REST...",
                "summary": "El sistema analizó los requisitos y diseñó una arquitectura completa...",
                "key_decisions": [
                    "Usar FastAPI como framework backend",
                    "PostgreSQL como base de datos",
                    "Implementar autenticación JWT"
                ],
                "entities_created": 15,
                "agents_involved": ["BackendDev_001", "DBAdmin_001", "SecurityExpert_001"],
                "confidence": 0.92
            }
        }


class SynthesizerConfig(BaseModel):
    """
    Configuración de comportamiento del Synthesizer.

    Controla formato y nivel de detalle de output.
    """
    model_name: Optional[str] = Field(
        default=None,
        description="Modelo LLM para Synthesizer (None = usa default global)"
    )
    output_format: Literal["prose", "structured", "markdown"] = Field(
        default="prose",
        description="Formato de la respuesta: prosa natural, estructurado (JSON-like), o markdown"
    )
    include_kg_dump: bool = Field(
        default=False,
        description="Incluir dump completo del Knowledge Graph en output"
    )
    verbosity: Literal["concise", "normal", "detailed"] = Field(
        default="normal",
        description="Nivel de detalle en la respuesta"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "output_format": "markdown",
                "include_kg_dump": False,
                "verbosity": "normal"
            }
        }


# Exports
__all__ = ["SynthesisResult", "SynthesizerConfig"]
