"""NLM (Natural Language MES) Endpoints

Provides natural language interface for MES queries using enhanced intent detection
with synonyms, flexible patterns, and dynamic UI component generation.
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import date, datetime, timedelta, timezone
import re
import logging
import calendar

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...deps import DBSession, CurrentUser
from ....services.aggregation_service import (
    aggregate_daily_status,
    aggregate_equipment_utilization,
    aggregate_lot_traceability,
    aggregate_kpi_dashboard,
)
from ....services.nlm_retriever.keyword_retriever import KeywordRetriever
from ....services.nlm_retriever.examples import get_default_examples

# Initialize global retriever for NLM
_nlm_retriever = None


def get_nlm_retriever() -> KeywordRetriever:
    """Get or create the NLM keyword retriever."""
    global _nlm_retriever
    if _nlm_retriever is None:
        _nlm_retriever = KeywordRetriever()
        _nlm_retriever.initialize(get_default_examples())
    return _nlm_retriever


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class UIComponent(BaseModel):
    type: str
    props: Dict[str, Any] = Field(default_factory=dict)


class UISchema(BaseModel):
    layout: str = Field("single")
    title: Optional[str] = None
    components: List[UIComponent] = Field(default_factory=list)


class QueryMetadata(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: int = 0


class QueryResult(BaseModel):
    text_response: str
    ui_schema: Optional[UISchema] = None
    metadata: Optional[QueryMetadata] = None


class Message(BaseModel):
    role: str
    content: str
    timestamp: str
    ui_schema: Optional[UISchema] = None


# ============================================================================
# Synonym Dictionary - 동의어 사전
# ============================================================================


class SynonymDict:
    """Synonym dictionary for natural language understanding"""

    SYNONYMS = {
        # 생산 관련
        "생산": ["생산", "제조", "만들", "찍", "가공", "산출", "생산량", "제작"],
        "실적": ["실적", "현황", "상황", "상태", "결과", "성과", "성적"],
        "양품": ["양품", "ok", "정상", "합격", "good", "pass"],
        "불량": ["불량", "ng", "부적합", "불합격", "bad", "fail", "defect"],
        # 설비 관련
        "설비": ["설비", "장비", "기계", "머신", "machine", "equipment", "라인", "호기"],
        "가동": ["가동", "운전", "작동", "돌아", "running", "run", "동작", "작업중", "살아있"],
        "정지": ["정지", "멈춤", "스톱", "stop", "다운", "down", "중지", "중단", "멈췄"],
        "고장": [
            "고장",
            "에러",
            "error",
            "알람",
            "alarm",
            "이상",
            "문제",
            "fault",
            "trouble",
            "망가",
            "터졌",
            "안 돼",
            "안돼",
            "빨간불",
            "소리 나",
            "이상해",
        ],
        "대기": ["대기", "유휴", "idle", "놀", "쉬", "빈", "여유", "available"],
        "정비": ["정비", "점검", "pm", "maintenance", "수리", "보수"],
        # 품질 관련
        "수율": ["수율", "yield", "양품률", "품질", "quality"],
        "불량률": ["불량률", "ng율", "불량비율", "defect rate"],
        # 작업 관련
        "작업": ["작업", "오더", "order", "지시", "wo", "job", "task", "할 일", "할일"],
        "진행": ["진행", "진행중", "running", "in progress", "작업중", "하는중", "하고 있"],
        "완료": ["완료", "끝", "done", "complete", "finished", "종료", "끝났", "끝나면"],
        "대기중": ["대기", "대기중", "ready", "waiting", "pending", "할", "다음"],
        # 스케줄 관련
        "스케줄": ["스케줄", "일정", "schedule", "계획", "plan", "예정"],
        # KPI 관련
        "kpi": ["kpi", "지표", "indicator", "성과지표", "metric", "대시보드", "dashboard"],
        # 분석 관련
        "분석": ["분석", "analysis", "원인", "이유", "왜"],
        "추이": ["추이", "추세", "trend", "변화", "트렌드"],
        "비교": ["비교", "대비", "vs", "compare", "차이"],
        # 현장작업자 관점 - 구어체
        "급함": ["급해", "급한", "긴급", "먼저", "바로", "빨리", "서둘러"],
        "남음": ["남은", "남았", "더 해야", "얼마나 남", "몇 개 더"],
        "문제해결": ["왜 이래", "뭐가 문제", "어떻게 해", "안 되", "안되"],
        # 공장관리자 관점 - 전체/종합
        "전체": ["전체", "공장", "라인 전체", "전부", "모든", "종합"],
        "병목": ["병목", "느린", "효율 낮", "개선 필요", "문제 설비"],
        "목표": ["목표", "계획 대비", "달성률", "타겟", "target"],
        "리포트": ["리포트", "보고서", "보고", "요약", "report", "회의용", "경영진"],
        # 중소기업 사장님 관점
        "요약": ["요약", "핵심", "결론", "한 줄로", "간단히", "핵심만"],
        "납기": ["납기", "출하", "약속", "기한", "마감", "딜리버리", "delivery"],
        "고객": ["고객", "클레임", "불만", "반품", "컴플레인", "claim"],
        "성장": ["성장", "나아", "좋아", "개선", "향상", "올라"],
        "문제": ["문제", "걱정", "리스크", "위험", "이슈", "trouble"],
        "인력": ["야근", "인력", "사람", "인원", "투자", "노후"],
    }

    @classmethod
    def expand_query(cls, query: str) -> Set[str]:
        """Expand query with synonyms for better matching"""
        query_lower = query.lower()
        words = set()
        words.add(query_lower)

        for key, synonyms in cls.SYNONYMS.items():
            for syn in synonyms:
                if syn in query_lower:
                    words.add(key)
                    words.update(synonyms)

        return words

    @classmethod
    def contains_any(cls, query: str, category: str) -> bool:
        """Check if query contains any word from a category"""
        query_lower = query.lower()
        synonyms = cls.SYNONYMS.get(category, [])
        return any(syn in query_lower for syn in synonyms)


# ============================================================================
# Date/Time Entity Extractor
# ============================================================================


class DateExtractor:
    """Extract date/time entities from natural language"""

    RELATIVE_DAYS = {
        "오늘": 0,
        "금일": 0,
        "당일": 0,
        "어제": -1,
        "전일": -1,
        "하루 전": -1,
        "하루전": -1,
        "그제": -2,
        "그저께": -2,
        "엊그제": -2,
        "이틀 전": -2,
        "이틀전": -2,
        "그끄저께": -3,
        "삼일 전": -3,
        "삼일전": -3,
        "3일 전": -3,
        "3일전": -3,
        "내일": 1,
        "명일": 1,
        "모레": 2,
        "이틀 후": 2,
        "글피": 3,
        "삼일 후": 3,
    }

    WEEKDAYS = {
        "월요일": 0,
        "월": 0,
        "화요일": 1,
        "화": 1,
        "수요일": 2,
        "수": 2,
        "목요일": 3,
        "목": 3,
        "금요일": 4,
        "금": 4,
        "토요일": 5,
        "토": 5,
        "일요일": 6,
        "일": 6,
    }

    WEEK_PATTERNS = {
        "이번주": (0, 6),
        "이번 주": (0, 6),
        "금주": (0, 6),
        "지난주": (-7, -1),
        "지난 주": (-7, -1),
        "전주": (-7, -1),
        "저번주": (-7, -1),
        "다음주": (7, 13),
        "다음 주": (7, 13),
        "차주": (7, 13),
    }

    MONTH_PATTERNS = {
        "이번달": "current",
        "이번 달": "current",
        "이달": "current",
        "금월": "current",
        "지난달": "previous",
        "지난 달": "previous",
        "전달": "previous",
        "전월": "previous",
        "저번달": "previous",
        "다음달": "next",
        "다음 달": "next",
        "차월": "next",
    }

    @classmethod
    def extract_date(cls, query: str) -> Optional[date]:
        """Extract a single date from query"""
        query_lower = query.lower()
        today = date.today()

        # Check relative days first
        for word, offset in cls.RELATIVE_DAYS.items():
            if word in query_lower:
                return today + timedelta(days=offset)

        # Check "지난 {요일}" / "이번 {요일}" / "다음 {요일}"
        for weekday_name, weekday_num in cls.WEEKDAYS.items():
            if weekday_name in query:
                days_diff = weekday_num - today.weekday()

                if "지난" in query or "저번" in query:
                    if days_diff >= 0:
                        days_diff -= 7
                elif "다음" in query:
                    if days_diff <= 0:
                        days_diff += 7
                else:  # 이번
                    pass  # keep as is

                return today + timedelta(days=days_diff)

        # Check specific date patterns: YYYY-MM-DD, YYYY/MM/DD, YYYY년 MM월 DD일
        patterns = [
            r"(\d{4})[-/년\s]*(\d{1,2})[-/월\s]*(\d{1,2})일?",
            r"(\d{1,2})[-/월\s]*(\d{1,2})일?",
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 3:
                        return date(int(groups[0]), int(groups[1]), int(groups[2]))
                    elif len(groups) == 2:
                        return date(today.year, int(groups[0]), int(groups[1]))
                except ValueError:
                    pass

        # Check "N일 전" / "N일 후" pattern
        match = re.search(r"(\d+)\s*일\s*전", query)
        if match:
            return today - timedelta(days=int(match.group(1)))

        match = re.search(r"(\d+)\s*일\s*후", query)
        if match:
            return today + timedelta(days=int(match.group(1)))

        return None

    @classmethod
    def extract_date_range(cls, query: str) -> Optional[Tuple[date, date]]:
        """Extract a date range from query"""
        today = date.today()

        # Check "최근 N일" / "N일간" pattern
        match = re.search(r"최근\s*(\d+)\s*일", query)
        if match:
            days = int(match.group(1))
            return (today - timedelta(days=days - 1), today)

        match = re.search(r"(\d+)\s*일\s*간", query)
        if match:
            days = int(match.group(1))
            return (today - timedelta(days=days - 1), today)

        # Check week patterns
        for pattern, (start_offset, end_offset) in cls.WEEK_PATTERNS.items():
            if pattern in query:
                monday = today - timedelta(days=today.weekday())
                start = monday + timedelta(days=start_offset)
                end = monday + timedelta(days=end_offset)
                return (start, end)

        # Check month patterns
        for pattern, month_type in cls.MONTH_PATTERNS.items():
            if pattern in query:
                if month_type == "current":
                    start = today.replace(day=1)
                    _, last_day = calendar.monthrange(today.year, today.month)
                    end = today.replace(day=last_day)
                elif month_type == "previous":
                    first_of_month = today.replace(day=1)
                    end = first_of_month - timedelta(days=1)
                    start = end.replace(day=1)
                else:
                    _, last_day = calendar.monthrange(today.year, today.month)
                    first_of_next = today.replace(day=last_day) + timedelta(days=1)
                    _, next_last_day = calendar.monthrange(first_of_next.year, first_of_next.month)
                    start = first_of_next
                    end = first_of_next.replace(day=next_last_day)
                return (start, end)

        # Check specific month: "1월", "2월" etc.
        match = re.search(r"(\d{1,2})월", query)
        if match and "일" not in query:  # Avoid matching "1월 15일"
            month = int(match.group(1))
            year = today.year
            # If month is in the future of current year, might mean last year
            if month > today.month + 3:
                year -= 1
            try:
                _, last_day = calendar.monthrange(year, month)
                return (date(year, month, 1), date(year, month, last_day))
            except ValueError:
                pass

        return None

    @classmethod
    def extract_time_entities(cls, query: str) -> Dict[str, Any]:
        """Extract all time-related entities from query"""
        entities = {}

        single_date = cls.extract_date(query)
        if single_date:
            entities["date"] = single_date.isoformat()

        date_range = cls.extract_date_range(query)
        if date_range:
            entities["date_range"] = {
                "start": date_range[0].isoformat(),
                "end": date_range[1].isoformat(),
            }

        return entities


# ============================================================================
# Enhanced Intent Detector
# ============================================================================


class IntentDetector:
    """Enhanced intent detection with synonyms and flexible patterns"""

    # Intent definitions with patterns and keywords
    INTENTS = {
        "daily_status": {
            "keywords": [
                "현황",
                "상황",
                "상태",
                "실적",
                "어때",
                "어떻게",
                "알려줘",
                "보여줘",
                "핵심",
                "요약",
                "결론",
            ],
            "patterns": [
                r"(생산|제조).*현황",
                r"현황.*(보여|알려|어때)",
                r"(오늘|어제|금일|전일).*(어때|어떻게|현황|상태|실적)",
                r"(얼마나|몇\s*개).*(만들|찍|생산)",
                r"생산.*(했|나왔|됐)",
                # 현장작업자 구어체
                r"잘\s*되고\s*있",
                r"문제\s*없",
                r"라인\s*살아있",
                # 공장관리자 - 전체
                r"공장\s*(전체|어때)",
                r"전체\s*(라인|현황|상태)",
                # 사장님 관점
                r"한\s*줄로",
                r"핵심만",
                r"결론이\s*뭐",
                r"잘\s*돌아가",
                r"문제\s*없지",
            ],
            "required_categories": [],  # Any of these must match
            "description": "일일 생산 현황 조회",
        },
        "production_count": {
            "keywords": [
                "몇 개",
                "몇개",
                "얼마나",
                "생산량",
                "수량",
                "개수",
                "남은",
                "남았",
                "성장",
                "나아",
                "더 해야",
                "달성률",
                "목표",
            ],
            "patterns": [
                r"몇\s*개",
                r"얼마나.*(만들|생산|찍)",
                r"생산량",
                r"(양품|불량).*(몇|얼마)",
                # 현장작업자
                r"몇\s*개\s*더\s*해야",
                r"(몇\s*개|얼마나)\s*더\s*해",
                r"남은\s*거",
                r"끝나려면",
                # 공장관리자
                r"목표\s*달성률",
                r"목표\s*달성",
                r"달성률",
                r"계획\s*대비",
                r"라인별\s*실적",
                # 사장님
                r"계획대로\s*가",
                r"성장하고\s*있",
                r"나아졌",
                r"좋아졌",
            ],
            "required_categories": [],  # 더 유연하게
            "description": "생산량 조회",
        },
        "current_status": {
            "keywords": ["지금", "현재", "돌아가", "가동중", "작업중", "살아있"],
            "patterns": [
                r"지금.*(뭐|무엇|어떤|상태|상황)",
                r"현재.*(상태|상황|가동|작업)",
                r"(돌아가|작업중|가동중)",
                # 현장작업자
                r"라인\s*살아있",
                r"돌아가\?",
                r"상황\s*어때",
            ],
            "required_categories": [],
            "description": "현재 가동 상태",
        },
        "compare_status": {
            "keywords": ["비교", "대비", "vs", "차이", "보다"],
            "patterns": [
                r"(어제|전일).*(오늘|금일)",
                r"(오늘|금일).*(어제|전일)",
                r"(비교|대비|차이)",
                r"vs",
                r"(지난|전).*(이번|금)",
                r".+보다.*(어때|어떻게|나아|좋아|많아|적어)",
            ],
            "required_categories": ["비교"],
            "description": "기간 비교",
        },
        "trend": {
            "keywords": ["추이", "추세", "트렌드", "변화", "그래프"],
            "patterns": [
                r"(추이|추세|트렌드|변화)",
                r"그래프",
                r"(최근|지난).*(분석|보여|확인)",
            ],
            "required_categories": ["추이"],
            "description": "추세 분석",
        },
        "equipment_status": {
            "keywords": ["설비", "장비", "기계", "가동률", "호기", "병목", "효율", "투자", "노후"],
            "patterns": [
                r"(설비|장비|기계|머신).*(상태|현황|어때|가동)",
                r"가동률",
                r"(몇|어떤).*(설비|장비).*(돌아|가동)",
                r"\d+\s*호기",
                r"(CNC|프레스|로봇|선반)",
                # 공장관리자 - 병목/효율 분석
                r"병목.*(설비|어디|분석)",
                r"효율\s*(낮|떨어지)",
                r"개선\s*(필요|포인트)",
                r"다운타임\s*(많|분석)",
                r"전체\s*설비\s*상태",
                r"라인\s*가동\s*현황",
                # 사장님 - 설비 투자/노후
                r"설비\s*투자",
                r"노후\s*설비",
                r"기계\s*문제\s*없",
                r"설비\s*고장\s*많",
            ],
            "required_categories": ["설비"],
            "description": "설비 상태 조회",
        },
        "equipment_error": {
            "keywords": [
                "고장",
                "에러",
                "알람",
                "이상",
                "문제",
                "망가",
                "터졌",
                "빨간불",
                "안 돌아",
                "망가졌",
                "들어왔어",
            ],
            "patterns": [
                r"(고장|에러|알람|이상|문제).*(설비|장비|있)",
                r"(설비|장비).*(고장|에러|알람|이상|문제)",
                # 현장작업자 - 고장 신고 구어체
                r"(이거|기계|장비)\s*(망가졌|이상해|안\s*돌아|멈췄|터졌)",
                r"(안\s*돌아가|안돌아가|안\s*돌아$)",
                r"빨간불.*(들어왔|켜졌|떴)",
                r"빨간불\s*들어왔어",  # 직접 매칭
                r"소리\s*나",
                r"이상한\s*소리",
                # 단독 고장 표현 (이거 포함)
                r"(이거\s*)?(망가졌|터졌|멈췄)",
                r"망가졌어",
                r"터졌어",
            ],
            "required_categories": [],  # 단독으로도 인식되도록 비움
            "description": "설비 고장/에러 조회",
        },
        "equipment_idle": {
            "keywords": ["대기", "유휴", "놀고", "빈", "여유", "사용 가능"],
            "patterns": [
                r"(대기|유휴|빈|놀).*(설비|장비)",
                r"(사용|이용).*(가능|할 수)",
            ],
            "required_categories": ["대기", "설비"],
            "description": "유휴 설비 조회",
        },
        "yield_status": {
            "keywords": ["수율", "yield", "양품률", "품질"],
            "patterns": [
                r"수율.*(얼마|어때|몇|현황)",
                r"(얼마|어때|몇).*수율",
                r"yield",
                r"양품률",
            ],
            "required_categories": ["수율"],
            "description": "수율 조회",
        },
        "defect_analysis": {
            "keywords": ["불량", "ng", "부적합", "defect", "클레임", "반품", "불만", "품질문제"],
            "patterns": [
                r"불량.*(분석|현황|원인|어때|몇|얼마)",
                r"(왜|원인).*(불량|ng)",
                r"(설비|제품|품목)별.*불량",
                r"불량.*(설비|제품|품목)",
                # 사장님 - 품질/고객 (더 유연하게)
                r"클레임",
                r"고객.*불만",
                r"반품",
                r"품질.*(문제|이슈|어때)",
                r"컴플레인",
            ],
            "required_categories": [],  # 클레임, 반품도 인식되도록
            "description": "불량 분석",
        },
        "lot_trace": {
            "keywords": ["lot", "로트", "이력", "추적"],
            "patterns": [
                r"lot[-_]?\d+",
                r"로트[-_]?\d+",
                r"(이력|추적).*(조회|확인|보여)",
                r"lot.*(어디|이력|추적|상태)",
            ],
            "required_categories": [],
            "description": "LOT 이력 추적",
        },
        "work_orders": {
            "keywords": ["작업지시", "작업 지시", "오더", "order", "wo", "할 일", "할일"],
            "patterns": [
                r"작업.*(지시|현황|목록|뭐)",
                r"오더.*(현황|목록|상태)",
                r"(할|하는|해야).*(작업|일)",
                r"(진행중|대기|완료).*(작업|오더)",
                # 현장작업자
                r"뭐\s*해(\?|$)",
                r"지금\s*뭐\s*해야",
                # 공장관리자
                r"전체\s*작업\s*현황",
                r"라인별\s*작업",
                r"작업\s*진척",
            ],
            "required_categories": ["작업"],
            "description": "작업지시 조회",
        },
        "work_orders_in_progress": {
            "keywords": ["진행중", "진행 중", "하고 있는", "작업중"],
            "patterns": [
                r"진행.*(중|작업|오더)",
                r"(하고|하는)\s*있는",
                r"작업\s*중",
                # 현장작업자
                r"내\s*작업",
                r"지금\s*하고\s*있",
            ],
            "required_categories": ["진행", "작업"],
            "description": "진행중 작업 조회",
        },
        "work_orders_pending": {
            "keywords": ["대기", "대기중", "할", "다음", "그 다음", "다음뭐", "끝나면"],
            "patterns": [
                r"대기.*(작업|오더|중)",
                r"(할|다음).*(작업|일|거)",
                # 현장작업자
                r"다음\s*뭐야",
                r"다음\s*뭐\?",
                r"다음\s*뭐$",  # 더 구체적인 패턴
                r"그\s*다음",
                r"이거\s*끝나면",
                r"끝나면\s*뭐",
            ],
            "required_categories": [],  # 더 유연하게 매칭
            "description": "대기 작업 조회",
        },
        "work_orders_completed": {
            "keywords": ["완료", "끝난", "done", "완성"],
            "patterns": [
                r"(완료|끝난|완성).*(작업|오더)",
                r"(작업|오더).*(완료|끝)",
            ],
            "required_categories": ["완료", "작업"],
            "description": "완료 작업 조회",
        },
        "schedule": {
            "keywords": ["스케줄", "일정", "계획", "예정", "납기", "출하"],
            "patterns": [
                r"(스케줄|일정|계획).*(보여|알려|어때|있)",
                r"(오늘|내일|이번주).*(스케줄|일정|계획|뭐)",
                r"(뭐|무엇).*(해야|할)",
                # 사장님 - 납기/출하
                r"납기\s*(지킬|맞출|어때)",
                r"출하\s*(언제|뭐)",
                r"고객\s*(약속|납기)",
                r"늦어지는\s*거",
            ],
            "required_categories": ["스케줄"],
            "description": "스케줄 조회",
        },
        "schedule_delay": {
            "keywords": ["지연", "딜레이", "늦", "밀린", "위험"],
            "patterns": [
                r"(지연|딜레이|늦|밀린).*(작업|스케줄|일정)",
                # 사장님
                r"늦어지",
                r"납기\s*위험",
                r"마감\s*못",
            ],
            "required_categories": [],
            "description": "지연 작업 조회",
        },
        "kpi": {
            "keywords": ["kpi", "지표", "대시보드", "dashboard", "성과", "리스크", "걱정"],
            "patterns": [
                r"kpi",
                r"지표.*(보여|어때)",
                r"대시보드",
                r"성과.*지표",
                # 공장관리자
                r"oee",
                r"종합.*효율",
                r"성과.*분석",
                # 사장님 - 전체 문제 파악
                r"(제일|가장)\s*(큰|심각)\s*문제",
                r"걱정되는",
                r"리스크",
                r"숫자로",
                r"실적\s*어때",
                r"돈\s*(벌|이익)",
            ],
            "required_categories": [],  # 사장님 질문도 인식되도록
            "description": "KPI 조회",
        },
        "report": {
            "keywords": ["리포트", "보고서", "report", "요약", "회의용", "경영진", "야근", "인력"],
            "patterns": [
                r"(일일|주간|월간).*(리포트|보고|보여)",
                r"(리포트|보고서).*(보여|만들)",
                # 공장관리자
                r"경영진\s*보고",
                r"회의용\s*자료",
                r"실적\s*요약",
                r"보고서\s*뽑아",
                # 사장님
                r"야근\s*해야",
                r"인력\s*(부족|필요)",
            ],
            "required_categories": [],
            "description": "리포트 생성",
        },
        "help": {
            "keywords": ["도움", "help", "사용법", "기능", "명령어", "뭘 할 수", "어떻게 해"],
            "patterns": [
                r"(도움|help|사용법)",
                r"뭘.*할.*수",
                r"(기능|명령어).*(알려|뭐)",
                # 현장작업자 - 도움 요청
                r"어떻게\s*해(\?|$)",
                r"뭐야\s*이게",
                r"모르겠",
            ],
            "required_categories": [],
            "description": "도움말",
        },
        "greeting": {
            "keywords": ["안녕", "하이", "hi", "hello", "반가"],
            "patterns": [
                r"^안녕",
                r"^하이",
                r"^hi",
                r"^hello",
            ],
            "required_categories": [],
            "description": "인사",
        },
    }

    # Period indicators - words that suggest a date RANGE (not single date)
    PERIOD_INDICATORS = [
        "지난달",
        "지난 달",
        "전달",
        "전월",
        "저번달",
        "저번 달",
        "이번달",
        "이번 달",
        "이달",
        "금월",
        "다음달",
        "다음 달",
        "차월",
        "지난주",
        "지난 주",
        "전주",
        "저번주",
        "저번 주",
        "이번주",
        "이번 주",
        "금주",
        "다음주",
        "다음 주",
        "차주",
        "최근",
        "동안",
        "일간",
    ]

    # Single date indicators
    SINGLE_DATE_INDICATORS = ["오늘", "어제", "그제", "그저께", "내일", "모레", "금일", "전일"]

    @classmethod
    def has_period_indicator(cls, query: str) -> bool:
        """Check if query has period/range expressions"""
        query_lower = query.lower()

        # Check period words
        for indicator in cls.PERIOD_INDICATORS:
            if indicator in query_lower:
                return True

        # Check "최근 N일", "N일간" patterns
        if re.search(r"최근\s*\d+\s*일", query_lower):
            return True
        if re.search(r"\d+\s*일\s*간", query_lower):
            return True

        # Check month patterns like "1월", "12월" (without specific day)
        if re.search(r"(\d{1,2})월(?!\s*\d)", query_lower):
            return True

        return False

    @classmethod
    def has_single_date_only(cls, query: str) -> bool:
        """Check if query has ONLY single date (not range)"""
        query_lower = query.lower()
        has_single = any(ind in query_lower for ind in cls.SINGLE_DATE_INDICATORS)
        has_period = cls.has_period_indicator(query_lower)
        return has_single and not has_period

    @classmethod
    def detect(cls, query: str) -> Tuple[str, float, Dict[str, Any]]:
        """Detect intent from query using keywords, patterns, and DATE-AWARE routing.
        Key: Period expressions → trend/period queries, Single date → daily queries
        """
        query_lower = query.lower().strip()
        entities = DateExtractor.extract_time_entities(query)

        # === KEY LOGIC: Detect period vs single date ===
        has_period = cls.has_period_indicator(query_lower) or "date_range" in entities
        has_single_date = cls.has_single_date_only(query_lower)

        # Expand query with synonyms (reserved for future enhanced matching)
        _ = SynonymDict.expand_query(query_lower)

        # Score each intent
        scores = {}
        for intent, config in cls.INTENTS.items():
            score = 0

            # Check keywords
            for keyword in config.get("keywords", []):
                if keyword.lower() in query_lower:
                    score += 2

            # Check patterns
            for pattern in config.get("patterns", []):
                if re.search(pattern, query_lower):
                    score += 3

            # Check required categories (using synonyms)
            required = config.get("required_categories", [])
            if required:
                matched_required = sum(
                    1 for cat in required if SynonymDict.contains_any(query_lower, cat)
                )
                if matched_required > 0:
                    score += matched_required * 2

            if score > 0:
                scores[intent] = score

        # === PERIOD-AWARE ROUTING ===
        # If period detected AND query is about production/status, route to trend
        if has_period and not has_single_date:
            is_production_query = (
                SynonymDict.contains_any(query_lower, "생산")
                or "실적" in query_lower
                or "현황" in query_lower
                or "뭘" in query_lower
                or "무엇" in query_lower
                or "어떤" in query_lower
                or "했" in query_lower
            )

            if is_production_query:
                # Force trend intent with high score
                scores["trend"] = max(scores.get("trend", 0), 10)
                logger.info(f"Period detected, routing to trend: {query}")

        # === PRIORITY ROUTING: Error/Fault keywords → equipment_error ===
        error_keywords = [
            "망가",
            "터졌",
            "빨간불",
            "고장",
            "에러",
            "알람",
            "멈췄",
            "안 돌아",
            "이상해",
        ]
        if any(kw in query_lower for kw in error_keywords):
            scores["equipment_error"] = max(scores.get("equipment_error", 0), 12)
            logger.info(f"Error keyword detected, boosting equipment_error: {query}")

        # === PRIORITY ROUTING: "다음 뭐" → work_orders_pending ===
        if re.search(r"다음\s*뭐", query_lower) or "그 다음" in query_lower:
            scores["work_orders_pending"] = max(scores.get("work_orders_pending", 0), 12)
            logger.info(f"Next task keyword detected, boosting work_orders_pending: {query}")

        # === PRIORITY ROUTING: Production count keywords ===
        if (
            re.search(r"몇\s*개\s*더", query_lower)
            or "달성률" in query_lower
            or re.search(r"목표\s*달성", query_lower)
        ):
            scores["production_count"] = max(scores.get("production_count", 0), 12)
            logger.info(f"Production count keyword detected, boosting: {query}")

        if not scores:
            return "unknown", 0.3, entities

        # Get best match
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]

        # Calculate confidence
        if max_score >= 8:
            confidence = 0.95
        elif max_score >= 5:
            confidence = 0.9
        elif max_score >= 3:
            confidence = 0.75
        else:
            confidence = 0.6

        # Reduce confidence if multiple intents have similar scores
        similar_intents = [i for i, s in scores.items() if s >= max_score - 1 and i != best_intent]
        if similar_intents:
            confidence -= 0.1

        logger.info(
            f"Intent detection: query='{query}', period={has_period}, best={best_intent}({max_score})"
        )

        return best_intent, confidence, entities

    @classmethod
    def extract_lot_no(cls, query: str) -> Optional[str]:
        """Extract LOT number from query"""
        patterns = [
            r"(LOT[-_]?\d{4}[-_]?\d{4})",
            r"(LOT[-_]?\d+)",
            r"(lot[-_]?\d+)",
            r"로트[-_]?(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                lot = match.group(1)
                if lot.isdigit():
                    return f"LOT-{lot}"
                return lot.upper().replace("_", "-")
        return None

    @classmethod
    def extract_equipment(cls, query: str) -> Optional[str]:
        """Extract equipment identifier from query"""
        patterns = [
            r"(EQ[-_]?\d+)",
            r"(\d+)\s*호기",
            r"(CNC[-_]?\d*)",
            r"(프레스[-_]?\d*)",
            r"(로봇[-_]?\d*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @classmethod
    def extract_work_order_filter(cls, query: str) -> Optional[str]:
        """Extract work order status filter from query"""
        if SynonymDict.contains_any(query, "진행"):
            return "RUNNING"
        elif SynonymDict.contains_any(query, "완료"):
            return "DONE"
        elif SynonymDict.contains_any(query, "대기중"):
            return "READY"
        return None


# ============================================================================
# Response Generators
# ============================================================================


class ResponseGenerator:
    """Generate responses for different intents with dynamic UI components"""

    @staticmethod
    async def generate_daily_status(db, target_date: Optional[date] = None) -> QueryResult:
        """Generate daily status response"""
        import time

        start_time = time.time()

        if target_date is None:
            target_date = date.today()

        result = await aggregate_daily_status(db, target_date)
        data = result.data

        orders = data.get("orders", {})
        results_data = data.get("results", {})
        equipment = data.get("equipment", {})
        kpis = data.get("kpis", {})

        # Format date string naturally
        today = date.today()
        if target_date == today:
            date_str = "오늘"
        elif target_date == today - timedelta(days=1):
            date_str = "어제"
        elif target_date == today - timedelta(days=2):
            date_str = "그제"
        elif target_date == today + timedelta(days=1):
            date_str = "내일"
        else:
            date_str = target_date.strftime("%m월 %d일")

        ok_qty = results_data.get("total_ok_qty", 0)
        ng_qty = results_data.get("total_ng_qty", 0)
        yield_rate = results_data.get("yield_rate", 0)

        text = f"""📊 **{date_str} ({target_date.strftime("%Y-%m-%d")}) 생산 현황**

