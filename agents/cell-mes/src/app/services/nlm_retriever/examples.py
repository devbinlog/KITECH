"""
Example queries for training/initializing retrievers.

Organized by intent with variations for different user personas.
"""

from typing import List
from .base import IntentExample


def get_default_examples() -> List[IntentExample]:
    """
    Get default training examples for all intents.

    Includes variations for:
        - 현장작업자 (Operator)
        - 공장관리자 (Factory Manager)
        - 사장님 (SME Owner)
    """
    examples = [
        # === daily_status ===
        IntentExample("오늘 생산 현황", "daily_status"),
        IntentExample("오늘 어때?", "daily_status"),
        IntentExample("오늘 실적", "daily_status"),
        IntentExample("금일 생산량", "daily_status"),
        IntentExample("생산 상황 알려줘", "daily_status"),
        IntentExample("어제 생산 현황", "daily_status"),
        IntentExample("어제 실적 어땠어?", "daily_status"),
        IntentExample("라인 살아있어?", "daily_status"),
        IntentExample("돌아가?", "daily_status"),
        IntentExample("상황 어때?", "daily_status"),
        IntentExample("잘 되고 있어?", "daily_status"),
        IntentExample("문제 없어?", "daily_status"),
        IntentExample("공장 전체 현황", "daily_status"),
        IntentExample("전체 라인 상태", "daily_status"),
        IntentExample("오늘 잘 돌아가?", "daily_status"),
        IntentExample("문제 없지?", "daily_status"),
        IntentExample("핵심만 말해봐", "daily_status"),
        IntentExample("한 줄로 요약해줘", "daily_status"),
        IntentExample("결론이 뭐야?", "daily_status"),
        # === production_count ===
        IntentExample("오늘 몇 개 만들었어?", "production_count"),
        IntentExample("생산량 알려줘", "production_count"),
        IntentExample("얼마나 찍었어?", "production_count"),
        IntentExample("몇 개 나왔어?", "production_count"),
        IntentExample("양품 몇 개?", "production_count"),
        IntentExample("불량 얼마나 나왔어?", "production_count"),
        IntentExample("몇 개 더 해야 해?", "production_count"),
        IntentExample("남은 거 얼마야?", "production_count"),
        IntentExample("끝나려면?", "production_count"),
        IntentExample("목표 달성률", "production_count"),
        IntentExample("계획 대비 현황", "production_count"),
        # === equipment_status ===
        IntentExample("설비 상태 어때?", "equipment_status"),
        IntentExample("장비 현황", "equipment_status"),
        IntentExample("기계 돌아가?", "equipment_status"),
        IntentExample("가동률 얼마야?", "equipment_status"),
        IntentExample("전체 설비 상태", "equipment_status"),
        IntentExample("라인 가동 현황", "equipment_status"),
        IntentExample("병목 설비 어디야?", "equipment_status"),
        IntentExample("효율 낮은 설비", "equipment_status"),
        IntentExample("설비 투자 필요해?", "equipment_status"),
        IntentExample("노후 설비 있어?", "equipment_status"),
        IntentExample("설비 고장 많아?", "equipment_status"),
        # === equipment_error ===
        IntentExample("고장난 설비 있어?", "equipment_error"),
        IntentExample("에러 난 장비", "equipment_error"),
        IntentExample("알람 뜬 거 있어?", "equipment_error"),
        IntentExample("이거 망가졌어", "equipment_error"),
        IntentExample("기계 이상해", "equipment_error"),
        IntentExample("안 돌아가", "equipment_error"),
        IntentExample("멈췄어", "equipment_error"),
        IntentExample("터졌어", "equipment_error"),
        IntentExample("빨간불 들어왔어", "equipment_error"),
        IntentExample("소리 나", "equipment_error"),
        # === equipment_idle ===
        IntentExample("대기중인 설비", "equipment_idle"),
        IntentExample("놀고 있는 장비", "equipment_idle"),
        IntentExample("유휴 설비", "equipment_idle"),
        IntentExample("사용 가능한 장비", "equipment_idle"),
        # === yield_status ===
        IntentExample("수율 얼마야?", "yield_status"),
        IntentExample("yield 몇이야?", "yield_status"),
        IntentExample("품질 어때?", "yield_status"),
        IntentExample("양품률", "yield_status"),
        IntentExample("수율 추이", "yield_status"),
        # === defect_analysis ===
        IntentExample("불량 얼마나 나왔어?", "defect_analysis"),
        IntentExample("오늘 불량", "defect_analysis"),
        IntentExample("NG 현황", "defect_analysis"),
        IntentExample("불량률 어때?", "defect_analysis"),
        IntentExample("왜 불량이 많아?", "defect_analysis"),
        IntentExample("불량 원인 뭐야?", "defect_analysis"),
        IntentExample("설비별 불량률", "defect_analysis"),
        IntentExample("클레임 들어온 거 있어?", "defect_analysis"),
        IntentExample("고객 불만 없지?", "defect_analysis"),
        IntentExample("반품된 거 있어?", "defect_analysis"),
        IntentExample("품질 문제 없어?", "defect_analysis"),
        # === lot_trace ===
        IntentExample("LOT-001 이력", "lot_trace"),
        IntentExample("로트 추적해줘", "lot_trace"),
        IntentExample("LOT 어디까지 갔어?", "lot_trace"),
        IntentExample("LOT-001 품질 데이터", "lot_trace"),
        IntentExample("로트 진행 상황", "lot_trace"),
        # === work_orders ===
        IntentExample("작업지시 현황", "work_orders"),
        IntentExample("오더 상황", "work_orders"),
        IntentExample("작업 뭐 있어?", "work_orders"),
        IntentExample("할 일 뭐야?", "work_orders"),
        IntentExample("뭐 해?", "work_orders"),
        IntentExample("지금 뭐 해야 해?", "work_orders"),
        IntentExample("전체 작업 현황", "work_orders"),
        # === work_orders_in_progress ===
        IntentExample("진행중인 작업", "work_orders_in_progress"),
        IntentExample("지금 하고 있는 거", "work_orders_in_progress"),
        IntentExample("작업중인 오더", "work_orders_in_progress"),
        IntentExample("내 작업", "work_orders_in_progress"),
        # === work_orders_pending ===
        IntentExample("대기 작업", "work_orders_pending"),
        IntentExample("할 거 뭐 있어?", "work_orders_pending"),
        IntentExample("다음 작업 뭐야?", "work_orders_pending"),
        IntentExample("다음 뭐야?", "work_orders_pending"),
        IntentExample("그 다음?", "work_orders_pending"),
        IntentExample("이거 끝나면?", "work_orders_pending"),
        IntentExample("끝나면 뭐 해?", "work_orders_pending"),
        # === work_orders_completed ===
        IntentExample("완료된 작업", "work_orders_completed"),
        IntentExample("끝난 거 뭐야?", "work_orders_completed"),
        IntentExample("오늘 완료 건수", "work_orders_completed"),
        # === schedule ===
        IntentExample("오늘 스케줄", "schedule"),
        IntentExample("오늘 일정", "schedule"),
        IntentExample("금일 계획", "schedule"),
        IntentExample("내일 계획", "schedule"),
        IntentExample("이번 주 스케줄", "schedule"),
        IntentExample("납기 지킬 수 있어?", "schedule"),
        IntentExample("늦어지는 거 있어?", "schedule"),
        IntentExample("출하 언제야?", "schedule"),
        IntentExample("고객 약속 지킬 수 있어?", "schedule"),
        # === schedule_delay ===
        IntentExample("지연된 작업", "schedule_delay"),
        IntentExample("늦어진 거 있어?", "schedule_delay"),
        IntentExample("딜레이 현황", "schedule_delay"),
        IntentExample("납기 위험한 거", "schedule_delay"),
        # === compare_status ===
        IntentExample("어제보다 어때?", "compare_status"),
        IntentExample("전일 대비", "compare_status"),
        IntentExample("어제랑 비교해줘", "compare_status"),
        IntentExample("지난주보다?", "compare_status"),
        IntentExample("저번 달보다 어때?", "compare_status"),
        IntentExample("저번 달보다 나아?", "compare_status"),
        IntentExample("나아졌어?", "compare_status"),
        IntentExample("좋아졌어?", "compare_status"),
        IntentExample("성장하고 있어?", "compare_status"),
        # === trend ===
        IntentExample("추이 분석해줘", "trend"),
        IntentExample("트렌드 보여줘", "trend"),
        IntentExample("변화 추이", "trend"),
        IntentExample("이번 주 실적", "trend"),
        IntentExample("이번주 뭘 했어?", "trend"),
        IntentExample("지난주 현황", "trend"),
        IntentExample("이번 달 생산량", "trend"),
        IntentExample("지난달 생산 현황", "trend"),
        IntentExample("최근 7일", "trend"),
        # === kpi ===
        IntentExample("KPI 보여줘", "kpi"),
        IntentExample("지표 어때?", "kpi"),
        IntentExample("대시보드", "kpi"),
        IntentExample("성과 지표", "kpi"),
        IntentExample("OEE 어때?", "kpi"),
        IntentExample("숫자로 보여줘", "kpi"),
        IntentExample("실적 어때?", "kpi"),
        IntentExample("돈 벌고 있어?", "kpi"),
        IntentExample("야근해야 해?", "kpi"),
        IntentExample("지금 제일 큰 문제가 뭐야?", "kpi"),
        IntentExample("걱정되는 거 있어?", "kpi"),
        # === report ===
        IntentExample("일일 보고서", "report"),
        IntentExample("데일리 리포트", "report"),
        IntentExample("주간 보고", "report"),
        IntentExample("월간 리포트", "report"),
        IntentExample("경영진 보고용 자료", "report"),
        IntentExample("회의용 자료", "report"),
        IntentExample("실적 요약해줘", "report"),
        # === greeting ===
        IntentExample("안녕", "greeting"),
        IntentExample("안녕하세요", "greeting"),
        IntentExample("하이", "greeting"),
        IntentExample("hi", "greeting"),
        IntentExample("hello", "greeting"),
        # === help ===
        IntentExample("도움말", "help"),
        IntentExample("뭘 할 수 있어?", "help"),
        IntentExample("기능 알려줘", "help"),
        IntentExample("사용법", "help"),
        IntentExample("어떻게 해?", "help"),
    ]

    return examples


def get_examples_by_intent(intent: str) -> List[IntentExample]:
    """Get examples for a specific intent."""
    all_examples = get_default_examples()
    return [ex for ex in all_examples if ex.intent == intent]


def get_intent_list() -> List[str]:
    """Get list of all intents."""
    all_examples = get_default_examples()
    return list(set(ex.intent for ex in all_examples))
