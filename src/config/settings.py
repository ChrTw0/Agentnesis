"""
Configuración global del sistema cargada desde .env

Usa Pydantic BaseSettings para validación y tipos.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from src.specialists.genesis.schema import GenesisConfig
from src.specialists.moderator.schema import ModeratorConfig
from src.specialists.integrator.schema import IntegratorConfig
from src.specialists.universal_worker.schema import UniversalWorkerConfig, ContextRetrievalConfig
from src.specialists.synthesizer.schema import SynthesizerConfig


class LLMConfig(BaseModel):
    """Configuración de LLMs (OpenAI o OpenRouter)"""

    # API Keys
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # Model name (OpenAI directo o OpenRouter format)
    openai_model: str = "gpt-4-turbo-preview"

    # Generation params
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=256, le=163840)


class FractalAgentConfig(BaseModel):
    """Configuración del subgrafo fractal (Planner/Executor/Critic)"""

    planner_model: Optional[str] = None
    executor_model: Optional[str] = None
    critic_model: Optional[str] = None
    max_retries: int = Field(default=3, ge=1, le=10)
    absolute_max_retries: int = Field(default=5, ge=2, le=10)


class GraphConfig(BaseModel):
    """Configuración del grafo principal (LangGraph)"""

    checkpoint_enabled: bool = True
    checkpoint_dir: str = "./checkpoints"
    recursion_limit: int = Field(ge=25, le=500)


class DeveloperConfig(BaseModel):
    """Configuración para modo developer (debugging/testing)"""

    developer_mode: bool = False
    log_dir: str = "./logs"
    log_llm_responses: bool = True
    log_graph_states: bool = True
    log_format: Literal["json", "txt"] = "json"


class Settings(BaseModel):
    """
    Configuración global del sistema.

    Carga desde .env y valida con Pydantic.
    """

    # LLM Configuration
    llm: LLMConfig

    # Specialist Configs
    genesis: GenesisConfig
    moderator: ModeratorConfig
    integrator: IntegratorConfig
    worker: UniversalWorkerConfig
    context_retrieval: ContextRetrievalConfig
    synthesizer: SynthesizerConfig
    fractal: FractalAgentConfig
    graph: GraphConfig
    developer: DeveloperConfig

    @classmethod
    def load_from_env(cls) -> "Settings":
        """
        Factory method para cargar settings desde .env con override desde variables.

        Esto permite que valores del .env sobrescriban los defaults.
        """
        import os
        from dotenv import load_dotenv

        # Cargar .env
        load_dotenv()

        # Crear LLMConfig
        llm_config = LLMConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
        )

        # Crear configs individuales desde env vars
        genesis_config = GenesisConfig(
            model_name=os.getenv("GENESIS_MODEL"),
            max_agents=int(os.getenv("GENESIS_MAX_AGENTS", "10")),
            max_spawn_depth=int(os.getenv("GENESIS_MAX_SPAWN_DEPTH")) if os.getenv("GENESIS_MAX_SPAWN_DEPTH") else None,
            allow_dynamic_spawn=os.getenv("GENESIS_ALLOW_DYNAMIC_SPAWN", "true").lower() == "true",
            spawn_cooldown=int(os.getenv("GENESIS_SPAWN_COOLDOWN", "0")),
            enable_agent_reuse=os.getenv("GENESIS_ENABLE_AGENT_REUSE", "true").lower() == "true",
            saturation_threshold=float(os.getenv("GENESIS_SATURATION_THRESHOLD", "0.8"))
        )

        moderator_config = ModeratorConfig(
            model_name=os.getenv("MODERATOR_MODEL"),
            max_iterations=int(os.getenv("MODERATOR_MAX_ITERATIONS", "20")),
            rejection_loop_threshold=int(os.getenv("MODERATOR_REJECTION_LOOP_THRESHOLD", "3")),
            enable_human_override=os.getenv("MODERATOR_ENABLE_HUMAN_OVERRIDE", "true").lower() == "true"
        )

        integrator_config = IntegratorConfig(
            model_name=os.getenv("INTEGRATOR_MODEL"),
            strict_mode=os.getenv("INTEGRATOR_STRICT_MODE", "false").lower() == "true",
            allow_property_override=os.getenv("INTEGRATOR_ALLOW_PROPERTY_OVERRIDE", "true").lower() == "true",
            max_conflicts_per_proposal=int(os.getenv("INTEGRATOR_MAX_CONFLICTS_PER_PROPOSAL", "5"))
        )

        worker_config = UniversalWorkerConfig(
            model_name=os.getenv("WORKER_MODEL"),
            execution_timeout=int(os.getenv("WORKER_EXECUTION_TIMEOUT", "120")),
            max_retries_on_error=int(os.getenv("WORKER_MAX_RETRIES_ON_ERROR", "1")),
            cache_subgraphs=os.getenv("WORKER_CACHE_SUBGRAPHS", "true").lower() == "true"
        )

        context_config = ContextRetrievalConfig(
            top_k=int(os.getenv("CONTEXT_TOP_K", "10")),
            use_embeddings=os.getenv("CONTEXT_USE_EMBEDDINGS", "false").lower() == "true",
            min_relevance_score=float(os.getenv("CONTEXT_MIN_RELEVANCE_SCORE", "0.5")),
            include_relations=os.getenv("CONTEXT_INCLUDE_RELATIONS", "true").lower() == "true"
        )

        synthesizer_config = SynthesizerConfig(
            model_name=os.getenv("SYNTHESIZER_MODEL"),
            output_format=os.getenv("SYNTHESIZER_OUTPUT_FORMAT", "prose"),
            include_kg_dump=os.getenv("SYNTHESIZER_INCLUDE_KG_DUMP", "false").lower() == "true",
            verbosity=os.getenv("SYNTHESIZER_VERBOSITY", "normal")
        )

        fractal_config = FractalAgentConfig(
            planner_model=os.getenv("FRACTAL_PLANNER_MODEL"),
            executor_model=os.getenv("FRACTAL_EXECUTOR_MODEL"),
            critic_model=os.getenv("FRACTAL_CRITIC_MODEL"),
            max_retries=int(os.getenv("FRACTAL_MAX_RETRIES", "3")),
            absolute_max_retries=int(os.getenv("FRACTAL_ABSOLUTE_MAX_RETRIES", "5"))
        )

        graph_config = GraphConfig(
            checkpoint_enabled=os.getenv("GRAPH_CHECKPOINT_ENABLED", "true").lower() == "true",
            checkpoint_dir=os.getenv("GRAPH_CHECKPOINT_DIR", "./checkpoints"),
            recursion_limit=int(os.getenv("GRAPH_RECURSION_LIMIT"))
        )

        developer_config = DeveloperConfig(
            developer_mode=os.getenv("DEVELOPER_MODE", "false").lower() == "true",
            log_dir=os.getenv("LOG_DIR", "./logs"),
            log_llm_responses=os.getenv("LOG_LLM_RESPONSES", "true").lower() == "true",
            log_graph_states=os.getenv("LOG_GRAPH_STATES", "true").lower() == "true",
            log_format=os.getenv("LOG_FORMAT", "json")
        )

        return cls(
            llm=llm_config,
            genesis=genesis_config,
            moderator=moderator_config,
            integrator=integrator_config,
            worker=worker_config,
            context_retrieval=context_config,
            synthesizer=synthesizer_config,
            fractal=fractal_config,
            graph=graph_config,
            developer=developer_config
        )


# Singleton global
settings = Settings.load_from_env()


# Exports
__all__ = ["Settings", "settings", "LLMConfig", "FractalAgentConfig", "GraphConfig"]
