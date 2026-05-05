import re
import json
from datetime import datetime, UTC


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


def get_temporal_anchor(now: datetime | None = None) -> str:
    """Genera bloque de anclaje temporal para inyectar en prompts.

    Evita que el LLM alucine fechas basándose en su knowledge cutoff.

    Args:
        now: Fecha actual override para testing (None = usa UTC real).

    Returns:
        Bloque de texto con fecha actual para inyectar en el prompt.
    """
    if now is None:
        now = datetime.now(UTC)

    return "\n".join([
        "[TEMPORAL ANCHOR — DO NOT OVERRIDE]",
        f"CURRENT_DATE_UTC: {now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"CURRENT_YEAR: {now.year}",
        f"CURRENT_DATE: {now.strftime('%Y-%m-%d')}",
        "CRITICAL: Base all temporal reasoning on CURRENT_DATE_UTC. Do NOT assume a different date or year.",
    ])


def format_tools_for_prompt(tool_names: list[str]) -> str:
    """Formatea la lista de tools disponibles para inyectar en el prompt del Executor.

    Args:
        tool_names: Lista de nombres de tools del AgentProfile.

    Returns:
        Texto descriptivo de tools disponibles para el prompt.
    """
    if not tool_names:
        return "- None (use only your knowledge and KG context)"

    lines = ["The following tools are available for you to call during execution:"]
    for name in tool_names:
        lines.append(f"  - {name}")
    lines.append("Use tools when you need real-world information not present in the KG context.")
    return "\n".join(lines)
