"""graph/nodes.py — LangGraph node factories for agent reasoning."""
import json
import logging
import re
from typing import Any, Dict, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from .state import AgentState

logger = logging.getLogger(__name__)


def _try_parse_json(text: str):
    """Attempt to parse JSON from raw text or a ```json ... ``` block."""
    try:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        return json.loads(text)
    except Exception:
        return None


def make_reasoning_node(model: BaseChatModel, tools: List[Any]):
    """Return an async reasoning node bound to the given model and tools."""
    bound = model.bind_tools(tools) if tools else model

    async def reasoning(state: AgentState) -> Dict[str, Any]:
        msgs = state["messages"]
        try:
            response = await bound.ainvoke(msgs)
        except NotImplementedError:
            response = bound.invoke(msgs)
        return {"messages": [response]}

    return reasoning


def should_continue(state: AgentState) -> str:
    """Routing function: 'tool_call' if last message has tool calls, else 'end'."""
    last = state["messages"][-1] if state["messages"] else None
    if last and getattr(last, "tool_calls", None):
        return "tool_call"
    return "end"


def make_planner_node(model: BaseChatModel):
    """Planner: user request → step-by-step plan (no tool calls)."""

    async def planner(state: AgentState) -> Dict[str, Any]:
        from .personas import PLANNER_PROMPT
        msgs = [SystemMessage(content=PLANNER_PROMPT)] + list(state["messages"])
        try:
            response = await model.ainvoke(msgs)
        except NotImplementedError:
            response = model.invoke(msgs)
        plan = _try_parse_json(response.content) if hasattr(response, "content") else None
        return {"messages": [response], "plan": plan}

    return planner


def make_executor_node(model: BaseChatModel, tools: List[Any]):
    """Executor: receives plan + tools and runs the ReAct loop."""
    bound = model.bind_tools(tools) if tools else model

    async def executor(state: AgentState) -> Dict[str, Any]:
        from .personas import EXECUTOR_PROMPT
        msgs = [SystemMessage(content=EXECUTOR_PROMPT)] + list(state["messages"])
        try:
            response = await bound.ainvoke(msgs)
        except NotImplementedError:
            response = bound.invoke(msgs)
        return {"messages": [response]}

    return executor


def make_critic_node(model: BaseChatModel):
    """Critic: reviews executor answer and emits approved / revision_needed verdict."""

    async def critic(state: AgentState) -> Dict[str, Any]:
        from .personas import CRITIC_PROMPT
        msgs = [SystemMessage(content=CRITIC_PROMPT)] + list(state["messages"])
        try:
            response = await model.ainvoke(msgs)
        except NotImplementedError:
            response = model.invoke(msgs)
        verdict = _try_parse_json(response.content) if hasattr(response, "content") else None
        revision_count = state.get("revision_count", 0)
        if verdict and verdict.get("verdict") == "approved":
            last_ai = next(
                (m for m in reversed(state["messages"]) if getattr(m, "type", None) == "ai"),
                None,
            )
            return {
                "messages": [response],
                "final_answer": getattr(last_ai, "content", "") if last_ai else "",
            }
        return {
            "messages": [response],
            "revision_count": revision_count + 1,
        }

    return critic


def critic_routing(state: AgentState) -> str:
    """Critic routing: 'end' if approved or max revisions reached, else 'executor'."""
    if state.get("final_answer"):
        return "end"
    if state.get("revision_count", 0) >= 2:
        return "end"  # max revisions exhausted
    return "executor"


async def intent_classify_node(state: AgentState) -> Dict[str, Any]:
    """Classify the user's intent and select relevant tools + system prompt."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from ..core.intent_router import classify_intent, select_tools_for_intent
    from ..core.system_prompts import build_system_prompt

    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if not last_human:
        return {}
    intent_data = await classify_intent(str(last_human.content), state.get("session_id", "agent"))
    intent = intent_data.get("intent", "unknown")
    tool_names = select_tools_for_intent(intent)
    sys_prompt = build_system_prompt(intent, tool_names)
    return {
        "messages": [SystemMessage(content=sys_prompt)],
        "active_tools": tool_names,
        "intent": intent,
    }
