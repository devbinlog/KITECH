"""
Mock Middleware Server

Simulates the middleware server for development and testing.
Provides endpoints for:
- GET /assets - AAS asset discovery
- GET /status - Equipment status polling
- POST /run - Work execution command
- GET /health - Health check
"""

import random
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Mock Middleware Server",
    description="Simulates middleware for Cell-MES development",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Mock Data
# ============================================================================

MOCK_ASSETS: List[Dict[str, Any]] = [
    {
        "id": "urn:aas:cnc:laser-001",
        "name": "Laser Cutter #1",
        "type": "CNC",
        "connection": {"ip": "192.168.1.101", "port": 502, "protocol": "modbus"},
        "spec": {
            "manufacturer": "Trumpf",
            "model": "TruLaser 3030",
            "max_power_kw": 6,
            "work_area_mm": {"x": 3000, "y": 1500},
        },
    },
    {
        "id": "urn:aas:cnc:bend-001",
        "name": "Press Brake #1",
        "type": "CNC",
        "connection": {"ip": "192.168.1.102", "port": 502, "protocol": "modbus"},
        "spec": {
            "manufacturer": "Amada",
            "model": "HFE 3i 8025",
            "max_force_ton": 80,
            "bed_length_mm": 2500,
        },
    },
    {
        "id": "urn:aas:robot:arm-001",
        "name": "Robot Arm #1",
        "type": "ROBOT",
        "connection": {"ip": "192.168.1.201", "port": 30002, "protocol": "tcp"},
        "spec": {
            "manufacturer": "Universal Robots",
            "model": "UR10e",
            "payload_kg": 10,
            "reach_mm": 1300,
            "axes": 6,
        },
    },
    {
        "id": "urn:aas:amr:agv-001",
        "name": "AMR Unit #1",
        "type": "AMR",
        "connection": {"ip": "192.168.1.211", "port": 8080, "protocol": "rest"},
        "spec": {
            "manufacturer": "MiR",
            "model": "MiR250",
            "max_payload_kg": 250,
            "battery_capacity_kwh": 2.4,
        },
    },
    {
        "id": "urn:aas:plc:main-001",
        "name": "Main PLC",
        "type": "PLC",
        "connection": {"ip": "192.168.1.50", "port": 102, "protocol": "s7"},
        "spec": {
            "manufacturer": "Siemens",
            "model": "S7-1500",
            "cpu": "1515-2 PN",
        },
    },
]


def generate_cnc_status() -> Dict[str, Any]:
    """Generate random CNC status data."""
    is_running = random.random() > 0.3
    has_error = random.random() < 0.05

    return {
        "spindle_rpm": random.randint(8000, 18000) if is_running else 0,
        "load_percent": random.uniform(20, 80) if is_running else 0,
        "temperature": random.uniform(40, 90),
        "alarm_code": "E-001" if has_error else "0",
        "program_name": f"O{random.randint(1000, 9999)}" if is_running else "",
        "feed_rate": random.randint(1000, 8000) if is_running else 0,
        "axis_position": {
            "x": random.uniform(0, 3000),
            "y": random.uniform(0, 1500),
            "z": random.uniform(-100, 100),
        },
    }


def generate_robot_status() -> Dict[str, Any]:
    """Generate random robot status data."""
    is_moving = random.random() > 0.4
    has_error = random.random() < 0.03

    return {
        "joint_angles": [random.uniform(-180, 180) for _ in range(6)],
        "battery_level": random.randint(20, 100),
        "current_position": {
            "x": random.uniform(-500, 500),
            "y": random.uniform(-500, 500),
            "z": random.uniform(100, 800),
        },
        "is_moving": is_moving,
        "error_code": "ERR-JOINT" if has_error else None,
        "task_id": f"TASK-{random.randint(1, 100):03d}" if is_moving else "",
        "speed_percent": random.randint(50, 100) if is_moving else 0,
    }


def generate_plc_status() -> Dict[str, Any]:
    """Generate random PLC status data."""
    is_running = random.random() > 0.2
    has_error = random.random() < 0.02

    return {
        "registers": {f"D{i}": random.randint(0, 65535) for i in range(10)},
        "coils": {f"M{i}": random.random() > 0.5 for i in range(8)},
        "error_flag": has_error,
        "cycle_count": random.randint(10000, 99999),
        "running": is_running,
    }


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "server": "mock-middleware",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/assets")
async def get_assets():
    """
    Get all AAS assets (Asset Discovery).

    Returns list of equipment with their AAS identifiers and specifications.
    """
    return MOCK_ASSETS


@app.get("/status")
async def get_equipment_status(
    ip: str = Query(..., description="Equipment IP address"),
    port: int = Query(..., description="Equipment port"),
    protocol: str = Query("modbus", description="Communication protocol"),
):
    """
    Get equipment status.

    Simulates polling an equipment for its current status.
    Returns different data based on the equipment type (inferred from connection).
    """
    # Find matching asset to determine type
    asset_type = "CNC"
    for asset in MOCK_ASSETS:
        conn = asset.get("connection", {})
        if conn.get("ip") == ip and conn.get("port") == port:
            asset_type = asset.get("type", "CNC")
            break

    # Generate appropriate status data
    if asset_type == "ROBOT" or asset_type == "AMR":
        return generate_robot_status()
    elif asset_type == "PLC":
        return generate_plc_status()
    else:
        return generate_cnc_status()


@app.post("/run")
async def run_work(payload: Dict[str, Any]):
    """
    Execute work command.

    Receives work info payload and simulates starting execution.
    Uses wo_id and op_id for identification.
    """
    wo_id = payload.get("wo_id", "unknown")
    op_id = payload.get("op_id", "unknown")
    return {
        "status": "accepted",
        "wo_id": wo_id,
        "op_id": op_id,
        "message": f"Work execution started for {wo_id}/{op_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
