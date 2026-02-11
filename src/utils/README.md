# Utils Module - Advanced Features (Phase 2+)

This directory contains utility functions for the system.

## Active Utilities (v0.1.0)

- `helpers.py` - JSON extraction, turn formatting
- `prompt_loader.py` - Prompt file loading and formatting
- `dev_logger.py` - Development logging and LLM interaction tracking
- `llm_wrapper.py` - LLM invocation with logging

## Planned Utilities (Future Phases)

### Context & RAG
- `context_retrieval.py` - Smart context retrieval from Knowledge Graph using embeddings and vector search (Phase 2)

### Validation & Graphs  
- `dependency_graph.py` - Dependency analysis and circular dependency detection for agent coordination (Phase 3)

## Implementation Notes

**context_retrieval.py**: Will use FAISS/Chroma for vector search to retrieve relevant KG context instead of passing entire graph to agents.

**dependency_graph.py**: Will implement DFS-based cycle detection before agent spawning to prevent deadlocks.
