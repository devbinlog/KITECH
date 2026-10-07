"""Tests for POST/GET/POST cancel scenario test-runs.

Forces the simulator path (N8N_FORCE_SIMULATOR=1) so tests don't require
a live n8n container. Verifies the contract surface and lifecycle:
queued -> running -> success / cancelled.

Design Ref: §8.2 L1 API rows #5-7 (test-runs / cancel)
Plan SC: #10 (Test Run -> 노드별 success/error)
"""

import asyncio
import os

# Force simulator BEFORE the n8n_runner module is imported.
os.environ["N8N_FORCE_SIMULATOR"] = "1"

import pytest
from httpx import AsyncClient


VALID_WORKFLOW = {
    "name": "TestRun",
    "nodes": [
        {
            "id": "n1",
            "name": "Manual Trigger",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {},
        },
        {
            "id": "n2",
            "name": "Step 1",
            "type": "n8n-nodes-scenario.scenarioStep",
            "typeVersion": 1,
            "position": [240, 0],
            "parameters": {"stepId": "1-1", "stepName": "first"},
        },
        {
            "id": "sticky",
            "name": "Sticky Note",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [0, 200],
            "parameters": {"content": "review"},
        },
    ],
    "connections": {},
}


class TestTestRunLifecycle:
    @pytest.mark.asyncio
    async def test_unauthorized(self, client: AsyncClient, sample_scenario):
        response = await client.post(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/test-runs",
            json={"workflow": VALID_WORKFLOW},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_returns_execution_id(
        self, client: AsyncClient, auth_headers, sample_scenario
    ):
        r = await client.post(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/test-runs",
            headers=auth_headers,
            json={"workflow": VALID_WORKFLOW},
        )
        assert r.status_code == 202, r.text
        body = r.json()
        assert body["execution_id"].startswith("exec_")
        assert body["status"] in {"queued", "running"}

    @pytest.mark.asyncio
    async def test_status_progresses_to_success(
        self, client: AsyncClient, auth_headers, sample_scenario, monkeypatch
    ):
        import src.app.services.n8n_runner as n8n_runner
        from src.app.services.n8n_runner import get_execution

        # Speed up simulator: zero-duration per node so task finishes instantly.
        monkeypatch.setattr(n8n_runner, "_SIM_NODE_DURATION_MS", 0)

        r = await client.post(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/test-runs",
            headers=auth_headers,
            json={"workflow": VALID_WORKFLOW},
        )
        assert r.status_code == 202, r.text
        execution_id = r.json()["execution_id"]

        # Await the background task directly — deterministic, no wall-clock wait.
        state = get_execution(execution_id)
        assert state is not None
        if state._task and not state._task.done():
            await asyncio.wait_for(state._task, timeout=5)

        poll = await client.get(
            f"/api/v1/masters/scenarios/test-runs/{execution_id}",
            headers=auth_headers,
        )
        assert poll.status_code == 200
        body = poll.json()

        assert body["status"] == "success"
        # Sticky note must NOT have an executable status entry.
        assert "sticky" not in body["nodes"]
        # Manual trigger and Step 1 nodes should both have a 'success' entry.
        assert body["nodes"]["n1"]["status"] == "success"
        assert body["nodes"]["n2"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_cancel_running_execution(
        self, client: AsyncClient, auth_headers, sample_scenario, monkeypatch
    ):
        import src.app.services.n8n_runner as n8n_runner
        from src.app.services.n8n_runner import get_execution

        # Use a nonzero but very short duration so the task is still running
        # when we cancel — just long enough to be in-flight.
        monkeypatch.setattr(n8n_runner, "_SIM_NODE_DURATION_MS", 5)

        # A heavier workflow so we can cancel before it finishes.
        wf = dict(VALID_WORKFLOW)
        wf["nodes"] = [
            {
                "id": f"step-{i}",
                "name": f"Step {i}",
                "type": "n8n-nodes-scenario.scenarioStep",
                "typeVersion": 1,
                "position": [i * 240, 0],
                "parameters": {},
            }
            for i in range(20)
        ]
        r = await client.post(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/test-runs",
            headers=auth_headers,
            json={"workflow": wf},
        )
        execution_id = r.json()["execution_id"]

        # Wait until the execution task has actually started (status becomes
        # "running") rather than sleeping for a fixed wall-clock duration.
        state = get_execution(execution_id)
        assert state is not None
        for _ in range(100):
            if state.status == "running":
                break
            await asyncio.sleep(0)  # yield to event loop
        # Cancel immediately once running.
        cancel = await client.post(
            f"/api/v1/masters/scenarios/test-runs/{execution_id}/cancel",
            headers=auth_headers,
        )
        assert cancel.status_code == 200, cancel.text
        assert cancel.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_status_404_for_unknown_id(
        self, client: AsyncClient, auth_headers
    ):
        r = await client.get(
            "/api/v1/masters/scenarios/test-runs/exec_nope",
            headers=auth_headers,
        )
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_404_for_unknown_id(
        self, client: AsyncClient, auth_headers
    ):
        r = await client.post(
            "/api/v1/masters/scenarios/test-runs/exec_nope/cancel",
            headers=auth_headers,
        )
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_create_404_for_unknown_scenario(
        self, client: AsyncClient, auth_headers
    ):
        r = await client.post(
            "/api/v1/masters/scenarios/999999/test-runs",
            headers=auth_headers,
            json={"workflow": VALID_WORKFLOW},
        )
        assert r.status_code == 404
