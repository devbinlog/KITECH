"""API selector and orchestration plan builder"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .skill_registry import SkillDefinition, OutputType
from ..understanding.intents import Intent
from ..understanding.entities import DateRangeResolver, DATE_KEYWORDS
from ..core.config import settings

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """API execution mode"""

    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class APICall:
    """Single API call definition"""

    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    path_params: Dict[str, str] = field(default_factory=dict)
    depends_on: Optional[str] = None  # Key of dependent call
    result_key: str = ""  # Key to store result
    timeout: int = 30  # Seconds

    def get_full_endpoint(self) -> str:
        """경로 파라미터가 치환된 전체 엔드포인트 반환.

        Returns:
            path_params가 적용된 엔드포인트 문자열

        """
        endpoint = self.endpoint
        for key, value in self.path_params.items():
            endpoint = endpoint.replace(f"{{{key}}}", str(value))
        return endpoint


@dataclass
class OrchestrationPlan:
    """Plan for executing multiple API calls"""

    calls: List[APICall]
    execution_mode: ExecutionMode
    aggregation_strategy: str = "merge"  # merge, join, timeline
    output_type: OutputType = OutputType.DASHBOARD
    skill_name: str = ""

    @property
    def has_dependencies(self) -> bool:
        """Check if any calls have dependencies"""
        return any(c.depends_on for c in self.calls)


class APISelector:
    """Select and configure API calls based on skill and entities"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.CELL_MES_URL

    def _resolve_date(self, date_value: str) -> str:
        """날짜 키워드를 ISO 형식으로 변환.

        Args:
            date_value: 날짜 문자열 (yesterday, today 등 또는 YYYY-MM-DD)

        Returns:
            YYYY-MM-DD 형식 날짜 문자열

        """
        if date_value in DATE_KEYWORDS:
            resolved = DATE_KEYWORDS[date_value]()
            return resolved.isoformat()
        # Already ISO format or unrecognized - return as-is
        return date_value

    def build_plan(
        self,
        skill: SkillDefinition,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> OrchestrationPlan:
        """Build an orchestration plan for the given skill and entities

        Args:
            skill: Selected skill
            intent: Classified intent
            entities: Extracted entities

        Returns:
            OrchestrationPlan with configured API calls

        """
        calls = []

        # Build calls based on skill and intent combination
        if skill.name == "mes_production_query":
            calls = self._build_production_calls(intent, entities)
        elif skill.name == "mes_equipment_status":
            calls = self._build_equipment_calls(intent, entities)
        elif skill.name == "mes_kpi_query":
            calls = self._build_kpi_calls(intent, entities)
        elif skill.name == "mes_traceability":
            calls = self._build_traceability_calls(intent, entities)
        elif skill.name == "mes_scheduling":
            calls = self._build_scheduling_calls(intent, entities)
        elif skill.name == "mes_master_data":
            calls = self._build_master_data_calls(intent, entities)
        elif skill.name == "mes_error_diagnosis":
            calls = self._build_error_diagnosis_calls(intent, entities)
        elif skill.name == "mes_delay_prediction":
            calls = self._build_delay_prediction_calls(intent, entities)
        elif skill.name == "mes_defect_analysis":
            calls = self._build_defect_analysis_calls(intent, entities)
        elif skill.name == "mes_comparison":
            calls = self._build_comparison_calls(intent, entities)
        elif skill.name == "mes_tool_management":
            calls = self._build_tool_management_calls(intent, entities)
        else:
            # Default: use first endpoint
            if skill.api_endpoints:
                calls = [
                    APICall(
                        endpoint=skill.api_endpoints[0],
                        result_key="result",
                    )
                ]

        # Determine execution mode
        has_dependencies = any(c.depends_on for c in calls)
        execution_mode = ExecutionMode.SEQUENTIAL if has_dependencies else ExecutionMode.PARALLEL

        return OrchestrationPlan(
            calls=calls,
            execution_mode=execution_mode,
            output_type=skill.output_type,
            skill_name=skill.name,
        )

    def _build_production_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """생산 조회용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (date, lot_no 등)

        Returns:
            API 호출 목록

        """
        calls = []

        if intent == Intent.PRODUCTION_STATUS:
            # Use aggregated endpoint
            params = {}
            if "date" in entities:
                params["target_date"] = self._resolve_date(entities["date"])

            calls.append(
                APICall(
                    endpoint="/api/v1/analytics/daily-status",
                    params=params,
                    result_key="daily_status",
                )
            )

        elif intent == Intent.PRODUCTION_DETAIL:
            # Get specific LOT details
            lot_no = entities.get("lot_no")
            if lot_no:
                calls.append(
                    APICall(
                        endpoint="/api/v1/production/orders",
                        params={"lot_no": lot_no},
                        result_key="orders",
                    )
                )
                calls.append(
                    APICall(
                        endpoint="/api/v1/production/results",
                        params={"lot_no": lot_no},
                        result_key="results",
                    )
                )

        return calls

    def _build_equipment_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """설비 조회용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (equipment_id, equipment_type, status 등)

        Returns:
            API 호출 목록

        """
        calls = []

        params = {}
        if "equipment_type" in entities:
            params["equipment_type"] = entities["equipment_type"]
        if "status" in entities:
            params["status"] = entities["status"]

        if "equipment_id" in entities:
            # Single equipment status
            calls.append(
                APICall(
                    endpoint=f"/api/v1/masters/equipments/{entities['equipment_id']}/status",
                    params={"refresh": "true"},
                    result_key="equipment_status",
                )
            )
        else:
            # List all equipment
            calls.append(
                APICall(
                    endpoint="/api/v1/masters/equipments",
                    params=params,
                    result_key="equipments",
                )
            )

        return calls

    def _build_kpi_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """KPI 조회용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (date, metric, date_range 등)

        Returns:
            API 호출 목록

        """
        calls = []

        if intent == Intent.KPI_QUERY:
            # Check if specific date is requested
            if "date" in entities:
                # Use daily-status endpoint for date-specific KPIs
                params = {"target_date": self._resolve_date(entities["date"])}
                calls.append(
                    APICall(
                        endpoint="/api/v1/analytics/daily-status",
                        params=params,
                        result_key="daily_status",
                    )
                )
            else:
                # Use kpis endpoint for today's dashboard KPIs
                calls.append(
                    APICall(
                        endpoint="/api/v1/analytics/kpis",
                        result_key="kpis",
                    )
                )

        elif intent == Intent.ANALYTICS:
            # Trend data
            params = {"days": 7}
            if "metric" in entities:
                params["metric"] = entities["metric"]
            if "date_range" in entities:
                # Map date_range to days
                range_to_days = {
                    "this_week": 7,
                    "last_week": 7,
                    "last_7_days": 7,
                    "this_month": 30,
                    "last_month": 30,
                    "last_30_days": 30,
                }
                params["days"] = range_to_days.get(entities["date_range"], 7)

            calls.append(
                APICall(
                    endpoint="/api/v1/analytics/trends",
                    params=params,
                    result_key="trends",
                )
            )

        elif intent == Intent.COMPARISON:
            # Equipment utilization comparison
            params = {"days": 7}
            if "equipment_ids" in entities:
                params["equipment_ids"] = entities["equipment_ids"]

            calls.append(
                APICall(
                    endpoint="/api/v1/analytics/equipment-utilization",
                    params=params,
                    result_key="utilization",
                )
            )

        return calls

    def _build_traceability_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """LOT 추적용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (lot_no 필수)

        Returns:
            API 호출 목록

        """
        calls = []

        lot_no = entities.get("lot_no")
        if lot_no:
            calls.append(
                APICall(
                    endpoint=f"/api/v1/analytics/traceability/{lot_no}",
                    result_key="traceability",
                )
            )

        return calls

    def _build_scheduling_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """스케줄링용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트 (SCHEDULE_REQUEST 또는 SCHEDULE_QUERY)
            entities: 추출된 엔티티 (horizon_hours, solver_type 등)

        Returns:
            API 호출 목록

        """
        calls = []

        if intent == Intent.SCHEDULE_REQUEST:
            # Execute scheduling solve
            params = {
                "horizon_hours": entities.get("horizon_hours", 24),
                "include_running": entities.get("include_running", False),
                "solver_type": entities.get("solver_type", "OR_TOOLS"),
                "time_limit_sec": entities.get("time_limit_sec", 60),
            }

            calls.append(
                APICall(
                    endpoint="/api/v1/scheduler/solve",
                    method="POST",
                    params=params,
                    result_key="scheduling_result",
                    timeout=300,  # 5 minutes for scheduling solve
                )
            )
        else:
            # SCHEDULE_QUERY: Query scheduled/running work orders from MES.
            # /api/v1/scheduler/current-schedule does not exist in MES v5;
            # use the production orders endpoint filtered by SCHEDULED/RUNNING status.
            params: Dict[str, Any] = {"status": "SCHEDULED,RUNNING"}
            if "date" in entities:
                params["target_date"] = self._resolve_date(entities["date"])
            if "equipment_ids" in entities:
                params["equipment_ids"] = entities["equipment_ids"]

            calls.append(
                APICall(
                    endpoint="/api/v1/production/orders",
                    params=params,
                    result_key="schedule",
                )
            )

        return calls

    def _build_master_data_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """마스터 데이터 조회용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (product_id, product_code, process_code 등)

        Returns:
            API 호출 목록

        """
        calls = []

        if "product_id" in entities or "product_code" in entities:
            params = {}
            if "product_code" in entities:
                params["code"] = entities["product_code"]
            calls.append(
                APICall(
                    endpoint="/api/v1/masters/products",
                    params=params,
                    result_key="products",
                )
            )
        elif "process_code" in entities:
            calls.append(
                APICall(
                    endpoint="/api/v1/masters/std-processes",
                    params={"code": entities["process_code"]},
                    result_key="processes",
                )
            )
        else:
            # Default: get products list
            calls.append(
                APICall(
                    endpoint="/api/v1/masters/products",
                    result_key="products",
                )
            )

        return calls

    def _resolve_date_params(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """날짜 엔티티를 API 파라미터로 변환.

        Args:
            entities: 추출된 엔티티 (date, date_range 등)

        Returns:
            API 파라미터 딕셔너리 (target_date, start_date, end_date)

        """
        resolved = {}

        # 단일 날짜
        if "date" in entities:
            resolved["target_date"] = self._resolve_date(entities["date"])

        # 날짜 범위
        if "date_range" in entities:
            date_range = entities["date_range"]
            bounds = DateRangeResolver.to_dict(date_range)
            resolved["start_date"] = bounds["start_date"]
            resolved["end_date"] = bounds["end_date"]

        return resolved

    def _build_error_diagnosis_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """에러 진단용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (equipment_id, alarm_code 등)

        Returns:
            API 호출 목록

        """
        calls = []

        if "equipment_id" in entities:
            # 특정 설비 상태 조회
            calls.append(
                APICall(
                    endpoint=f"/api/v1/masters/equipments/{entities['equipment_id']}/status",
                    params={"refresh": "true"},
                    result_key="equipment_status",
                )
            )
        else:
            # 전체 설비 상태 조회 (에러 상태 필터)
            calls.append(
                APICall(
                    endpoint="/api/v1/masters/equipments",
                    params={"status": "ERROR"},
                    result_key="error_equipments",
                )
            )

        return calls

    def _build_delay_prediction_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """납기 지연 예측용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (date_range, status 등)

        Returns:
            API 호출 목록

        """
        calls = []

        # 진행중인 오더 조회
        params = {"status": "RUNNING"}
        date_params = self._resolve_date_params(entities)
        params.update(date_params)

        calls.append(
            APICall(
                endpoint="/api/v1/production/orders",
                params=params,
                result_key="running_orders",
            )
        )

        # 일별 현황 조회 (생산 속도 계산용)
        calls.append(
            APICall(
                endpoint="/api/v1/analytics/daily-status",
                result_key="daily_status",
            )
        )

        return calls

    def _build_defect_analysis_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """불량 분석용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (defect_type, product_id, equipment_id 등)

        Returns:
            API 호출 목록

        """
        calls = []

        params = {}
        date_params = self._resolve_date_params(entities)
        params.update(date_params)

        if "product_id" in entities:
            params["product_id"] = entities["product_id"]
        if "equipment_id" in entities:
            params["equipment_id"] = entities["equipment_id"]

        # 생산 실적 조회 (불량 데이터 포함)
        calls.append(
            APICall(
                endpoint="/api/v1/production/results",
                params=params,
                result_key="production_results",
            )
        )

        # KPI 조회 (수율 데이터)
        calls.append(
            APICall(
                endpoint="/api/v1/analytics/kpis",
                result_key="kpis",
            )
        )

        return calls

    def _build_comparison_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """비교 분석용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (group_by, metric 등)

        Returns:
            API 호출 목록

        """
        calls = []

        params = {}
        date_params = self._resolve_date_params(entities)
        params.update(date_params)

        if "group_by" in entities:
            params["group_by"] = entities["group_by"]
        if "metric" in entities:
            params["metric"] = entities["metric"]

        # 설비 가동률 비교
        calls.append(
            APICall(
                endpoint="/api/v1/analytics/equipment-utilization",
                params={"days": 30},
                result_key="utilization",
            )
        )

        # 트렌드 데이터
        calls.append(
            APICall(
                endpoint="/api/v1/analytics/trends",
                params={"days": 30},
                result_key="trends",
            )
        )

        return calls

    def _build_tool_management_calls(
        self,
        intent: Intent,
        entities: Dict[str, Any],
    ) -> List[APICall]:
        """공구 관리용 API 호출 목록 생성.

        Args:
            intent: 분류된 인텐트
            entities: 추출된 엔티티 (equipment_id, tool_id 등)

        Returns:
            API 호출 목록

        """
        calls = []

        params = {}
        if "equipment_id" in entities:
            params["equipment_id"] = entities["equipment_id"]

        # 설비 정보 조회 (공구 데이터는 설비에 연결됨)
        calls.append(
            APICall(
                endpoint="/api/v1/masters/equipments",
                params=params,
                result_key="equipments",
            )
        )

        return calls
