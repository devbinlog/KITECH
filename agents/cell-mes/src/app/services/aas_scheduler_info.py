"""Helpers for extracting schedulerInfo from AAS payloads."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Optional


LIST_KEYS = {"breaks", "accessibleMachines"}
SEQ = re.compile(r"^(.*)_(\d+)$")


def _model_type(element: Dict[str, Any]) -> Optional[str]:
    model_type = element.get("modelType")
    if isinstance(model_type, dict):
        return model_type.get("name") or model_type.get("modelType")
    return model_type


def _cast_value(value: Any, value_type: Optional[str]) -> Any:
    if value is None:
        return None

    normalized_type = (value_type or "").lower()
    try:
        if normalized_type.endswith(("xs:int", "xs:integer", "#int", "#integer")):
            return int(value)
        if normalized_type.endswith(("xs:double", "xs:float", "xs:decimal", "#double", "#float", "#decimal")):
            return float(value)
        if normalized_type.endswith(("xs:boolean", "#boolean")):
            return str(value).lower() in {"true", "1"}
    except (TypeError, ValueError):
        return value
    return value


def _element_children(element: Dict[str, Any]) -> list[Dict[str, Any]]:
    children = element.get("value") or []
    if isinstance(children, dict):
        return list(children.values())
    if isinstance(children, list):
        return [child for child in children if isinstance(child, dict)]
    return []


def parse_aas_element(element: Dict[str, Any]) -> Any:
    """Parse one AAS submodel element into a metadata-free JSON value."""
    model_type = _model_type(element)
    id_short = element.get("idShort")

    if model_type == "Property":
        return _cast_value(element.get("value"), element.get("valueType"))

    if model_type == "SubmodelElementList":
        return [parse_aas_element(child) for child in _element_children(element)]

    if model_type == "SubmodelElementCollection":
        children = _element_children(element)
        is_list = id_short in LIST_KEYS or (
            bool(children) and all(SEQ.match(str(child.get("idShort", ""))) for child in children)
        )
        if is_list:
            return [parse_aas_element(child) for child in children]
        return {
            child.get("idShort"): parse_aas_element(child)
            for child in children
            if child.get("idShort") is not None
        }

    return element.get("value")


def flatten_scheduler_info(scheduler_info: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten an AAS schedulerInfo submodel into Equipment.spec_data shape."""
    return {
        element.get("idShort"): parse_aas_element(element)
        for element in scheduler_info.get("submodelElements", [])
        if isinstance(element, dict) and element.get("idShort") is not None
    }


def _normalize_flattened_value(key: Optional[str], value: Any) -> Any:
    """Normalize middleware's already-flattened schedulerInfo values.

    Some middleware responses already remove AAS metadata but still represent
    list-like collections as {"break_0": {...}} or {"machine_0": "..."}.
    Apply the same list/dict rules from AAS_FLATTENING_RULES.md to that shape.
    """
    if isinstance(value, list):
        return [_normalize_flattened_value(None, item) for item in value]
    if not isinstance(value, dict):
        return value

    items = list(value.items())
    is_list = key in LIST_KEYS or (
        bool(items) and all(SEQ.match(str(item_key)) for item_key, _ in items)
    )
    if is_list:
        return [_normalize_flattened_value(None, item_value) for _, item_value in items]
    return {
        item_key: _normalize_flattened_value(item_key, item_value)
        for item_key, item_value in items
    }


def normalize_flattened_scheduler_info(scheduler_info: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an already-flattened schedulerInfo dict from middleware."""
    return {
        key: _normalize_flattened_value(key, value)
        for key, value in scheduler_info.items()
        if key not in {"idShort", "modelType", "semanticId", "description", "qualifiers"}
    }


def extract_scheduler_info(asset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the schedulerInfo submodel from a normalized or legacy asset dict."""
    direct = asset.get("schedulerInfo")
    if isinstance(direct, dict):
        return direct

    submodels = asset.get("submodels")
    if isinstance(submodels, dict):
        scheduler_info = submodels.get("schedulerInfo")
        if isinstance(scheduler_info, dict):
            return scheduler_info
        for submodel in submodels.values():
            if isinstance(submodel, dict) and submodel.get("idShort") == "schedulerInfo":
                return submodel
    elif isinstance(submodels, list):
        for submodel in submodels:
            if isinstance(submodel, dict) and submodel.get("idShort") == "schedulerInfo":
                return submodel

    return None


def scheduler_spec_from_asset(asset: Dict[str, Any]) -> Dict[str, Any]:
    scheduler_info = extract_scheduler_info(asset)
    if not scheduler_info:
        return {}
    if isinstance(scheduler_info.get("submodelElements"), list):
        return flatten_scheduler_info(scheduler_info)
    return normalize_flattened_scheduler_info(scheduler_info)


def _ref_value(ref: Dict[str, Any]) -> Optional[str]:
    keys = ref.get("keys") or []
    if keys and isinstance(keys[0], dict):
        return keys[0].get("value")
    return ref.get("value")


def normalize_aas_assets_response(data: Any) -> list[Dict[str, Any]]:
    """Normalize middleware /api/aas/view responses into per-AAS asset dicts.

    Supports both the legacy list format used by sync tests and full AAS
    environments shaped as {"assetAdministrationShells": [...], "submodels": [...]}.
    Full AAS responses are resolved so asset["submodels"] is a dict keyed by
    submodel idShort, including schedulerInfo when present.
    """
    if isinstance(data, dict) and "data" in data:
        return normalize_aas_assets_response(data["data"])

    if isinstance(data, list):
        return [asset for asset in data if isinstance(asset, dict)]

    if not isinstance(data, dict):
        return []

    shells = data.get("assetAdministrationShells")
    submodels = data.get("submodels")
    if not isinstance(shells, list) or not isinstance(submodels, list):
        return []

    submodel_by_id = {
        submodel.get("id"): submodel
        for submodel in submodels
        if isinstance(submodel, dict) and submodel.get("id")
    }

    normalized_assets: list[Dict[str, Any]] = []
    for shell in shells:
        if not isinstance(shell, dict):
            continue
        resolved_submodels: Dict[str, Dict[str, Any]] = {}
        for ref in _iter_submodel_refs(shell.get("submodels")):
            submodel_id = _ref_value(ref)
            submodel = submodel_by_id.get(submodel_id or "")
            if isinstance(submodel, dict) and submodel.get("idShort"):
                resolved_submodels[submodel["idShort"]] = submodel

        asset = dict(shell)
        asset["submodels"] = resolved_submodels
        normalized_assets.append(asset)

    return normalized_assets


def _iter_submodel_refs(refs: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict):
                yield ref
    elif isinstance(refs, dict):
        for ref in refs.values():
            if isinstance(ref, dict):
                yield ref
