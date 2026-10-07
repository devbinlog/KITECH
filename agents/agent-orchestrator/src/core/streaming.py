"""core/streaming.py — Helpers for WebSocket streaming of agent responses.

stream_agent_response() uses a lazy import of graph.builder so that the
module loads cleanly even when the graph sub-package has not been written yet.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict

logger = logging.getLogger(__name__)


async def stream_agent_response(
    session_id: str,
    user_message: str,
) -> AsyncIterator[Dict[str, Any]]:
    """Run the agent graph and yield state-snapshot chunks.

    Each yielded dict has at minimum a ``type`` key:
        {"type": "message", "role": "ai", "content": "..."}
        {"type": "error",   "error": "..."}

    Args:
        session_id: LangGraph thread_id used for checkpointing.
        user_message: The user's natural language query.

    Yields:
        Dicts suitable for JSON serialisation over a WebSocket.
    """
    try:
        from ..graph.builder import get_compiled_graph  # type: ignore[import]
        from langchain_core.messages import HumanMessage
    except ImportError as exc:
        logger.warning("graph.builder not importable: %s", exc)
        yield {"type": "error", "error": f"graph not available: {exc}"}
        return

    try:
        graph = await get_compiled_graph()
    except Exception as exc:
        logger.exception("get_compiled_graph raised")
        yield {"type": "error", "error": f"graph init failed: {exc}"}
        return

    config: Dict[str, Any] = {"configurable": {"thread_id": session_id}}
    state_input: Dict[str, Any] = {"messages": [HumanMessage(content=user_message)]}

    try:
        async for event in graph.astream(state_input, config=config, stream_mode="values"):
            messages = event.get("messages", [])
            if messages:
                last = messages[-1]
                yield {
                    "type": "message",
                    "role": getattr(last, "type", "ai"),
                    "content": getattr(last, "content", str(last)),
                }
    except Exception as exc:
        logger.exception("graph.astream raised")
        yield {"type": "error", "error": str(exc)}
