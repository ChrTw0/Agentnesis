"""
Genesis Agent - Meta-Cognición y Spawning Inteligente.

Responsabilidades:
1. Analizar dominio del problema inicial
2. Decidir sobre SpawnRequests dinámicos
3. Crear AgentProfiles con prompts personalizados
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI

from src.core.states.schemas import AgentProfile, SpawnRequest
from src.specialists.genesis.schema import DomainAnalysis, SpawnDecision, GenesisConfig
from src.specialists.genesis.chains import GenesisChains


class GenesisAgent:
    """
    Genesis - Agente de meta-cognición y spawning inteligente.

    Orquesta las chains de Genesis y maneja la lógica de negocio:
    - Análisis de dominio
    - Decisiones de spawn
    - Creación de AgentProfiles
    """

    def __init__(self, config: GenesisConfig, llm: ChatOpenAI):
        """
        Args:
            config: Configuración de Genesis
            llm: LLM configurado (OpenAI/OpenRouter)
        """
        self.config = config
        self.llm = llm
        self.name = "Genesis"

        # Inicializar chains
        self.chains = GenesisChains(llm)

    def analyze_domain(self, user_query: str, num_agents: int = 0) -> DomainAnalysis:
        """
        Analiza el user_query para determinar dominio y roles necesarios.

        Args:
            user_query: Query del usuario
            num_agents: Número actual de agentes en el sistema

        Returns:
            DomainAnalysis con dominio, complejidad y roles requeridos
        """
        return self.chains.analyze_domain(
            user_query=user_query,
            num_agents=num_agents,
            max_agents=self.config.max_agents
        )

    def decide_spawn(
        self,
        request: SpawnRequest,
        num_agents: int,
        agents: List[AgentProfile],
        num_pending_requests: int
    ) -> SpawnDecision:
        """
        Decisión inteligente sobre SpawnRequest.

        Args:
            request: SpawnRequest del agente
            num_agents: Número actual de agentes
            agents: Lista de agentes existentes
            num_pending_requests: Requests pendientes en cola

        Returns:
            SpawnDecision con veredicto (spawn/reusar/rechazar)
        """
        return self.chains.decide_spawn(
            request=request,
            num_agents=num_agents,
            max_agents=self.config.max_agents,
            agents=agents,
            num_pending_requests=num_pending_requests,
            saturation_threshold=self.config.saturation_threshold,
            max_spawn_depth=self.config.max_spawn_depth
        )

    def create_agent_profile(
        self,
        role: str,
        expertise: List[str],
        spawned_by: str,
        spawn_depth: int,
        existing_agents: List[AgentProfile],
        spawn_reason: Optional[str] = None
    ) -> AgentProfile:
        """
        Crea un AgentProfile completo para un nuevo agente.

        Args:
            role: Rol del agente (ej: "Backend Developer")
            expertise: Lista de expertise (ej: ["FastAPI", "PostgreSQL"])
            spawned_by: Quién lo spawneó
            spawn_depth: Profundidad en el árbol de spawning
            existing_agents: Agentes existentes (para generar nombre único)
            spawn_reason: Razón del spawn (opcional)

        Returns:
            AgentProfile completo con system_prompt personalizado
        """
        # Generar nombre único
        role_slug = role.replace(" ", "")
        existing_count = len([a for a in existing_agents if a.role == role])
        agent_name = f"{role_slug}_{existing_count + 1:03d}"

        # Generar system prompt personalizado para este rol
        system_prompt = self._generate_role_prompt(agent_name, role, expertise)

        return AgentProfile(
            name=agent_name,
            role=role,
            expertise=expertise,
            system_prompt=system_prompt,
            tools=[],  # TODO: Asignar tools según rol
            dependencies=[],
            spawn_depth=spawn_depth,
            spawned_by=spawned_by,
            spawn_reason=spawn_reason
        )

    def _generate_role_prompt(self, agent_name: str, role: str, expertise: List[str]) -> str:
        """
        Genera system_prompt personalizado para un agente spawneado.

        Este prompt es la "INNER LAYER" que Universal Worker inyectará.
        """
        expertise_list = "\n".join([f"- {exp}" for exp in expertise])

        return f"""You are {agent_name}, a specialized agent with the role: {role}.

YOUR EXPERTISE:
{expertise_list}

YOUR RESPONSIBILITIES:
- Propose solutions within your domain of expertise
- Use the Knowledge Graph context provided to ensure consistency
- Emit structured proposals (entities + relations) for validation
- Request spawn of other agents (SpawnRequest) if you need help outside your expertise

CONSTRAINTS:
- DO NOT propose changes outside your expertise areas
- DO NOT assume information not present in the Knowledge Graph
- Be specific and concise in your proposals
- If uncertain, acknowledge it with lower confidence_score

OUTPUT FORMAT:
Always provide:
1. draft: Textual description of your work
2. structured_data: {{"entities": {{}}, "relations": []}}
3. confidence_score: Self-evaluation (0-1)
4. spawn_requested: true if you need help from another specialist
"""


# Export
__all__ = ["GenesisAgent"]
