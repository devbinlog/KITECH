"""
Tests for Cell-Scheduler Integration

Tests the integration between Cell-MES and Cell-Scheduler agents.
Operations are directly under WorkOrder (no Job layer).
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from src.protocols.scheduler_protocol import (
    EquipmentAvailability,
    WorkOrderForScheduling,
    SchedulingRequest,
    SchedulingResult,
    ScheduledTask,
    OperationInfo,
    NcCodeInfo,
)


class TestSchedulerProtocol:
    """Test the scheduler protocol data structures"""

    def test_equipment_availability_creation(self):
        """Test creating equipment availability data"""
        eq = EquipmentAvailability(
            machine_id="EQ-1",
            machine_name="CNC-001",
            machine_type="CNC",
            status="AVAILABLE",
            available_from="2024-01-01T09:00:00",
            setup_change_time_min=5,
            mes_equipment_id=1,
        )

        assert eq.machine_id == "EQ-1"
        assert eq.status == "AVAILABLE"

        # Test to_dict
        data = eq.to_dict()
        assert data["machine_id"] == "EQ-1"
        assert data["machine_type"] == "CNC"

    def test_equipment_availability_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "machine_id": "EQ-2",
            "machine_name": "Robot-001",
            "machine_type": "ROBOT",
            "status": "RUNNING",
            "available_from": "2024-01-01T10:00:00",
            "mes_equipment_id": 2,
        }

        eq = EquipmentAvailability.from_dict(data)
        assert eq.machine_id == "EQ-2"
        assert eq.machine_type == "ROBOT"

    def test_work_order_for_scheduling(self):
        """Test work order data structure (operations directly)"""
        nc_code = NcCodeInfo(
            program_id="NC-001",
            file_path="programs/part1.nc",
            cycle_time_sec=120,
        )

        operation = OperationInfo(
            op_id="OP-1",
            op_name="Machining",
            sequence=10,
            required_machine_type="CNC",
            nc_code=nc_code,
            cycle_time_sec=120,
            process_routing_id=1,
        )

        # Operations directly under work order, no jobs layer
        wo = WorkOrderForScheduling(
            wo_id="WO-1",
            product_id="PROD-1",
            product_name="Test Product",
            order_quantity=100,
            due_date="2024-01-02T17:00:00",
            priority=8,
            release_date="2024-01-01T09:00:00",
            operations=[operation],
            mes_work_order_id=1,
            lot_no="LOT-20240101-001",
        )

        assert wo.wo_id == "WO-1"
        assert wo.priority == 8
        assert len(wo.operations) == 1
        assert wo.operations[0].op_id == "OP-1"

        # Test to_dict
        data = wo.to_dict()
        assert data["wo_id"] == "WO-1"
        assert len(data["operations"]) == 1
        assert "jobs" not in data  # No jobs layer

    def test_operation_cycle_time(self):
        """Test operation cycle time getter"""
        nc_code = NcCodeInfo(
            program_id="NC-001",
            file_path="programs/part1.nc",
            cycle_time_sec=120,
        )

        # With direct cycle_time_sec
        op_with_direct = OperationInfo(
            op_id="OP-1",
            op_name="Machining",
            sequence=10,
            cycle_time_sec=90,
            nc_code=nc_code,
        )
        assert op_with_direct.get_cycle_time() == 90  # Direct value takes precedence

        # Without direct cycle_time_sec, falls back to nc_code
        op_from_nc = OperationInfo(
            op_id="OP-2",
            op_name="Machining",
            sequence=20,
            nc_code=nc_code,
        )
        assert op_from_nc.get_cycle_time() == 120  # From nc_code

        # Without any cycle time
        op_default = OperationInfo(
            op_id="OP-3",
            op_name="Machining",
            sequence=30,
        )
        assert op_default.get_cycle_time() == 60  # Default

    def test_scheduling_request(self):
        """Test creating scheduling request"""
        machines = [
            EquipmentAvailability(
                machine_id="EQ-1",
                machine_name="CNC-001",
                machine_type="CNC",
                status="AVAILABLE",
                available_from="2024-01-01T09:00:00",
            ),
            EquipmentAvailability(
                machine_id="EQ-2",
                machine_name="CNC-002",
                machine_type="CNC",
                status="AVAILABLE",
                available_from="2024-01-01T09:00:00",
            ),
        ]

        work_orders = [
            WorkOrderForScheduling(
                wo_id="WO-1",
                product_id="PROD-1",
                product_name="Product A",
                order_quantity=50,
                due_date="2024-01-02T17:00:00",
                priority=8,
                release_date="2024-01-01T09:00:00",
                operations=[],
            ),
        ]

        request = SchedulingRequest(
            request_id="REQ-001",
            request_time="2024-01-01T08:00:00",
            horizon_start="2024-01-01T09:00:00",
            horizon_end="2024-01-02T17:00:00",
            machines=machines,
            work_orders=work_orders,
        )

        # Convert to scheduler format
        scheduler_input = request.to_scheduler_format()

        assert "request" in scheduler_input
        assert "machines" in scheduler_input
        assert "work_orders" in scheduler_input
        assert len(scheduler_input["machines"]) == 2
        assert len(scheduler_input["work_orders"]) == 1

    def test_scheduled_task(self):
        """Test scheduled task structure"""
        task = ScheduledTask(
            wo_id="WO-1",
            op_id="OP-1",
            machine_id="EQ-1",
            start_time=0,
            end_time=3600,
            quantity=10,
        )

        assert task.wo_id == "WO-1"
        assert task.op_id == "OP-1"
        assert not hasattr(task, "job_id")  # No job_id field

    def test_scheduling_result_from_output(self):
        """Test parsing scheduling result"""
        scheduler_output = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": "WO-1",
                    "op_id": "OP-1",
                    "machine_id": "EQ-1",
                    "start_time": 0,
                    "end_time": 3600,
                    "quantity": 10,
                },
                {
                    "wo_id": "WO-1",
                    "op_id": "OP-2",
                    "machine_id": "EQ-2",
                    "start_time": 3600,
                    "end_time": 7200,
                    "quantity": 10,
                },
            ],
            "statistics": {
                "objective_value": 7200,
                "solve_time_sec": 1.5,
                "makespan_seconds": 7200,
                "machine_utilization": {"EQ-1": 50.0, "EQ-2": 50.0},
                "bottleneck_machines": [],
            },
            "gantt_data": {"tasks": []},
        }

        result = SchedulingResult.from_scheduler_output(scheduler_output)

        assert result.status == "success"
        assert len(result.scheduled_tasks) == 2
        assert result.total_makespan == 7200
        assert result.solve_time_sec == 1.5

        # Test filtering methods
        wo_tasks = result.get_tasks_for_work_order("WO-1")
        assert len(wo_tasks) == 2

        machine_tasks = result.get_tasks_for_machine("EQ-1")
        assert len(machine_tasks) == 1


class TestSchedulerIntegrationService:
    """Test the scheduler integration service"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return AsyncMock()

    @pytest.fixture
    def mock_equipment(self):
        """Create mock equipment data"""
        eq = MagicMock()
        eq.id = 1
        eq.name = "CNC-001"
        eq.equipment_type = "cnc"
        eq.status = "AVAILABLE"
        eq.is_active = True
        eq.aas_id = "aas-001"
        eq.location = "Line 1"
        eq.spec_data = {"machine_type": "CNC", "setup_change_time_min": 10}
        eq.last_data = None
        return eq

    @pytest.fixture
    def mock_work_order(self):
        """Create mock work order data"""
        wo = MagicMock()
        wo.id = 1
        wo.lot_no = "LOT-001"
        wo.product_id = 1
        wo.qty = 100
        wo.priority = 8
        wo.status = "READY"
        wo.due_date = datetime.now(timezone.utc) + timedelta(days=1)
        wo.start_time = datetime.now(timezone.utc)
        wo.remarks = "Test order"
        wo.scenario_id = None

        # Mock product
        product = MagicMock()
        product.name = "Test Product"
        wo.product = product

        return wo

    @pytest.mark.asyncio
    async def test_equipment_status_mapping(self):
        """Test equipment status mapping to scheduler format"""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        # Test status mapping
        service = SchedulerIntegrationService(AsyncMock())

        assert service._map_equipment_status("AVAILABLE") == "AVAILABLE"
        assert service._map_equipment_status("RUNNING") == "RUNNING"
        assert service._map_equipment_status("IDLE") == "AVAILABLE"
        assert service._map_equipment_status("ERROR") == "ERROR"
        assert service._map_equipment_status("UNKNOWN") == "OFFLINE"

