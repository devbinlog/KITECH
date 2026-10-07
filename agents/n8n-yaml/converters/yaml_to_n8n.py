"""
yaml_to_n8n.py
YAML 시나리오 파일 → n8n workflow JSON 변환기

사용법:
    python yaml_to_n8n.py <scenario.yaml> [--aas <aas.json>] [--base-url <url>] [-o <output.json>]

예시:
    python yaml_to_n8n.py ../data/cell1_scenario.yaml --aas ../data/cell1_aas.json -o cell1_workflow.json
"""

import json
import sys
import uuid
import argparse
from typing import Any

try:
    import yaml
except ImportError:
    print("pyyaml이 필요합니다: pip install pyyaml")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 레이아웃 상수
# ─────────────────────────────────────────────────────────────
X_START = 240
Y_MAIN = 300
X_STEP = 240      # 노드 간 수평 간격
Y_BRANCH = 180    # 분기 수직 간격


# ─────────────────────────────────────────────────────────────
# 노드 생성 헬퍼
# ─────────────────────────────────────────────────────────────

def make_id() -> str:
    return str(uuid.uuid4())


def make_trigger_node(x: int, y: int) -> dict:
    return {
        "id": make_id(),
        "name": "Manual Trigger",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {},
    }


def make_config_node(scenario: dict, aas_path: str, base_url: str, x: int, y: int) -> dict:
    assets = [
        {"id": a["id"], "name": a["name"]}
        for a in scenario.get("assets", [])
    ]
    return {
        "id": make_id(),
        "name": "Scenario Config",
        "type": "n8n-nodes-scenario.scenarioConfig",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {
            "scenarioName": scenario.get("name", ""),
            "aasFilePath": aas_path,
            "baseUrl": base_url,
            "assets": {
                "asset": assets
            },
        },
    }


def build_routing_values(routing: list) -> list:
    """
    YAML routing 리스트 → ScenarioStep 노드의 routing.values 변환

    각 routing 항목:
      when: "'{{res}}' == 'OK'"
      then:
        - next: "1-2"
        - set_var: 1
    """
    values = []
    for i, route in enumerate(routing):
        when_expr = route.get("when") or ""
        then_actions = route.get("then") or []

        # then 액션 직렬화 (각 항목은 단일 키 dict)
        then_list = []
        for action in then_actions:
            if isinstance(action, dict):
                then_list.append(action)
            # YAML에서 단순 스칼라인 경우 skip

        # 출력 핀 라벨 자동 생성
        # then 액션에서 alarm/next 여부로 의미있는 라벨 결정
        alarm_msg = next((a.get("alarm") for a in then_list if isinstance(a, dict) and "alarm" in a), None)
        next_id = next((a.get("next") for a in then_list if isinstance(a, dict) and "next" in a), None)

        if when_expr:
            label = when_expr[:30] if len(when_expr) > 30 else when_expr
        elif alarm_msg:
            label = f"ALARM: {str(alarm_msg)[:20]}"
        elif next_id:
            label = f"→ {next_id}"
        else:
            label = "Default"

        values.append({
            "label": label,
            "when": when_expr,
            "thenJson": json.dumps(then_list, ensure_ascii=False),
        })

    return values


def make_step_node(step: dict, x: int, y: int) -> dict:
    """YAML step → ScenarioStep n8n 노드"""
    step_id = step.get("id", "")
    step_name = step.get("name", "")
    action = step.get("action", "")
    params = step.get("params") or {}
    routing = step.get("routing") or []

    # acquire 파라미터 구성
    acquire_param: dict = {}
    if "acquire" in step:
        acq = step["acquire"]
        roles: dict = {}
        for role in ["main", "sub1", "sub2", "sub3"]:
            val = acq.get(role)
            if val:
                # 리스트면 쉼표로 결합
                if isinstance(val, list):
                    roles[role] = ",".join(str(v) for v in val)
                else:
                    roles[role] = str(val)
        if roles:
            acquire_param = {"roles": roles}

    return {
        "id": make_id(),
        "name": f"Step {step_id}: {step_name}"[:50],
        "type": "n8n-nodes-scenario.scenarioStep",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {
            "stepId": step_id,
            "stepName": step_name,
            "acquire": acquire_param,
            "action": action,
            "paramsJson": json.dumps(params, ensure_ascii=False) if params else "{}",
            "routing": {
                "values": build_routing_values(routing)
            },
        },
    }


# ─────────────────────────────────────────────────────────────
# 레이아웃 계산
# ─────────────────────────────────────────────────────────────

def compute_layout(steps: list, step_id_to_node: dict) -> None:
    """
    BFS 방식으로 next 연결을 따라 노드 위치(x, y)를 결정.
    - 메인 흐름: y = Y_MAIN, x 순차 증가
    - 분기(alarm 전용, next 없는 조건): 아래쪽 y
    """
    # step_id → next step_id 맵 구성
    next_map: dict[str, list[str]] = {}
    for step in steps:
        sid = step["id"]
        nexts = []
        for route in step.get("routing", []):
            for action in route.get("then", []):
                if isinstance(action, dict) and "next" in action:
                    nexts.append(action["next"])
        next_map[sid] = nexts

    # BFS
    visited: set[str] = set()
    queue = [steps[0]["id"]] if steps else []
    x = X_START + X_STEP * 2  # trigger + config 이후부터
    y = Y_MAIN
    col = 0

    while queue:
        sid = queue.pop(0)
        if sid in visited:
            continue
        visited.add(sid)

        node = step_id_to_node.get(sid)
        if node:
            node["position"] = [x + col * X_STEP, y]

        col += 1
        for nxt in next_map.get(sid, []):
            if nxt not in visited:
                queue.append(nxt)

    # 미방문 step은 아래에 배치 (고아 노드 방지)
    orphan_y = Y_MAIN + Y_BRANCH * 2
    orphan_x = X_START + X_STEP * 2
    for step in steps:
        sid = step["id"]
        if sid not in visited:
            node = step_id_to_node.get(sid)
            if node:
                node["position"] = [orphan_x, orphan_y]
                orphan_x += X_STEP


