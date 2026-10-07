"""service.py — Thin FastAPI wrapper for TORUS Platform Mock Server.

Containerises the existing torus-mock library as a standard library-agent
service following the shared service_base conventions (port 8015).

Endpoint layout (all existing routers preserved):
  GET/PUT  /api/v1/data          — getData / updateData (TORUS address format)
  POST     /api/v1/data/batch    — batch getData
  GET/PUT  /api/v1/plc           — getPlcSignal / setPlcSignal
  GET      /api/v1/machines      — list machines
  GET      /api/v1/machines/{id} — machine detail
  GET      /api/v1/machines/{id}/channel/{ch} — channel detail
  POST/DELETE/GET /api/v1/subscribe — subscribeData / unsubscribeData
  WS       /ws/subscribe         — WebSocket hot-link push
  GET      /api/v1/files         — getFileList
  POST     /api/v1/files/upload  — UploadFile (mock)
  GET      /api/v1/files/download — DownloadFile (mock)
  GET/POST /api/v1/simulation/*  — simulation control

Auth:
  By default all domain endpoints require X-Internal-Key (require_internal).
  Set MOCK_SKIP_AUTH=1 to disable auth — intended for test / demo environments
  where cell-mes calls this mock without a service key.

Callers (cell-mes config):
  TORUS_GATEWAY_URL=http://torus-mock:8015
"""
from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI

# Ensure shared/ is importable when running via uvicorn from workspace root.
_workspace_root = Path(__file__).parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from shared.common.service_base import (
    create_app,
    make_capability,
    require_internal,
)

from .app.routers import data, files, machines, plc, simulation, subscribe
from .app.services.data_simulator import get_simulator
from .app.services.machine_store import get_store
from .app.services.subscription_manager import get_subscription_manager

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Auth dependency — bypassed when MOCK_SKIP_AUTH=1
# ---------------------------------------------------------------------------


def _auth_dependency() -> Any:
    """Return require_internal or None based on MOCK_SKIP_AUTH env var."""
    if os.getenv("MOCK_SKIP_AUTH", "0") == "1":
        return []  # no dependency
    return [Depends(require_internal)]


# ---------------------------------------------------------------------------
# Capabilities declaration (MCP-style)
# ---------------------------------------------------------------------------

CAPABILITIES = [
    make_capability(
        name="get_data",
        description=(
            "Read a single CNC machine data value using TORUS address format. "
            "Example: address='data://machine/channel/axis/machinePosition', "
            "filter='machine=1&channel=1&axis=1'."
        ),
        path="/api/v1/data",
        method="GET",
        idempotent=True,
    ),
    make_capability(
        name="update_data",
        description=(
            "Write a writable CNC machine data value using TORUS address format. "
            "Only R/W fields (axisLimitPlus, workCounter, etc.) can be modified."
        ),
        path="/api/v1/data",
        method="PUT",
        idempotent=True,
    ),
    make_capability(
        name="batch_get_data",
        description="Batch-read multiple TORUS data addresses in a single request.",
        path="/api/v1/data/batch",
        method="POST",
        idempotent=True,
    ),
    make_capability(
        name="list_machines",
        description="List all simulated CNC machines with summary info.",
        path="/api/v1/machines",
        method="GET",
        idempotent=True,
    ),
    make_capability(
        name="get_machine",
        description="Get full machine data snapshot for a given machine ID.",
        path="/api/v1/machines/{machine_id}",
        method="GET",
        idempotent=True,
    ),
    make_capability(
        name="get_plc_signal",
        description="Read PLC memory block (getPlcSignal). Types 1-10.",
        path="/api/v1/plc",
        method="GET",
        idempotent=True,
    ),
    make_capability(
        name="set_plc_signal",
        description="Write PLC memory block (setPlcSignal). Writable types 2,4,6,8,10 only.",
        path="/api/v1/plc",
        method="PUT",
        idempotent=False,
    ),
    make_capability(
        name="subscribe_data",
        description="Subscribe to periodic TORUS data pushes (subscribeData).",
        path="/api/v1/subscribe",
        method="POST",
        idempotent=False,
    ),
    make_capability(
        name="get_file_list",
        description="List NC program files on a simulated machine (getFileList).",
        path="/api/v1/files",
        method="GET",
        idempotent=True,
    ),
    make_capability(
        name="simulation_status",
        description="Get the current state of the data simulation engine.",
        path="/api/v1/simulation/status",
        method="GET",
        idempotent=True,
    ),
]

# ---------------------------------------------------------------------------
# Lifespan: load machine data + start services
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Load default machine data and start background services on startup."""
    store = get_store()
    default_json = DATA_DIR / "default_machines.json"
    if default_json.exists():
        store.load_from_json(default_json)
        logger.info("torus-mock: loaded %d machines from %s", len(store.machines), default_json)

    manager = get_subscription_manager()
    await manager.start_push_loop()
    logger.info("torus-mock: subscription push loop started")

    yield

    sim = get_simulator()
    await sim.stop()
    await manager.stop_push_loop()
    logger.info("torus-mock: shutdown complete")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = create_app(
    name="torus-mock",
    version="0.1.0",
    description=(
        "Mock server simulating TORUS Platform Machine Data Model and APIs. "
        "Drop-in replacement for TORUS_GATEWAY_URL (http://10.10.10.113:5001) "
        "in test / demo environments. Port 8015."
    ),
    capabilities=CAPABILITIES,
    cors_origins=["*"],
)

# Replace lifespan after creation (create_app does not expose lifespan param)
app.router.lifespan_context = _lifespan  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Mount existing routers
# ---------------------------------------------------------------------------

_deps = _auth_dependency()

app.include_router(data.router, dependencies=_deps)
app.include_router(plc.router, dependencies=_deps)
app.include_router(machines.router, dependencies=_deps)
app.include_router(subscribe.router, dependencies=_deps)
app.include_router(files.router, dependencies=_deps)
app.include_router(simulation.router, dependencies=_deps)
