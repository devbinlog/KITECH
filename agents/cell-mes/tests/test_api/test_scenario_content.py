"""Tests for PUT /scenarios/{id}/content + GET /scenarios/actions.

Design Ref: §8.2 L1 API Test Scenarios (rows #1-#4 PUT content, #4 catalog)
Plan SC: #2, #7, #8

n8n YAML editor integration M0.
"""

import pytest
from httpx import AsyncClient

from src.app.models.master import Scenario


VALID_YAML_MIN = """\
name: TestScenarioMin
assets:
  - id: A
    name: AAA
steps:
  - id: s1
    name: Step1
    action: "{{acq.main}}/api/move"
"""


VALID_YAML_WITH_NOTES = """\
name: TestScenarioNotes
assets:
  - id: A
    name: AAA
steps:
  - id: s1
    name: Step1
    action: "{{acq.main}}/api/move"
notes:
  - x: 100
    y: 200
    w: 240
    h: 180
    text: "TODO: review"
    color: yellow
"""


INVALID_YAML = """\
name: bad
assets:
  - id: A
    name: AAA
  this is not valid yaml: [unclosed
steps:
"""


# --------------------------------------------------------------------------- #
# Fixture: redirect SCENARIOS_DIR to tmp_path so PUT writes are isolated.
# --------------------------------------------------------------------------- #


@pytest.fixture
def tmp_scenarios_dir(tmp_path, monkeypatch):
    """Point settings.SCENARIOS_DIR to a temp directory for the test."""
    from src.app.core import config as config_mod

    target = tmp_path / "scenarios_root"
    target.mkdir()
    monkeypatch.setattr(config_mod.settings, "SCENARIOS_DIR", str(target), raising=False)
    return target


# --------------------------------------------------------------------------- #
# GET /scenarios/{id}/download
# --------------------------------------------------------------------------- #


class TestScenarioDownload:
    """Test raw scenario file download endpoint."""

    @pytest.mark.asyncio
    async def test_download_scenario_file(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
        tmp_scenarios_dir,
    ):
        """Download returns the raw YAML/XML file as inline text."""
        target = tmp_scenarios_dir / sample_scenario.file_path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(VALID_YAML_MIN, encoding="utf-8")

        response = await client.get(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/yaml; charset=utf-8"
        assert "content-disposition" not in response.headers
        assert response.text == VALID_YAML_MIN

    @pytest.mark.asyncio
    async def test_download_scenario_file_not_found(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
        tmp_scenarios_dir,
    ):
        """Missing scenario file returns 404."""
        response = await client.get(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Scenario file not found on disk"


# --------------------------------------------------------------------------- #
# GET /scenarios/actions
# --------------------------------------------------------------------------- #


class TestActionCatalog:
    """Test GET /scenarios/actions endpoint."""

    @pytest.mark.asyncio
    async def test_actions_unauthorized(self, client: AsyncClient):
        """Unauthorized returns 401."""
        response = await client.get("/api/v1/masters/scenarios/actions")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_actions_returns_catalog(self, client: AsyncClient, auth_headers):
        """Returns non-empty list with required fields."""
        response = await client.get(
            "/api/v1/masters/scenarios/actions", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0
        for item in body["data"]:
            assert "key" in item
            assert "category" in item
            assert "description" in item


# --------------------------------------------------------------------------- #
# PUT /scenarios/{id}/content
# --------------------------------------------------------------------------- #


class TestSaveScenarioContent:
    """Test PUT /scenarios/{id}/content endpoint."""

    @pytest.mark.asyncio
    async def test_save_unauthorized(self, client: AsyncClient, sample_scenario):
        """Unauthorized returns 401."""
        response = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            json={"content": VALID_YAML_MIN},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_valid_yaml(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
        tmp_scenarios_dir,
    ):
        """Valid YAML payload writes file and returns metadata."""
        response = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            headers=auth_headers,
            json={"content": VALID_YAML_MIN},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["id"] == sample_scenario.id
        assert body["file_path"] == sample_scenario.file_path
        assert body["size_bytes"] == len(VALID_YAML_MIN.encode("utf-8"))
        assert body["backup_created"] is False  # No prior file in tmp dir

        # File actually exists with given content
        target = tmp_scenarios_dir / sample_scenario.file_path.lstrip("/")
        assert target.exists()
        assert target.read_text(encoding="utf-8") == VALID_YAML_MIN

    @pytest.mark.asyncio
    async def test_save_creates_backup_on_overwrite(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
        tmp_scenarios_dir,
    ):
        """Second save creates .bak from existing file."""
        # First save (no backup)
        r1 = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            headers=auth_headers,
            json={"content": VALID_YAML_MIN},
        )
        assert r1.status_code == 200
        assert r1.json()["backup_created"] is False

        # Second save (backup of first)
        r2 = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            headers=auth_headers,
            json={"content": VALID_YAML_WITH_NOTES},
        )
        assert r2.status_code == 200
        assert r2.json()["backup_created"] is True

        target = tmp_scenarios_dir / sample_scenario.file_path.lstrip("/")
        bak = target.with_suffix(target.suffix + ".bak")
        assert bak.exists()
        assert bak.read_text(encoding="utf-8") == VALID_YAML_MIN
        assert target.read_text(encoding="utf-8") == VALID_YAML_WITH_NOTES

    @pytest.mark.asyncio
    async def test_save_rejects_invalid_yaml(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
        tmp_scenarios_dir,
    ):
        """Malformed YAML returns 400 with VALIDATION_ERROR detail."""
        response = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            headers=auth_headers,
            json={"content": INVALID_YAML},
        )
        assert response.status_code == 400
        body = response.json()
        # FastAPI wraps detail under 'detail' key
        detail = body.get("detail", body)
        assert detail.get("code") == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_save_rejects_non_dict_root(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
        tmp_scenarios_dir,
    ):
        """YAML whose root is a list/scalar is rejected."""
        response = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            headers=auth_headers,
            json={"content": "- just\n- a\n- list\n"},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", {})
        assert detail.get("code") == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_save_not_found(
        self,
        client: AsyncClient,
        auth_headers,
        tmp_scenarios_dir,
    ):
        """Unknown scenario id returns 404."""
        response = await client.put(
            "/api/v1/masters/scenarios/999999/content",
            headers=auth_headers,
            json={"content": VALID_YAML_MIN},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_save_empty_content_rejected(
        self,
        client: AsyncClient,
        auth_headers,
        sample_scenario,
    ):
        """Empty string is rejected by Pydantic min_length=1."""
        response = await client.put(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/content",
            headers=auth_headers,
            json={"content": ""},
        )
        assert response.status_code == 422
