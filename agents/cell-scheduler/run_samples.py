"""샘플 데이터로 5개 솔버 모두 재실행 + JSON/Gantt PNG 저장.

수정 후 출력 갱신용 일회성 드라이버.
실행: python run_samples.py
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from solvers import (  # noqa: E402
    SolverFactory, SolverType, SchedulerConfig,
    WorkOrder, Operation, NcCode,
)
import importlib.util  # noqa: E402

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# services/__init__.py가 SchedulerService를 통해 상대 임포트를 트리거하므로
# 모듈 파일을 직접 로드해 우회한다.
_aas_mod = _load_module("aas_loader_direct", ROOT / "src/app/services/aas_loader.py")
AASLoader = _aas_mod.AASLoader
_out_mod = _load_module("output_saver_direct", ROOT / "src/app/output_saver.py")
save_schedule_output = _out_mod.save_schedule_output

SAMPLES_DIR = ROOT.parents[1] / "samples" / "cell-scheduler"
INPUT_DIR = SAMPLES_DIR / "input"


def parse_work_orders(path: Path) -> list[WorkOrder]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    wos = []
    for w in raw:
        ops = []
        for o in w["operations"]:
            nc = o.get("nc_code") or {}
            nc_code = NcCode(
                program_id=nc.get("program_id", ""),
                file_path=nc.get("file_path", ""),
                cycle_time_sec=nc.get("cycle_time_sec", 0),
                cycle_time_confidence=nc.get("cycle_time_confidence", 0.9),
                tool_list=nc.get("tool_list", []),
                tool_change_count=nc.get("tool_change_count", 0),
                compatible_machines=nc.get("compatible_machines", []),
            )
            ops.append(Operation(
                op_id=o["op_id"],
                op_name=o.get("op_name", ""),
                sequence=o["sequence"],
                predecessors=o.get("predecessors", []),
                required_machines=o.get("required_machines", []),
                setup_id=o.get("setup_id", ""),
                nc_code=nc_code,
                cycle_time_sec=o.get("cycle_time_sec"),
            ))
        wos.append(WorkOrder(
            wo_id=w["wo_id"],
            product_id=w["product_id"],
            product_name=w["product_name"],
            order_quantity=w["order_quantity"],
            due_date=datetime.fromisoformat(w["due_date"]),
            priority=w["priority"],
            release_date=datetime.fromisoformat(w["release_date"]),
            customer=w.get("customer", ""),
            operations=ops,
        ))
    return wos


def build_result_dict(result, gantt_data, quality, machine_name_map, solver_info, request_id):
    """scheduler_service._format_response와 동등한 출력 구조."""
    tasks = []
    for t in result.scheduled_tasks:
        tasks.append({
            "wo_id": t.wo_id,
            "op_id": t.op_id,
            "machine_id": t.machine_id,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "quantity": t.quantity,
            "setup_time": t.setup_time,
            "sublot_no": t.sublot_no,
            "lot_no": t.lot_no,
            "op_name": t.op_name,
            "assigned_machines": t.assigned_machines,
            "amr_transfer_sec": t.amr_transfer_sec,
        })
    return {
        "status": result.status,
        "scheduled_tasks": tasks,
        "statistics": {
            "total_tasks": len(tasks),
            "makespan_seconds": result.total_makespan,
            "makespan_hours": round(result.total_makespan / 3600, 2),
            "machine_utilization": result.machine_utilization,
            "bottleneck_machines": result.bottleneck_machines,
            "solve_time_sec": round(result.solve_time_sec, 2),
            "objective_value": result.objective_value,
            "weighted_tardiness_sec": getattr(result, "weighted_tardiness_sec", 0),
            "weighted_completion_sec": getattr(result, "weighted_completion_sec", 0),
            "total_setup_sec": getattr(result, "total_setup_sec", 0),
        },
        "quality_metrics": quality,
        "gantt_data": gantt_data,
        "solver_info": solver_info,
        "request_id": request_id,
        "setup_intervals": [s.to_dict() for s in result.setup_intervals],
        "infeasible_wos": result.infeasible_wos,
        "machine_name_map": machine_name_map,
    }


def main():
    config_data = json.loads((INPUT_DIR / "scheduler_config.json").read_text(encoding="utf-8"))
    horizon_start = datetime.fromisoformat(config_data["horizon"]["start"])
    horizon_end = datetime.fromisoformat(config_data["horizon"]["end"])
    lot_size = config_data.get("lot_size", 1)
    amr_transfer = config_data.get("amr_transfer_time_sec", 60)

    work_orders = parse_work_orders(INPUT_DIR / "new_work_orders_v3.json")
    aas = AASLoader(str(INPUT_DIR / "aas_revised.json"))
    machines = aas.load_machines(horizon_start)
    amrs = aas.load_amrs()
    mt_params = aas.load_machine_type_params()
    sched_cfg = SchedulerConfig(lot_size=lot_size, amr_transfer_time_sec=amr_transfer)

    print(f"Loaded: {len(work_orders)} WOs, {len(machines)} machines, {len(amrs)} AMRs")
    print(f"Horizon: {horizon_start} → {horizon_end}")

    solver_types = [
        SolverType.OR_TOOLS,
        SolverType.GENETIC_ALGORITHM,
        SolverType.SIMULATED_ANNEALING,
        SolverType.TABU_SEARCH,
        SolverType.ALNS,
    ]

    for st in solver_types:
        cfg = SolverFactory.get_default_config(st)
        cfg.time_limit_sec = 15  # 기존 출력의 OR_TOOLS와 동일 수준

        solver = SolverFactory.create_solver(
            solver_type=st,
            work_orders=work_orders,
            machines=machines,
            machine_type_params=mt_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            constraints={},
            config=cfg,
            amrs=amrs,
            scheduler_config=sched_cfg,
        )
        result = solver.solve(time_limit_sec=cfg.time_limit_sec)
        gantt = solver.generate_gantt_data()
        quality = solver.estimate_schedule_quality()
        name_map = {m.machine_id: m.machine_name for m in machines}
        info = solver.get_solver_info()
        info["error"] = None

        out = build_result_dict(result, gantt, quality, name_map, info, str(uuid.uuid4()))
        save_schedule_output(out, st.value)
        ms = result.total_makespan
        late_h = quality.get("total_lateness_hours", 0)
        tard = getattr(result, "weighted_tardiness_sec", 0)
        setup = getattr(result, "total_setup_sec", 0)
        util = result.machine_utilization
        avg_u = round(sum(util.values()) / len(util), 1) if util else 0.0
        print(f"  {st.value:8s}: status={result.status}, makespan={ms}s ({ms/60:.1f}min), "
              f"w_tardiness={tard}s, setup={setup}s, avg_util={avg_u}%, "
              f"tasks={len(result.scheduled_tasks)}, solve={result.solve_time_sec:.2f}s")


if __name__ == "__main__":
    main()
