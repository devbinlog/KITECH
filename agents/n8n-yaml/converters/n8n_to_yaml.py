"""
n8n_to_yaml.py
n8n workflow JSON → YAML 시나리오 역변환기

사용법:
    python n8n_to_yaml.py <workflow.json> [-o <output.yaml>]

예시:
    python n8n_to_yaml.py cell1_workflow.json -o cell1_recovered.yaml
"""

import json
import sys
import argparse
from typing import Any

try:
    import yaml
except ImportError:
    print("pyyaml이 필요합니다: pip install pyyaml")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 커스텀 YAML 덤퍼 (원본 형식 보존)
# ─────────────────────────────────────────────────────────────

class LiteralStr(str):
    """멀티라인 문자열을 YAML literal block(|)으로 출력"""
    pass


def _literal_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """따옴표 스타일 자동 결정"""
    if any(c in data for c in ["{{", "}}", ":", "#", "'", "\n"]):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


class FlowDict(dict):
    """params 처럼 원본 YAML에서 인라인 {...} 스타일로 표현되는 딕셔너리"""
    pass


class ScenarioDumper(yaml.Dumper):
    pass


ScenarioDumper.add_representer(LiteralStr, _literal_representer)
ScenarioDumper.add_representer(str, _str_representer)
ScenarioDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)
ScenarioDumper.add_representer(
    FlowDict,
    lambda dumper, data: dumper.represent_mapping(
        "tag:yaml.org,2002:map", data, flow_style=True
    ),
)


# ─────────────────────────────────────────────────────────────
# 노드 파싱 헬퍼
# ─────────────────────────────────────────────────────────────

def find_node_by_type(nodes: list, node_type: str) -> dict | None:
    for node in nodes:
        if node.get("type") == node_type:
            return node
    return None


def find_nodes_by_type(nodes: list, node_type: str) -> list:
    return [n for n in nodes if n.get("type") == node_type]


def parse_config_node(config_node: dict) -> tuple[str, str, list]:
    """ScenarioConfig 노드 → (name, desc, assets)"""
    params = config_node.get("parameters", {})
    name = params.get("scenarioName", "")
    desc = ""  # desc는 메타에서 복원
    assets_param = params.get("assets", {})
    asset_list = assets_param.get("asset", [])
    assets = [{"id": a["id"], "name": a["name"]} for a in asset_list if a.get("id") and a.get("name")]
    return name, desc, assets


def parse_acquire(acquire_param: dict) -> dict | None:
    """acquire 파라미터 → YAML acquire 딕셔너리"""
    if not acquire_param:
        return None
    roles = acquire_param.get("roles", {})
    if not roles:
        return None

    result: dict = {}
    for role in ["main", "sub1", "sub2", "sub3"]:
        val = roles.get(role)
        if val:
            # 쉼표 분리 → 리스트
            items = [v.strip() for v in val.split(",") if v.strip()]
            if items:
                result[role] = items

    return result if result else None


def parse_then_json(then_json_str: str) -> list:
    """thenJson 문자열 → YAML then 액션 리스트"""
    try:
        actions = json.loads(then_json_str or "[]")
    except (json.JSONDecodeError, TypeError):
        return []

    result = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        for key, val in action.items():
            # 값이 None이거나 빈 값인 경우 처리
            if val is None or val == "" or val == []:
                continue
            result.append({key: val})

    return result


def parse_routing(routing_param: dict) -> list:
    """ScenarioStep routing 파라미터 → YAML routing 리스트"""
    values = routing_param.get("values", []) if routing_param else []
    routing = []

    for cond in values:
        when_expr = cond.get("when", "") or None  # 빈 문자열 → None (YAML에서 빈 when)
        then_actions = parse_then_json(cond.get("thenJson", "[]"))

        route: dict = {}
        if when_expr:
            route["when"] = when_expr
        else:
            route["when"] = None  # YAML의 빈 when: 표현
        route["then"] = then_actions if then_actions else []

        routing.append(route)

    return routing


