"""P4R JSON preview adapter for MES work orders."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.master import ProcessRouting
from ...models.production import Unit, WorkOrder
from ..aas_scheduler_info import scheduler_spec_from_asset
from .aas_view_client import AasViewClient, AasViewClientError
from .failure_rules import P4RFailureRuleSet, load_p4r_failure_rules
from .p4r_action_timing import (
    ActionTimingEntry,
    build_action_timing_catalog,
    calculate_processing_time,
    group_actions_by_op,
    mapping_by_process_code,
)
from .scenario_asset_parser import (
    load_scenario_yaml,
    p4r_process_mappings,
    scenario_assets,
    scenario_operation_ids,
    scenario_step_actions,
)

ID_SAFE = re.compile(r"[^A-Za-z0-9_\-]+")
P4R_AAS_VIEW_TIMEOUT_SEC = 3.0
QCM_RESOURCE_TYPES = {"QCM", "QUALITY_CONTROL_MACHINE", "QUALITY_CONTROLL_MACHINE"}
P4R_QCM_RESOURCE_TYPE = "QUALITY_CONTROLL_MACHINE"


def _sid(value: Any, fallback: str = "NA") -> str:
    text = str(value or fallback).strip()
    return ID_SAFE.sub("_", text) or fallback


def _s(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _int_string(value: Any, default: int = 0) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(default)


def _flatten_submodel_elements(submodel: dict[str, Any]) -> dict[str, Any]:
    elements = submodel.get("submodelElements")
    if not isinstance(elements, list):
        return submodel

    flattened: dict[str, Any] = {}
    for element in elements:
        if not isinstance(element, dict):
            continue
        key = element.get("idShort")
        if not key:
            continue
        if isinstance(element.get("value"), list):
            flattened[str(key)] = _flatten_submodel_elements({"submodelElements": element["value"]})
        elif "value" in element:
            flattened[str(key)] = element.get("value")
    return flattened


def _profile(asset: dict[str, Any]) -> dict[str, Any]:
    submodels = asset.get("submodels") if isinstance(asset.get("submodels"), dict) else {}
    profile = submodels.get("DtSimulationProfile") or submodels.get("dtSimulationProfile") or {}
    return _flatten_submodel_elements(profile) if isinstance(profile, dict) else {}


def _profile_value(profile: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in profile and profile[key] not in (None, ""):
            return profile[key]
    return default


def _status(asset: dict[str, Any]) -> dict[str, Any]:
    submodels = asset.get("submodels") if isinstance(asset.get("submodels"), dict) else {}
    merged: dict[str, Any] = {}
    for gateway_name in (
        "CncGateway",
        "RobotGateway",
        "HttpGateway",
        "ModbusGateway",
        "cncGateway",
        "robotGateway",
        "httpGateway",
        "modbusGateway",
    ):
        gateway = submodels.get(gateway_name)
        if not isinstance(gateway, dict):
            continue
        gateway = _flatten_submodel_elements(gateway)
        if "IsConnected" in gateway:
            merged.setdefault("isConnected", gateway.get("IsConnected"))
        status = gateway.get("Status")
        if isinstance(status, dict):
            merged.update(status)
    return merged


def _asset_id(asset: dict[str, Any]) -> str:
    return str(asset.get("idShort") or asset.get("id") or "")


def _asset_name_matches_resource(asset_name: str, resource_type: str) -> bool:
    label = asset_name.upper()
    if resource_type in QCM_RESOURCE_TYPES:
        return "QCM" in label or "EQUATOR" in label or "INSPECTION" in label
    if resource_type == "CNC":
        return (
            label.startswith("NX")
            or label.startswith("DH")
            or ("CNC" in label and "DIE" not in label)
        )
    if resource_type == "FEEDER":
        return "FEEDER" in label
    if resource_type == "MM":
        return "AMR" in label or "MOMA" in label
    if resource_type in {"CR", "MHR"}:
        return "UR" in label or ("ROBOT" in label and "FEEDER" not in label)
    if resource_type == "BUFFER":
        return "RACK" in label or "DIE" in label or "BUFFER" in label
    return resource_type in label


def _resource_type(profile: dict[str, Any]) -> str:
    return str(_profile_value(profile, "dt_resource_type", "resourceType", default="")).upper()


def _p4r_machine_resource_type(resource_type: str) -> str:
    if resource_type in QCM_RESOURCE_TYPES:
        return P4R_QCM_RESOURCE_TYPE
    return resource_type or "MACHINE"


def _type_id(asset_id: str, profile: dict[str, Any]) -> str:
    return str(_profile_value(profile, "dt_type_id", "machineTypeId", default=f"TYPE_{asset_id}"))


def _feeder_buffer_specs(asset_name: str, asset: dict[str, Any]) -> list[dict[str, Any]]:
    profile = _profile(asset)
    if _resource_type(profile) != "FEEDER":
        return []

    scheduler_info = scheduler_spec_from_asset(asset)
    feeder_id = _sid(asset_name or _type_id(asset_name, profile))
    specs: list[dict[str, Any]] = []
    for suffix, capacity_keys, status_keys in (
        (
            "IN",
            ("loaderSlots", "loader_slots", "loaderCapacity", "loader_capacity"),
            ("loaderCount", "loader_count"),
        ),
        (
            "OUT",
            ("unloaderSlots", "unloader_slots", "unloaderCapacity", "unloader_capacity"),
            ("unloaderCount", "unloader_count"),
        ),
    ):
        capacity = _profile_value(scheduler_info, *capacity_keys)
        if capacity in (None, ""):
            continue
        specs.append(
            {
                "direction": suffix,
                "type_id": f"BT_{feeder_id}_{suffix}",
                "instance_id": f"{feeder_id}_{suffix}",
                "capacity": capacity,
                "status_keys": status_keys,
            }
        )
    return specs


def _first_present_value(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def _last_operation_id_for_code(process_info: list[dict[str, Any]], process_code: str) -> str:
    code = process_code.upper()
    for process in reversed(process_info):
        process_id = str(process.get("PROCESS_INFO_ID") or "").upper()
        operations = process.get("PROCESS_OPERATION_INFO") or []
        for operation in reversed(operations):
            if not isinstance(operation, dict):
                continue
            operation_id = str(operation.get("PROCESS_OPERATION_INFO_ID") or "")
            if f"_{code}_" in operation_id.upper() or process_id.endswith(f"_{code}"):
                return operation_id
    return ""


def _first_nc_filename(routing: ProcessRouting) -> str:
    files = sorted(routing.files or [], key=lambda item: item.sort_order)
    for file in files:
        if str(file.file_type or "").upper() == "NC":
            return file.original_filename or file.file_path
    return files[0].original_filename or files[0].file_path if files else ""


def _routing_cycle_time(routing: ProcessRouting) -> Any:
    if routing.cycle_time_sec is not None:
        return routing.cycle_time_sec
    if routing.std_process:
        return routing.std_process.cycle_time_sec
    return None


def _routing_cycle_time_source(routing: ProcessRouting) -> str:
    if routing.cycle_time_sec is not None:
        return "process_routings.cycle_time_sec"
    if routing.std_process and routing.std_process.cycle_time_sec is not None:
        return "std_processes.cycle_time_sec"
    return "default"


def _parse_slots(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, str):
        for candidate in (value, value.replace("'", '"')):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    return list(parsed.values())
            except ValueError:
                continue
    return []


def _occupied_slot_count(value: Any) -> str:
    slots = _parse_slots(value)
    count = 0
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        state = str(slot.get("state") or slot.get("status") or "").lower()
        content = str(slot.get("content") or slot.get("material") or "").lower()
        occupied = bool(slot.get("occupied")) if "occupied" in slot else False
        if occupied or state in {"occupied", "full", "used"} or content not in {"", "none", "null"}:
            count += 1
    return str(count)


class P4RPayloadAdapter:
    """Build P4R preview payloads from MES data and middleware AAS view."""

    def __init__(
        self,
        aas_client: AasViewClient | None = None,
        failure_rules: P4RFailureRuleSet | None = None,
    ):
        self.aas_client = aas_client or AasViewClient(timeout=P4R_AAS_VIEW_TIMEOUT_SEC)
        self.failure_rules = failure_rules or load_p4r_failure_rules()

    async def build_preview(self, db: AsyncSession, lot_no: str) -> dict[str, Any]:
        warnings: list[str] = []
        warnings.extend(self.failure_rules.warnings)
        order = await self._get_order(db, lot_no)
        if order is None:
            raise ValueError(f"작업지시 LOT를 찾을 수 없습니다: {lot_no}")
        if not order.product:
            raise ValueError(f"작업지시에 제품이 연결되어 있지 않습니다: {lot_no}")
        if not order.scenario:
            raise ValueError(f"작업지시에 시나리오가 연결되어 있지 않습니다: {lot_no}")

        scenario_content: dict[str, Any] = {}
        scenario_path = None
        try:
            scenario_content, scenario_path = load_scenario_yaml(order.scenario.file_path)
        except Exception as exc:
            warnings.append(f"시나리오 YAML을 읽지 못했습니다: {exc}")

        scenario_asset_rows = scenario_assets(scenario_content)
        scenario_asset_names = [item["name"] for item in scenario_asset_rows]
        scenario_ops = scenario_operation_ids(scenario_content)
        scenario_p4r_mappings = p4r_process_mappings(scenario_content)
        scenario_timing_actions = scenario_step_actions(scenario_content, scenario_asset_rows)
        if not scenario_asset_names:
            warnings.append("시나리오에서 assets 목록을 찾지 못했습니다")

        aas_assets: list[dict[str, Any]] = []
        try:
            aas_assets = await self.aas_client.fetch_assets()
        except AasViewClientError as exc:
            warnings.append(str(exc))

        aas_by_name = {_asset_id(asset): asset for asset in aas_assets if _asset_id(asset)}
        selected_assets = {
            name: aas_by_name.get(name, {"idShort": name, "submodels": {}})
            for name in scenario_asset_names
        }
        for name, asset in selected_assets.items():
            if not asset.get("submodels"):
                warnings.append(f"AAS view에서 자산을 찾지 못했습니다: {name}")
            elif not _profile(asset):
                warnings.append(f"DtSimulationProfile이 없습니다: {name}")

        routings = await self._get_routings(db, order.product_id)
        if not routings:
            warnings.append(f"제품 라우팅이 없습니다: {order.product.code}")
        if order.status == "DONE":
            warnings.append("완료된 LOT 기준으로 P4R preview를 생성합니다")
        warnings.append(
            "MATERIAL_ID는 MES material 기준 테이블 부재로 제품 코드 기반 규칙(MT_{PRODUCT_ID})으로 생성합니다"
        )

        failure_interpretations: list[dict[str, Any]] = []
        processing_time_breakdowns: list[dict[str, Any]] = []
        action_timing_catalog = build_action_timing_catalog(selected_assets)
        payload = self._build_payload(
            order,
            routings,
            selected_assets,
            warnings,
            failure_interpretations,
            scenario_p4r_mappings,
            scenario_timing_actions,
            action_timing_catalog,
            processing_time_breakdowns,
        )
        return {
            "status": "success",
            "lot_no": order.lot_no,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "warnings": warnings,
            "sources": {
                "mes": {
                    "work_order_id": order.id,
                    "product_id": order.product_id,
                    "product_code": order.product.code,
                    "scenario_id": order.scenario_id,
                    "routing_count": len(routings),
                    "unit_count": len(order.units or []),
                    "routing_cycle_times": [
                        {
                            "routing_id": routing.id,
                            "sequence": routing.sequence,
                            "std_process_id": routing.std_process_id,
                            "process_code": (
                                routing.std_process.code if routing.std_process else None
                            ),
                            "cycle_time_sec": _routing_cycle_time(routing),
                            "source": _routing_cycle_time_source(routing),
                            "breakdown": routing.cycle_time_breakdown,
                        }
                        for routing in routings
                    ],
                },
                "scenario": {
                    "file_path": str(scenario_path or order.scenario.file_path),
                    "assets": scenario_asset_rows,
                    "operation_ids": scenario_ops,
                    "p4r_process_mapping": scenario_p4r_mappings,
                },
                "aas": {
                    "base_url": self.aas_client.base_url,
                    "asset_count": len(aas_assets),
                    "selected_assets": list(selected_assets.keys()),
                    "status_snapshot": {
                        name: _status(asset) for name, asset in selected_assets.items()
                    },
                },
                "p4r_failure_interpretations": {
                    "source": self.failure_rules.source,
                    "items": failure_interpretations,
                },
                "p4r_processing_time": {
                    "mapping_count": len(scenario_p4r_mappings),
                    "scenario_action_count": len(scenario_timing_actions),
                    "profile_action_count": len(action_timing_catalog),
                    "items": processing_time_breakdowns,
                },
            },
        }

    async def _get_order(self, db: AsyncSession, lot_no: str) -> WorkOrder | None:
        result = await db.execute(
            select(WorkOrder)
            .where(WorkOrder.lot_no == lot_no)
            .options(
                selectinload(WorkOrder.product),
                selectinload(WorkOrder.scenario),
                selectinload(WorkOrder.units).selectinload(Unit.scenario),
            )
        )
        return result.scalar_one_or_none()

    async def _get_routings(self, db: AsyncSession, product_id: int | None) -> list[ProcessRouting]:
        if product_id is None:
            return []
        result = await db.execute(
            select(ProcessRouting)
            .where(ProcessRouting.product_id == product_id)
            .options(
                selectinload(ProcessRouting.std_process),
                selectinload(ProcessRouting.files),
            )
            .order_by(ProcessRouting.sequence)
        )
        return list(result.scalars().all())

    def _build_payload(
        self,
        order: WorkOrder,
        routings: list[ProcessRouting],
        assets: dict[str, dict[str, Any]],
        warnings: list[str],
        failure_interpretations: list[dict[str, Any]],
        scenario_p4r_mappings: list[dict[str, Any]] | None = None,
        scenario_timing_actions: list[dict[str, str]] | None = None,
        action_timing_catalog: dict[tuple[str, str], ActionTimingEntry] | None = None,
        processing_time_breakdowns: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        product_code = _sid(order.product.code)
        material_id = f"MT_{product_code}"
        process_info = self._build_process_info(
            product_code,
            material_id,
            routings,
            assets,
            warnings,
            scenario_p4r_mappings,
            scenario_timing_actions,
            action_timing_catalog,
            processing_time_breakdowns,
        )

        machine_types, buffer_types, mm_types, mhr_types = self._build_type_sections(assets)
        machine_instances, buffer_instances, mm_instances, mhr_instances = self._build_instances(
            product_code, material_id, assets, process_info, failure_interpretations
        )

        return {
            "PRODUCT_INFO": [{"PRODUCT_ID": product_code}],
            "MATERIAL_INFO": [{"MATERIAL_ID": material_id, "PRODUCT_ID": product_code}],
            "PROCESS_INFO": process_info,
            "MATERIAL_HANDLING_INFO": self._build_material_handling(
                product_code, material_id, assets
            ),
            "MACHINE_TYPE": machine_types,
            "BUFFER_TYPE": buffer_types,
            "MM_TYPE": mm_types,
            "MHR_TYPE": mhr_types,
            "PRODUCTION_PLAN": [
                {
                    "PRODUCTION_PLAN_ID": f"PPS_{order.lot_no}",
                    "PRODUCT_ID": product_code,
                    "PRODUCTION_VOLUME": _int_string(order.target_qty or order.qty),
                    "CURRENT_VOLUME": _int_string(order.completed_qty),
                }
            ],
            "MACHINE_INSTANCE": machine_instances,
            "BUFFER_INSTANCE": buffer_instances,
            "MM_INSTANCE": mm_instances,
            "MHR_INSTANCE": mhr_instances,
        }

    def _build_process_info(
        self,
        product_code: str,
        material_id: str,
        routings: list[ProcessRouting],
        assets: dict[str, dict[str, Any]],
        warnings: list[str] | None = None,
        scenario_p4r_mappings: list[dict[str, Any]] | None = None,
        scenario_timing_actions: list[dict[str, str]] | None = None,
        action_timing_catalog: dict[tuple[str, str], ActionTimingEntry] | None = None,
        processing_time_breakdowns: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        mapping_lookup = mapping_by_process_code(scenario_p4r_mappings or [])
        actions_by_op = group_actions_by_op(scenario_timing_actions or [])
        timing_catalog = action_timing_catalog or {}
        for index, routing in enumerate(routings):
            code = _sid(
                routing.std_process.code if routing.std_process else f"PROC{routing.sequence}"
            )
            timing = calculate_processing_time(
                process_code=code,
                routing_cycle_time=_routing_cycle_time(routing),
                routing_cycle_time_source=_routing_cycle_time_source(routing),
                mapping_by_process=mapping_lookup,
                scenario_actions_by_op=actions_by_op,
                action_timing_catalog=timing_catalog,
            )
            if timing.warning and warnings is not None:
                warnings.append(timing.warning)
            if processing_time_breakdowns is not None:
                processing_time_breakdowns.append(timing.breakdown)
            asset_name = self._operation_asset_name(code, routing, assets)
            asset = assets.get(asset_name or "", {})
            machine_type_id = _type_id(asset_name or _sid(routing.std_process_id), _profile(asset))
            op_id = f"OR_{product_code}_{code}_{_sid(asset_name or machine_type_id)}"
            entry = {
                "PROCESS_INFO_ID": f"PP_{product_code}_{code}",
                "PRODUCT_ID": product_code,
                "PROCESS_OPERATION_INFO": [
                    {
                        "PROCESS_OPERATION_INFO_ID": op_id,
                        "MACHINE_TYPE_ID": machine_type_id,
                        "PROCESSING_TIME": _int_string(timing.value, default=0),
                    }
                ],
                "CONSUMED_MATERIAL_INFO": [
                    {
                        "CONSUMED_MATERIAL_INFO_ID": f"CMI_{product_code}_{code}",
                        "MATERIAL_ID": material_id,
                        "PROC_NUM": str(index + 1),
                        "MATERIAL_NUM": "1",
                    }
                ],
                "PRODUCED_MATERIAL_INFO": [
                    {
                        "PRODUCED_MATERIAL_INFO_ID": f"PMI_{product_code}_{code}",
                        "MATERIAL_ID": material_id,
                        "PROC_NUM": str(index + 2),
                        "MATERIAL_NUM": "1",
                    }
                ],
            }
            nc_file = _first_nc_filename(routing)
            if nc_file:
                entry["PART_PROGRAM_ID"] = nc_file
            result.append(entry)
        return result

    def _operation_asset_name(
        self,
        process_code: str,
        routing: ProcessRouting,
        assets: dict[str, dict[str, Any]],
    ) -> str | None:
        code = process_code.upper()
        equipment_type = str(
            routing.std_process.equipment_type if routing.std_process else ""
        ).upper()
        resource_priority: list[str]
        if (
            "INSP" in code
            or "INSPECT" in code
            or "QC" in code
            or equipment_type in {"QCM", "INSPECTION", "QUALITY_CONTROL_MACHINE"}
        ):
            resource_priority = ["QCM", "QUALITY_CONTROL_MACHINE", "QUALITY_CONTROLL_MACHINE"]
        elif "MILL" in code or "CNC" in equipment_type:
            resource_priority = ["CNC"]
        elif "UNLOAD" in code or "LOAD" in code or "ROBOT" in equipment_type:
            resource_priority = ["FEEDER", "CNC", "MM", "CR"]
        else:
            resource_priority = [equipment_type, "CNC", "FEEDER", "MM", "CR"]
        for resource in resource_priority:
            for asset_name, asset in assets.items():
                profile = _profile(asset)
                asset_label = asset_name.upper()
                if (
                    _resource_type(profile) == resource
                    or _type_id(asset_name, profile).upper() == resource
                    or _asset_name_matches_resource(asset_label, resource)
                ):
                    return asset_name
        return next(iter(assets), None)

    def _build_type_sections(
        self, assets: dict[str, dict[str, Any]]
    ) -> tuple[
        list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]
    ]:
        machine_types: list[dict[str, str]] = []
        buffer_types: list[dict[str, str]] = []
        mm_types: list[dict[str, str]] = []
        mhr_types: list[dict[str, str]] = []
        seen: set[str] = set()
        for asset_name, asset in assets.items():
            profile = _profile(asset)
            resource_type = _resource_type(profile)
            type_id = _type_id(asset_name, profile)
            if type_id in seen:
                continue
            seen.add(type_id)
            if resource_type in {"CNC", "FEEDER", "MACHINE"} | QCM_RESOURCE_TYPES:
                machine_types.append(
                    {
                        "MACHINE_TYPE_ID": type_id,
                        "RESOURCE_TYPE": _p4r_machine_resource_type(resource_type),
                        "CAPACITY": _int_string(_profile_value(profile, "capacity"), 1),
                        "MEAN_TIME_TO_REPAIR": _int_string(
                            _profile_value(profile, "mean_time_to_repair", "meanTimeToRepair"),
                            999999,
                        ),
                        "MEAN_TIME_BETWEEN_FAILURE": _int_string(
                            _profile_value(
                                profile,
                                "mean_time_between_failure",
                                "meanTimeBetweenFailure",
                            ),
                            99999999,
                        ),
                    }
                )
                if resource_type == "FEEDER":
                    for spec in _feeder_buffer_specs(asset_name, asset):
                        buffer_type_id = spec["type_id"]
                        if buffer_type_id in seen:
                            continue
                        seen.add(buffer_type_id)
                        buffer_types.append(
                            {
                                "BUFFER_TYPE_ID": buffer_type_id,
                                "RESOURCE_TYPE": "BUFFER",
                                "CAPACITY": _int_string(spec["capacity"], 1),
                            }
                        )
            elif resource_type == "BUFFER":
                buffer_types.append(
                    {
                        "BUFFER_TYPE_ID": type_id,
                        "RESOURCE_TYPE": "BUFFER",
                        "CAPACITY": _int_string(
                            _profile_value(profile, "capacity", "slotCapacity"), 1
                        ),
                    }
                )
            elif resource_type == "MM":
                mm_types.append(
                    {
                        "MM_TYPE_ID": type_id,
                        "RESOURCE_TYPE": "MM",
                        "OPERATION_SPEED": _int_string(
                            _profile_value(profile, "operation_speed", "operationSpeed"), 0
                        ),
                        "TRANSPORTATION_SPEED": _int_string(
                            _profile_value(
                                profile,
                                "transportation_speed",
                                "transportationSpeed",
                            ),
                            0,
                        ),
                        "TURN_SPEED": _int_string(
                            _profile_value(profile, "turn_speed", "turnSpeed"), 0
                        ),
                        "MOVE_SPEED": _int_string(
                            _profile_value(profile, "move_speed", "moveSpeed"), 0
                        ),
                        "MEAN_TIME_BETWEEN_FAILURE": _int_string(
                            _profile_value(
                                profile,
                                "mean_time_between_failure",
                                "meanTimeBetweenFailure",
                            ),
                            999999,
                        ),
                        "MEAN_TIME_TO_REPAIR": _int_string(
                            _profile_value(profile, "mean_time_to_repair", "meanTimeToRepair"),
                            999999,
                        ),
                        "CAPACITY": _int_string(_profile_value(profile, "capacity"), 1),
                        "BATTERY_CAPACITY": _int_string(
                            _profile_value(profile, "battery_capacity", "batteryCapacity"), 100
                        ),
                        "POWER_TO_CHARGE_LIMIT": _int_string(
                            _profile_value(
                                profile,
                                "power_to_charge_limit",
                                "powerToChargeLimit",
                            ),
                            15,
                        ),
                    }
                )
            elif resource_type in {"CR", "MHR"}:
                mhr_types.append(
                    {
                        "MHR_TYPE_ID": type_id,
                        "RESOURCE_TYPE": "CR",
                        "MEAN_TIME_TO_REPAIR": _int_string(
                            _profile_value(profile, "mean_time_to_repair", "meanTimeToRepair"),
                            999999,
                        ),
                        "MEAN_TIME_BETWEEN_FAILURE": _int_string(
                            _profile_value(
                                profile,
                                "mean_time_between_failure",
                                "meanTimeBetweenFailure",
                            ),
                            999999,
                        ),
                        "CAPACITY": _int_string(_profile_value(profile, "capacity"), 1),
                    }
                )
        return machine_types, buffer_types, mm_types, mhr_types

    def _build_material_handling(
        self, product_code: str, material_id: str, assets: dict[str, dict[str, Any]]
    ) -> list[dict[str, str]]:
        result = []
        for asset_name, asset in assets.items():
            profile = _profile(asset)
            if _resource_type(profile) != "MM":
                continue
            result.append(
                {
                    "MATERIAL_HANDLING_INFO_ID": f"MHI_{product_code}_{_sid(asset_name)}",
                    "MATERIAL_ID": material_id,
                    "MHE_TYPE_ID": _type_id(asset_name, profile),
                    "HANDLING_BATCH_SIZE": _int_string(
                        _profile_value(profile, "handling_batch_size", "handlingBatchSize"), 1
                    ),
                    "PUSH_PULL": _s(_profile_value(profile, "push_pull", "pushPull"), "PULL"),
                    "LOADING_TIME": _int_string(
                        _profile_value(profile, "loading_time_sec", "loadingTimeSec"), 0
                    ),
                    "UNLOADING_TIME": _int_string(
                        _profile_value(profile, "unloading_time_sec", "unloadingTimeSec"), 0
                    ),
                }
            )
        return result

    def _build_instances(
        self,
        product_code: str,
        material_id: str,
        assets: dict[str, dict[str, Any]],
        process_info: list[dict[str, Any]],
        failure_interpretations: list[dict[str, Any]] | None = None,
    ) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
    ]:
        machine_instances: list[dict[str, Any]] = []
        buffer_instances: list[dict[str, Any]] = []
        mm_instances: list[dict[str, Any]] = []
        mhr_instances: list[dict[str, Any]] = []
        finished_op_id = ""
        if process_info:
            finished_op_id = process_info[-1]["PROCESS_OPERATION_INFO"][0][
                "PROCESS_OPERATION_INFO_ID"
            ]
        for asset_name, asset in assets.items():
            profile = _profile(asset)
            status = _status(asset)
            resource_type = _resource_type(profile)
            type_id = _type_id(asset_name, profile)
            if resource_type in {"CNC", "FEEDER", "MACHINE"} | QCM_RESOURCE_TYPES:
                p4r_resource_type = _p4r_machine_resource_type(resource_type)
                failure_status = self.failure_rules.interpret(
                    asset_id=asset_name,
                    resource_type=p4r_resource_type,
                    status=status,
                )
                if failure_interpretations is not None:
                    failure_interpretations.append(
                        failure_status.as_trace(asset_name, p4r_resource_type)
                    )
                machine_instances.append(
                    {
                        "MACHINE_INSTANCE_ID": asset_name,
                        "MACHINE_TYPE_ID": type_id,
                        "FAILURE_STATUS": [
                            {
                                "FAILURE_STATUS_ID": f"FS_{_sid(asset_name)}",
                                "FAILURE_TYPE": failure_status.failure_type,
                                "REMAINING_REPAIR_TIME": _int_string(
                                    failure_status.remaining_repair_time
                                ),
                            }
                        ],
                        "WORK_IN_PROCESS_STATUS": [
                            {
                                "WORK_IN_PROCESS_STATUS_ID": f"WIPS_{_sid(asset_name)}",
                                "PROCESS_OPERATION_INFO_ID": "",
                                "PROCESSED_TIME": "",
                            }
                        ],
                    }
                )
                if resource_type == "FEEDER":
                    for spec in _feeder_buffer_specs(asset_name, asset):
                        wip_count = _int_string(
                            _first_present_value(status, *spec["status_keys"], default=0),
                            0,
                        )
                        finished_operation_id = ""
                        if spec["direction"] == "OUT" and wip_count != "0":
                            finished_operation_id = (
                                _last_operation_id_for_code(process_info, "UNLOAD")
                                or finished_op_id
                            )
                        buffer_instances.append(
                            {
                                "BUFFER_INSTANCE_ID": spec["instance_id"],
                                "BUFFER_TYPE_ID": spec["type_id"],
                                "WORK_IN_PROCESS_STATUS": [
                                    {
                                        "WORK_IN_PROCESS_STATUS_ID": (
                                            f"WIPBF_{_sid(spec['instance_id'])}"
                                        ),
                                        "FINISHED_OPERATION_INFO_ID": finished_operation_id,
                                        "MATERIAL_ID": material_id,
                                        "WORK_IN_PROCESS_NUM": wip_count,
                                    }
                                ],
                            }
                        )
            elif resource_type == "BUFFER":
                buffer_instances.append(
                    {
                        "BUFFER_INSTANCE_ID": asset_name,
                        "BUFFER_TYPE_ID": type_id,
                        "WORK_IN_PROCESS_STATUS": [
                            {
                                "WORK_IN_PROCESS_STATUS_ID": f"WIPBF_{_sid(asset_name)}",
                                "FINISHED_OPERATION_INFO_ID": finished_op_id,
                                "MATERIAL_ID": material_id,
                                "WORK_IN_PROCESS_NUM": _occupied_slot_count(
                                    status.get("allSlots")
                                    or [
                                        status.get("occupiedInputSlot"),
                                        status.get("occupiedOutputSlot"),
                                    ]
                                ),
                            }
                        ],
                    }
                )
            elif resource_type == "MM":
                mm_instances.append(
                    {
                        "MM_INSTANCE_ID": asset_name,
                        "MM_TYPE_ID": type_id,
                        "MATERIAL_HANDLING_STATUS": [
                            {
                                "MATERIAL_HANDLING_STATUS_ID": f"MHS_{_sid(asset_name)}",
                                "MATERIAL_HANDLING_INFO_ID": f"MHI_{product_code}_{_sid(asset_name)}",
                                "CURRENT_POSITION_X": _s(status.get("agvPositionX")),
                                "CURRENT_POSITION_Y": _s(status.get("agvPositionY")),
                                "CURRENT_POSITION_Z": "0",
                            }
                        ],
                    }
                )
            elif resource_type in {"CR", "MHR"}:
                mhr_instances.append(
                    {
                        "MHR_INSTANCE_ID": asset_name,
                        "MHR_TYPE_ID": type_id,
                    }
                )
        return machine_instances, buffer_instances, mm_instances, mhr_instances
