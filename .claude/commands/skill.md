# /skill - Load Development Skill

Load and reference a development skill from `shared/skills/` directory.

## Usage

```
/skill <skill-name>
```

Available skills:
- `test_driven_updates` - Code change workflow, test synchronization
- `test_implementation` - pytest fixtures, test patterns
- `error_handling` - Try-catch patterns, AnalysisResult
- `config_management` - YAML/JSON loading, validation
- `data_validation` - Dataclass definition, type coercion
- `code_documentation` - Docstrings, README, API specs
- `performance_optimization` - Profiling, bottleneck analysis
- `dependency_integration` - Optional dependencies, fallbacks

## Execution Steps

1. **Load skill file**:
   ```
   Read: shared/skills/<skill-name>.md
   ```

2. **Display key sections**:
   - Description
   - Workflow/Patterns
   - Code Examples
   - Anti-patterns to avoid

3. **Apply to current task**:
   - Follow the patterns defined in the skill
   - Reference the skill in commit messages

## Example

User: `/skill error_handling`

Result:
```
Loading skill: error_handling

== Error Handling Skill ==

Key Patterns:
1. Always wrap external calls in try-except
2. Use AnalysisResult structure for return values
3. Log errors with context (logger.error with args)
4. Propagate errors through workflow stages

Example:
def execute(self, inputs):
    try:
        result = self.process(inputs)
        return AnalysisResult(status="success", data=result)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return AnalysisResult(status="error", errors=[str(e)])

Applying this pattern to your current task...
```