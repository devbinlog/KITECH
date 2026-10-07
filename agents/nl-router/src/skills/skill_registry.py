"""Skill registry for MES domain skills"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..understanding.intents import Intent

logger = logging.getLogger(__name__)


class OutputType(str, Enum):
    """UI output types"""

    DASHBOARD = "dashboard"
    DETAIL = "detail"
    LIST = "list"
    STATUS_GRID = "status_grid"
    GANTT = "gantt"
    KPI_DASHBOARD = "kpi_dashboard"
    CHART = "chart"
    COMPARISON_CHART = "comparison_chart"
    TRACEABILITY_TIMELINE = "traceability_timeline"
    CONFIRMATION = "confirmation"
    HELP = "help"
    # 신규 출력 타입
    DIAGNOSIS_PANEL = "diagnosis_panel"
    RISK_DASHBOARD = "risk_dashboard"
    ANALYSIS_DASHBOARD = "analysis_dashboard"
    TOOL_STATUS = "tool_status"


@dataclass
class SkillDefinition:
    """Definition of a skill that can handle specific intents"""

    name: str
    description: str
    intents: List[Intent]
    api_endpoints: List[str]
    required_entities: List[str] = field(default_factory=list)
    optional_entities: List[str] = field(default_factory=list)
    output_type: OutputType = OutputType.DASHBOARD
    priority: int = 0  # Higher priority = preferred when multiple skills match

    def matches_intent(self, intent: Intent) -> bool:
        """스킬이 주어진 인텐트를 처리할 수 있는지 확인.

        Args:
            intent: 확인할 인텐트

        Returns:
            처리 가능 여부

        """
        return intent in self.intents

    def has_required_entities(self, entities: Dict[str, Any]) -> bool:
        """필수 엔티티가 모두 존재하는지 확인.

        Args:
            entities: 추출된 엔티티 딕셔너리

        Returns:
            필수 엔티티 충족 여부

        """
        return all(e in entities for e in self.required_entities)

    def get_missing_entities(self, entities: Dict[str, Any]) -> List[str]:
        """누락된 필수 엔티티 목록 반환.

        Args:
            entities: 추출된 엔티티 딕셔너리

        Returns:
            누락된 필수 엔티티 이름 목록

        """
        return [e for e in self.required_entities if e not in entities]


# MES Domain Skills Definition
MES_SKILLS: Dict[str, SkillDefinition] = {
    "mes_production_query": SkillDefinition(
        name="mes_production_query",
        description="생산 현황, 작업지시, 생산실적 조회",
        intents=[Intent.PRODUCTION_STATUS, Intent.PRODUCTION_DETAIL],
        api_endpoints=[
            "/api/v1/analytics/daily-status",
            "/api/v1/production/orders",
            "/api/v1/production/results",
        ],
        required_entities=[],
        optional_entities=["date", "date_range", "lot_no", "status"],
        output_type=OutputType.DASHBOARD,
        priority=10,
    ),
    "mes_equipment_status": SkillDefinition(
        name="mes_equipment_status",
        description="설비 상태 조회, 실시간 모니터링",
        intents=[Intent.EQUIPMENT_STATUS, Intent.EQUIPMENT_LIST],
        api_endpoints=[
            "/api/v1/masters/equipments",
            "/api/v1/masters/equipments/{id}/status",
        ],
        required_entities=[],
        optional_entities=["equipment_id", "equipment_type", "status"],
        output_type=OutputType.STATUS_GRID,
        priority=10,
    ),
    "mes_kpi_query": SkillDefinition(
        name="mes_kpi_query",
        description="KPI 지표 조회 - 가동률, 수율, 생산량",
        intents=[Intent.KPI_QUERY, Intent.ANALYTICS, Intent.COMPARISON],
        api_endpoints=[
            "/api/v1/analytics/kpis",
            "/api/v1/analytics/equipment-utilization",
            "/api/v1/analytics/trends",
        ],
        required_entities=[],
        optional_entities=["metric", "date_range", "group_by", "equipment_ids"],
        output_type=OutputType.KPI_DASHBOARD,
        priority=10,
    ),
    "mes_traceability": SkillDefinition(
        name="mes_traceability",
        description="LOT 추적 - 생산 이력 조회",
        intents=[Intent.TRACEABILITY, Intent.PRODUCTION_DETAIL],
        api_endpoints=[
            "/api/v1/analytics/traceability/{lot_no}",
        ],
        required_entities=["lot_no"],
        optional_entities=[],
        output_type=OutputType.TRACEABILITY_TIMELINE,
        priority=15,  # Higher priority for traceability when lot_no is present
    ),
    "mes_scheduling": SkillDefinition(
        name="mes_scheduling",
        description="스케줄 조회 및 스케줄링 요청",
        intents=[Intent.SCHEDULE_QUERY, Intent.SCHEDULE_REQUEST],
        api_endpoints=[
            "/api/v1/scheduler/equipment-availability",
            "/api/v1/scheduler/requests",
        ],
        required_entities=[],
        optional_entities=["date_range", "equipment_ids"],
        output_type=OutputType.GANTT,
        priority=10,
    ),
    "mes_master_data": SkillDefinition(
        name="mes_master_data",
        description="마스터 데이터 조회 - 제품, 공정",
        intents=[Intent.MASTER_DATA_QUERY],
        api_endpoints=[
            "/api/v1/masters/products",
            "/api/v1/masters/std-processes",
        ],
        required_entities=[],
        optional_entities=["product_id", "product_code", "process_code"],
        output_type=OutputType.LIST,
        priority=5,
    ),
    # 신규 스킬들
    "mes_error_diagnosis": SkillDefinition(
        name="mes_error_diagnosis",
        description="설비 알람 및 에러 진단 - 알람 해석, 해결책 제시",
        intents=[Intent.ERROR_DIAGNOSIS],
        api_endpoints=[
            "/api/v1/masters/equipments/{id}/status",
            "/api/v1/masters/equipments",
        ],
        required_entities=[],
        optional_entities=["equipment_id", "alarm_code"],
        output_type=OutputType.DIAGNOSIS_PANEL,
        priority=10,
    ),
    "mes_delay_prediction": SkillDefinition(
        name="mes_delay_prediction",
        description="납기 지연 예측 - 위험 오더 식별",
        intents=[Intent.DELAY_PREDICTION],
        api_endpoints=[
            "/api/v1/production/orders",
            "/api/v1/analytics/daily-status",
        ],
        required_entities=[],
        optional_entities=["date_range", "status"],
        output_type=OutputType.RISK_DASHBOARD,
        priority=10,
    ),
    "mes_defect_analysis": SkillDefinition(
        name="mes_defect_analysis",
        description="불량 원인 분석 - 불량률 추이, 원인 파레토",
        intents=[Intent.DEFECT_ANALYSIS],
        api_endpoints=[
            "/api/v1/production/results",
            "/api/v1/analytics/kpis",
        ],
        required_entities=[],
        optional_entities=["defect_type", "product_id", "equipment_id", "date_range"],
        output_type=OutputType.ANALYSIS_DASHBOARD,
        priority=10,
    ),
    "mes_comparison": SkillDefinition(
        name="mes_comparison",
        description="비교 분석 - 기간별, 설비별, 제품별 비교",
        intents=[Intent.COMPARISON],
        api_endpoints=[
            "/api/v1/analytics/kpis",
            "/api/v1/analytics/trends",
        ],
        required_entities=[],
        optional_entities=["date_range", "group_by", "metric", "shift"],
        output_type=OutputType.COMPARISON_CHART,
        priority=12,  # 비교 분석은 KPI보다 높은 우선순위
    ),
    "mes_tool_management": SkillDefinition(
        name="mes_tool_management",
        description="공구 관리 - 수명 예측, 교체 일정",
        intents=[Intent.TOOL_MANAGEMENT],
        api_endpoints=[
            "/api/v1/masters/equipments",
        ],
        required_entities=[],
        optional_entities=["equipment_id", "tool_id"],
        output_type=OutputType.TOOL_STATUS,
        priority=10,
    ),
    "mes_help": SkillDefinition(
        name="mes_help",
        description="도움말 - 사용 가능한 기능 안내",
        intents=[Intent.HELP],
        api_endpoints=[],
        required_entities=[],
        optional_entities=[],
        output_type=OutputType.HELP,
        priority=0,
    ),
}


class SkillRegistry:
    """Registry for managing and matching skills"""

    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
        self._load_default_skills()

    def _load_default_skills(self):
        """기본 MES 스킬 로드.

        MES_SKILLS 딕셔너리에 정의된 모든 스킬을 레지스트리에 등록합니다.
        """
        for name, skill in MES_SKILLS.items():
            self.register(skill)

    def register(self, skill: SkillDefinition):
        """스킬 등록.

        Args:
            skill: 등록할 스킬 정의

        """
        self._skills[skill.name] = skill
        logger.debug(f"Registered skill: {skill.name}")

    def get(self, name: str) -> Optional[SkillDefinition]:
        """이름으로 스킬 조회.

        Args:
            name: 스킬 이름

        Returns:
            스킬 정의 (없으면 None)

        """
        return self._skills.get(name)

    def list_all(self) -> List[SkillDefinition]:
        """등록된 모든 스킬 목록 반환.

        Returns:
            스킬 정의 목록

        """
        return list(self._skills.values())

    def match_skills(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[SkillDefinition]:
        """Find skills that match the given intent and have required entities

        Args:
            intent: Classified intent
            entities: Extracted entities

        Returns:
            List of matching skills, sorted by priority (highest first)

        """
        matching = []

        for skill in self._skills.values():
            if not skill.matches_intent(intent):
                continue

            if not skill.has_required_entities(entities):
                continue

            matching.append(skill)

        # Sort by priority (descending)
        matching.sort(key=lambda s: s.priority, reverse=True)
        return matching

    def get_best_skill(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> Optional[SkillDefinition]:
        """최적 매칭 스킬 반환.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티

        Returns:
            가장 우선순위 높은 매칭 스킬 (없으면 None)

        """
        matching = self.match_skills(intent, entities)
        return matching[0] if matching else None

    def get_skills_for_intent(self, intent: Intent) -> List[SkillDefinition]:
        """인텐트 처리 가능한 모든 스킬 반환.

        Args:
            intent: 인텐트

        Returns:
            해당 인텐트를 처리할 수 있는 스킬 목록

        """
        return [s for s in self._skills.values() if s.matches_intent(intent)]


# Singleton instance
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """전역 스킬 레지스트리 인스턴스 반환.

    싱글톤 패턴으로 구현되어 있어 항상 동일한 인스턴스를 반환합니다.

    Returns:
        SkillRegistry 인스턴스

    """
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
