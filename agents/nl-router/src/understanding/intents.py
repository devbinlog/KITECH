"""Intent definitions for MES domain queries"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Intent(str, Enum):
    """Supported query intents for MES domain"""

    # Production related
    PRODUCTION_STATUS = "production_status"  # 생산 현황, 작업지시, 생산실적
    PRODUCTION_DETAIL = "production_detail"  # 특정 LOT/작업지시 상세

    # Equipment related
    EQUIPMENT_STATUS = "equipment_status"  # 설비 상태, 모니터링
    EQUIPMENT_LIST = "equipment_list"  # 설비 목록 조회

    # Scheduling related
    SCHEDULE_QUERY = "schedule_query"  # 스케줄 조회
    SCHEDULE_REQUEST = "schedule_request"  # 스케줄링 요청

    # Master data related
    MASTER_DATA_QUERY = "master_data_query"  # 제품/공정 마스터 조회

    # KPI and analytics
    KPI_QUERY = "kpi_query"  # KPI 조회 (가동률, 수율)
    ANALYTICS = "analytics"  # 트렌드 분석, 예측
    COMPARISON = "comparison"  # 비교 분석

    # Traceability
    TRACEABILITY = "traceability"  # LOT 추적, 이력 조회

    # Error and Alarm
    ERROR_DIAGNOSIS = "error_diagnosis"  # 알람/에러 진단

    # Delay Prediction
    DELAY_PREDICTION = "delay_prediction"  # 납기 지연 예측

    # Defect Analysis
    DEFECT_ANALYSIS = "defect_analysis"  # 불량 원인 분석

    # Tool Management
    TOOL_MANAGEMENT = "tool_management"  # 공구 수명/교체 관리

    # Actions
    ACTION_REQUEST = "action_request"  # 작업지시 생성, 설비 동기화

    # Help
    HELP = "help"  # 도움말, 사용법 안내

    # Unknown
    UNKNOWN = "unknown"  # 분류 불가


class IntentResult(BaseModel):
    """Result of intent classification"""

    intent: Intent = Field(..., description="Classified intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    sub_intent: Optional[str] = Field(None, description="More specific sub-intent")
    reasoning: Optional[str] = Field(None, description="Classification reasoning")
    requires_clarification: bool = Field(False, description="Needs user clarification")
    suggested_questions: List[str] = Field(default_factory=list, description="Follow-up questions")


# Intent metadata for routing
INTENT_METADATA = {
    Intent.PRODUCTION_STATUS: {
        "description": "생산 현황 조회 - 작업지시, 생산실적 요약",
        "skills": ["mes_production_query"],
        "required_entities": [],
        "optional_entities": ["date", "date_range", "status"],
        "output_type": "dashboard",
    },
    Intent.PRODUCTION_DETAIL: {
        "description": "특정 LOT 또는 작업지시 상세 조회",
        "skills": ["mes_production_query", "mes_traceability"],
        "required_entities": ["lot_no"],
        "optional_entities": [],
        "output_type": "detail",
    },
    Intent.EQUIPMENT_STATUS: {
        "description": "설비 상태 조회 - 실시간 모니터링",
        "skills": ["mes_equipment_status"],
        "required_entities": [],
        "optional_entities": ["equipment_id", "equipment_type"],
        "output_type": "status_grid",
    },
    Intent.EQUIPMENT_LIST: {
        "description": "설비 목록 조회",
        "skills": ["mes_equipment_status"],
        "required_entities": [],
        "optional_entities": ["equipment_type", "status"],
        "output_type": "list",
    },
    Intent.SCHEDULE_QUERY: {
        "description": "스케줄 조회",
        "skills": ["mes_scheduling"],
        "required_entities": [],
        "optional_entities": ["date_range", "equipment_ids"],
        "output_type": "gantt",
    },
    Intent.SCHEDULE_REQUEST: {
        "description": "스케줄링 실행 요청 - 최적화 스케줄 생성",
        "skills": ["mes_scheduling"],
        "required_entities": [],
        "optional_entities": ["horizon_hours", "include_running", "solver_type"],
        "output_type": "gantt",
    },
    Intent.KPI_QUERY: {
        "description": "KPI 지표 조회 - 가동률, 수율, 생산량",
        "skills": ["mes_kpi_query"],
        "required_entities": [],
        "optional_entities": ["metric", "date_range", "group_by"],
        "output_type": "kpi_dashboard",
    },
    Intent.ANALYTICS: {
        "description": "트렌드 분석, 추이 조회",
        "skills": ["mes_kpi_query", "mes_analytics"],
        "required_entities": [],
        "optional_entities": ["metric", "date_range"],
        "output_type": "chart",
    },
    Intent.COMPARISON: {
        "description": "비교 분석 - 설비별, 제품별 비교",
        "skills": ["mes_kpi_query"],
        "required_entities": ["group_by"],
        "optional_entities": ["metric", "date_range"],
        "output_type": "comparison_chart",
    },
    Intent.TRACEABILITY: {
        "description": "LOT 추적 - 생산 이력 조회",
        "skills": ["mes_traceability"],
        "required_entities": ["lot_no"],
        "optional_entities": [],
        "output_type": "traceability_timeline",
    },
    Intent.ERROR_DIAGNOSIS: {
        "description": "알람/에러 진단 - 설비 알람 해석 및 해결책 제시",
        "skills": ["mes_error_diagnosis"],
        "required_entities": [],
        "optional_entities": ["equipment_id", "alarm_code"],
        "output_type": "diagnosis_panel",
    },
    Intent.DELAY_PREDICTION: {
        "description": "납기 지연 예측 - 위험 오더 식별",
        "skills": ["mes_delay_prediction"],
        "required_entities": [],
        "optional_entities": ["date_range", "status"],
        "output_type": "risk_dashboard",
    },
    Intent.DEFECT_ANALYSIS: {
        "description": "불량 원인 분석 - 불량률 추이 및 원인 파레토",
        "skills": ["mes_defect_analysis"],
        "required_entities": [],
        "optional_entities": ["defect_type", "product_id", "equipment_id", "date_range"],
        "output_type": "analysis_dashboard",
    },
    Intent.TOOL_MANAGEMENT: {
        "description": "공구 관리 - 수명 예측, 교체 일정",
        "skills": ["mes_tool_management"],
        "required_entities": [],
        "optional_entities": ["equipment_id", "tool_id"],
        "output_type": "tool_status",
    },
    Intent.MASTER_DATA_QUERY: {
        "description": "마스터 데이터 조회 - 제품, 공정",
        "skills": ["mes_master_data"],
        "required_entities": [],
        "optional_entities": ["product_id", "product_code", "process_code"],
        "output_type": "list",
    },
    Intent.ACTION_REQUEST: {
        "description": "액션 요청 - 작업지시 생성, 설비 동기화",
        "skills": ["mes_action"],
        "required_entities": ["action_type"],
        "optional_entities": [],
        "output_type": "confirmation",
    },
    Intent.HELP: {
        "description": "도움말 - 시스템 사용법 안내",
        "skills": ["help"],
        "required_entities": [],
        "optional_entities": ["topic"],
        "output_type": "help",
    },
    Intent.UNKNOWN: {
        "description": "분류 불가 - 도움말 제공",
        "skills": [],
        "required_entities": [],
        "optional_entities": [],
        "output_type": "help",
    },
}


def get_intent_metadata(intent: Intent) -> Dict[str, Any]:
    """Get metadata for an intent"""
    return INTENT_METADATA.get(intent, INTENT_METADATA[Intent.UNKNOWN])
