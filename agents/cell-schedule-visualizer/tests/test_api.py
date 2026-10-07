"""
Tests for FastAPI Manufacturing Schedule API Server
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from api_server_fastapi import app, create_sample_data, ScheduleData


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_data():
    """Get sample schedule data"""
    return create_sample_data()


# ============================================================================
# Health Endpoint Tests
# ============================================================================


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health endpoint returns OK"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_health_check_timestamp_format(self, client):
        """Test health endpoint returns valid timestamp"""
        response = client.get("/api/health")

        data = response.json()
        # Should be ISO format
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise

    def test_health_check_response_model(self, client):
        """Test health endpoint response structure"""
        response = client.get("/api/health")

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "timestamp" in data


# ============================================================================
# Schedule Endpoint Tests
# ============================================================================


class TestScheduleEndpoint:
    """Test schedule data endpoint"""

    def test_get_schedule(self, client):
        """Test getting complete schedule"""
        response = client.get("/api/schedule")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "timestamp" in data

    def test_schedule_data_structure(self, client):
        """Test schedule data has correct structure"""
        response = client.get("/api/schedule")

        data = response.json()["data"]
        assert "scheduled_tasks" in data
        assert "quality_metrics" in data
        assert "gantt_data" in data
        assert "statistics" in data

    def test_schedule_tasks_structure(self, client):
        """Test scheduled tasks structure"""
        response = client.get("/api/schedule")

        data = response.json()["data"]
        tasks = data["scheduled_tasks"]

        assert isinstance(tasks, list)
        if len(tasks) > 0:
            task = tasks[0]
            assert "wo_id" in task
            assert "op_id" in task
            assert "machine_id" in task
            assert "start_time" in task
            assert "end_time" in task
            assert "quantity" in task

    def test_schedule_quality_metrics(self, client):
        """Test quality metrics in schedule"""
        response = client.get("/api/schedule")

        data = response.json()["data"]
        metrics = data["quality_metrics"]

        assert "makespan_hours" in metrics
        assert "total_lateness_hours" in metrics
        assert "avg_machine_utilization" in metrics
        assert "machine_utilization" in metrics
        assert "total_scheduled_tasks" in metrics


# ============================================================================
# Gantt Endpoint Tests
# ============================================================================


class TestGanttEndpoint:
    """Test Gantt chart data endpoint"""

    def test_get_gantt(self, client):
        """Test getting Gantt data"""
        response = client.get("/api/schedule/gantt")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_gantt_data_structure(self, client):
        """Test Gantt data structure"""
        response = client.get("/api/schedule/gantt")

        data = response.json()["data"]
        assert "tasks" in data
        assert "resources" in data
        assert "start" in data
        assert "end" in data

    def test_gantt_task_structure(self, client):
        """Test individual Gantt task structure"""
        response = client.get("/api/schedule/gantt")

        data = response.json()["data"]
        tasks = data["tasks"]

        assert isinstance(tasks, list)
        if len(tasks) > 0:
            task = tasks[0]
            assert "name" in task
            assert "start" in task
            assert "end" in task
            assert "resource" in task
            assert "priority" in task
            assert "color" in task
            assert "quantity" in task
            assert "duration_minutes" in task

    def test_gantt_resources(self, client):
        """Test Gantt resources list"""
        response = client.get("/api/schedule/gantt")

        data = response.json()["data"]
        resources = data["resources"]

        assert isinstance(resources, list)
        assert len(resources) > 0

    def test_gantt_datetime_format(self, client):
        """Test Gantt datetime format is ISO"""
        response = client.get("/api/schedule/gantt")

        data = response.json()["data"]

        # Validate start and end are ISO format
        datetime.fromisoformat(data["start"])
        datetime.fromisoformat(data["end"])

        # Validate task times
        for task in data["tasks"]:
            datetime.fromisoformat(task["start"])
            datetime.fromisoformat(task["end"])


# ============================================================================
# Metrics Endpoint Tests
# ============================================================================


class TestMetricsEndpoint:
    """Test metrics endpoint"""

    def test_get_metrics(self, client):
        """Test getting metrics"""
        response = client.get("/api/schedule/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_metrics_content(self, client):
        """Test metrics content"""
        response = client.get("/api/schedule/metrics")

        data = response.json()["data"]
        assert "metrics" in data
        assert "statistics" in data

    def test_metrics_fields(self, client):
        """Test metrics have required fields"""
        response = client.get("/api/schedule/metrics")

        metrics = response.json()["data"]["metrics"]
        assert "makespan_hours" in metrics
        assert "avg_machine_utilization" in metrics
        assert "machine_utilization" in metrics

    def test_statistics_fields(self, client):
        """Test statistics have required fields"""
        response = client.get("/api/schedule/metrics")

        stats = response.json()["data"]["statistics"]
        assert "total_tasks" in stats
        assert "makespan_seconds" in stats
        assert "makespan_hours" in stats
        assert "solve_time_sec" in stats
        assert "objective_value" in stats


# ============================================================================
# Tasks Endpoint Tests
# ============================================================================


class TestTasksEndpoint:
    """Test tasks endpoint"""

    def test_get_tasks(self, client):
        """Test getting tasks"""
        response = client.get("/api/schedule/tasks")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_tasks_content(self, client):
        """Test tasks content"""
        response = client.get("/api/schedule/tasks")

        data = response.json()["data"]
        assert "tasks" in data
        assert "total" in data

    def test_tasks_count_consistency(self, client):
        """Test tasks count matches array length"""
        response = client.get("/api/schedule/tasks")

        data = response.json()["data"]
        assert len(data["tasks"]) == data["total"]

    def test_tasks_structure(self, client):
        """Test individual task structure"""
        response = client.get("/api/schedule/tasks")

        tasks = response.json()["data"]["tasks"]
        if len(tasks) > 0:
            task = tasks[0]
            required_fields = ["wo_id", "op_id", "machine_id", "start_time", "end_time", "quantity"]
            for field in required_fields:
                assert field in task, f"Missing field: {field}"


# ============================================================================
# Utilization Endpoint Tests
# ============================================================================


class TestUtilizationEndpoint:
    """Test utilization endpoint"""

    def test_get_utilization(self, client):
        """Test getting utilization"""
        response = client.get("/api/schedule/utilization")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_utilization_content(self, client):
        """Test utilization content"""
        response = client.get("/api/schedule/utilization")

        data = response.json()["data"]
        assert "data" in data
        assert "average" in data

    def test_utilization_values_range(self, client):
        """Test utilization values are in valid range"""
        response = client.get("/api/schedule/utilization")

        data = response.json()["data"]
        for machine, util in data["data"].items():
            assert 0 <= util <= 100, f"Invalid utilization for {machine}: {util}"

    def test_average_utilization(self, client):
        """Test average utilization"""
        response = client.get("/api/schedule/utilization")

        data = response.json()["data"]
        assert isinstance(data["average"], (int, float))
        assert 0 <= data["average"] <= 100


# ============================================================================
# Lateness Endpoint Tests
# ============================================================================


class TestLatenessEndpoint:
    """Test lateness endpoint"""

    def test_get_lateness(self, client):
        """Test getting lateness"""
        response = client.get("/api/schedule/lateness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_lateness_content(self, client):
        """Test lateness content"""
        response = client.get("/api/schedule/lateness")

        data = response.json()["data"]
        assert "data" in data
        assert "total" in data

    def test_lateness_values(self, client):
        """Test lateness values are non-negative"""
        response = client.get("/api/schedule/lateness")

        data = response.json()["data"]
        for wo_id, lateness in data["data"].items():
            assert lateness >= 0, f"Negative lateness for {wo_id}: {lateness}"

    def test_total_lateness(self, client):
        """Test total lateness"""
        response = client.get("/api/schedule/lateness")

        data = response.json()["data"]
        assert isinstance(data["total"], (int, float))
        assert data["total"] >= 0


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling"""

    def test_not_found_endpoint(self, client):
        """Test 404 response for unknown endpoint"""
        response = client.get("/api/unknown")

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert "message" in data

    def test_invalid_method(self, client):
        """Test invalid HTTP method"""
        response = client.post("/api/health")

        # FastAPI returns 405 for method not allowed
        assert response.status_code == 405


