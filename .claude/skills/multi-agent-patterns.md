---
name: multi-agent-patterns
description: Use when designing multi-agent systems, implementing supervisor patterns, creating swarm architectures, or coordinating multiple agents
---

# Multi-Agent Architecture Patterns

Multi-agent architectures distribute work across multiple language model instances, each with its own context window. The critical insight is that sub-agents exist primarily to isolate context, not to anthropomorphize role division.

## When to Activate

- Single-agent context limits constrain task complexity
- Tasks decompose naturally into parallel subtasks
- Different subtasks require different tool sets or system prompts
- Building systems that must handle multiple domains simultaneously
- Designing production agent systems with multiple specialized components

## Core Patterns

### Pattern 1: Supervisor/Orchestrator

Central agent in control, delegating to specialists and synthesizing results.

```
User Query -> Supervisor -> [Specialist, Specialist, Specialist] -> Aggregation -> Final Output
```

**When to use:** Complex tasks with clear decomposition, tasks requiring coordination across domains

**The Telephone Game Problem:** Supervisors paraphrase sub-agent responses incorrectly, losing fidelity.

**Fix:** Implement `forward_message` tool allowing sub-agents to pass responses directly to users.

### Pattern 2: Peer-to-Peer/Swarm

Removes central control, agents communicate directly based on predefined protocols.

```python
def transfer_to_agent_b():
    return agent_b  # Handoff via function return

agent_a = Agent(
    name="Agent A",
    functions=[transfer_to_agent_b]
)
```

**When to use:** Tasks requiring flexible exploration, tasks with emergent requirements

### Pattern 3: Hierarchical

Agents organized into layers: strategic, planning, and execution.

```
Strategy Layer (Goal Definition) -> Planning Layer (Task Decomposition) -> Execution Layer (Atomic Tasks)
```

**When to use:** Large-scale projects, enterprise workflows

## Context Isolation Mechanisms

**Full context delegation:** Sub-agent receives complete context. Maximum capability but defeats isolation purpose.

**Instruction passing:** Planner creates minimal instructions. Maintains isolation but limits flexibility.

**File system memory:** Agents read/write to persistent storage. Enables shared state without context passing.

## Token Economics

| Architecture | Token Multiplier | Use Case |
|--------------|------------------|----------|
| Single agent chat | 1× baseline | Simple queries |
| Single agent with tools | ~4× baseline | Tool-using tasks |
| Multi-agent system | ~15× baseline | Complex research |

## Failure Modes

**Supervisor Bottleneck:** Implement output schema constraints, use checkpointing.

**Coordination Overhead:** Minimize communication, batch results, use async patterns.

**Divergence:** Define objective boundaries, implement convergence checks, use TTL limits.

**Error Propagation:** Validate outputs before passing, implement retry with circuit breakers.

## LangGraph Integration

For this project's orchestrator:

```python
from langgraph.graph import StateGraph

# Define state
class AgentState(TypedDict):
    messages: list
    current_agent: str
    results: dict

# Create graph with specialized nodes
workflow = StateGraph(AgentState)
workflow.add_node("parser", gcode_parser_node)
workflow.add_node("analyzer", cam_runner_node)
workflow.add_node("scheduler", cell_scheduler_node)

# Add conditional routing
workflow.add_conditional_edges(
    "parser",
    route_by_complexity,
    {"simple": "scheduler", "complex": "analyzer"}
)
```

## Guidelines

1. Design for context isolation as the primary benefit
2. Choose pattern based on coordination needs, not organizational metaphor
3. Implement explicit handoff protocols with state passing
4. Monitor for supervisor bottlenecks
5. Validate outputs between agents
6. Set time-to-live limits to prevent infinite loops
