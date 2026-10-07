"""
scenario_converter.py
n8n ↔ YAML 시나리오 양방향 파이썬 컨버터 로직 (API 레벨)

Design Ref: §3 Data Model (StickyNote schema), §4 API Spec (converters)
Plan SC: #9 (Sticky note YAML 보존)
"""

import json
import uuid
import yaml
from typing import Any


# ==============================================================================
# Sticky Note 매핑 (M0 — n8n YAML editor integration)
# ==============================================================================
#
# YAML schema extension (옵션 키, 하위 호환):
#   notes:
#     - { x: 100, y: 200, w: 240, h: 180, text: "...", color: yellow }
#
# n8n stickyNote 노드는 {nodes} 배열 안에 type=n8n-nodes-base.stickyNote 로 들어감.
# n8n 내부 color 값은 정수 1-7. UI 색상 이름과 양방향 매핑.

STICKY_TYPE = "n8n-nodes-base.stickyNote"

# UI 색상 이름 → n8n 내부 정수 (n8n editor 시각 일관성)
COLOR_NAME_TO_INT = {
    "yellow": 3,
    "blue": 4,
    "pink": 6,
    "green": 5,
}
COLOR_INT_TO_NAME = {v: k for k, v in COLOR_NAME_TO_INT.items()}


def make_sticky_node(note: dict) -> dict:
    """YAML notes[] 항목 1개를 n8n stickyNote 노드로 변환."""
    color_name = note.get("color", "yellow")
    color_int = COLOR_NAME_TO_INT.get(color_name, 3)
    return {
        "id": make_id(),
        "name": "Sticky Note",
        "type": STICKY_TYPE,
        "typeVersion": 1,
        "position": [int(note.get("x", 0)), int(note.get("y", 0))],
        "parameters": {
            "content": note.get("text", ""),
            "width": int(note.get("w", 240)),
            "height": int(note.get("h", 180)),
            "color": color_int,
        },
    }


def parse_sticky_node(node: dict) -> dict:
    """n8n stickyNote 노드를 YAML notes[] 항목으로 변환."""
    params = node.get("parameters", {}) or {}
    pos = node.get("position", [0, 0])
    color_int = params.get("color", 3)
    return {
        "x": int(pos[0]) if len(pos) > 0 else 0,
        "y": int(pos[1]) if len(pos) > 1 else 0,
        "w": int(params.get("width", 240)),
        "h": int(params.get("height", 180)),
        "text": params.get("content", "") or "",
        "color": COLOR_INT_TO_NAME.get(color_int, "yellow"),
    }

# ==============================================================================
# yaml_to_n8n.py 로직
# ==============================================================================

# 레이아웃 상수
X_START = 240
Y_MAIN = 300
X_STEP = 240      # 노드 간 수평 간격
Y_BRANCH = 180    # 분기 수직 간격

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
    values = []
    for i, route in enumerate(routing):
        when_expr = route.get("when") or ""
        then_actions = route.get("then") or []

        then_list = []
        for action in then_actions:
            if isinstance(action, dict):
                then_list.append(action)

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
    step_id = step.get("id", "")
    step_name = step.get("name", "")
    action = step.get("action", "")
    params = step.get("params") or {}
    routing = step.get("routing") or []

    acquire_param: dict = {}
    if "acquire" in step:
        acq = step["acquire"]
        roles: dict = {}
        for role in ["main", "sub1", "sub2", "sub3"]:
            val = acq.get(role)
            if val:
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

def compute_layout(steps: list, step_id_to_node: dict) -> None:
    next_map: dict[str, list[str]] = {}
    for step in steps:
        sid = step["id"]
        nexts = []
        for route in step.get("routing", []):
            for action in route.get("then", []):
                if isinstance(action, dict) and "next" in action:
                    nexts.append(action["next"])
        next_map[sid] = nexts

    visited: set[str] = set()
    queue = [steps[0]["id"]] if steps else []
    x = X_START + X_STEP * 2
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

    orphan_y = Y_MAIN + Y_BRANCH * 2
    orphan_x = X_START + X_STEP * 2
    for step in steps:
        sid = step["id"]
        if sid not in visited:
            node = step_id_to_node.get(sid)
            if node:
                node["position"] = [orphan_x, orphan_y]
                orphan_x += X_STEP

