"""TORUS Platform Mock Server — FastAPI Application.

Simulates TORUS Machine Data Model and Data Access APIs via REST.
Port: 8003 (default)
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import data, files, machines, plc, simulation, subscribe
from .services.data_simulator import get_simulator
from .services.machine_store import get_store
from .services.subscription_manager import get_subscription_manager

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load data, start services."""
    # Load default machine data
    store = get_store()
    default_json = DATA_DIR / "default_machines.json"
    if default_json.exists():
        store.load_from_json(default_json)

    # Start subscription push loop
    manager = get_subscription_manager()
    await manager.start_push_loop()

    yield

    # Shutdown
    simulator = get_simulator()
    await simulator.stop()
    await manager.stop_push_loop()


app = FastAPI(
    title="TORUS Platform Mock Server",
    description=(
        "Mock server simulating TORUS Platform Machine Data Model and APIs. "
        "Provides REST endpoints for getData, updateData, PLC signals, "
        "file management, and real-time data simulation for CNC development/testing."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(data.router)
app.include_router(plc.router)
app.include_router(machines.router)
app.include_router(subscribe.router)
app.include_router(files.router)
app.include_router(simulation.router)


@app.get("/health")
async def health():
    """Health check."""
    store = get_store()
    sim = get_simulator()
    return {
        "status": "ok",
        "service": "torus-mock",
        "machines": len(store.machines),
        "simulation_running": sim.running,
    }