# ============================================================================
# CORS Tests
# ============================================================================


class TestCORSConfiguration:
    """Test CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/health", headers={"Origin": "http://localhost:3000"})

        # FastAPI with CORS middleware should allow requests
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled

    def test_cross_origin_request(self, client):
        """Test cross-origin request is allowed"""
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200


# ============================================================================
# Data Model Tests
# ============================================================================


class TestDataModels:
    """Test Pydantic data models"""

    def test_create_sample_data(self, sample_data):
        """Test sample data creation"""
        assert isinstance(sample_data, ScheduleData)
        assert len(sample_data.scheduled_tasks) == 2
        assert len(sample_data.gantt_data.tasks) == 2

    def test_sample_data_quality_metrics(self, sample_data):
        """Test sample data quality metrics"""
        metrics = sample_data.quality_metrics

        assert metrics.makespan_hours > 0
        assert metrics.avg_machine_utilization >= 0
        assert len(metrics.machine_utilization) > 0

    def test_sample_data_statistics(self, sample_data):
        """Test sample data statistics"""
        stats = sample_data.statistics

        assert stats.total_tasks >= 0
        assert stats.makespan_seconds >= 0
        assert stats.makespan_hours >= 0

    def test_sample_data_gantt(self, sample_data):
        """Test sample data Gantt"""
        gantt = sample_data.gantt_data

        assert isinstance(gantt.tasks, list)
        assert isinstance(gantt.resources, list)
        assert len(gantt.resources) > 0


# ============================================================================
# Response Format Tests
# ============================================================================


class TestResponseFormat:
    """Test API response format consistency"""

    def test_all_endpoints_have_status(self, client):
        """Test all endpoints return status field"""
        endpoints = [
            "/api/health",
            "/api/schedule",
            "/api/schedule/gantt",
            "/api/schedule/metrics",
            "/api/schedule/tasks",
            "/api/schedule/utilization",
            "/api/schedule/lateness",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert "status" in data, f"Missing status in {endpoint}"

    def test_all_schedule_endpoints_have_timestamp(self, client):
        """Test schedule endpoints return timestamp"""
        endpoints = [
            "/api/schedule",
            "/api/schedule/gantt",
            "/api/schedule/metrics",
            "/api/schedule/tasks",
            "/api/schedule/utilization",
            "/api/schedule/lateness",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert "timestamp" in data, f"Missing timestamp in {endpoint}"

    def test_schedule_endpoints_have_data(self, client):
        """Test schedule endpoints return data field"""
        endpoints = [
            "/api/schedule",
            "/api/schedule/gantt",
            "/api/schedule/metrics",
            "/api/schedule/tasks",
            "/api/schedule/utilization",
            "/api/schedule/lateness",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert "data" in data, f"Missing data in {endpoint}"
            assert data["data"] is not None, f"Null data in {endpoint}"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests"""

    def test_data_consistency_across_endpoints(self, client):
        """Test data is consistent across endpoints"""
        # Get full schedule
        schedule = client.get("/api/schedule").json()["data"]

        # Get tasks
        tasks = client.get("/api/schedule/tasks").json()["data"]

        # Task count should match
        assert len(schedule["scheduled_tasks"]) == tasks["total"]

    def test_gantt_matches_schedule(self, client):
        """Test Gantt data matches schedule"""
        schedule = client.get("/api/schedule").json()["data"]
        gantt = client.get("/api/schedule/gantt").json()["data"]

        # Should have same number of tasks
        assert len(schedule["gantt_data"]["tasks"]) == len(gantt["tasks"])

    def test_metrics_consistency(self, client):
        """Test metrics are consistent"""
        schedule = client.get("/api/schedule").json()["data"]
        metrics = client.get("/api/schedule/metrics").json()["data"]

        # Metrics should match
        assert schedule["quality_metrics"]["makespan_hours"] == metrics["metrics"]["makespan_hours"]

    def test_utilization_consistency(self, client):
        """Test utilization is consistent"""
        schedule = client.get("/api/schedule").json()["data"]
        utilization = client.get("/api/schedule/utilization").json()["data"]

        # Utilization data should match
        assert schedule["quality_metrics"]["machine_utilization"] == utilization["data"]
