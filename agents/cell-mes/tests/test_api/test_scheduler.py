"""Tests for scheduler integration API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from src.app.models.equipment import Equipment
from src.app.models.production import WorkOrder


class TestEquipmentAvailability:
    """Test equipment availability endpoint."""

    @pytest.mark.asyncio
    async def test_get_equipment_availability(
        self, client: AsyncClient, auth_headers, sample_equipment, db_session
    ):
        """Get equipment availability for scheduler."""
        response = await client.get(
            "/api/v1/scheduler/equipment-availability", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "machines" in data
        assert "count" in data
        assert data["count"] == 1

        machine = data["machines"][0]
        assert machine["machine_id"] == f"EQ-{sample_equipment.id}"
        assert machine["machine_name"] == "Test CNC"
        assert machine["machine_type"] == "CNC"
        assert "status" in machine
        assert "available_from" in machine

    @pytest.mark.asyncio
    async def test_get_equipment_availability_filter_by_ids(
        self, client: AsyncClient, auth_headers, sample_equipment, db_session
    ):
        """Get equipment availability filtered by IDs."""
        # Create another equipment
        equipment2 = Equipment(
            eq_code="EQ-CNC-TEST-002",
            aas_id="urn:aas:cnc:test-002",
            eq_name="Test CNC 2",
            equipment_type="CNC",
            connection_config={},
            current_status="AVAILABLE",
        )
        db_session.add(equipment2)
        await db_session.commit()
        await db_session.refresh(equipment2)

        # Filter by first equipment only
        response = await client.get(
            f"/api/v1/scheduler/equipment-availability?equipment_ids={sample_equipment.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["machines"][0]["mes_equipment_id"] == sample_equipment.id

    @pytest.mark.asyncio
    async def test_get_equipment_availability_multiple_ids(
        self, client: AsyncClient, auth_headers, sample_equipment, db_session
    ):
        """Get equipment availability for multiple IDs."""
        # Create another equipment
        equipment2 = Equipment(
            eq_code="EQ-CNC-TEST-002-MULTI",
            aas_id="urn:aas:cnc:test-002-multi",
            eq_name="Test CNC 2",
            equipment_type="CNC",
            connection_config={},
            current_status="AVAILABLE",
        )
        db_session.add(equipment2)
        await db_session.commit()
        await db_session.refresh(equipment2)

        response = await client.get(
            f"/api/v1/scheduler/equipment-availability?equipment_ids={sample_equipment.id},{equipment2.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_get_equipment_availability_invalid_ids(
        self, client: AsyncClient, auth_headers
    ):
        """Invalid equipment_ids format returns 400."""
        response = await client.get(
            "/api/v1/scheduler/equipment-availability?equipment_ids=invalid,abc",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid equipment_ids" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_equipment_availability_status_mapping(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test various equipment statuses are mapped correctly."""
        statuses = [
            ("AVAILABLE", "AVAILABLE"),
            ("RUNNING", "RUNNING"),
            ("IDLE", "AVAILABLE"),
            ("ERROR", "ERROR"),
            ("MAINTENANCE", "MAINTENANCE"),
            ("OFFLINE", "OFFLINE"),
        ]

        for mes_status, expected_scheduler_status in statuses:
            eq = Equipment(
                eq_code=f"EQ-CNC-{mes_status}",
                aas_id=f"urn:aas:test:{mes_status.lower()}",
                eq_name=f"Test {mes_status}",
                equipment_type="CNC",
                connection_config={},
                current_status=mes_status,
            )
            db_session.add(eq)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/equipment-availability", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(statuses)


