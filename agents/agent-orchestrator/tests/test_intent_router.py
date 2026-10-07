"""test_intent_router.py — Tests for intent_router core module."""
import textwrap
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_MAPPING: Dict[str, Any] = {
    "version": "1.0",
    "mappings": {
        "production_status": {
            "tool": "cell-mes__get_equipment_utilization",
            "args_from_entities": {"date": "date"},
            "secondary": ["cell-mes__list_work_orders"],
        },
        "equipment_status": {
            "tool": "cell-mes__list_equipments",
            "secondary": ["cell-mes__list_alarms"],
        },
        "alarm_query": {
            "tool": "cell-mes__list_alarms",
            "args_from_entities": {"level": "level"},
        },
    },
    "default_fallback": [
        "cell-mes__list_work_orders",
        "cell-mes__list_equipments",
    ],
}


@pytest.fixture(autouse=True)
def reset_mapping_cache():
    """Ensure mapping cache is cleared between tests."""
    from src.core.intent_router import _reset_mapping_cache
    _reset_mapping_cache()
    yield
    _reset_mapping_cache()


# ---------------------------------------------------------------------------
# classify_intent — success path
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_classify_intent_success():
    """classify_intent returns nl-router JSON on success."""
    expected = {"intent": "production_status", "entities": {"date": "today"}, "confidence": 0.95}

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=expected)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch("shared.common.tracing.get_trace_id", return_value="trace-001"):
            from src.core.intent_router import classify_intent
            result = await classify_intent("오늘 생산 현황 보여줘", session_id="test-session")

    assert result["intent"] == "production_status"
    assert result["entities"] == {"date": "today"}
    assert result["confidence"] == 0.95

    # Verify trace header was forwarded
    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["headers"]["X-Trace-Id"] == "trace-001"


# ---------------------------------------------------------------------------
# classify_intent — nl-router down (fallback)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_classify_intent_fallback_on_connection_error():
    """classify_intent returns unknown intent when nl-router is down."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch("shared.common.tracing.get_trace_id", return_value=None):
            from src.core.intent_router import classify_intent
            result = await classify_intent("오늘 생산 현황", session_id="test")

    assert result["intent"] == "unknown"
    assert result["entities"] == {}
    assert result["confidence"] == 0.0


@pytest.mark.anyio
async def test_classify_intent_fallback_on_http_error():
    """classify_intent falls back on HTTP 4xx/5xx errors."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(side_effect=Exception("500 Internal Server Error"))

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch("shared.common.tracing.get_trace_id", return_value=None):
            from src.core.intent_router import classify_intent
            result = await classify_intent("알람 조회", session_id="test")

    assert result["intent"] == "unknown"


# ---------------------------------------------------------------------------
# select_tools_for_intent
# ---------------------------------------------------------------------------

def test_select_tools_known_intent():
    """Known intent returns primary + secondary + fallback (deduped, max 7)."""
    from src.core.intent_router import select_tools_for_intent

    tools = select_tools_for_intent("production_status", mapping=MINIMAL_MAPPING)

    # primary tool must be first
    assert tools[0] == "cell-mes__get_equipment_utilization"
    # secondary included
    assert "cell-mes__list_work_orders" in tools
    # fallback included
    assert "cell-mes__list_equipments" in tools
    # total <= 7
    assert len(tools) <= 7


def test_select_tools_no_duplicates():
    """select_tools_for_intent does not return duplicates."""
    from src.core.intent_router import select_tools_for_intent

    tools = select_tools_for_intent("production_status", mapping=MINIMAL_MAPPING)
    assert len(tools) == len(set(tools))


def test_select_tools_unknown_intent_returns_fallback():
    """Unknown intent returns default_fallback list."""
    from src.core.intent_router import select_tools_for_intent

    tools = select_tools_for_intent("unknown", mapping=MINIMAL_MAPPING)
    assert tools == ["cell-mes__list_work_orders", "cell-mes__list_equipments"]


