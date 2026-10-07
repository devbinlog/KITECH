"""Tests for data consistency and integrity."""

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from src.app.models.master import StdProcess


class TestUniquenessConstraints:
    """Test uniqueness constraints on database models."""

    @pytest.mark.asyncio
    async def test_lot_no_uniqueness(
        self, client: AsyncClient, auth_headers, sample_product, sample_scenario, db_session, mock_middleware_http
    ):
        """lot_no must be unique."""
        # Create first work order
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-UNIQUE-001",
                "product_id": sample_product.id,
                "target_qty": 100,
                "scenario_id": sample_scenario.id,
            },
        )
        assert response.status_code == 201

        # Try to create second work order with same lot_no
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-UNIQUE-001",  # Same lot_no
                "product_id": sample_product.id,
                "target_qty": 50,
                "scenario_id": sample_scenario.id,
            },
        )
        # Should fail due to uniqueness constraint
        assert response.status_code in [400, 409, 422]

    @pytest.mark.asyncio
    async def test_product_code_uniqueness(
        self, client: AsyncClient, admin_auth_headers, db_session
    ):
        """product.code must be unique."""
        # Create first product
        response = await client.post(
            "/api/v1/masters/products",
            headers=admin_auth_headers,
            json={
                "code": "PROD-UNIQUE-001",
                "name": "First Product",
                "unit": "EA",
            },
        )
        assert response.status_code == 201

        # Try to create second product with same code
        response = await client.post(
            "/api/v1/masters/products",
            headers=admin_auth_headers,
            json={
                "code": "PROD-UNIQUE-001",  # Same code
                "name": "Second Product",
                "unit": "EA",
            },
        )
        # Should fail due to uniqueness constraint
        assert response.status_code in [400, 409, 422]

    @pytest.mark.asyncio
    async def test_std_process_code_uniqueness(self, db_session):
        """std_process.code must be unique at database level."""
        # Create first process
        process1 = StdProcess(
            code="STD-UNIQUE-001",
            name="First Process",
        )
        db_session.add(process1)
        await db_session.commit()

        # Try to create second process with same code
        process2 = StdProcess(
            code="STD-UNIQUE-001",  # Same code
            name="Second Process",
        )
        db_session.add(process2)

        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_equipment_aas_id_uniqueness(
        self, client: AsyncClient, admin_auth_headers, sample_equipment
    ):
        """equipment.aas_id must be unique."""
        # Try to create equipment with same aas_id
        response = await client.post(
            "/api/v1/masters/equipments",
            headers=admin_auth_headers,
            json={
                "eq_code": "EQ-CNC-DUP-TEST",
                "eq_name": "Duplicate Equipment",
                "equipment_type": "CNC",
                "aas_id": sample_equipment.aas_id,  # Same aas_id
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestWorkOrderStateTransitions:
    """Test work order state machine transitions."""

    @pytest.mark.asyncio
    async def test_ready_to_running(self, client: AsyncClient, auth_headers, sample_work_order):
        """READY -> RUNNING is valid."""
        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_ready_to_pause_invalid(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """READY -> PAUSE is invalid."""
        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "PAUSE"},
        )
        # Should fail - can't pause from READY state
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_ready_to_done_invalid(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """READY -> DONE is invalid."""
        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "DONE"},
        )
        # Should fail - can't complete from READY state
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_running_to_pause(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """RUNNING -> PAUSE is valid."""
        # First change to RUNNING
        sample_work_order.status = "RUNNING"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "PAUSE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "PAUSE"

    @pytest.mark.asyncio
    async def test_running_to_done(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """RUNNING -> DONE is valid."""
        # First change to RUNNING
        sample_work_order.status = "RUNNING"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "DONE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "DONE"

    @pytest.mark.asyncio
    async def test_running_to_error(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """RUNNING -> ERROR is valid."""
        # First change to RUNNING
        sample_work_order.status = "RUNNING"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "ERROR"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ERROR"

    @pytest.mark.asyncio
    async def test_pause_to_running(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """PAUSE -> RUNNING is valid (resume)."""
        # First change to PAUSE
        sample_work_order.status = "PAUSE"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_pause_to_done(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """PAUSE -> DONE is valid."""
        # First change to PAUSE
        sample_work_order.status = "PAUSE"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "DONE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "DONE"

    @pytest.mark.asyncio
    async def test_error_to_running(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """ERROR -> RUNNING is valid (retry)."""
        # First change to ERROR
        sample_work_order.status = "ERROR"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_error_to_done(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """ERROR -> DONE is valid (force complete)."""
        # First change to ERROR
        sample_work_order.status = "ERROR"
        db_session.add(sample_work_order)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "DONE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "DONE"

    @pytest.mark.asyncio
    async def test_done_to_any_invalid(
        self, client: AsyncClient, auth_headers, sample_work_order, db_session
    ):
        """DONE -> any state is invalid."""
        # First change to DONE
        sample_work_order.status = "DONE"
        db_session.add(sample_work_order)
        await db_session.commit()

        # Try to change to RUNNING
        response = await client.patch(
            f"/api/v1/production/orders/{sample_work_order.id}/status",
            headers=auth_headers,
            json={"status": "RUNNING"},
        )
        # Should fail - can't change from DONE
        assert response.status_code in [400, 422]


class TestForeignKeyIntegrity:
    """Test foreign key constraints."""

    @pytest.mark.asyncio
    async def test_work_order_requires_valid_product(
        self, client: AsyncClient, auth_headers, sample_scenario
    ):
        """Work order must reference existing product."""
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-FK-001",
                "product_id": 99999,  # Non-existent product
                "target_qty": 100,
                "scenario_id": sample_scenario.id,
            },
        )
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_work_order_requires_valid_scenario(
        self, client: AsyncClient, auth_headers, sample_product
    ):
        """Work order must reference existing scenario."""
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-FK-002",
                "product_id": sample_product.id,
                "target_qty": 100,
                "scenario_id": 99999,  # Non-existent scenario
            },
        )
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_routing_requires_valid_product(
        self, client: AsyncClient, admin_auth_headers, sample_std_process
    ):
        """Process routing must reference existing product."""
        # API uses PUT for routings, not POST
        response = await client.put(
            "/api/v1/masters/products/99999/routings",
            headers=admin_auth_headers,
            json=[
                {
                    "std_process_id": sample_std_process.id,
                    "sequence": 10,
                }
            ],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_routing_requires_valid_std_process(
        self, client: AsyncClient, admin_auth_headers, sample_product
    ):
        """Process routing must reference existing std_process."""
        # API uses PUT for routings, not POST
        response = await client.put(
            f"/api/v1/masters/products/{sample_product.id}/routings",
            headers=admin_auth_headers,
            json=[
                {
                    "std_process_id": 99999,  # Non-existent process
                    "sequence": 10,
                }
            ],
        )
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_prod_result_requires_valid_work_order(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Production result must reference existing work order."""
        response = await client.post(
            "/api/v1/production/results",
            headers=auth_headers,
            json={
                "work_order_id": 99999,  # Non-existent work order
                "equipment_id": sample_equipment.id,
                "ok_qty": 10,
                "ng_qty": 0,
            },
        )
        assert response.status_code in [400, 404, 422]


class TestSoftDelete:
    """Test soft delete functionality."""

    @pytest.mark.asyncio
    async def test_product_soft_delete(
        self, client: AsyncClient, admin_auth_headers, sample_product
    ):
        """Product deletion is soft (is_deleted flag)."""
        # Delete product
        response = await client.delete(
            f"/api/v1/masters/products/{sample_product.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 204

        # Product should not appear in normal list
        response = await client.get(
            "/api/v1/masters/products",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        product_ids = [p["id"] for p in response.json()]
        assert sample_product.id not in product_ids

        # But should appear with include_deleted flag
        response = await client.get(
            "/api/v1/masters/products?include_deleted=true",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        product_ids = [p["id"] for p in response.json()]
        assert sample_product.id in product_ids

    @pytest.mark.asyncio
    async def test_equipment_soft_delete(
        self, client: AsyncClient, admin_auth_headers, sample_equipment
    ):
        """Equipment deletion is soft (is_deleted flag)."""
        # Delete equipment
        response = await client.delete(
            f"/api/v1/masters/equipments/{sample_equipment.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 204

        # Equipment should not appear in normal list
        response = await client.get(
            "/api/v1/masters/equipments",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        eq_ids = [e["id"] for e in response.json()]
        assert sample_equipment.id not in eq_ids


class TestDataValidation:
    """Test data validation rules."""

    @pytest.mark.asyncio
    async def test_work_order_priority_range(
        self, client: AsyncClient, auth_headers, sample_product, sample_scenario, mock_middleware_http
    ):
        """Work order priority must be within valid range."""
        # Valid priority (1-10)
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-VAL-001",
                "product_id": sample_product.id,
                "target_qty": 100,
                "priority": 5,
                "scenario_id": sample_scenario.id,
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_work_order_target_qty_positive(
        self, client: AsyncClient, auth_headers, sample_product, sample_scenario
    ):
        """Work order target_qty must be positive."""
        response = await client.post(
            "/api/v1/production/orders",
            headers=auth_headers,
            json={
                "lot_no": "LOT-VAL-002",
                "product_id": sample_product.id,
                "target_qty": 0,  # Invalid
                "scenario_id": sample_scenario.id,
            },
        )
        # Should fail validation
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_product_unit_valid_values(self, client: AsyncClient, admin_auth_headers):
        """Product unit must be valid (EA, SET, KG, M, etc.)."""
        # Valid unit
        response = await client.post(
            "/api/v1/masters/products",
            headers=admin_auth_headers,
            json={
                "code": "PROD-VAL-001",
                "name": "Valid Product",
                "unit": "EA",
            },
        )
        assert response.status_code == 201
