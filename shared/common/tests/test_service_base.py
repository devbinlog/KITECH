"""Unit tests for shared/common/service_base.py.

Covers:
- require_internal dependency (fail-closed, missing header, wrong key, correct key)
- create_app factory (type, /health, /capabilities, /docs, CORS, middleware)
- make_capability helper
- error_envelope helper
- HTTPException handler shape
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from shared.common.service_base import (
    create_app,
    error_envelope,
    make_capability,
    require_internal,
)
from shared.common.tracing import TraceIdMiddleware


# ---------------------------------------------------------------------------
# require_internal
# ---------------------------------------------------------------------------


class TestRequireInternal:
    """Tests for the require_internal FastAPI dependency."""

    def test_no_env_key_returns_503(self, monkeypatch):
        """When INTERNAL_SERVICE_KEY is not set the service must fail-closed."""
        monkeypatch.delenv("INTERNAL_SERVICE_KEY", raising=False)

        app = FastAPI()

        @app.get("/probe")
        def probe(dep=Depends(require_internal)):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/probe", headers={"X-Internal-Key": "anything"})
        assert resp.status_code == 503

    def test_missing_header_returns_401(self, client):
        """A request with no X-Internal-Key header must be rejected with 401."""
        # /health has no auth; use a protected endpoint created ad-hoc
        app = FastAPI()

        @app.get("/secure")
        def secure(dep=Depends(require_internal)):
            return {"ok": True}

        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/secure")
        # Header defaults to "" which != expected key
        assert resp.status_code == 401

    def test_wrong_key_returns_401(self, client, auth_headers):
        """A request with a wrong key must be rejected with 401."""
        app = FastAPI()

        @app.get("/secure")
        def secure(dep=Depends(require_internal)):
            return {"ok": True}

        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/secure", headers={"X-Internal-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_correct_key_passes(self, monkeypatch):
        """A request with the correct key must not raise."""
        monkeypatch.setenv("INTERNAL_SERVICE_KEY", "secret")

        app = FastAPI()

        @app.get("/secure")
        def secure(dep=Depends(require_internal)):
            return {"ok": True}

        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/secure", headers={"X-Internal-Key": "secret"})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}


# ---------------------------------------------------------------------------
# create_app
# ---------------------------------------------------------------------------


class TestCreateApp:
    """Tests for the create_app factory."""

    def test_returns_fastapi_instance(self, app):
        assert isinstance(app, FastAPI)

    def test_health_endpoint_exists_and_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_structure(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert body["status"] == "ok"
        assert "service" in body
        assert "version" in body

    def test_capabilities_endpoint_exists_and_returns_200(self, client):
        resp = client.get("/capabilities")
        assert resp.status_code == 200

    def test_capabilities_exposes_tools(self, client):
        resp = client.get("/capabilities")
        body = resp.json()
        assert "tools" in body
        assert isinstance(body["tools"], list)
        assert len(body["tools"]) >= 1

    def test_capabilities_contains_service_metadata(self, client):
        resp = client.get("/capabilities")
        body = resp.json()
        assert body["service"] == "test-service"
        assert body["version"] == "0.0.1"
        assert "description" in body

    def test_docs_endpoint_returns_200(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_cors_preflight_includes_allow_origin(self, app):
        """OPTIONS preflight must carry CORS allow headers."""
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Either 200 or 405 — what matters is the CORS header is present
        assert "access-control-allow-origin" in resp.headers

    def test_trace_id_middleware_registered(self, app):
        """TraceIdMiddleware must be in the middleware stack."""
        middleware_types = [
            m.cls for m in app.user_middleware if hasattr(m, "cls")
        ]
        assert TraceIdMiddleware in middleware_types

    def test_additional_setup_callback_called(self):
        """additional_setup callback must be invoked with the app."""
        called_with = []

        def _setup(a):
            called_with.append(a)

        a = create_app(
            name="cb-test",
            version="0.1.0",
            description="callback test",
            capabilities=[],
            additional_setup=_setup,
        )
        assert len(called_with) == 1
        assert called_with[0] is a

    def test_custom_cors_origins(self):
        """Custom cors_origins must be forwarded to CORSMiddleware."""
        a = create_app(
            name="cors-test",
            version="0.1.0",
            description="cors test",
            capabilities=[],
            cors_origins=["https://example.com"],
        )
        c = TestClient(a, raise_server_exceptions=False)
        resp = c.options(
            "/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        origin_header = resp.headers.get("access-control-allow-origin", "")
        assert "example.com" in origin_header or origin_header == "*"


# ---------------------------------------------------------------------------
# make_capability
# ---------------------------------------------------------------------------


class TestMakeCapability:
    """Tests for the make_capability helper."""

    def test_required_fields_present(self):
        cap = make_capability(name="parse", description="Parses gcode", path="/api/v1/parse")
        assert cap["name"] == "parse"
        assert cap["description"] == "Parses gcode"
        assert "endpoint" in cap

    def test_endpoint_contains_method_and_path(self):
        cap = make_capability(name="x", description="x", path="/x")
        assert cap["endpoint"]["path"] == "/x"
        assert "method" in cap["endpoint"]

    def test_default_method_is_post_uppercased(self):
        cap = make_capability(name="x", description="x", path="/x")
        assert cap["endpoint"]["method"] == "POST"

    def test_method_is_uppercased(self):
        cap = make_capability(name="x", description="x", method="post", path="/x")
        assert cap["endpoint"]["method"] == "POST"

    def test_default_idempotent_is_true(self):
        cap = make_capability(name="x", description="x", path="/x")
        assert cap["idempotent"] is True

    def test_idempotent_can_be_false(self):
        cap = make_capability(name="x", description="x", path="/x", idempotent=False)
        assert cap["idempotent"] is False

    def test_default_input_schema_ref_is_none(self):
        cap = make_capability(name="x", description="x", path="/x")
        assert cap["input_schema_ref"] is None

    def test_input_schema_ref_set(self):
        cap = make_capability(
            name="x", description="x", path="/x", input_schema_ref="#/components/schemas/Foo"
        )
        assert cap["input_schema_ref"] == "#/components/schemas/Foo"

    def test_various_methods(self):
        for method in ("GET", "PUT", "DELETE", "PATCH"):
            cap = make_capability(name="x", description="x", method=method, path="/x")
            assert cap["endpoint"]["method"] == method


# ---------------------------------------------------------------------------
# error_envelope
# ---------------------------------------------------------------------------


class TestErrorEnvelope:
    """Tests for the error_envelope helper."""

    def test_returns_nested_error_key(self):
        env = error_envelope("NOT_FOUND", "resource not found")
        assert "error" in env

    def test_code_and_message_fields(self):
        env = error_envelope("CODE", "msg")
        assert env["error"]["code"] == "CODE"
        assert env["error"]["message"] == "msg"

    def test_hint_included_when_provided(self):
        env = error_envelope("CODE", "msg", hint="try again")
        assert env["error"]["hint"] == "try again"

    def test_hint_absent_when_not_provided(self):
        env = error_envelope("CODE", "msg")
        assert "hint" not in env["error"]

    def test_hint_absent_when_none(self):
        env = error_envelope("CODE", "msg", hint=None)
        assert "hint" not in env["error"]


# ---------------------------------------------------------------------------
# HTTPException handler
# ---------------------------------------------------------------------------


class TestHttpExceptionHandler:
    """The registered exception handler must wrap all HTTP errors as error envelopes."""

    def _make_app_with_route(self, status_code: int) -> TestClient:
        from fastapi import HTTPException as FHTTPException

        a = create_app(
            name="err-test",
            version="0.0.0",
            description="error handler test",
            capabilities=[],
        )

        @a.get("/trigger")
        def trigger():
            raise FHTTPException(status_code=status_code, detail="test error")

        return TestClient(a, raise_server_exceptions=False)

    def test_404_returns_error_envelope(self):
        c = self._make_app_with_route(404)
        resp = c.get("/trigger")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_401_returns_error_envelope(self):
        c = self._make_app_with_route(401)
        resp = c.get("/trigger")
        assert resp.status_code == 401
        assert "error" in resp.json()

    def test_500_returns_error_envelope(self):
        c = self._make_app_with_route(500)
        resp = c.get("/trigger")
        assert resp.status_code == 500
        assert "error" in resp.json()

    def test_error_code_includes_status_code(self):
        c = self._make_app_with_route(404)
        resp = c.get("/trigger")
        assert "404" in resp.json()["error"]["code"]
