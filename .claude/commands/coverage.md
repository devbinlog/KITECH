# /coverage - Check Test Coverage

Check test coverage for a specific module with detailed line-by-line report.

## Usage

```
/coverage <module-name>
```

Examples:
- `/coverage gcode-parser`
- `/coverage cell-scheduler`
- `/coverage cell-mes`

## Execution Steps

1. **Run tests with coverage**:
   ```bash
   uv run pytest agents/<module>/tests/ --cov=agents.<module_name> --cov-report=term-missing
   ```

2. **Analyze results**:
   - Report overall coverage percentage
   - List uncovered lines
   - Identify areas needing tests

3. **Generate HTML report** (optional):
   ```bash
   uv run pytest agents/<module>/tests/ --cov=agents.<module_name> --cov-report=html
   ```

## Coverage Targets

| Level | Coverage | Status |
|-------|----------|--------|
| Excellent | 95%+ | Green |
| Good | 85-94% | Yellow |
| Needs Work | < 85% | Red |

## Important

- Coverage should NOT drop after code changes
- Document baseline coverage before modifications
- Add tests for uncovered lines

## Example Output

```
Running coverage for gcode-parser...

Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
agents/gcode_parser/src/parser.py        120      3    97%   45, 78-79
agents/gcode_parser/src/blocks.py         45      0   100%
---------------------------------------------------------------------
TOTAL                                    165      3    98%

Uncovered lines:
- parser.py:45 - Error handling for invalid encoding
- parser.py:78-79 - Edge case for empty G-code blocks

Recommendation: Add tests for error handling cases.
```