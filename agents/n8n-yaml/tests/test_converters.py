"""
test_converters.py
변환기 테스트: YAML → JSON → YAML 라운드트립 검증

실행:
    cd n8n-project
    python tests/test_converters.py
"""

import json
import sys
import os
import difflib
from pathlib import Path

# 경로 설정
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "converters"))

from yaml_to_n8n import yaml_to_n8n
from n8n_to_yaml import n8n_to_yaml, scenario_to_yaml_str

try:
    import yaml
except ImportError:
    print("pyyaml이 필요합니다: pip install pyyaml")
    sys.exit(1)

DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "tests" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# 테스트 유틸
# ─────────────────────────────────────────────────────────────

PASS = "PASS"
FAIL = "FAIL"


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {label}")
    if not condition and detail:
        print(f"       └─ {detail}")
    return condition


# ─────────────────────────────────────────────────────────────
# 테스트 1: YAML → JSON 변환
# ─────────────────────────────────────────────────────────────

def test_yaml_to_json(yaml_name: str) -> dict | None:
    yaml_path = DATA_DIR / yaml_name
    if not yaml_path.exists():
        print(f"  [!] 파일 없음: {yaml_path}")
        return None

    print_section(f"TEST: YAML → JSON  ({yaml_name})")

    try:
        workflow = yaml_to_n8n(
            str(yaml_path),
            aas_path="/data/cell1_aas.json",
            base_url="http://localhost:8080",
        )
    except Exception as e:
        check("변환 실행", False, str(e))
        return None

    check("변환 성공", True)

    # 기본 구조 검증
    check("nodes 필드 존재", "nodes" in workflow)
    check("connections 필드 존재", "connections" in workflow)

    nodes = workflow["nodes"]
    node_types = [n["type"] for n in nodes]

    check("ManualTrigger 포함", "n8n-nodes-base.manualTrigger" in node_types)
    check("ScenarioConfig 포함", "n8n-nodes-scenario.scenarioConfig" in node_types)

    step_nodes = [n for n in nodes if n["type"] == "n8n-nodes-scenario.scenarioStep"]
    check(f"ScenarioStep 노드 수 > 0", len(step_nodes) > 0, f"실제: {len(step_nodes)}")

    # 원본 YAML step 수와 비교
    with open(yaml_path, "r", encoding="utf-8") as f:
        original = yaml.safe_load(f)
    original_step_count = len(original.get("steps", []))
    check(
        f"Step 수 일치 ({original_step_count}개)",
        len(step_nodes) == original_step_count,
        f"원본: {original_step_count}, 변환: {len(step_nodes)}"
    )

    # 그래프 연결성 검증: 고아 노드 없는지
    connections = workflow["connections"]
    connected_dst = set()
    for src_conns in connections.values():
        for output_list in src_conns.get("main", []):
            for conn in output_list:
                connected_dst.add(conn["node"])

    # trigger를 제외한 모든 노드는 적어도 입력 연결이 있어야 함
    non_trigger_names = [n["name"] for n in nodes if n["type"] != "n8n-nodes-base.manualTrigger"]
    orphans = [name for name in non_trigger_names if name not in connected_dst]
    check("고아 노드 없음 (모든 노드 연결됨)", len(orphans) == 0, f"고아: {orphans}")

    # ScenarioStep 노드들 간 연결 검증 (routing.then.next 기반)
    step_node_names = {n["name"] for n in step_nodes}
    step_connections_count = sum(
        1
        for src_name, conns in connections.items()
        if src_name in step_node_names
        for out_list in conns.get("main", [])
        for _ in out_list
    )
    check(f"Step간 연결 존재 ({step_connections_count}개)", step_connections_count > 0)

    # JSON 파일 저장
    out_path = OUT_DIR / yaml_name.replace(".yaml", "_workflow.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)
    print(f"\n  → 저장: {out_path}")

    return workflow


# ─────────────────────────────────────────────────────────────
# 테스트 2: JSON → YAML 역변환
# ─────────────────────────────────────────────────────────────

def test_json_to_yaml(json_path: Path, original_yaml_name: str) -> dict | None:
    print_section(f"TEST: JSON → YAML  ({json_path.name})")

    if not json_path.exists():
        check("JSON 파일 존재", False, str(json_path))
        return None

    try:
        scenario = n8n_to_yaml(str(json_path))
    except Exception as e:
        check("역변환 실행", False, str(e))
        return None

    check("역변환 성공", True)

    # 기본 필드 검증
    check("name 필드 존재", "name" in scenario and bool(scenario["name"]))
    check("assets 필드 존재", "assets" in scenario and len(scenario["assets"]) > 0)
    check("steps 필드 존재", "steps" in scenario and len(scenario["steps"]) > 0)

    steps = scenario.get("steps", [])
    check(f"Step 수 > 0", len(steps) > 0, f"실제: {len(steps)}")

    # 각 step에 id, action 포함 검증
    steps_with_id = [s for s in steps if s.get("id")]
    steps_with_action = [s for s in steps if s.get("action")]
    check("모든 Step에 id 존재", len(steps_with_id) == len(steps))
    check("모든 Step에 action 존재", len(steps_with_action) == len(steps))

    # routing 복원 검증
    steps_with_routing = [s for s in steps if s.get("routing")]
    check(f"routing 복원됨 ({len(steps_with_routing)}/{len(steps)} steps)", len(steps_with_routing) > 0)

    # YAML 파일 저장
    yaml_str = scenario_to_yaml_str(scenario)
    out_path = OUT_DIR / original_yaml_name.replace(".yaml", "_recovered.yaml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(yaml_str)
    print(f"\n  → 저장: {out_path}")

    return scenario


# ─────────────────────────────────────────────────────────────
# 테스트 3: 라운드트립 비교
# ─────────────────────────────────────────────────────────────

def test_roundtrip(yaml_name: str, original: dict, recovered: dict) -> None:
    print_section(f"TEST: 라운드트립 비교  ({yaml_name})")

    # 이름 비교
    check(
        "name 일치",
        original.get("name") == recovered.get("name"),
        f"원본: {original.get('name')}, 복원: {recovered.get('name')}"
    )

    # assets 비교
    orig_assets = {a["id"]: a["name"] for a in original.get("assets", [])}
    recv_assets = {a["id"]: a["name"] for a in recovered.get("assets", [])}
    check("assets 완전 일치", orig_assets == recv_assets, f"원본: {orig_assets}, 복원: {recv_assets}")

    # step 수 비교
    orig_steps = original.get("steps", [])
    recv_steps = recovered.get("steps", [])
    check(
        f"step 수 일치 ({len(orig_steps)}개)",
        len(orig_steps) == len(recv_steps),
        f"원본: {len(orig_steps)}, 복원: {len(recv_steps)}"
    )

    # 각 step 필드 비교
    match_count = 0
    for i, (orig, recv) in enumerate(zip(orig_steps, recv_steps)):
        id_match = orig.get("id") == recv.get("id")
        action_match = orig.get("action") == recv.get("action")
        params_match = orig.get("params") == recv.get("params")

        if id_match and action_match:
            match_count += 1
        else:
            print(f"  [!] Step {i+1} 불일치:")
            if not id_match:
                print(f"       id: 원본={orig.get('id')!r}, 복원={recv.get('id')!r}")
            if not action_match:
                print(f"       action: 원본={orig.get('action')!r}, 복원={recv.get('action')!r}")

    check(
        f"Step id/action 일치율 ({match_count}/{len(orig_steps)})",
        match_count == len(orig_steps)
    )

    # routing 조건 수 비교
    routing_match = 0
    for orig, recv in zip(orig_steps, recv_steps):
        orig_r = len(orig.get("routing", []))
        recv_r = len(recv.get("routing", []))
        if orig_r == recv_r:
            routing_match += 1
    check(
        f"routing 조건 수 일치 ({routing_match}/{len(orig_steps)} steps)",
        routing_match == len(orig_steps)
    )


# ─────────────────────────────────────────────────────────────
# 테스트 4: 커스텀 노드 구조 검증
# ─────────────────────────────────────────────────────────────

def test_node_structure(yaml_name: str, workflow: dict) -> None:
    print_section(f"TEST: 커스텀 노드 구조  ({yaml_name})")

    nodes = workflow.get("nodes", [])
    step_nodes = [n for n in nodes if n["type"] == "n8n-nodes-scenario.scenarioStep"]

    for i, node in enumerate(step_nodes[:3]):  # 처음 3개만 검증
        params = node.get("parameters", {})
        step_id = params.get("stepId", "")
        action = params.get("action", "")
        routing = params.get("routing", {}).get("values", [])

        check(f"Step[{i}] stepId 존재", bool(step_id), f"stepId={step_id!r}")
        check(f"Step[{i}] action 존재", bool(action), f"action={action!r}")
        check(f"Step[{i}] routing 존재", len(routing) > 0, f"routing={len(routing)}개")

        # routing 각 항목에 thenJson 파싱 검증
        for j, cond in enumerate(routing):
            try:
                then_actions = json.loads(cond.get("thenJson", "[]"))
                check(f"Step[{i}] routing[{j}] thenJson 파싱 가능", True)
            except json.JSONDecodeError as e:
                check(f"Step[{i}] routing[{j}] thenJson 파싱 가능", False, str(e))

        # acquire 파라미터가 있으면 검증
        acquire = params.get("acquire", {})
        if acquire.get("roles"):
            roles = acquire["roles"]
            check(f"Step[{i}] acquire roles 존재", any(roles.get(r) for r in ["main", "sub1", "sub2", "sub3"]))


# ─────────────────────────────────────────────────────────────
# 전체 테스트 실행
# ─────────────────────────────────────────────────────────────

def run_all_tests() -> None:
    test_cases = [
        "cell1_scenario.yaml",
        "cell2_scenario.yaml",
        "sample2.yaml",
    ]

    all_pass = True
    results: dict[str, bool] = {}

    for yaml_name in test_cases:
        yaml_path = DATA_DIR / yaml_name
        if not yaml_path.exists():
            print(f"\n[!] 파일 없음, 건너뜀: {yaml_name}")
            continue

        # 원본 YAML 로드
        with open(yaml_path, "r", encoding="utf-8") as f:
            original_scenario = yaml.safe_load(f)

        # Test 1: YAML → JSON
        workflow = test_yaml_to_json(yaml_name)
        if workflow is None:
            all_pass = False
            results[yaml_name] = False
            continue

        # Test 4: 노드 구조 검증
        test_node_structure(yaml_name, workflow)

        # Test 2: JSON → YAML
        json_path = OUT_DIR / yaml_name.replace(".yaml", "_workflow.json")
        recovered_scenario = test_json_to_yaml(json_path, yaml_name)
        if recovered_scenario is None:
            all_pass = False
            results[yaml_name] = False
            continue

        # Test 3: 라운드트립 비교
        test_roundtrip(yaml_name, original_scenario, recovered_scenario)

        results[yaml_name] = True

    # ── 최종 요약 ──────────────────────────────────────────────
    print_section("최종 결과 요약")
    for name, passed in results.items():
        status = PASS if passed else FAIL
        print(f"  [{status}] {name}")

    print(f"\n총 {len(results)}개 시나리오 테스트 완료")
    print(f"출력 파일 위치: {OUT_DIR}")


if __name__ == "__main__":
    run_all_tests()
