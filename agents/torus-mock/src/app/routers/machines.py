"""Machines router: list, detail, channel info.

Convenience endpoints for browsing machine data.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..schemas import MachineListResponse
from ..services.machine_store import get_store

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


@router.get("", response_model=MachineListResponse)
async def list_machines():
    """List all available machines (summary)."""
    store = get_store()
    return MachineListResponse(machines=store.list_machines())


@router.get("/{machine_id}")
async def get_machine(machine_id: int) -> Dict[str, Any]:
    """Get full machine data snapshot."""
    store = get_store()
    machine = store.get_machine(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return machine.model_dump()


@router.get("/{machine_id}/channel/{channel_id}")
async def get_channel(machine_id: int, channel_id: int) -> Dict[str, Any]:
    """Get specific channel data (1-based index)."""
    store = get_store()
    machine = store.get_machine(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    idx = channel_id - 1  # 1-based → 0-based
    if idx < 0 or idx >= len(machine.channel):
        raise HTTPException(
            status_code=404,
            detail=f"Channel {channel_id} not found (machine has {len(machine.channel)} channels)",
        )
    return machine.channel[idx].model_dump()
