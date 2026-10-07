"""Tests for NL-Router FastAPI API routes.

Uses httpx.AsyncClient + ASGITransport for in-process testing.
NL-Router pyproject.toml has asyncio_mode = "auto", so no @pytest.mark.asyncio needed.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from src.app.main import app
from src.understanding.intents import Intent, IntentResult
from src.understanding.entities import ExtractedEntities, Entity, EntityType
from src.nl_router_agent import NLRouterAgent, QueryResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_intent_result(intent: Intent, confidence: float = 0.9, **kwargs) -> IntentResult:
    return IntentResult(intent=intent, confidence=confidence, **kwargs)


def _make_entities(*entity_pairs) -> ExtractedEntities:
    """Build ExtractedEntities from (EntityType, value) pairs."""
    entities = [
        Entity(type=t, value=v, raw_text=v)
        for t, v in entity_pairs
    ]
    return ExtractedEntities(entities=entities)


def _mock_http_response(status_code: int = 200, json_data: dict = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# Fixture: patch the singleton NLRouterAgent
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_agent():
    """Return a pre-configured mock NLRouterAgent."""
    agent = NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")
    return agent


@pytest.fixture
def patched_app(mock_agent):
    """Patch get_nl_router so every request uses mock_agent."""
    with patch("src.app.routes.query.get_nl_router", return_value=mock_agent):
        yield mock_agent


# ---------------------------------------------------------------------------
# POST /api/v1/nlm/query — valid input
# ---------------------------------------------------------------------------


async def test_query_valid_korean_production(patched_app):
    """POST /query with valid Korean text → 200 with success=True."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.PRODUCTION_STATUS, confidence=0.95)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query",
                json={"query": "오늘 생산 현황 보여줘"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["intent"] == Intent.PRODUCTION_STATUS.value


async def test_query_valid_korean_equipment(patched_app):
    """POST /query with equipment query → 200."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.EQUIPMENT_STATUS)
        me.return_value = _make_entities((EntityType.EQUIPMENT_ID, "EQ-001"))
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query",
                json={"query": "CNC-001 설비 상태 어때?"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == Intent.EQUIPMENT_STATUS.value


async def test_query_response_schema_fields(patched_app):
    """Response must include all required QueryResponse fields."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.KPI_QUERY)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query",
                json={"query": "가동률 알려줘"},
            )

    assert resp.status_code == 200
    body = resp.json()
    for field in ("success", "intent", "entities", "data", "text_response", "errors"):
        assert field in body, f"Missing field: {field}"


async def test_query_with_session_id_in_body(patched_app):
    """session_id provided in body → tracked in debug (via header propagation)."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.PRODUCTION_STATUS)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query",
                json={"query": "생산 현황", "session_id": "sess-abc"},
            )

    assert resp.status_code == 200


async def test_query_with_session_id_in_header(patched_app):
    """session_id provided via X-Session-ID header → 200."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.PRODUCTION_STATUS)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query",
                json={"query": "생산 현황"},
                headers={"X-Session-ID": "sess-header-123"},
            )

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/nlm/query — invalid / empty input
# ---------------------------------------------------------------------------


async def test_query_empty_string_returns_422():
    """Empty string fails pydantic min_length=1 → 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/nlm/query",
            json={"query": ""},
        )
    assert resp.status_code == 422


async def test_query_whitespace_only_returns_422():
    """Whitespace-only query fails field_validator → 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/nlm/query",
            json={"query": "   "},
        )
    assert resp.status_code == 422


