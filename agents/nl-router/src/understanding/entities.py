"""Entity definitions for MES domain queries"""

from enum import Enum
from typing import Any, Optional, List
from datetime import date, timedelta
import re
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Supported entity types for MES domain"""

    # Time-related
    DATE = "date"  # 특정 날짜 (오늘, 어제, 2024-01-24)
    DATE_RANGE = "date_range"  # 기간 (이번 주, 지난 달, 최근 7일)
    TIME = "time"  # 시간

    # Production-related
    LOT_NO = "lot_no"  # LOT 번호
    WORK_ORDER_ID = "work_order_id"  # 작업지시 ID
    STATUS = "status"  # 상태 (RUNNING, DONE, ERROR)

    # Equipment-related
    EQUIPMENT_ID = "equipment_id"  # 설비 ID
    EQUIPMENT_NAME = "equipment_name"  # 설비 이름
    EQUIPMENT_TYPE = "equipment_type"  # 설비 타입 (CNC, ROBOT, PLC)

    # Product-related
    PRODUCT_ID = "product_id"  # 제품 ID
    PRODUCT_CODE = "product_code"  # 제품 코드
    PRODUCT_NAME = "product_name"  # 제품명

    # Process-related
    PROCESS_CODE = "process_code"  # 공정 코드
    PROCESS_NAME = "process_name"  # 공정명

    # Metrics
    METRIC = "metric"  # KPI 지표 (yield, utilization, production)
    GROUP_BY = "group_by"  # 그룹핑 기준 (equipment, product, day)

    # Action
    ACTION_TYPE = "action_type"  # 액션 타입 (create_order, sync_equipment)

    # Quantity
    QUANTITY = "quantity"  # 수량
    LIMIT = "limit"  # 조회 제한

    # Error/Alarm
    ALARM_CODE = "alarm_code"  # 알람 코드 (AL-001, E-123)

    # Quality
    DEFECT_TYPE = "defect_type"  # 불량 유형 (치수불량, 외관불량)

    # Shift/Time
    SHIFT = "shift"  # 근무조 (주간, 야간, 1조)
    TIME_RANGE = "time_range"  # 시간대 (오전, 오후)

    # Comparison
    COMPARISON_TARGET = "comparison_target"  # 비교 대상


class Entity(BaseModel):
    """Extracted entity from user query"""

    type: EntityType = Field(..., description="Entity type")
    value: Any = Field(..., description="Extracted value")
    raw_text: str = Field(..., description="Original text that was extracted")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")
    normalized: Optional[Any] = Field(None, description="Normalized value")


class ExtractedEntities(BaseModel):
    """Collection of extracted entities"""

    entities: List[Entity] = Field(default_factory=list)

    def get(self, entity_type: EntityType) -> Optional[Entity]:
        """Get first entity of given type"""
        for e in self.entities:
            if e.type == entity_type:
                return e
        return None

    def get_all(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of given type"""
        return [e for e in self.entities if e.type == entity_type]

    def get_value(self, entity_type: EntityType, default: Any = None) -> Any:
        """Get value of first entity of given type"""
        entity = self.get(entity_type)
        return entity.normalized or entity.value if entity else default

    def has(self, entity_type: EntityType) -> bool:
        """Check if entity type exists"""
        return any(e.type == entity_type for e in self.entities)

    def to_dict(self) -> dict:
        """Convert to dictionary for API parameters"""
        result = {}
        for e in self.entities:
            key = e.type.value
            value = e.normalized if e.normalized is not None else e.value
            if key in result:
                # Convert to list if multiple values
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        return result


# Entity normalization rules
DATE_KEYWORDS = {
    # 과거
    "오늘": lambda: date.today(),
    "today": lambda: date.today(),
    "어제": lambda: date.today() - timedelta(days=1),
    "yesterday": lambda: date.today() - timedelta(days=1),
    "그저께": lambda: date.today() - timedelta(days=2),
    "그제": lambda: date.today() - timedelta(days=2),
    # 미래
    "내일": lambda: date.today() + timedelta(days=1),
    "tomorrow": lambda: date.today() + timedelta(days=1),
    "모레": lambda: date.today() + timedelta(days=2),
}

DATE_RANGE_KEYWORDS = {
    # 현재
    "이번 주": "this_week",
    "이번주": "this_week",
    "this week": "this_week",
    "이번 달": "this_month",
    "이번달": "this_month",
    "this month": "this_month",
    # 과거
    "지난 주": "last_week",
    "지난주": "last_week",
    "last week": "last_week",
    "지난 달": "last_month",
    "지난달": "last_month",
    "last month": "last_month",
    "최근 7일": "last_7_days",
    "last 7 days": "last_7_days",
    "최근 30일": "last_30_days",
    "last 30 days": "last_30_days",
    # 미래
    "다음 주": "next_week",
    "다음주": "next_week",
    "next week": "next_week",
    "다음 달": "next_month",
    "다음달": "next_month",
    "next month": "next_month",
}