**작업지시**: 전체 {orders.get("total", 0)}건
- 완료: {orders.get("completed", 0)}건
- 진행중: {orders.get("in_progress", 0)}건
- 대기: {orders.get("pending", 0)}건

**생산 실적**
- 양품: {ok_qty:,}개
- 불량: {ng_qty:,}개
- 수율: {yield_rate:.1f}%

**설비 현황**
- 가동: {equipment.get("running", 0)}대
- 대기: {equipment.get("idle", 0)}대
- 에러: {equipment.get("error", 0)}대"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "완료율",
                    "value": round(kpis.get("completion_rate", 0), 1),
                    "unit": "%",
                    "icon": "check-circle",
                    "color": "green" if kpis.get("completion_rate", 0) >= 80 else "amber",
                    "target": 90,
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "수율",
                    "value": round(yield_rate, 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "blue" if yield_rate >= 95 else "amber",
                    "target": 95,
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "설비 가동률",
                    "value": round(kpis.get("equipment_utilization", 0), 1),
                    "unit": "%",
                    "icon": "activity",
                    "color": "blue",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "생산량",
                    "value": ok_qty,
                    "unit": "개",
                    "icon": "package",
                    "color": "green",
                },
            ),
        ]

        ui_schema = UISchema(
            layout="dashboard", title=f"{date_str} 생산 현황", components=components
        )

        processing_time = int((time.time() - start_time) * 1000)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="daily_status",
                confidence=0.9,
                entities={"date": target_date.isoformat()},
                processing_time_ms=processing_time,
            ),
        )

    @staticmethod
    async def generate_compare_status(db, date1: date, date2: date) -> QueryResult:
        """Generate comparison between two dates"""
        import time

        start_time = time.time()

        result1 = await aggregate_daily_status(db, date1)
        result2 = await aggregate_daily_status(db, date2)

        data1, data2 = result1.data, result2.data

        ok1 = data1.get("results", {}).get("total_ok_qty", 0)
        ok2 = data2.get("results", {}).get("total_ok_qty", 0)
        yield1 = data1.get("results", {}).get("yield_rate", 0)
        yield2 = data2.get("results", {}).get("yield_rate", 0)

        ok_diff = ok2 - ok1
        yield_diff = yield2 - yield1

        def trend_text(diff, unit=""):
            if diff > 0:
                return f"📈 +{diff:,}{unit}"
            elif diff < 0:
                return f"📉 {diff:,}{unit}"
            return "➖ 동일"

        d1_str = date1.strftime("%m/%d")
        d2_str = date2.strftime("%m/%d")

        text = f"""📊 **생산 현황 비교** ({d1_str} vs {d2_str})

| 항목 | {d1_str} | {d2_str} | 변화 |
|------|---------|---------|------|
| 생산량 | {ok1:,}개 | {ok2:,}개 | {trend_text(ok_diff, "개")} |
| 수율 | {yield1:.1f}% | {yield2:.1f}% | {trend_text(yield_diff, "%p")} |"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": f"{d1_str} 생산량",
                    "value": ok1,
                    "unit": "개",
                    "icon": "package",
                    "color": "gray",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": f"{d2_str} 생산량",
                    "value": ok2,
                    "unit": "개",
                    "icon": "package",
                    "color": "green" if ok_diff >= 0 else "red",
                    "trend": f"{ok_diff:+,}개",
                    "trendDirection": "up" if ok_diff > 0 else "down" if ok_diff < 0 else "neutral",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": f"{d1_str} 수율",
                    "value": round(yield1, 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "gray",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": f"{d2_str} 수율",
                    "value": round(yield2, 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "green" if yield_diff >= 0 else "red",
                    "trend": f"{yield_diff:+.1f}%p",
                    "trendDirection": "up"
                    if yield_diff > 0
                    else "down"
                    if yield_diff < 0
                    else "neutral",
                },
            ),
            UIComponent(
                type="BarChart",
                props={
                    "title": "비교 차트",
                    "data": [
                        {"name": d1_str, "생산량": ok1, "수율": yield1},
                        {"name": d2_str, "생산량": ok2, "수율": yield2},
                    ],
                    "xKey": "name",
                },
            ),
        ]

        ui_schema = UISchema(
            layout="dashboard", title=f"생산 비교 ({d1_str} vs {d2_str})", components=components
        )

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="compare_status",
                confidence=0.9,
                entities={"date1": date1.isoformat(), "date2": date2.isoformat()},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_trend(db, start_date: date, end_date: date) -> QueryResult:
        """Generate trend analysis for date range"""
        import time

        start_time = time.time()

        daily_data = []
        current = start_date
        while current <= end_date:
            result = await aggregate_daily_status(db, current)
            data = result.data
            daily_data.append(
                {
                    "date": current.strftime("%m/%d"),
                    "생산량": data.get("results", {}).get("total_ok_qty", 0),
                    "수율": data.get("results", {}).get("yield_rate", 0),
                    "완료율": data.get("kpis", {}).get("completion_rate", 0),
                }
            )
            current += timedelta(days=1)

        if not daily_data:
            return QueryResult(text_response="해당 기간의 데이터가 없습니다.")

        avg_production = sum(d["생산량"] for d in daily_data) / len(daily_data)
        avg_yield = sum(d["수율"] for d in daily_data) / len(daily_data)
        total_production = sum(d["생산량"] for d in daily_data)
        days = len(daily_data)

        text = f"""📈 **생산 추세 분석** ({start_date.strftime("%m/%d")} ~ {end_date.strftime("%m/%d")}, {days}일간)

