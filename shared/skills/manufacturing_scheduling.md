# Manufacturing Scheduling Skill

## Description
Solves multi-job scheduling problem using constraint satisfaction (OR-Tools CP-SAT solver). Assigns operations to machines, respects precedence/compatibility constraints, minimizes makespan.

## Input
```json
{
  "work_orders": [
    {
      "wo_id": string,
      "job_id": string,
      "quantity": integer,
      "due_date": "ISO8601 datetime"
    }
  ],
  "operations": [
    {
      "op_id": string,
      "job_id": string,
      "sequence": integer,
      "machine_types_required": [string],
      "duration_minutes": float,
      "setup_time_minutes": float
    }
  ],
  "machines": [
    {
      "machine_id": string,
      "machine_type": string,
      "available_from": "ISO8601 datetime",
      "available_until": "ISO8601 datetime",
      "active": boolean
    }
  ],
  "constraints": {
    "max_horizon_days": integer,
    "consider_tool_changeover": boolean,
    "solver_time_limit_seconds": integer (default: 60)
  }
}
```

## Output
```json
{
  "status": "success" | "no_feasible_solution" | "error",
  "data": {
    "schedule": [
      {
        "operation_id": string,
        "machine_id": string,
        "start_time": "ISO8601 datetime",
        "end_time": "ISO8601 datetime",
        "duration_minutes": float
      }
    ],
    "statistics": {
      "makespan_hours": float,
      "total_operations": integer,
      "scheduled_operations": integer,
      "average_machine_utilization": float (0.0-1.0),
      "bottleneck_machine": string,
      "bottleneck_utilization": float
    },
    "machine_utilization": {
      "machine_id": float (0.0-1.0)
    }
  },
  "errors": [string],
  "warnings": [string]
}
```

## Implementation Notes

### Constraint Model
1. **Decision Variables** (~100+ variables):
   - Start time for each operation on each machine
   - End time (= start + duration)
   - Machine assignment (which machine performs operation)
   - Auxiliary binary variables for disjunctive constraints

2. **Domain Constraints** (~50+):
   - **Machine assignment**: Each operation assigned to exactly one compatible machine
   - **Compatibility**: Machine type must be in operation's machine_types_required
   - **Precedence**: Job operations executed in sequence order
   - **No overlap**: On each machine, no two operations overlap in time
   - **Disjunctive**: For operation pairs on same machine: op1_end ≤ op2_start OR op2_end ≤ op1_start
   - **Time bounds**: All start times ≥ current time, ≤ time horizon
   - **Setup time**: If tool_changeover enabled, add setup duration between different tool types

3. **Objective Function**:
   - Minimize `max(end_time[op] for all operations)` (makespan)

### Solver Strategy
1. **Preprocessing**:
   - Validate inputs (non-negative durations, consistent machine types, etc.)
   - Filter to active machines only
   - Convert datetime to integer minutes (relative to epoch or current time)
   
2. **Model construction**:
   - Create CP-SAT model instance
   - Add variables and constraints as above
   - Set objective function
   
3. **Solving**:
   - Configure solver parameters:
     ```
     max_time_in_seconds = solver_time_limit_seconds
     log_search_progress = True
     num_workers = 4 (parallel threads)
     ```
   - Call solver.Solve()
   
4. **Solution extraction** (if feasible):
   - For each operation: read start_time from solver solution
   - Convert integer minutes back to ISO8601 datetime
   - Calculate end_time = start_time + duration
   - Build schedule array
   
5. **Metrics calculation**:
   - Makespan = max(end_time) - min(start_time)
   - Per-machine utilization = sum(operation durations) / available hours
   - Average utilization = sum(all utilization) / num_machines
   - Bottleneck = machine with highest utilization

### Feasibility Handling
- If `no_feasible_solution` returned by solver:
  - Return status="no_feasible_solution"
  - Log which constraints are unsatisfiable
  - Suggest relaxations (e.g., extend time horizon, reduce operation requirements)

### Edge Cases
- **Zero-duration operations**: Skip scheduling, mark as instant
- **No available machines**: Return error
- **Circular precedence**: Validate job operation sequences; return error if circular
- **All operations already past due**: Return with warning; still find best schedule
- **Machine unavailable**: Filter out; use only active machines in available time window

### Performance Tuning
- **Problem size**: >1000 operations may timeout; consider decomposition (schedule sub-jobs)
- **Symmetry breaking**: Assign operations to lowest-numbered compatible machine (breaks solver symmetry)
- **Incremental solving**: For interactive use, solve for feasibility first (max 10s), then optimize
