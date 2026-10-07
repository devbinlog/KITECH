# Workflow Definitions

This directory contains JSON-based workflow definitions for the Orchestrator.

## Available Workflows

### minimal-analysis.json

**Description:** G-code parsing and CAM analysis workflow

**Pipeline:**
```
gcode-parser → cam-runner
```

**Stages:**
- `gcode_parsing` - Parse G-code file and extract machining operations
- `cam_analysis` - Analyze cutting paths using CAM runner

**Usage:**
```bash
uv run orchestrator_main.py \
    --input samples/gcode-parser/simple/001_simple_square.nc \
    --workflow minimal-analysis
```

### full-manufacturing.json

**Description:** Complete manufacturing pipeline with scheduling and visualization

**Pipeline:**
```
gcode-parser → cam-runner → cell-scheduler → cell-schedule-visualizer
```

**Stages:**
- `gcode_parsing` - Parse G-code file and extract machining operations
- `cam_analysis` - Analyze cutting paths using CAM runner
- `cell_scheduling` - Schedule manufacturing operations on cell machines
- `schedule_visualization` - Generate visualization of the schedule

**Usage:**
```bash
uv run orchestrator_main.py \
    --input samples/gcode-parser/ISO10791/ISO10791_001.nc \
    --workflow full-manufacturing
```

## Creating Custom Workflows

To create a new workflow:

1. Create a new JSON file in this directory (e.g., `my-workflow.json`)
2. Follow this structure:

```json
{
  "name": "my-workflow",
  "description": "Your workflow description",
  "version": "1.0",
  "stages": [
    {
      "name": "stage_name",
      "agent": "agent-name",
      "description": "What this stage does",
      "enabled": true,
      "config": {
        "option1": "value1",
        "option2": true
      }
    }
  ]
}
```

3. Use the new workflow:

```bash
uv run orchestrator_main.py --input file.nc --workflow my-workflow
```

## Workflow Configuration

### Stage Fields

- **name** - Unique identifier within workflow (e.g., `gcode_parsing`)
- **agent** - Agent to execute (e.g., `gcode-parser`, `cam-runner`)
- **description** - Human-readable description
- **enabled** - Boolean to enable/disable (default: true)
- **config** - Agent-specific configuration (optional)

### Available Agents

- `gcode-parser` - Parses G-code files
- `cam-runner` - Analyzes cutting paths with CAM parameters
- `cell-scheduler` - Schedules work on manufacturing cells
- `cell-schedule-visualizer` - Generates schedule visualizations

## Workflow Discovery

To list all available workflows:

```bash
uv run orchestrator_main.py --list-workflows
```

To see detailed information about a workflow:

```bash
uv run orchestrator_main.py --workflow-info minimal-analysis
```

## Stage Output

Output from one stage becomes input to the next:

1. Stage 1 processes input → produces output
2. Output stored in `stage_results[stage_name]`
3. Next stage receives previous output as input
4. Continue until all enabled stages complete

## Adding Stages

To extend a workflow, add a new stage object to the `stages` array:

```json
{
  "stages": [
    { ... existing stages ... },
    {
      "name": "new_stage",
      "agent": "agent-name",
      "description": "New processing stage",
      "enabled": true,
      "config": { ... }
    }
  ]
}
```

## Best Practices

1. **Use descriptive names** - Stage names should indicate their purpose
2. **Document configs** - Add comments explaining configuration options
3. **Version your workflows** - Increment version when making changes
4. **Test thoroughly** - Verify workflow outputs match expectations
5. **Keep it simple** - Start with minimal workflows and expand as needed

## Notes

- Workflows are loaded from this directory automatically
- JSON files must be valid JSON
- Agent names must match registered agent names
- Stages execute sequentially in the order defined
- If a stage fails, workflow status becomes "partial"