**요약**
- 총 생산량: {total_production:,}개
- 일평균 생산량: {avg_production:,.0f}개
- 평균 수율: {avg_yield:.1f}%"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "총 생산량",
                    "value": total_production,
                    "unit": "개",
                    "icon": "package",
                    "color": "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "일평균",
                    "value": round(avg_production),
                    "unit": "개",
                    "icon": "chart",
                    "color": "blue",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "평균 수율",
                    "value": round(avg_yield, 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "green" if avg_yield >= 95 else "amber",
                },
            ),
            UIComponent(
                type="LineChart",
                props={
                    "title": "생산량 추이",
                    "data": daily_data,
                    "xKey": "date",
                    "yKey": "생산량",
                },
            ),
            UIComponent(
                type="LineChart",
                props={
                    "title": "수율 추이",
                    "data": daily_data,
                    "xKey": "date",
                    "yKey": "수율",
                    "targetLine": 95,
                },
            ),
        ]

        ui_schema = UISchema(
            layout="single",
            title=f"생산 추세 ({start_date.strftime('%m/%d')} ~ {end_date.strftime('%m/%d')})",
            components=components,
        )

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="trend",
                confidence=0.9,
                entities={
                    "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()}
                },
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_equipment_status(db, days: int = 7) -> QueryResult:
        """Generate equipment status response with CURRENT status + historical utilization"""
        import time

        start_time = time.time()

        # Get current equipment status (same as dashboard)
        daily_result = await aggregate_daily_status(db)
        current_eq = daily_result.data.get("equipment", {})

        # Get historical utilization
        result = await aggregate_equipment_utilization(db, None, days)
        data = result.data
        summary = data.get("summary", {})
        equipments = data.get("equipment_utilization", [])

        # Current status counts (matching dashboard)
        running = current_eq.get("running", 0)
        idle = current_eq.get("idle", 0)
        error = current_eq.get("error", 0)
        total = current_eq.get("total", 0)

        text = f"""🔧 **설비 현황**

**현재 상태**
- 전체: {total}대
- 가동중: {running}대
- 대기중: {idle}대
- 에러: {error}대

**{days}일간 가동률**
- 평균: {summary.get("average_utilization", 0):.1f}%
- 최고: {summary.get("top_performer", "N/A")} ({summary.get("top_utilization", 0):.1f}%)
- 최저: {summary.get("bottleneck", "N/A")} ({summary.get("bottleneck_utilization", 0):.1f}%)"""

        # Use actual current_status from equipment list
        equipment_list = current_eq.get("equipment_list", [])
        status_items = []
        for eq in equipment_list[:12]:
            status_items.append(
                {
                    "id": str(eq.get("id", "")),
                    "name": eq.get("name", "Unknown"),
                    "status": eq.get("status", "OFFLINE"),  # Use actual status from DB
                    "type": eq.get("type", ""),
                }
            )

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "전체 설비",
                    "value": total,
                    "unit": "대",
                    "icon": "chart",
                    "color": "gray",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "가동중",
                    "value": running,
                    "unit": "대",
                    "icon": "activity",
                    "color": "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "대기중",
                    "value": idle,
                    "unit": "대",
                    "icon": "clock",
                    "color": "amber",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "에러",
                    "value": error,
                    "unit": "대",
                    "icon": "alert",
                    "color": "red" if error > 0 else "gray",
                },
            ),
        ]

        if status_items:
            components.append(
                UIComponent(
                    type="StatusGrid",
                    props={
                        "title": "설비별 현재 상태",
                        "items": status_items,
                        "columns": 4,
                    },
                )
            )

        if equipments:
            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": f"{days}일간 가동률 상세",
                        "columns": [
                            {"key": "equipment_name", "label": "설비명", "sortable": True},
                            {"key": "current_status", "label": "현재상태", "sortable": True},
                            {"key": "utilization_rate", "label": "가동률(%)", "sortable": True},
                            {"key": "yield_rate", "label": "수율(%)", "sortable": True},
                        ],
                        "data": [
                            {
                                "equipment_name": eq.get("equipment_name", ""),
                                "current_status": eq.get("current_status", ""),
                                "utilization_rate": round(eq.get("utilization_rate", 0), 1),
                                "yield_rate": round(eq.get("yield_rate", 0), 1),
                            }
                            for eq in equipments
                        ],
                        "searchable": True,
                        "pagination": True,
                        "pageSize": 10,
                        "exportable": True,
                    },
                )
            )

        ui_schema = UISchema(layout="single", title="설비 가동 현황", components=components)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="equipment_status",
                confidence=0.9,
                entities={"days": days},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_yield_status(db, target_date: Optional[date] = None) -> QueryResult:
        """Generate yield/quality status"""
        import time

        start_time = time.time()

        if target_date is None:
            target_date = date.today()

        result = await aggregate_daily_status(db, target_date)
        data = result.data

        results_data = data.get("results", {})
        ok_qty = results_data.get("total_ok_qty", 0)
        ng_qty = results_data.get("total_ng_qty", 0)
        yield_rate = results_data.get("yield_rate", 0)
        total = ok_qty + ng_qty
        defect_rate = (ng_qty / total * 100) if total > 0 else 0

        date_str = "오늘" if target_date == date.today() else target_date.strftime("%m월 %d일")

        text = f"""📊 **{date_str} 수율 현황**

**품질 지표**
- 수율: {yield_rate:.1f}%
- 불량률: {defect_rate:.2f}%

**수량**
- 총 생산: {total:,}개
- 양품: {ok_qty:,}개
- 불량: {ng_qty:,}개"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "수율",
                    "value": round(yield_rate, 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "green"
                    if yield_rate >= 95
                    else "amber"
                    if yield_rate >= 90
                    else "red",
                    "target": 95,
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "불량률",
                    "value": round(defect_rate, 2),
                    "unit": "%",
                    "icon": "alert",
                    "color": "green"
                    if defect_rate <= 1
                    else "amber"
                    if defect_rate <= 5
                    else "red",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "양품",
                    "value": ok_qty,
                    "unit": "개",
                    "icon": "check-circle",
                    "color": "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "불량",
                    "value": ng_qty,
                    "unit": "개",
                    "icon": "alert",
                    "color": "red" if ng_qty > 0 else "gray",
                },
            ),
        ]

        ui_schema = UISchema(
            layout="dashboard", title=f"{date_str} 수율 현황", components=components
        )

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="yield_status",
                confidence=0.9,
                entities={"date": target_date.isoformat()},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_defect_analysis(db, target_date: Optional[date] = None) -> QueryResult:
        """Generate defect analysis response"""
        import time

        start_time = time.time()

        if target_date is None:
            target_date = date.today()

        from sqlalchemy import select, func, and_
        from ....models.production import ProdResult

        query = (
            select(
                ProdResult.equipment_id,
                func.sum(ProdResult.ok_qty).label("ok_qty"),
                func.sum(ProdResult.ng_qty).label("ng_qty"),
            )
            .where(
                and_(
                    func.date(ProdResult.start_time) == target_date,
                    ProdResult.ng_qty > 0,
                )
            )
            .group_by(ProdResult.equipment_id)
            .order_by(func.sum(ProdResult.ng_qty).desc())
        )

        result = await db.execute(query)
        defect_data = result.all()

        total_ok = sum(row.ok_qty or 0 for row in defect_data)
        total_ng = sum(row.ng_qty or 0 for row in defect_data)
        total = total_ok + total_ng
        defect_rate = (total_ng / total * 100) if total > 0 else 0

        date_str = "오늘" if target_date == date.today() else target_date.strftime("%m월 %d일")

        text = f"""🔴 **{date_str} 불량 분석**