class TestCellMesAgentIntegration:
    """Test CellMesAgent scheduler integration methods"""

    def test_agent_scheduling_actions(self):
        """Test agent has scheduling-related actions"""
        from src.cell_mes_agent import CellMesAgent

        agent = CellMesAgent()

        # Test create_scheduling_request action
        result = agent.process({"action": "create_scheduling_request", "horizon_hours": 48})
        assert result["status"] == "success"
        assert "48" in result["message"]

        # Test process_scheduling_result action
        result = agent.process(
            {
                "action": "process_scheduling_result",
                "scheduled_tasks": [{"wo_id": "WO-1", "machine_id": "EQ-1"}],
            }
        )
        assert result["status"] == "success"

    def test_agent_request_schedule(self):
        """Test agent request_schedule method"""
        from src.cell_mes_agent import CellMesAgent

        agent = CellMesAgent()
        result = agent.request_schedule(horizon_hours=12, include_running=True)

        assert result["status"] == "success"
        assert result["params"]["horizon_hours"] == 12
        assert result["params"]["include_running"]

    def test_agent_apply_schedule(self):
        """Test agent apply_schedule method"""
        from src.cell_mes_agent import CellMesAgent

        agent = CellMesAgent()

        scheduling_result = {
            "status": "success",
            "scheduled_tasks": [
                {"wo_id": "WO-1", "start_time": 0, "end_time": 3600},
            ],
        }

        result = agent.apply_schedule(scheduling_result)
        assert result["status"] == "success"

    def test_agent_notify_schedule_update(self):
        """Test agent notify_schedule_update method"""
        from src.cell_mes_agent import CellMesAgent

        agent = CellMesAgent()

        schedule_data = {
            "tasks": [
                {"wo_id": "WO-1", "machine_id": "EQ-1"},
                {"wo_id": "WO-2", "machine_id": "EQ-2"},
            ]
        }

        result = agent.notify_schedule_update(schedule_data)
        assert result