STATUS_KEYWORDS = {
    "진행중": "RUNNING",
    "running": "RUNNING",
    "완료": "DONE",
    "done": "DONE",
    "대기": "READY",
    "ready": "READY",
    "에러": "ERROR",
    "error": "ERROR",
    "오류": "ERROR",
}

EQUIPMENT_TYPE_KEYWORDS = {
    "cnc": "CNC",
    "씨엔씨": "CNC",
    "로봇": "ROBOT",
    "robot": "ROBOT",
    "plc": "PLC",
}

METRIC_KEYWORDS = {
    "가동률": "utilization",
    "utilization": "utilization",
    "수율": "yield",
    "yield": "yield",
    "생산량": "production",
    "production": "production",
    "완료율": "completion",
    "completion": "completion",
}

GROUP_BY_KEYWORDS = {
    "설비별": "equipment",
    "by equipment": "equipment",
    "제품별": "product",
    "by product": "product",
    "일별": "day",
    "by day": "day",
    "daily": "day",
}

DEFECT_KEYWORDS = {
    "치수불량": "DIMENSION",
    "치수 불량": "DIMENSION",
    "외경불량": "DIMENSION",
    "내경불량": "DIMENSION",
    "외관불량": "SURFACE",
    "외관 불량": "SURFACE",
    "스크래치": "SCRATCH",
    "크랙": "CRACK",
    "버": "BURR",
    "버어": "BURR",
}

SHIFT_KEYWORDS = {
    "주간": "DAY_SHIFT",
    "야간": "NIGHT_SHIFT",
    "1조": "SHIFT_1",
    "2조": "SHIFT_2",
    "3조": "SHIFT_3",
    "주간조": "DAY_SHIFT",
    "야간조": "NIGHT_SHIFT",
}

TIME_RANGE_KEYWORDS = {
    "오전": "AM",
    "오후": "PM",
    "아침": "MORNING",
    "점심": "NOON",
    "저녁": "EVENING",
}


class DateRangeResolver:
    """시맨틱 날짜 범위를 실제 날짜로 변환"""

    @staticmethod
    def resolve(date_range: str, reference_date: date = None) -> tuple:
        """
        날짜 범위 문자열을 실제 (start_date, end_date) 튜플로 변환

        Args:
            date_range: "this_week", "last_month", "last_7_days" 등
            reference_date: 기준 날짜 (기본: 오늘)

        Returns:
            (start_date, end_date) 튜플
        """
        ref = reference_date or date.today()

        if date_range == "this_week":
            start = ref - timedelta(days=ref.weekday())
            end = start + timedelta(days=6)
        elif date_range == "last_week":
            start = ref - timedelta(days=ref.weekday() + 7)
            end = start + timedelta(days=6)
        elif date_range == "next_week":
            start = ref + timedelta(days=(7 - ref.weekday()))
            end = start + timedelta(days=6)
        elif date_range == "this_month":
            start = ref.replace(day=1)
            # 다음 달 1일 - 1일 = 이번 달 마지막 날
            if ref.month == 12:
                end = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = ref.replace(month=ref.month + 1, day=1) - timedelta(days=1)
        elif date_range == "last_month":
            # 이번 달 1일 - 1일 = 지난 달 마지막 날
            last_day_prev = ref.replace(day=1) - timedelta(days=1)
            start = last_day_prev.replace(day=1)
            end = last_day_prev
        elif date_range == "next_month":
            if ref.month == 12:
                start = ref.replace(year=ref.year + 1, month=1, day=1)
                end = ref.replace(year=ref.year + 1, month=2, day=1) - timedelta(days=1)
            else:
                start = ref.replace(month=ref.month + 1, day=1)
                if ref.month + 1 == 12:
                    end = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end = ref.replace(month=ref.month + 2, day=1) - timedelta(days=1)
        else:
            # last_N_days 패턴 처리
            match = re.match(r"last_(\d+)_days", date_range)
            if match:
                days = int(match.group(1))
                start = ref - timedelta(days=days - 1)
                end = ref
            else:
                # 기본값: 오늘
                start = ref
                end = ref

        return (start, end)

    @staticmethod
    def to_dict(date_range: str, reference_date: date = None) -> dict:
        """
        날짜 범위를 API 파라미터용 딕셔너리로 변환

        Returns:
            {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
        """
        start, end = DateRangeResolver.resolve(date_range, reference_date)
        return {"start_date": start.isoformat(), "end_date": end.isoformat()}
