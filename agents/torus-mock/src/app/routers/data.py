"""Data router: getData / updateData / batch getData.

Maps TORUS getData → GET /api/v1/data
Maps TORUS updateData → PUT /api/v1/data
Maps TORUS batch getData → POST /api/v1/data/batch
"""

from fastapi import APIRouter, Query

from ..schemas import (
    BatchDataRequest,
    BatchDataResponse,
    DataResponse,
    DataUpdateRequest,
)
from ..services.machine_store import get_store

router = APIRouter(prefix="/api/v1/data", tags=["data"])


@router.get("", response_model=DataResponse)
async def get_data(
    address: str = Query(
        ..., description="TORUS data address, e.g. data://machine/channel/axis/machinePosition"
    ),
    filter: str = Query("", description="Filter string, e.g. machine=1&channel=1&axis=1"),
):
    """Get data using TORUS address format (getData)."""
    store = get_store()
    return store.get_value(address, filter)


@router.post("/batch", response_model=BatchDataResponse)
async def get_data_batch(request: BatchDataRequest):
    """Batch get data (multiple addresses at once)."""
    store = get_store()
    results = []
    for item in request.items:
        result = store.get_value(item.address, item.filter)
        results.append(result)
    return BatchDataResponse(items=results)


@router.put("", response_model=DataResponse)
async def update_data(request: DataUpdateRequest):
    """Update data using TORUS address format (updateData).

    Only writable fields (R/W) can be modified.
    """
    store = get_store()
    return store.set_value(request.address, request.filter, request.value)
