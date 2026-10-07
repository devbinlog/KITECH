# /sync - Sync Dependencies

Sync project dependencies using uv package manager.

## Usage

```
/sync
```

## Execution Steps

1. **Sync all dependencies**:
   ```bash
   uv sync
   ```

2. **Verify Python version**:
   ```bash
   uv run python --version
   ```
   Should be Python 3.11.x

3. **List installed packages** (optional):
   ```bash
   uv pip list
   ```

## Important

- This project REQUIRES uv package manager
- NEVER use `pip install` directly
- All dependencies are managed via `pyproject.toml` and `uv.lock`

## Why uv?

- Unified dependency management across workspace members
- Consistent Python version (3.11) across all developers
- Fast performance with optimized resolution
- Lock file guarantee (uv.lock) for reproducible builds
- Workspace support for monorepo structure

## First Time Setup

If this is your first time:

```bash
# 1. Install uv (if needed)
pip install uv

# 2. Sync all dependencies
uv sync

# 3. Verify installation
uv run python --version  # Should be Python 3.11.x
```

## Example Output

```
Syncing dependencies...

Resolved 45 packages in 1.2s
Installed 12 packages in 0.8s

Python version: 3.11.13
Dependencies synchronized successfully!
```