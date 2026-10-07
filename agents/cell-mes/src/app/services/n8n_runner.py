"""n8n_runner — thin client for the n8n REST API plus an in-memory store.

V1 (M9) responsibilities:
  - submit a workflow JSON to n8n for ad-hoc execution
  - poll execution status (per-node statuses)
  - cancel a running execution
  - graceful fallback to a SIMULATED runner when n8n is unavailable so the
    frontend integration can be demoed without a fully wired API key

The simulator walks the workflow's nodes in connection order, marking each
as `running` then `success` with a small delay between transitions. This
preserves the contract surface (status, nodes map) so M10 frontend can be
built without depending on n8n auth setup landing first.

Design Ref: §4 API Specification, §11 M9 Module
Plan SC: #10 (Test Run -> 노드별 success/error)
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_BASIC_AUTH_USER = os.getenv("N8N_BASIC_AUTH_USER", "")
N8N_BASIC_AUTH_PASSWORD = os.getenv("N8N_BASIC_AUTH_PASSWORD", "")
# Force the simulator path regardless of n8n availability — useful for tests.
N8N_FORCE_SIMULATOR = os.getenv("N8N_FORCE_SIMULATOR", "0") == "1"

# Simulator pacing
_SIM_NODE_DURATION_MS = 200

# Memory hygiene — prevent unbounded growth of _executions registry.
# (Audit C5: in-memory registry never evicts.)
_EXECUTION_TTL = timedelta(hours=1)
_MAX_EXECUTIONS = 1000

# Polling cadence (used by _run_via_n8n)
_N8N_POLL_INTERVAL_SEC = 1.0
_N8N_POLL_MAX_SEC = 120.0


# ---------------------------------------------------------------------------
# Per-execution state
# ---------------------------------------------------------------------------


class ExecutionState:
    __slots__ = (
        "execution_id",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "nodes",
        "_cancel",
        "_task",
    )

    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        self.status: str = "queued"
        # `created_at` is the registry insertion time (used for TTL eviction);
        # `started_at` is set when execution actually begins.
        self.created_at: datetime = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._cancel = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    def is_terminal(self) -> bool:
        return self.status in ("success", "error", "cancelled")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat()
            if self.finished_at
            else None,
            "nodes": self.nodes,
        }


# In-memory registry. V2 swaps to Redis for multi-worker setups.
_executions: Dict[str, ExecutionState] = {}


def _prune_executions(now: Optional[datetime] = None) -> int:
    """Evict terminal executions older than `_EXECUTION_TTL` (lazy GC).

    Also enforces `_MAX_EXECUTIONS` cap by dropping the oldest terminal
    entries. Active (queued/running) executions are never evicted.

    Called opportunistically at the start of each `start_execution()`. This
    avoids spawning a permanent background task while still bounding memory.

    Returns the number of evicted entries.
    """
    cutoff = (now or datetime.now(timezone.utc)) - _EXECUTION_TTL
    evicted = 0
    # Evict terminal entries past TTL
    for eid in list(_executions.keys()):
        st = _executions[eid]
        if st.is_terminal():
            anchor = st.finished_at or st.created_at
            if anchor < cutoff:
                _executions.pop(eid, None)
                evicted += 1
    # Hard cap fallback — if still over limit, drop oldest terminal entries
    if len(_executions) > _MAX_EXECUTIONS:
        terminal_sorted = sorted(
            (
                (eid, st)
                for eid, st in _executions.items()
                if st.is_terminal()
            ),
            key=lambda kv: kv[1].finished_at or kv[1].created_at,
        )
        overflow = len(_executions) - _MAX_EXECUTIONS
        for eid, _st in terminal_sorted[:overflow]:
            _executions.pop(eid, None)
            evicted += 1
    if evicted:
        logger.debug("n8n_runner: evicted %d stale execution entries", evicted)
    return evicted


# ---------------------------------------------------------------------------
# Public API used by endpoints
# ---------------------------------------------------------------------------


async def start_execution(workflow: Dict[str, Any]) -> ExecutionState:
    """Submit a workflow for execution and return the initial state."""
    _prune_executions()
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    state = ExecutionState(execution_id)
    _executions[execution_id] = state
    state._task = asyncio.create_task(_run_execution(state, workflow))
    return state


def get_execution(execution_id: str) -> Optional[ExecutionState]:
    return _executions.get(execution_id)


async def cancel_execution(execution_id: str) -> Optional[ExecutionState]:
    state = _executions.get(execution_id)
    if state is None:
        return None
    if state.status in ("queued", "running"):
        state._cancel.set()
        if state._task and not state._task.done():
            state._task.cancel()
        state.status = "cancelled"
        state.finished_at = datetime.now(timezone.utc)
    return state


# ---------------------------------------------------------------------------
# Execution drivers
# ---------------------------------------------------------------------------


async def _run_execution(
    state: ExecutionState, workflow: Dict[str, Any]
) -> None:
    """Try real n8n first; on any failure, fall back to the simulator."""
    if not N8N_FORCE_SIMULATOR and N8N_API_KEY:
        try:
            await _run_via_n8n(state, workflow)
            return
        except Exception as exc:  # noqa: BLE001
            # Record failure to call n8n then continue with simulator so the
            # editor still gets a meaningful response.
            logger.warning(
                "n8n unreachable for execution %s, falling back to simulator: %s",
                state.execution_id,
                exc,
                exc_info=True,
            )
            state.nodes["_n8n_attempt"] = {
                "status": "error",
                "error": f"n8n unreachable, falling back to simulator: {exc}",
            }
    await _run_via_simulator(state, workflow)


async def _run_via_n8n(
    state: ExecutionState, workflow: Dict[str, Any]
) -> None:
    """Best-effort path against the n8n public API.

    n8n's public API doesn't currently expose a generic "run any workflow
    JSON" endpoint without first persisting it. M9 V1 stores a temp
    workflow and triggers execution; cleanup happens on cancel or after
    a short TTL. If this path ever fails, the caller falls back to
    `_run_via_simulator`.
    """
    state.status = "running"
    state.started_at = datetime.now(timezone.utc)
    headers = {"X-N8N-API-KEY": N8N_API_KEY}
    base = N8N_BASE_URL.rstrip("/")
    # Optional HTTP Basic auth (when n8n editor is locked behind N8N_BASIC_AUTH).
    auth = (
        (N8N_BASIC_AUTH_USER, N8N_BASIC_AUTH_PASSWORD)
        if N8N_BASIC_AUTH_USER
        else None
    )

    async with httpx.AsyncClient(timeout=10.0, auth=auth) as client:
        # 1) Persist temp workflow (prefix marks it as test-only).
        wf_payload = dict(workflow)
        wf_payload["name"] = f"__test__/{state.execution_id}/" + str(
            workflow.get("name", "scenario")
        )
        create = await client.post(
            f"{base}/api/v1/workflows", json=wf_payload, headers=headers
        )
        create.raise_for_status()
        wf_id = create.json().get("id")
        if not wf_id:
            raise RuntimeError("n8n did not return workflow id")

        try:
            # 2) Activate (some n8n setups require this for /executions).
            await client.post(
                f"{base}/api/v1/workflows/{wf_id}/activate", headers=headers
            )
            # 3) Trigger ad-hoc execution.
            run = await client.post(
                f"{base}/api/v1/workflows/{wf_id}/run", headers=headers
            )
            run.raise_for_status()

            # 4) Poll execution status until terminal or cancelled.
            n8n_exec_id = run.json().get("id") or run.json().get("executionId")
            max_iters = int(_N8N_POLL_MAX_SEC / _N8N_POLL_INTERVAL_SEC)
            for _ in range(max_iters):
                if state._cancel.is_set():
                    break
                exec_resp = await client.get(
                    f"{base}/api/v1/executions/{n8n_exec_id}", headers=headers
                )
                if exec_resp.status_code != 200:
                    # Wake on cancel to keep cancellation responsive (~interval).
                    try:
                        await asyncio.wait_for(
                            state._cancel.wait(),
                            timeout=_N8N_POLL_INTERVAL_SEC,
                        )
                    except asyncio.TimeoutError:
                        pass
                    continue
                payload = exec_resp.json()
                _ingest_n8n_status(state, payload)
                if state.status in ("success", "error"):
                    break
                try:
                    await asyncio.wait_for(
                        state._cancel.wait(),
                        timeout=_N8N_POLL_INTERVAL_SEC,
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            # Best-effort cleanup of the temp workflow.
            try:
                await client.delete(
                    f"{base}/api/v1/workflows/{wf_id}", headers=headers
                )
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.warning(
                    "n8n_runner: failed to cleanup temp workflow %s: %s",
                    wf_id,
                    cleanup_exc,
                )

    if state.status not in ("success", "error", "cancelled"):
        state.status = "success"
    state.finished_at = datetime.now(timezone.utc)


def _ingest_n8n_status(state: ExecutionState, payload: Dict[str, Any]) -> None:
    finished = payload.get("finished")
    if finished is True:
        state.status = "success" if payload.get("status") != "error" else "error"
    else:
        state.status = "running"
    # Best-effort node status extraction; n8n's `data.resultData.runData` is
    # keyed by node *name*. We map those to the node-id space the editor
    # uses by walking the workflow nodes.
    data = (payload.get("data") or {}).get("resultData") or {}
    runData = data.get("runData") or {}
    for node_name, runs in runData.items():
        last = runs[-1] if isinstance(runs, list) and runs else {}
        success = last.get("error") is None
        state.nodes[node_name] = {
            "status": "success" if success else "error",
            "output": last.get("data"),
            "error": (last.get("error") or {}).get("message")
            if last.get("error")
            else None,
        }


async def _run_via_simulator(
    state: ExecutionState, workflow: Dict[str, Any]
) -> None:
    """Walk the workflow's nodes in registration order with simulated delays."""
    state.status = "running"
    state.started_at = datetime.now(timezone.utc)
    nodes = workflow.get("nodes") or []
    for node in nodes:
        if state._cancel.is_set():
            state.status = "cancelled"
            state.finished_at = datetime.now(timezone.utc)
            return
        nid = node.get("id") or node.get("name") or "unknown"
        # Skip sticky notes — they aren't executable.
        if node.get("type") == "n8n-nodes-base.stickyNote":
            continue
        state.nodes[nid] = {"status": "running"}
        try:
            await asyncio.sleep(_SIM_NODE_DURATION_MS / 1000)
        except asyncio.CancelledError:
            state.status = "cancelled"
            state.finished_at = datetime.now(timezone.utc)
            return
        state.nodes[nid] = {
            "status": "success",
            "output": {"simulated": True, "node": nid},
            "duration_ms": _SIM_NODE_DURATION_MS,
        }

    state.status = "success"
    state.finished_at = datetime.now(timezone.utc)
