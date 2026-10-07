"""Unit tests for shared/common/tracing.py.

Covers:
- TraceIdMiddleware: propagation, generation, response echo, context reset
- get_trace_id: outside request (None), inside request (value exists)
- TraceIdLogFilter: injects trace_id attribute, default "-" outside request
- _new_trace_id: 16-char hex, unique per call
"""
from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.common.tracing import (
    TRACE_ID_HEADER,
    TraceIdLogFilter,
    TraceIdMiddleware,
    _new_trace_id,
    get_trace_id,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tracing_app() -> FastAPI:
    """Minimal app with TraceIdMiddleware and an endpoint that echoes the trace id."""
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    @app.get("/echo-trace")
    def echo_trace():
        return {"trace_id": get_trace_id()}

    return app


# ---------------------------------------------------------------------------
# _new_trace_id
# ---------------------------------------------------------------------------


class TestNewTraceId:
    def test_is_16_chars(self):
        tid = _new_trace_id()
        assert len(tid) == 16

    def test_is_hex(self):
        tid = _new_trace_id()
        int(tid, 16)  # raises ValueError if not valid hex

    def test_unique_on_each_call(self):
        ids = {_new_trace_id() for _ in range(20)}
        assert len(ids) == 20


# ---------------------------------------------------------------------------
# get_trace_id outside a request
# ---------------------------------------------------------------------------


class TestGetTraceIdOutsideRequest:
    def test_returns_none_outside_request(self):
        # contextvar default is None; outside any middleware it must be None
        assert get_trace_id() is None


# ---------------------------------------------------------------------------
# TraceIdMiddleware
# ---------------------------------------------------------------------------


class TestTraceIdMiddleware:
    def setup_method(self):
        self.app = _make_tracing_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_incoming_trace_id_propagated_to_contextvar(self):
        """When X-Trace-Id is sent, the endpoint receives that exact id."""
        resp = self.client.get("/echo-trace", headers={TRACE_ID_HEADER: "abcd1234efgh5678"})
        assert resp.status_code == 200
        assert resp.json()["trace_id"] == "abcd1234efgh5678"

    def test_missing_trace_id_generates_new_one(self):
        """When no X-Trace-Id is sent, a new 16-char hex id is generated."""
        resp = self.client.get("/echo-trace")
        assert resp.status_code == 200
        tid = resp.json()["trace_id"]
        assert tid is not None
        assert len(tid) == 16
        int(tid, 16)  # valid hex

    def test_trace_id_echoed_on_response_header(self):
        """The response must carry X-Trace-Id matching what was used internally."""
        resp = self.client.get("/echo-trace", headers={TRACE_ID_HEADER: "feedcafe12345678"})
        assert resp.headers.get(TRACE_ID_HEADER) == "feedcafe12345678"

    def test_generated_trace_id_echoed_on_response_header(self):
        """Generated id must also be echoed on the response header."""
        resp = self.client.get("/echo-trace")
        echoed = resp.headers.get(TRACE_ID_HEADER)
        assert echoed is not None
        assert len(echoed) == 16

    def test_context_reset_after_request(self):
        """After the request completes, the contextvar must be reset to None."""
        self.client.get("/echo-trace", headers={TRACE_ID_HEADER: "1234567890abcdef"})
        # Outside the request scope the contextvar must be back to None
        assert get_trace_id() is None

    def test_response_trace_id_matches_contextvar_value(self):
        """The echoed header value must equal the value seen inside the handler."""
        resp = self.client.get("/echo-trace")
        body_trace = resp.json()["trace_id"]
        header_trace = resp.headers.get(TRACE_ID_HEADER)
        assert body_trace == header_trace


# ---------------------------------------------------------------------------
# get_trace_id inside a request
# ---------------------------------------------------------------------------


class TestGetTraceIdInsideRequest:
    def test_trace_id_is_non_none_inside_handler(self):
        app = _make_tracing_app()
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/echo-trace")
        assert resp.json()["trace_id"] is not None

    def test_incoming_id_matches_get_trace_id(self):
        app = _make_tracing_app()
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/echo-trace", headers={TRACE_ID_HEADER: "cafe0000cafe0000"})
        assert resp.json()["trace_id"] == "cafe0000cafe0000"


# ---------------------------------------------------------------------------
# TraceIdLogFilter
# ---------------------------------------------------------------------------


class TestTraceIdLogFilter:
    def _make_record(self) -> logging.LogRecord:
        return logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )

    def test_filter_returns_true(self):
        f = TraceIdLogFilter()
        record = self._make_record()
        assert f.filter(record) is True

    def test_trace_id_attribute_injected(self):
        f = TraceIdLogFilter()
        record = self._make_record()
        f.filter(record)
        assert hasattr(record, "trace_id")

    def test_trace_id_is_dash_outside_request(self):
        f = TraceIdLogFilter()
        record = self._make_record()
        f.filter(record)
        assert record.trace_id == "-"

    def test_trace_id_is_actual_value_inside_request(self):
        """Inside a live request the filter must inject the real trace id."""
        app = FastAPI()
        app.add_middleware(TraceIdMiddleware)

        captured: dict = {}

        @app.get("/log-filter-test")
        def log_filter_test():
            f = TraceIdLogFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="hello",
                args=(),
                exc_info=None,
            )
            f.filter(record)
            captured["trace_id"] = record.trace_id
            return {"ok": True}

        c = TestClient(app, raise_server_exceptions=False)
        c.get("/log-filter-test", headers={TRACE_ID_HEADER: "deadbeefdeadbeef"})
        assert captured["trace_id"] == "deadbeefdeadbeef"