def build_connections(
    trigger_node: dict,
    config_node: dict,
    steps: list,
    step_id_to_node: dict,
    step_id_to_routing: dict,
) -> dict:
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

    add_conn(trigger_node["name"], 0, config_node["name"])

    if steps:
        first_node = step_id_to_node.get(steps[0]["id"])
        if first_node:
            add_conn(config_node["name"], 0, first_node["name"])

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

def yaml_to_n8n_from_dict(
    scenario: dict,
    aas_path: str = "/data/cell1_aas.json",
    base_url: str = "http://localhost:8080",
) -> dict:
    steps: list = scenario.get("steps", [])
    nodes: list = []

    trigger = make_trigger_node(X_START, Y_MAIN)
    nodes.append(trigger)

    config = make_config_node(scenario, aas_path, base_url, X_START + X_STEP, Y_MAIN)
    nodes.append(config)

    step_id_to_node: dict[str, dict] = {}
    step_id_to_routing: dict[str, list] = {}
    for i, step in enumerate(steps):
        x = X_START + X_STEP * (i + 2)
        node = make_step_node(step, x, Y_MAIN)
        nodes.append(node)
        step_id_to_node[step["id"]] = node
        step_id_to_routing[step["id"]] = step.get("routing", [])

    compute_layout(steps, step_id_to_node)

    connections = build_connections(
        trigger, config, steps, step_id_to_node, step_id_to_routing
    )

    # Sticky notes (옵션, 하위 호환 — V1 n8n YAML editor)
    for note in scenario.get("notes", []) or []:
        if isinstance(note, dict):
            nodes.append(make_sticky_node(note))

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
            "generatedBy": "yaml_to_n8n_from_dict",
            "scenarioDesc": scenario.get("desc", ""),
        },
    }

    return workflow

# ==============================================================================
# n8n_to_yaml.py 로직
# ==============================================================================

class LiteralStr(str):
    pass

def _literal_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    if any(c in data for c in ["{{", "}}", ":", "#", "'", "\n"]):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

class FlowDict(dict):
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


def find_node_by_type(nodes: list, node_type: str) -> dict | None:
    for node in nodes:
        if node.get("type") == node_type:
            return node
    return None

def find_nodes_by_type(nodes: list, node_type: str) -> list:
    return [n for n in nodes if n.get("type") == node_type]

def parse_config_node(config_node: dict) -> tuple[str, str, list]:
    params = config_node.get("parameters", {})
    name = params.get("scenarioName", "")
    desc = ""
    assets_param = params.get("assets", {})
    asset_list = assets_param.get("asset", [])
    assets = [{"id": a["id"], "name": a["name"]} for a in asset_list if a.get("id") and a.get("name")]
    return name, desc, assets

def parse_acquire(acquire_param: dict) -> dict | None:
    if not acquire_param:
        return None
    roles = acquire_param.get("roles", {})
    if not roles:
        return None

    result: dict = {}
    for role in ["main", "sub1", "sub2", "sub3"]:
        val = roles.get(role)
        if val:
            items = [v.strip() for v in val.split(",") if v.strip()]
            if items:
                result[role] = items

    return result if result else None

def parse_then_json(then_json_str: str) -> list:
    try:
        actions = json.loads(then_json_str or "[]")
    except (json.JSONDecodeError, TypeError):
        return []

    result = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        for key, val in action.items():
            if val is None or val == "" or val == []:
                continue
            result.append({key: val})

    return result

