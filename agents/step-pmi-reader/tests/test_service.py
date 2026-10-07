"""Tests for step-pmi-reader FastAPI service.

Coverage:
    - GET  /health          -> 200 (no auth required)
    - GET  /capabilities    -> 200, valid structure (no auth required)
    - POST /api/v1/extract  -> 401 when X-Internal-Key missing
    - POST /api/v1/extract  -> 401 when X-Internal-Key wrong
    - POST /api/v1/extract  -> 200 when fixture STEP file present (skipped otherwise)

OCC dependency handling:
    The domain endpoint (extract_pmi) imports StepPmiReaderAgent lazily inside
    the handler, so importing service.py on the host never triggers an OCC
    ImportError.  Tests that actually *call* the endpoint with a real STEP file
    are skipped when no STEP fixture is available.
"""

import sys
import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup — must happen before any local imports
# ---------------------------------------------------------------------------
AGENT_ROOT = Path(__file__).parent.parent
REPO_ROOT = AGENT_ROOT.parents[1]

# shared.common must be importable
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# src/ must be importable (for step_pmi_reader_agent lazy import inside handler)
if str(AGENT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT / "src"))

# ---------------------------------------------------------------------------
# Set INTERNAL_SERVICE_KEY before importing service (require_internal reads
# os.getenv at *request time*, but we set it here for the test client session)
# ---------------------------------------------------------------------------
TEST_KEY = "test-secret-key-123"
os.environ["INTERNAL_SERVICE_KEY"] = TEST_KEY

from fastapi.testclient import TestClient  # noqa: E402

from src.service import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sample_step_file() -> Path:
    """Return path to a sample STEP file, or None if not present."""
    candidates = [
        AGENT_ROOT / "samples" / "sample_ap242_pmi.stp",
        AGENT_ROOT / "samples" / "sample_minimal_pmi.stp",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_200(self):
        """GET /health is open (no auth) and returns 200."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_payload(self):
        """GET /health returns service name and version."""
        resp = client.get("/health")
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "step-pmi-reader"
        assert "version" in body


# ---------------------------------------------------------------------------
# /capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    def test_capabilities_returns_200(self):
        """GET /capabilities is open (no auth) and returns 200."""
        resp = client.get("/capabilities")
        assert resp.status_code == 200

    def test_capabilities_structure(self):
        """GET /capabilities has required MCP-style keys."""
        resp = client.get("/capabilities")
        body = resp.json()
        assert "service" in body
        assert "version" in body
        assert "tools" in body
        assert isinstance(body["tools"], list)
        assert len(body["tools"]) >= 1

    def test_capabilities_tool_has_endpoint(self):
        """Each tool descriptor must have name, description, endpoint."""
        resp = client.get("/capabilities")
        for tool in resp.json()["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "endpoint" in tool
            assert tool["endpoint"]["method"] in ("GET", "POST", "PUT", "DELETE", "PATCH")


# ---------------------------------------------------------------------------
# POST /api/v1/extract — auth checks (no OCC needed)
# ---------------------------------------------------------------------------


class TestExtractAuth:
    def test_missing_key_returns_401(self):
        """POST /api/v1/extract without X-Internal-Key -> 401."""
        resp = client.post(
            "/api/v1/extract",
            files={"file": ("dummy.stp", b"ISO-10303-21;", "application/octet-stream")},
        )
        assert resp.status_code == 401

    def test_wrong_key_returns_401(self):
        """POST /api/v1/extract with wrong X-Internal-Key -> 401."""
        resp = client.post(
            "/api/v1/extract",
            files={"file": ("dummy.stp", b"ISO-10303-21;", "application/octet-stream")},
            headers={"X-Internal-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_empty_file_with_correct_key_returns_400(self):
        """POST /api/v1/extract with correct key but empty file -> 400."""
        resp = client.post(
            "/api/v1/extract",
            files={"file": ("empty.stp", b"", "application/octet-stream")},
            headers={"X-Internal-Key": TEST_KEY},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/v1/extract — domain (requires OCC inside container, skipped on host)
# ---------------------------------------------------------------------------


class TestExtractDomain:
    def test_extract_with_inline_step_content(self, sample_step_file):
        """POST /api/v1/extract with a real STEP file returns PMI data.

        Skipped when no sample STEP file is available (host without OCC).
        This test will PASS inside the container where pythonocc-core is
        installed and sample files are present.
        """
        if sample_step_file is None:
            pytest.skip("No sample STEP file available — skipping domain test (run in container)")

        with open(sample_step_file, "rb") as fh:
            resp = client.post(
                "/api/v1/extract",
                files={"file": (sample_step_file.name, fh, "application/octet-stream")},
                headers={"X-Internal-Key": TEST_KEY},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "data" in body
        data = body["data"]
        assert "schema" in data
        assert "summary" in data
        assert "datums" in data
        assert "geometric_tolerances" in data
        assert "dimensional_tolerances" in data
        assert "surface_finishes" in data
        assert "annotations" in data

    def test_extract_inline_ap242_content(self):
        """POST /api/v1/extract with minimal inline AP242 content.

        This test uses a tiny synthetic STEP string that exercises the
        text-based parser inside StepPmiReaderAgent.  It does NOT use
        pythonocc-core, so it runs on the host too.

        Skipped only if StepPmiReaderAgent cannot be imported.
        """
        try:
            from step_pmi_reader_agent import StepPmiReaderAgent  # noqa: F401
        except ImportError:
            pytest.skip("StepPmiReaderAgent not importable on this host")

        step_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('AP242 PMI Test'),'2;1');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1 = DATUM('Primary','A');
#2 = FLATNESS_TOLERANCE('TopFace',0.05);
#3 = LINEAR_DIMENSION('Width',100.0,0.1,-0.05);
ENDSEC;
END-ISO-10303-21;"""

        resp = client.post(
            "/api/v1/extract",
            files={"file": ("inline.stp", step_content, "application/octet-stream")},
            headers={"X-Internal-Key": TEST_KEY},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert data["schema"] == "AP242"
        assert data["summary"]["datum_count"] >= 1
        assert data["summary"]["geometric_tolerance_count"] >= 1
        assert data["summary"]["dimensional_tolerance_count"] >= 1
