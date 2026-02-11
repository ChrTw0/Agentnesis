# Agentnesis - Dynamic Multi-Agent System with Deep Reasoning

A multi-agent system that **generates specialized experts on-demand** to solve complex problems through collaborative reasoning.

## The Problem

Traditional LLM systems have fundamental limitations:

1. **Single-agent systems** (ChatGPT, Claude) lack specialized domain expertise
2. **Fixed multi-agent systems** (AutoGen, CrewAI) use predefined agents that may not fit the problem
3. **Simple ReAct agents** lack depth — they don't plan, critique, or self-improve
4. **No coordination** — agents work in isolation, creating contradictory outputs

## The Solution: Agentnesis

**Genesis**, the meta-cognitive core, analyzes your problem and **dynamically spawns the exact team of specialists you need**. Each specialist is a **DeepAgent** with its own reasoning cycle (Plan → Execute → Critique), not a simple tool-calling loop.

Key innovations:
- **Dynamic spawning**: No hardcoded agents — Genesis creates Backend Devs, Legal Experts, Research Analysts, etc. based on your query
- **Deep reasoning**: Each agent runs Plan-Execute-Critique cycles (fractal architecture)
- **Collaborative validation**: Proposals are validated against a shared Knowledge Graph to prevent contradictions
- **Orchestrated turns**: A Moderator manages who speaks when, preventing chaos and deadlocks

## How it Works

Instead of using a single LLM or a fixed set of agents, Agentnesis:

1. **Genesis analyzes your question** to determine what expertise is needed
2. **Spawns specialized agents dynamically** (e.g., Legal Expert, Backend Developer, Research Analyst)
3. **Each agent runs a deep reasoning loop**: Plan → Execute → Self-Critique (not simple tool-calling)
4. **Integrator validates proposals** for consistency before adding them to the knowledge graph
5. **Moderator orchestrates turns** to prevent chaos and detect deadlocks
6. **Synthesizer consolidates** all approved work into a coherent final answer

## Key features

- **Dynamic Agent Creation**: Genesis spawns agents on-demand based on the problem domain
- **Fractal Architecture**: Each agent runs its own Plan-Execute-Critique loop (DeepAgent pattern)
- **Knowledge Graph**: Shared memory stores validated decisions as entities and relations
- **Conflict Resolution**: Integrator validates proposals against the KG to prevent contradictions
- **Turn Management**: Moderator orchestrates agent turns and detects deadlocks
- **State Isolation**: Each agent has its own LLM chain and toolset to prevent cross-contamination

## Architecture

```
                      User Query
                           ↓
                    ┌──────────────┐
                    │   Genesis    │ ← Spawns agents dynamically
                    │ (Bootstrap)  │
                    └──────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        │         Collaborative Loop          │
        │  (Repeats until FINISH or Deadlock) │
        └─────────────────────────────────────┘
                           ↓
           ┌───────────────────────────────┐
           │        Moderator              │
           │  - Decides next speaker       │
           │  - Monitors progress          │
           └───────────────────────────────┘
                ↓              ↓           ↓
        ┌───────────┐   ┌──────────┐   ┌─────────┐
        │   Agent   │   │Integrator│   │ FINISH  │
        │   Work    │   │(Validate)│   │    ↓    │
        └───────────┘   └──────────┘   │Synthesize
             ↓                ↓         └─────────┘
    ┌────────────────┐        │
    │ Fractal Loop:  │        │
    │ Plan→Execute   │        │
    │    →Critique   │        │
    └────────────────┘        │
             ↓                ↓
        Staging Area ← Approved/Rejected
             ↓
      Knowledge Graph (Shared Memory)
```

**Key Flow:**
1. Genesis analyzes query → spawns N agents
2. **Loop** (Moderator orchestrates):
   - Agent turn → Fractal reasoning → Publish proposal
   - Integrator validates → Approve/Reject
   - Moderator decides next action
3. When all agents approved → Synthesizer generates final answer

## Current Limitations

**Tools:** Currently operates using only LLM knowledge and reasoning. External tools (web search, PDF parsing, code execution) are planned for future versions.

