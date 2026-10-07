"""Tests for CellSchedulerAgent."""

import pytest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.cell_scheduler_agent import CellSchedulerAgent, DataLoader
from src.solvers import (
    WorkOrder,
    Machine,
)


SAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "samples" / "cell-scheduler"


class TestDataLoader:
    """Tests for DataLoader class."""

    @pytest.fixture
    def sample_input_dir(self, tmp_path):
        """Create sample input files."""
        # 00_scheduling_request.json
        request = {
            "scheduling_request": {
                "scheduling_horizon": {
                    "start": datetime.now(timezone.utc).isoformat(),
                    "end": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                }
            }
        }
        (tmp_path / "00_scheduling_request.json").write_text(json.dumps(request))

        # 01_work_orders.json
        work_orders = {
            "work_orders": [
                {
                    "wo_id": "WO-001",
                    "product_id": "PROD-001",
                    "product_name": "Test Product",
                    "order_quantity": 10,
                    "due_date": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                    "priority": 5,
                    "release_date": datetime.now(timezone.utc).isoformat(),
                    "customer": "Test Customer",
                    "jobs": [
                        {
                            "op_id": "JOB-001",
                            "part_id": "PART-001",
                            "part_name": "Test Part",
                            "quantity": 10,
                            "material": "Steel",
                            "operations": [
                                {
                                    "op_id": "OP-001",
                                    "op_name": "Machining",
                                    "sequence": 10,
                                    "predecessors": [],
                                    "required_machines": ["CNC"],
                                    "setup_id": "SETUP-A",
                                    "nc_code": {
                                        "program_id": "NC-001",
                                        "file_path": "/nc/test.nc",
                                        "cycle_time_sec": 300,
                                        "cycle_time_confidence": 0.95,
                                        "tool_list": ["T01"],
                                        "tool_change_count": 1,
                                        "compatible_machines": ["CNC"],
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        (tmp_path / "01_work_orders.json").write_text(json.dumps(work_orders))

        # 02_machines.json
        machines = {
            "machines": [
                {
                    "machine_id": "CNC-001",
                    "machine_name": "CNC Machine 1",
                    "machine_type": "CNC",
                    "status": "AVAILABLE",
                    "available_from": datetime.now(timezone.utc).isoformat(),
                    "current_setup_id": None,
                    "setup_change_time_min": 5,
                }
            ]
        }
        (tmp_path / "02_machines.json").write_text(json.dumps(machines))

        # 03_machine_type_params.json
        params = {
            "machine_type_params": {
                "CNC": {
                    "loading_type": "AMR",
                    "amr_transport_qty": 1,
                    "exchange_time_sec": 60,
                    "load_unload_time_sec": 30,
                }
            }
        }
        (tmp_path / "03_machine_type_params.json").write_text(json.dumps(params))

        # 05_cell_layout.json
        layout = {"cell_layout": {"rows": 2, "cols": 3}}
        (tmp_path / "05_cell_layout.json").write_text(json.dumps(layout))

        # 06_constraints.json
        constraints = {"constraints": {"max_setup_changes": 5}}
        (tmp_path / "06_constraints.json").write_text(json.dumps(constraints))

        return tmp_path

    def test_load_all(self, sample_input_dir):
        """Should load all input files."""
        loader = DataLoader(str(sample_input_dir))
        data = loader.load_all()

        assert "request" in data
        assert "work_orders" in data
        assert "machines" in data
        assert "machine_type_params" in data
        assert "cell_layout" in data
        assert "constraints" in data

    def test_parse_work_orders(self, sample_input_dir):
        """Should parse work orders correctly."""
        loader = DataLoader(str(sample_input_dir))
        data = loader.load_all()

        assert len(data["work_orders"]) == 1
        wo = data["work_orders"][0]
        assert isinstance(wo, WorkOrder)
        assert wo.wo_id == "WO-001"
        assert len(wo.operations) == 1

    def test_parse_machines(self, sample_input_dir):
        """Should parse machines correctly."""
        loader = DataLoader(str(sample_input_dir))
        data = loader.load_all()

        assert len(data["machines"]) == 1
        machine = data["machines"][0]
        assert isinstance(machine, Machine)
        assert machine.machine_id == "CNC-001"

    def test_horizon_start_set(self, sample_input_dir):
        """Should set horizon_start from request."""
        loader = DataLoader(str(sample_input_dir))
        loader.load_all()

        assert loader.horizon_start is not None
        assert isinstance(loader.horizon_start, datetime)


class TestCellSchedulerAgentInit:
    """Tests for CellSchedulerAgent initialization."""

    def test_init_defaults(self):
        """Should initialize with defaults."""
        agent = CellSchedulerAgent()

        assert agent.name == "cell-scheduler"
        assert agent.solver is None  # Initialized on first use

    def test_init_with_config(self):
        """Should accept config dictionary."""
        config = {"solver_type": "GA", "time_limit_sec": 120}
        agent = CellSchedulerAgent(config=config)

        assert agent.config == config

    def test_init_empty_config(self):
        """Should work with empty config."""
        agent = CellSchedulerAgent(config={})

        assert agent.config == {}


class TestCellSchedulerAgentProcess:
    """Tests for CellSchedulerAgent.process method."""

    @pytest.fixture
    def agent(self):
        return CellSchedulerAgent()

    @pytest.mark.skipif(not (SAMPLES_DIR / "input").exists(), reason="Sample input files not found")
    def test_process_with_sample_dir(self, agent):
        """Should process sample input directory."""
        input_dir = str(SAMPLES_DIR / "input")
        result = agent.process(input_dir)

        assert isinstance(result, dict)
        assert "status" in result
        # May be success or no_solution depending on data

    def test_process_with_dict_input(self, agent):
        """Should process dictionary input."""
        now = datetime.now(timezone.utc)
        input_data = {
            "request": {
                "scheduling_request": {
                    "scheduling_horizon": {
                        "start": now.isoformat(),
                        "end": (now + timedelta(hours=8)).isoformat(),
                    }
                }
            },
            "work_orders": [
                {
                    "wo_id": "WO-001",
                    "product_id": "PROD-001",
                    "product_name": "Test",
                    "order_quantity": 5,
                    "due_date": (now + timedelta(hours=8)).isoformat(),
                    "priority": 5,
                    "release_date": now.isoformat(),
                    "customer": "Test",
                    "jobs": [
                        {
                            "op_id": "JOB-001",
                            "job_name": "Test Job",
                            "sequence": 1,
                            "operations": [
                                {
                                    "op_id": "OP-001",
                                    "op_name": "Test Op",
                                    "sequence": 1,
                                    "predecessors": [],
                                    "required_machines": ["CNC"],
                                    "setup_id": "SETUP-A",
                                    "nc_code": {
                                        "program_id": "NC-001",
                                        "file_path": "/nc/test.nc",
                                        "cycle_time_sec": 60,
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
            "machines": [
                {
                    "machine_id": "CNC-001",
                    "machine_name": "CNC 1",
                    "machine_type": "CNC",
                    "status": "available",
                    "available_from": now.isoformat(),
                }
            ],
            "machine_type_params": {
                "CNC": {
                    "setup_time_default": 5,
                    "processing_speed_factor": 1.0,
                }
            },
        }

        result = agent.process(input_data)

        assert isinstance(result, dict)
        assert "status" in result


class TestCellSchedulerAgentSolvers:
    """Tests for different solver integrations via SolverFactory."""

    @pytest.fixture
    def minimal_input(self):
        """Create minimal input for quick tests."""
        now = datetime.now(timezone.utc)
        return {
            "request": {
                "scheduling_request": {
                    "scheduling_horizon": {
                        "start": now.isoformat(),
                        "end": (now + timedelta(hours=4)).isoformat(),
                    }
                }
            },
            "work_orders": [
                {
                    "wo_id": "WO-001",
                    "product_id": "P1",
                    "product_name": "Product",
                    "order_quantity": 1,
                    "due_date": (now + timedelta(hours=4)).isoformat(),
                    "priority": 5,
                    "release_date": now.isoformat(),
                    "customer": "C1",
                    "jobs": [
                        {
                            "op_id": "J1",
                            "job_name": "Job",
                            "sequence": 1,
                            "operations": [
                                {
                                    "op_id": "O1",
                                    "op_name": "Op",
                                    "sequence": 1,
                                    "predecessors": [],
                                    "required_machines": ["CNC"],
                                    "setup_id": "S1",
                                    "nc_code": {
                                        "program_id": "N1",
                                        "file_path": "/n1.nc",
                                        "cycle_time_sec": 60,
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
            "machines": [
                {
                    "machine_id": "M1",
                    "machine_name": "Machine 1",
                    "machine_type": "CNC",
                    "status": "available",
                    "available_from": now.isoformat(),
                }
            ],
            "machine_type_params": {"CNC": {"setup_time_default": 5}},
        }

    def test_default_solver(self, minimal_input):
        """Should work with default solver."""
        agent = CellSchedulerAgent()
        result = agent.process(minimal_input)

        assert "status" in result

    def test_with_solver_config(self, minimal_input):
        """Should work with solver specified in input."""
        minimal_input["solver_type"] = "OR_TOOLS"
        minimal_input["time_limit_sec"] = 5

        agent = CellSchedulerAgent()
        result = agent.process(minimal_input)

        assert "status" in result


class TestCellSchedulerAgentOutput:
    """Tests for output format."""

    @pytest.fixture
    def agent(self):
        return CellSchedulerAgent()

    @pytest.fixture
    def minimal_input(self):
        now = datetime.now(timezone.utc)
        return {
            "request": {
                "scheduling_request": {
                    "scheduling_horizon": {
                        "start": now.isoformat(),
                        "end": (now + timedelta(hours=4)).isoformat(),
                    }
                }
            },
            "work_orders": [
                {
                    "wo_id": "WO-001",
                    "product_id": "P1",
                    "product_name": "Product",
                    "order_quantity": 1,
                    "due_date": (now + timedelta(hours=4)).isoformat(),
                    "priority": 5,
                    "release_date": now.isoformat(),
                    "customer": "C1",
                    "jobs": [
                        {
                            "op_id": "J1",
                            "job_name": "Job",
                            "sequence": 1,
                            "operations": [
                                {
                                    "op_id": "O1",
                                    "op_name": "Op",
                                    "sequence": 1,
                                    "predecessors": [],
                                    "required_machines": ["CNC"],
                                    "setup_id": "S1",
                                    "nc_code": {
                                        "program_id": "N1",
                                        "file_path": "/n1.nc",
                                        "cycle_time_sec": 60,
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
            "machines": [
                {
                    "machine_id": "M1",
                    "machine_name": "Machine 1",
                    "machine_type": "CNC",
                    "status": "available",
                    "available_from": now.isoformat(),
                }
            ],
            "machine_type_params": {"CNC": {"setup_time_default": 5}},
        }

    def test_output_has_status(self, agent, minimal_input):
        """Output should have status field."""
        result = agent.process(minimal_input)
        assert "status" in result

    def test_output_has_scheduled_tasks(self, agent, minimal_input):
        """Output should have scheduled_tasks field."""
        result = agent.process(minimal_input)
        assert "scheduled_tasks" in result

    def test_output_has_statistics(self, agent, minimal_input):
        """Output should have statistics fields."""
        result = agent.process(minimal_input)

        # Statistics are in quality_metrics or solver_info
        if result.get("status") == "success":
            has_stats = (
                "quality_metrics" in result or "solver_info" in result or "solve_time_sec" in result
            )
            assert has_stats
