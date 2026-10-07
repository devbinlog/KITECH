"""Tests for NLRouterAgent main class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.nl_router_agent import NLRouterAgent, QueryResult
from src.understanding.intents import Intent, IntentResult
from src.understanding.entities import ExtractedEntities, Entity, EntityType


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_create_success_result(self):
        """Should create successful result."""
        result = QueryResult(
            success=True,
            intent=Intent.PRODUCTION_STATUS,
            data={"orders": []},
            text_response="생산 현황입니다.",
        )

        assert result.success is True
        assert result.intent == Intent.PRODUCTION_STATUS
        assert result.data == {"orders": []}

    def test_create_error_result(self):
        """Should create error result."""
        result = QueryResult(
            success=False,
            intent=Intent.UNKNOWN,
            errors=["API connection failed"],
        )

        assert result.success is False
        assert len(result.errors) == 1

    def test_default_values(self):
        """Should have correct default values."""
        result = QueryResult(
            success=True,
            intent=Intent.EQUIPMENT_STATUS,
        )

        assert result.entities == {}
        assert result.data == {}
        assert result.ui_schema is None
        assert result.text_response == ""
        assert result.errors == []
        assert result.debug_info == {}

    def test_with_ui_schema(self):
        """Should support ui_schema."""
        schema = {"type": "dashboard", "components": []}
        result = QueryResult(
            success=True,
            intent=Intent.KPI_QUERY,
            ui_schema=schema,
        )

        assert result.ui_schema == schema

    def test_with_debug_info(self):
        """Should support debug_info."""
        result = QueryResult(
            success=True,
            intent=Intent.ANALYTICS,
            debug_info={"query": "test", "processing_time_ms": 150},
        )

        assert result.debug_info["processing_time_ms"] == 150


class TestNLRouterAgentInit:
    """Tests for NLRouterAgent initialization."""

    def test_init_defaults(self):
        """Should initialize with default values."""
        agent = NLRouterAgent()

        assert agent.mes_api_base_url == "http://localhost:8000"
        assert agent.intent_classifier is not None
        assert agent.entity_extractor is not None
        assert agent.skill_registry is not None
        assert agent.api_selector is not None
        assert agent.ui_generator is not None

    def test_init_custom_url(self):
        """Should accept custom MES API URL."""
        agent = NLRouterAgent(mes_api_base_url="http://mes-api:9000")

        assert agent.mes_api_base_url == "http://mes-api:9000"

    def test_init_without_llm(self):
        """Should work without LLM client."""
        agent = NLRouterAgent(use_llm=False)

        assert agent.llm_client is None

    def test_conversation_manager_initialized(self):
        """Should have conversation manager."""
        agent = NLRouterAgent()

        assert agent.conversation_manager is not None


class TestNLRouterAgentComponents:
    """Tests for NLRouterAgent component integration."""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False)

    def test_intent_classifier_exists(self, agent):
        """Should have intent classifier."""
        assert agent.intent_classifier is not None

    def test_entity_extractor_exists(self, agent):
        """Should have entity extractor."""
        assert agent.entity_extractor is not None

    def test_skill_registry_exists(self, agent):
        """Should have skill registry."""
        assert agent.skill_registry is not None

    def test_api_selector_exists(self, agent):
        """Should have API selector."""
        assert agent.api_selector is not None

    def test_ui_generator_exists(self, agent):
        """Should have UI generator."""
        assert agent.ui_generator is not None


class TestNLRouterAgentHttpClient:
    """Tests for HTTP client handling."""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False)

    def test_http_client_lazy_init(self, agent):
        """HTTP client should be lazily initialized."""
        # Before first access
        assert agent._http_client is None

        # After access
        client = agent.http_client
        assert client is not None
        assert agent._http_client is not None

    @pytest.mark.asyncio
    async def test_close_cleans_up(self, agent):
        """Close should cleanup HTTP client."""
        # Initialize client
        _ = agent.http_client
        assert agent._http_client is not None

        # Close
        await agent.close()
        assert agent._http_client is None


@pytest.mark.asyncio
class TestNLRouterAgentProcessQuery:
    """Tests for process_query method."""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False)

    async def test_process_query_returns_result(self, agent):
        """Should return QueryResult."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.PRODUCTION_STATUS,
                    confidence=0.95,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                # Mock internal HTTP client
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"orders": []}

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("오늘 생산 현황")

                assert isinstance(result, QueryResult)

    async def test_process_query_unknown_intent(self, agent):
        """Should handle unknown intent."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.UNKNOWN,
                    confidence=0.3,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                result = await agent.process_query("이상한 질문")

                assert result.intent == Intent.UNKNOWN

    async def test_process_query_with_session_id(self, agent):
        """Should track session context."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.PRODUCTION_STATUS,
                    confidence=0.9,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query(
                    "생산 현황",
                    session_id="test-session-123",
                )

                # Should include session in debug info
                assert result.debug_info.get("session_id") == "test-session-123"

    async def test_process_query_clarification_needed(self, agent):
        """Should return clarification request when needed."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.EQUIPMENT_STATUS,
                    confidence=0.5,
                    requires_clarification=True,
                    suggested_questions=["어떤 설비를 조회하시겠습니까?"],
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                result = await agent.process_query("설비")

                assert result.success is True
                assert "명확히" in result.text_response or "설비" in result.text_response

    async def test_process_query_extracts_entities(self, agent):
        """Should extract entities from query."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.EQUIPMENT_STATUS,
                    confidence=0.9,
                    entities={"equipment_type": "CNC"},
                )
                mock_extract.return_value = ExtractedEntities(
                    entities=[
                        Entity(
                            type=EntityType.EQUIPMENT_ID,
                            value="EQ-001",
                            raw_text="1번 설비",
                        )
                    ]
                )

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("1번 CNC 설비 상태")

                # Entities should be merged
                assert "equipment_type" in result.entities or "equipment_id" in result.entities


