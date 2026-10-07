# src/utils/cam_nx_adapter.py
from typing import Any, Dict, List

__all__ = ["pick_nx_ops"]


def pick_nx_ops(cam_json: Any) -> List[Dict[str, Any]]:
    """
    NX CAM JSON 구조:
    {
      "key": {...},
      "values": [ {...}, {...}, ... ]
    }
    → values가 operation 리스트이다.

    기존 NX 구버전 JSON도 호환되도록 fallback 로직도 유지.
    """

    # 1) NX 최신 구조: values가 실제 operation 리스트
    if isinstance(cam_json, dict):
        v = cam_json.get("values")
        if isinstance(v, list):
            return v

    # 2) 기존 로직 그대로 유지 (구버전 호환)
    if isinstance(cam_json, list):
        return cam_json
    if not isinstance(cam_json, dict):
        return [cam_json]

    for k in ("operations", "ops", "toolpaths", "steps", "items"):
        v = cam_json.get(k)
        if isinstance(v, list):
            return v

    # 3) 못 찾으면 단일 op로 처리
    return [cam_json]
