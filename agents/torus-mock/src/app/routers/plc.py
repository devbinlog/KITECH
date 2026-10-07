"""PLC router: getPlcSignal / setPlcSignal.

Maps TORUS getPlcSignal → GET /api/v1/plc
Maps TORUS setPlcSignal → PUT /api/v1/plc
"""

from fastapi import APIRouter, Query

from ..schemas import PlcResponse, PlcWriteRequest
from ..services.machine_store import get_store

router = APIRouter(prefix="/api/v1/plc", tags=["plc"])


@router.get("", response_model=PlcResponse)
async def get_plc_signal(
    machine: int = Query(1, description="Machine ID"),
    type: int = Query(..., description="PLC memory type (1-10)"),
    startAddress: int = Query(0, description="Start address"),
    count: int = Query(1, description="Number of items to read"),
):
    """Read PLC memory block (getPlcSignal)."""
    store = get_store()
    return store.get_plc(machine, type, startAddress, count)


@router.put("", response_model=PlcResponse)
async def set_plc_signal(request: PlcWriteRequest):
    """Write PLC memory block (setPlcSignal).

    Only writable types (2,4,6,8,10) are allowed.
    """
    store = get_store()
    return store.set_plc(request.machine, request.type, request.startAddress, request.data)
