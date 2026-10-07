# /check - Pre-Commit Checks

Run all pre-commit checks before committing: tests, coverage, format, and lint.

## Usage

```
/check
```

## Execution Steps

Execute ALL of these in sequence:

1. **Run all tests**:
   ```bash
   uv run pytest tests/ -v
   ```

2. **Check coverage**:
   ```bash
   uv run pytest --cov
   ```

3. **Format code**:
   ```bash
   uv run ruff format agents/ shared/
   ```

4. **Lint code**:
   ```bash
   uv run ruff check agents/ shared/
   ```

5. **Clean up temporary files**:
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
   find . -name ".coverage" -delete 2>/dev/null
   ```

## Report Format

After all checks, report:

```
Pre-Commit Check Results:
========================

[✓] Tests: 25/25 passed
[✓] Coverage: 97% (no drop)
[✓] Formatting: All files formatted
[✓] Linting: No errors

Ready to commit!
```

Or if issues found:

```
Pre-Commit Check Results:
========================

[✓] Tests: 24/25 passed
[✗] 1 test failed: test_parse_invalid_input
[✓] Coverage: 95%
[✗] Linting: 2 errors in parser.py

Please fix issues before committing.
```

## Important

- ALL checks must pass before commit
- Coverage should not drop below baseline
- Known intentional lint exceptions: E402 (sys.path manipulation), F841 (test placeholders)