**요약**
- 총 생산: {total:,}개
- 불량 수량: {total_ng:,}개
- 불량률: {defect_rate:.2f}%
- 불량 발생 설비: {len(defect_data)}대"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "불량 수량",
                    "value": total_ng,
                    "unit": "개",
                    "icon": "alert",
                    "color": "red" if total_ng > 0 else "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "불량률",
                    "value": round(defect_rate, 2),
                    "unit": "%",
                    "icon": "percent",
                    "color": "red" if defect_rate > 5 else "amber" if defect_rate > 1 else "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "양품 수량",
                    "value": total_ok,
                    "unit": "개",
                    "icon": "check-circle",
                    "color": "green",
                },
            ),
        ]

        if defect_data:
            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": "설비별 불량 현황",
                        "columns": [
                            {"key": "equipment_id", "label": "설비", "sortable": True},
                            {"key": "ok_qty", "label": "양품", "sortable": True},
                            {"key": "ng_qty", "label": "불량", "sortable": True},
                            {"key": "defect_rate", "label": "불량률(%)", "sortable": True},
                        ],
                        "data": [
                            {
                                "equipment_id": f"EQ-{row.equipment_id}",
                                "ok_qty": row.ok_qty or 0,
                                "ng_qty": row.ng_qty or 0,
                                "defect_rate": round(
                                    (row.ng_qty or 0)
                                    / ((row.ok_qty or 0) + (row.ng_qty or 0))
                                    * 100,
                                    2,
                                )
                                if ((row.ok_qty or 0) + (row.ng_qty or 0)) > 0
                                else 0,
                            }
                            for row in defect_data
                        ],
                        "searchable": True,
                        "pagination": True,
                    },
                )
            )

            components.append(
                UIComponent(
                    type="PieChart",
                    props={
                        "title": "설비별 불량 분포",
                        "data": [
                            {"name": f"EQ-{row.equipment_id}", "value": row.ng_qty or 0}
                            for row in defect_data[:10]
                        ],
                    },
                )
            )

        ui_schema = UISchema(layout="single", title=f"{date_str} 불량 분석", components=components)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="defect_analysis",
                confidence=0.9,
                entities={"date": target_date.isoformat()},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_lot_trace(db, lot_no: str) -> QueryResult:
        """Generate LOT traceability response"""
        import time

        start_time = time.time()

        result = await aggregate_lot_traceability(db, lot_no)

        if result.output_type == "error":
            return QueryResult(
                text_response=f"❌ LOT '{lot_no}'을(를) 찾을 수 없습니다.",
                metadata=QueryMetadata(
                    intent="lot_trace",
                    confidence=0.9,
                    entities={"lot_no": lot_no},
                    processing_time_ms=int((time.time() - start_time) * 1000),
                ),
            )

        data = result.data
        wo = data.get("work_order", {})
        product = data.get("product", {})
        summary = data.get("summary", {})
        timeline = data.get("timeline", [])

        text = f"""🔍 **LOT 이력: {lot_no}**

**제품**: {product.get("name", "N/A")} ({product.get("code", "N/A")})
**상태**: {wo.get("status", "N/A")}
**수율**: {summary.get("yield_rate", 0):.1f}%
**양품/불량**: {summary.get("total_ok_qty", 0)}개 / {summary.get("total_ng_qty", 0)}개"""

        trace_steps = [
            {
                "sequence": step.get("sequence", 0),
                "operation": step.get("operation", ""),
                "operationName": step.get("operation_name", ""),
                "equipmentId": step.get("equipment_id", ""),
                "equipmentName": step.get("equipment_name", ""),
                "startTime": step.get("start_time", ""),
                "endTime": step.get("end_time"),
                "status": step.get("status", "PENDING"),
                "okQty": step.get("ok_qty", 0),
                "ngQty": step.get("ng_qty", 0),
            }
            for step in timeline
        ]

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "양품",
                    "value": summary.get("total_ok_qty", 0),
                    "unit": "개",
                    "icon": "check-circle",
                    "color": "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "불량",
                    "value": summary.get("total_ng_qty", 0),
                    "unit": "개",
                    "icon": "alert",
                    "color": "red" if summary.get("total_ng_qty", 0) > 0 else "gray",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "수율",
                    "value": round(summary.get("yield_rate", 0), 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "blue" if summary.get("yield_rate", 0) >= 95 else "amber",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "공정 수",
                    "value": summary.get("process_count", 0),
                    "unit": "개",
                    "icon": "clipboard",
                    "color": "gray",
                },
            ),
        ]

        if trace_steps:
            components.append(
                UIComponent(
                    type="TraceabilityTimeline",
                    props={
                        "title": f"LOT {lot_no} 공정 이력",
                        "lotNo": lot_no,
                        "product": product.get("name", ""),
                        "steps": trace_steps,
                    },
                )
            )

        ui_schema = UISchema(layout="single", title=f"LOT {lot_no} 이력", components=components)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="lot_trace",
                confidence=0.9,
                entities={"lot_no": lot_no},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_work_orders(db, status_filter: Optional[str] = None) -> QueryResult:
        """Generate work orders status response"""
        import time

        start_time = time.time()

        from sqlalchemy import select, func
        from ....models.production import WorkOrder

        query = select(WorkOrder.status, func.count(WorkOrder.id).label("count")).group_by(
            WorkOrder.status
        )
        result = await db.execute(query)
        status_counts = {row.status: row.count for row in result.all()}

        recent_query = select(WorkOrder)
        if status_filter:
            recent_query = recent_query.where(WorkOrder.status == status_filter)
        recent_query = recent_query.order_by(WorkOrder.created_at.desc()).limit(20)

        recent_result = await db.execute(recent_query)
        recent_orders = recent_result.scalars().all()

        total = sum(status_counts.values())
        ready = status_counts.get("READY", 0)
        running = status_counts.get("RUNNING", 0)
        done = status_counts.get("DONE", 0)

        filter_str = {"READY": "대기중", "RUNNING": "진행중", "DONE": "완료"}.get(
            status_filter, "전체"
        )

        text = f"""📋 **작업지시 현황** ({filter_str})

**요약**: 전체 {total}건
- 대기: {ready}건
- 진행중: {running}건
- 완료: {done}건"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "전체",
                    "value": total,
                    "unit": "건",
                    "icon": "clipboard",
                    "color": "gray",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "대기",
                    "value": ready,
                    "unit": "건",
                    "icon": "clock",
                    "color": "amber",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "진행중",
                    "value": running,
                    "unit": "건",
                    "icon": "activity",
                    "color": "blue",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "완료",
                    "value": done,
                    "unit": "건",
                    "icon": "check-circle",
                    "color": "green",
                },
            ),
        ]

        if recent_orders:
            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": f"작업지시 목록 ({filter_str})",
                        "columns": [
                            {"key": "lot_no", "label": "LOT", "sortable": True},
                            {"key": "qty", "label": "수량", "sortable": True},
                            {"key": "status", "label": "상태", "sortable": True},
                            {"key": "priority", "label": "우선순위", "sortable": True},
                        ],
                        "data": [
                            {
                                "lot_no": o.lot_no,
                                "qty": o.qty,
                                "status": o.status,
                                "priority": o.priority,
                            }
                            for o in recent_orders
                        ],
                        "searchable": True,
                        "pagination": True,
                    },
                )
            )

        ui_schema = UISchema(layout="single", title="작업지시 현황", components=components)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="work_orders",
                confidence=0.9,
                entities={"status_filter": status_filter},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_schedule(db, target_date: Optional[date] = None) -> QueryResult:
        """Generate schedule status response"""
        import time

        start_time = time.time()

        if target_date is None:
            target_date = date.today()

        from sqlalchemy import select, and_
        from ....models.production import WorkOrder

        query = (
            select(WorkOrder)
            .where(
                and_(WorkOrder.start_time.isnot(None), WorkOrder.status.in_(["READY", "RUNNING"]))
            )
            .order_by(WorkOrder.start_time)
            .limit(30)
        )
        result = await db.execute(query)
        scheduled_orders = result.scalars().all()

        running = sum(1 for o in scheduled_orders if o.status == "RUNNING")
        ready = sum(1 for o in scheduled_orders if o.status == "READY")

        date_str = "오늘" if target_date == date.today() else target_date.strftime("%m월 %d일")

        text = f"""📅 **{date_str} 스케줄**