# ─────────────────────────────────────────────────────────────
# 연결(connections) 생성
# ─────────────────────────────────────────────────────────────

def build_connections(
    trigger_node: dict,
    config_node: dict,
    steps: list,
    step_id_to_node: dict,
    step_id_to_routing: dict,
) -> dict:
    """
    n8n workflow connections 딕셔너리 생성.
    연결 구조: { "NodeName": { "main": [ [출력핀0 연결들], [출력핀1 연결들], ... ] } }
    """
    connections: dict = {}

    def add_conn(src_name: str, src_output: int, dst_name: str, dst_input: int = 0) -> None:
        if src_name not in connections:
            connections[src_name] = {"main": []}
        while len(connections[src_name]["main"]) <= src_output:
            connections[src_name]["main"].append([])
        connections[src_name]["main"][src_output].append({
            "node": dst_name,
            "type": "main",
            "index": dst_input,
        })

    # Trigger → Config
    add_conn(trigger_node["name"], 0, config_node["name"])

    # Config → 첫 번째 step
    if steps:
        first_node = step_id_to_node.get(steps[0]["id"])
        if first_node:
            add_conn(config_node["name"], 0, first_node["name"])

    # 각 step의 routing → 다음 step 연결
    for step in steps:
        sid = step["id"]
        src_node = step_id_to_node.get(sid)
        if not src_node:
            continue

        routing = step.get("routing", [])
        for ri, route in enumerate(routing):
            then_actions = route.get("then", [])
            for action in then_actions:
                if isinstance(action, dict) and "next" in action:
                    next_sid = action["next"]
                    dst_node = step_id_to_node.get(next_sid)
                    if dst_node:
                        add_conn(src_node["name"], ri, dst_node["name"])

    return connections


# ─────────────────────────────────────────────────────────────
# 메인 변환 함수
# ─────────────────────────────────────────────────────────────

def yaml_to_n8n(
    yaml_path: str,
    aas_path: str = "/data/cell1_aas.json",
    base_url: str = "http://localhost:8080",
) -> dict:
    with open(yaml_path, "r", encoding="utf-8") as f:
        scenario = yaml.safe_load(f)

    steps: list = scenario.get("steps", [])
    nodes: list = []

    # ── 노드 생성 ──────────────────────────────────────────────

    # 1. Manual Trigger
    trigger = make_trigger_node(X_START, Y_MAIN)
    nodes.append(trigger)

    # 2. Scenario Config
    config = make_config_node(scenario, aas_path, base_url, X_START + X_STEP, Y_MAIN)
    nodes.append(config)

    # 3. Scenario Step 노드들 (임시 위치, layout 후 갱신)
    step_id_to_node: dict[str, dict] = {}
    step_id_to_routing: dict[str, list] = {}
    for i, step in enumerate(steps):
        x = X_START + X_STEP * (i + 2)
        node = make_step_node(step, x, Y_MAIN)
        nodes.append(node)
        step_id_to_node[step["id"]] = node
        step_id_to_routing[step["id"]] = step.get("routing", [])

    # 4. 레이아웃 재계산
    compute_layout(steps, step_id_to_node)

    # ── 연결 생성 ──────────────────────────────────────────────
    connections = build_connections(
        trigger, config, steps, step_id_to_node, step_id_to_routing
    )

    # ── n8n workflow JSON 조립 ─────────────────────────────────
    workflow = {
        "name": scenario.get("name", "Scenario"),
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1"
        },
        "id": make_id(),
        "meta": {
            "generatedBy": "yaml_to_n8n.py",
            "sourceYaml": yaml_path,
            "scenarioDesc": scenario.get("desc", ""),
        },
    }

    return workflow


# ─────────────────────────────────────────────────────────────
# CLI 진입점
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="YAML 시나리오 → n8n workflow JSON 변환")
    parser.add_argument("yaml_path", help="입력 YAML 파일 경로")
    parser.add_argument("--aas", default="/data/cell1_aas.json", help="AAS JSON 파일 경로 (컨테이너 내부 경로)")
    parser.add_argument("--base-url", default="http://localhost:8080", help="자산 API 기본 URL")
    parser.add_argument("-o", "--output", default=None, help="출력 JSON 파일 경로 (기본: stdout)")
    args = parser.parse_args()

    workflow = yaml_to_n8n(args.yaml_path, aas_path=args.aas, base_url=args.base_url)
    result_json = json.dumps(workflow, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result_json)
        print(f"저장 완료: {args.output}")
        print(f"  - 노드 수: {len(workflow['nodes'])}")
        print(f"  - Step 수: {len(workflow['nodes']) - 2}")  # trigger + config 제외
    else:
        print(result_json)


if __name__ == "__main__":
    main()
