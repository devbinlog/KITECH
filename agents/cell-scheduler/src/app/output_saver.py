"""output_saver.py — 스케줄링 결과를 JSON + PNG로 저장하는 유틸리티.

저장 경로: <workspace_root>/samples/cell-scheduler/output/
파일 규칙:
  schedule_result_{solver_type}.json  — 솔버별 최신 결과 JSON
  gantt_{solver_type}.png             — 솔버별 최신 간트 차트 (기계별, 초 단위 X축)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

# workspace_root/samples/cell-scheduler/output/
_OUTPUT_DIR = Path(__file__).parents[4] / "samples" / "cell-scheduler" / "output"

_TYPE_ORDER = ["VMC_3AXIS_MASS", "VMC_3AXIS_PALLET", "AMR", "RACK"]
_WO_PALETTE = ["#4472C4", "#ED7D31", "#70AD47", "#FFC000"]


def _ensure_output_dir() -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _OUTPUT_DIR


def _save_json(result_dict: Dict[str, Any], solver_type: str, out_dir: Path) -> Path:
    path = out_dir / f"schedule_result_{solver_type}.json"
    path.write_text(json.dumps(result_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _save_gantt_png(result_dict: Dict[str, Any], solver_type: str, out_dir: Path) -> Path | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.patches as mpatches
        import matplotlib.pyplot as plt
        plt.rcParams["font.family"] = "Malgun Gothic"
        plt.rcParams["axes.unicode_minus"] = False
    except ImportError:
        logger.warning("matplotlib not installed — skipping PNG save")
        return None

    tasks: List[Dict] = result_dict.get("scheduled_tasks") or []
    setup_intervals: List[Dict] = result_dict.get("setup_intervals") or []
    name_map: Dict[str, str] = result_dict.get("machine_name_map") or {}

    if not tasks:
        logger.warning("No scheduled_tasks — skipping PNG save")
        return None

    # machine_id → machine_type 매핑 (정렬용)
    mid_to_type: Dict[str, str] = {}
    for t in tasks:
        for mtype, mid in t.get("assigned_machines", {}).items():
            mid_to_type[mid] = mtype

    # 사용된 machine_id 수집
    used: Set[str] = set()
    for t in tasks:
        used.update(t.get("assigned_machines", {}).values())
    for s in setup_intervals:
        mid = s.get("machine_id", "")
        if mid:
            used.add(mid)

    def _type_key(mid: str) -> int:
        mtype = mid_to_type.get(mid, "")
        try:
            return _TYPE_ORDER.index(mtype)
        except ValueError:
            return len(_TYPE_ORDER)

    order = sorted(used, key=_type_key)
    # machine_name_map이 있으면 이름으로, 없으면 machine_id 그대로
    labels = [name_map.get(mid, mid) for mid in order]
    idx = {m: i for i, m in enumerate(order)}
    n = len(order)

    # WO별 색상
    wo_ids = sorted({t.get("wo_id", "") for t in tasks})
    wo_color = {wo: _WO_PALETTE[i % len(_WO_PALETTE)] for i, wo in enumerate(wo_ids)}

    fig, ax = plt.subplots(figsize=(14, max(4, n * 0.9 + 2)))
    H = 0.5

    # 셋업 구간
    for s in setup_intervals:
        mid = s.get("machine_id", "")
        yi = idx.get(mid)
        if yi is None:
            continue
        st = s.get("start_time", 0)
        dur = s.get("duration_sec", 0) or (s.get("end_time", 0) - st)
        if dur <= 0:
            continue
        ax.barh(yi, dur, left=st, height=H,
                color="lightgray", edgecolor="gray", hatch="//", alpha=0.9)
        ax.text(st + dur / 2, yi, "SETUP",
                ha="center", va="center", fontsize=7, color="gray")

    # 태스크
    for t in tasks:
        st = t.get("start_time", 0)
        et = t.get("end_time", 0)
        dur = et - st
        if dur <= 0:
            continue
        wo_id = t.get("wo_id", "")
        color = wo_color.get(wo_id, "steelblue")
        op_name = t.get("op_name", "") or t.get("op_id", "")
        sublot_no = t.get("sublot_no", 1)
        abbr = op_name[:2] if op_name else ""
        label = f"{abbr}\nL{sublot_no}"

        for mid in t.get("assigned_machines", {}).values():
            yi = idx.get(mid)
            if yi is None:
                continue
            ax.barh(yi, dur, left=st, height=H,
                    color=color, edgecolor="white", linewidth=0.5)
            if dur > 40:
                ax.text(st + dur / 2, yi, label,
                        ha="center", va="center", fontsize=6.5,
                        color="white", fontweight="bold")

    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_xlabel("시간 (초, horizon 기준)", fontsize=11)
    ax.set_title(f"기계별 간트차트 — {solver_type}", fontsize=13, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    legend = [mpatches.Patch(color=wo_color[w], label=w) for w in wo_ids]
    legend.append(mpatches.Patch(facecolor="lightgray", edgecolor="gray",
                                  hatch="//", label="셋업"))
    ax.legend(handles=legend, loc="lower right", fontsize=9)

    plt.tight_layout()
    path = out_dir / f"gantt_{solver_type}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def save_schedule_output(result_dict: Dict[str, Any], solver_type: str) -> None:
    """스케줄링 결과를 JSON + PNG로 저장한다. 오류는 로그만 남기고 무시."""
    try:
        out_dir = _ensure_output_dir()

        json_path = _save_json(result_dict, solver_type, out_dir)
        logger.info("Saved schedule JSON: %s", json_path)

        png_path = _save_gantt_png(result_dict, solver_type, out_dir)
        if png_path:
            logger.info("Saved Gantt PNG: %s", png_path)

    except Exception:
        logger.exception("Failed to save schedule output (non-fatal)")
