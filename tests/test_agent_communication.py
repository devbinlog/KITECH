"""Tests for agent-to-agent communication."""

import pytest
from datetime import datetime, timedelta


class TestMESToSchedulerCommunication:
    """Test MES to Cell-Scheduler communication."""

    @pytest.fixture
    def sample_scheduling_request(self):
        """Create a sample scheduling request."""
        return {
            "work_orders": [
                {
                    "wo_id": "WO-001",
                    "product_id": "PROD-001",
                    "product_name": "Test Product",
                    "order_quantity": 10,
                    "due_date": (datetime.now() + timedelta(hours=24)).isoformat(),
                    "priority": 5,
                    "release_date": datetime.now().isoformat(),
                    "customer": "Test Customer",
                    "jobs": [
                        {
                            "job_id": "JOB-001",
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
                                    "required_machine_type": "CNC",
                                    "setup_id": "SETUP-A",
                                    "nc_code": {
                                        "program_id": "NC-001",
                                        "file_path": "/nc/test.nc",
                                        "cycle_time_sec": 300,
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
                    "machine_name": "CNC Machine 1",
                    "machine_type": "CNC",
                    "status": "AVAILABLE",
                    "available_from": datetime.now().isoformat(),
                    "current_setup_id": None,
                    "setup_change_time_min": 5,
                }
            ],
            "machine_type_params": {
                "CNC": {
                    "loading_type": "MANUAL",
                    "amr_transport_qty": 1,
                    "exchange_time_sec": 30,
                    "load_unload_time_sec": 60,
                }
            },
            "scheduling_horizon": {
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(hours=24)).isoformat(),
            },
            "constraints": {},
            "options": {
                "solver_type": "OR_TOOLS",
                "time_limit_sec": 60,
            },
        }

    @pytest.fixture
    def sample_scheduling_response(self):
        """Create a sample scheduling response."""
        return {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": "WO-001",
                    "job_id": "JOB-001",
                    "op_id": "OP-001",
                    "machine_id": "CNC-001",
                    "start_time": 0,
                    "end_time": 300,
                    "quantity": 10,
                    "setup_time": 60,
                }
            ],
            "statistics": {
                "total_tasks": 1,
                "makespan_seconds": 360,
                "makespan_hours": 0.1,
                "machine_utilization": {"CNC-001": 83.3},
                "bottleneck_machines": [],
                "solve_time_sec": 2.5,
            },
            "quality_metrics": {
                "status": "FEASIBLE",
                "makespan_hours": 0.1,
                "total_lateness_hours": 0,
                "avg_machine_utilization": 83.3,
                "schedule_efficiency": 95.0,
                "per_wo_lateness": {},
                "bottleneck_machines": [],
            },
            "gantt_data": {
                "tasks": [
                    {
                        "wo_id": "WO-001",
                        "name": "WO-001 - Test Product (OP-001)",
                        "start": datetime.now().isoformat(),
                        "end": (datetime.now() + timedelta(minutes=6)).isoformat(),
                        "resource": "CNC-001",
                        "priority": 5,
                        "quantity": 10,
                    }
                ],
                "resources": ["CNC-001"],
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(hours=24)).isoformat(),
            },
            "solver_info": {
                "solver_type": "OR_TOOLS",
                "solve_time_sec": 2.5,
            },
        }

    def test_request_format_validation(self, sample_scheduling_request):
        """Validate scheduling request format."""
        request = sample_scheduling_request

        # Required top-level fields
        assert "work_orders" in request
        assert "machines" in request
        assert "machine_type_params" in request
        assert "scheduling_horizon" in request
        assert "options" in request

        # Work order structure
        wo = request["work_orders"][0]
        assert "wo_id" in wo
        assert "product_id" in wo
        assert "due_date" in wo
        assert "priority" in wo
        assert "jobs" in wo

        # Job structure
        job = wo["jobs"][0]
        assert "job_id" in job
        assert "operations" in job

        # Operation structure
        op = job["operations"][0]
        assert "op_id" in op
        assert "required_machine_type" in op
        assert "nc_code" in op

    def test_response_format_validation(self, sample_scheduling_response):
        """Validate scheduling response format."""
        response = sample_scheduling_response

        # Required top-level fields
        assert "status" in response
        assert "scheduled_tasks" in response
        assert "statistics" in response
        assert "quality_metrics" in response
        assert "gantt_data" in response

        # Scheduled task structure
        task = response["scheduled_tasks"][0]
        assert "wo_id" in task
        assert "job_id" in task
        assert "op_id" in task
        assert "machine_id" in task
        assert "start_time" in task
        assert "end_time" in task

        # Statistics structure
        stats = response["statistics"]
        assert "total_tasks" in stats
        assert "makespan_seconds" in stats
        assert "machine_utilization" in stats

    def test_wo_id_format(self, sample_scheduling_request, sample_scheduling_response):
        """WO ID should match between request and response."""
        request_wo_id = sample_scheduling_request["work_orders"][0]["wo_id"]
        response_wo_id = sample_scheduling_response["scheduled_tasks"][0]["wo_id"]

        # IDs should match
        assert request_wo_id == response_wo_id

        # ID format should be "WO-XXX"
        assert response_wo_id.startswith("WO-")

    def test_time_values_are_integers(self, sample_scheduling_response):
        """Start and end times should be integers (seconds from horizon start)."""
        task = sample_scheduling_response["scheduled_tasks"][0]

        assert isinstance(task["start_time"], int)
        assert isinstance(task["end_time"], int)
        assert task["end_time"] > task["start_time"]


