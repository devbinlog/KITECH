"""
FastAPI Server for Manufacturing Schedule Visualization

Features:
- Automatic Swagger documentation: http://localhost:8080/docs
- Automatic ReDoc documentation: http://localhost:8080/redoc
- Type-safe endpoints with Pydantic validation
- CORS support
- Sample data with 2 tasks and 2 machines
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ============================================================================
# Data Models (Pydantic)
# ============================================================================


class ScheduledTask(BaseModel):
    """Scheduled task model"""

    wo_id: str = Field(..., description="Work Order ID")
    op_id: str = Field(..., description="Operation ID")
    machine_id: str = Field(..., description="Machine ID")
    start_time: int = Field(..., description="Start time (Unix timestamp)")
    end_time: int = Field(..., description="End time (Unix timestamp)")
    quantity: int = Field(..., description="Quantity")


class QualityMetrics(BaseModel):
    """Quality metrics model"""

    makespan_hours: float
    total_lateness_hours: float
    avg_machine_utilization: float
    machine_utilization: Dict[str, float]
    total_scheduled_tasks: int
    total_work_orders: int
    total_machines: int
    per_wo_lateness: Dict[str, float]


class GanttTask(BaseModel):
    """Gantt chart task"""

    name: str
    start: str
    end: str
    resource: str
    priority: int
    color: str
    quantity: int
    duration_minutes: int


class GanttData(BaseModel):
    """Gantt chart data"""

    tasks: List[GanttTask]
    resources: List[str]
    start: str
    end: str


class Statistics(BaseModel):
    """Statistics model"""

    total_tasks: int
    makespan_seconds: int
    makespan_hours: float
    solve_time_sec: float
    objective_value: float


class ScheduleData(BaseModel):
    """Complete schedule data"""

    scheduled_tasks: List[ScheduledTask]
    quality_metrics: QualityMetrics
    gantt_data: GanttData
    statistics: Statistics


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: str


class ApiResponse(BaseModel):
    """Generic API response"""

    status: str
    data: Any = None
    timestamp: str


# ============================================================================
# Sample Data
# ============================================================================


def create_sample_data() -> ScheduleData:
    """Create sample schedule data"""
    now = datetime.now(timezone.utc)

    return ScheduleData(
        scheduled_tasks=[
            ScheduledTask(
                wo_id="WO-001",
                op_id="OP-001",
                machine_id="MCH-001",
                start_time=int(now.timestamp()),
                end_time=int((now + timedelta(hours=2)).timestamp()),
                quantity=100,
            ),
            ScheduledTask(
                wo_id="WO-002",
                op_id="OP-002",
                machine_id="MCH-002",
                start_time=int((now + timedelta(hours=1)).timestamp()),
                end_time=int((now + timedelta(hours=3)).timestamp()),
                quantity=50,
            ),
        ],
        quality_metrics=QualityMetrics(
            makespan_hours=3.5,
            total_lateness_hours=0.2,
            avg_machine_utilization=72.5,
            machine_utilization={"MCH-001": 85.0, "MCH-002": 72.0},
            total_scheduled_tasks=2,
            total_work_orders=2,
            total_machines=2,
            per_wo_lateness={"WO-001": 0.1, "WO-002": 0.1},
        ),
        gantt_data=GanttData(
            tasks=[
                GanttTask(
                    name="WO-001",
                    start=now.isoformat(),
                    end=(now + timedelta(hours=2)).isoformat(),
                    resource="MCH-001",
                    priority=1,
                    color="#FF6B6B",
                    quantity=100,
                    duration_minutes=120,
                ),
                GanttTask(
                    name="WO-002",
                    start=(now + timedelta(hours=1)).isoformat(),
                    end=(now + timedelta(hours=3)).isoformat(),
                    resource="MCH-002",
                    priority=2,
                    color="#FFA500",
                    quantity=50,
                    duration_minutes=120,
                ),
            ],
            resources=["MCH-001", "MCH-002"],
            start=now.isoformat(),
            end=(now + timedelta(hours=4)).isoformat(),
        ),
        statistics=Statistics(
            total_tasks=2,
            makespan_seconds=10800,
            makespan_hours=3.0,
            solve_time_sec=0.1,
            objective_value=100.5,
        ),
    )


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Manufacturing Schedule API",
    description="API for manufacturing schedule visualization",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data
schedule_data = create_sample_data()


# ============================================================================
# Routes
# ============================================================================


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Health check endpoint"""
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc).isoformat())


@app.get("/api/schedule", response_model=ApiResponse, tags=["Schedule"])
async def get_schedule():
    """Get complete schedule data"""
    return ApiResponse(
        status="success",
        data=schedule_data.model_dump(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/schedule/gantt", response_model=ApiResponse, tags=["Schedule"])
async def get_gantt():
    """Get Gantt chart data"""
    return ApiResponse(
        status="success",
        data=schedule_data.gantt_data.model_dump(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/schedule/metrics", response_model=ApiResponse, tags=["Schedule"])
async def get_metrics():
    """Get quality metrics"""
    return ApiResponse(
        status="success",
        data={
            "metrics": schedule_data.quality_metrics.model_dump(),
            "statistics": schedule_data.statistics.model_dump(),
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/schedule/tasks", response_model=ApiResponse, tags=["Schedule"])
async def get_tasks():
    """Get scheduled tasks"""
    return ApiResponse(
        status="success",
        data={
            "tasks": [task.model_dump() for task in schedule_data.scheduled_tasks],
            "total": len(schedule_data.scheduled_tasks),
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/schedule/utilization", response_model=ApiResponse, tags=["Schedule"])
async def get_utilization():
    """Get machine utilization"""
    return ApiResponse(
        status="success",
        data={
            "data": schedule_data.quality_metrics.machine_utilization,
            "average": schedule_data.quality_metrics.avg_machine_utilization,
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/schedule/lateness", response_model=ApiResponse, tags=["Schedule"])
async def get_lateness():
    """Get work order lateness"""
    return ApiResponse(
        status="success",
        data={
            "data": schedule_data.quality_metrics.per_wo_lateness,
            "total": schedule_data.quality_metrics.total_lateness_hours,
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("")
    print("=" * 70)
    print("FastAPI Manufacturing Schedule Server")
    print("=" * 70)
    print("")
    print("Swagger Documentation: http://localhost:8080/docs")
    print("ReDoc Documentation: http://localhost:8080/redoc")
    print("")
    print("API Endpoints:")
    print("  GET /api/health")
    print("  GET /api/schedule")
    print("  GET /api/schedule/gantt")
    print("  GET /api/schedule/metrics")
    print("  GET /api/schedule/tasks")
    print("  GET /api/schedule/utilization")
    print("  GET /api/schedule/lateness")
    print("")
    print("=" * 70)
    print("")

    uvicorn.run(app, host="0.0.0.0", port=8080)
