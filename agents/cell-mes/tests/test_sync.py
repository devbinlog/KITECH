"""Tests for AAS asset synchronization."""

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from src.app.models.equipment import Equipment
from src.app.services.aas_scheduler_info import (
    flatten_scheduler_info,
    normalize_aas_assets_response,
    scheduler_spec_from_asset,
)
from src.app.services.sync_service import sync_equipments_from_middleware


def _scheduler_info_submodel():
    return {
        "idShort": "schedulerInfo",
        "modelType": "Submodel",
        "submodelElements": [
            {
                "idShort": "machineType",
                "modelType": "Property",
                "value": "VMC_3AXIS_MASS",
                "valueType": "xs:string",
            },
            {
                "idShort": "setupChangeTimeMin",
                "modelType": "Property",
                "value": "15",
                "valueType": "xs:int",
            },
            {
                "idShort": "currentSetupId",
                "modelType": "Property",
                "value": "TS-MASS-001",
                "valueType": "xs:string",
            },
            {
                "idShort": "machineTypeParams",
                "modelType": "SubmodelElementCollection",
                "value": [
                    {
                        "idShort": "loadingType",
                        "modelType": "Property",
                        "value": "buffer_exchange",
                        "valueType": "xs:string",
                    },
                    {
                        "idShort": "amrTransportQty",
                        "modelType": "Property",
                        "value": "3",
                        "valueType": "xs:int",
                    },
                ],
            },
            {
                "idShort": "calendar",
                "modelType": "SubmodelElementCollection",
                "value": [
                    {
                        "idShort": "shiftStart",
                        "modelType": "Property",
                        "value": "08:00",
                        "valueType": "xs:string",
                    },
                    {
                        "idShort": "shiftEnd",
                        "modelType": "Property",
                        "value": "20:00",
                        "valueType": "xs:string",
                    },
                    {
                        "idShort": "breaks",
                        "modelType": "SubmodelElementCollection",
                        "value": [
                            {
                                "idShort": "break_0",
                                "modelType": "SubmodelElementCollection",
                                "value": [
                                    {
                                        "idShort": "start",
                                        "modelType": "Property",
                                        "value": "12:00",
                                        "valueType": "xs:string",
                                    },
                                    {
                                        "idShort": "end",
                                        "modelType": "Property",
                                        "value": "13:00",
                                        "valueType": "xs:string",
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
        ],
    }


def test_flatten_scheduler_info_preserves_nested_shape_and_casts_types():
    spec = flatten_scheduler_info(_scheduler_info_submodel())

    assert spec["machineType"] == "VMC_3AXIS_MASS"
    assert spec["setupChangeTimeMin"] == 15
    assert spec["currentSetupId"] == "TS-MASS-001"
    assert spec["machineTypeParams"] == {
        "loadingType": "buffer_exchange",
        "amrTransportQty": 3,
    }
    assert spec["calendar"] == {
        "shiftStart": "08:00",
        "shiftEnd": "20:00",
        "breaks": [{"start": "12:00", "end": "13:00"}],
    }


def test_normalize_aas_environment_resolves_scheduler_info_submodel():
    sample_path = (
        Path(__file__).resolve().parents[3]
        / "samples"
        / "cell-scheduler"
        / "input"
        / "aas_revised.json"
    )
    data = json.loads(sample_path.read_text(encoding="utf-8"))

    assets = normalize_aas_assets_response(data)

    assert len(assets) == 4
    dh400 = next(asset for asset in assets if asset["idShort"] == "DH400")
    assert "schedulerInfo" in dh400["submodels"]
    spec = flatten_scheduler_info(dh400["submodels"]["schedulerInfo"])
    assert spec["machineType"] == "VMC_3AXIS_MASS"
    assert spec["machineTypeParams"]["amrTransportQty"] == 3
    assert spec["calendar"]["breaks"] == [{"start": "12:00", "end": "13:00"}]


def test_scheduler_spec_from_already_flattened_middleware_asset_normalizes_lists():
    asset = {
        "id": "https://example.com/ids/aas/7483_2191_1062_9621",
        "idShort": "DOOSAN_MOMA",
        "submodels": {
            "schedulerInfo": {
                "machineType": "AMR",
                "model": "MiR250",
                "status": "available",
                "speedMPerSec": 1.0,
                "accessibleMachines": {
                    "machine_0": "https://example.com/ids/aas/5154_7101_1062_2938",
                    "machine_1": "https://example.com/ids/aas/2405_6010_2062_9026",
                },
                "capacityByType": {
                    "VMC_3AXIS_MASS": 3,
                    "RACK": 1,
                },
                "calendar": {
                    "shiftStart": "08:00",
                    "shiftEnd": "20:00",
                    "breaks": {},
                },
            }
        },
    }

    spec = scheduler_spec_from_asset(asset)

    assert spec["machineType"] == "AMR"
    assert spec["accessibleMachines"] == [
        "https://example.com/ids/aas/5154_7101_1062_2938",
        "https://example.com/ids/aas/2405_6010_2062_9026",
    ]
    assert spec["capacityByType"] == {"VMC_3AXIS_MASS": 3, "RACK": 1}
    assert spec["calendar"]["breaks"] == []


class TestAssetSync:
    """Test AAS asset discovery and synchronization."""

    @pytest.mark.asyncio
    async def test_sync_creates_new_equipment(self, db_session):
        """New assets are created in DB."""
        mock_assets = [
            {
                "id": "urn:aas:cnc:new-001",
                "idShort": "New CNC",
                "submodels": {"cncGateway": {"isConnected": True}},
            }
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 1
        assert "urn:aas:cnc:new-001" in result.created
        assert len(result.updated) == 0

        # Verify in database
        query = select(Equipment).where(Equipment.aas_id == "urn:aas:cnc:new-001")
        db_result = await db_session.execute(query)
        equipment = db_result.scalar_one_or_none()

        assert equipment is not None
        assert equipment.eq_name == "New CNC"
        assert equipment.equipment_type == "CNC"

    @pytest.mark.asyncio
    async def test_sync_stores_scheduler_info_in_spec_data(self, db_session):
        """schedulerInfo is flattened into equipment.spec_data during sync."""
        mock_assets = [
            {
                "id": "urn:aas:cnc:scheduler-001",
                "idShort": "DH400",
                "submodels": {
                    "cncGateway": {"idShort": "cncGateway"},
                    "schedulerInfo": _scheduler_info_submodel(),
                },
            }
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 1
        query = select(Equipment).where(Equipment.aas_id == "urn:aas:cnc:scheduler-001")
        db_result = await db_session.execute(query)
        equipment = db_result.scalar_one()

        assert equipment.equipment_type == "CNC"
        assert equipment.spec_data["machineType"] == "VMC_3AXIS_MASS"
        assert equipment.spec_data["setupChangeTimeMin"] == 15
        assert equipment.spec_data["machineTypeParams"]["loadingType"] == "buffer_exchange"
        assert equipment.spec_data["calendar"]["breaks"] == [{"start": "12:00", "end": "13:00"}]

    @pytest.mark.asyncio
    async def test_sync_maps_scheduler_and_case_variant_gateway_types(self, db_session):
        """Equipment types use schedulerInfo and case-insensitive gateway idShorts."""
        mock_assets = [
            {
                "id": "urn:aas:feeder",
                "idShort": "FEEDER",
                "submodels": {
                    "RobotGateway": {"idShort": "RobotGateway"},
                    "schedulerInfo": {"machineType": "FEEDER"},
                },
            },
            {
                "id": "urn:aas:equator",
                "idShort": "EQUATOR_01",
                "submodels": {
                    "RobotGateway": {"idShort": "RobotGateway"},
                    "schedulerInfo": {"machineType": "QCM"},
                },
            },
            {
                "id": "urn:aas:ur",
                "idShort": "UR_ROBOT",
                "submodels": {
                    "RobotGateway": {"idShort": "RobotGateway"},
                    "schedulerInfo": {"machineType": "ROBOT_ARM"},
                },
            },
            {
                "id": "urn:aas:amr",
                "idShort": "ANT_AMR",
                "submodels": {
                    "RobotGateway": {"idShort": "RobotGateway"},
                    "schedulerInfo": {"machineType": "AMR"},
                },
            },
            {
                "id": "urn:aas:rack",
                "idShort": "RACK_01",
                "submodels": {"HttpGateway": {"idShort": "HttpGateway"}},
            },
            {
                "id": "urn:aas:nx5500",
                "idShort": "NX5500",
                "submodels": {"CncGateway2": {"idShort": "CncGateway2"}},
            },
            {
                "id": "urn:aas:nx5500-virtual",
                "idShort": "NX5500_VIRTUAL_01",
                "submodels": {"schedulerInfo": {"machineType": "VMC_3AXIS_MASS"}},
            },
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == len(mock_assets)
        query = select(Equipment)
        db_result = await db_session.execute(query)
        by_name = {equipment.eq_name: equipment for equipment in db_result.scalars().all()}

        assert by_name["FEEDER"].equipment_type == "FEEDER"
        assert by_name["EQUATOR_01"].equipment_type == "QCM"
        assert by_name["UR_ROBOT"].equipment_type == "ROBOT"
        assert by_name["ANT_AMR"].equipment_type == "AMR"
        assert by_name["RACK_01"].equipment_type == "RACK"
        assert by_name["NX5500"].equipment_type == "CNC"
        assert by_name["NX5500_VIRTUAL_01"].equipment_type == "CNC"

    @pytest.mark.asyncio
    async def test_sync_updates_existing_equipment(self, db_session, sample_equipment):
        """Existing assets are updated, not duplicated."""
        # sample_equipment has aas_id = "urn:aas:cnc:test-001"
        mock_assets = [
            {
                "id": "urn:aas:cnc:test-001",
                "idShort": "Updated CNC Name",
                "submodels": {"cncGateway": {"isConnected": True}},
            }
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 1
        assert "urn:aas:cnc:test-001" in result.updated
        assert len(result.created) == 0

        # Verify update in database
        await db_session.refresh(sample_equipment)
        assert sample_equipment.eq_name == "Updated CNC Name"

    @pytest.mark.asyncio
    async def test_sync_updates_scheduler_info_and_preserves_existing_spec(self, db_session, sample_equipment):
        """Existing non-scheduler spec keys are preserved when schedulerInfo is updated."""
        mock_assets = [
            {
                "id": "urn:aas:cnc:test-001",
                "idShort": "Updated CNC Name",
                "submodels": {
                    "cncGateway": {"idShort": "cncGateway"},
                    "schedulerInfo": _scheduler_info_submodel(),
                },
            }
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 1
        assert "urn:aas:cnc:test-001" in result.updated
        await db_session.refresh(sample_equipment)
        assert sample_equipment.spec_data["manufacturer"] == "Test"
        assert sample_equipment.spec_data["machineType"] == "VMC_3AXIS_MASS"
        assert sample_equipment.spec_data["machineTypeParams"]["amrTransportQty"] == 3

    @pytest.mark.asyncio
    async def test_sync_handles_multiple_assets(self, db_session):
        """Multiple assets are synced correctly."""
        mock_assets = [
            {"id": "urn:aas:cnc:001", "name": "CNC 1", "type": "CNC", "connection": {}, "spec": {}},
            {
                "id": "urn:aas:robot:001",
                "name": "Robot 1",
                "type": "ROBOT",
                "connection": {},
                "spec": {},
            },
            {"id": "urn:aas:plc:001", "name": "PLC 1", "type": "PLC", "connection": {}, "spec": {}},
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 3
        assert len(result.created) == 3

    @pytest.mark.asyncio
    async def test_sync_handles_middleware_error(self, db_session):
        """Middleware connection errors are handled gracefully."""
        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=Exception("Connection refused"),
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 0
        assert len(result.errors) == 1
        assert "Connection refused" in result.errors[0]

    @pytest.mark.asyncio
    async def test_sync_skips_assets_without_id(self, db_session):
        """Assets without 'id' field are skipped with error."""
        mock_assets = [
            {"name": "No ID Asset", "type": "CNC"},  # Missing 'id'
            {
                "id": "urn:aas:cnc:valid",
                "name": "Valid Asset",
                "type": "CNC",
                "connection": {},
                "spec": {},
            },
        ]

        with patch(
            "src.app.services.sync_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=mock_assets,
        ):
            result = await sync_equipments_from_middleware(db_session)

        assert result.synced_count == 1
        assert "urn:aas:cnc:valid" in result.created
        assert len(result.errors) == 1