def test_select_tools_unmapped_intent_returns_fallback():
    """Completely unmapped intent (not in mappings) returns default_fallback."""
    from src.core.intent_router import select_tools_for_intent

    tools = select_tools_for_intent("totally_unknown_intent", mapping=MINIMAL_MAPPING)
    assert tools == ["cell-mes__list_work_orders", "cell-mes__list_equipments"]


# ---------------------------------------------------------------------------
# build_tool_call
# ---------------------------------------------------------------------------

def test_build_tool_call_with_entities():
    """build_tool_call extracts entity values into args."""
    from src.core.intent_router import build_tool_call

    intent_data = {
        "intent": "production_status",
        "entities": {"date": "2025-01-15"},
        "confidence": 0.9,
    }
    result = build_tool_call(intent_data, mapping=MINIMAL_MAPPING)

    assert result is not None
    assert result["name"] == "cell-mes__get_equipment_utilization"
    assert result["args"]["date"] == "2025-01-15"
    assert result["id"].startswith("call_")


def test_build_tool_call_no_matching_entities():
    """build_tool_call returns non-empty args even when entities don't match."""
    from src.core.intent_router import build_tool_call

    intent_data = {
        "intent": "production_status",
        "entities": {},  # no date entity
        "confidence": 0.8,
    }
    result = build_tool_call(intent_data, mapping=MINIMAL_MAPPING)

    assert result is not None
    assert result["name"] == "cell-mes__get_equipment_utilization"
    # must be non-empty for ToolNode compatibility
    assert result["args"] == {"payload": {}}


def test_build_tool_call_unknown_intent_returns_none():
    """build_tool_call returns None for unmapped intent."""
    from src.core.intent_router import build_tool_call

    intent_data = {"intent": "unknown", "entities": {}, "confidence": 0.0}
    result = build_tool_call(intent_data, mapping=MINIMAL_MAPPING)

    assert result is None


def test_build_tool_call_id_is_unique():
    """Each build_tool_call returns a unique id."""
    from src.core.intent_router import build_tool_call

    intent_data = {"intent": "equipment_status", "entities": {}, "confidence": 0.9}
    r1 = build_tool_call(intent_data, mapping=MINIMAL_MAPPING)
    r2 = build_tool_call(intent_data, mapping=MINIMAL_MAPPING)

    assert r1 is not None
    assert r2 is not None
    assert r1["id"] != r2["id"]


# ---------------------------------------------------------------------------
# summarize_tool_result
# ---------------------------------------------------------------------------

def test_summarize_tool_result_template_match():
    """summarize_tool_result uses template when intent is known."""
    from src.core.intent_router import summarize_tool_result

    result = summarize_tool_result(
        "equipment_status",
        "cell-mes__list_equipments",
        {"total": 10, "running": 7, "idle": 3},
    )
    assert "10" in result
    assert "7" in result
    assert "3" in result


def test_summarize_tool_result_dict_fallback():
    """summarize_tool_result falls back to key=value for unknown intent."""
    from src.core.intent_router import summarize_tool_result

    result = summarize_tool_result(
        "schedule_solve",
        "cell-scheduler__solve_schedule",
        {"job_id": "abc", "status": "queued"},
    )
    assert "cell-scheduler__solve_schedule" in result
    assert "job_id" in result


def test_summarize_tool_result_non_dict_fallback():
    """summarize_tool_result handles non-dict results gracefully."""
    from src.core.intent_router import summarize_tool_result

    result = summarize_tool_result("schedule_view", "cell-scheduler__list_solvers", "ok")
    assert "cell-scheduler__list_solvers" in result


# ---------------------------------------------------------------------------
# load_mapping — file-based
# ---------------------------------------------------------------------------

def test_load_mapping_from_file(tmp_path):
    """load_mapping reads yaml from given path."""
    from src.core.intent_router import load_mapping, _reset_mapping_cache

    mapping_file = tmp_path / "test_mapping.yaml"
    mapping_file.write_text(yaml.dump(MINIMAL_MAPPING))

    _reset_mapping_cache()
    m = load_mapping(path=mapping_file)
    assert "production_status" in m["mappings"]
    _reset_mapping_cache()
