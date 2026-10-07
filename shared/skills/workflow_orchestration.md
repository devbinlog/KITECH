# Workflow Orchestration Skill

## Description
Manages multi-stage directed acyclic graph (DAG) workflows using LangGraph. Chains agent outputs as inputs to downstream stages, maintains state threading, handles failures gracefully with optional checkpoint persistence.

## Input
```json
{
  "workflow_definition": {
    "name": string,
    "stages": [
      {
        "stage_name": string,
        "agent_name": string (e.g., "gcode_parser", "cam_runner", "cell_scheduler"),
        "enabled": boolean,
        "input_mapping": {
          "field_name": "path.to.previous.stage.output"
        },
        "timeout_seconds": integer (optional)
      }
    ]
  },
  "initial_input": {
    "gcode_source": string,
    "tool": object,
    "material": object
  },
  "checkpoint_db_path": string (optional, for state recovery)
}
```

## Output
```json
{
  "status": "success" | "partial_success" | "error",
  "data": {
    "stages_completed": [string],
    "stages_failed": [string],
    "stage_results": {
      "stage_name": object (output from each stage)
    },
    "execution_summary": {
      "total_duration_seconds": float,
      "stage_timings": {
        "stage_name": float (seconds)
      }
    }
  },
  "errors": [
    {
      "stage": string,
      "error": string,
      "timestamp": "ISO8601 datetime"
    }
  ]
}
```

## Implementation Notes

### State Threading Architecture

**WorkflowState Schema**:
```python
@dataclass
class WorkflowState:
    input_data: dict          # Initial/accumulated input
    stages_completed: list    # Reducer: accumulates completed stage names
    stages_failed: list       # Reducer: accumulates failed stage names
    stage_results: dict       # Merged stage outputs (key: stage_name)
```

**Execution Flow**:
1. Initialize WorkflowState with input_data
2. For each enabled stage:
   - Receive current WorkflowState (includes all prior stage results)
   - Perform stage work (call agent)
   - Return Dict[field: value] with results
   - LangGraph auto-merges returned dict into state → available to next stage
3. Downstream stages read merged state (implicit threading, no manual dict passing)

**State Merging Example**:
```
Stage 1 (gcode_parser) returns: {"blocks": [...], "total_distance": 100}
  → LangGraph merges into WorkflowState.stage_results["gcode_parser"]

Stage 2 (cam_runner) reads: WorkflowState.stage_results["gcode_parser"]["blocks"]
  → Performs CAM analysis
  → Returns: {"tool_engagement": {...}}
  → LangGraph merges into WorkflowState.stage_results["cam_runner"]

Stage 3 (cell_scheduler) reads both Stage 1 and Stage 2 results via state
```

### Node Creation & Graph Construction

**Per-stage node definition**:
```
For each enabled stage:
  1. Create wrapper function: async def stage_node(state: WorkflowState) → dict
  2. Inside wrapper:
     a. Resolve input_mapping references → replace "path.to.x" with actual values
     b. Call agent.execute(resolved_inputs)
     c. Wrap in try-catch
     d. If success: return {stage_name: result, "stages_completed": [stage_name]}
     e. If error: return {"stages_failed": [stage_name], "error_detail": {...}}
  3. Add node to graph: graph.add_node(stage_name, stage_node)
```

**Graph construction sequence**:
1. Create `StateGraph(WorkflowState)`
2. Add nodes for each enabled stage (skip disabled)
3. Create edges in sequence order: stage1 → stage2 → stage3 → ...
4. Set `start_node` to first enabled stage
5. Compile: `graph.compile()`

### Input Mapping Resolution

**Mapping syntax**: `"path.to.value"` = nested dict access
```
Example mapping:
{
  "blocks": "gcode_parser.blocks",
  "tool_engagement": "cam_runner.tool_engagement"
}

Resolution algorithm:
  1. Start with WorkflowState.stage_results as root
  2. Split path by "." → ["gcode_parser", "blocks"]
  3. Traverse: stage_results["gcode_parser"]["blocks"]
  4. If key not found: log warning, use empty dict default
```

**Error handling in mapping**:
- If reference path doesn't exist → use `{}` and log warning
- If intermediate key missing → treat as no-op (don't halt)
- Allow explicit overrides via additional input dict parameter

### Error Propagation Strategy

**Per-stage error handling**:
```python
try:
    result = agent.execute(inputs)
    state["stages_completed"].append(stage_name)
    return {"stage_results": {stage_name: result}}
except Exception as e:
    state["stages_failed"].append(stage_name)
    state["errors"].append({
        "stage": stage_name,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    })
    return {}  # Continue to next stage (don't halt workflow)
```

**Workflow-level status**:
- `status="success"` if all stages succeeded
- `status="partial_success"` if some stages failed but others completed
- `status="error"` if all stages failed or graph construction failed

### Checkpointing & State Recovery (Optional)

**Checkpoint storage**:
- If `checkpoint_db_path` provided: persist WorkflowState to SQLite after each stage
- Record: stage_name, timestamp, state_snapshot (JSON serialized)

**Recovery logic**:
- On workflow restart: query checkpoint DB for last completed stage
- Resume from next stage (skip already-completed ones)
- Load intermediate state from checkpoint

**Use case**: Long-running workflows (>1 hour); interruption resilience

### Stage Timing & Metrics

**Timing collection**:
```python
import time

for stage_name in enabled_stages:
    start = time.time()
    result = execute_stage(stage_name, state)
    elapsed = time.time() - start
    stage_timings[stage_name] = elapsed
```

**Execution summary output**:
```json
{
  "total_duration_seconds": 120.5,
  "stage_timings": {
    "gcode_parser": 2.3,
    "cam_runner": 15.7,
    "cell_scheduler": 95.2,
    "schedule_visualization": 7.3
  }
}
```

### Edge Cases & Validation

1. **Circular dependencies**: Validate that no stage's input references a later stage (DAG check)
2. **Missing agents**: If agent_name not registered → error, don't create stage
3. **No enabled stages**: Return error (empty workflow)
4. **Timeout**: Use asyncio timeout wrapper; if exceeded, mark stage as failed, continue
5. **Large state objects**: Consider compression/streaming if state > 100MB