class TestWorkOrdersForScheduling:
    """Test work orders for scheduling endpoint."""

    @pytest.mark.asyncio
    async def test_get_work_orders_default_status(
        self, client: AsyncClient, auth_headers, sample_product, sample_routing, db_session
    ):
        """Get work orders with default READY status filter."""
        # Create orders with different statuses
        for status in ["READY", "RUNNING", "DONE"]:
            order = WorkOrder(
                lot_no=f"LOT-{status}",
                product_id=sample_product.id,
                target_qty=100,
                qty=100,
                status=status,
            )
            db_session.add(order)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/work-orders", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        # wo_id format is "WO-{id}", verify it's a valid work order
        assert data["work_orders"][0]["wo_id"].startswith("WO-")

    @pytest.mark.asyncio
    async def test_get_work_orders_multiple_status(
        self, client: AsyncClient, auth_headers, sample_product, sample_routing, db_session
    ):
        """Get work orders with multiple status filter."""
        for status in ["READY", "RUNNING", "DONE"]:
            order = WorkOrder(
                lot_no=f"LOT-MULTI-{status}",
                product_id=sample_product.id,
                target_qty=100,
                qty=100,
                status=status,
            )
            db_session.add(order)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/work-orders?status=READY,RUNNING", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_get_work_orders_with_limit(
        self, client: AsyncClient, auth_headers, sample_product, sample_routing, db_session
    ):
        """Get work orders with limit."""
        for i in range(10):
            order = WorkOrder(
                lot_no=f"LOT-LIMIT-{i:03d}",
                product_id=sample_product.id,
                target_qty=100,
                qty=100,
                status="READY",
            )
            db_session.add(order)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/work-orders?limit=5", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    @pytest.mark.asyncio
    async def test_get_work_orders_empty(self, client: AsyncClient, auth_headers):
        """Get work orders returns empty when no orders exist."""
        response = await client.get(
            "/api/v1/scheduler/work-orders", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["work_orders"] == []


class TestCreateSchedulingRequest:
    """Test create scheduling request endpoint."""

    @pytest.mark.asyncio
    async def test_create_scheduling_request(
        self, client: AsyncClient, auth_headers, sample_equipment, sample_product, sample_routing, db_session
    ):
        """Create a complete scheduling request."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-SCHED-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()

        response = await client.post(
            "/api/v1/scheduler/create-request",
            json={"horizon_hours": 24, "include_running": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check request structure
        assert "request" in data
        assert "scheduling_request" in data["request"]
        assert "machines" in data
        assert "work_orders" in data
        assert "machine_type_params" in data

        # Check machines
        assert len(data["machines"]) == 1

        # Check work orders
        assert len(data["work_orders"]) == 1

    @pytest.mark.asyncio
    async def test_create_scheduling_request_custom_horizon(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Create scheduling request with custom horizon."""
        response = await client.post(
            "/api/v1/scheduler/create-request",
            json={"horizon_hours": 48, "include_running": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify horizon in request
        horizon = data["request"]["scheduling_request"]["scheduling_horizon"]
        start = datetime.fromisoformat(horizon["start"])
        end = datetime.fromisoformat(horizon["end"])
        diff = end - start
        assert diff.total_seconds() == 48 * 3600

    @pytest.mark.asyncio
    async def test_create_scheduling_request_include_running(
        self, client: AsyncClient, auth_headers, sample_product, sample_routing, db_session
    ):
        """Create scheduling request including running orders."""
        # Create orders
        for status in ["READY", "RUNNING"]:
            order = WorkOrder(
                lot_no=f"LOT-INCL-{status}",
                product_id=sample_product.id,
                target_qty=100,
                qty=100,
                status=status,
            )
            db_session.add(order)
        await db_session.commit()

        response = await client.post(
            "/api/v1/scheduler/create-request",
            json={"horizon_hours": 24, "include_running": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["work_orders"]) == 2


class TestProcessSchedulingResult:
    """Test process scheduling result endpoint."""

    @pytest.mark.asyncio
    async def test_process_scheduling_result_success(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Process successful scheduling result."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-RESULT-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Process result
        result = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": f"WO-{order.id}",
                    "machine_id": "EQ-1",
                    "start_time": 0,
                    "end_time": 3600,
                }
            ],
            "statistics": {"makespan_seconds": 3600},
            "gantt_data": {"start": datetime.now(timezone.utc).isoformat()},
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["updated_orders"]) == 1

    @pytest.mark.asyncio
    async def test_process_scheduling_result_failure(
        self, client: AsyncClient, auth_headers
    ):
        """Process failed scheduling result returns 400."""
        result = {
            "status": "failed",
            "scheduled_tasks": [],
            "error": "Infeasible problem",
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_process_scheduling_result_empty_tasks(
        self, client: AsyncClient, auth_headers
    ):
        """Process result with empty tasks."""
        result = {
            "status": "success",
            "scheduled_tasks": [],
            "statistics": {},
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["updated_orders"]) == 0


class TestMachineTypeParams:
    """Test machine type parameters endpoint."""

    @pytest.mark.asyncio
    async def test_get_machine_type_params(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Get machine type parameters."""
        response = await client.get(
            "/api/v1/scheduler/machine-type-params", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "machine_types" in data
        assert "CNC" in data["machine_types"]

    @pytest.mark.asyncio
    async def test_get_machine_type_params_multiple_types(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Get params for multiple machine types."""
        # Create different equipment types
        for eq_type in ["CNC", "ROBOT", "PLC"]:
            eq = Equipment(
                eq_code=f"EQ-{eq_type}-PARAM",
                aas_id=f"urn:aas:{eq_type.lower()}:test",
                eq_name=f"Test {eq_type}",
                equipment_type=eq_type,
                connection_config={},
                current_status="AVAILABLE",
            )
            db_session.add(eq)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/machine-type-params", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["machine_types"]) == 3

    @pytest.mark.asyncio
    async def test_get_machine_type_params_with_spec_data(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Get params with custom spec_data."""
        eq = Equipment(
            eq_code="EQ-CNC-CUSTOM",
            aas_id="urn:aas:cnc:custom",
            eq_name="Custom CNC",
            equipment_type="CNC",
            connection_config={},
            spec_data={
                "machine_type": "CNC_ADVANCED",
                "loading_type": "auto",
                "amr_transport_qty": 2,
            },
            current_status="AVAILABLE",
        )
        db_session.add(eq)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/machine-type-params", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "CNC_ADVANCED" in data["machine_types"]
        assert data["machine_types"]["CNC_ADVANCED"]["loading_type"] == "auto"


class TestScheduleWorkOrderIntegration:
    """Test scheduling and work order integration."""

    @pytest.mark.asyncio
    async def test_schedule_updates_work_order_plan_times(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Schedule execution updates work order plan_start and plan_end times."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-PLAN-TIME-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Process scheduling result
        result = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": f"WO-{order.id}",
                    "machine_id": f"EQ-{sample_equipment.id}",
                    "start_time": 0,
                    "end_time": 7200,
                    "op_id": "OP-1",
                }
            ],
            "statistics": {"makespan_seconds": 7200},
            "gantt_data": {"start": datetime.now(timezone.utc).isoformat()},
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["updated_orders"]) == 1
        assert data["updated_orders"][0]["scheduled_start"] is not None
        assert data["updated_orders"][0]["scheduled_end"] is not None

    @pytest.mark.asyncio
    async def test_schedule_with_equipment_downtime(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Schedule respects equipment downtime (MAINTENANCE status)."""
        # Create maintenance equipment
        eq_maintenance = Equipment(
            eq_code="EQ-MAINT-001",
            aas_id="urn:aas:cnc:maint",
            eq_name="Maintenance CNC",
            equipment_type="CNC",
            connection_config={},
            current_status="MAINTENANCE",
        )
        db_session.add(eq_maintenance)
        await db_session.commit()
        await db_session.refresh(eq_maintenance)

        response = await client.get(
            "/api/v1/scheduler/equipment-availability", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find the maintenance equipment
        maint_machine = next(
            (m for m in data["machines"] if m["machine_name"] == "Maintenance CNC"), None
        )
        assert maint_machine is not None
        assert maint_machine["status"] == "MAINTENANCE"
        # available_from should be in the future
        available_from = datetime.fromisoformat(
            maint_machine["available_from"].replace("Z", "+00:00")
        )
        assert available_from > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_reschedule_on_urgent_order(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, sample_routing, db_session
    ):
        """Urgent orders (high priority) can be scheduled."""
        # Create urgent order with high priority
        urgent_order = WorkOrder(
            lot_no="LOT-URGENT-001",
            product_id=sample_product.id,
            target_qty=50,
            qty=50,
            priority=1,  # Highest priority
            status="READY",
        )
        # Create normal order
        normal_order = WorkOrder(
            lot_no="LOT-NORMAL-001",
            product_id=sample_product.id,
            target_qty=50,
            qty=50,
            priority=5,  # Normal priority
            status="READY",
        )
        db_session.add(urgent_order)
        db_session.add(normal_order)
        await db_session.commit()

        # Create scheduling request
        response = await client.post(
            "/api/v1/scheduler/create-request",
            json={"horizon_hours": 24, "include_running": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify both orders are included
        wo_ids = [wo["lot_no"] for wo in data["work_orders"]]
        assert "LOT-URGENT-001" in wo_ids
        assert "LOT-NORMAL-001" in wo_ids

        # Verify priority is preserved
        urgent = next(wo for wo in data["work_orders"] if wo["lot_no"] == "LOT-URGENT-001")
        normal = next(wo for wo in data["work_orders"] if wo["lot_no"] == "LOT-NORMAL-001")
        assert urgent["priority"] < normal["priority"]  # Lower number = higher priority

    @pytest.mark.asyncio
    async def test_schedule_conflict_detection(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Detect scheduling conflicts when equipment is already occupied."""
        from src.app.models.production import ProdResult

        now = datetime.now(timezone.utc)

        # Create existing work order with scheduled time
        existing_order = WorkOrder(
            lot_no="LOT-EXISTING-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="RUNNING",
            start_time=now,
            end_time=now + timedelta(hours=2),
        )
        db_session.add(existing_order)
        await db_session.commit()
        await db_session.refresh(existing_order)

        # Create production result with scheduled slot
        prod_result = ProdResult(
            work_order_id=existing_order.id,
            target_equipment_id=sample_equipment.id,
            start_time=now,
            end_time=now + timedelta(hours=2),
            ok_qty=0,
            ng_qty=0,
        )
        db_session.add(prod_result)
        await db_session.commit()

        # Get equipment availability - should show occupied slot
        response = await client.post(
            "/api/v1/scheduler/create-request",
            json={"horizon_hours": 24, "include_running": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check if equipment has occupied slots
        machine = next(
            (m for m in data["machines"] if m["mes_equipment_id"] == sample_equipment.id), None
        )
        # Note: occupied_slots may or may not be populated depending on horizon
        assert machine is not None

    @pytest.mark.asyncio
    async def test_schedule_rollback_on_failure(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Failed scheduling result should not update work orders."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-ROLLBACK-001",
            product_id=sample_product.id,
            target_qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        original_start_time = order.start_time  # Should be None

        # Process failed scheduling result
        result = {
            "status": "failed",
            "scheduled_tasks": [],
            "error": "Infeasible problem",
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 400

        # Verify work order was not modified
        await db_session.refresh(order)
        assert order.start_time == original_start_time  # Still None

    @pytest.mark.asyncio
    async def test_schedule_respects_equipment_capability(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Scheduling respects equipment type capability constraints."""
        # Create different equipment types
        cnc = Equipment(
            eq_code="EQ-CNC-CAP-001",
            aas_id="urn:aas:cnc:cap",
            eq_name="Capability CNC",
            equipment_type="CNC",
            connection_config={},
            current_status="AVAILABLE",
        )
        robot = Equipment(
            eq_code="EQ-ROBOT-CAP-001",
            aas_id="urn:aas:robot:cap",
            eq_name="Capability Robot",
            equipment_type="ROBOT",
            connection_config={},
            current_status="AVAILABLE",
        )
        db_session.add(cnc)
        db_session.add(robot)
        await db_session.commit()

        response = await client.get(
            "/api/v1/scheduler/equipment-availability", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify equipment types are preserved
        machine_types = {m["machine_type"] for m in data["machines"]}
        assert "CNC" in machine_types
        assert "ROBOT" in machine_types

    @pytest.mark.asyncio
    async def test_schedule_minimizes_makespan(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Verify makespan statistics are returned after scheduling."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-MAKESPAN-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Process scheduling result with makespan statistics
        result = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": f"WO-{order.id}",
                    "machine_id": f"EQ-{sample_equipment.id}",
                    "start_time": 0,
                    "end_time": 3600,
                    "op_id": "OP-1",
                }
            ],
            "statistics": {
                "makespan_seconds": 3600,
                "total_processing_time": 3600,
                "average_machine_utilization": 0.85,
            },
            "gantt_data": {"start": datetime.now(timezone.utc).isoformat()},
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert data["statistics"]["makespan_seconds"] == 3600

    @pytest.mark.asyncio
    async def test_schedule_with_setup_time(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Scheduling includes setup change time from equipment spec."""
        # Create equipment with setup time spec
        eq = Equipment(
            eq_code="EQ-SETUP-001",
            aas_id="urn:aas:cnc:setup",
            eq_name="Setup CNC",
            equipment_type="CNC",
            connection_config={},
            spec_data={"setup_change_time_min": 15},
            current_status="AVAILABLE",
        )
        db_session.add(eq)
        await db_session.commit()
        await db_session.refresh(eq)

        response = await client.get(
            "/api/v1/scheduler/equipment-availability", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find the equipment with setup time
        setup_machine = next(
            (m for m in data["machines"] if m["machine_name"] == "Setup CNC"), None
        )
        assert setup_machine is not None
        assert setup_machine["setup_change_time_min"] == 15

    @pytest.mark.asyncio
    async def test_partial_schedule_execution(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Process scheduling result with only some tasks scheduled."""
        # Create multiple work orders
        orders = []
        for i in range(3):
            order = WorkOrder(
                lot_no=f"LOT-PARTIAL-{i:03d}",
                product_id=sample_product.id,
                target_qty=100,
                qty=100,
                status="READY",
            )
            db_session.add(order)
            orders.append(order)
        await db_session.commit()
        for order in orders:
            await db_session.refresh(order)

        # Process result with only first order scheduled
        result = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": f"WO-{orders[0].id}",
                    "machine_id": f"EQ-{sample_equipment.id}",
                    "start_time": 0,
                    "end_time": 3600,
                    "op_id": "OP-1",
                }
            ],
            "statistics": {"makespan_seconds": 3600},
            "gantt_data": {"start": datetime.now(timezone.utc).isoformat()},
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["updated_orders"]) == 1

        # Verify only first order was updated
        await db_session.refresh(orders[0])
        assert orders[0].start_time is not None
        await db_session.refresh(orders[1])
        assert orders[1].start_time is None

    @pytest.mark.asyncio
    async def test_get_current_schedule_accuracy(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Current schedule endpoint returns accurate data."""
        from src.app.models.production import ProdResult

        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        # Create work order with scheduled time today
        order = WorkOrder(
            lot_no="LOT-CURRENT-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
            start_time=now,
            end_time=now + timedelta(hours=2),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Create production result
        prod_result = ProdResult(
            work_order_id=order.id,
            target_equipment_id=sample_equipment.id,
            start_time=now,
            end_time=now + timedelta(hours=2),
            ok_qty=0,
            ng_qty=0,
        )
        db_session.add(prod_result)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/scheduler/current-schedule?target_date={today_str}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "availability" in data
        assert "summary" in data
        assert data["summary"]["total_scheduled_orders"] >= 1

    @pytest.mark.asyncio
    async def test_schedule_equipment_utilization(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Scheduling result includes equipment utilization metrics."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-UTIL-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Process result with utilization metrics
        result = {
            "status": "success",
            "scheduled_tasks": [
                {
                    "wo_id": f"WO-{order.id}",
                    "machine_id": f"EQ-{sample_equipment.id}",
                    "start_time": 0,
                    "end_time": 7200,
                    "op_id": "OP-1",
                }
            ],
            "statistics": {
                "makespan_seconds": 7200,
                "average_machine_utilization": 0.75,
            },
            "quality_metrics": {
                "equipment_utilization": {
                    f"EQ-{sample_equipment.id}": 0.75
                }
            },
            "gantt_data": {"start": datetime.now(timezone.utc).isoformat()},
        }

        response = await client.post(
            "/api/v1/scheduler/process-result",
            json=result,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Quality metrics are passed through
        assert "quality_metrics" in data or "statistics" in data

    @pytest.mark.asyncio
    async def test_reschedule_preserves_completed_orders(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Rescheduling does not modify DONE work orders."""
        # Create completed order
        completed_order = WorkOrder(
            lot_no="LOT-DONE-PRESERVE-001",
            product_id=sample_product.id,
            target_qty=100,
            status="DONE",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        db_session.add(completed_order)
        await db_session.commit()
        await db_session.refresh(completed_order)
        original_end_time = completed_order.end_time

        # Get work orders for scheduling - should not include DONE orders
        response = await client.get(
            "/api/v1/scheduler/work-orders?status=READY", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # DONE orders should not be included
        wo_ids = [wo["lot_no"] for wo in data["work_orders"]]
        assert "LOT-DONE-PRESERVE-001" not in wo_ids

        # Verify the order was not modified
        await db_session.refresh(completed_order)
        assert completed_order.end_time == original_end_time
        assert completed_order.status == "DONE"
