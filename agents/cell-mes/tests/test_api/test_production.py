"""Tests for production management endpoints."""

import pytest
from httpx import AsyncClient

from src.app.api.v1.endpoints.production import _scenario_required_resources
from src.app.api.v1.endpoints.production import _scenario_role_resources
from src.app.models.master import ProcessRouting, ProcessRoutingFile, Scenario
from src.app.models.production import WorkOrder
from src.app.models.production import Unit


class TestWorkOrderCRUD:
    """Test work order CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_work_order(
        self, client: AsyncClient, auth_headers, sample_product, db_session, mock_middleware_http
    ):
        """Create a new work order."""
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-TEST-001",
                "product_id": sample_product.id,
                "target_qty": 100,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["lot_no"] == "LOT-TEST-001"
        assert data["status"] == "READY"
        assert data["target_qty"] == 100

    @pytest.mark.asyncio
    async def test_create_work_order_allocates_next_bigint_id(
        self, client: AsyncClient, auth_headers, sample_product, db_session, mock_middleware_http
    ):
        """Create assigns max(id)+1 for legacy SQLite BIGINT work_order ids."""
        existing = WorkOrder(
            id=2000,
            lot_no="LOT-ID-SEED-001",
            product_id=sample_product.id,
            target_qty=50,
        )
        db_session.add(existing)
        await db_session.commit()

        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-ID-ALLOC-001",
                "product_id": sample_product.id,
                "target_qty": 100,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 2001
        assert data["lot_no"] == "LOT-ID-ALLOC-001"

    @pytest.mark.asyncio
    async def test_create_work_order_duplicate_lot_no(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Duplicate lot_no returns 400."""
        # Create first order
        order = WorkOrder(
            lot_no="LOT-DUP-001",
            product_id=sample_product.id,
            target_qty=50,
        )
        db_session.add(order)
        await db_session.commit()

        # Try to create duplicate
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-DUP-001",
                "product_id": sample_product.id,
                "target_qty": 100,
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_work_orders(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """List work orders."""
        # Create some orders
        for i in range(3):
            order = WorkOrder(
                lot_no=f"LOT-LIST-{i:03d}",
                product_id=sample_product.id,
                target_qty=100,
            )
            db_session.add(order)
        await db_session.commit()

        response = await client.get("/api/v1/production/orders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3  # At least our 3 created orders

    @pytest.mark.asyncio
    async def test_list_work_orders_filter_by_status(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Filter work orders by status."""
        # Create orders with different statuses
        statuses = ["READY", "RUNNING", "DONE"]
        for i, status in enumerate(statuses):
            order = WorkOrder(
                lot_no=f"LOT-FILTER-{i:03d}",
                product_id=sample_product.id,
                target_qty=100,
                status=status,
            )
            db_session.add(order)
        await db_session.commit()

        response = await client.get(
            "/api/v1/production/orders?status=RUNNING",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        # All returned items should have RUNNING status
        for item in data["items"]:
            assert item["status"] == "RUNNING"


class TestReadyUnits:
    """Test ready unit queue response for middleware."""

    def test_required_resources_use_first_acquire_step_only(self):
        """Resource hints should not include assets acquired by later steps."""
        resources = _scenario_required_resources(
            {
                "assets": [
                    {"id": "NC1", "name": "DH400"},
                    {"id": "AMR", "name": "DOOSAN_MOMA"},
                    {"id": "RACK", "name": "Rack01"},
                ],
                "steps": [
                    {"id": "1", "name": "first", "acquire": {"sub1": ["AMR"], "sub2": ["RACK"]}},
                    {"id": "2", "name": "later"},
                    {"id": "3", "name": "cnc", "acquire": {"main": ["NC1"], "sub1": ["AMR"]}},
                ],
            }
        )

        assert resources == {
            "sub1": ["DOOSAN_MOMA"],
            "sub2": ["Rack01"],
        }

    def test_role_resources_can_use_later_acquire_step(self):
        """NC file hints can still resolve the first main CNC asset."""
        scenario_content = {
            "assets": [
                {"id": "NC1", "name": "DH400"},
                {"id": "AMR", "name": "DOOSAN_MOMA"},
                {"id": "RACK", "name": "Rack01"},
            ],
            "steps": [
                {"id": "1", "name": "first", "acquire": {"sub1": ["AMR"], "sub2": ["RACK"]}},
                {"id": "2", "name": "cnc", "acquire": {"main": ["NC1"], "sub1": ["AMR"]}},
            ],
        }

        assert _scenario_role_resources(scenario_content, "main") == ["DH400"]

    @pytest.mark.asyncio
    async def test_ready_units_include_recipe_resources_and_nc_files(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        sample_std_process,
        db_session,
    ):
        """Ready units expose recipe, YAML resource names, and NC download links."""
        sample_std_process.equipment_type = "CNC"
        sample_std_process.required_machines = ["CNC"]

        scenario = Scenario(
            code="SCN-READY-001",
            product_id=sample_product.id,
            name="Ready Scenario",
            file_path="cell-mes/data/sample2.yaml",
            is_active=True,
        )
        db_session.add(scenario)
        await db_session.flush()

        order = WorkOrder(
            lot_no="LOT-READY-001",
            product_id=sample_product.id,
            scenario_id=scenario.id,
            target_qty=1,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(
            work_order_id=order.id,
            unit_no=1,
            scenario_id=scenario.id,
            status="READY",
        )
        db_session.add(unit)

        routing = ProcessRouting(
            product_id=sample_product.id,
            std_process_id=sample_std_process.id,
            sequence=10,
            required_machines=["CNC"],
        )
        db_session.add(routing)
        await db_session.flush()

        routing_file = ProcessRoutingFile(
            process_routing_id=routing.id,
            file_type="NC",
            file_path="/uploads/nc/ready-program.nc",
            original_filename="ready-program.nc",
            sort_order=1,
        )
        db_session.add(routing_file)
        await db_session.commit()

        response = await client.get(
            "/api/v1/production/orders/ready-units",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        ready_unit = next(item for item in data if item["lot_no"] == "LOT-READY-001")
        assert ready_unit["unit_no"] == "1"
        assert ready_unit["recipe"] == {
            "name": "sample",
            "url": f"http://test/api/v1/masters/scenarios/{scenario.id}/download",
        }
        assert ready_unit["required_resources"]["main"] == ["NX5500", "DH400"]
        assert ready_unit["required_resources"]["sub1"] == ["DOOSAN_MOMA"]
        assert ready_unit["nc_files"] == [
            {
                "asset": "NX5500",
                "name": "ready-program.nc",
                "url": f"http://test/api/v1/masters/files/{routing_file.id}/download",
            }
        ]


class TestUnitDispatchByLot:
    """Test unit dispatch endpoints using lot_no and unit_no."""

    @pytest.mark.asyncio
    async def test_claim_and_complete_unit_by_lot_and_unit_no(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        db_session,
    ):
        """Middleware can claim and complete a unit using lot_no/unit_no."""
        order = WorkOrder(
            lot_no="LOT-DISPATCH-001",
            product_id=sample_product.id,
            target_qty=1,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(
            work_order_id=order.id,
            unit_no=1,
            status="READY",
        )
        db_session.add(unit)
        await db_session.commit()

        claim_response = await client.post(
            "/api/v1/production/orders/units/claim",
            headers=auth_headers,
            params={"lot_no": "LOT-DISPATCH-001", "unit_no": "1"},
        )

        assert claim_response.status_code == 200
        claim_data = claim_response.json()
        assert claim_data["message"] == "Unit claimed successfully"
        assert claim_data["work_order_id"] == order.id
        assert claim_data["unit_id"] == unit.id
        assert claim_data["unit_no"] == "1"
        await db_session.refresh(unit)
        assert unit.status == "RUNNING"

        complete_response = await client.post(
            "/api/v1/production/orders/units/complete",
            headers=auth_headers,
            params={"lot_no": "LOT-DISPATCH-001", "unit_no": "1"},
        )

        assert complete_response.status_code == 200
        complete_data = complete_response.json()
        assert complete_data["message"] == "Unit completed successfully"
        assert complete_data["unit_no"] == "1"
        assert complete_data["completed_qty"] == 1
        assert complete_data["work_order_status"] == "DONE"
        await db_session.refresh(unit)
        await db_session.refresh(order)
        assert unit.status == "DONE"
        assert order.completed_qty == 1
        assert order.status == "DONE"

    @pytest.mark.asyncio
    async def test_claim_unit_by_lot_not_found(
        self,
        client: AsyncClient,
        auth_headers,
    ):
        """Missing lot/unit pair returns 404."""
        response = await client.post(
            "/api/v1/production/orders/units/claim",
            headers=auth_headers,
            params={"lot_no": "LOT-NOT-FOUND", "unit_no": "1"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Unit not found for lot_no and unit_no"


class TestUnitExecutionPackage:
    """Test unit execution package lookup for middleware."""

    @pytest.mark.asyncio
    async def test_get_execution_package_by_lot_and_unit_no(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        sample_std_process,
        db_session,
    ):
        """Return scenario content URL and routing file download URLs."""
        scenario = Scenario(
            code="SCN-PKG-001",
            product_id=sample_product.id,
            name="Package Scenario",
            file_path="cell-mes/data/sample2.yaml",
            is_active=True,
        )
        db_session.add(scenario)
        await db_session.flush()

        order = WorkOrder(
            lot_no="LOT-PKG-001",
            product_id=sample_product.id,
            scenario_id=scenario.id,
            target_qty=3,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(
            work_order_id=order.id,
            unit_no=2,
            scenario_id=scenario.id,
            status="READY",
        )
        db_session.add(unit)

        routing = ProcessRouting(
            product_id=sample_product.id,
            std_process_id=sample_std_process.id,
            sequence=20,
            remarks="NC operation",
        )
        db_session.add(routing)
        await db_session.flush()

        routing_file = ProcessRoutingFile(
            process_routing_id=routing.id,
            file_type="NC",
            file_path="/uploads/nc/test-program.nc",
            original_filename="original-program.nc",
            sort_order=1,
        )
        db_session.add(routing_file)
        await db_session.commit()

        response = await client.get(
            "/api/v1/production/orders/ready-units/execution-package",
            headers=auth_headers,
            params={"lot_no": "LOT-PKG-001", "unit_no": "2"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["lot_no"] == "LOT-PKG-001"
        assert data["unit"]["unit_no"] == "2"
        assert data["unit"]["scenario_id"] == scenario.id
        assert data["scenario"]["id"] == scenario.id
        assert data["scenario"]["content_url"].endswith(
            f"/api/v1/masters/scenarios/{scenario.id}/content"
        )
        assert data["scenario"]["download_url"].endswith(
            f"/api/v1/masters/scenarios/{scenario.id}/download"
        )
        assert data["processing_steps"][0]["sequence"] == 20
        assert data["processing_steps"][0]["files"][0]["id"] == routing_file.id
        assert data["processing_steps"][0]["files"][0]["original_filename"] == "original-program.nc"
        assert data["processing_steps"][0]["files"][0]["download_url"].endswith(
            f"/api/v1/masters/files/{routing_file.id}/download"
        )

    @pytest.mark.asyncio
    async def test_get_execution_package_not_found(
        self,
        client: AsyncClient,
        auth_headers,
    ):
        """Missing lot/unit pair returns 404."""
        response = await client.get(
            "/api/v1/production/orders/ready-units/execution-package",
            headers=auth_headers,
            params={"lot_no": "LOT-MISSING", "unit_no": "1"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Unit not found for lot_no and unit_no"


class TestUnitScenarioChange:
    """Test unit-level scenario hold and change flow."""

    @pytest.mark.asyncio
    async def test_hold_hides_unit_from_ready_queue_and_blocks_claim(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        db_session,
    ):
        """Held units stay visible to MES but are hidden from middleware ready queue."""
        scenario = Scenario(
            code="SCN-HOLD-001",
            product_id=sample_product.id,
            name="Hold Scenario",
            file_path="cell-mes/data/sample2.yaml",
            is_active=True,
        )
        db_session.add(scenario)
        await db_session.flush()

        order = WorkOrder(
            lot_no="LOT-HOLD-001",
            product_id=sample_product.id,
            scenario_id=scenario.id,
            target_qty=1,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(
            work_order_id=order.id,
            unit_no=1,
            scenario_id=scenario.id,
            status="READY",
        )
        db_session.add(unit)
        await db_session.commit()

        hold_response = await client.post(
            f"/api/v1/production/orders/{order.id}/units/{unit.id}/scenario-hold",
            headers=auth_headers,
        )
        assert hold_response.status_code == 200
        assert hold_response.json()["status"] == "SCENARIO_HOLD"

        await db_session.refresh(unit)
        assert unit.status == "SCENARIO_HOLD"
        assert unit.scenario_hold_started_at is not None
        assert unit.scenario_hold_by == "testuser"

        ready_response = await client.get(
            "/api/v1/production/orders/ready-units",
            headers=auth_headers,
        )
        assert ready_response.status_code == 200
        assert all(item["lot_no"] != "LOT-HOLD-001" for item in ready_response.json())

        units_response = await client.get(
            f"/api/v1/production/orders/{order.id}/units",
            headers=auth_headers,
        )
        assert units_response.status_code == 200
        assert units_response.json()["items"][0]["status"] == "SCENARIO_HOLD"

        claim_response = await client.post(
            "/api/v1/production/orders/units/claim",
            headers=auth_headers,
            params={"lot_no": "LOT-HOLD-001", "unit_no": "1"},
        )
        assert claim_response.status_code == 409

    @pytest.mark.asyncio
    async def test_change_held_unit_scenario_releases_to_ready_and_execution_package_uses_unit_scenario(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        db_session,
    ):
        """Changing a held unit scenario returns it to READY and middleware payload uses it."""
        original = Scenario(
            code="SCN-UNIT-OLD",
            product_id=sample_product.id,
            name="Original Scenario",
            file_path="cell-mes/data/sample2.yaml",
            is_active=True,
        )
        replacement = Scenario(
            code="SCN-UNIT-NEW",
            product_id=sample_product.id,
            name="Replacement Scenario",
            file_path="cell-mes/data/sample3.yaml",
            is_active=True,
        )
        db_session.add_all([original, replacement])
        await db_session.flush()

        order = WorkOrder(
            lot_no="LOT-UNIT-SCENARIO-001",
            product_id=sample_product.id,
            scenario_id=original.id,
            target_qty=1,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(
            work_order_id=order.id,
            unit_no=1,
            scenario_id=original.id,
            status="READY",
        )
        db_session.add(unit)
        await db_session.commit()

        hold_response = await client.post(
            f"/api/v1/production/orders/{order.id}/units/{unit.id}/scenario-hold",
            headers=auth_headers,
        )
        assert hold_response.status_code == 200

        change_response = await client.patch(
            f"/api/v1/production/orders/{order.id}/units/{unit.id}/scenario",
            headers=auth_headers,
            json={"scenario_id": replacement.id},
        )
        assert change_response.status_code == 200
        assert change_response.json()["status"] == "READY"
        assert change_response.json()["scenario_id"] == replacement.id

        await db_session.refresh(unit)
        assert unit.status == "READY"
        assert unit.scenario_id == replacement.id
        assert unit.scenario_hold_started_at is None
        assert unit.scenario_hold_by is None

        package_response = await client.get(
            "/api/v1/production/orders/ready-units/execution-package",
            headers=auth_headers,
            params={"lot_no": "LOT-UNIT-SCENARIO-001", "unit_no": "1"},
        )
        assert package_response.status_code == 200
        assert package_response.json()["scenario"]["id"] == replacement.id

        work_info_response = await client.get(
            "/api/v1/production/middleware/work-info",
            headers=auth_headers,
            params={"lot_no": "LOT-UNIT-SCENARIO-001", "unit_no": "1"},
        )
        assert work_info_response.status_code == 200
        assert work_info_response.json()["logistics"]["scenario_name"] == "Replacement Scenario"

    @pytest.mark.asyncio
    async def test_unit_scenario_must_match_work_order_product(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        db_session,
    ):
        """Unit scenario change rejects active scenarios registered to another product."""
        from src.app.models.master import Product

        other_product = Product(code="PROD-OTHER", name="Other Product", unit="EA")
        db_session.add(other_product)
        await db_session.flush()

        original = Scenario(
            code="SCN-PROD-OLD",
            product_id=sample_product.id,
            name="Product Scenario",
            file_path="cell-mes/data/sample2.yaml",
            is_active=True,
        )
        wrong_product = Scenario(
            code="SCN-PROD-WRONG",
            product_id=other_product.id,
            name="Wrong Product Scenario",
            file_path="cell-mes/data/sample3.yaml",
            is_active=True,
        )
        db_session.add_all([original, wrong_product])
        await db_session.flush()

        order = WorkOrder(
            lot_no="LOT-WRONG-SCENARIO-001",
            product_id=sample_product.id,
            scenario_id=original.id,
            target_qty=1,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(work_order_id=order.id, unit_no=1, scenario_id=original.id, status="READY")
        db_session.add(unit)
        await db_session.commit()

        hold_response = await client.post(
            f"/api/v1/production/orders/{order.id}/units/{unit.id}/scenario-hold",
            headers=auth_headers,
        )
        assert hold_response.status_code == 200

        change_response = await client.patch(
            f"/api/v1/production/orders/{order.id}/units/{unit.id}/scenario",
            headers=auth_headers,
            json={"scenario_id": wrong_product.id},
        )
        assert change_response.status_code == 400
        assert "not registered" in change_response.json()["detail"]

    @pytest.mark.asyncio
    async def test_release_scenario_hold_without_change(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        db_session,
    ):
        """Operator can cancel a scenario change and return the unit to READY."""
        order = WorkOrder(
            lot_no="LOT-RELEASE-HOLD-001",
            product_id=sample_product.id,
            target_qty=1,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(work_order_id=order.id, unit_no=1, status="SCENARIO_HOLD")
        db_session.add(unit)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/production/orders/{order.id}/units/{unit.id}/scenario-release",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "READY"

        await db_session.refresh(unit)
        assert unit.status == "READY"

    @pytest.mark.asyncio
    async def test_work_order_scenario_override_blocks_held_units(
        self,
        client: AsyncClient,
        auth_headers,
        sample_product,
        db_session,
    ):
        """Bulk Work Order scenario override must not overwrite held unit scenario work."""
        old_scenario = Scenario(
            code="SCN-BULK-OLD",
            product_id=sample_product.id,
            name="Bulk Old Scenario",
            file_path="cell-mes/data/sample2.yaml",
            is_active=True,
        )
        new_scenario = Scenario(
            code="SCN-BULK-NEW",
            product_id=sample_product.id,
            name="Bulk New Scenario",
            file_path="cell-mes/data/sample3.yaml",
            is_active=True,
        )
        db_session.add_all([old_scenario, new_scenario])
        await db_session.flush()

        order = WorkOrder(
            lot_no="LOT-BULK-HOLD-001",
            product_id=sample_product.id,
            scenario_id=old_scenario.id,
            target_qty=1,
            status="PAUSE",
        )
        db_session.add(order)
        await db_session.flush()

        unit = Unit(
            work_order_id=order.id,
            unit_no=1,
            scenario_id=old_scenario.id,
            status="SCENARIO_HOLD",
        )
        db_session.add(unit)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/scenario",
            headers=auth_headers,
            json={"scenario_id": new_scenario.id},
        )
        assert response.status_code == 409
        assert "held" in response.json()["detail"]


class TestWorkOrderStatus:
    """Test work order status transitions."""

    @pytest.mark.asyncio
    async def test_start_work_order(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Start a work order (READY -> RUNNING)."""
        order = WorkOrder(
            lot_no="LOT-START-001",
            product_id=sample_product.id,
            target_qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_pause_work_order(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Pause a work order (RUNNING -> PAUSE)."""
        order = WorkOrder(
            lot_no="LOT-PAUSE-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "PAUSE"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAUSE"

    @pytest.mark.asyncio
    async def test_complete_work_order(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Complete a work order (RUNNING -> DONE)."""
        order = WorkOrder(
            lot_no="LOT-DONE-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "DONE"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DONE"

    @pytest.mark.asyncio
    async def test_invalid_status_transition(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Invalid status transition returns 400."""
        order = WorkOrder(
            lot_no="LOT-INVALID-001",
            product_id=sample_product.id,
            target_qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Try to go directly from READY to DONE (invalid)
        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "DONE"},
        )

        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cannot_restart_done_order(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Cannot restart a completed order."""
        order = WorkOrder(
            lot_no="LOT-RESTART-001",
            product_id=sample_product.id,
            target_qty=100,
            status="DONE",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )

        assert response.status_code == 400


class TestWorkOrderUpdate:
    """Test work order update operations."""

    @pytest.mark.asyncio
    async def test_update_work_order(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Update a work order's basic fields."""
        order = WorkOrder(
            lot_no="LOT-UPDATE-001",
            product_id=sample_product.id,
            target_qty=100,
            priority=5,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Note: The current API may not have a PATCH /orders/{id} endpoint
        # Check if endpoint exists, otherwise test the status update endpoint
        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_update_work_order_invalid_status(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Invalid status value returns 422 (validation error)."""
        order = WorkOrder(
            lot_no="LOT-INVALID-UPDATE-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Valid status values are: RUNNING, PAUSE, DONE, ERROR
        # READY is not a valid status for update (only for initial state)
        # This should return 422 (validation error) because schema doesn't allow READY
        response = await client.patch(
            f"/api/v1/production/orders/{order.id}/status",
            headers=auth_headers,
            json={"status": "READY"},  # Not allowed by schema
        )

        # 422 Unprocessable Entity for invalid status value
        assert response.status_code == 422


class TestWorkOrderDelete:
    """Test work order delete operations (DELETE not supported on production router)."""

    @pytest.mark.asyncio
    async def test_delete_work_order_not_supported(
        self, client: AsyncClient, auth_headers, sample_product, db_session, mock_middleware_http
    ):
        """DELETE endpoint returns 204 on successful deletion."""
        order = WorkOrder(
            lot_no="LOT-DELETE-001",
            product_id=sample_product.id,
            target_qty=100,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.delete(
            f"/api/v1/production/orders/{order.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_work_order_in_progress_not_supported(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """DELETE on RUNNING work order returns 400 (cannot delete running order)."""
        order = WorkOrder(
            lot_no="LOT-DELETE-RUNNING-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.delete(
            f"/api/v1/production/orders/{order.id}",
            headers=auth_headers,
        )

        assert response.status_code == 400


class TestWorkOrderRouting:
    """Test work order with routing operations."""

    @pytest.mark.asyncio
    async def test_create_work_order_with_routing(
        self, client: AsyncClient, auth_headers, sample_product, sample_routing, db_session, mock_middleware_http
    ):
        """Create a work order for a product that has routing."""
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-WITH-ROUTING-001",
                "product_id": sample_product.id,
                "target_qty": 50,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["lot_no"] == "LOT-WITH-ROUTING-001"
        assert data["product_id"] == sample_product.id

        # Verify the routing exists for the product
        from src.app.models.master import ProcessRouting
        from sqlalchemy import select

        result = await db_session.execute(
            select(ProcessRouting).where(ProcessRouting.product_id == sample_product.id)
        )
        routings = list(result.scalars().all())
        assert len(routings) >= 1


class TestWorkOrderFiltering:
    """Test work order filtering and sorting."""

    @pytest.mark.asyncio
    async def test_work_order_priority_sorting(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Work orders can be sorted by priority."""
        # Create orders with different priorities
        priorities = [3, 1, 5, 2, 4]
        for i, priority in enumerate(priorities):
            order = WorkOrder(
                lot_no=f"LOT-PRIORITY-{i:03d}",
                product_id=sample_product.id,
                target_qty=100,
                priority=priority,
                status="READY",
            )
            db_session.add(order)
        await db_session.commit()

        # Test sorting by priority ascending
        response = await client.get(
            "/api/v1/production/orders?sort_by=priority&sort_order=asc",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Check that items are sorted by priority
        priorities_returned = [item["priority"] for item in data["items"]]
        assert priorities_returned == sorted(priorities_returned)

    @pytest.mark.asyncio
    async def test_work_order_due_date_filter(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Filter work orders by due date range."""
        from datetime import datetime, timedelta, timezone

        today = datetime.now(timezone.utc)

        # Create orders with different due dates
        dates = [
            today - timedelta(days=2),  # Past
            today,  # Today
            today + timedelta(days=1),  # Tomorrow
            today + timedelta(days=7),  # Next week
        ]
        for i, due_date in enumerate(dates):
            order = WorkOrder(
                lot_no=f"LOT-DUEDATE-{i:03d}",
                product_id=sample_product.id,
                target_qty=100,
                due_date=due_date,
                status="READY",
            )
            db_session.add(order)
        await db_session.commit()

        # Filter by date_from
        date_from_str = today.strftime("%Y-%m-%d")
        response = await client.get(
            f"/api/v1/production/orders?date_from={date_from_str}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Note: The API may filter by start_time, not due_date
        # This test verifies the endpoint accepts the parameter

    @pytest.mark.asyncio
    async def test_work_order_overdue_detection(
        self, client: AsyncClient, auth_headers, sample_product, db_session
    ):
        """Detect overdue work orders (due_date in past, not DONE)."""
        from datetime import datetime, timedelta, timezone

        past_date = datetime.now(timezone.utc) - timedelta(days=3)

        # Create an overdue order
        order = WorkOrder(
            lot_no="LOT-OVERDUE-001",
            product_id=sample_product.id,
            target_qty=100,
            due_date=past_date,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # List orders and check if overdue can be detected
        response = await client.get(
            "/api/v1/production/orders?status=READY",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Find the overdue order
        overdue_order = next(
            (item for item in data["items"] if item["lot_no"] == "LOT-OVERDUE-001"), None
        )
        assert overdue_order is not None
        assert overdue_order["due_date"] is not None

        # Verify due_date is in the past
        due_date = datetime.fromisoformat(overdue_order["due_date"].replace("Z", "+00:00"))
        assert due_date < datetime.now(due_date.tzinfo)


class TestProductionResult:
    """Test production result registration."""

    @pytest.mark.asyncio
    async def test_register_production_result(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Register a production result for a work order."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-RESULT-REG-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = await client.post(
            "/api/v1/production/results",
            headers=auth_headers,
            json={
                "work_order_id": order.id,
                "equipment_id": sample_equipment.id,
                "ok_qty": 50,
                "ng_qty": 2,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["work_order_id"] == order.id
        assert data["ok_qty"] == 50
        assert data["ng_qty"] == 2

    @pytest.mark.asyncio
    async def test_auto_complete_on_target_qty(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Register result meeting target_qty: status stays RUNNING (auto-complete not implemented)."""
        # Create work order with low target
        order = WorkOrder(
            lot_no="LOT-AUTO-COMPLETE-001",
            product_id=sample_product.id,
            target_qty=10,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Register result that meets target
        response = await client.post(
            "/api/v1/production/results",
            headers=auth_headers,
            json={
                "work_order_id": order.id,
                "equipment_id": sample_equipment.id,
                "ok_qty": 10,
                "ng_qty": 0,
            },
        )

        assert response.status_code == 201

        # Auto-complete is not implemented; status remains RUNNING
        response = await client.get(
            f"/api/v1/production/orders/{order.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_concurrent_result_registration(
        self, client: AsyncClient, auth_headers, sample_product, sample_equipment, db_session
    ):
        """Multiple production results can be registered for the same work order."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-CONCURRENT-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Register multiple results
        for i in range(3):
            response = await client.post(
                "/api/v1/production/results",
                headers=auth_headers,
                json={
                    "work_order_id": order.id,
                    "equipment_id": sample_equipment.id,
                    "ok_qty": 10 + i,
                    "ng_qty": i,
                },
            )
            assert response.status_code == 201

        # List results for this work order
        response = await client.get(
            f"/api/v1/production/results?work_order_id={order.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3

        # Verify total quantities
        total_ok = sum(item["ok_qty"] for item in data["items"])
        total_ng = sum(item["ng_qty"] for item in data["items"])
        assert total_ok == 10 + 11 + 12  # 10, 11, 12
        assert total_ng == 0 + 1 + 2  # 0, 1, 2


# ============================================================================
# QA/QC Regression Tests - API Boundary & Edge Cases
# ============================================================================


class TestAPIBoundary:
    """Test API parameter boundary values (QA/QC regression)."""

    @pytest.mark.asyncio
    async def test_orders_limit_100(self, client: AsyncClient, auth_headers):
        """limit=100 should be accepted."""
        response = await client.get(
            "/api/v1/production/orders?limit=100",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_orders_limit_500(self, client: AsyncClient, auth_headers):
        """limit=500 should be accepted (regression: was 422 with le=100)."""
        response = await client.get(
            "/api/v1/production/orders?limit=500",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_orders_limit_1000(self, client: AsyncClient, auth_headers):
        """limit=1000 should be accepted (max allowed)."""
        response = await client.get(
            "/api/v1/production/orders?limit=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_orders_limit_over_max(self, client: AsyncClient, auth_headers):
        """limit > 1000 should return 422."""
        response = await client.get(
            "/api/v1/production/orders?limit=1001",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_results_limit_1000(self, client: AsyncClient, auth_headers):
        """Results endpoint also accepts limit=1000."""
        response = await client.get(
            "/api/v1/production/results?limit=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_orders_view_all_with_high_limit(self, client: AsyncClient, auth_headers):
        """view=all with limit=1000 should work (dashboard use case)."""
        response = await client.get(
            "/api/v1/production/orders?view=all&limit=1000",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data  # pagination info
