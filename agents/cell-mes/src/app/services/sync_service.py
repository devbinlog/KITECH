"""AAS Asset Discovery and synchronization service."""

from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.equipment import Equipment
from ..schemas.equipment import EquipmentSync
from .aas_scheduler_info import scheduler_spec_from_asset
from ...clients.middleware_client import middleware_client


def _submodel_key_set(submodels: Any) -> set[str]:
    """Return case-insensitive submodel idShort keys from middleware AAS payloads."""
    if isinstance(submodels, dict):
        keys = set(submodels.keys())
        for submodel in submodels.values():
            if isinstance(submodel, dict) and submodel.get("idShort"):
                keys.add(str(submodel["idShort"]))
        return {key.lower() for key in keys}
    if isinstance(submodels, list):
        return {
            str(submodel.get("idShort")).lower()
            for submodel in submodels
            if isinstance(submodel, dict) and submodel.get("idShort")
        }
    return set()


def _equipment_type_from_scheduler_machine_type(machine_type: str) -> str | None:
    """Map scheduler machineType to the high-level MES equipment_type."""
    normalized = machine_type.upper()
    if not normalized:
        return None
    if normalized in {"AMR", "AGV", "MM"}:
        return "AMR"
    if normalized in {"RACK", "BUFFER"}:
        return "RACK"
    if normalized in {"FEEDER", "FEEDER_TYPE"}:
        return "FEEDER"
    if normalized in {"QCM", "QC", "INSPECTION", "EQUATOR"}:
        return "QCM"
    if normalized in {"ROBOT", "ROBOT_ARM", "CR", "COBOT"}:
        return "ROBOT"
    if normalized.startswith(("CNC", "VMC_", "HMC_", "LATHE", "MILL")):
        return "CNC"
    return None


def _equipment_type_from_asset(asset: dict, scheduler_spec: dict) -> str:
    """Resolve the display/analytics equipment type without losing scheduler detail."""
    scheduler_machine_type = str(scheduler_spec.get("machineType") or "")
    scheduler_equipment_type = _equipment_type_from_scheduler_machine_type(
        scheduler_machine_type
    )
    if scheduler_equipment_type:
        return scheduler_equipment_type

    submodel_keys = _submodel_key_set(asset.get("submodels", {}))
    if any(key.startswith("cncgateway") for key in submodel_keys):
        return "CNC"
    if "robotgateway" in submodel_keys:
        return "ROBOT"
    if "httpgateway" in submodel_keys:
        return "RACK"
    if "localgateway" in submodel_keys:
        return "PLC"

    legacy_type = str(asset.get("type") or "").upper()
    if legacy_type:
        return legacy_type

    return "CNC"


async def sync_equipments_from_middleware(
    db: AsyncSession, delete_orphans: bool = False
) -> EquipmentSync:
    """
    Synchronize equipment from middleware (AAS Asset Discovery).

    Fetches all assets from middleware and:
    - Creates new equipment records for unknown aas_ids
    - Updates existing equipment records if aas_id exists
    - Optionally soft-deletes orphan equipment (aas_id에 더 이상 없는 기록)

    Args:
        db: Database session
        delete_orphans: True면 미들웨어에 없는 기존 설비를 소프트 삭제

    Returns:
        EquipmentSync result with counts and details
    """
    created: List[str] = []
    updated: List[str] = []
    deleted: List[str] = []
    errors: List[str] = []

    try:
        # Fetch assets from middleware
        assets = await middleware_client.fetch_all_assets()
    except Exception as e:
        return EquipmentSync(
            synced_count=0,
            created=[],
            updated=[],
            deleted=[],
            errors=[f"Failed to fetch assets from middleware: {str(e)}"],
        )

    # 미들웨어 aas_id 세트
    middleware_aas_ids = {asset["id"] for asset in assets if "id" in asset}

    for asset in assets:
        aas_id = asset.get("id")
        if not aas_id:
            errors.append(f"Asset missing 'id' field: {asset}")
            continue

        scheduler_spec = scheduler_spec_from_asset(asset)

        # 자산 트리에서 설비 유형 추출
        eq_type = _equipment_type_from_asset(asset, scheduler_spec)

        id_short = asset.get("idShort", "")
        aas_suffix = aas_id.split("/")[-1].upper() if "/" in aas_id else aas_id.upper()
        eq_code = f"EQ-{eq_type}-{aas_suffix[:20]}"
        eq_name = id_short or f"Equipment-{aas_id}"

        # Use a savepoint per asset
        nested = await db.begin_nested()
        try:
            result = await db.execute(select(Equipment).where(Equipment.aas_id == aas_id))
            existing = result.scalar_one_or_none()

            if existing:
                existing.eq_name = id_short or existing.eq_name
                existing.equipment_type = eq_type
                if scheduler_spec:
                    existing.spec_data = {
                        **(existing.spec_data or {}),
                        **scheduler_spec,
                    }
                existing.last_connected_at = datetime.now(timezone.utc)
                existing.is_deleted = False  # 있던 건 다시 활성화
                await nested.commit()
                updated.append(aas_id)
            else:
                equipment = Equipment(
                    eq_code=eq_code,
                    aas_id=aas_id,
                    eq_name=eq_name,
                    model_name=id_short or None,
                    equipment_type=eq_type,
                    connection_config={},
                    spec_data=scheduler_spec,
                    last_connected_at=datetime.now(timezone.utc),
                )
                db.add(equipment)
                await nested.commit()
                created.append(aas_id)

        except Exception as e:
            errors.append(f"Error processing asset {aas_id}: {str(e)}")
            await nested.rollback()

    # 선택적 고암 설비 소프트 삭제
    if delete_orphans:
        orphan_result = await db.execute(
            select(Equipment).where(
                Equipment.is_deleted.is_(False),
                Equipment.aas_id.isnot(None),
                Equipment.aas_id.notin_(middleware_aas_ids),
            )
        )
        orphans = list(orphan_result.scalars().all())
        for orphan in orphans:
            orphan.is_deleted = True
            deleted.append(orphan.eq_name or orphan.aas_id)

    await db.commit()

    return EquipmentSync(
        synced_count=len(created) + len(updated),
        created=created,
        updated=updated,
        deleted=deleted,
        errors=errors,
    )
