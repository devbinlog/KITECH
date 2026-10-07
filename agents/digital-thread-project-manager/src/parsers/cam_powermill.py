"""PowerMill CAM JSON parser."""

from typing import Any


def pick_powermill_ops(cam_json: Any) -> list[dict[str, Any]]:
    """
    Extract operation list from PowerMill CAM JSON.

    PowerMill typically has one toolpath per file.
    """
    if isinstance(cam_json, list):
        return cam_json
    if not isinstance(cam_json, dict):
        return [cam_json]

    for k in ("operation", "toolpath", "items"):
        v = cam_json.get(k)
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            return [v]

    return [cam_json]
