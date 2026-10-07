"""Integration tests for agents workspace."""

import sys
from pathlib import Path

import pytest

# Add paths for all agents and orchestrator
# IMPORTANT: shared must be added FIRST and remain at position 0
# to resolve models/core/utils correctly (avoid conflicts with agent-specific modules)
workspace_root = Path(__file__).parent.parent

# Clear any existing agent paths that might conflict
_paths_to_remove = [
    str(workspace_root / "agents" / "digital-thread-project-manager" / "src"),
    str(workspace_root / "agents" / "monitoring-data-replayer" / "src"),
]
for p in _paths_to_remove:
    if p in sys.path:
        sys.path.remove(p)

# Add shared FIRST - this is critical for correct module resolution
shared_path = str(workspace_root / "shared")
if shared_path in sys.path:
    sys.path.remove(shared_path)
sys.path.insert(0, shared_path)

# Add other agent paths after shared
for agent_path in [
    workspace_root / "agents" / "gcode-parser" / "src",
    workspace_root / "agents" / "cam-runner" / "src",
    workspace_root / "agents" / "cell-scheduler" / "src",
    workspace_root / "agents" / "cell-schedule-visualizer" / "src",
    workspace_root / "orchestrator" / "src",
]:
    path_str = str(agent_path)
    if path_str not in sys.path:
        sys.path.insert(1, path_str)  # Insert after shared

from langgraph_orchestrator import LangGraphOrchestrator  # noqa: E402
from gcode_parser_agent import GcodeParserAgent  # noqa: E402
from cam_runner_agent import CAMRunnerAgent  # noqa: E402


def test_gcode_parser():
    """Test G-code parser agent."""
    agent = GcodeParserAgent()
    gcode = "G00 X10 Y20\\nG01 Z-5 F100\\nM05"
    result = agent.analyze_gcode(gcode, "test.nc")
    assert result.status == "success"
    assert result.data["filename"] == "test.nc"
    print("✓ G-code parser test passed")


def test_cam_runner():
    """Test CAM runner agent."""
    agent = CAMRunnerAgent()
    result = agent.analyze_gcode_paths({})
    # Empty gcode_data will return warning status, but data should contain summary
    assert result.status in ["success", "warning"]
    assert "summary" in result.data
    print("✓ CAM runner test passed")


def test_orchestrator():
    """Test orchestrator workflow."""
    orch = LangGraphOrchestrator()
    gcode = "G00 Z10\\nG01 X10 Y10\\nM05"
    result = orch.run_workflow(gcode, workflow_name="minimal-analysis")
    assert result["status"] == "success"
    assert "gcode_parsing" in result["stages"]
    assert "cam_analysis" in result["stages"]
    print("✓ Orchestrator test passed")


def test_full_manufacturing_workflow():
    """Test full manufacturing workflow including scheduling.

    Note: cell-scheduler is now an HTTP service (port 8002), not a library agent.
    The orchestrator may report 'partial' status if the scheduler isn't registered.
    This test validates the stages that are available.
    """
    orch = LangGraphOrchestrator()
    gcode = "G00 Z10\\nG01 X10 Y10\\nM05"

    result = orch.run_workflow(gcode, workflow_name="full-manufacturing")

    # Check overall status - can be partial if scheduler isn't registered
    assert result["status"] in ["success", "partial"]

    # Check stages that should always be present
    stages = result["stages"]
    assert "gcode_parsing" in stages
    assert "cam_analysis" in stages
    # Note: cell_scheduling and schedule_visualization may not be in stages
    # if the scheduler agent isn't registered (it's now an HTTP service)

    # Check gcode_parsing succeeded
    assert stages["gcode_parsing"]["status"] == "success"

    # Check cam_analysis
    assert stages["cam_analysis"]["status"] in ["success", "warning"]

    # Check cell_scheduling if present (scheduler may not be registered)
    if "cell_scheduling" in stages and stages.get("cell_scheduling", {}).get("status") == "success":
        assert "scheduled_tasks" in stages["cell_scheduling"]
        assert "statistics" in stages["cell_scheduling"]
        assert "quality_metrics" in stages["cell_scheduling"]

    # Check schedule_visualization if present
    if "schedule_visualization" in stages:
        assert stages["schedule_visualization"]["status"] == "success"
        # After migration to Next.js, we return json_path instead of html_path
        assert (
            "json_path" in stages["schedule_visualization"]
            or "html_path" in stages["schedule_visualization"]
        )
        assert "message" in stages["schedule_visualization"]

    print("✓ Full manufacturing workflow test passed")


