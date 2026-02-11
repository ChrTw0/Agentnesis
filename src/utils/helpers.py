import re
import json


def extract_json(text: str) -> dict:
    """Extrae JSON de un string que puede estar envuelto en markdown (```json ... ```)."""
    # Intentar parsear directamente
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Buscar bloque ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())

    raise json.JSONDecodeError("No valid JSON found", text, 0)


def format_recent_turns(turn_history: list[str], last_n: int = 5) -> str:
    """Formatea los últimos N turnos del historial como secuencia."""
    recent = turn_history[-last_n:] if turn_history else []
    return " -> ".join(recent) if recent else "- None"
