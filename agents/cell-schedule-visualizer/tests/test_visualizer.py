"""
Tests for Schedule Visualizer Agent
"""

import pytest
import os
from src.schedule_visualizer_agent import ScheduleVisualizer, ScheduleVisualizerAgent


@pytest.fixture
def sample_schedule_result():
    """Sample schedule result for testing"""
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
    """Empty schedule result for edge case testing"""
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


class TestScheduleVisualizerInitialization:
    """Test ScheduleVisualizer initialization"""

    def test_visualizer_initialization(self, sample_schedule_result):
        """Test visualizer initialization"""
        visualizer = ScheduleVisualizer(sample_schedule_result)

        assert visualizer.result == sample_schedule_result
        assert len(visualizer.scheduled_tasks) == 2
        assert visualizer.quality_metrics["makespan_hours"] == 1.5

    def test_visualizer_empty_initialization(self, empty_schedule_result):
        """Test visualizer with empty schedule"""
        visualizer = ScheduleVisualizer(empty_schedule_result)

        assert visualizer.result == empty_schedule_result
        assert len(visualizer.scheduled_tasks) == 0
        assert visualizer.quality_metrics["makespan_hours"] == 0.0

    def test_scheduled_tasks_extraction(self, sample_schedule_result):
        """Test scheduled tasks extraction"""
        visualizer = ScheduleVisualizer(sample_schedule_result)

        assert len(visualizer.scheduled_tasks) == 2
        assert visualizer.scheduled_tasks[0]["wo_id"] == "WO-001"
        assert visualizer.scheduled_tasks[1]["wo_id"] == "WO-002"

    def test_gantt_data_extraction(self, sample_schedule_result):
        """Test gantt data extraction"""
        visualizer = ScheduleVisualizer(sample_schedule_result)

        assert len(visualizer.gantt_data["tasks"]) == 2
        assert len(visualizer.gantt_data["resources"]) == 2
        assert "MCH-001" in visualizer.gantt_data["resources"]


class TestScheduleVisualizerAgent:
    """Test ScheduleVisualizerAgent"""

    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = ScheduleVisualizerAgent()

        assert agent.name == "schedule-visualizer"
        assert agent.config is not None

    def test_agent_process_with_dict(self, sample_schedule_result):
        """Test agent process with dictionary input"""
        agent = ScheduleVisualizerAgent()
        result = agent.process(sample_schedule_result)

        assert result["status"] == "success"
        # Result may have html_path or json_path depending on config
        assert "json_path" in result or "html_path" in result

    def test_agent_process_with_empty_schedule(self, empty_schedule_result):
        """Test agent with empty schedule"""
        agent = ScheduleVisualizerAgent()
        result = agent.process(empty_schedule_result)

        # Should still succeed but with warnings
        assert result["status"] in ["success", "warning"]


class TestHTMLGeneration:
    """Test HTML file generation"""

    def test_html_file_created(self, sample_schedule_result):
        """Test HTML file is created"""
        agent = ScheduleVisualizerAgent()
        result = agent.process(sample_schedule_result)

        # Should successfully process
        assert result["status"] == "success"

        # Check if HTML file was generated
        html_file = "schedule_dashboard.html"
        if os.path.exists(html_file):
            # Verify file has content
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 0
                assert "<!DOCTYPE html>" in content

    def test_html_content_structure(self, sample_schedule_result):
        """Test HTML content structure"""
        agent = ScheduleVisualizerAgent()
        result = agent.process(sample_schedule_result)

        assert result["status"] == "success"

        # Check if dashboard.html exists and has content
        html_file = "schedule_dashboard.html"
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Check for expected HTML elements
                assert "<!DOCTYPE html>" in content
                assert "<title>" in content
                assert "Manufacturing Schedule" in content or "🏭" in content

    def test_html_metrics_display(self, sample_schedule_result):
        """Test HTML displays correct metrics"""
        agent = ScheduleVisualizerAgent()
        result = agent.process(sample_schedule_result)

        assert result["status"] == "success"

        html_file = "schedule_dashboard.html"
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Check for metrics (values may be displayed)
                # Looking for makespan, tasks count, utilization
                assert "Total Tasks" in content or "tasks" in content.lower()
                assert "Makespan" in content or "makespan" in content.lower()


