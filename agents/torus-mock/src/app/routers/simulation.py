"""Simulation router: control the data simulator.

POST /api/v1/simulation/start — Start simulation
POST /api/v1/simulation/stop — Stop simulation
GET  /api/v1/simulation/status — Get status
POST /api/v1/simulation/trigger-alarm — Manual alarm
POST /api/v1/simulation/tool-change — Manual tool change
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..schemas import Alarm, SimulationStatus, TriggerAlarmRequest, ToolChangeRequest
from ..services.data_simulator import get_simulator
from ..services.machine_store import get_store

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


@router.get("/status", response_model=SimulationStatus)
async def get_status():
    """Get simulation engine status."""
    sim = get_simulator()
    status = sim.get_status()
    return SimulationStatus(**status)


@router.post("/start")
async def start_simulation(interval_ms: int = 500):
    """Start the simulation engine."""
    sim = get_simulator()
    sim.interval_ms = interval_ms
    await sim.start()
    return {"success": True, "message": "Simulation started", "interval_ms": interval_ms}


@router.post("/stop")
async def stop_simulation():
    """Stop the simulation engine."""
    sim = get_simulator()
    await sim.stop()
    return {"success": True, "message": "Simulation stopped", "tick_count": sim.tick_count}


@router.post("/trigger-alarm")
async def trigger_alarm(request: TriggerAlarmRequest):
    """Manually trigger an alarm on a machine."""
    store = get_store()
    machine = store.get_machine(request.machine)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {request.machine} not found")

    ch_idx = request.channel - 1
    if ch_idx < 0 or ch_idx >= len(machine.channel):
        raise HTTPException(status_code=404, detail=f"Channel {request.channel} not found")

    channel = machine.channel[ch_idx]
    alarm = Alarm(
        alarmNumber=request.alarmNumber,
        alarmText=request.alarmText,
        alarmCategory=request.alarmCategory,
        raisedTimeStamp=datetime.now(timezone.utc).isoformat(),
    )
    channel.alarm.append(alarm)
    channel.numberOfAlarms = len(channel.alarm)
    channel.alarmStatus = 1

    return {"success": True, "alarm": alarm.model_dump()}


@router.post("/tool-change")
async def tool_change(request: ToolChangeRequest):
    """Manually change the active tool on a machine."""
    store = get_store()
    machine = store.get_machine(request.machine)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {request.machine} not found")

    ch_idx = request.channel - 1
    if ch_idx < 0 or ch_idx >= len(machine.channel):
        raise HTTPException(status_code=404, detail=f"Channel {request.channel} not found")

    channel = machine.channel[ch_idx]

    # Find tool in magazine
    tool_found = None
    for mag in machine.toolArea.magazine:
        for tool in mag.tools:
            if tool.toolNumber == request.toolNumber:
                tool_found = tool
                break

    if not tool_found:
        raise HTTPException(
            status_code=404,
            detail=f"Tool T{request.toolNumber:02d} not found in magazine",
        )

    # Update active tool
    channel.activeTool.toolNumber = tool_found.toolNumber
    channel.activeTool.toolName = tool_found.toolName
    channel.activeTool.locationNumber = tool_found.locationNumber
    channel.activeTool.numberOfEdges = tool_found.numberOfEdges
    channel.activeTool.magazineNumber = tool_found.magazineNumber
    channel.activeTool.toolEdge = tool_found.toolEdge.copy()

    return {
        "success": True,
        "tool": {
            "toolNumber": tool_found.toolNumber,
            "toolName": tool_found.toolName,
            "locationNumber": tool_found.locationNumber,
        },
    }
