"""test_tool_loader.py — tool_loader with mocked httpx + YAML registry."""
import textwrap
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


FAKE_YAML = textwrap.dedent("""\
    services:
      - name: cell-scheduler
        base_url: http://cell-scheduler:8000
        capabilities: true
      - name: agent-orchestrator
        base_url: http://agent-orchestrator:8000
        capabilities: true
""")

FAKE_CAPS = {
    "tools": [
        {
            "name": "schedule",
            "description": "Schedule a job",
            "endpoint": {"method": "POST", "path": "/api/v1/schedule"},
        }
    ]
}


@pytest.mark.anyio
async def test_load_tools_returns_list(tmp_path):
    yaml_file = tmp_path / "registry.yaml"
    yaml_file.write_text(FAKE_YAML)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=FAKE_CAPS)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        from src.core.tool_loader import load_tools_from_registry
        tools = await load_tools_from_registry(yaml_path=str(yaml_file))

    # cell-scheduler is included; agent-orchestrator is excluded by default
    assert len(tools) == 1
    assert tools[0].name == "cell-scheduler__schedule"


@pytest.mark.anyio
async def test_load_tools_handles_failed_capabilities(tmp_path):
    yaml_file = tmp_path / "registry.yaml"
    yaml_file.write_text(FAKE_YAML)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        from src.core.tool_loader import load_tools_from_registry
        tools = await load_tools_from_registry(yaml_path=str(yaml_file))

    assert tools == []
