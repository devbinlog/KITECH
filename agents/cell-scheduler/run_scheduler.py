"""
스케줄러 실행 스크립트

세 입력 파일을 읽어 스케줄링 후 결과를 samples/cell-scheduler/output/ 에 저장:
  - schedule_result.json
  - gantt_machine.png   (기계별 간트차트)
  - gantt_work_order.png (작업별 간트차트)

실행:
    uv run python agents/cell-scheduler/run_scheduler.py
"""

import dataclasses
import json
import sys
from datetime import datetime
from pathlib import Path

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
workspace  = Path(__file__).parent.parent.parent          # agents-workspace_260409/
src_path   = workspace / "agents" / "cell-scheduler" / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(workspace / "shared"))

INPUT_DIR  = workspace / "samples" / "cell-scheduler" / "input"
OUTPUT_DIR = workspace / "samples" / "cell-scheduler" / "output"

AAS_FILE = INPUT_DIR / "aas_revised.json"
WO_FILE  = INPUT_DIR / "new_work_orders_v3.json"
CFG_FILE = INPUT_DIR / "scheduler_config.json"

import importlib.util as _ilu

def _load_aas_loader():
    spec = _ilu.spec_from_file_location(
        "aas_loader", src_path / "app" / "services" / "aas_loader.py"
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AASLoader

AASLoader = _load_aas_loader()

from solvers import (                                       # noqa: E402
    NcCode, Operation, WorkOrder,
    SolverFactory, SolverType, SolverConfig,
    SchedulerConfig,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

TYPE_ORDER = ["VMC_3AXIS_MASS", "VMC_3AXIS_PALLET", "AMR", "RACK"]


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def build_uri_to_name(loader) -> dict:
    """AAS URI → idShort 역매핑."""
    return {aas["id"]: aas["idShort"]
            for aas in loader.data.get("assetAdministrationShells", [])}


def build_name_map(machines, amrs, loader) -> dict:
    """idShort → AAS URI (머신 + AMR 통합 매핑)."""
    m = {machine.machine_name: machine.machine_id for machine in machines}
    amr_ids = {a.amr_id for a in amrs}
    for aas in loader.data.get("assetAdministrationShells", []):
        if aas["id"] in amr_ids:
            m[aas["idShort"]] = aas["id"]
    return m


def build_name_to_type(machines, amrs, uri_to_name: dict) -> dict:
    """machine_name / AMR idShort → machineType 매핑 (간트 정렬용)."""
    result = {m.machine_name: m.machine_type for m in machines}
    for a in amrs:
        name = uri_to_name.get(a.amr_id, a.amr_id)
        result[name] = "AMR"
    return result


def parse_work_orders(raw_list: list, name_map: dict) -> list:
    """작업지시서 파싱 — compatible_machines만 idShort → AAS URI 해석.

    required_machines는 머신 타입 문자열(VMC_3AXIS_MASS, AMR, RACK 등)로
    작업지시서에 기재되어 있으며, 솔버가 직접 해석한다.
    """
    work_orders = []
    for wo_raw in raw_list:
        operations = []
        for op_raw in wo_raw.get("operations", []):
            # required_machines: 머신 타입 문자열 그대로 유지
            required_machines = op_raw.get("required_machines", [])
            nc_raw = op_raw.get("nc_code", {})
            # compatible_machines: 특정 NC 프로그램을 실행할 수 있는 기계 idShort → AAS URI
            resolved_compat = [
                name_map.get(n, n) for n in nc_raw.get("compatible_machines", [])
            ]
            nc = NcCode(
                program_id=nc_raw.get("program_id", "UNKNOWN"),
                file_path=nc_raw.get("file_path", ""),
                cycle_time_sec=nc_raw.get("cycle_time_sec", 60),
                compatible_machines=resolved_compat,
            )
            operations.append(Operation(
                op_id=op_raw["op_id"],
                op_name=op_raw.get("op_name", ""),
                sequence=op_raw["sequence"],
                predecessors=op_raw.get("predecessors", []),
                required_machines=required_machines,
                setup_id=op_raw.get("setup_id", "DEFAULT"),
                nc_code=nc,
                cycle_time_sec=op_raw.get("cycle_time_sec"),
            ))
        work_orders.append(WorkOrder(
            wo_id=wo_raw["wo_id"],
            product_id=wo_raw.get("product_id", "PROD"),
            product_name=wo_raw.get("product_name", ""),
            order_quantity=wo_raw["order_quantity"],
            release_date=datetime.fromisoformat(wo_raw["release_date"]),
            due_date=datetime.fromisoformat(wo_raw["due_date"]),
            priority=wo_raw.get("priority", 1),
            customer=wo_raw.get("customer", ""),
            operations=operations,
        ))
    return work_orders


# ── JSON 결과 저장 ────────────────────────────────────────────────────────────

def save_schedule_result(result, horizon_start, horizon_end, uri_to_name, out_dir):
    util = {uri_to_name.get(k, k): v for k, v in result.machine_utilization.items()}

    setup_list = [
        {
            "machine_id": uri_to_name.get(s.machine_id, s.machine_id),
            "wo_id": s.wo_id,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration_sec": s.end_time - s.start_time,
        }
        for s in result.setup_intervals
    ]

    tasks_out = []
    for t in result.scheduled_tasks:
        assigned = {
            uri_to_name.get(k, k): uri_to_name.get(v, v)
            for k, v in t.assigned_machines.items()
        }
        tasks_out.append({
            "wo_id": t.wo_id,
            "op_id": t.op_id,
            "op_name": t.op_name,
            "sublot_no": t.sublot_no,
            "lot_no": t.lot_no,
            "quantity": t.quantity,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "duration_sec": t.end_time - t.start_time,
            "setup_time": t.setup_time,
            "amr_transfer_sec": t.amr_transfer_sec,
            "assigned_machines": assigned,
        })

    makespan = result.total_makespan
    out = {
        "status": result.status,
        "makespan_sec": makespan,
        "makespan_min": round(makespan / 60, 2),
        "machine_utilization": util,
        "solve_time_sec": round(result.solve_time_sec, 3),
        "objective_value": result.objective_value,
        "horizon_start": horizon_start.isoformat(),
        "horizon_end": horizon_end.isoformat(),
        "infeasible_wos": result.infeasible_wos,
        "setup_intervals": setup_list,
        "scheduled_tasks": tasks_out,
    }

    path = out_dir / "schedule_result.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  schedule_result.json → {path}")


# ── 기계별 간트차트 ───────────────────────────────────────────────────────────

def plot_gantt_machine(result, uri_to_name, name_to_type, out_dir):
    # 사용된 머신 이름 수집
    used = set()
    for t in result.scheduled_tasks:
        for v in t.assigned_machines.values():
            used.add(uri_to_name.get(v, v))
    for s in result.setup_intervals:
        used.add(uri_to_name.get(s.machine_id, s.machine_id))

    # 표시 순서: TYPE_ORDER 기반 동적 정렬 (index 0 = 하단)
    def _type_key(name):
        t = name_to_type.get(name, "")
        try:
            return TYPE_ORDER.index(t)
        except ValueError:
            return len(TYPE_ORDER)

    order = sorted(used, key=_type_key)
    idx = {m: i for i, m in enumerate(order)}

    # WO 색상
    wo_ids = sorted({t.wo_id for t in result.scheduled_tasks})
    palette = ["#4472C4", "#ED7D31", "#70AD47", "#FFC000"]
    wo_color = {wo: palette[i % len(palette)] for i, wo in enumerate(wo_ids)}

    fig, ax = plt.subplots(figsize=(14, 5))
    H = 0.5  # bar height

    # 셋업 구간
    for s in result.setup_intervals:
        mname = uri_to_name.get(s.machine_id, s.machine_id)
        yi = idx.get(mname)
        if yi is None:
            continue
        dur = s.end_time - s.start_time
        ax.barh(yi, dur, left=s.start_time, height=H,
                color="lightgray", edgecolor="gray", hatch="//", alpha=0.9)
        ax.text(s.start_time + dur / 2, yi, "SETUP",
                ha="center", va="center", fontsize=7, color="gray")

    # 태스크
    for t in result.scheduled_tasks:
        dur = t.end_time - t.start_time
        color = wo_color.get(t.wo_id, "steelblue")
        abbr = t.op_name[:2] if t.op_name else t.op_id
        label = f"{abbr}\nL{t.sublot_no}"
        for v in t.assigned_machines.values():
            mname = uri_to_name.get(v, v)
            yi = idx.get(mname)
            if yi is None:
                continue
            ax.barh(yi, dur, left=t.start_time, height=H,
                    color=color, edgecolor="white", linewidth=0.5)
            if dur > 40:
                ax.text(t.start_time + dur / 2, yi, label,
                        ha="center", va="center", fontsize=6.5,
                        color="white", fontweight="bold")

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_xlabel("시간 (초, horizon 기준)", fontsize=11)
    ax.set_title("기계별 간트차트", fontsize=13, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    legend = [mpatches.Patch(color=wo_color[w], label=w) for w in wo_ids]
    legend.append(mpatches.Patch(facecolor="lightgray", edgecolor="gray",
                                  hatch="//", label="셋업"))
    ax.legend(handles=legend, loc="lower right", fontsize=9)

    plt.tight_layout()
    path = out_dir / "gantt_machine.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  gantt_machine.png    → {path}")


# ── 작업별 간트차트 ───────────────────────────────────────────────────────────

def plot_gantt_work_order(result, out_dir):
    # 행: (wo_id, sublot_no), WO-A01 L1 = 하단, WO-B01 Lmax = 상단
    rows = sorted(
        {(t.wo_id, t.sublot_no) for t in result.scheduled_tasks},
        key=lambda x: (x[0], x[1]),
    )
    row_idx = {r: i for i, r in enumerate(rows)}

    # WO별 op 순서 (sequence 기준)
    wo_op_order: dict = {}
    for t in sorted(result.scheduled_tasks, key=lambda t: (t.wo_id, t.start_time)):
        if t.wo_id not in wo_op_order:
            wo_op_order[t.wo_id] = []
        if t.op_id not in wo_op_order[t.wo_id]:
            wo_op_order[t.wo_id].append(t.op_id)

    op_palette = ["#4472C4", "#ED7D31", "#70AD47"]

    # 범례 수집 (시퀀스 인덱스 → op_name)
    legend_map: dict = {}
    for t in result.scheduled_tasks:
        seq = wo_op_order.get(t.wo_id, [])
        si = seq.index(t.op_id) if t.op_id in seq else 0
        legend_map.setdefault(si, t.op_name)

    fig, ax = plt.subplots(figsize=(14, 6))
    H = 0.5

    for t in result.scheduled_tasks:
        yi = row_idx.get((t.wo_id, t.sublot_no))
        if yi is None:
            continue
        dur = t.end_time - t.start_time
        seq = wo_op_order.get(t.wo_id, [])
        si = seq.index(t.op_id) if t.op_id in seq else 0
        color = op_palette[si % len(op_palette)]

        ax.barh(yi, dur, left=t.start_time, height=H,
                color=color, edgecolor="white", linewidth=0.5)
        if dur > 40:
            ax.text(t.start_time + dur / 2, yi, t.op_name,
                    ha="center", va="center", fontsize=7,
                    color="white", fontweight="bold")

    # Y축 레이블
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{wo}  Lot {lot}" for wo, lot in rows])

    # WO 그룹 구분선
    wo_ids_in_rows = list(dict.fromkeys(wo for wo, _ in rows))
    if len(wo_ids_in_rows) > 1:
        boundary = max(i for i, (wo, _) in enumerate(rows)
                       if wo == wo_ids_in_rows[0])
        ax.axhline(y=boundary + 0.5, color="gray", linestyle="--", linewidth=1)

    ax.set_xlabel("시간 (초, horizon 기준)", fontsize=11)
    ax.set_title("작업별 간트차트", fontsize=13, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    legend = [
        mpatches.Patch(color=op_palette[si % len(op_palette)],
                       label=f"{si + 1}번째 op: {name}")
        for si, name in sorted(legend_map.items())
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=9)

    plt.tight_layout()
    path = out_dir / "gantt_work_order.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  gantt_work_order.png → {path}")


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 설정 로드
    with open(CFG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)
    horizon_start  = datetime.fromisoformat(cfg["horizon"]["start"])
    horizon_end    = datetime.fromisoformat(cfg["horizon"]["end"])
    lot_size       = cfg.get("lot_size", 1)
    amr_transfer   = cfg.get("amr_transfer_time_sec", 60)
    sched_cfg      = SchedulerConfig(lot_size=lot_size, amr_transfer_time_sec=amr_transfer)

    # 솔버 선택 및 설정
    solver_section = cfg.get("solver", {})
    solver_type    = SolverFactory.get_solver_type(solver_section.get("type", "OR_TOOLS"))
    valid_fields   = {f.name for f in dataclasses.fields(SolverConfig)}
    solver_kwargs  = {k: v for k, v in solver_section.items() if k in valid_fields}
    solver_cfg     = SolverConfig(**solver_kwargs)

    print(f"horizon : {horizon_start.date()} ~ {horizon_end.date()}")
    print(f"solver  : {solver_type.value}")
    print(f"lot_size={lot_size}, amr_transfer={amr_transfer}s, time_limit={solver_cfg.time_limit_sec}s\n")

    # AAS 로드
    loader          = AASLoader(str(AAS_FILE))
    machines        = loader.load_machines(horizon_start)
    mtype_params    = loader.load_machine_type_params()
    amrs            = loader.load_amrs()
    uri_to_name     = build_uri_to_name(loader)
    name_map        = build_name_map(machines, amrs, loader)
    name_to_type    = build_name_to_type(machines, amrs, uri_to_name)

    print(f"machines : {[m.machine_name for m in machines]}")
    print(f"AMRs     : {[a.model for a in amrs]}")

    # 작업지시서 로드
    with open(WO_FILE, encoding="utf-8") as f:
        wo_raw = json.load(f)
    work_orders = parse_work_orders(wo_raw, name_map)
    print(f"WOs      : {[wo.wo_id for wo in work_orders]}\n")

    # 스케줄링
    solver = SolverFactory.create_solver(
        solver_type=solver_type,
        work_orders=work_orders,
        machines=machines,
        machine_type_params=mtype_params,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        config=solver_cfg,
        amrs=amrs,
        scheduler_config=sched_cfg,
    )
    result = solver.solve(time_limit_sec=solver_cfg.time_limit_sec)

    print(f"status   : {result.status}")
    print(f"makespan : {result.total_makespan}초 ({result.total_makespan / 60:.1f}분)")
    print(f"tasks    : {len(result.scheduled_tasks)}개")
    print(f"solve    : {result.solve_time_sec:.3f}초\n")

    # 결과 저장
    print("결과 저장 중...")
    save_schedule_result(result, horizon_start, horizon_end, uri_to_name, OUTPUT_DIR)
    plot_gantt_machine(result, uri_to_name, name_to_type, OUTPUT_DIR)
    plot_gantt_work_order(result, OUTPUT_DIR)
    print("\n완료!")


if __name__ == "__main__":
    main()
