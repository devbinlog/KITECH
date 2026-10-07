"""Scenario action catalog.

Static V1 catalog of action templates available for ScenarioStep nodes.
Used by:
  - Step parameter form (action dropdown)
  - Expression autocomplete (suggestions for "{{acq.main}}/api/...")

Design Ref: §4 API Specification (GET /scenarios/actions)
Plan SC: #7 (paramsJson `{{$` 입력 시 expression suggestion)

V2 (future): replace with DB-backed catalog (alembic migration + admin UI).
"""

from typing import List

from ..schemas.master import ActionCatalogItem


# Manufacturing-domain action template catalog (V1: static)
# Format: {{acq.<role>}}/<service-path>
# Role token resolves at runtime via ScenarioContext.acq map.
ACTIONS: List[ActionCatalogItem] = [
    # --- Robot motion ---
    ActionCatalogItem(
        key="{{acq.main}}/robotGateway/commands/move",
        category="robot",
        description="로봇 이동 (지정된 좌표/포즈로)",
    ),
    ActionCatalogItem(
        key="{{acq.main}}/robotGateway/commands/home",
        category="robot",
        description="로봇 홈 위치로 복귀",
    ),
    ActionCatalogItem(
        key="{{acq.sub1}}/robotGateway/commands/supply",
        category="robot",
        description="소재 공급 동작 (보조 로봇)",
    ),
    # --- Gripper / End-effector ---
    ActionCatalogItem(
        key="{{acq.main}}/robotGateway/commands/grip",
        category="gripper",
        description="그리퍼 클로즈 (소재 잡기)",
    ),
    ActionCatalogItem(
        key="{{acq.main}}/robotGateway/commands/release",
        category="gripper",
        description="그리퍼 오픈 (소재 놓기)",
    ),
    # --- CNC ---
    ActionCatalogItem(
        key="{{acq.main}}/cncGateway/commands/start",
        category="cnc",
        description="CNC 가공 시작",
    ),
    ActionCatalogItem(
        key="{{acq.main}}/cncGateway/commands/stop",
        category="cnc",
        description="CNC 가공 정지",
    ),
    ActionCatalogItem(
        key="{{acq.main}}/cncGateway/commands/door-open",
        category="cnc",
        description="CNC 도어 오픈",
    ),
    ActionCatalogItem(
        key="{{acq.main}}/cncGateway/commands/door-close",
        category="cnc",
        description="CNC 도어 클로즈",
    ),
    # --- Utility / Flow control ---
    ActionCatalogItem(
        key="util://wait",
        category="util",
        description="대기 (params: {ms: <int>})",
    ),
    ActionCatalogItem(
        key="util://check",
        category="util",
        description="상태 체크 (params: {var: <name>, op: '==', value: <any>})",
    ),
]


def get_actions() -> List[ActionCatalogItem]:
    """Return the full action catalog. Stable order for client cache."""
    return list(ACTIONS)
