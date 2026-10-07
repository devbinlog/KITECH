"""Integration tests for TORUS Mock Server API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.app.main import app
from src.app.services.machine_store import get_store, reset_store


@pytest.fixture(autouse=True)
def setup_store():
    """Reset and load store for each test."""
    from pathlib import Path

    reset_store()
    store = get_store()
    store.load_from_json(Path(__file__).parent.parent / "data" / "default_machines.json")
    yield
    reset_store()


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Test health check."""

    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "torus-mock"
        assert data["machines"] == 2


class TestMachinesEndpoint:
    """Test /api/v1/machines endpoints."""

    @pytest.mark.asyncio
    async def test_list_machines(self, client):
        resp = await client.get("/api/v1/machines")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["machines"]) == 2

    @pytest.mark.asyncio
    async def test_get_machine(self, client):
        resp = await client.get("/api/v1/machines/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["machineName"] == "FANUC-Mill-01"
        assert data["vendorName"] == "FANUC"

    @pytest.mark.asyncio
    async def test_get_machine_not_found(self, client):
        resp = await client.get("/api/v1/machines/99")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_channel(self, client):
        resp = await client.get("/api/v1/machines/1/channel/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["numberOfAxes"] == 3

    @pytest.mark.asyncio
    async def test_get_channel_not_found(self, client):
        resp = await client.get("/api/v1/machines/1/channel/99")
        assert resp.status_code == 404


class TestDataEndpoint:
    """Test /api/v1/data endpoints."""

    @pytest.mark.asyncio
    async def test_get_axis_position(self, client):
        resp = await client.get(
            "/api/v1/data",
            params={
                "address": "data://machine/channel/axis/machinePosition",
                "filter": "machine=1&channel=1&axis=1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["value"], (int, float))

    @pytest.mark.asyncio
    async def test_get_multiple_axes(self, client):
        resp = await client.get(
            "/api/v1/data",
            params={
                "address": "data://machine/channel/axis/axisName",
                "filter": "machine=1&channel=1&axis=1-3",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["value"] == ["X", "Y", "Z"]

    @pytest.mark.asyncio
    async def test_update_writable_field(self, client):
        resp = await client.put(
            "/api/v1/data",
            json={
                "address": "data://machine/channel/axis/axisLimitPlus",
                "filter": "machine=1&channel=1&axis=1",
                "value": 600.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["value"] == 600.0

        # Verify
        resp2 = await client.get(
            "/api/v1/data",
            params={
                "address": "data://machine/channel/axis/axisLimitPlus",
                "filter": "machine=1&channel=1&axis=1",
            },
        )
        assert resp2.json()["value"] == 600.0

    @pytest.mark.asyncio
    async def test_update_readonly_fails(self, client):
        resp = await client.put(
            "/api/v1/data",
            json={
                "address": "data://machine/channel/axis/machinePosition",
                "filter": "machine=1&channel=1&axis=1",
                "value": 999.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "read-only" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_batch_get(self, client):
        resp = await client.post(
            "/api/v1/data/batch",
            json={
                "items": [
                    {
                        "address": "data://machine/channel/axis/axisName",
                        "filter": "machine=1&channel=1&axis=1",
                    },
                    {
                        "address": "data://machine/ncMemory/totalCapacity",
                        "filter": "machine=1",
                    },
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["value"] == "X"
        assert data["items"][1]["value"] == 2097152.0


class TestPlcEndpoint:
    """Test /api/v1/plc endpoints."""

    @pytest.mark.asyncio
    async def test_read_plc(self, client):
        resp = await client.get(
            "/api/v1/plc",
            params={"machine": 1, "type": 1, "startAddress": 0, "count": 4},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 4

    @pytest.mark.asyncio
    async def test_write_plc(self, client):
        resp = await client.put(
            "/api/v1/plc",
            json={"machine": 1, "type": 2, "startAddress": 0, "data": [True, True, False]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_write_readonly_plc_fails(self, client):
        resp = await client.put(
            "/api/v1/plc",
            json={"machine": 1, "type": 1, "startAddress": 0, "data": [True]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False


class TestFilesEndpoint:
    """Test /api/v1/files endpoints."""

    @pytest.mark.asyncio
    async def test_list_files(self, client):
        resp = await client.get("/api/v1/files", params={"machine": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["files"]) >= 1

    @pytest.mark.asyncio
    async def test_download_file(self, client):
        resp = await client.get(
            "/api/v1/files/download",
            params={"machine": 1, "name": "O0001"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "content" in data


class TestSimulationEndpoint:
    """Test /api/v1/simulation endpoints."""

    @pytest.mark.asyncio
    async def test_status(self, client):
        resp = await client.get("/api/v1/simulation/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is False

    @pytest.mark.asyncio
    async def test_start_stop(self, client):
        # Start
        resp = await client.post("/api/v1/simulation/start", params={"interval_ms": 100})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Check status
        resp = await client.get("/api/v1/simulation/status")
        assert resp.json()["running"] is True

        # Stop
        resp = await client.post("/api/v1/simulation/stop")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.asyncio
    async def test_trigger_alarm(self, client):
        resp = await client.post(
            "/api/v1/simulation/trigger-alarm",
            json={
                "machine": 1,
                "channel": 1,
                "alarmNumber": "5000",
                "alarmText": "Test alarm",
                "alarmCategory": "WARNING",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["alarm"]["alarmNumber"] == "5000"

    @pytest.mark.asyncio
    async def test_tool_change(self, client):
        resp = await client.post(
            "/api/v1/simulation/tool-change",
            json={"machine": 1, "channel": 1, "toolNumber": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["tool"]["toolNumber"] == 2


class TestSubscribeEndpoint:
    """Test /api/v1/subscribe endpoints."""

    @pytest.mark.asyncio
    async def test_subscribe(self, client):
        resp = await client.post(
            "/api/v1/subscribe",
            json={
                "address": "data://machine/channel/axis/machinePosition",
                "filter": "machine=1&channel=1&axis=1",
                "interval": 500,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "subscriptionId" in data
        assert data["address"] == "data://machine/channel/axis/machinePosition"

    @pytest.mark.asyncio
    async def test_unsubscribe(self, client):
        # Subscribe first
        resp = await client.post(
            "/api/v1/subscribe",
            json={
                "address": "data://machine/channel/axis/machinePosition",
                "filter": "machine=1&channel=1&axis=1",
            },
        )
        sub_id = resp.json()["subscriptionId"]

        # Unsubscribe
        resp = await client.delete(f"/api/v1/subscribe/{sub_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, client):
        resp = await client.get("/api/v1/subscribe")
        assert resp.status_code == 200
        assert "subscriptions" in resp.json()
