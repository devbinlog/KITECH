"""Tests for Intent Classifier"""

import pytest
from src.understanding.intents import Intent, IntentResult
from src.understanding.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Tests for rule-based intent classification"""

    @pytest.fixture
    def classifier(self):
        """Create classifier with LLM disabled"""
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_production_status_intent(self, classifier):
        """Test production status classification"""
        queries = [
            "오늘 생산 현황 보여줘",
            "생산 실적 조회",
            "작업지시 목록",
        ]

        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.PRODUCTION_STATUS
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_equipment_status_intent(self, classifier):
        """Test equipment status classification"""
        queries = [
            "CNC-001 설비 상태 어때?",
            "설비 상태 조회",
            "장비 상태 확인",
        ]

        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.EQUIPMENT_STATUS
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_kpi_query_intent(self, classifier):
        """Test KPI query classification"""
        queries = [
            "가동률 보여줘",
            "수율 조회",
            "KPI 확인",
        ]

        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.KPI_QUERY
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_traceability_intent(self, classifier):
        """Test traceability classification"""
        queries = [
            "LOT-001 이력 조회",
            "LOT 추적",
            "생산 이력 확인",
        ]

        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.TRACEABILITY
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_analytics_intent(self, classifier):
        """Test analytics classification"""
        queries = [
            "수율 추이",
            "트렌드 분석",
            "변화 추이",
        ]

        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.ANALYTICS
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_comparison_intent(self, classifier):
        """Test comparison classification"""
        queries = [
            "설비별 가동률 비교",
            "제품별 비교",
        ]

        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.COMPARISON
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_unknown_intent(self, classifier):
        """Test unknown query classification"""
        result = await classifier.classify("아무 관련없는 질문")
        assert result.intent == Intent.UNKNOWN
        assert result.confidence == 0

    @pytest.mark.asyncio
    async def test_entity_extraction_lot_no(self, classifier):
        """Test LOT number extraction"""
        result = await classifier.classify(
            "LOT-001 이력 조회"
        )  # Use query that matches traceability
        assert "lot_no" in result.entities
        assert "LOT-001" in result.entities["lot_no"]

    @pytest.mark.asyncio
    async def test_entity_extraction_equipment_id(self, classifier):
        """Test equipment ID extraction"""
        result = await classifier.classify("CNC-001 설비 상태")
        assert "equipment_id" in result.entities
        assert "CNC-001" in result.entities["equipment_id"]

    @pytest.mark.asyncio
    async def test_entity_extraction_date(self, classifier):
        """Test date keyword extraction"""
        result = await classifier.classify("오늘 생산 현황")
        assert "date" in result.entities
        assert result.entities["date"] == "today"

    @pytest.mark.asyncio
    async def test_entity_extraction_date_range(self, classifier):
        """Test date range extraction"""
        result = await classifier.classify("이번 주 생산 현황")
        assert "date_range" in result.entities
        assert result.entities["date_range"] == "this_week"

    @pytest.mark.asyncio
    async def test_entity_extraction_metric(self, classifier):
        """Test metric extraction"""
        result = await classifier.classify("가동률 조회")
        assert "metric" in result.entities
        assert result.entities["metric"] == "utilization"

    @pytest.mark.asyncio
    async def test_entity_extraction_group_by(self, classifier):
        """Test group_by extraction"""
        result = await classifier.classify("설비별 비교")
        assert "group_by" in result.entities
        assert result.entities["group_by"] == "equipment"


class TestIntentResult:
    """Tests for IntentResult model"""

    def test_intent_result_creation(self):
        """Test IntentResult creation"""
        result = IntentResult(
            intent=Intent.PRODUCTION_STATUS,
            confidence=0.95,
            entities={"date": "today"},
        )

        assert result.intent == Intent.PRODUCTION_STATUS
        assert result.confidence == 0.95
        assert result.entities["date"] == "today"

    def test_intent_result_defaults(self):
        """Test IntentResult defaults"""
        result = IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.0,
        )

        assert result.entities == {}
        assert result.sub_intent is None
        assert result.requires_clarification is False
        assert result.suggested_questions == []


# ============================================================================
# 보강된 테스트: 계산 로직 검증
# ============================================================================

class TestConfidenceCalculation:
    """신뢰도(confidence) 계산 정확성 테스트"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_confidence_capped_at_0_9(self, classifier):
        """Rule-based 분류 시 신뢰도는 0.9를 초과하지 않음"""
        # 여러 키워드가 매칭되어도 0.9 이하여야 함
        result = await classifier.classify("오늘 생산 현황 작업 지시 목록")
        assert result.confidence <= 0.9, "Rule-based 신뢰도는 0.9 이하여야 함"

    @pytest.mark.asyncio
    async def test_confidence_zero_for_unknown(self, classifier):
        """매칭되는 키워드 없을 시 신뢰도 0"""
        result = await classifier.classify("아무 관련없는 문장입니다")
        assert result.intent == Intent.UNKNOWN
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_confidence_proportional_to_matches(self, classifier):
        """매칭 수가 많을수록 신뢰도가 높아져야 함"""
        # 단일 키워드
        result1 = await classifier.classify("생산 현황")
        # 여러 키워드
        result2 = await classifier.classify("오늘 생산 현황 작업 지시")

        # 둘 다 같은 Intent인 경우에만 비교
        if result1.intent == result2.intent:
            assert result2.confidence >= result1.confidence

    @pytest.mark.asyncio
    async def test_multiple_intents_select_highest_score(self, classifier):
        """여러 Intent에 매칭 시 가장 높은 점수의 Intent 선택"""
        # "설비 가동률" - EQUIPMENT_STATUS와 KPI_QUERY 둘 다 매칭 가능
        result = await classifier.classify("설비 가동률 보여줘")
        # 가동률이 KPI_QUERY에 더 강하게 매칭
        assert result.intent == Intent.KPI_QUERY
        assert result.confidence > 0