async def test_query_missing_body_returns_422():
    """Missing required 'query' field → 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/nlm/query",
            json={},
        )
    assert resp.status_code == 422


async def test_query_too_long_returns_422():
    """Query exceeding max_length=500 → 422."""
    long_query = "가" * 501
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/nlm/query",
            json={"query": long_query},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/nlm/classify
# ---------------------------------------------------------------------------


async def test_classify_intent_production(patched_app):
    """POST /classify → returns intent + confidence."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc:
        mc.return_value = _make_intent_result(
            Intent.PRODUCTION_STATUS, confidence=0.92,
            requires_clarification=False, suggested_questions=[]
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/classify",
                json={"query": "오늘 생산량"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == Intent.PRODUCTION_STATUS.value
    assert isinstance(body["confidence"], float)
    assert "requires_clarification" in body


async def test_classify_intent_equipment(patched_app):
    """POST /classify → equipment intent correctly identified."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc:
        mc.return_value = _make_intent_result(
            Intent.EQUIPMENT_STATUS, confidence=0.88,
            requires_clarification=False, suggested_questions=[]
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/classify",
                json={"query": "CNC 설비 상태"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == Intent.EQUIPMENT_STATUS.value


async def test_classify_empty_query_returns_422():
    """POST /classify with empty query → 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/nlm/classify",
            json={"query": ""},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/nlm/conversation/{session_id}/history
# ---------------------------------------------------------------------------


async def test_get_history_session_not_found():
    """GET /conversation/{id}/history for unknown session → 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/nlm/conversation/nonexistent-session-xyz/history")
    assert resp.status_code == 404


async def test_get_history_after_query(patched_app):
    """History endpoint returns data after a query creates a session."""
    agent = patched_app
    session_id = "test-history-session-999"

    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.PRODUCTION_STATUS)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create session via query
            await client.post(
                "/api/v1/nlm/query",
                json={"query": "생산 현황", "session_id": session_id},
            )
            # Now fetch history
            resp = await client.get(f"/api/v1/nlm/conversation/{session_id}/history")

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert "messages" in body
    assert "active_entities" in body


# ---------------------------------------------------------------------------
# DELETE /api/v1/nlm/conversation/{session_id}
# ---------------------------------------------------------------------------


async def test_clear_conversation_returns_message():
    """DELETE /conversation/{id} → returns confirmation message."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.delete("/api/v1/nlm/conversation/any-session-to-clear")
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body


# ---------------------------------------------------------------------------
# Health & root endpoints
# ---------------------------------------------------------------------------


async def test_health_endpoint():
    """GET /health → healthy."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


async def test_root_endpoint():
    """GET / → service info."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "NL Router Gateway"
    assert body["status"] == "running"


async def test_skills_endpoint():
    """GET /api/v1/nlm/skills → lists skills."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/nlm/skills")
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "skills" in body
    assert isinstance(body["skills"], list)


async def test_intents_endpoint():
    """GET /api/v1/nlm/intents → lists supported intents."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/nlm/intents")
    assert resp.status_code == 200
    body = resp.json()
    assert "intents" in body
    # UNKNOWN should not be listed
    intent_names = [i["name"] for i in body["intents"]]
    assert Intent.UNKNOWN.value not in intent_names


# ---------------------------------------------------------------------------
# POST /api/v1/nlm/query/debug
# ---------------------------------------------------------------------------


async def test_query_debug_includes_debug_info(patched_app):
    """POST /query/debug → response includes debug_info field."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.KPI_QUERY)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query/debug",
                json={"query": "KPI 보여줘"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert "debug_info" in body


# ---------------------------------------------------------------------------
# Deprecation headers
# ---------------------------------------------------------------------------


async def test_query_returns_deprecation_headers(patched_app):
    """POST /query → response includes Deprecation header."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.PRODUCTION_STATUS)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query",
                json={"query": "오늘 생산 현황"},
            )

    assert resp.status_code == 200
    assert resp.headers.get("deprecation") == "true"
    assert "successor-version" in resp.headers.get("link", "")


async def test_query_debug_returns_deprecation_headers(patched_app):
    """POST /query/debug → response includes Deprecation header."""
    agent = patched_app
    with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
         patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
        mc.return_value = _make_intent_result(Intent.KPI_QUERY)
        me.return_value = _make_entities()
        agent._http_client = AsyncMock()
        agent._http_client.request = AsyncMock(return_value=_mock_http_response(200, {}))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/nlm/query/debug",
                json={"query": "KPI 보여줘"},
            )

    assert resp.status_code == 200
    assert resp.headers.get("deprecation") == "true"


# ---------------------------------------------------------------------------
# GET /capabilities
# ---------------------------------------------------------------------------


async def test_capabilities_returns_service_info():
    """GET /capabilities → returns nl-router service + tools list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/capabilities")

    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "nl-router"
    assert "version" in body
    assert "description" in body
    assert isinstance(body["tools"], list)
    assert len(body["tools"]) >= 1


async def test_capabilities_classify_intent_tool():
    """GET /capabilities → classify_intent tool is declared correctly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/capabilities")

    assert resp.status_code == 200
    body = resp.json()
    tool_names = [t["name"] for t in body["tools"]]
    assert "classify_intent" in tool_names

    classify_tool = next(t for t in body["tools"] if t["name"] == "classify_intent")
    assert classify_tool["idempotent"] is True
    assert classify_tool["endpoint"]["method"] == "POST"
    assert "/classify" in classify_tool["endpoint"]["path"]
