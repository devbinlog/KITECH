# Development Guidelines

This document outlines the development practices and workflows for this manufacturing agents project.

## ⚙️ Environment Setup (IMPORTANT)

### Required: Use uv Package Manager

This project **REQUIRES** the `uv` package manager. Do NOT use pip directly.

```bash
# ✅ CORRECT: Use uv for all operations
uv sync                                    # Install dependencies
uv run pytest tests/ -v                    # Run tests
uv run ruff format agents/ shared/          # Format code
uv run ruff check agents/ shared/          # Lint code

# ❌ INCORRECT: Do not use pip directly
pip install -r requirements.txt            # ❌ DON'T
pip install package_name                   # ❌ DON'T
```

### Why uv?

- **Unified dependency management** across workspace members (gcode-parser, cam-runner, etc.)
- **Consistent Python version** (3.11) across all developers
- **Fast performance** with optimized resolution
- **Lock file guarantee** (uv.lock) for reproducible builds
- **Workspace support** for monorepo structure

### First Time Setup

```bash
# 1. Install uv (if needed)
pip install uv

# 2. Sync all dependencies
uv sync

# 3. Verify installation
uv run python --version  # Should be Python 3.11.13
```

### Activate Virtual Environment (Optional)

```bash
# On Windows
.venv\Scripts\Activate.ps1

# On macOS/Linux
source .venv/bin/activate
```

**Note**: You don't need to activate for `uv run` commands, but it's useful for IDE integration.

---

## Core Principles

1. **Tests are first-class artifacts** - Every code change must have corresponding test updates
2. **Code quality is non-negotiable** - All code must pass linting, formatting, and test requirements
3. **Consistency through skills** - Follow patterns defined in `shared/skills/` for all development work
4. **Documentation matters** - Code changes include docstring and README updates

## Code Change Workflow

### Before You Start

- [ ] Understand the existing code and tests
- [ ] Run baseline tests for the module you'll modify
- [ ] Review coverage metrics
- [ ] Note which components might be affected

```bash
# Example: Before modifying gcode-parser
uv run pytest agents/gcode-parser/tests/ -v
uv run pytest agents/gcode-parser/tests/ --cov=agents.gcode_parser
```

### During Development

