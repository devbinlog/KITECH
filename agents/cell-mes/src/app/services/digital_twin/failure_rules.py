"""Failure status rules for P4R preview payload generation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...core.config import settings

CELL_MES_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RULE_CONFIG: dict[str, Any] = {
    "version": "1.0",
    "default": {
        "failureType": "NONE",
        "remainingRepairTime": 0,
    },
    "rules": [
        {
            "id": "disconnected",
            "priority": 10,
            "when": {"isConnected": False},
            "result": {
                "failureType": "DISCONNECTED",
                "remainingRepairTime": 300,
            },
        },
        {
            "id": "cnc_alarm",
            "priority": 30,
            "resourceTypes": ["CNC"],
            "whenAny": [
                {"statusIn": ["ALARM", "ERROR", "FAULT"]},
                {"hasField": ["alarm", "error"]},
            ],
            "result": {
                "failureType": "CNC_ALARM",
                "remainingRepairTime": 600,
            },
        },
        {
            "id": "feeder_robot_error",
            "priority": 30,
            "resourceTypes": ["FEEDER"],
            "whenAny": [
                {"statusIn": ["ALARM", "ERROR", "FAULT"]},
                {"hasField": ["alarm", "error"]},
            ],
            "result": {
                "failureType": "ROBOT_ERROR",
                "remainingRepairTime": 600,
            },
        },
        {
            "id": "qcm_error",
            "priority": 30,
            "resourceTypes": ["QCM", "QUALITY_CONTROL_MACHINE", "QUALITY_CONTROLL_MACHINE"],
            "whenAny": [
                {"statusIn": ["ALARM", "ERROR", "FAULT"]},
                {"hasField": ["alarm", "error"]},
            ],
            "result": {
                "failureType": "QCM_ERROR",
                "remainingRepairTime": 600,
            },
        },
        {
            "id": "machine_error",
            "priority": 50,
            "resourceTypes": ["MACHINE"],
            "whenAny": [
                {"statusIn": ["ALARM", "ERROR", "FAULT"]},
                {"hasField": ["alarm", "error"]},
            ],
            "result": {
                "failureType": "UNKNOWN_ERROR",
                "remainingRepairTime": 300,
            },
        },
    ],
}


@dataclass(frozen=True)
class P4RFailureStatus:
    """Normalized failure status for one P4R machine instance."""

    failure_type: str
    remaining_repair_time: int
    matched_rule: str
    raw_message: str = ""
    raw_status: dict[str, Any] = field(default_factory=dict)

    def as_trace(self, asset_id: str, resource_type: str) -> dict[str, Any]:
        return {
            "asset_id": asset_id,
            "resource_type": resource_type,
            "failureType": self.failure_type,
            "remainingRepairTime": self.remaining_repair_time,
            "matchedRule": self.matched_rule,
            "rawMessage": self.raw_message,
            "rawStatus": self.raw_status,
        }


@dataclass(frozen=True)
class P4RFailureRuleSet:
    """Rule set loaded from JSON config with safe fallback defaults."""

    default_failure_type: str
    default_remaining_repair_time: int
    rules: list[dict[str, Any]]
    source: str
    warnings: list[str] = field(default_factory=list)

    def interpret(
        self,
        *,
        asset_id: str,
        resource_type: str,
        status: dict[str, Any],
    ) -> P4RFailureStatus:
        raw_status = status if isinstance(status, dict) else {}
        normalized_resource = resource_type.upper()
        for rule in self.rules:
            if _rule_matches(rule, normalized_resource, raw_status):
                result = rule["result"]
                return P4RFailureStatus(
                    failure_type=str(result["failureType"]),
                    remaining_repair_time=_int_value(result.get("remainingRepairTime"), 0),
                    matched_rule=str(rule["id"]),
                    raw_message=_raw_message(raw_status),
                    raw_status=raw_status,
                )
        return P4RFailureStatus(
            failure_type=self.default_failure_type,
            remaining_repair_time=self.default_remaining_repair_time,
            matched_rule="default",
            raw_message=_raw_message(raw_status),
            raw_status=raw_status,
        )


def load_p4r_failure_rules(path: str | Path | None = None) -> P4RFailureRuleSet:
    """Load P4R failure rules from JSON, falling back to built-in defaults."""

    configured_path = path or settings.P4R_FAILURE_RULES_PATH
    resolved = _resolve_config_path(configured_path)
    warnings: list[str] = []
    if resolved.exists():
        try:
            with resolved.open("r", encoding="utf-8") as handle:
                config = json.load(handle)
            return _build_rule_set(config, source=str(resolved), warnings=warnings)
        except (OSError, ValueError, TypeError) as exc:
            warnings.append(f"P4R failure rule 파일을 읽지 못해 기본 rule을 사용합니다: {exc}")
    else:
        warnings.append(f"P4R failure rule 파일을 찾지 못해 기본 rule을 사용합니다: {resolved}")
    return _build_rule_set(DEFAULT_RULE_CONFIG, source="built-in-default", warnings=warnings)


def _resolve_config_path(path: str | Path) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        return raw
    candidates = [Path.cwd() / raw, CELL_MES_ROOT / raw]
    parts = raw.parts
    if len(parts) >= 2 and parts[0] == "agents" and parts[1] == "cell-mes":
        candidates.append(CELL_MES_ROOT / Path(*parts[2:]))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _build_rule_set(
    config: dict[str, Any],
    *,
    source: str,
    warnings: list[str],
) -> P4RFailureRuleSet:
    if not isinstance(config, dict):
        warnings.append("P4R failure rule 설정이 객체가 아니어서 기본 rule을 사용합니다")
        return _build_rule_set(DEFAULT_RULE_CONFIG, source="built-in-default", warnings=warnings)

    default = config.get("default") if isinstance(config.get("default"), dict) else {}
    default_failure_type = str(default.get("failureType") or "NONE")
    default_repair_time = _int_value(default.get("remainingRepairTime"), 0)
    raw_rules = config.get("rules") if isinstance(config.get("rules"), list) else []
    rules: list[dict[str, Any]] = []
    for index, rule in enumerate(raw_rules):
        normalized = _normalize_rule(rule, index)
        if normalized:
            rules.append(normalized)
        else:
            warnings.append(f"P4R failure rule #{index + 1} 형식이 올바르지 않아 무시합니다")
    rules.sort(key=lambda item: (item["priority"], item["order"]))
    return P4RFailureRuleSet(
        default_failure_type=default_failure_type,
        default_remaining_repair_time=default_repair_time,
        rules=rules,
        source=source,
        warnings=warnings,
    )


def _normalize_rule(rule: Any, index: int) -> dict[str, Any] | None:
    if not isinstance(rule, dict):
        return None
    result = rule.get("result")
    if not isinstance(result, dict) or not result.get("failureType"):
        return None
    if not any(
        isinstance(rule.get(key), value_type)
        for key, value_type in (("when", dict), ("whenAny", list))
    ):
        return None
    return {
        "id": str(rule.get("id") or f"rule_{index + 1}"),
        "priority": _int_value(rule.get("priority"), 1000),
        "order": index,
        "resourceTypes": [str(item).upper() for item in rule.get("resourceTypes") or []],
        "when": rule.get("when") if isinstance(rule.get("when"), dict) else None,
        "whenAny": rule.get("whenAny") if isinstance(rule.get("whenAny"), list) else None,
        "result": {
            "failureType": str(result["failureType"]),
            "remainingRepairTime": _int_value(result.get("remainingRepairTime"), 0),
        },
    }


def _rule_matches(rule: dict[str, Any], resource_type: str, status: dict[str, Any]) -> bool:
    resource_types = rule.get("resourceTypes") or []
    if resource_types and resource_type not in resource_types:
        return False
    when = rule.get("when")
    if isinstance(when, dict) and not _condition_matches(when, status):
        return False
    when_any = rule.get("whenAny")
    if isinstance(when_any, list) and not any(
        _condition_matches(condition, status)
        for condition in when_any
        if isinstance(condition, dict)
    ):
        return False
    return True


def _condition_matches(condition: dict[str, Any], status: dict[str, Any]) -> bool:
    handled_keys = {"isConnected", "statusIn", "hasField", "field", "equals", "in", "containsAny"}

    if "isConnected" in condition:
        actual_is_connected = _field_value(status, "isConnected")
        if actual_is_connected is None or _bool_value(actual_is_connected) != _bool_value(
            condition["isConnected"]
        ):
            return False

    if "statusIn" in condition:
        allowed = {_norm_text(value) for value in _as_list(condition["statusIn"])}
        if not any(candidate in allowed for candidate in _status_candidates(status)):
            return False

    if "hasField" in condition and not any(
        _has_meaningful_value(status, field_name) for field_name in _as_list(condition["hasField"])
    ):
        return False

    if "field" in condition:
        value = _field_value(status, str(condition["field"]))
        if "equals" in condition and _norm_text(value) != _norm_text(condition["equals"]):
            return False
        if "in" in condition:
            allowed = {_norm_text(item) for item in _as_list(condition["in"])}
            if _norm_text(value) not in allowed:
                return False
        if "containsAny" in condition and not _contains_any(value, condition["containsAny"]):
            return False

    if "containsAny" in condition and "field" not in condition:
        if not _contains_any(status, condition["containsAny"]):
            return False

    for key, expected in condition.items():
        if key in handled_keys:
            continue
        actual = _field_value(status, key)
        if isinstance(expected, list):
            if _norm_text(actual) not in {_norm_text(item) for item in expected}:
                return False
        elif _norm_text(actual) != _norm_text(expected):
            return False
    return True


def _field_value(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        if part in current:
            current = current[part]
            continue
        lower = part.lower()
        matched_key = next((key for key in current if str(key).lower() == lower), None)
        current = current.get(matched_key) if matched_key is not None else None
    return current


def _has_meaningful_value(data: dict[str, Any], path: Any) -> bool:
    value = _field_value(data, str(path))
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "none", "null", "ok", "normal"}
    return value not in (None, "", False, 0)


def _status_candidates(status: dict[str, Any]) -> set[str]:
    candidates = {
        _norm_text(_field_value(status, key))
        for key in ("status", "state", "currentStatus", "result")
        if _field_value(status, key) not in (None, "")
    }
    return {candidate for candidate in candidates if candidate}


def _raw_message(status: dict[str, Any]) -> str:
    for key in ("alarm_message", "alarmMessage", "message", "errorMessage", "error", "alarm"):
        value = _field_value(status, key)
        if value not in (None, ""):
            return str(value)
    return ""


def _contains_any(value: Any, candidates: Any) -> bool:
    text = (
        json.dumps(value, ensure_ascii=False).lower()
        if isinstance(value, (dict, list))
        else str(value).lower()
    )
    return any(str(candidate).lower() in text for candidate in _as_list(candidates))


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _norm_text(value: Any) -> str:
    return str(value or "").strip().upper()


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _int_value(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
