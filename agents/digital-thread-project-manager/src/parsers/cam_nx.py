"""NX CAM JSON parser."""

from typing import Any


def pick_nx_ops(cam_json: Any) -> list[dict[str, Any]]:
    """
    Extract operation list from NX CAM JSON.

    NX structure: {"key": {...}, "values": [...operations...]}
    """
    if isinstance(cam_json, dict):
        v = cam_json.get("values")
        if isinstance(v, list):
            return v

    if isinstance(cam_json, list):
        return cam_json
    if not isinstance(cam_json, dict):
        return [cam_json]

    for k in ("operations", "ops", "toolpaths", "steps", "items"):
        v = cam_json.get(k)
        if isinstance(v, list):
            return v

    return [cam_json]