class TestOccupiedSlots:
    """Test occupied slots (existing schedule) functionality.

    Background: When equipment already has production results with
    start_time/end_time, these must be passed to the scheduler as
    'occupied_slots' to prevent new schedules from overlapping.
    Without this, Gantt charts showed overlapping Work Orders.
    """

    @pytest.fixture
    def mock_db_with_prod_results(self):
        """Mock DB that returns ProdResult records with time slots."""
        db = AsyncMock()

        # Create mock ProdResults with start/end times
        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

        pr1 = MagicMock()
        pr1.target_equipment_id = 1
        pr1.work_order_id = 10
        pr1.start_time = now
        pr1.end_time = now + timedelta(hours=1)  # 9:00~10:00

        pr2 = MagicMock()
        pr2.target_equipment_id = 1
        pr2.work_order_id = 11
        pr2.start_time = now + timedelta(hours=2)
        pr2.end_time = now + timedelta(hours=3)  # 11:00~12:00

        pr3 = MagicMock()
        pr3.target_equipment_id = 2
        pr3.work_order_id = 12
        pr3.start_time = now + timedelta(hours=1)
        pr3.end_time = now + timedelta(hours=2)  # 10:00~11:00

        # Mock the execute result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [pr1, pr2, pr3]
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        return db, now

    @pytest.mark.asyncio
    async def test_get_occupied_slots_returns_correct_structure(self, mock_db_with_prod_results):
        """_get_occupied_slots returns dict of equipment_id -> slot list."""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        db, now = mock_db_with_prod_results
        service = SchedulerIntegrationService(db)

        horizon_start = now
        horizon_end = now + timedelta(hours=24)

        result = await service._get_occupied_slots(
            equipment_ids=[1, 2],
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )

        # Should have entries for equipment 1 and 2
        assert 1 in result
        assert 2 in result

        # Equipment 1 has 2 slots
        assert len(result[1]) == 2

        # Equipment 2 has 1 slot
        assert len(result[2]) == 1

    @pytest.mark.asyncio
    async def test_get_occupied_slots_time_conversion(self, mock_db_with_prod_results):
        """Slots are correctly converted to seconds from horizon_start."""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        db, now = mock_db_with_prod_results
        service = SchedulerIntegrationService(db)

        horizon_start = now
        horizon_end = now + timedelta(hours=24)

        result = await service._get_occupied_slots(
            equipment_ids=[1, 2],
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )

        # Equipment 1, first slot: 9:00~10:00 → 0~3600 seconds
        slot1 = result[1][0]
        assert slot1["start"] == 0
        assert slot1["end"] == 3600
        assert slot1["wo_id"] == "WO-10"

        # Equipment 1, second slot: 11:00~12:00 → 7200~10800 seconds
        slot2 = result[1][1]
        assert slot2["start"] == 7200
        assert slot2["end"] == 10800
        assert slot2["wo_id"] == "WO-11"

        # Equipment 2, first slot: 10:00~11:00 → 3600~7200 seconds
        slot3 = result[2][0]
        assert slot3["start"] == 3600
        assert slot3["end"] == 7200
        assert slot3["wo_id"] == "WO-12"

    @pytest.mark.asyncio
    async def test_get_occupied_slots_empty_when_no_results(self):
        """No ProdResults → empty occupied slots map."""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        service = SchedulerIntegrationService(db)

        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        result = await service._get_occupied_slots(
            equipment_ids=[1, 2],
            horizon_start=now,
            horizon_end=now + timedelta(hours=24),
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_occupied_slots_clamps_negative_start(self):
        """Slots starting before horizon_start should have start clamped to 0."""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        db = AsyncMock()

        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

        # ProdResult that started 1 hour BEFORE horizon_start
        pr = MagicMock()
        pr.target_equipment_id = 1
        pr.work_order_id = 5
        pr.start_time = now - timedelta(hours=1)  # Before horizon
        pr.end_time = now + timedelta(minutes=30)  # Ends 30 min into horizon

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [pr]
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        service = SchedulerIntegrationService(db)

        result = await service._get_occupied_slots(
            equipment_ids=[1],
            horizon_start=now,
            horizon_end=now + timedelta(hours=24),
        )

        assert 1 in result
        slot = result[1][0]
        assert slot["start"] == 0  # Clamped to 0, not -3600
        assert slot["end"] == 1800  # 30 minutes in seconds


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_full_scheduling_flow(self):
        """Test complete scheduling data flow"""
        # 1. Create equipment availability data
        machines = [
            EquipmentAvailability(
                machine_id="EQ-1",
                machine_name="CNC-001",
                machine_type="CNC",
                status="AVAILABLE",
                available_from=datetime.now(timezone.utc).isoformat(),
                mes_equipment_id=1,
            ),
            EquipmentAvailability(
                machine_id="EQ-2",
                machine_name="CNC-002",
                machine_type="CNC",
                status="AVAILABLE",
                available_from=datetime.now(timezone.utc).isoformat(),
                mes_equipment_id=2,
            ),
        ]

        # 2. Create work order data - operations directly under work order
        work_orders = [
            WorkOrderForScheduling(
                wo_id="WO-1",
                product_id="PROD-1",
                product_name="Test Product",
                order_quantity=100,
                due_date=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                priority=8,
                release_date=datetime.now(timezone.utc).isoformat(),
                operations=[
                    OperationInfo(
                        op_id="OP-1",
                        op_name="Machining",
                        sequence=10,
                        required_machine_type="CNC",
                        nc_code=NcCodeInfo(
                            program_id="NC-001",
                            file_path="programs/part1.nc",
                            cycle_time_sec=60,
                        ),
                        cycle_time_sec=60,
                        process_routing_id=1,
                    ),
                ],
                mes_work_order_id=1,
                lot_no="LOT-001",
            ),
        ]

        # 3. Create scheduling request
        request = SchedulingRequest(
            request_id="REQ-001",
            request_time=datetime.now(timezone.utc).isoformat(),
            horizon_start=datetime.now(timezone.utc).isoformat(),
            horizon_end=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            machines=machines,
            work_orders=work_orders,
            machine_type_params={
                "machine_types": {
                    "CNC": {
                        "loading_type": "manual",
                        "amr_transport_qty": 1,
                    },
                },
            },
        )

        # 4. Convert to scheduler format
        scheduler_input = request.to_scheduler_format()

        # Verify structure
        assert "request" in scheduler_input
        assert "scheduling_request" in scheduler_input["request"]
        assert len(scheduler_input["machines"]) == 2
        assert len(scheduler_input["work_orders"]) == 1
        # Priority is numeric
        assert scheduler_input["work_orders"][0]["priority"] == 8

        # 5. Simulate scheduling result
        mock_scheduler_output = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": "WO-1",
                    "op_id": "OP-1",
                    "machine_id": "EQ-1",
                    "start_time": 0,
                    "end_time": 6000,  # 100 units × 60 sec
                    "quantity": 100,
                },
            ],
            "statistics": {
                "objective_value": 6000,
                "solve_time_sec": 0.5,
                "makespan_seconds": 6000,
                "machine_utilization": {"EQ-1": 6.94, "EQ-2": 0},
            },
        }

        # 6. Parse scheduling result
        result = SchedulingResult.from_scheduler_output(mock_scheduler_output)

        assert result.status == "success"
        assert len(result.scheduled_tasks) == 1
        assert result.scheduled_tasks[0].machine_id == "EQ-1"
        assert result.scheduled_tasks[0].end_time == 6000

    def test_work_order_from_dict(self):
        """Test WorkOrderForScheduling.from_dict"""
        wo_data = {
            "wo_id": "WO-1",
            "product_id": "PROD-1",
            "product_name": "Test Product",
            "order_quantity": 100,
            "due_date": "2024-01-02T17:00:00",
            "priority": 8,
            "release_date": "2024-01-01T09:00:00",
            "operations": [
                {
                    "op_id": "OP-1",
                    "op_name": "Machining",
                    "sequence": 10,
                    "required_machine_type": "CNC",
                    "setup_id": "SETUP-1",
                    "nc_code": {
                        "program_id": "NC-001",
                        "file_path": "programs/part1.nc",
                        "cycle_time_sec": 60,
                    },
                    "cycle_time_sec": 60,
                    "process_routing_id": 1,
                },
            ],
            "mes_work_order_id": 1,
            "lot_no": "LOT-001",
        }

        wo = WorkOrderForScheduling.from_dict(wo_data)

        assert wo.wo_id == "WO-1"
        assert wo.priority == 8
        assert len(wo.operations) == 1
        assert wo.operations[0].op_id == "OP-1"
        assert wo.operations[0].cycle_time_sec == 60
        assert wo.operations[0].process_routing_id == 1
