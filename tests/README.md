# Test Suite (Future)

Test coverage will be added in future releases.

## Planned Test Structure

```
tests/
├── test_states.py              # State reducers and merging
├── test_integration.py         # End-to-end system tests
└── test_specialists/
    ├── test_genesis.py         # Genesis domain analysis & spawning
    ├── test_moderator.py       # Turn management & deadlock detection
    ├── test_integrator.py      # Proposal validation
    └── test_universal_worker.py # Agent execution & fractal loop
```

## Testing Strategy

**Unit Tests:** Individual components (reducers, validators, prompts)
**Integration Tests:** Full workflows (Genesis → Agents → Integrator → Synthesizer)
**Fixtures:** Mock LLM responses for deterministic testing

## Run Tests (when implemented)

```bash
pytest tests/ -v
```
