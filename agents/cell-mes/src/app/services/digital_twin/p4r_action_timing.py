"""P4R processing-time calculation from scenario mappings and AAS action profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

ACTION_PROFILE_KEYS = {"P4RActionTimingProfile", "p4rActionTimingProfile"}
TIME_MODE_ROUTING = "ROUTING_CYCLE"
TIME_MODE_ACTION = "ACTION_PROFILE"
TIME_MODE_ROUTING_PLUS_ACTION = "ROUTING_CYCLE_PLUS_ACTION_PROFILE"
TIME_MODE_ROUTING_OR_ACTION = "ROUTING_CYCLE_OR_ACTION_PROFILE"
TOKEN_SAFE = re.compile(r"[^A-Za-z0-9]+")


@dataclass(frozen=True)
class ActionTimingEntry:
    asset: str
    action: str
    default_duration_sec: int | None
    time_ownership: str
    can_contribute_to_routing_cycle_time: bool


@dataclass(frozen=True)
class ProcessingTimeResult:
    value: int
    source: str
    mapping_applied: bool
    warning: str | None = None
    breakdown: dict[str, Any] = field(default_factory=dict)


def build_action_timing_catalog(
    assets: dict[str, dict[str, Any]],
) -> dict[tuple[str, str], ActionTimingEntry]:
    """Build {(asset, action): timing} lookup from AAS P4RActionTimingProfile submodels."""

    catalog: dict[tuple[str, str], ActionTimingEntry] = {}
    for asset_name, asset in assets.items():
        profile = _action_profile(asset)
        actions = _profile_actions(profile)
        for action_name, action_data in actions:
            entry = _timing_entry(asset_name, action_name, action_data)
            if entry is None:
                continue
            catalog[(_key(asset_name), _key(entry.action))] = entry
    return catalog


def calculate_processing_time(
    *,
    process_code: str,
    routing_cycle_time: Any,
    routing_cycle_time_source: str,
    mapping_by_process: dict[str, dict[str, Any]],
    scenario_actions_by_op: dict[str, list[dict[str, str]]],
    action_timing_catalog: dict[tuple[str, str], ActionTimingEntry],
) -> ProcessingTimeResult:
    """Calculate PROCESSING_TIME with explicit scenario mapping fallback."""

    base_value = _int_value(routing_cycle_time, 0)
    process_key = _key(process_code)
    mapping = mapping_by_process.get(process_key)
    if not mapping:
        return ProcessingTimeResult(
            value=base_value,
            source=routing_cycle_time_source,
            mapping_applied=False,
            breakdown={
                "mode": TIME_MODE_ROUTING,
                "base_sec": base_value,
                "base_source": routing_cycle_time_source,
                "reason": "p4r_process_mapping 없음",
            },
        )

    mode = str(mapping.get("time_mode") or TIME_MODE_ROUTING).upper()
    op_ids = [str(op_id) for op_id in mapping.get("op_ids") or [] if op_id]
    action_components, skipped_actions = _collect_action_components(
        op_ids, scenario_actions_by_op, action_timing_catalog
    )
    action_total = sum(component["duration_sec"] for component in action_components)
    warning: str | None = None

    if mode == TIME_MODE_ROUTING:
        value = base_value
        source = routing_cycle_time_source
    elif mode == TIME_MODE_ACTION:
        if action_components:
            value = action_total
            source = "scenario.p4r_process_mapping.action_profile"
        else:
            value = base_value
            source = routing_cycle_time_source
            warning = f"{process_code} action profile 매칭 결과가 없어 기존 routing cycle time을 사용합니다"
    elif mode == TIME_MODE_ROUTING_PLUS_ACTION:
        value = base_value + action_total
        source = "routing_cycle_time+scenario_action_profile"
    elif mode == TIME_MODE_ROUTING_OR_ACTION:
        if routing_cycle_time is not None:
            value = base_value
            source = routing_cycle_time_source
        elif action_components:
            value = action_total
            source = "scenario.p4r_process_mapping.action_profile"
        else:
            value = base_value
            source = routing_cycle_time_source
            warning = f"{process_code} time source가 없어 0초로 fallback합니다"
    else:
        value = base_value
        source = routing_cycle_time_source
        warning = (
            f"{process_code} time_mode={mode}를 알 수 없어 기존 routing cycle time을 사용합니다"
        )

    return ProcessingTimeResult(
        value=value,
        source=source,
        mapping_applied=True,
        warning=warning,
        breakdown={
            "mode": mode,
            "process_code": process_code,
            "op_ids": op_ids,
            "base_sec": base_value,
            "base_source": routing_cycle_time_source,
            "action_profile_sec": action_total,
            "total_sec": value,
            "components": action_components,
            "skipped_actions": skipped_actions,
        },
    )


def group_actions_by_op(actions: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for action in actions:
        op_id = action.get("op_id")
        if not op_id:
            continue
        grouped.setdefault(str(op_id), []).append(action)
    return grouped


def mapping_by_process_code(mappings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for mapping in mappings:
        process_code = mapping.get("process_code")
        if not process_code:
            continue
        result[_key(process_code)] = mapping
    return result


def _collect_action_components(
    op_ids: list[str],
    scenario_actions_by_op: dict[str, list[dict[str, str]]],
    action_timing_catalog: dict[tuple[str, str], ActionTimingEntry],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    components: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for op_id in op_ids:
        for action in scenario_actions_by_op.get(op_id, []):
            asset = action["asset"]
            action_id = action["action"]
            timing = action_timing_catalog.get((_key(asset), _key(action_id)))
            if timing is None:
                skipped.append(_skip(action, "NO_PROFILE_ACTION"))
                continue
            if not timing.can_contribute_to_routing_cycle_time:
                skipped.append(_skip(action, "CAN_NOT_CONTRIBUTE"))
                continue
            if timing.default_duration_sec is None:
                skipped.append(_skip(action, "NO_DURATION"))
                continue
            components.append(
                {
                    "op_id": op_id,
                    "step_id": action.get("step_id", ""),
                    "asset": asset,
                    "gateway": action.get("gateway", ""),
                    "action": timing.action,
                    "duration_sec": timing.default_duration_sec,
                    "time_ownership": timing.time_ownership,
                    "source": "P4RActionTimingProfile",
                }
            )
    return components, skipped


def _action_profile(asset: dict[str, Any]) -> dict[str, Any]:
    submodels = asset.get("submodels") if isinstance(asset.get("submodels"), dict) else {}
    for key, value in submodels.items():
        if key in ACTION_PROFILE_KEYS and isinstance(value, dict):
            return _flatten_submodel_elements(value)
        if str(key).lower() in {item.lower() for item in ACTION_PROFILE_KEYS} and isinstance(
            value, dict
        ):
            return _flatten_submodel_elements(value)
    return {}


def _profile_actions(profile: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    actions = _first_present(profile, "Actions", "actions")
    if isinstance(actions, dict):
        return [
            (str(key), value)
            for key, value in actions.items()
            if isinstance(value, dict) and key not in {"idShort", "modelType"}
        ]
    if isinstance(actions, list):
        result = []
        for item in actions:
            if not isinstance(item, dict):
                continue
            action_name = _first_present(item, "actionId", "sourceAction", "idShort")
            if action_name:
                result.append((str(action_name), item))
        return result
    return []


def _timing_entry(
    asset_name: str, action_name: str, action_data: dict[str, Any]
) -> ActionTimingEntry | None:
    action_id = _first_present(action_data, "actionId", "sourceAction", "idShort") or action_name
    duration = _int_or_none(
        _first_present(action_data, "defaultDurationSec", "durationSec", "duration")
    )
    return ActionTimingEntry(
        asset=asset_name,
        action=str(action_id),
        default_duration_sec=duration,
        time_ownership=str(_first_present(action_data, "timeOwnership") or ""),
        can_contribute_to_routing_cycle_time=_bool_value(
            _first_present(action_data, "canContributeToRoutingCycleTime"),
            default=False,
        ),
    )


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
        model_type = element.get("modelType")
        if isinstance(model_type, dict):
            model_type = model_type.get("name") or model_type.get("modelType")
        value = element.get("value")
        if model_type in {"SubmodelElementCollection", "SubmodelElementList"} or isinstance(
            value, list
        ):
            flattened[str(key)] = _flatten_submodel_elements({"submodelElements": value or []})
        elif "value" in element:
            flattened[str(key)] = value
    return flattened


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
        lower = key.lower()
        matched_key = next((item_key for item_key in data if str(item_key).lower() == lower), None)
        if matched_key is not None and data[matched_key] not in (None, ""):
            return data[matched_key]
    return None


def _skip(action: dict[str, str], reason: str) -> dict[str, Any]:
    return {
        "op_id": action.get("op_id", ""),
        "step_id": action.get("step_id", ""),
        "asset": action.get("asset", ""),
        "gateway": action.get("gateway", ""),
        "action": action.get("action", ""),
        "reason": reason,
    }


def _key(value: Any) -> str:
    return TOKEN_SAFE.sub("", str(value or "")).upper()


def _bool_value(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _int_value(value: Any, default: int) -> int:
    parsed = _int_or_none(value)
    return default if parsed is None else parsed