# ============================================================================
# 보강된 테스트: 비즈니스 규칙 검증
# ============================================================================

class TestIntentClassificationRules:
    """Intent 분류 규칙 검증"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_production_status_patterns(self, classifier):
        """생산 현황 관련 패턴 → PRODUCTION_STATUS"""
        patterns = [
            "오늘 생산 어때?",
            "작업 지시 목록 조회",
            "라인 살아있어?",
            "잘 돌아가?",
            "몇 개 남았어?",
        ]
        for query in patterns:
            result = await classifier.classify(query)
            assert result.intent == Intent.PRODUCTION_STATUS, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_equipment_status_patterns(self, classifier):
        """설비 상태 관련 패턴 → EQUIPMENT_STATUS"""
        patterns = [
            "CNC-001 설비 상태",
            "장비 상태 확인해줘",
            "병목 설비 어디야?",
            "전체 설비 현황",
        ]
        for query in patterns:
            result = await classifier.classify(query)
            assert result.intent == Intent.EQUIPMENT_STATUS, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_error_diagnosis_patterns(self, classifier):
        """고장/에러 신고 패턴 → ERROR_DIAGNOSIS"""
        patterns = [
            "기계 고장났어",
            "알람 떴어",
            "에러 발생",
            "왜 안 돼?",
            "망가졌어",
            "터졌어",
            "빨간불 들어왔어",
        ]
        for query in patterns:
            result = await classifier.classify(query)
            assert result.intent == Intent.ERROR_DIAGNOSIS, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_defect_analysis_patterns(self, classifier):
        """불량 분석 패턴 → DEFECT_ANALYSIS"""
        patterns = [
            "불량률 확인",
            "불량 원인 분석",
            "왜 불량이 나왔어?",
            "클레임 들어온 거 있어?",
        ]
        for query in patterns:
            result = await classifier.classify(query)
            assert result.intent == Intent.DEFECT_ANALYSIS, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_schedule_query_patterns(self, classifier):
        """스케줄/납기 패턴 → SCHEDULE_QUERY"""
        patterns = [
            "스케줄 확인",
            "일정 어떻게 돼?",
            "납기 지킬 수 있어?",
            "언제까지 해야 해?",
        ]
        for query in patterns:
            result = await classifier.classify(query)
            assert result.intent == Intent.SCHEDULE_QUERY, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_analytics_patterns(self, classifier):
        """추이/트렌드 패턴 → ANALYTICS"""
        patterns = [
            "수율 추이",
            "트렌드 분석",
            "변화 추이 보여줘",
            "이번 주 뭘 했지?",
        ]
        for query in patterns:
            result = await classifier.classify(query)
            assert result.intent == Intent.ANALYTICS, f"Failed: {query}"


class TestEntityExtractionFromClassifier:
    """분류 시 엔티티 추출 검증"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_extract_lot_with_dash(self, classifier):
        """LOT-XXX 형식 추출"""
        result = await classifier.classify("LOT-2024-001 이력 조회")
        assert "lot_no" in result.entities

    @pytest.mark.asyncio
    async def test_extract_equipment_with_number(self, classifier):
        """CNC-001, ROBOT-002 형식 추출"""
        result = await classifier.classify("CNC-005 상태 확인")
        assert "equipment_id" in result.entities
        assert "CNC" in result.entities["equipment_id"].upper()

    @pytest.mark.asyncio
    async def test_extract_date_keywords(self, classifier):
        """오늘, 어제 등 날짜 키워드 추출"""
        result = await classifier.classify("어제 생산 현황")
        assert "date" in result.entities
        assert result.entities["date"] == "yesterday"

    @pytest.mark.asyncio
    async def test_extract_date_range(self, classifier):
        """이번 주, 지난 달 등 기간 추출"""
        result = await classifier.classify("이번 주 생산 현황")
        assert "date_range" in result.entities
        assert result.entities["date_range"] == "this_week"

    @pytest.mark.asyncio
    async def test_extract_metric(self, classifier):
        """가동률, 수율 등 지표 추출"""
        result = await classifier.classify("수율 확인해줘")
        assert "metric" in result.entities
        assert result.entities["metric"] == "yield"

    @pytest.mark.asyncio
    async def test_extract_group_by(self, classifier):
        """설비별, 제품별 등 그룹핑 추출"""
        result = await classifier.classify("제품별 비교")
        assert "group_by" in result.entities
        assert result.entities["group_by"] == "product"


