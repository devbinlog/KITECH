"""Scenario YAML helpers for digital twin payload generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CELL_MES_ROOT = Path(__file__).resolve().parents[4]


def resolve_scenario_path(file_path: str) -> Path:
    """Resolve a Scenario.file_path value against common Cell-MES locations."""
    raw = Path(file_path)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend(
            [
                Path.cwd() / raw,
                CELL_MES_ROOT / raw,
            ]
        )
        parts = raw.parts
        if parts and parts[0] == "cell-mes":
            candidates.append(CELL_MES_ROOT / Path(*parts[1:]))
        candidates.append(CELL_MES_ROOT / "data" / raw.name)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else raw


def load_scenario_yaml(file_path: str) -> tuple[dict[str, Any], Path]:
    """Load scenario YAML and return both parsed content and resolved path."""
    resolved = resolve_scenario_path(file_path)
    with resolved.open("r", encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}
    if not isinstance(content, dict):
        raise ValueError(f"Scenario YAML must be an object: {resolved}")
    return content, resolved


def scenario_assets(content: dict[str, Any]) -> list[dict[str, str]]:
    """Return scenario assets as [{id, name}], dropping malformed entries."""
    assets = content.get("assets") or []
    if not isinstance(assets, list):
        return []
    result: list[dict[str, str]] = []
    for item in assets:
        if not isinstance(item, dict):
            continue
        asset_id = item.get("id")
        asset_name = item.get("name")
        if asset_id and asset_name:
            result.append({"id": str(asset_id), "name": str(asset_name)})
    return result


def scenario_operation_ids(content: dict[str, Any]) -> list[str]:
    """Return op_id values in first-seen order for trace/debug metadata."""
    seen: set[str] = set()
    operations: list[str] = []
    steps = content.get("steps") or []
    if not isinstance(steps, list):
        return operations
    for step in steps:
        if not isinstance(step, dict):
            continue
        op_id = step.get("op_id")
        if op_id and str(op_id) not in seen:
            seen.add(str(op_id))
            operations.append(str(op_id))
    return operations


def p4r_process_mappings(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Return explicit P4R process mappings from scenario YAML."""

    mappings = content.get("p4r_process_mapping") or content.get("p4rProcessMapping") or []
    if not isinstance(mappings, list):
        return []

    result: list[dict[str, Any]] = []
    for item in mappings:
        if not isinstance(item, dict):
            continue
        process_code = item.get("process_code") or item.get("processCode")
        op_ids = item.get("op_ids") or item.get("opIds") or []
        if isinstance(op_ids, str):
            op_ids = [op_ids]
        if not process_code or not isinstance(op_ids, list) or not op_ids:
            continue
        result.append(
            {
                "process_code": str(process_code),
                "op_ids": [str(op_id) for op_id in op_ids if op_id],
                "time_mode": str(item.get("time_mode") or item.get("timeMode") or "ROUTING_CYCLE"),
                "routing_cycle_time_role": (
                    item.get("routing_cycle_time_role") or item.get("routingCycleTimeRole")
                ),
            }
        )
    return result


def scenario_step_actions(
    content: dict[str, Any],
    asset_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Resolve scenario step actions into asset/action records for timing lookup."""

    assets_by_id = {
        row["id"]: row["name"] for row in asset_rows if row.get("id") and row.get("name")
    }
    active_aliases: dict[str, str] = {}
    result: list[dict[str, str]] = []
    steps = content.get("steps") or []
    if not isinstance(steps, list):
        return result

    for step in steps:
        if not isinstance(step, dict):
            continue
        _apply_acquire_bindings(step.get("acquire"), active_aliases, assets_by_id)
        parsed = _parse_action(step.get("action"), active_aliases, assets_by_id)
        if parsed and step.get("op_id"):
            result.append(
                {
                    "step_id": str(step.get("id") or ""),
                    "op_id": str(step["op_id"]),
                    "asset": parsed["asset"],
                    "gateway": parsed["gateway"],
                    "action": parsed["action"],
                    "raw_action": str(step.get("action") or ""),
                }
            )
    return result


def _apply_acquire_bindings(
    acquire: Any,
    active_aliases: dict[str, str],
    assets_by_id: dict[str, str],
) -> None:
    if not isinstance(acquire, dict):
        return
    for alias, candidates in acquire.items():
        if not isinstance(candidates, list) or not candidates:
            continue
        asset_id = str(candidates[0])
        active_aliases[str(alias)] = assets_by_id.get(asset_id, asset_id)


def _parse_action(
    action: Any,
    active_aliases: dict[str, str],
    assets_by_id: dict[str, str],
) -> dict[str, str] | None:
    if not isinstance(action, str) or action.startswith("@"):
        return None
    parts = [part for part in action.split("/") if part]
    if len(parts) < 4:
        return None
    asset_ref = parts[0]
    asset = _resolve_asset_ref(asset_ref, active_aliases, assets_by_id)
    if not asset:
        return None
    return {
        "asset": asset,
        "gateway": parts[1],
        "action": parts[-1],
    }


def _resolve_asset_ref(
    asset_ref: str,
    active_aliases: dict[str, str],
    assets_by_id: dict[str, str],
) -> str | None:
    match = asset_ref.strip()
    if match.startswith("{{") and match.endswith("}}"):
        inner = match[2:-2].strip()
        prefix = "acq."
        if inner.startswith(prefix):
            return active_aliases.get(inner[len(prefix) :])
        return None
    return assets_by_id.get(match, match)