def parse_step_node(step_node: dict) -> dict:
    """ScenarioStep 노드 → YAML step 딕셔너리"""
    params = step_node.get("parameters", {})

    step: dict = {}

    # 기본 필드
    step_id = params.get("stepId", "")
    step_name = params.get("stepName", "")
    if step_id:
        step["id"] = step_id
    if step_name:
        step["name"] = step_name

    # acquire
    acquire = parse_acquire(params.get("acquire", {}))
    if acquire:
        step["acquire"] = acquire

    # action
    action = params.get("action", "")
    if action:
        step["action"] = action

    # params
    params_json = params.get("paramsJson", "{}")
    try:
        parsed_params = json.loads(params_json)
        if parsed_params:
            step["params"] = FlowDict(parsed_params)
    except (json.JSONDecodeError, TypeError):
        pass

    # routing
    routing = parse_routing(params.get("routing", {}))
    if routing:
        step["routing"] = routing

    return step


# ─────────────────────────────────────────────────────────────
# 연결 기반 step 순서 복원
# ─────────────────────────────────────────────────────────────

def enrich_steps_with_connections(
    steps: list,
    ordered_step_nodes: list,
    connections: dict,
    step_node_names: set,
) -> None:
    """
    n8n connections에서 읽은 연결 정보를 YAML step의 routing.next에 반영.

    n8n UI에서 선으로만 연결한 경우 parameters.routing에는 next가 없고
    connections 딕셔너리에만 기록된다. 이 함수는 그 누락된 next를 채워준다.
    """
    name_to_step_id: dict[str, str] = {
        n["name"]: n.get("parameters", {}).get("stepId", "")
        for n in ordered_step_nodes
        if n.get("parameters", {}).get("stepId", "")
    }

    for step, node in zip(steps, ordered_step_nodes):
        node_name = node["name"]
        node_conns = connections.get(node_name, {}).get("main", [])

        for ri, output_conns in enumerate(node_conns):
            for conn in output_conns:
                next_node_name = conn.get("node", "")
                if next_node_name not in step_node_names:
                    continue  # ScenarioStep 이외 노드(Config 등) 무시
                next_step_id = name_to_step_id.get(next_node_name)
                if not next_step_id:
                    continue

                routing = step.setdefault("routing", [])
                while len(routing) <= ri:
                    routing.append({"when": None, "then": []})

                then_actions = routing[ri].setdefault("then", [])
                already = any(
                    isinstance(a, dict) and a.get("next") == next_step_id
                    for a in then_actions
                )
                if not already:
                    then_actions.append({"next": next_step_id})


def restore_step_order(
    step_nodes: list,
    connections: dict,
    config_node_name: str,
) -> list:
    """
    n8n connections를 BFS로 순회하여 YAML step 순서를 복원.
    ScenarioConfig → 첫 번째 step, 이후 각 step의 next 연결을 따라감.
    """
    # 노드 이름 → step_node 매핑
    name_to_step_node: dict[str, dict] = {n["name"]: n for n in step_nodes}

    # ScenarioStep 노드들의 stepId → 노드 매핑
    step_id_to_node: dict[str, dict] = {}
    for n in step_nodes:
        sid = n.get("parameters", {}).get("stepId", "")
        if sid:
            step_id_to_node[sid] = n

    # BFS로 연결 순서 탐색
    visited_names: set[str] = set()
    ordered_nodes: list[dict] = []

    # 시작점: Config 노드에서 연결된 첫 번째 step
    start_conns = connections.get(config_node_name, {}).get("main", [[]])
    start_targets = start_conns[0] if start_conns else []

    queue: list[str] = []
    for t in start_targets:
        target_name = t.get("node", "")
        if target_name in name_to_step_node:
            queue.append(target_name)

    while queue:
        node_name = queue.pop(0)
        if node_name in visited_names:
            continue
        visited_names.add(node_name)

        node = name_to_step_node.get(node_name)
        if node:
            ordered_nodes.append(node)

        # 이 노드에서 연결된 다음 step들 추가
        node_conns = connections.get(node_name, {}).get("main", [])
        for output_conns in node_conns:
            for conn in output_conns:
                next_name = conn.get("node", "")
                if next_name in name_to_step_node and next_name not in visited_names:
                    queue.append(next_name)

    # 연결에 포함되지 않은 step 노드 (고아 노드) 순서대로 추가
    for node in step_nodes:
        if node["name"] not in visited_names:
            ordered_nodes.append(node)
            visited_names.add(node["name"])

    return ordered_nodes