# ============================================================================
# 보강된 테스트: 워크플로우 시나리오 (작업자/운영자)
# ============================================================================

class TestWorkerScenarios:
    """작업자 시나리오 테스트"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_worker_check_daily_tasks(self, classifier):
        """작업자: 오늘 내 작업 조회"""
        queries = [
            "오늘 작업 지시 목록",
            "생산 현황 보여줘",
            "작업 목록 조회",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent in [
                Intent.PRODUCTION_STATUS,
                Intent.PRODUCTION_DETAIL,
            ], f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_worker_report_production(self, classifier):
        """작업자: 생산 실적 보고"""
        result = await classifier.classify("오늘 생산량 보여줘")
        # 생산 관련 Intent여야 함
        assert result.intent in [Intent.PRODUCTION_STATUS, Intent.KPI_QUERY]

    @pytest.mark.asyncio
    async def test_worker_report_breakdown(self, classifier):
        """작업자: 설비 고장 신고"""
        queries = [
            "설비 고장났어",
            "기계 멈췄어",
            "안 돌아가",
            "이상한 소리 나",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.ERROR_DIAGNOSIS, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_worker_next_task_inquiry(self, classifier):
        """작업자: 다음 작업 문의"""
        queries = [
            "다음 뭐야?",
            "그 다음은?",
            "끝나면 뭐 해?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.PRODUCTION_DETAIL, f"Failed: {query}"


class TestOperatorScenarios:
    """운영자/관리자 시나리오 테스트"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_operator_check_oee(self, classifier):
        """운영자: 전체 가동률(OEE) 조회"""
        queries = [
            "전체 가동률 알려줘",
            "설비 가동률 조회",
            "KPI 지표 보여줘",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent in [
                Intent.KPI_QUERY,
                Intent.EQUIPMENT_STATUS,
            ], f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_operator_check_delays(self, classifier):
        """운영자: 지연 작업 확인"""
        queries = [
            "지연된 작업 있어?",
            "납기 지연 확인",
            "위험 오더 확인",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.DELAY_PREDICTION, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_operator_equipment_comparison(self, classifier):
        """운영자: 설비별 비교"""
        result = await classifier.classify("설비별 가동률 비교해줘")
        assert result.intent == Intent.COMPARISON
        assert "group_by" in result.entities
        assert result.entities["group_by"] == "equipment"

    @pytest.mark.asyncio
    async def test_operator_bottleneck_analysis(self, classifier):
        """운영자: 병목 분석"""
        queries = [
            "병목 설비 어디야?",
            "효율 떨어지는 설비",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.EQUIPMENT_STATUS, f"Failed: {query}"


class TestCeoScenarios:
    """사장님/경영진 시나리오 테스트"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_ceo_high_level_kpi(self, classifier):
        """CEO: 고수준 KPI 조회"""
        queries = [
            "실적 어때?",
            "숫자로 보여줘",
            "제일 큰 문제가 뭐야?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent in [
                Intent.KPI_QUERY,
                Intent.DEFECT_ANALYSIS,
            ], f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_ceo_delivery_check(self, classifier):
        """CEO: 납기 준수 확인"""
        queries = [
            "납기 지킬 수 있어?",
            "출하 언제 돼?",
            "고객 약속 맞출 수 있어?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.SCHEDULE_QUERY, f"Failed: {query}"

    @pytest.mark.asyncio
    async def test_ceo_period_comparison(self, classifier):
        """CEO: 기간 비교"""
        queries = [
            "저번 달보다 나아졌어?",
            "성장하고 있어?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.COMPARISON, f"Failed: {query}"


# ============================================================================
# E2E 실패 케이스 대응 테스트
# ============================================================================

class TestE2EFailureCases:
    """E2E 테스트에서 실패한 케이스들 - 구어체/캐주얼 표현"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_equipment_running_count(self, classifier):
        """현재 가동 중인 설비가 몇 대야? → equipment_status 또는 equipment_list (둘 다 유효)"""
        queries = [
            "현재 가동 중인 설비가 몇 대야?",
            "가동 중인 설비 몇 대?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            # 가동 상태 조건이 있지만, 수량 질문이므로 둘 다 유효
            assert result.intent in [Intent.EQUIPMENT_STATUS, Intent.EQUIPMENT_LIST], \
                f"Failed: {query} → {result.intent}"

    @pytest.mark.asyncio
    async def test_equipment_running_status(self, classifier):
        """가동 관련 설비 상태 질문 → equipment_status"""
        queries = [
            "가동 중인 설비 상태",
            "설비들 잘 돌아가고 있어?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.EQUIPMENT_STATUS, f"Failed: {query} → {result.intent}"

    @pytest.mark.asyncio
    async def test_quality_issues_count(self, classifier):
        """처리 안 된 품질 이슈가 몇 건이야? → defect_analysis"""
        queries = [
            "처리 안 된 품질 이슈가 몇 건이야?",
            "미처리 품질 이슈",
            "품질 이슈 몇 건 있어?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.DEFECT_ANALYSIS, f"Failed: {query} → {result.intent}"

    @pytest.mark.asyncio
    async def test_total_equipment_count(self, classifier):
        """전체 설비 수가 몇 개야? → equipment_list"""
        queries = [
            "전체 설비 수가 몇 개야?",
            "설비가 몇 대야?",
            "장비 몇 개 있어?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.EQUIPMENT_LIST, f"Failed: {query} → {result.intent}"

    @pytest.mark.asyncio
    async def test_today_tasks(self, classifier):
        """오늘 작업해야 할 게 뭐야? → production_status"""
        queries = [
            "오늘 작업해야 할 게 뭐야?",
            "오늘 해야 할 게 뭐야?",
            "오늘 할 일이 뭐야?",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.PRODUCTION_STATUS, f"Failed: {query} → {result.intent}"

    @pytest.mark.asyncio
    async def test_equipment_status_casual(self, classifier):
        """현재 설비들 상태가 어때? → equipment_status"""
        queries = [
            "현재 설비들 상태가 어때?",
            "설비 상태 어때?",
            "장비들 상태 좀 알려줘",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.EQUIPMENT_STATUS, f"Failed: {query} → {result.intent}"

    @pytest.mark.asyncio
    async def test_help_request(self, classifier):
        """실적 등록은 어떻게 해? → help"""
        queries = [
            "실적 등록은 어떻게 해?",
            "조회는 어떻게 해?",
            "사용법 알려줘",
            "도움말",
        ]
        for query in queries:
            result = await classifier.classify(query)
            assert result.intent == Intent.HELP, f"Failed: {query} → {result.intent}"
