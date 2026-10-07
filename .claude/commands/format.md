# /format - Format and Lint Code

Format code with ruff and check linting following project standards.

## Usage

```
/format [path]
```

- Without argument: Format `agents/`, `shared/`
- With path: Format specific path

## Execution Steps

1. **Format with ruff**:
   ```bash
   uv run ruff format agents/ shared/
   ```

2. **Check with ruff**:
   ```bash
   uv run ruff check agents/ shared/
   ```

3. **Auto-fix safe issues**:
   ```bash
   uv run ruff check --fix agents/ shared/
   ```

4. **Report results**:
   - Number of files reformatted
   - Any linting errors found
   - If errors found, suggest fixes

## Important

- Always use `uv run` prefix (project requirement)
- Line length limit: 100 characters (configured in pyproject.toml `[tool.ruff]`)
- Fix any ruff errors before commit
- Known intentional exceptions: E402 (sys.path manipulation), F841 (test placeholders)

## Code Style Rules

- Line length: 100 characters
- Consistent indentation (4 spaces)
- No unused imports
- No undefined variables
- Type hints on all function signatures

## Example Output

```
Formatting code with ruff...
51 files reformatted, 252 files left unchanged

Running ruff check...
Found 9 errors.
[*] 7 fixable with the `--fix` option

Running ruff check --fix...
Found 9 errors (7 fixed, 2 remaining).
```
