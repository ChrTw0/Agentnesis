"""
Developer Logger - Logging de interacciones LLM y estados del grafo.

Cuando DEVELOPER_MODE=true, guarda todas las interacciones en archivos JSON
para debugging y análisis posterior.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.config.settings import settings


class DevLogger:
    """
    Logger para modo developer.

    Guarda logs de:
    - LLM prompts y responses
    - Graph state transitions
    - Agent executions
    """

    def __init__(self):
        self.enabled = settings.developer.developer_mode
        self.log_dir = Path(settings.developer.log_dir)
        self.log_format = settings.developer.log_format

        # Crear directorio de logs si no existe
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Crear run ID único
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_dir = self.log_dir / f"run_{self.run_id}"
            self.run_dir.mkdir(parents=True, exist_ok=True)

            # Inicializar archivos de log
            self.llm_log_file = self.run_dir / "llm_interactions.json"
            self.graph_log_file = self.run_dir / "graph_states.json"

            # Contadores
            self.llm_call_count = 0
            self.state_count = 0

    def log_llm_call(
        self,
        agent_name: str,
        chain_name: str,
        model: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log de llamada a LLM.

        Args:
            agent_name: Nombre del agente (Genesis, Moderator, etc.)
            chain_name: Nombre de la chain (analyze_domain, decide_turn, etc.)
            model: Modelo usado (gpt-4-turbo-preview, etc.)
            prompt: Prompt enviado al LLM
            response: Respuesta del LLM
            metadata: Metadata adicional (temperatura, tokens, etc.)
        """
        if not self.enabled or not settings.developer.log_llm_responses:
            return

        self.llm_call_count += 1

        log_entry = {
            "call_id": self.llm_call_count,
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "chain": chain_name,
            "model": model,
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {}
        }

        # Append al archivo JSON
        self._append_to_json_file(self.llm_log_file, log_entry)

    def log_graph_state(
        self,
        node_name: str,
        state_snapshot: Dict[str, Any],
        action: str = "transition"
    ):
        """
        Log de transición de estado del grafo.

        Args:
            node_name: Nombre del nodo (genesis_bootstrap, moderator, etc.)
            state_snapshot: Snapshot del GlobalState
            action: Tipo de acción (transition, entry, exit)
        """
        if not self.enabled or not settings.developer.log_graph_states:
            return

        self.state_count += 1

        log_entry = {
            "state_id": self.state_count,
            "timestamp": datetime.now().isoformat(),
            "node": node_name,
            "action": action,
            "state": self._serialize_state(state_snapshot)
        }

        # Append al archivo JSON
        self._append_to_json_file(self.graph_log_file, log_entry)

    def _append_to_json_file(self, filepath: Path, entry: Dict[str, Any]):
        """Helper: Append entry a archivo JSON (array)."""
        # Leer existente o inicializar array
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        # Agregar entrada
        data.append(entry)

        # Escribir de vuelta
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Helper: Serializar estado del grafo (manejar tipos no JSON-safe)."""
        serialized = {}

        for key, value in state.items():
            try:
                # Intentar serializar directamente
                json.dumps(value)
                serialized[key] = value
            except (TypeError, ValueError):
                # Si falla, convertir a string
                serialized[key] = str(value)

        return serialized

    def finalize_run(self):
        """
        Finaliza el run y crea summary.

        Genera archivo summary.json con metadata del run.
        """
        if not self.enabled:
            return

        summary = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "llm_calls": self.llm_call_count,
            "state_transitions": self.state_count,
            "log_files": {
                "llm_interactions": str(self.llm_log_file.relative_to(self.log_dir)),
                "graph_states": str(self.graph_log_file.relative_to(self.log_dir))
            }
        }

        summary_file = self.run_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)


# Singleton global
dev_logger = DevLogger()


# Export
__all__ = ["DevLogger", "dev_logger"]
