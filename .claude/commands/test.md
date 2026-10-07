# /test - Run Tests

Run tests for a specific module or all tests following the project's test-driven workflow.

## Usage

```
/test [module-name]
```

- Without argument: Run all tests
- With module name: Run tests for specific module

## Execution Steps

1. **If module specified**: Run module tests
   ```bash
   uv run pytest agents/<module>/tests/ -v --tb=short
   ```

2. **If no module specified**: Run all tests
   ```bash
   uv run pytest tests/ -v
   ```

3. **Show coverage** after tests complete:
   ```bash
   uv run pytest agents/<module>/tests/ --cov=agents.<module_name> --cov-report=term-missing
   ```

## Important

- Always use `uv run` prefix (project requirement)
- Report test count and pass/fail status
- If tests fail, analyze the failure message and suggest fixes
- Reference `shared/skills/test_driven_updates.md` for test patterns

## Example Output

```
Running tests for gcode-parser...

agents/gcode-parser/tests/test_agent.py::TestGcodeParser::test_parse PASSED
agents/gcode-parser/tests/test_agent.py::TestGcodeParser::test_error PASSED

========================= 12 passed in 0.32s =========================

Coverage Report:
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
agents/gcode_parser/src/parser.py        120      2    98%
```