class TestSchedulerResponseProcessing:
    """Test processing of scheduler responses."""

    @pytest.fixture
    def sample_processing_result(self):
        """Sample result after processing scheduler response."""
        return {
            "success": True,
            "message": "Schedule approved and applied",
            "updated_orders": [
                {
                    "mes_order_id": 1,
                    "wo_id": "WO-001",
                    "lot_no": "LOT-2026-001",
                    "plan_start": "2026-01-25T10:00:00",
                    "plan_end": "2026-01-25T10:06:00",
                    "machine_id": "CNC-001",
                }
            ],
            "statistics": {
                "total_updated": 1,
                "total_scheduled": 1,
                "horizon_start": "2026-01-25T10:00:00",
            },
        }

    def test_processing_result_format(self, sample_processing_result):
        """Validate processing result format."""
        result = sample_processing_result

        assert "success" in result
        assert "message" in result
        assert "updated_orders" in result

        # Updated order structure
        order = result["updated_orders"][0]
        assert "mes_order_id" in order
        assert "wo_id" in order
        assert "plan_start" in order
        assert "plan_end" in order

    def test_time_conversion(self, sample_processing_result):
        """Plan times should be ISO format datetimes."""
        order = sample_processing_result["updated_orders"][0]

        # Should be parseable as datetime
        plan_start = datetime.fromisoformat(order["plan_start"])
        plan_end = datetime.fromisoformat(order["plan_end"])

        assert isinstance(plan_start, datetime)
        assert isinstance(plan_end, datetime)
        assert plan_end > plan_start


class TestNLRouterToMESCommunication:
    """Test NL-Router to MES communication."""

    @pytest.fixture
    def sample_nl_query(self):
        """Sample natural language query."""
        return {
            "query": "오늘 생산 현황 보여줘",
            "session_id": "test-session-001",
            "user_id": "test-user",
        }

    @pytest.fixture
    def sample_nl_response(self):
        """Sample NL-Router response."""
        return {
            "success": True,
            "intent": "PRODUCTION_STATUS",
            "confidence": 0.95,
            "entities": {
                "time_period": "TODAY",
            },
            "data": {
                "orders": [
                    {
                        "id": 1,
                        "lot_no": "LOT-2026-001",
                        "product_name": "Test Product",
                        "status": "RUNNING",
                        "target_qty": 100,
                    }
                ],
                "summary": {
                    "total_orders": 1,
                    "running": 1,
                    "completed": 0,
                },
            },
            "ui_schema": {
                "type": "DASHBOARD",
                "cards": [
                    {
                        "title": "진행중인 작업",
                        "value": 1,
                        "color": "blue",
                    }
                ],
            },
            "text_response": "현재 1개의 작업이 진행 중입니다.",
            "errors": [],
        }

    def test_query_format(self, sample_nl_query):
        """Validate NL query format."""
        assert "query" in sample_nl_query
        assert "session_id" in sample_nl_query
        assert isinstance(sample_nl_query["query"], str)
        assert len(sample_nl_query["query"]) > 0

    def test_response_format(self, sample_nl_response):
        """Validate NL response format."""
        response = sample_nl_response

        assert "success" in response
        assert "intent" in response
        assert "data" in response
        assert "ui_schema" in response
        assert "text_response" in response

    def test_intent_classification(self, sample_nl_response):
        """Intent should be a valid enum value."""
        valid_intents = [
            "PRODUCTION_STATUS",
            "PRODUCTION_DETAIL",
            "EQUIPMENT_STATUS",
            "EQUIPMENT_LIST",
            "SCHEDULE_QUERY",
            "SCHEDULE_REQUEST",
            "MASTER_DATA_QUERY",
            "KPI_QUERY",
            "ANALYTICS",
            "COMPARISON",
            "TRACEABILITY",
            "ERROR_DIAGNOSIS",
            "DELAY_PREDICTION",
            "DEFECT_ANALYSIS",
            "TOOL_MANAGEMENT",
            "ACTION_REQUEST",
            "UNKNOWN",
        ]

        assert sample_nl_response["intent"] in valid_intents

    def test_ui_schema_structure(self, sample_nl_response):
        """UI schema should have proper structure."""
        ui_schema = sample_nl_response["ui_schema"]

        assert "type" in ui_schema
        valid_types = ["DASHBOARD", "LIST", "TIMELINE", "CHART", "TABLE", "GANTT"]
        assert ui_schema["type"] in valid_types


