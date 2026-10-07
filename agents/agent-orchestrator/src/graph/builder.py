"""graph/builder.py — Builds and caches the compiled LangGraph agent graph."""
import logging
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .nodes import (
    make_reasoning_node,
    should_continue,
    make_planner_node,
    make_executor_node,
    make_critic_node,
    critic_routing,
    intent_classify_node,
)

logger = logging.getLogger(__name__)
_compiled = None


async def build_agent_graph():
    """Build graph based on ORCHESTRATOR_PIPELINE env var.

    ORCHESTRATOR_PIPELINE=react (default) → single ReAct loop with intent classify.
    ORCHESTRATOR_PIPELINE=multi_agent     → planner → executor → critic pipeline.
    """
    pipeline = os.getenv("ORCHESTRATOR_PIPELINE", "react").lower()
    if pipeline == "multi_agent":
        return await _build_multi_agent_graph()
    return await _build_react_graph()


async def _build_react_graph():
    """Single ReAct loop: intent_classify → reasoning → (tool_call →) reasoning → END."""
    from ..core.llm_provider import get_chat_model

    try:
        from ..core.tool_loader import load_tools_from_registry
    except ImportError:
        load_tools_from_registry = None

    try:
        from ..core.checkpoint import get_saver
    except ImportError:
        get_saver = None

    model = get_chat_model()
    tools = []
    if load_tools_from_registry:
        try:
            tools = await load_tools_from_registry()
        except Exception as exc:
            logger.warning("tool loader failed: %s", exc)

    saver = None
    if get_saver:
        try:
            saver = await get_saver()
        except Exception as exc:
            logger.warning("checkpoint saver failed (in-memory): %s", exc)

    g = StateGraph(AgentState)
    g.add_node("intent_classify", intent_classify_node)
    g.add_node("reasoning", make_reasoning_node(model, tools))
    if tools:
        g.add_node("tool_call", ToolNode(tools))
    g.set_entry_point("intent_classify")
    g.add_edge("intent_classify", "reasoning")
    if tools:
        g.add_conditional_edges("reasoning", should_continue, {"tool_call": "tool_call", "end": END})
        g.add_edge("tool_call", "reasoning")
    else:
        g.add_edge("reasoning", END)
    return g.compile(checkpointer=saver) if saver else g.compile()


async def _build_multi_agent_graph():
    """Planner → executor → critic pipeline (original multi-agent flow)."""
    from ..core.llm_provider import get_chat_model

    try:
        from ..core.tool_loader import load_tools_from_registry
    except ImportError:
        load_tools_from_registry = None

    try:
        from ..core.checkpoint import get_saver
    except ImportError:
        get_saver = None

    model = get_chat_model()
    tools = []
    if load_tools_from_registry:
        try:
            tools = await load_tools_from_registry()
        except Exception as exc:
            logger.warning("tool loader failed: %s", exc)

    saver = None
    if get_saver:
        try:
            saver = await get_saver()
        except Exception as exc:
            logger.warning("checkpoint saver failed (in-memory): %s", exc)

    graph = StateGraph(AgentState)
    graph.add_node("planner", make_planner_node(model))
    graph.add_node("executor", make_executor_node(model, tools))
    graph.add_node("critic", make_critic_node(model))

    if tools:
        graph.add_node("tool_call", ToolNode(tools))

    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")

    if tools:
        graph.add_conditional_edges(
            "executor",
            should_continue,
            {"tool_call": "tool_call", "end": "critic"},
        )
        graph.add_edge("tool_call", "executor")
    else:
        graph.add_edge("executor", "critic")

    graph.add_conditional_edges(
        "critic",
        critic_routing,
        {"executor": "executor", "end": END},
    )

    return graph.compile(checkpointer=saver) if saver else graph.compile()


async def get_compiled_graph():
    """Return the cached compiled graph, building it on first call."""
    global _compiled
    if _compiled is None:
        _compiled = await build_agent_graph()
    return _compiled