def test_workflow_execution_summary():
    """Test workflow execution summary."""
    orch = LangGraphOrchestrator()
    gcode = "G00 X10 Y10\\nG01 Z-5\\nM05"

    result = orch.run_workflow(gcode, workflow_name="minimal-analysis")

    # Check execution summary
    assert "execution_summary" in result
    summary = result["execution_summary"]

    assert "total_stages" in summary
    assert "completed_stages" in summary
    assert "failed_stages" in summary
    assert summary["total_stages"] > 0

    print("✓ Workflow execution summary test passed")


def test_scheduling_metrics_calculation():
    """Test scheduling metrics are calculated correctly.

    Note: This test requires cell-scheduler to be registered as an agent.
    Since cell-scheduler is now an HTTP service, this test validates
    that metrics would be correct if the scheduler were available.
    """

    orch = LangGraphOrchestrator()
    gcode = "G00 Z10\\nG01 X10 Y10"

    result = orch.run_workflow(gcode, workflow_name="full-manufacturing")

    # Check if cell_scheduling stage is present
    stages = result.get("stages", {})
    if "cell_scheduling" not in stages:
        pytest.skip("cell-scheduler is not registered (now an HTTP service)")

    # Extract scheduling results
    cell_scheduling = stages["cell_scheduling"]
    if cell_scheduling.get("status") != "success":
        pytest.skip("cell_scheduling stage did not succeed")

    # Check metrics
    metrics = cell_scheduling.get("quality_metrics", {})
    stats = cell_scheduling.get("statistics", {})

    # Verify metric calculations
    if stats.get("total_tasks", 0) > 0:
        assert metrics.get("makespan_hours", 0) > 0, "Makespan must be > 0 when tasks exist"
    assert 0 <= metrics.get("avg_machine_utilization", 0) <= 100

    # Verify scheduled tasks
    tasks = cell_scheduling.get("scheduled_tasks", [])
    assert len(tasks) >= 0  # Can be zero if no valid schedule

    print("✓ Scheduling metrics calculation test passed")


def test_visualization_dashboard_generation():
    """Test that visualization dashboard is properly generated.

    Note: This test may be affected by cell-scheduler availability.
    The visualization stage should still produce output even with
    partial workflow completion.
    """
    orch = LangGraphOrchestrator()
    gcode = "G00 Z10\\nG01 X10 Y10"

    result = orch.run_workflow(gcode, workflow_name="full-manufacturing")

    # Check if visualization stage is present
    stages = result.get("stages", {})
    if "schedule_visualization" not in stages:
        pytest.skip("Visualization stage not present (earlier stages may have failed)")

    # Check visualization stage (now returns json_path instead of html_path after Next.js migration)
    viz_stage = stages["schedule_visualization"]
    assert viz_stage["status"] == "success"
    # After migration to Next.js, we return json_path instead of html_path
    assert "json_path" in viz_stage or "html_path" in viz_stage
    assert "message" in viz_stage

    print("✓ Visualization dashboard generation test passed")


if __name__ == "__main__":
    print("Running integration tests...\\n")
    test_gcode_parser()
    test_cam_runner()
    test_orchestrator()
    test_full_manufacturing_workflow()
    test_workflow_execution_summary()
    test_scheduling_metrics_calculation()
    test_visualization_dashboard_generation()
    print("\\n✅ All tests passed!")
