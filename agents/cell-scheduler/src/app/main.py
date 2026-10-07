"""
Cell-Scheduler FastAPI Application

Manufacturing cell scheduling service with multi-solver support.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import scheduler
from .schemas import HealthResponse
from .config import settings
from .services.event_publisher import init_event_publisher, shutdown_event_publisher

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Cell-Scheduler Service...")
    logger.info("Available solvers: OR-Tools, Genetic Algorithm, Simulated Annealing, Tabu Search, ALNS")
    await init_event_publisher()
    yield
    logger.info("Shutting down Cell-Scheduler Service...")
    await shutdown_event_publisher()


# Create FastAPI application
app = FastAPI(
    title="Cell-Scheduler API",
    description="""
Manufacturing Cell Scheduling Service with Multi-Solver Support

## Features
- **Multiple Solvers**: OR-Tools CP-SAT, Genetic Algorithm, Simulated Annealing, Tabu Search
- **Constraint Satisfaction**: Precedence, machine compatibility, setup time, release/due dates
- **Multi-Objective Optimization**: Minimize makespan, lateness, maximize utilization
- **Real-time Gantt**: Generate Gantt chart data for visualization

## Solver Selection Guide
| Solver | Best For |
|--------|----------|
| OR_TOOLS | Small-medium problems (<30 jobs), optimal solutions |
| GA | Large problems, balanced quality and speed |
| SA | Fast approximate solutions |
| TABU | Complex constraints, avoiding local optima |
    """,
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS middleware - origins from environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scheduler.router)

# Serve solver output files (gantt PNG, result JSON) as static files
_output_dir = Path(__file__).parents[4] / "samples" / "cell-scheduler" / "output"
_output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(_output_dir)), name="output")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint

    Returns service status and version information.
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        service=settings.APP_NAME.lower(),
    )


@app.get("/capabilities", tags=["meta"])
async def get_capabilities():
    """Tools for agent-orchestrator's dynamic tool_loader."""
    return {
        "service": "cell-scheduler",
        "version": "0.1.0",
        "description": "OR-Tools based production scheduler. Optimizes work order assignment to equipment over time horizon.",
        "tools": [
            {
                "name": "solve_schedule",
                "description": "Solve a production scheduling problem given work orders + equipment availability + horizon. Returns optimized assignment + gantt data. Use when user asks 'when can we produce X' or 'is Y feasible by Z'.",
                "endpoint": {"method": "POST", "path": "/api/v1/schedule/solve"},
                "idempotent": True,
            },
            {
                "name": "list_solvers",
                "description": "Get a list of available scheduling solvers (OR-Tools, Genetic Algorithm, Simulated Annealing, Tabu Search, ALNS) with their characteristics and best-use recommendations.",
                "endpoint": {"method": "GET", "path": "/api/v1/schedule/solvers"},
                "idempotent": True,
            },
            {
                "name": "get_solver_info",
                "description": "Get detailed information about a specific solver by type (OR_TOOLS, GA, SA, TABU, ALNS). Returns solver characteristics and default parameters.",
                "endpoint": {"method": "GET", "path": "/api/v1/schedule/solver/{solver_type}"},
                "idempotent": True,
            },
        ],
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Cell-Scheduler",
        "version": "0.2.0",
        "description": "Manufacturing Cell Scheduling Service",
        "docs": "/api/docs",
        "health": "/health",
        "endpoints": {
            "solve": "POST /api/v1/schedule/solve",
            "solvers": "GET /api/v1/schedule/solvers",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
