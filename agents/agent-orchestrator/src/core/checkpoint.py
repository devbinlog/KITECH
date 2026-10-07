"""core/checkpoint.py — SqliteSaver wrapper + session trace helper.

Provides a lazy singleton AsyncSqliteSaver and a helper used by
/sessions/{id}/trace to retrieve checkpointed conversation state.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

# UUIDv4 pattern — validated before any saver interaction to prevent IDOR
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Lazy singleton saver
# ---------------------------------------------------------------------------

_saver: Optional[Any] = None  # AsyncSqliteSaver once initialised
_saver_cm: Optional[Any] = None  # context manager — kept alive to prevent GC-triggered close
_conn: Optional[Any] = None  # aiosqlite.Connection — kept alive (alternative path)


def get_db_path() -> str:
    """Return the SQLite database path from env or the container default."""
    return os.getenv(
        "ORCHESTRATOR_DB_PATH",
        "/app/agents/agent-orchestrator/data/conversations.db",
    )


async def get_saver() -> Any:
    """Return (and lazily initialise) the AsyncSqliteSaver singleton.

    Strategy: build aiosqlite.Connection directly + pass to AsyncSqliteSaver.
    This avoids the async-context-manager GC trap where `from_conn_string()`'s
    CM closes the connection if the CM goes out of scope.
    """
    global _saver, _saver_cm, _conn
    if _saver is None:
        import aiosqlite  # type: ignore[import]
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver  # type: ignore[import]

        _conn = await aiosqlite.connect(get_db_path(), check_same_thread=False)
        _saver = AsyncSqliteSaver(_conn)
        if hasattr(_saver, "setup"):
            try:
                await _saver.setup()
            except Exception:
                pass
    return _saver


# ---------------------------------------------------------------------------
# Trace helper
# ---------------------------------------------------------------------------


async def load_session_trace(session_id: str) -> Dict[str, Any]:
    """Load the latest checkpoint for a thread and return a trace dict.

    Raises ValueError for invalid/non-UUIDv4 session_id so callers cannot
    pass arbitrary strings to the SQLite layer (defence-in-depth vs IDOR).

    Returns:
        {"messages": [...], "tools_used": [...]}
        Both lists are empty when no checkpoint exists or on error.
    """
    if not session_id or not _UUID_RE.match(session_id):
        raise ValueError(f"session_id must be UUIDv4, got: {session_id!r}")

    saver = await get_saver()
    config = {"configurable": {"thread_id": session_id}}
    try:
        snapshot = await saver.aget(config)
        if not snapshot:
            return {"messages": [], "tools_used": []}
        return {
            "messages": [
                _msg_to_dict(m) for m in snapshot.values.get("messages", [])
            ],
            "tools_used": snapshot.values.get("tools_used", []),
        }
    except Exception:
        return {"messages": [], "tools_used": []}


def _msg_to_dict(msg: Any) -> Dict[str, Any]:
    return {
        "type": getattr(msg, "type", "unknown"),
        "content": getattr(msg, "content", str(msg)),
    }
