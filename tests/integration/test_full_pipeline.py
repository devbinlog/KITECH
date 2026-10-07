"""
Full Integration Test for Manufacturing Agent Pipeline

Tests the complete workflow:
1. G-code parsing
2. CAM analysis with cycle time calculation
3. Cell scheduling with multiple solvers
4. Schedule visualization

Run with: cd agents-workspace && uv run pytest tests/integration/test_full_pipeline.py -v
"""

import sys
from pathlib import Path
import pytest

# Add paths
workspace = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace / "orchestrator" / "src"))
sys.path.insert(0, str(workspace / "agents" / "gcode-parser" / "src"))
sys.path.insert(0, str(workspace / "agents" / "cam-runner" / "src"))
sys.path.insert(0, str(workspace / "agents" / "cell-scheduler" / "src"))
sys.path.insert(0, str(workspace / "agents" / "cell-schedule-visualizer" / "src"))
sys.path.insert(0, str(workspace / "shared"))


class TestGCodeParser:
    """Test G-code parser agent"""

    def test_parse_simple_gcode(self):
        """Test parsing simple G-code"""
        from gcode_parser_agent import GcodeParserAgent

        gcode = """
        G21
        G90
        G00 X0 Y0 Z25
        G01 Z-5 F500
        G01 X50 Y0 F1000
        G01 X50 Y50
        G00 Z25
        M30
        """

        agent = GcodeParserAgent()
        result = agent.process(gcode)

        assert result["status"] == "success"
        assert result["data"]["total_commands"] > 0
        assert result["data"]["cutting_distance"] > 0
        assert result["data"]["feed_rate"] > 0

    def test_parse_file(self):
        """Test parsing G-code from file"""
        from gcode_parser_agent import GcodeParserAgent

        sample_file = workspace / "samples/gcode-parser/simple/001_simple_square.nc"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        agent = GcodeParserAgent()
        result = agent.process(str(sample_file))

        assert result["status"] == "success"
        assert result["data"]["gcode_blocks"]


class TestCAMRunner:
    """Test CAM runner agent with cycle time calculation"""

    def test_analyze_paths(self):
        """Test path analysis"""
        from gcode_parser_agent import GcodeParserAgent
        from cam_runner_agent import CAMRunnerAgent

        gcode = """
        G21
        G90
        G00 X0 Y0 Z25
        G01 Z-5 F500
        G01 X50 Y0 F1000
        G01 X50 Y50
        G00 Z25
        M30
        """

        parser = GcodeParserAgent()
        parsed = parser.process(gcode)

        cam = CAMRunnerAgent()
        result = cam.analyze_gcode_paths(parsed["data"])

        if hasattr(result, "to_dict"):
            result = result.to_dict()

        assert result["status"] == "success"
        assert "cycle_time" in result["data"]

    def test_cycle_time_calculation(self):
        """Test cycle time is calculated correctly"""
        from gcode_parser_agent import GcodeParserAgent
        from cam_runner_agent import CAMRunnerAgent

        gcode = """
        G21
        G90
        G00 X0 Y0 Z25
        G01 Z-5 F500
        G01 X100 Y0 F1000
        G00 Z25
        M30
        """

        parser = GcodeParserAgent()
        parsed = parser.process(gcode)

        cam = CAMRunnerAgent()
        result = cam.analyze_gcode_paths(parsed["data"])

        if hasattr(result, "to_dict"):
            result = result.to_dict()

        cycle_time = result["data"]["cycle_time"]

        # Verify cycle time components exist
        assert cycle_time["cutting_time_sec"] > 0
        assert cycle_time["total_cycle_time_sec"] > 0
        assert cycle_time["feed_rate_used"] == 1000


