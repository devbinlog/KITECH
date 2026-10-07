"""Tests for equipment management endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from src.app.models.equipment import Equipment


class TestEquipmentList:
    """Test equipment list endpoint."""

    @pytest.mark.asyncio
    async def test_list_equipments(self, client: AsyncClient, auth_headers, sample_equipment):
        """List all equipments."""
        response = await client.get("/api/v1/masters/equipments", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["eq_name"] == "Test CNC"
        assert data[0]["aas_id"] == "urn:aas:cnc:test-001"

    @pytest.mark.asyncio
    async def test_list_equipments_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/masters/equipments")

        assert response.status_code == 401


class TestEquipmentCreate:
    """Test equipment creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_equipment_admin(self, client: AsyncClient, admin_auth_headers):
        """Admin can create equipment."""
        response = await client.post(
            "/api/v1/masters/equipments",
            headers=admin_auth_headers,
            json={
                "eq_code": "EQ-ROBOT-NEW-001",
                "eq_name": "New Equipment",
                "equipment_type": "ROBOT",
                "aas_id": "urn:aas:robot:new-001",
                "connection_config": {"ip": "192.168.1.50", "port": 30002},
                "spec_data": {"manufacturer": "UR"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["eq_name"] == "New Equipment"
        assert data["equipment_type"] == "ROBOT"

    @pytest.mark.asyncio
    async def test_create_equipment_non_admin(self, client: AsyncClient, auth_headers):
        """Non-admin cannot create equipment."""
        response = await client.post(
            "/api/v1/masters/equipments",
            headers=auth_headers,
            json={"eq_code": "EQ-CNC-NEW", "eq_name": "New Equipment", "equipment_type": "CNC"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_equipment_duplicate_aas_id(
        self, client: AsyncClient, admin_auth_headers, sample_equipment
    ):
        """Duplicate AAS ID returns 400."""
        response = await client.post(
            "/api/v1/masters/equipments",
            headers=admin_auth_headers,
            json={
                "eq_code": "EQ-CNC-DUP-001",
                "eq_name": "Duplicate Equipment",
                "equipment_type": "CNC",
                "aas_id": "urn:aas:cnc:test-001",  # Same as sample_equipment
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestEquipmentVirtualCopies:
    """Test MES-managed virtual equipment copy endpoint."""

    @pytest.mark.asyncio
    async def test_create_virtual_copies_from_physical_equipment(
        self, client: AsyncClient, admin_auth_headers, db_session, sample_equipment
    ):
        """Admin can create virtual scheduling copies without copying AAS connection state."""
        sample_equipment.spec_data = {
            "machineType": "VMC_3AXIS_PALLET",
            "setupChangeTimeMin": 5,
            "machineTypeParams": {
                "loadingType": "pallet_single",
                "amrTransportQty": 1,
            },
        }
        await db_session.commit()

        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/virtual-copies",
            headers=admin_auth_headers,
            json={
                "count": 3,
                "name_prefix": "DH400_MES_VIRTUAL",
                "overrides": {
                    "setupChangeTimeMin": 8,
                    "machineTypeParams": {
                        "loadingType": "buffer_exchange",
                        "amrTransportQty": 2,
                    },
                    "isVirtual": False,
                    "equipmentSource": "PHYSICAL",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 3
        assert [item["eq_name"] for item in data["created"]] == [
            "DH400_MES_VIRTUAL_01",
            "DH400_MES_VIRTUAL_02",
            "DH400_MES_VIRTUAL_03",
        ]

        first = data["created"][0]
        assert first["aas_id"] is None
        assert first["equipment_type"] == sample_equipment.equipment_type
        assert first["connection_config"] == {}
        assert first["last_data"] == {}
        assert first["current_status"] == "STOP"
        assert first["spec_data"]["isVirtual"] is True
        assert first["spec_data"]["equipmentSource"] == "MES"
        assert first["spec_data"]["virtualizationType"] == "SCHEDULING_COPY"
        assert first["spec_data"]["physicalEquipmentId"] == sample_equipment.id
        assert first["spec_data"]["physicalAssetRef"] == sample_equipment.aas_id
        assert first["spec_data"]["virtualEquipmentGroup"] == sample_equipment.eq_name
        assert first["spec_data"]["setupChangeTimeMin"] == 8
        assert first["spec_data"]["machineTypeParams"]["amrTransportQty"] == 2

        result = await db_session.execute(
            select(Equipment).where(Equipment.eq_name.like("DH400_MES_VIRTUAL%"))
        )
        created = list(result.scalars().all())
        assert len(created) == 3
        assert all(equipment.aas_id is None for equipment in created)

    @pytest.mark.asyncio
    async def test_create_virtual_copy_non_admin_forbidden(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Non-admin users cannot create virtual equipment copies."""
        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/virtual-copies",
            headers=auth_headers,
            json={"count": 1},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_virtual_copy_rejects_virtual_source(
        self, client: AsyncClient, admin_auth_headers, db_session
    ):
        """Virtual equipment cannot be used as another virtual copy source."""
        virtual_equipment = Equipment(
            eq_code="EQ-VIRT-CNC-001",
            aas_id=None,
            eq_name="Virtual CNC",
            equipment_type="CNC",
            connection_config={},
            spec_data={"isVirtual": True, "equipmentSource": "MES"},
            last_data={},
            current_status="STOP",
        )
        db_session.add(virtual_equipment)
        await db_session.commit()
        await db_session.refresh(virtual_equipment)

        response = await client.post(
            f"/api/v1/masters/equipments/{virtual_equipment.id}/virtual-copies",
            headers=admin_auth_headers,
            json={"count": 1},
        )

        assert response.status_code == 400
        assert "Virtual equipment" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_virtual_copy_count_limit(
        self, client: AsyncClient, admin_auth_headers, sample_equipment
    ):
        """Copy count is bounded to avoid accidental bulk creation."""
        response = await client.post(
            f"/api/v1/masters/equipments/{sample_equipment.id}/virtual-copies",
            headers=admin_auth_headers,
            json={"count": 21},
        )

        assert response.status_code == 422


class TestEquipmentStatus:
    """Test equipment status endpoint."""

    @pytest.mark.asyncio
    async def test_get_equipment_status(self, client: AsyncClient, auth_headers, sample_equipment):
        """Get equipment status."""
        response = await client.get(
            f"/api/v1/masters/equipments/{sample_equipment.id}/status",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_status"] == "RUN"
        assert data["last_data"]["spindle_rpm"] == 15000

    @pytest.mark.asyncio
    async def test_get_equipment_status_not_found(self, client: AsyncClient, auth_headers):
        """Non-existent equipment returns 404."""
        response = await client.get(
            "/api/v1/masters/equipments/9999/status",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestEquipmentSync:
    """Test equipment sync endpoint."""

    @pytest.mark.asyncio
    async def test_sync_equipments(self, client: AsyncClient, admin_auth_headers):
        """Admin can sync equipment from middleware."""
        mock_assets = [
            {
                "id": "urn:aas:cnc:sync-001",
                "name": "Synced CNC",
                "type": "CNC",
                "connection": {"ip": "192.168.1.100"},
                "spec": {},
            }
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            response = await client.post(
                "/api/v1/masters/equipments/sync",
                headers=admin_auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["synced_count"] == 1
        assert "urn:aas:cnc:sync-001" in data["created"]

    @pytest.mark.asyncio
    async def test_sync_equipments_non_admin(self, client: AsyncClient, auth_headers):
        """Non-admin cannot sync equipment."""
        response = await client.post(
            "/api/v1/masters/equipments/sync",
            headers=auth_headers,
        )

        assert response.status_code == 403