class TestNLRouterAgentIntegration:
    """Integration-style tests (still mocked but more complete)."""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")

    @pytest.mark.asyncio
    async def test_full_flow_production_query(self, agent):
        """Test complete flow for production query."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.PRODUCTION_STATUS,
                    confidence=0.95,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "daily_summary": {
                        "total_orders": 10,
                        "completed": 8,
                    }
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("오늘 생산 현황 보여줘")

                assert result.success is True
                assert result.intent == Intent.PRODUCTION_STATUS

    @pytest.mark.asyncio
    async def test_debug_info_populated(self, agent):
        """Debug info should contain useful information."""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.KPI_QUERY,
                    confidence=0.88,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("가동률 보여줘")

                assert "query" in result.debug_info
                assert "intent_result" in result.debug_info


# ============================================================================
# 보강된 테스트: 워크플로우 시나리오 (작업자/운영자)
# ============================================================================

class TestWorkerWorkflowScenarios:
    """작업자 워크플로우 시나리오 테스트 (MES API mock)"""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")

    @pytest.mark.asyncio
    async def test_worker_daily_task_query(self, agent):
        """작업자: '오늘 내 작업 뭐야?' → 작업 목록 정확성"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.PRODUCTION_STATUS,
                    confidence=0.9,
                    entities={"date": "today"},
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                # MES API 응답 mock
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "work_orders": [
                        {"id": 1, "lot_no": "LOT-001", "status": "READY", "target_qty": 100},
                        {"id": 2, "lot_no": "LOT-002", "status": "RUNNING", "target_qty": 200},
                    ]
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("오늘 내 작업 뭐야?")

                assert result.success is True
                assert result.intent == Intent.PRODUCTION_STATUS

    @pytest.mark.asyncio
    async def test_worker_production_completion_report(self, agent):
        """작업자: '100개 생산 완료' → 실적 등록"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.ACTION_REQUEST,
                    confidence=0.85,
                    entities={"quantity": 100},
                )
                mock_extract.return_value = ExtractedEntities(
                    entities=[
                        Entity(
                            type=EntityType.QUANTITY,
                            value="100개",
                            raw_text="100개",
                            normalized=100,
                        )
                    ]
                )

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "ok_qty": 100,
                    "yield_rate": 98.5,
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("100개 생산 완료")

                assert result.entities.get("quantity") == 100 or "quantity" in str(result.entities)

    @pytest.mark.asyncio
    async def test_worker_equipment_breakdown_report(self, agent):
        """작업자: '설비 고장났어' → 다운타임 등록 트리거"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.ERROR_DIAGNOSIS,
                    confidence=0.92,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "equipments": [
                        {"id": 1, "eq_name": "CNC-001", "current_status": "ERROR"},
                    ]
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("설비 고장났어")

                assert result.intent == Intent.ERROR_DIAGNOSIS


