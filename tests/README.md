# Testing Documentation

This directory contains integration tests for the agents workspace.

## Test Files

### Integration Tests
- **test_integration.py** - End-to-end workflow tests
- **integration/test_full_pipeline.py** - Full pipeline integration tests covering:
  - G-code parser agent
  - CAM runner agent with cycle time calculation
  - Cell scheduler with all solvers (OR-Tools, GA, SA, TABU, ALNS)
  - LangGraph orchestrator workflows
  - REST API health and OpenAPI validation

## Running Tests

### All Integration Tests
```bash
uv run pytest tests/ -v
```

### Full Pipeline Tests
```bash
uv run pytest tests/integration/test_full_pipeline.py -v
```

### Agent-Specific Tests
```bash
uv run pytest agents/gcode-parser/tests/ -v
uv run pytest agents/cam-runner/tests/test_agent.py -v
uv run pytest agents/cell-scheduler/tests/ -v
uv run pytest agents/cell-schedule-visualizer/tests/ -v
```

### MES Tests
```bash
cd agents/cell-mes && uv run pytest tests/ -v
```

## Test Coverage Summary

| Agent | Tests | Status |
|-------|-------|--------|
| gcode-parser | 2 | ✅ Pass |
| cam-runner | 12 | ✅ Pass |
| cell-scheduler | 12+ | ✅ Pass |
| cell-schedule-visualizer | 18 | ✅ Pass |
| cell-mes | 170+ | ✅ Pass |
| Integration (full_pipeline) | 14 | ✅ Pass |

## Solver Test Coverage

| Solver | Status | Notes |
|--------|--------|-------|
| OR-Tools | ✅ Pass | Optimal baseline |
| GA | ✅ Pass | +3.87% gap |
| SA | ✅ Pass | +3.87% gap |
| TABU | ✅ Pass | +3.87% gap |
| ALNS | ✅ Pass | +3.87% gap |

## Adding New Tests

1. Place agent-specific tests in `agents/*/tests/`
2. Place integration tests in `tests/integration/`
3. Follow pytest conventions with fixtures and test classes
4. Add descriptive docstrings
5. Include both positive and edge case scenarios

## CI/CD Integration

Tests are designed to run without external dependencies:
- No API keys required for agent tests
- Sample data included in `samples/` directory
- REST API tests skip if services not running