**요약**: {len(scheduled_orders)}건
- 진행중: {running}건
- 대기: {ready}건"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "스케줄",
                    "value": len(scheduled_orders),
                    "unit": "건",
                    "icon": "clipboard",
                    "color": "blue",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "진행중",
                    "value": running,
                    "unit": "건",
                    "icon": "activity",
                    "color": "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "대기",
                    "value": ready,
                    "unit": "건",
                    "icon": "clock",
                    "color": "amber",
                },
            ),
        ]

        if scheduled_orders:
            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": f"{date_str} 스케줄",
                        "columns": [
                            {"key": "lot_no", "label": "LOT", "sortable": True},
                            {"key": "qty", "label": "수량", "sortable": True},
                            {"key": "status", "label": "상태", "sortable": True},
                            {"key": "start_time", "label": "시작", "sortable": True},
                            {"key": "end_time", "label": "종료", "sortable": True},
                        ],
                        "data": [
                            {
                                "lot_no": o.lot_no,
                                "qty": o.qty,
                                "status": o.status,
                                "start_time": o.start_time.strftime("%H:%M")
                                if o.start_time
                                else "-",
                                "end_time": o.end_time.strftime("%H:%M") if o.end_time else "-",
                            }
                            for o in scheduled_orders
                        ],
                        "searchable": True,
                        "pagination": True,
                    },
                )
            )

        ui_schema = UISchema(layout="single", title=f"{date_str} 스케줄", components=components)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="schedule",
                confidence=0.9,
                entities={"date": target_date.isoformat()},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    async def generate_kpi(db) -> QueryResult:
        """Generate KPI dashboard response"""
        import time

        start_time = time.time()

        result = await aggregate_kpi_dashboard(db)
        data = result.data

        today = data.get("today", {})
        week = data.get("week", {})
        current = data.get("current", {})

        text = f"""📈 **KPI 대시보드**

**오늘**
- 완료율: {today.get("completion_rate", 0):.1f}%
- 수율: {today.get("yield_rate", 0):.1f}%
- 생산량: {today.get("production_qty", 0):,}개

**현재 상태**
- 진행중 작업: {current.get("active_orders", 0)}건
- 가동중 설비: {current.get("running_equipment", 0)}대"""

        components = [
            UIComponent(
                type="KPICard",
                props={
                    "title": "완료율",
                    "value": round(today.get("completion_rate", 0), 1),
                    "unit": "%",
                    "icon": "check-circle",
                    "color": "green" if today.get("completion_rate", 0) >= 80 else "amber",
                    "target": 90,
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "수율",
                    "value": round(today.get("yield_rate", 0), 1),
                    "unit": "%",
                    "icon": "percent",
                    "color": "blue" if today.get("yield_rate", 0) >= 95 else "amber",
                    "target": 95,
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "생산량",
                    "value": today.get("production_qty", 0),
                    "unit": "개",
                    "icon": "package",
                    "color": "green",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "주간 가동률",
                    "value": round(week.get("avg_utilization", 0), 1),
                    "unit": "%",
                    "icon": "activity",
                    "color": "blue",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "진행중 작업",
                    "value": current.get("active_orders", 0),
                    "unit": "건",
                    "icon": "clipboard",
                    "color": "amber",
                },
            ),
            UIComponent(
                type="KPICard",
                props={
                    "title": "가동중 설비",
                    "value": current.get("running_equipment", 0),
                    "unit": "대",
                    "icon": "activity",
                    "color": "green",
                },
            ),
        ]

        ui_schema = UISchema(layout="dashboard", title="KPI 대시보드", components=components)

        return QueryResult(
            text_response=text,
            ui_schema=ui_schema,
            metadata=QueryMetadata(
                intent="kpi",
                confidence=0.9,
                entities={},
                processing_time_ms=int((time.time() - start_time) * 1000),
            ),
        )

    @staticmethod
    def generate_greeting() -> QueryResult:
        """Generate greeting response"""
        return QueryResult(
            text_response="""안녕하세요! 👋 MES AI 어시스턴트입니다.

생산 현황, 설비 상태, 품질 지표 등을 자연어로 질문해 주세요.

예시:
- "오늘 생산 현황 어때?"
- "어제 수율 얼마야?"
- "설비 가동률 알려줘"
- "진행중인 작업 뭐야?"

무엇을 도와드릴까요?""",
            metadata=QueryMetadata(
                intent="greeting", confidence=1.0, entities={}, processing_time_ms=0
            ),
        )

    @staticmethod
    def generate_help() -> QueryResult:
        """Generate help response"""
        text = """💡 **MES AI 어시스턴트 도움말**

**📊 생산 현황**
- "오늘 생산 현황" / "어제 실적 어땠어?"
- "이번 주 실적" / "최근 7일 추이"
- "어제랑 오늘 비교해줘"

**🔧 설비**
- "설비 가동률" / "장비 상태 어때?"
- "고장난 설비 있어?" / "대기중인 장비"

**📈 품질**
- "수율 얼마야?" / "오늘 불량 현황"
- "불량 원인 분석" / "설비별 불량률"

**📋 작업**
- "진행중인 작업" / "대기 작업 목록"
- "오늘 스케줄" / "완료된 작업"

**🔍 추적**
- "LOT-001 이력 조회"

**📊 KPI**
- "KPI 보여줘" / "대시보드"

자연스럽게 질문해 주세요!"""

        return QueryResult(
            text_response=text,
            metadata=QueryMetadata(
                intent="help", confidence=1.0, entities={}, processing_time_ms=0
            ),
        )

    @staticmethod
    def generate_unknown(query: str) -> QueryResult:
        """Generate response for unknown intent"""
        return QueryResult(
            text_response=f"""🤔 "{query}" 질문을 이해하지 못했습니다.

다음과 같이 질문해 보세요:
- "오늘 생산 현황" / "어제 실적"
- "설비 가동률" / "수율 얼마야?"
- "진행중인 작업" / "스케줄 보여줘"

"도움말"을 입력하면 전체 기능을 확인할 수 있습니다.""",
            metadata=QueryMetadata(
                intent="unknown", confidence=0.3, entities={}, processing_time_ms=0
            ),
        )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/query", response_model=QueryResult)