- [ ] Write code following relevant skills from `shared/skills/`
- [ ] Write new tests **immediately** (don't defer)
- [ ] Keep tests synchronized with code changes
- [ ] Run tests frequently to catch issues early

```bash
# Run tests frequently during development
uv run pytest agents/gcode-parser/tests/ -v --tb=short
```

### Before Commit

All of these must pass:

- [ ] **Tests pass**: `uv run pytest tests/ -v` (all tests)
- [ ] **Coverage verified**: `uv run pytest --cov` (coverage didn't drop)
- [ ] **Code formatted**: `uv run ruff format agents/ shared/`
- [ ] **Linting passes**: `uv run ruff check agents/ shared/`
- [ ] **Docstrings updated** (if applicable)
- [ ] **Commit message includes test changes**

```bash
# Complete pre-commit checklist (using uv)
uv run pytest tests/ -v                                    # All tests
uv run pytest --cov                                        # Coverage
uv run ruff format agents/ shared/                 # Format
uv run ruff check agents/ shared/                # Lint

# If all pass, commit with detailed message
git add .
git commit -m "feat: Your feature description

- Specific change 1
- Specific change 2
- Added X new tests for Y functionality
- All 25 tests passing, 98% coverage

See: shared/skills/test_driven_updates.md"
```

## Skills to Follow

Follow the detailed patterns in these skill files for every development task:

### For Any Code Modification
**→ Read**: [shared/skills/test_driven_updates.md](shared/skills/test_driven_updates.md)
- Workflow for keeping tests synchronized
- Test update patterns
- Coverage monitoring
- Commit message guidelines

### For Writing Tests
**→ Read**: [shared/skills/test_implementation.md](shared/skills/test_implementation.md)
- pytest fixture patterns
- Test class organization
- Edge case coverage
- Mocking strategies

### For Error Handling
**→ Read**: [shared/skills/error_handling.md](shared/skills/error_handling.md)
- Try-catch wrapping patterns
- AnalysisResult structure
- Logging with context
- Error propagation in workflows

### For Configuration/Data
**→ Read**: [shared/skills/config_management.md](shared/skills/config_management.md)
**→ Read**: [shared/skills/data_validation.md](shared/skills/data_validation.md)
- Config loading (YAML/JSON)
- Validation patterns
- Type coercion
- Environment variables

### For Documentation
**→ Read**: [shared/skills/code_documentation.md](shared/skills/code_documentation.md)
- Docstring format (Google style)
- README structure
- API documentation
- Version tracking

### For Performance Work
**→ Read**: [shared/skills/performance_optimization.md](shared/skills/performance_optimization.md)
- Profiling tools
- Bottleneck analysis
- Optimization techniques
- Regression testing

### For Adding Dependencies
**→ Read**: [shared/skills/dependency_integration.md](shared/skills/dependency_integration.md)
- Conditional imports
- Version checking
- Feature flags
- Graceful fallbacks

## Testing Requirements

### Unit Tests
- **Must exist** for all public methods
- **Must cover** happy path + edge cases + error conditions
- **Must pass** before commit
- **Must not drop coverage** below baseline

### Integration Tests
- **Must pass** for all workflow changes
- **Must validate** stage-to-stage communication
- **Must check** error propagation
- **Must verify** output structure

### Test Execution
```bash
# Run specific module tests
uv run pytest agents/<module-name>/tests/ -v

# Run ALL tests (unit + integration)
uv run pytest tests/ -v

# Check coverage
uv run pytest agents/<module-name>/tests/ --cov=agents.<module_name>

# Run specific test
uv run pytest agents/<module-name>/tests/test_file.py::TestClass::test_method -v
```

## Code Quality Requirements

### Formatting
```bash
# Format code (required before commit)
uv run ruff format agents/ shared/
```
- Single quotes for strings
- Line length: 88 characters
- Consistent indentation

### Linting
```bash
# Check for style issues (required before commit)
uv run ruff check agents/ shared/
```
- No unused imports
- No undefined variables
- Consistent naming conventions
- No line length violations

### Type Hints
- All function signatures must have type hints
- Return types must be specified
- Use `Optional[]` for nullable values
- Use `|` (or `Union[]` for older Python) for multiple types

## Cleanup Guidelines (IMPORTANT)

### Before Every Commit

Clean up temporary files and caches generated during development:

```bash
# Remove Python cache directories
find . -type d -name __pycache__ -exec rm -rf {} +

# Remove pytest cache
rm -rf .pytest_cache

# Remove coverage files
rm -f .coverage

# Remove compiled Python files
find . -type f -name "*.pyc" -delete

# Remove egg-info directories
find . -type d -name "*.egg-info" -exec rm -rf {} +

# Or use git to remove untracked files (be careful!)
git clean -fd -x --exclude=.venv
```

### What Gets Cleaned

| Item | Pattern | Why Remove |
|------|---------|-----------|
| Python Cache | `__pycache__/` | Generated during import, platform-specific |
| Pytest Cache | `.pytest_cache/` | Regenerated when tests run |
| Coverage Data | `.coverage`, `htmlcov/` | Test artifact, should regenerate fresh |
| Compiled Python | `*.pyc` | Platform-specific, regenerated on import |
| Build Artifacts | `*.egg-info/` | Generated by setuptools, not needed in repo |
| IDE Caches | `.venv/`, `.idea/`, `.vscode/` | Should be in `.gitignore`, never commit |

### .gitignore Verification

This project should have these in `.gitignore` (already configured):

```
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.Python
venv/
.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
```

Verify with:
```bash
cat .gitignore | grep -E "__pycache__|pytest_cache|.coverage"
```

### Cleanup Checklist

- [ ] All temporary files cleaned before commit
- [ ] No `.pyc` files in git status
- [ ] No `__pycache__` directories in git status
- [ ] No `.pytest_cache` in git status
- [ ] Git status shows only your changes
- [ ] Run `git status` to verify

```bash
# Final verification before commit
git status

# Should only show changed source files, not generated files
# If you see generated files, run cleanup and re-check
```

---

## Commit Message Format

Commit messages should clearly describe both code changes AND test updates:

```
feat: Brief description of what changed

Detailed explanation of the change:
- Specific modification 1
- Specific modification 2
- Why this change was needed

Tests:
- Added X new tests for functionality Y
- Updated Z tests for behavior change
- All N tests passing, M% coverage

Changed files:
  - agents/module/src/file.py (X lines changed)
  - agents/module/tests/test_file.py (+Y lines, Z new tests)

See: shared/skills/test_driven_updates.md for patterns
```

### Example Commit Messages

**Good:**
```
feat: Add incremental coordinate mode (G91) support

- Implement G91/G90 mode switching
- Track incremental_mode in parser state
- Modify position calculation for relative coordinates
- Add 4 new tests for mode transitions
- All 16 tests passing, 97% coverage

Changed files:
  - agents/gcode-parser/src/gcode_parser_agent.py (12 lines)
  - agents/gcode-parser/tests/test_agent.py (+45 lines, 4 new tests)

See: shared/skills/test_driven_updates.md
```

**Poor:**
```
updated code
```

## Code Review Checklist

When reviewing code changes (or preparing for review), verify:

- [ ] Tests were added/updated with code
- [ ] All tests pass
- [ ] Coverage didn't drop
- [ ] Code is formatted and lints
- [ ] Docstrings are updated
- [ ] Commit message documents test changes
- [ ] No deprecated patterns used
- [ ] Error handling follows skill patterns
- [ ] Integration tests pass

## Quick Reference: Common Tasks

### Task: Fix a Bug
1. Write a test that reproduces the bug (will fail)
2. Fix the code
3. Verify test now passes
4. Run full test suite
5. Update docstring if behavior clarified
6. Commit with test reference

### Task: Add a Feature
1. Write tests first (will fail - TDD style)
2. Implement feature
3. Verify all tests pass
4. Add docstrings
5. Update README if needed
6. Commit with test count

### Task: Refactor Code
1. Run baseline tests (must all pass)
2. Refactor code
3. Verify tests still pass
4. Run integration tests
5. Document what changed
6. Commit with "refactor:" prefix

### Task: Optimize Performance
1. Profile current code
2. Implement optimization
3. Re-profile to verify improvement
4. Ensure tests still pass
5. Document optimization in docstring
6. Commit with "perf:" prefix and improvement %

### Task: Update Documentation
1. Make documentation changes
2. Run `black` and `flake8` on any code examples
3. Verify links still work
4. Commit with "docs:" prefix

## Tools & Commands

### Essential Commands
```bash
# Sync dependencies
uv sync

# Run all tests
pytest tests/ -v

# Run module tests with coverage
pytest agents/<module>/tests/ --cov=agents.<module> --cov-report=term-missing

# Format code
black agents/ shared/ orchestrator/

# Lint code
flake8 agents/ shared/ orchestrator/

# List available workflows
uv run orchestrator_main.py --list-workflows

# Run a workflow
uv run orchestrator_main.py --workflow minimal-analysis --input samples/simple/001_simple_square.nc
```

### Useful Testing Commands
```bash
# Run specific test file
pytest agents/gcode-parser/tests/test_agent.py -v

# Run specific test class
pytest agents/gcode-parser/tests/test_agent.py::TestGcodeParser -v

# Run specific test method
pytest agents/gcode-parser/tests/test_agent.py::TestGcodeParser::test_parse -v

# Run with short traceback
pytest agents/gcode-parser/tests/ -v --tb=short

# Run and show print statements
pytest agents/gcode-parser/tests/ -v -s

# Stop on first failure
pytest agents/gcode-parser/tests/ -x

# Run last failed tests
pytest --lf
```

## Workflow: Day-to-Day Development

### Morning: Start Work
```bash
# Update dependencies
uv sync

# Run full test suite to ensure baseline
pytest tests/ -v

# Start working on your task
```

### During Work: Development Loop
```bash
# Frequently run module tests (every few minutes)
uv run pytest agents/<your-module>/tests/ -v --tb=short

# When adding features
uv run pytest agents/<your-module>/tests/ --cov

# Before switching tasks/taking break
uv run pytest tests/ -v
```

### Before Commit: Final Checks
```bash
# 1. Run all tests
uv run pytest tests/ -v

# 2. Check coverage
uv run pytest --cov

# 3. Format code
uv run ruff format agents/ shared/

# 4. Lint code
uv run ruff check agents/ shared/

# 5. CLEANUP: Remove all temporary files before commit
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null
find . -type f -name .coverage -delete 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# 6. Review changes (should only show source code changes)
git status
git diff

# 7. Create detailed commit message referencing test updates
git commit -m "feat: Your feature

- Change 1
- Added X new tests
- All Y tests passing, Z% coverage

See: shared/skills/test_driven_updates.md"
```

## Project Structure Context

When developing, keep this structure in mind:

```
agents-workspace/
├── agents/                    # Agent implementations
│   ├── gcode-parser/         # Parse G-code files
│   ├── cam-runner/           # Calculate cutting parameters
│   ├── cell-scheduler/       # Schedule work orders
│   └── cell-schedule-visualizer/  # Generate dashboards
├── orchestrator/             # Workflow orchestration (LangGraph)
├── shared/                   # Shared utilities
│   └── skills/              # Development patterns & guidelines
├── samples/                  # Test data and workflow definitions
├── tests/                    # Integration tests
└── DEVELOPMENT_GUIDELINES.md # This file
```

## Getting Help

**For development patterns:** See `shared/skills/` directory
- Each file contains detailed patterns and examples
- Follow the skill relevant to your task
- Link to skills in commit messages

**For project structure:** See [README.md](README.md)
- Architecture overview
- How to run workflows
- Test structure
- Available tools

**For specific agents:** See individual agent READMEs
- `agents/gcode-parser/README.md`
- `agents/cam-runner/README.md`
- `agents/cell-scheduler/README.md`
- `agents/cell-schedule-visualizer/README.md`

## Summary

Follow these 3 principles for all development:

1. **Update tests with code** - Use [test_driven_updates.md](shared/skills/test_driven_updates.md)
2. **Follow skill patterns** - Reference `shared/skills/` for your task type
3. **Verify before commit** - Run tests, coverage, format, lint

This ensures:
- ✅ Code quality is maintained
- ✅ Tests are always up-to-date
- ✅ Changes are reviewable and provable
- ✅ Knowledge is preserved in tests
- ✅ Regressions are caught early
