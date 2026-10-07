"""MES-managed virtual equipment copy service."""

from __future__ import annotations

import copy
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.equipment import Equipment
from ..schemas.equipment import EquipmentVirtualCopyCreate


ALLOWED_OVERRIDE_KEYS = {
    "machineType",
    "setupChangeTimeMin",
    "currentSetupId",
    "machineTypeParams",
    "calendar",
    "capacity",
    "buffer",
}
PROTECTED_SPEC_KEYS = {
    "isVirtual",
    "is_virtual",
    "equipmentSource",
    "virtualizationType",
    "physicalEquipmentId",
    "physicalAssetRef",
    "virtualEquipmentGroup",
}


class VirtualEquipmentError(Exception):
    """Domain error raised when virtual copy creation is invalid."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _truthy_flag(value: Any) -> bool:
    if value is True or value == 1:
        return True
    if not isinstance(value, str):
        return False
    return value.strip().lower() in {"true", "1", "y", "yes"}


def is_virtual_spec(spec_data: dict[str, Any] | None) -> bool:
    spec = spec_data or {}
    source = str(spec.get("equipmentSource") or "").upper()
    return (
        _truthy_flag(spec.get("isVirtual"))
        or _truthy_flag(spec.get("is_virtual"))
        or source in {"VIRTUAL", "MES"}
    )


def _sanitize_code_part(value: str, fallback: str = "EQ") -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.upper()).strip("_")
    return normalized or fallback


async def _load_existing_names_and_codes(db: AsyncSession) -> tuple[set[str], set[str]]:
    result = await db.execute(select(Equipment.eq_name, Equipment.eq_code))
    rows = result.all()
    return {row[0] for row in rows}, {row[1] for row in rows}


def _next_name(prefix: str, existing_names: set[str]) -> str:
    index = 1
    while True:
        candidate = f"{prefix}_{index:02d}"
        if candidate not in existing_names:
            existing_names.add(candidate)
            return candidate
        index += 1


def _next_code(source: Equipment, ordinal: int, existing_codes: set[str]) -> str:
    type_part = _sanitize_code_part(source.equipment_type or "EQ", "EQ")[:6]
    name_part = _sanitize_code_part(source.eq_name, "VIRTUAL")

    # Equipment.eq_code is String(30). Reserve suffix room and keep codes readable.
    index = ordinal
    while True:
        suffix = f"{index:02d}"
        base = f"EQ-VIRT-{type_part}-{name_part}"
        max_base_len = 30 - len(suffix) - 1
        candidate = f"{base[:max_base_len]}-{suffix}"
        if candidate not in existing_codes:
            existing_codes.add(candidate)
            return candidate
        index += 1


def _copy_scheduler_spec(
    source: Equipment,
    payload: EquipmentVirtualCopyCreate,
) -> dict[str, Any]:
    spec = copy.deepcopy(source.spec_data or {})

    for key, value in (payload.overrides or {}).items():
        if key in ALLOWED_OVERRIDE_KEYS:
            spec[key] = copy.deepcopy(value)

    if payload.machineType:
        spec["machineType"] = payload.machineType

    # Protected metadata is always controlled by the server.
    for key in PROTECTED_SPEC_KEYS:
        spec.pop(key, None)

    spec["isVirtual"] = True
    spec["equipmentSource"] = "MES"
    spec["virtualizationType"] = "SCHEDULING_COPY"
    spec["physicalEquipmentId"] = source.id
    if source.aas_id:
        spec["physicalAssetRef"] = source.aas_id
    spec["virtualEquipmentGroup"] = source.eq_name
    return spec


async def create_virtual_copies(
    db: AsyncSession,
    source_equipment_id: int,
    payload: EquipmentVirtualCopyCreate,
) -> list[Equipment]:
    result = await db.execute(
        select(Equipment).where(Equipment.id == source_equipment_id)
    )
    source = result.scalar_one_or_none()
    if not source or source.is_deleted:
        raise VirtualEquipmentError("Source equipment not found", status_code=404)
    if is_virtual_spec(source.spec_data):
        raise VirtualEquipmentError("Virtual equipment cannot be used as a copy source")

    prefix = (payload.name_prefix or f"{source.eq_name}_MES_VIRTUAL").strip()
    if not prefix:
        raise VirtualEquipmentError("name_prefix cannot be empty")

    existing_names, existing_codes = await _load_existing_names_and_codes(db)
    created: list[Equipment] = []

    for ordinal in range(1, payload.count + 1):
        eq_name = _next_name(prefix, existing_names)
        eq_code = _next_code(source, ordinal, existing_codes)
        equipment = Equipment(
            eq_code=eq_code,
            aas_id=None,
            eq_name=eq_name,
            model_name=source.model_name or source.eq_name,
            equipment_type=source.equipment_type,
            location=source.location,
            cell_id=source.cell_id,
            connection_config={},
            spec_data=_copy_scheduler_spec(source, payload),
            last_data={},
            current_status="STOP",
        )
        db.add(equipment)
        created.append(equipment)

    await db.commit()
    for equipment in created:
        await db.refresh(equipment)
    return created