**Recommended Model:** [DeepSeek V3.2](https://platform.deepseek.com/) via [OpenRouter](https://openrouter.ai/)
- **Why DeepSeek?** Sparse attention architecture → low cost (~$0.25/1M input tokens)
- **Performance:** Top 30 in [LMArena](https://lmarena.ai/) leaderboard (as of Feb 2026)
- **Quality:** Produces 95-98% confidence outputs in our benchmarks

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Agentnesis.git
cd Agentnesis

# Create conda environment
conda create -n Agentnesis python=3.12 -y
conda activate Agentnesis

# Install dependencies
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
```env
# API Key - supports OpenAI or OpenRouter
OPENROUTER_API_KEY=your_api_key_here

# Model selection (per agent)
GENESIS_MODEL=deepseek/deepseek-v3.2
MODERATOR_MODEL=deepseek/deepseek-v3.2
INTEGRATOR_MODEL=deepseek/deepseek-v3.2
SYNTHESIZER_MODEL=deepseek/deepseek-v3.2
WORKER_MODEL=deepseek/deepseek-v3.2

# System limits
GRAPH_RECURSION_LIMIT=75
MODERATOR_MAX_ITERATIONS=20
GENESIS_MAX_AGENTS=10
```

## Usage

```bash
python -m src.main "Why is the ocean blue?"
```

## Project Structure

```
Agentnesis/
├── src/
│   ├── config/              # Settings and LLM factory
│   ├── core/
│   │   ├── states/          # GlobalState, schemas, reducers
│   │   └── main_graph.py    # Main LangGraph assembly
│   ├── specialists/
│   │   ├── genesis/         # Domain analysis & dynamic spawning
│   │   ├── moderator/       # Turn orchestration & deadlock detection
│   │   ├── integrator/      # Proposal validation vs KG
│   │   ├── synthesizer/     # Final output consolidation
│   │   ├── fractal_agent/   # Plan-Execute-Critique loop
│   │   └── universal_worker/# Polymorphic agent execution
│   ├── utils/               # Helpers (prompt loader, JSON parser, logger)
│   ├── tools/               # External tools (Phase 2 - see tools/README.md)
│   └── services/            # External integrations (Phase 3 - see services/__init__.py)
├── tests/                   # Test suite (future - see tests/README.md)
├── scripts/                 # Development scripts
├── .env.example             # Configuration template
├── pyproject.toml           # Dependencies
└── README.md                # This file
```

## How it works

### 1. Genesis analyzes the query
```python
# Determines domain and required expertise
domain_analysis = genesis.analyze_domain(user_query)
# Result: "physics-and-chemistry" → spawns PhysicsExpert, OpticsSpecialist
```

### 2. Each agent runs a fractal cycle
```python
# Inside agent subgraph
plan = planner(task, context)  # "I need to explain absorption and scattering"
execution = executor(plan)      # Generates proposal with structured_data
critique = critic(execution)    # "Proposal is complete and accurate"
# → Publishes to Staging Area
```

### 3. Integrator validates proposals
```python
# Checks against Knowledge Graph
if conflicts_with_kg(proposal):
    return {"status": "rejected", "feedback": "..."}
else:
    return {"status": "approved"}
```

### 4. Moderator decides next speaker
```python
# Considers: pending proposals, agent status, dependencies, recent turns
next_speaker = moderator.decide_turn(state)
# Returns: "OpticsSpecialist_001" or "INTEGRATOR" or "FINISH"
```

### 5. Synthesizer consolidates final answer
```python
# Transforms Knowledge Graph into coherent response
final_output = synthesizer.synthesize(
    kg_entities=approved_entities,
    kg_relations=approved_relations,
    user_query=original_query
)
```


## Metrics (last 5 runs)

- Average confidence: 95-98%
- LLM calls per run: 15-22
- Agents spawned: 2-3
- Success rate: 100% (5/5)

## Roadmap

**Phase 1 (Current - MVP):** [OK]
- Dynamic agent spawning
- Fractal reasoning loops
- Knowledge graph integration
- Validation and orchestration

**Phase 2 (Next - Tools Exploration):**
- **Web Search**: Tavily/SerpAPI/DuckDuckGo (real-time information retrieval)
- **PDF Parsing**: Document ingestion and extraction
- **Web Scraping**: BeautifulSoup/Playwright for structured data
- **Code Execution**: Sandboxed environments (under evaluation)
- **Dynamic Tool Binding**: Tools assigned per agent role at spawn time

**Phase 3 (Future):**
- Persistent checkpointing (PostgreSQL)
- Parallel agent execution
- Advanced conflict resolution
- Human-in-the-loop for critical decisions

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details

## Author

**Christian Sosa** - [christian.sosa.r16@gmail.com](mailto:christian.sosa.r16@gmail.com)

## Contributing

This is an open-source research project. Issues and PRs are welcome.