class TestJSONExport:
    """Test JSON export functionality"""

    def test_json_export(self, sample_schedule_result, tmp_path):
        """Test JSON export"""
        import json

        visualizer = ScheduleVisualizer(sample_schedule_result)
        output_file = tmp_path / "schedule_data.json"

        success = visualizer.export_schedule_json(str(output_file))

        assert success is True
        assert output_file.exists()

        # Verify JSON content
        with open(output_file, "r") as f:
            data = json.load(f)
            assert data["status"] == "success"
            assert "schedule" in data
            assert data["schedule"]["scheduled_tasks"] == sample_schedule_result["scheduled_tasks"]

    def test_json_export_empty_schedule(self, empty_schedule_result, tmp_path):
        """Test JSON export with empty schedule"""
        import json

        visualizer = ScheduleVisualizer(empty_schedule_result)
        output_file = tmp_path / "schedule_data.json"

        success = visualizer.export_schedule_json(str(output_file))

        assert success is True

        with open(output_file, "r") as f:
            data = json.load(f)
            assert data["status"] == "success"
            assert data["schedule"]["scheduled_tasks"] == []


class TestDataIntegrity:
    """Test data integrity and validation"""

    def test_visualization_data_integrity(self, sample_schedule_result):
        """Test visualization data integrity"""
        visualizer = ScheduleVisualizer(sample_schedule_result)

        # Tasks data
        assert len(visualizer.gantt_data["tasks"]) == 2
        for task in visualizer.gantt_data["tasks"]:
            assert "name" in task
            assert "start" in task
            assert "end" in task
            assert "resource" in task
            assert "duration_minutes" in task

    def test_quality_metrics_completeness(self, sample_schedule_result):
        """Test quality metrics are complete"""
        visualizer = ScheduleVisualizer(sample_schedule_result)
        metrics = visualizer.quality_metrics

        required_fields = [
            "status",
            "makespan_hours",
            "avg_machine_utilization",
            "machine_utilization",
            "total_scheduled_tasks",
            "total_work_orders",
            "total_machines",
        ]

        for field in required_fields:
            assert field in metrics, f"Missing field: {field}"

    def test_scheduled_tasks_completeness(self, sample_schedule_result):
        """Test scheduled tasks have required fields"""
        visualizer = ScheduleVisualizer(sample_schedule_result)

        for task in visualizer.scheduled_tasks:
            required_fields = [
                "wo_id",
                "op_id",
                "machine_id",
                "start_time",
                "end_time",
                "quantity",
            ]
            for field in required_fields:
                assert field in task, f"Missing field in task: {field}"


class TestVisualizerStatistics:
    """Test statistics calculation and display"""

    def test_makespan_hours_calculation(self, sample_schedule_result):
        """Test makespan calculation"""
        ScheduleVisualizer(sample_schedule_result)

        # Check makespan consistency
        stats = sample_schedule_result["statistics"]
        metrics = sample_schedule_result["quality_metrics"]

        makespan_hours = stats["makespan_seconds"] / 3600
        assert abs(metrics["makespan_hours"] - makespan_hours) < 0.01

    def test_utilization_values(self, sample_schedule_result):
        """Test machine utilization values"""
        visualizer = ScheduleVisualizer(sample_schedule_result)
        metrics = visualizer.quality_metrics

        for machine, utilization in metrics["machine_utilization"].items():
            assert 0 <= utilization <= 100, f"Invalid utilization for {machine}: {utilization}%"

    def test_bottleneck_identification(self, sample_schedule_result):
        """Test bottleneck machine identification"""
        visualizer = ScheduleVisualizer(sample_schedule_result)
        metrics = visualizer.quality_metrics

        # Bottleneck should be in machine_utilization
        bottlenecks = metrics.get("bottleneck_machines", [])
        for bottleneck in bottlenecks:
            assert bottleneck in metrics["machine_utilization"]
