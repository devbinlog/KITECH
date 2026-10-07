# /commit - Create Commit with Proper Format

Create a git commit following the project's commit message guidelines.

## Usage

```
/commit <type>: <brief description>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `docs`: Documentation only
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

## Execution Steps

1. **Run pre-commit checks** first:
   ```bash
   uv run pytest tests/ -v
   uv run ruff format agents/ shared/
   uv run ruff check agents/ shared/
   ```

2. **Clean up temporary files**:
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
   find . -name ".coverage" -delete 2>/dev/null
   ```

3. **Show git status**:
   ```bash
   git status
   ```

4. **Create commit** with detailed message format:
   ```
   <type>: <brief description>

   Detailed explanation:
   - Specific change 1
   - Specific change 2
   - Why this change was needed

   Tests:
   - Added X new tests for functionality Y
   - All N tests passing, M% coverage

   Changed files:
     - path/to/file.py (X lines changed)
     - path/to/test_file.py (+Y lines, Z new tests)

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```

## Important

- NEVER commit if tests fail
- NEVER commit __pycache__ or .pytest_cache
- Always mention test changes in commit message
- Reference relevant skills if patterns were followed
- Ask user which files to stage if unclear

## Example

User: `/commit feat: Add G91 incremental mode support`

Result:
```
git commit -m "feat: Add G91 incremental mode support

- Implement G91/G90 mode switching
- Track incremental_mode in parser state
- Modify position calculation for relative coordinates

Tests:
- Added 4 new tests for mode transitions
- All 16 tests passing, 97% coverage

Changed files:
  - agents/gcode-parser/src/parser.py (12 lines)
  - agents/gcode-parser/tests/test_agent.py (+45 lines, 4 new tests)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```