class TestErrorPropagation:
    """Test error propagation between agents."""

    def test_scheduler_error_response(self):
        """Scheduler error response format."""
        error_response = {
            "status": "error",
            "message": "Solver timeout exceeded",
            "scheduled_tasks": [],
            "statistics": {
                "total_tasks": 0,
                "makespan_seconds": 0,
                "solve_time_sec": 60.0,
            },
            "quality_metrics": {
                "status": "NO_SOLUTION",
                "makespan_hours": 0,
            },
            "gantt_data": {
                "tasks": [],
                "resources": [],
                "start": "",
                "end": "",
            },
            "solver_info": {
                "solver_type": "OR_TOOLS",
                "error": "Timeout after 60 seconds",
            },
        }

        assert error_response["status"] == "error"
        assert "message" in error_response
        assert len(error_response["scheduled_tasks"]) == 0

    def test_nl_router_error_response(self):
        """NL-Router error response format."""
        error_response = {
            "success": False,
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "entities": {},
            "data": None,
            "ui_schema": None,
            "text_response": "죄송합니다. 요청을 이해하지 못했습니다.",
            "errors": [
                {
                    "code": "INTENT_CLASSIFICATION_FAILED",
                    "message": "Could not classify intent",
                }
            ],
        }

        assert error_response["success"] is False
        assert len(error_response["errors"]) > 0
        assert error_response["errors"][0]["code"] == "INTENT_CLASSIFICATION_FAILED"

    def test_mes_error_response(self):
        """MES error response format."""
        error_response = {
            "detail": "Work order not found",
            "status_code": 404,
        }

        assert "detail" in error_response
        assert error_response["status_code"] == 404


class TestDataConsistencyAcrossAgents:
    """Test data consistency between agents."""

    def test_equipment_id_consistency(self):
        """Equipment IDs should be consistent between MES and Scheduler."""
        # MES equipment format
        mes_equipment = {
            "id": 1,
            "eq_name": "CNC-001",
            "aas_id": "urn:aas:cnc:001",
            "equipment_type": "CNC",
        }

        # Scheduler machine format (transformed from MES)
        scheduler_machine = {
            "machine_id": f"EQ-{mes_equipment['id']}",
            "machine_name": mes_equipment["eq_name"],
            "machine_type": mes_equipment["equipment_type"],
        }

        # ID should follow "EQ-{id}" pattern
        assert scheduler_machine["machine_id"] == "EQ-1"
        assert scheduler_machine["machine_type"] == mes_equipment["equipment_type"]

    def test_work_order_id_consistency(self):
        """Work order IDs should be consistent between MES and Scheduler."""
        # MES work order
        mes_order = {
            "id": 123,
            "lot_no": "LOT-2026-001",
            "product_id": 1,
        }

        # Scheduler work order (transformed)
        scheduler_wo = {
            "wo_id": f"WO-{mes_order['id']}",
            "product_id": f"PROD-{mes_order['product_id']}",
        }

        # ID should follow "WO-{id}" pattern
        assert scheduler_wo["wo_id"] == "WO-123"

        # Reverse transformation
        mes_id = int(scheduler_wo["wo_id"].replace("WO-", ""))
        assert mes_id == mes_order["id"]
