"""Pytest configuration and fixtures for cell-schedule-visualizer tests."""

import pytest
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_schedule_result():
    """Sample schedule result for testing."""
    return {
        "status": "success",
        "scheduled_tasks": [
            {
                "wo_id": "WO-001",
                "op_id": "OP10",
                "machine_id": "MCH-001",
                "start_time": 0,
                "end_time": 3600,
                "quantity": 50,
            },
            {
                "wo_id": "WO-002",
                "op_id": "OP10",
                "machine_id": "MCH-002",
                "start_time": 0,
                "end_time": 5400,
                "quantity": 75,
            },
        ],
        "statistics": {
            "total_tasks": 2,
            "makespan_seconds": 5400,
            "makespan_hours": 1.5,
            "solve_time_sec": 0.05,
            "objective_value": 5400.0,
        },
        "quality_metrics": {
            "status": "scheduled",
            "makespan_hours": 1.5,
            "total_lateness_hours": 0.0,
            "avg_machine_utilization": 5.0,
            "machine_utilization": {"MCH-001": 5.0, "MCH-002": 7.5},
            "bottleneck_machines": ["MCH-002"],
            "schedule_efficiency": 2.5,
            "per_wo_lateness": {"WO-001": 0.0, "WO-002": 0.0},
            "total_scheduled_tasks": 2,
            "total_work_orders": 2,
            "total_machines": 2,
        },
        "gantt_data": {
            "tasks": [
                {
                    "name": "WO-001 / OP10",
                    "start": "2025-01-17T08:00:00",
                    "end": "2025-01-17T09:00:00",
                    "resource": "MCH-001",
                    "priority": 1,
                    "color": "#4ECDC4",
                    "quantity": 50,
                    "duration_minutes": 60.0,
                },
                {
                    "name": "WO-002 / OP10",
                    "start": "2025-01-17T08:00:00",
                    "end": "2025-01-17T09:30:00",
                    "resource": "MCH-002",
                    "priority": 2,
                    "color": "#4ECDC4",
                    "quantity": 75,
                    "duration_minutes": 90.0,
                },
            ],
            "resources": ["MCH-001", "MCH-002"],
            "start": "2025-01-17T08:00:00",
            "end": "2025-01-22T20:00:00",
        },
    }


@pytest.fixture
def empty_schedule_result():
    """Empty schedule result for edge case testing."""
    return {
        "status": "success",
        "scheduled_tasks": [],
        "statistics": {
            "total_tasks": 0,
            "makespan_seconds": 0,
            "makespan_hours": 0.0,
            "solve_time_sec": 0.0,
            "objective_value": 0.0,
        },
        "quality_metrics": {
            "status": "empty",
            "makespan_hours": 0.0,
            "avg_machine_utilization": 0.0,
            "machine_utilization": {},
            "bottleneck_machines": [],
            "total_scheduled_tasks": 0,
            "total_work_orders": 0,
            "total_machines": 0,
        },
        "gantt_data": {"tasks": [], "resources": []},
    }
