"""graph/state.py — LangGraph AgentState definition."""
from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    tools_used: Annotated[List[Dict[str, Any]], operator.add]
    session_id: str
    trace_id: str
    # planner/executor/critic extended state
    plan: Optional[Dict[str, Any]]    # Planner output
    revision_count: int                # Critic retry count (max 2)
    final_answer: Optional[str]        # Final answer that passed Critic
    # react graph extended state
    active_tools: List[str]            # Tool names selected for current intent
    intent: Optional[str]              # Classified intent for current turn