# ─────────────────────────────────────────────────────────────
# 메인 역변환 함수
# ─────────────────────────────────────────────────────────────

def n8n_to_yaml(workflow_json_path: str) -> dict:
    with open(workflow_json_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    nodes: list = workflow.get("nodes", [])
    connections: dict = workflow.get("connections", {})
    meta: dict = workflow.get("meta", {})

    # ── ScenarioConfig 노드 파싱 ──────────────────────────────
    config_node = find_node_by_type(nodes, "n8n-nodes-scenario.scenarioConfig")
    if not config_node:
        # 폴백: 이름으로 검색
        for n in nodes:
            if "Scenario Config" in n.get("name", ""):
                config_node = n
                break

    if not config_node:
        raise ValueError("ScenarioConfig 노드를 찾을 수 없습니다.")

    scenario_name, _, assets = parse_config_node(config_node)

    # ── ScenarioStep 노드들 파싱 ──────────────────────────────
    step_nodes = find_nodes_by_type(nodes, "n8n-nodes-scenario.scenarioStep")
    if not step_nodes:
        # 폴백: 이름으로 검색
        step_nodes = [n for n in nodes if "Step " in n.get("name", "")]

    if not step_nodes:
        raise ValueError("ScenarioStep 노드를 찾을 수 없습니다.")

    # 연결 기반으로 step 순서 복원
    ordered_step_nodes = restore_step_order(step_nodes, connections, config_node["name"])

    # 각 step 노드 → YAML step 딕셔너리
    steps = [parse_step_node(n) for n in ordered_step_nodes]

    # connections에 있지만 routing 파라미터에 없는 next 연결 보완
    step_node_name_set = {n["name"] for n in step_nodes}
    enrich_steps_with_connections(steps, ordered_step_nodes, connections, step_node_name_set)

    # ── YAML 시나리오 딕셔너리 조립 ──────────────────────────
    scenario: dict = {}
    scenario["name"] = scenario_name or workflow.get("name", "")

    # desc 복원 (메타에 저장된 경우)
    desc = meta.get("scenarioDesc", "")
    if desc:
        scenario["desc"] = desc

    if assets:
        scenario["assets"] = assets

    scenario["steps"] = steps

    return scenario


# ─────────────────────────────────────────────────────────────
# YAML 직렬화
# ─────────────────────────────────────────────────────────────

def scenario_to_yaml_str(scenario: dict) -> str:
    """
    시나리오 딕셔너리 → YAML 문자열 (원본 형식 최대한 보존)
    """
    return yaml.dump(
        scenario,
        Dumper=ScenarioDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
        width=120,
    )


# ─────────────────────────────────────────────────────────────
# CLI 진입점
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="n8n workflow JSON → YAML 시나리오 역변환")
    parser.add_argument("json_path", help="입력 n8n workflow JSON 파일 경로")
    parser.add_argument("-o", "--output", default=None, help="출력 YAML 파일 경로 (기본: stdout)")
    args = parser.parse_args()

    scenario = n8n_to_yaml(args.json_path)
    yaml_str = scenario_to_yaml_str(scenario)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        print(f"저장 완료: {args.output}")
        print(f"  - Step 수: {len(scenario.get('steps', []))}")
    else:
        print(yaml_str)


if __name__ == "__main__":
    main()
