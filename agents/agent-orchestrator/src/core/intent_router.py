"""intent_router.py — Bridge between NL-router intent classification and tool selection.

Used by both Mock LLM (for demo) and SLM/strong-LLM modes (as auxiliary hint).
- classify_intent(message) → {intent, entities, confidence} via nl-router HTTP
- select_tools_for_intent(intent) → List[tool_name] (5-7 from mapping yaml)
- build_tool_call(intent_data, mapping) → dict {name, args, id} for AIMessage.tool_calls
- Best-effort: nl-router down → return "unknown" intent
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml

logger = logging.getLogger(__name__)

NL_ROUTER_URL = os.getenv("NL_ROUTER_URL", "http://nl-router:8001")
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "")
DEFAULT_MAPPING_PATH = Path(__file__).parent.parent.parent / "config" / "intent_tool_mapping.yaml"


_mapping_cache: Optional[Dict[str, Any]] = None


def load_mapping(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load intent→tool mapping yaml (cached)."""
    global _mapping_cache
    if _mapping_cache is None:
        p = path or DEFAULT_MAPPING_PATH
        with open(p) as f:
            _mapping_cache = yaml.safe_load(f) or {}
    return _mapping_cache


def _reset_mapping_cache() -> None:
    """Reset the mapping cache (useful in tests)."""
    global _mapping_cache
    _mapping_cache = None


async def classify_intent(message: str, session_id: str = "agent") -> Dict[str, Any]:
    """Call nl-router /classify. Returns {intent, entities, confidence}.

    nl-router 다운 시 fallback {"intent": "unknown", "entities": {}, "confidence": 0.0}.
    """
    from shared.common.tracing import get_trace_id

    headers = {"Content-Type": "application/json"}
    if INTERNAL_SERVICE_KEY:
        headers["X-Internal-Key"] = INTERNAL_SERVICE_KEY
    if tid := get_trace_id():
        headers["X-Trace-Id"] = tid

    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.post(
                f"{NL_ROUTER_URL}/api/v1/nlm/classify",
                json={"query": message, "session_id": session_id},
                headers=headers,
            )
            r.raise_for_status()
            return r.json()
    except Exception as exc:
        logger.warning("nl-router classify failed: %s — fallback to 'unknown'", exc)
        return {"intent": "unknown", "entities": {}, "confidence": 0.0}


def select_tools_for_intent(intent: str, mapping: Optional[Dict] = None) -> List[str]:
    """Return ordered list of tool names for an intent (5-7 max).

    intent에 매핑된 primary tool + secondary 1-2개 + always-available 1-2개.
    unknown intent → DEFAULT_FALLBACK_TOOLS.
    """
    m = mapping or load_mapping()
    mappings = m.get("mappings", {})
    if intent in mappings:
        entry = mappings[intent]
        if isinstance(entry, dict):
            primary = [entry.get("tool")] if entry.get("tool") else []
            secondary = entry.get("secondary", [])
            tools = primary + secondary
        else:
            tools = [entry]
        # always include 1-2 fallback for safety
        fallback = m.get("default_fallback", [])[:2]
        return list(dict.fromkeys(t for t in tools + fallback if t))[:7]
    return m.get("default_fallback", [])[:5]


def build_tool_call(
    intent_data: Dict[str, Any],
    mapping: Optional[Dict] = None,
) -> Optional[Dict[str, Any]]:
    """Build a tool_call dict from intent + entities.

    Returns {id, name, args} or None if intent unmapped.
    """
    m = mapping or load_mapping()
    intent = intent_data.get("intent", "unknown")
    entities = intent_data.get("entities", {})
    mappings = m.get("mappings", {})

    if intent not in mappings:
        return None

    entry = mappings[intent]
    tool_name = entry.get("tool") if isinstance(entry, dict) else entry
    if not tool_name:
        return None

    # Extract args from entities based on mapping
    args: Dict[str, Any] = {}
    args_from_entities = entry.get("args_from_entities", {}) if isinstance(entry, dict) else {}
    for arg_name, entity_name in args_from_entities.items():
        if entity_name in entities:
            args[arg_name] = entities[entity_name]

    # Static args (e.g., default filters)
    static_args = entry.get("args_static", {}) if isinstance(entry, dict) else {}
    args.update(static_args)

    # tool_loader wraps every endpoint in a generic InputModel with a single
    # `payload: Dict[str, Any]` field, so all extracted args go inside `payload`.
    return {
        "id": f"call_{uuid.uuid4().hex[:8]}",
        "name": tool_name,
        "args": {"payload": args},
    }


def summarize_tool_result(intent: str, tool_name: str, result: Any) -> str:
    """Generate Korean natural-language summary of a tool result.

    Templates per intent — fall back to JSON dump if no template.
    """
    from .system_prompts import RESULT_SUMMARY_TEMPLATES

    template = RESULT_SUMMARY_TEMPLATES.get(intent)
    if template:
        try:
            return template.format(result=result, tool=tool_name)
        except (KeyError, IndexError):
            pass
    # Generic fallback
    if isinstance(result, dict):
        keys = list(result.keys())[:3]
        return f"[{tool_name}] 결과: {', '.join(f'{k}={result.get(k)}' for k in keys)}"
    return f"[{tool_name}] 결과 도착 (상세는 trace 참조)"