class TestCellScheduler:
    """Test cell scheduler with multiple solvers"""

    @pytest.fixture
    def input_dir(self):
        return str(workspace / "samples/cell-scheduler/input")

    def test_ortools_solver(self, input_dir):
        """Test OR-Tools solver"""
        from cell_scheduler_agent import CellSchedulerAgent

        agent = CellSchedulerAgent()
        result = agent.process(input_dir, solver_type="OR_TOOLS")

        assert result["status"] == "success"
        assert result["statistics"]["total_tasks"] > 0
        assert result["statistics"]["makespan_hours"] > 0

    def test_genetic_algorithm_solver(self, input_dir):
        """Test GA solver"""
        from cell_scheduler_agent import CellSchedulerAgent

        agent = CellSchedulerAgent()
        result = agent.process(input_dir, solver_type="GA")

        assert result["status"] == "success"
        assert result["statistics"]["total_tasks"] > 0

    def test_simulated_annealing_solver(self, input_dir):
        """Test SA solver"""
        from cell_scheduler_agent import CellSchedulerAgent

        agent = CellSchedulerAgent()
        result = agent.process(input_dir, solver_type="SA")

        assert result["status"] == "success"
        assert result["statistics"]["total_tasks"] > 0

    def test_tabu_search_solver(self, input_dir):
        """Test Tabu Search solver"""
        from cell_scheduler_agent import CellSchedulerAgent

        agent = CellSchedulerAgent()
        result = agent.process(input_dir, solver_type="TABU")

        assert result["status"] == "success"
        assert result["statistics"]["total_tasks"] > 0

    def test_alns_solver(self, input_dir):
        """Test ALNS solver"""
        from cell_scheduler_agent import CellSchedulerAgent

        agent = CellSchedulerAgent()
        result = agent.process(input_dir, solver_type="ALNS")

        assert result["status"] == "success"
        assert result["statistics"]["total_tasks"] > 0

    def test_solver_comparison(self, input_dir):
        """Compare all solvers produce reasonable results"""
        from cell_scheduler_agent import CellSchedulerAgent

        solvers = ["OR_TOOLS", "GA", "SA", "TABU", "ALNS"]
        results = {}

        for solver in solvers:
            agent = CellSchedulerAgent()
            result = agent.process(input_dir, solver_type=solver)
            results[solver] = result["statistics"]["makespan_hours"]

        # All solvers should find a solution
        assert all(r > 0 for r in results.values())

        # Metaheuristics should be within 20% of OR-Tools
        ortools_makespan = results["OR_TOOLS"]
        for solver, makespan in results.items():
            if solver != "OR_TOOLS":
                gap = (makespan - ortools_makespan) / ortools_makespan
                assert gap < 0.20, f"{solver} gap {gap:.2%} exceeds 20%"


class TestOrchestrator:
    """Test LangGraph orchestrator"""

    def test_workflow_loading(self):
        """Test workflows load correctly"""
        from workflows import list_workflows

        workflows = list_workflows()
        assert "minimal-analysis" in workflows
        assert "full-manufacturing" in workflows

    def test_minimal_workflow(self):
        """Test minimal analysis workflow"""
        from langgraph_orchestrator import LangGraphOrchestrator

        gcode = """
        G21
        G90
        G00 X0 Y0 Z25
        G01 Z-5 F500
        G01 X50 Y0 F1000
        G00 Z25
        M30
        """

        orchestrator = LangGraphOrchestrator()
        result = orchestrator.run_workflow(gcode_input=gcode, workflow_name="minimal-analysis")

        assert result["status"] == "success"
        assert "gcode_parsing" in result["execution_summary"]["stages_completed"]
        assert "cam_analysis" in result["execution_summary"]["stages_completed"]

    def test_full_workflow(self):
        """Test full manufacturing workflow"""
        from langgraph_orchestrator import LangGraphOrchestrator

        gcode = """
        G21
        G90
        G00 X0 Y0 Z25
        G01 Z-5 F500
        G01 X50 Y0 F1000
        G00 Z25
        M30
        """

        orchestrator = LangGraphOrchestrator()
        result = orchestrator.run_workflow(gcode_input=gcode, workflow_name="full-manufacturing")

        # Should complete at least the first stages
        assert result["status"] in ["success", "partial"]
        assert len(result["execution_summary"]["stages_completed"]) >= 2


class TestRESTAPIs:
    """Test REST API endpoints (requires services running)"""

    @pytest.fixture
    def skip_if_no_service(self):
        import httpx

        try:
            resp = httpx.get("http://localhost:8002/health", timeout=2)
            if resp.status_code != 200:
                pytest.skip("Cell-Scheduler service not running")
        except Exception:
            pytest.skip("Cell-Scheduler service not running")

    def test_scheduler_health(self, skip_if_no_service):
        """Test scheduler health endpoint"""
        import httpx

        resp = httpx.get("http://localhost:8002/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_scheduler_openapi(self, skip_if_no_service):
        """Test scheduler OpenAPI spec"""
        import httpx

        resp = httpx.get("http://localhost:8002/api/v1/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "Cell-Scheduler API"
        assert "/api/v1/schedule/solve" in data["paths"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