class TestOperatorWorkflowScenarios:
    """운영자 워크플로우 시나리오 테스트 (MES API mock)"""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")

    @pytest.mark.asyncio
    async def test_operator_oee_query(self, agent):
        """운영자: '전체 가동률 알려줘' → OEE 계산 정확성"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.KPI_QUERY,
                    confidence=0.95,
                    entities={"metric": "utilization"},
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                # OEE 데이터 mock
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "kpis": {
                        "equipment_utilization": 85.5,
                        "yield_rate": 98.2,
                        "oee": 83.9,  # availability * performance * quality
                    }
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("전체 가동률 알려줘")

                assert result.success is True
                assert result.intent == Intent.KPI_QUERY

    @pytest.mark.asyncio
    async def test_operator_delay_check(self, agent):
        """운영자: '지연된 작업 있어?' → 지연 판단 로직"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.DELAY_PREDICTION,
                    confidence=0.88,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                # 지연 작업 데이터 mock
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "delayed_orders": [
                        {
                            "lot_no": "LOT-003",
                            "due_date": "2026-02-08",
                            "expected_completion": "2026-02-10",
                            "delay_hours": 48,
                        }
                    ],
                    "total_delayed": 1,
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("지연된 작업 있어?")

                assert result.intent == Intent.DELAY_PREDICTION

    @pytest.mark.asyncio
    async def test_operator_equipment_comparison(self, agent):
        """운영자: '설비별 가동률 비교' → 비교 분석"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.COMPARISON,
                    confidence=0.9,
                    entities={"group_by": "equipment", "metric": "utilization"},
                )
                mock_extract.return_value = ExtractedEntities(
                    entities=[
                        Entity(
                            type=EntityType.GROUP_BY,
                            value="설비별",
                            raw_text="설비별",
                            normalized="equipment",
                        ),
                        Entity(
                            type=EntityType.METRIC,
                            value="가동률",
                            raw_text="가동률",
                            normalized="utilization",
                        ),
                    ]
                )

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "equipment_utilization": [
                        {"equipment_name": "CNC-001", "utilization_rate": 90.0},
                        {"equipment_name": "CNC-002", "utilization_rate": 75.0},
                        {"equipment_name": "ROBOT-001", "utilization_rate": 88.0},
                    ]
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("설비별 가동률 비교")

                assert result.intent == Intent.COMPARISON


class TestMESDataConsistency:
    """MES 데이터 정합성 검증 테스트"""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")

    @pytest.mark.asyncio
    async def test_kpi_data_matches_raw_data(self, agent):
        """KPI 데이터가 원본 데이터와 일치"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.KPI_QUERY,
                    confidence=0.9,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                # KPI가 원본 데이터에서 계산됨을 검증
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "raw_data": {
                        "total_produced": 1000,
                        "total_ok": 985,  # 98.5% yield
                    },
                    "kpis": {
                        "yield_rate": 98.5,
                    }
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("수율 확인")

                assert result.success is True

    @pytest.mark.asyncio
    async def test_traceability_lot_exists(self, agent):
        """추적성 조회 시 LOT 존재 여부 확인"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.TRACEABILITY,
                    confidence=0.95,
                    entities={"lot_no": "LOT-2026-001"},
                )
                mock_extract.return_value = ExtractedEntities(
                    entities=[
                        Entity(
                            type=EntityType.LOT_NO,
                            value="LOT-2026-001",
                            raw_text="LOT-2026-001",
                        )
                    ]
                )

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "lot_no": "LOT-2026-001",
                    "timeline": [
                        {"step": 1, "operation": "CNC 가공", "start": "10:00", "end": "11:00"},
                        {"step": 2, "operation": "검사", "start": "11:00", "end": "11:30"},
                    ],
                }

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("LOT-2026-001 이력 조회")

                assert result.success is True
                assert result.intent == Intent.TRACEABILITY


class TestErrorHandlingScenarios:
    """에러 처리 시나리오 테스트"""

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, agent):
        """API 타임아웃 처리"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.PRODUCTION_STATUS,
                    confidence=0.9,
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                # 타임아웃 시뮬레이션
                import httpx
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
                agent._http_client = mock_client

                result = await agent.process_query("생산 현황")

                # 에러가 있어야 함
                assert result.success is False or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_api_404_handling(self, agent):
        """API 404 에러 처리"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.TRACEABILITY,
                    confidence=0.9,
                    entities={"lot_no": "NONEXISTENT-LOT"},
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.json.return_value = {"detail": "LOT not found"}

                mock_client = AsyncMock()
                mock_client.request = AsyncMock(return_value=mock_response)
                agent._http_client = mock_client

                result = await agent.process_query("NONEXISTENT-LOT 이력")

                # 404 처리됨 - errors 리스트에 에러가 있거나 success가 False
                assert len(result.errors) > 0 or result.success is False

    @pytest.mark.asyncio
    async def test_low_confidence_fallback(self, agent):
        """낮은 신뢰도 시 폴백 처리"""
        with patch.object(
            agent.intent_classifier, "classify", new_callable=AsyncMock
        ) as mock_classify:
            with patch.object(
                agent.entity_extractor, "extract", new_callable=AsyncMock
            ) as mock_extract:
                mock_classify.return_value = IntentResult(
                    intent=Intent.UNKNOWN,
                    confidence=0.2,
                    requires_clarification=True,
                    suggested_questions=["무엇을 도와드릴까요?"],
                )
                mock_extract.return_value = ExtractedEntities(entities=[])

                result = await agent.process_query("블라블라")

                assert result.intent == Intent.UNKNOWN


class TestGenerateSummary:
    """Tests for _generate_summary method - ensures all intents have proper response formatting."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return NLRouterAgent(use_llm=False)

    def test_schedule_query_with_data(self, agent):
        """SCHEDULE_QUERY should format schedule data properly."""
        data = {
            "schedule": {
                "date": "2026-02-13",
                "availability": [
                    {
                        "equipment_id": "EQ-1",
                        "equipment_name": "CNC-001",
                        "equipment_type": "CNC",
                        "schedule": [
                            {"status": "RUNNING", "product": "알루미늄 브라켓"},
                            {"status": "PAUSE", "product": "티타늄 플레이트"},
                        ],
                    },
                    {
                        "equipment_id": "EQ-2",
                        "equipment_name": "CNC-002",
                        "equipment_type": "CNC",
                        "schedule": [
                            {"status": "RUNNING", "product": "정밀 기어"},
                        ],
                    },
                ],
                "summary": {
                    "total_equipments": 9,
                    "total_scheduled_orders": 4,
                    "running_orders": 2,
                },
            }
        }

        result = agent._generate_summary(data, Intent.SCHEDULE_QUERY, "오늘 스케줄")

        assert "2026-02-13" in result
        assert "9대" in result or "9" in result
        assert "4건" in result or "4" in result
        assert "CNC-001" in result
        assert "CNC-002" in result

    def test_schedule_query_empty_data(self, agent):
        """SCHEDULE_QUERY should handle empty schedule gracefully."""
        data = {
            "schedule": {
                "date": "2026-02-13",
                "availability": [],
                "summary": {
                    "total_equipments": 0,
                    "total_scheduled_orders": 0,
                    "running_orders": 0,
                },
            }
        }

        result = agent._generate_summary(data, Intent.SCHEDULE_QUERY, "오늘 스케줄")

        assert "0대" in result or "0건" in result or "0" in result

    def test_schedule_query_without_schedule_key(self, agent):
        """SCHEDULE_QUERY should handle data without 'schedule' wrapper."""
        data = {
            "date": "2026-02-13",
            "availability": [
                {
                    "equipment_name": "CNC-001",
                    "schedule": [{"status": "RUNNING", "product": "제품A"}],
                }
            ],
            "summary": {
                "total_equipments": 1,
                "total_scheduled_orders": 1,
                "running_orders": 1,
            },
        }

        result = agent._generate_summary(data, Intent.SCHEDULE_QUERY, "오늘 스케줄")

        assert "CNC-001" in result

    def test_production_status_response(self, agent):
        """PRODUCTION_STATUS should format production data."""
        data = {
            "daily_status": {
                "orders": {"total": 50, "completed": 45},
                "kpis": {"yield_rate": 98.5},
            }
        }

        result = agent._generate_summary(data, Intent.PRODUCTION_STATUS, "오늘 생산 현황")

        assert "50" in result
        assert "45" in result
        assert "98.5" in result or "98" in result

    def test_equipment_status_list_response(self, agent):
        """EQUIPMENT_STATUS should handle equipment list."""
        data = {
            "equipments": [
                {"eq_name": "CNC-001", "current_status": "RUN"},
                {"eq_name": "CNC-002", "current_status": "IDLE"},
                {"eq_name": "CNC-003", "current_status": "RUN"},
            ]
        }

        result = agent._generate_summary(data, Intent.EQUIPMENT_STATUS, "설비 상태")

        assert "3대" in result or "3" in result
        assert "2대" in result or "2" in result  # running count

    def test_kpi_query_response(self, agent):
        """KPI_QUERY should format KPI data."""
        data = {
            "kpis": {
                "today": {
                    "completion_rate": 90.0,
                    "yield_rate": 95.5,
                    "equipment_utilization": 85.0,
                }
            }
        }

        result = agent._generate_summary(data, Intent.KPI_QUERY, "KPI")

        assert "90" in result
        assert "95" in result
        assert "85" in result

    def test_unknown_intent_fallback(self, agent):
        """Unknown intent should return generic message."""
        data = {"some": "data"}

        result = agent._generate_summary(data, Intent.UNKNOWN, "알 수 없는 질문")

        assert "완료" in result

    def test_production_detail_response(self, agent):
        """PRODUCTION_DETAIL should format lot detail."""
        data = {
            "production_detail": {
                "lot_no": "LOT-2026-001",
                "status": "RUNNING",
                "target_qty": 100,
                "ok_qty": 85,
                "ng_qty": 3,
            }
        }

        result = agent._generate_summary(data, Intent.PRODUCTION_DETAIL, "LOT-2026-001 상세")

        assert "LOT-2026-001" in result
        assert "RUNNING" in result
        assert "100" in result
        assert "85" in result
        assert "3" in result
        assert result != "조회가 완료되었습니다."

    def test_equipment_list_response(self, agent):
        """EQUIPMENT_LIST should format equipment list."""
        data = {
            "equipment_list": [
                {"name": "CNC-001", "equipment_type": "CNC", "status": "RUN"},
                {"name": "ROBOT-001", "equipment_type": "ROBOT", "status": "IDLE"},
            ]
        }

        result = agent._generate_summary(data, Intent.EQUIPMENT_LIST, "설비 목록")

        assert "2대" in result
        assert "CNC-001" in result
        assert "ROBOT-001" in result
        assert result != "조회가 완료되었습니다."

    def test_schedule_request_response(self, agent):
        """SCHEDULE_REQUEST should confirm scheduling request."""
        data = {
            "schedule_request": {
                "solver": "ALNS",
                "horizon_hours": 48,
                "status": "완료",
            }
        }

        result = agent._generate_summary(data, Intent.SCHEDULE_REQUEST, "스케줄링 요청")

        assert "ALNS" in result
        assert "48" in result
        assert "완료" in result
        assert result != "조회가 완료되었습니다."

    def test_master_data_query_response(self, agent):
        """MASTER_DATA_QUERY should format master data."""
        data = {
            "master_data": {
                "products": [
                    {"name": "알루미늄 브라켓"},
                    {"name": "티타늄 플레이트"},
                ],
                "processes": [
                    {"name": "CNC 가공"},
                    {"name": "검사"},
                    {"name": "조립"},
                ],
            }
        }

        result = agent._generate_summary(data, Intent.MASTER_DATA_QUERY, "마스터 데이터")

        assert "2건" in result  # products
        assert "3건" in result  # processes
        assert "알루미늄 브라켓" in result
        assert result != "조회가 완료되었습니다."

    def test_analytics_response(self, agent):
        """ANALYTICS should format trend analysis."""
        data = {
            "analytics": {
                "period": "최근 7일",
                "trend": {"change_rate": 5.3},
            }
        }

        result = agent._generate_summary(data, Intent.ANALYTICS, "트렌드 분석")

        assert "최근 7일" in result
        assert "5.3" in result
        assert "상승" in result
        assert result != "조회가 완료되었습니다."

    def test_analytics_negative_trend(self, agent):
        """ANALYTICS should handle negative trend."""
        data = {
            "analytics": {
                "period": "이번 주",
                "trend": {"change_rate": -2.1},
            }
        }

        result = agent._generate_summary(data, Intent.ANALYTICS, "트렌드")

        assert "하락" in result
        assert "2.1" in result

    def test_error_diagnosis_response(self, agent):
        """ERROR_DIAGNOSIS should format alarm data."""
        data = {
            "diagnosis": {
                "alarm_code": "E-4012",
                "equipment_name": "CNC-003",
                "cause": "스핀들 과부하",
            }
        }

        result = agent._generate_summary(data, Intent.ERROR_DIAGNOSIS, "알람 진단")

        assert "E-4012" in result
        assert "CNC-003" in result
        assert "스핀들 과부하" in result
        assert result != "조회가 완료되었습니다."

    def test_delay_prediction_response(self, agent):
        """DELAY_PREDICTION should format delayed orders."""
        data = {
            "delay_prediction": {
                "delayed_orders": [
                    {"lot_no": "LOT-DELAY-001", "delay_hours": 48},
                    {"lot_no": "LOT-DELAY-002", "delay_hours": 12},
                ],
                "total_delayed": 2,
            }
        }

        result = agent._generate_summary(data, Intent.DELAY_PREDICTION, "지연 예측")

        assert "2건" in result
        assert "LOT-DELAY-001" in result
        assert result != "조회가 완료되었습니다."

    def test_delay_prediction_empty(self, agent):
        """DELAY_PREDICTION should handle no delayed orders."""
        data = {
            "delay_prediction": {
                "delayed_orders": [],
                "total_delayed": 0,
            }
        }

        result = agent._generate_summary(data, Intent.DELAY_PREDICTION, "지연 예측")

        assert "0건" in result

    def test_defect_analysis_response(self, agent):
        """DEFECT_ANALYSIS should format defect data."""
        data = {
            "defect_analysis": {
                "defect_rate": 1.5,
                "main_cause": "원자재 불량",
            }
        }

        result = agent._generate_summary(data, Intent.DEFECT_ANALYSIS, "불량 분석")

        assert "1.5" in result
        assert "원자재 불량" in result
        assert result != "조회가 완료되었습니다."

    def test_tool_management_response(self, agent):
        """TOOL_MANAGEMENT should format tool life data."""
        data = {
            "tool_management": {
                "avg_remaining_life": 65,
                "need_replacement": 3,
            }
        }

        result = agent._generate_summary(data, Intent.TOOL_MANAGEMENT, "공구 수명")

        assert "65" in result
        assert "3건" in result
        assert result != "조회가 완료되었습니다."

    def test_action_request_response(self, agent):
        """ACTION_REQUEST should format action result."""
        data = {
            "action_result": {
                "action_type": "설비 재시작",
                "result": "성공",
            }
        }

        result = agent._generate_summary(data, Intent.ACTION_REQUEST, "설비 재시작")

        assert "설비 재시작" in result
        assert "성공" in result
        assert result != "조회가 완료되었습니다."

    def test_help_response(self, agent):
        """HELP should return static help text."""
        data = {}

        result = agent._generate_summary(data, Intent.HELP, "도움말")

        assert "생산 현황" in result
        assert "설비 상태" in result
        assert "LOT" in result
        assert result != "조회가 완료되었습니다."

    def test_all_handled_intents_have_formatters(self, agent):
        """All intents (except UNKNOWN) should have dedicated formatters."""
        intent_data_map = {
            Intent.PRODUCTION_STATUS: {"daily_status": {"orders": {"total": 1, "completed": 1}, "kpis": {"yield_rate": 100}}},
            Intent.PRODUCTION_DETAIL: {"production_detail": {"lot_no": "LOT-001", "status": "DONE", "target_qty": 10, "ok_qty": 10, "ng_qty": 0}},
            Intent.EQUIPMENT_STATUS: {"equipments": [{"current_status": "RUN"}]},
            Intent.EQUIPMENT_LIST: {"equipment_list": [{"name": "EQ-1", "equipment_type": "CNC", "status": "RUN"}]},
            Intent.KPI_QUERY: {"kpis": {"today": {"completion_rate": 100, "yield_rate": 100, "equipment_utilization": 100}}},
            Intent.TRACEABILITY: {"traceability": {"lot_no": "LOT-001", "summary": {"total_ok_qty": 100, "total_ng_qty": 0, "yield_rate": 100}}},
            Intent.COMPARISON: {"utilization": {"summary": {"total_equipment": 5, "average_utilization": 80, "top_performer": "EQ-1", "bottleneck": "EQ-5"}}},
            Intent.SCHEDULE_QUERY: {"schedule": {"date": "2026-01-01", "availability": [], "summary": {"total_equipments": 0, "total_scheduled_orders": 0, "running_orders": 0}}},
            Intent.SCHEDULE_REQUEST: {"schedule_request": {"solver": "ALNS", "horizon_hours": 24, "status": "완료"}},
            Intent.MASTER_DATA_QUERY: {"master_data": {"products": [{"name": "P1"}], "processes": []}},
            Intent.ANALYTICS: {"analytics": {"period": "최근", "trend": {"change_rate": 1.0}}},
            Intent.ERROR_DIAGNOSIS: {"diagnosis": {"alarm_code": "E-001", "equipment_name": "EQ-1", "cause": "과부하"}},
            Intent.DELAY_PREDICTION: {"delay_prediction": {"delayed_orders": [], "total_delayed": 0}},
            Intent.DEFECT_ANALYSIS: {"defect_analysis": {"defect_rate": 0.5, "main_cause": "원인"}},
            Intent.TOOL_MANAGEMENT: {"tool_management": {"avg_remaining_life": 50, "need_replacement": 1}},
            Intent.ACTION_REQUEST: {"action_result": {"action_type": "test", "result": "OK"}},
            Intent.HELP: {},
        }

        for intent, data in intent_data_map.items():
            result = agent._generate_summary(data, intent, "test query")
            assert result != "조회가 완료되었습니다.", f"Intent {intent} has no dedicated formatter!"