def parse_routing(routing_param: dict) -> list:
    values = routing_param.get("values", []) if routing_param else []
    routing = []

    for cond in values:
        when_expr = cond.get("when", "") or None
        then_actions = parse_then_json(cond.get("thenJson", "[]"))

        route: dict = {}
        if when_expr:
            route["when"] = when_expr
        else:
            route["when"] = None
        route["then"] = then_actions if then_actions else []

        routing.append(route)

    return routing

def parse_step_node(step_node: dict) -> dict:
    params = step_node.get("parameters", {})
    step: dict = {}

    step_id = params.get("stepId", "")
    step_name = params.get("stepName", "")
    if step_id:
        step["id"] = step_id
    if step_name:
        step["name"] = step_name

    acquire = parse_acquire(params.get("acquire", {}))
    if acquire:
        step["acquire"] = acquire

    action = params.get("action", "")
    if action:
        step["action"] = action

    params_json = params.get("paramsJson", "{}")
    try:
        parsed_params = json.loads(params_json)
        if parsed_params:
            step["params"] = FlowDict(parsed_params)
    except (json.JSONDecodeError, TypeError):
        pass

    routing = parse_routing(params.get("routing", {}))
    if routing:
        step["routing"] = routing

    return step

def enrich_steps_with_connections(
    steps: list,
    ordered_step_nodes: list,
    connections: dict,
    step_node_names: set,
) -> None:
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
                    continue
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
    name_to_step_node: dict[str, dict] = {n["name"]: n for n in step_nodes}
    visited_names: set[str] = set()
    ordered_nodes: list[dict] = []

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

        node_conns = connections.get(node_name, {}).get("main", [])
        for output_conns in node_conns:
            for conn in output_conns:
                next_name = conn.get("node", "")
                if next_name in name_to_step_node and next_name not in visited_names:
                    queue.append(next_name)

    for node in step_nodes:
        if node["name"] not in visited_names:
            ordered_nodes.append(node)
            visited_names.add(node["name"])

    return ordered_nodes

def n8n_to_yaml_from_dict(workflow: dict) -> dict:
    nodes: list = workflow.get("nodes", [])
    connections: dict = workflow.get("connections", {})
    meta: dict = workflow.get("meta", {})

    config_node = find_node_by_type(nodes, "n8n-nodes-scenario.scenarioConfig")
    if not config_node:
        for n in nodes:
            if "Scenario Config" in n.get("name", ""):
                config_node = n
                break

    if not config_node:
        raise ValueError("ScenarioConfig 노드를 찾을 수 없습니다.")

    scenario_name, _, assets = parse_config_node(config_node)

    step_nodes = find_nodes_by_type(nodes, "n8n-nodes-scenario.scenarioStep")
    if not step_nodes:
        step_nodes = [n for n in nodes if "Step " in n.get("name", "")]

    if not step_nodes:
        raise ValueError("ScenarioStep 노드를 찾을 수 없습니다.")

    ordered_step_nodes = restore_step_order(step_nodes, connections, config_node["name"])
    steps = [parse_step_node(n) for n in ordered_step_nodes]

    step_node_name_set = {n["name"] for n in step_nodes}
    enrich_steps_with_connections(steps, ordered_step_nodes, connections, step_node_name_set)

    scenario: dict = {}
    scenario["name"] = scenario_name or workflow.get("name", "")

    desc = meta.get("scenarioDesc", "")
    if desc:
        scenario["desc"] = desc

    if assets:
        scenario["assets"] = assets

    scenario["steps"] = steps

    # Sticky notes (옵션, 하위 호환 — V1 n8n YAML editor)
    sticky_nodes = find_nodes_by_type(nodes, STICKY_TYPE)
    if sticky_nodes:
        scenario["notes"] = [parse_sticky_node(n) for n in sticky_nodes]

    return scenario

def scenario_to_yaml_str(scenario: dict) -> str:
    return yaml.dump(
        scenario,
        Dumper=ScenarioDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
        width=120,
    )