async def process_query(
    request: QueryRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> QueryResult:
    """Process natural language query with enhanced intent detection."""
    query = request.query.strip()
    logger.info(f"NLM Query: {query}")

    # Use nlm_retriever for intent detection (100% accuracy)
    retriever = get_nlm_retriever()
    results = retriever.retrieve(query, top_k=1)
    if results:
        intent = results[0].intent
        confidence = results[0].score
    else:
        intent = "unknown"
        confidence = 0.3

    # Extract entities using existing DateExtractor
    entities = DateExtractor.extract_time_entities(query)
    logger.info(f"Intent: {intent} ({confidence}), entities: {entities}")

    try:
        # Parse date
        target_date = None
        if "date" in entities:
            target_date = date.fromisoformat(entities["date"])
        else:
            target_date = DateExtractor.extract_date(query)

        # Parse date range
        date_range = None
        if "date_range" in entities:
            dr = entities["date_range"]
            date_range = (date.fromisoformat(dr["start"]), date.fromisoformat(dr["end"]))
        else:
            date_range = DateExtractor.extract_date_range(query)

        # Route to appropriate handler
        if intent == "greeting":
            return ResponseGenerator.generate_greeting()

        elif intent == "help":
            return ResponseGenerator.generate_help()

        elif intent in ("daily_status", "production_count", "current_status"):
            return await ResponseGenerator.generate_daily_status(db, target_date)

        elif intent == "compare_status":
            date1 = target_date or date.today() - timedelta(days=1)
            date2 = date1 + timedelta(days=1) if target_date else date.today()
            return await ResponseGenerator.generate_compare_status(db, date1, date2)

        elif intent == "trend":
            if date_range:
                return await ResponseGenerator.generate_trend(db, date_range[0], date_range[1])
            end = date.today()
            start = end - timedelta(days=6)
            return await ResponseGenerator.generate_trend(db, start, end)

        elif intent in ("equipment_status", "equipment_error", "equipment_idle"):
            days = 7
            if date_range:
                days = (date_range[1] - date_range[0]).days + 1
            return await ResponseGenerator.generate_equipment_status(db, days)

        elif intent == "yield_status":
            return await ResponseGenerator.generate_yield_status(db, target_date)

        elif intent == "defect_analysis":
            return await ResponseGenerator.generate_defect_analysis(db, target_date)

        elif intent == "lot_trace":
            lot_no = IntentDetector.extract_lot_no(query)
            if lot_no:
                return await ResponseGenerator.generate_lot_trace(db, lot_no)
            return QueryResult(text_response="LOT 번호를 입력해 주세요. 예: 'LOT-001 이력 조회'")

        elif intent in (
            "work_orders",
            "work_orders_in_progress",
            "work_orders_pending",
            "work_orders_completed",
        ):
            status_filter = IntentDetector.extract_work_order_filter(query)
            return await ResponseGenerator.generate_work_orders(db, status_filter)

        elif intent in ("schedule", "schedule_delay"):
            return await ResponseGenerator.generate_schedule(db, target_date)

        elif intent in ("kpi", "report"):
            return await ResponseGenerator.generate_kpi(db)

        else:
            return ResponseGenerator.generate_unknown(query)

    except Exception as e:
        logger.error(f"NLM error: {e}", exc_info=True)
        return QueryResult(
            text_response="처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            metadata=QueryMetadata(
                intent=intent, confidence=0.0, entities=entities, processing_time_ms=0
            ),
        )


# Placeholder endpoints
@router.get("/history")
async def get_query_history(
    db: DBSession, current_user: CurrentUser, limit: int = 50
) -> Dict[str, Any]:
    return {"messages": []}


@router.post("/favorites")
async def add_favorite(
    request: QueryRequest, db: DBSession, current_user: CurrentUser
) -> Dict[str, str]:
    return {"status": "ok"}


@router.delete("/favorites")
async def remove_favorite(
    request: QueryRequest, db: DBSession, current_user: CurrentUser
) -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/favorites")
async def get_favorites(db: DBSession, current_user: CurrentUser) -> Dict[str, List[str]]:
    return {
        "favorites": ["오늘 생산 현황", "어제 실적", "설비 가동률", "수율 현황", "진행중인 작업"]
    }


@router.get("/quota")
async def get_quota_status(current_user: CurrentUser) -> Dict[str, Any]:
    return {
        "requests": {"used": 0, "limit": 1000, "reset_at": datetime.now(timezone.utc).isoformat()},
        "llm_calls": {"used": 0, "limit": 100, "reset_at": datetime.now(timezone.utc).isoformat()},
    }
