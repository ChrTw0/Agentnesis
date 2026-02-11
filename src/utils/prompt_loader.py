"""
Utilidad para cargar prompts desde archivos .txt.

Proporciona funciones helper para leer y formatear prompts
con variables dinámicas usando f-strings.
"""

from pathlib import Path
from typing import Dict, Any


def load_prompt(prompt_path: str, **kwargs: Any) -> str:
    """
    Carga un prompt desde un archivo .txt y reemplaza variables.

    Args:
        prompt_path: Ruta relativa al archivo prompt (ej: "genesis/system_prompt.txt")
        **kwargs: Variables a interpolar en el prompt usando .format()

    Returns:
        Prompt formateado con variables reemplazadas

    Example:
        >>> prompt = load_prompt(
        ...     "genesis/task_domain_analysis.txt",
        ...     user_query="Build an API",
        ...     max_agents=10
        ... )
    """
    # Construir ruta absoluta desde src/specialists/
    base_path = Path(__file__).parent.parent / "specialists"
    full_path = base_path / prompt_path

    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")

    # Leer contenido
    with open(full_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Formatear con variables (si hay)
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable in prompt template: {e}")

    return template


def load_prompt_safe(prompt_path: str, **kwargs: Any) -> str:
    """
    Versión segura de load_prompt que reemplaza solo las variables provistas.

    Variables no provistas quedan como {variable} sin error.
    Útil para prompts con variables opcionales.

    Args:
        prompt_path: Ruta relativa al archivo prompt
        **kwargs: Variables a interpolar (opcionales)

    Returns:
        Prompt con variables reemplazadas (las no provistas quedan intactas)
    """
    base_path = Path(__file__).parent.parent / "specialists"
    full_path = base_path / prompt_path

    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Reemplazar solo las variables provistas
    for key, value in kwargs.items():
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, str(value))

    return template


# Exports
__all__ = ["load_prompt", "load_prompt_safe"]
