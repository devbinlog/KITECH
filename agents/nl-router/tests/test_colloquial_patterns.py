"""Tests for colloquial (구어체) pattern recognition"""

import pytest
from src.understanding.intents import Intent
from src.understanding.intent_classifier import IntentClassifier


class TestColloquialPatterns:
    """Tests for shop floor worker / manager colloquial expressions"""

    @pytest.fixture
    def classifier(self):
        """Create classifier with LLM disabled"""
        return IntentClassifier(use_llm=False)

    @pytest.mark.asyncio
    async def test_shop_floor_error_expressions(self, classifier):
        """Test shop floor worker error reporting expressions"""
        queries = [
            ("이거 망가졌어", Intent.ERROR_DIAGNOSIS),
            ("빨간불 들어왔어", Intent.ERROR_DIAGNOSIS),
            ("기계 안 돌아가", Intent.ERROR_DIAGNOSIS),
            ("설비 터졌어", Intent.ERROR_DIAGNOSIS),
            ("이상한 소리 나", Intent.ERROR_DIAGNOSIS),
        ]

        for query, expected_intent in queries:
            result = await classifier.classify(query)
            assert result.intent == expected_intent, f"Failed for: {query}"
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_shop_floor_status_expressions(self, classifier):
        """Test shop floor worker status check expressions"""
        queries = [
            ("라인 살아있어?", Intent.PRODUCTION_STATUS),
            ("오늘 잘 돌아가?", Intent.PRODUCTION_STATUS),
            ("오늘 생산 현황", Intent.PRODUCTION_STATUS),
        ]

        for query, expected_intent in queries:
            result = await classifier.classify(query)
            assert result.intent == expected_intent, f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_shop_floor_next_task_expressions(self, classifier):
        """Test shop floor worker next task expressions"""
        queries = [
            ("다음 뭐야?", Intent.PRODUCTION_DETAIL),
            ("끝나면 뭐 해?", Intent.PRODUCTION_DETAIL),
            ("그 다음은?", Intent.PRODUCTION_DETAIL),
        ]

        for query, expected_intent in queries:
            result = await classifier.classify(query)
            assert result.intent == expected_intent, f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_manager_bottleneck_expressions(self, classifier):
        """Test factory manager bottleneck analysis expressions"""
        queries = [
            ("병목 설비 어디야?", Intent.EQUIPMENT_STATUS),
            ("효율 떨어지는 설비", Intent.EQUIPMENT_STATUS),
            ("전체 설비 상태", Intent.EQUIPMENT_STATUS),
        ]

        for query, expected_intent in queries:
            result = await classifier.classify(query)
            assert result.intent == expected_intent, f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_manager_kpi_expressions(self, classifier):
        """Test factory manager KPI expressions"""
        queries = [
            ("KPI 지표 보여줘", Intent.KPI_QUERY),
            ("오늘 생산 실적 어때", Intent.KPI_QUERY),  # "실적" triggers KPI
        ]

        for query, expected_intent in queries:
            result = await classifier.classify(query)
            assert result.intent == expected_intent, f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_ceo_expressions(self, classifier):
        """Test CEO/owner expressions"""
        queries = [
            ("불량 클레임 들어온 거 있어?", Intent.DEFECT_ANALYSIS),
            ("스케줄 납기 지킬 수 있어?", Intent.SCHEDULE_QUERY),
        ]

        for query, expected_intent in queries:
            result = await classifier.classify(query)
            assert result.intent == expected_intent, f"Failed for: {query}"
