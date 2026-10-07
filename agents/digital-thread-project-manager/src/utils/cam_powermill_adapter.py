# src/utils/cam_powermill_adapter.py
from typing import Any, Dict, List
from fastapi import HTTPException, UploadFile
import os, json

__all__ = ["pick_powermill_ops"]


def pick_powermill_ops(cam_json: Any) -> List[Dict[str, Any]]:
    """
    PowerMILL 계열: 보통 파일 당 1개의 toolpath/operation.
    그래도 프로젝트에 따라 리스트일 수 있어 방어적으로 파싱.
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


# utils/cam_order_powermill.py


def _canon(name: str) -> str:
    """파일명 정규화: 경로 제거, 소문자, 확장자 제거, 트림"""
    base = os.path.basename(name.strip())
    root, _ext = os.path.splitext(base)
    return root.lower()


def _parse_ops_order_string(ops_order: str) -> List[str]:
    """
    ops_order는 보통 "fileA.json, fileB.json, fileC.json" 형태(콤마 구분).
    - JSON 배열 문자열 '["fileA.json","fileB.json"]' 형태도 허용.
    - 확장자 생략/대소문자 섞여도 OK (정규화해서 비교).
    """
    s = (ops_order or "").strip()
    if not s:
        raise HTTPException(
            status_code=422, detail="ops_order is required for powermill."
        )
    # JSON 배열도 허용
    if s.startswith("["):
        try:
            arr = json.loads(s)
            if not isinstance(arr, list) or not arr:
                raise ValueError()
            return [str(x) for x in arr]
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid ops_order JSON array.")
    # 콤마 구분 기본
    parts = [p for p in (x.strip() for x in s.split(",")) if p]
    if not parts:
        raise HTTPException(
            status_code=422, detail="ops_order must list filenames separated by commas."
        )
    return parts


def reorder_powermill_files_by_order(
    cam_files: List[UploadFile], ops_order: str
) -> List[UploadFile]:
    """
    업로드된 cam_files를 ops_order의 파일명 순서대로 재배열.
    - 파일명 매칭은 basename(확장자 무시), case-insensitive
    - 중복 파일명/누락/개수 불일치 시 422
    """
    want_names = _parse_ops_order_string(ops_order)
    want_keys = [_canon(n) for n in want_names]

    # 업로드 파일 인덱스 빌드
    slot: Dict[str, Any] = {}
    seen_upload_keys: Dict[str, int] = {}
    for f in cam_files:
        name_val = f.filename if hasattr(f, "filename") else os.path.basename(str(f))
        key = _canon(name_val or "")
        if not key:
            raise HTTPException(
                status_code=422, detail="Uploaded CAM file without a valid filename."
            )
        if key in slot:
            # 같은 이름(확장자 무시) 중복 업로드는 모호 → 금지
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate uploaded filename (ignoring extension): {name_val}",
            )
        slot[key] = f
        seen_upload_keys[key] = 1

    # ops_order 개수/멤버 검증
    if len(want_keys) != len(cam_files):
        raise HTTPException(
            status_code=422,
            detail=f"ops_order count ({len(want_keys)}) must equal uploaded files count ({len(cam_files)}).",
        )

    # 재배열 & 존재/중복 검사
    ordered: List[UploadFile] = []
    used: Dict[str, int] = {}
    for key in want_keys:
        if key not in slot:
            # 없는 파일명을 지목
            raise HTTPException(
                status_code=422,
                detail=f"ops_order references a file that was not uploaded: '{key}'",
            )
        if used.get(key):
            raise HTTPException(
                status_code=422,
                detail=f"ops_order contains a duplicate entry: '{key}'",
            )
        ordered.append(slot[key])
        used[key] = 1

    return ordered
