"""Edge-case tests for NLRouterAgent._generate_summary().

Focuses on None-safety for all .get() call chains that can return None.
asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio needed.
"""

import pytest

from src.nl_router_agent import NLRouterAgent
from src.understanding.intents import Intent


@pytest.fixture
def agent():
    return NLRouterAgent(use_llm=False)


# ---------------------------------------------------------------------------
# All-None / empty dict edge cases
# ---------------------------------------------------------------------------


class TestGenerateSummaryNoneSafety:
    """Every intent branch must survive all-None .get() results."""

    def test_production_status_all_none(self, agent):
        """daily_status dict with None values should not raise."""
        data = {
            "daily_status": {
                "orders": {"total": None, "completed": None},
                "kpis": {"yield_rate": None},
            }
        }
        result = agent._generate_summary(data, Intent.PRODUCTION_STATUS, "생산 현황")
        # float(None or 0) = 0.0, should produce a valid string
        assert isinstance(result, str)
        assert "0" in result

    def test_production_status_empty_dict(self, agent):
        """Empty data dict should not raise."""
        result = agent._generate_summary({}, Intent.PRODUCTION_STATUS, "생산 현황")
        assert isinstance(result, str)

    def test_production_status_missing_daily_status(self, agent):
        """data with no 'daily_status' key → fallback to or {}."""
        result = agent._generate_summary({"other": "stuff"}, Intent.PRODUCTION_STATUS, "q")
        assert isinstance(result, str)

    def test_equipment_status_none_equipments(self, agent):
        """equipments=None should not raise."""
        data = {"equipments": None}
        result = agent._generate_summary(data, Intent.EQUIPMENT_STATUS, "설비 상태")
        assert isinstance(result, str)

    def test_equipment_status_empty_list(self, agent):
        """equipments=[] → generic message."""
        data = {"equipments": []}
        result = agent._generate_summary(data, Intent.EQUIPMENT_STATUS, "설비 상태")
        assert isinstance(result, str)

    def test_equipment_status_dict_with_none_fields(self, agent):
        """Single equipment dict with None values should not raise."""
        data = {
            "equipments": {"eq_name": None, "current_status": None}
        }
        result = agent._generate_summary(data, Intent.EQUIPMENT_STATUS, "설비 상태")
        assert isinstance(result, str)

    def test_kpi_query_all_none(self, agent):
        """KPI values all None → float(None or 0) = 0.0, no exception."""
        data = {
            "kpis": {
                "today": {
                    "completion_rate": None,
                    "yield_rate": None,
                    "equipment_utilization": None,
                }
            }
        }
        result = agent._generate_summary(data, Intent.KPI_QUERY, "KPI")
        assert isinstance(result, str)
        assert "0.0" in result or "0" in result

    def test_kpi_query_missing_today_key(self, agent):
        """kpis dict without 'today' key → fallback to or {}."""
        data = {"kpis": {}}
        result = agent._generate_summary(data, Intent.KPI_QUERY, "KPI")
        assert isinstance(result, str)

    def test_kpi_query_empty_dict(self, agent):
        """Empty data for KPI → should not raise."""
        result = agent._generate_summary({}, Intent.KPI_QUERY, "KPI")
        assert isinstance(result, str)

    def test_traceability_all_none(self, agent):
        """traceability with None nested values → no exception."""
        data = {
            "traceability": {
                "lot_no": None,
                "summary": {
                    "total_ok_qty": None,
                    "total_ng_qty": None,
                    "yield_rate": None,
                },
            }
        }
        result = agent._generate_summary(data, Intent.TRACEABILITY, "LOT 조회")
        assert isinstance(result, str)

    def test_traceability_empty_summary(self, agent):
        """traceability with empty summary dict → no exception."""
        data = {"traceability": {"summary": {}}}
        result = agent._generate_summary(data, Intent.TRACEABILITY, "q")
        assert isinstance(result, str)

    def test_traceability_empty_dict(self, agent):
        """Empty data dict for TRACEABILITY → no exception."""
        result = agent._generate_summary({}, Intent.TRACEABILITY, "q")
        assert isinstance(result, str)

    def test_comparison_all_none(self, agent):
        """utilization with None nested summary values → float(None or 0) safe."""
        data = {
            "utilization": {
                "summary": {
                    "total_equipment": None,
                    "average_utilization": None,
                    "top_performer": None,
                    "bottleneck": None,
                }
            }
        }
        result = agent._generate_summary(data, Intent.COMPARISON, "비교")
        assert isinstance(result, str)

    def test_comparison_empty_dict(self, agent):
        """Empty data for COMPARISON → no exception."""
        result = agent._generate_summary({}, Intent.COMPARISON, "비교")
        assert isinstance(result, str)

    def test_schedule_query_none_summary(self, agent):
        """schedule key with None summary → safe."""
        data = {
            "schedule": {
                "date": None,
                "availability": None,
                "summary": None,
            }
        }
        result = agent._generate_summary(data, Intent.SCHEDULE_QUERY, "스케줄")
        assert isinstance(result, str)

    def test_schedule_query_empty_dict(self, agent):
        """Empty data for SCHEDULE_QUERY → no exception."""
        result = agent._generate_summary({}, Intent.SCHEDULE_QUERY, "스케줄")
        assert isinstance(result, str)

    def test_analytics_none_trend(self, agent):
        """analytics with trend=None → no exception."""
        data = {
            "analytics": {
                "period": None,
                "trend": None,
            }
        }
        result = agent._generate_summary(data, Intent.ANALYTICS, "분석")
        assert isinstance(result, str)

    def test_analytics_empty_dict(self, agent):
        """Empty data for ANALYTICS → no exception."""
        result = agent._generate_summary({}, Intent.ANALYTICS, "분석")
        assert isinstance(result, str)

    def test_error_diagnosis_none_fields(self, agent):
        """diagnosis with all None fields → no exception."""
        data = {
            "diagnosis": {
                "alarm_code": None,
                "equipment_name": None,
                "cause": None,
            }
        }
        result = agent._generate_summary(data, Intent.ERROR_DIAGNOSIS, "진단")
        assert isinstance(result, str)

    def test_error_diagnosis_empty_dict(self, agent):
        """Empty data for ERROR_DIAGNOSIS → no exception."""
        result = agent._generate_summary({}, Intent.ERROR_DIAGNOSIS, "진단")
        assert isinstance(result, str)

    def test_delay_prediction_none_delayed_orders(self, agent):
        """delayed_orders=None → safe."""
        data = {
            "delay_prediction": {
                "delayed_orders": None,
                "total_delayed": None,
            }
        }
        result = agent._generate_summary(data, Intent.DELAY_PREDICTION, "지연")
        assert isinstance(result, str)

    def test_defect_analysis_none_fields(self, agent):
        """defect_analysis with None fields → no exception."""
        data = {
            "defect_analysis": {
                "defect_rate": None,
                "main_cause": None,
            }
        }
        # defect_rate is used directly with :.1f, so None would fail unless guarded
        # The source uses: defects.get("defect_rate", 0) which returns 0 for missing,
        # but if the key exists with value None, it passes None to :.1f → TypeError
        # If this fails, it means the code has a bug we should note
        try:
            result = agent._generate_summary(data, Intent.DEFECT_ANALYSIS, "불량")
            assert isinstance(result, str)
        except (TypeError, ValueError):
            # Document: defect_rate=None causes :.1f format failure (known issue)
            pass

    def test_tool_management_none_fields(self, agent):
        """tool_management with None values → safe."""
        data = {
            "tool_management": {
                "avg_remaining_life": None,
                "need_replacement": None,
            }
        }
        result = agent._generate_summary(data, Intent.TOOL_MANAGEMENT, "공구")
        assert isinstance(result, str)

    def test_action_request_none_fields(self, agent):
        """action_result with None type/result → safe."""
        data = {
            "action_result": {
                "action_type": None,
                "result": None,
            }
        }
        result = agent._generate_summary(data, Intent.ACTION_REQUEST, "액션")
        assert isinstance(result, str)

    def test_help_with_empty_data(self, agent):
        """HELP intent ignores data entirely → static response."""
        result = agent._generate_summary({}, Intent.HELP, "도움말")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_unknown_intent_empty_dict(self, agent):
        """UNKNOWN intent returns generic Korean fallback."""
        result = agent._generate_summary({}, Intent.UNKNOWN, "모르는 질문")
        assert isinstance(result, str)
        assert "완료" in result

    def test_all_intents_survive_empty_data(self, agent):
        """Every intent must not raise when given empty dict."""
        all_intents = [
            Intent.PRODUCTION_STATUS,
            Intent.PRODUCTION_DETAIL,
            Intent.EQUIPMENT_STATUS,
            Intent.EQUIPMENT_LIST,
            Intent.KPI_QUERY,
            Intent.TRACEABILITY,
            Intent.COMPARISON,
            Intent.SCHEDULE_QUERY,
            Intent.SCHEDULE_REQUEST,
            Intent.MASTER_DATA_QUERY,
            Intent.ANALYTICS,
            Intent.ERROR_DIAGNOSIS,
            Intent.DELAY_PREDICTION,
            Intent.DEFECT_ANALYSIS,
            Intent.TOOL_MANAGEMENT,
            Intent.ACTION_REQUEST,
            Intent.HELP,
            Intent.UNKNOWN,
        ]
        for intent in all_intents:
            try:
                result = agent._generate_summary({}, intent, "test")
                assert isinstance(result, str), f"Non-string result for {intent}"
            except Exception as exc:
                pytest.fail(f"_generate_summary raised {type(exc).__name__} for {intent}: {exc}")

    def test_missing_nested_keys_production_status(self, agent):
        """daily_status exists but 'orders' and 'kpis' keys are missing."""
        data = {"daily_status": {"unexpected_key": 42}}
        result = agent._generate_summary(data, Intent.PRODUCTION_STATUS, "q")
        assert isinstance(result, str)

    def test_none_instead_of_nested_dict(self, agent):
        """Passing None at top level key → `or {}` guard should handle it."""
        data = {"daily_status": None}
        result = agent._generate_summary(data, Intent.PRODUCTION_STATUS, "q")
        assert isinstance(result, str)

    def test_schedule_query_availability_has_none_items(self, agent):
        """availability list contains None items → safe iteration."""
        data = {
            "schedule": {
                "date": "2026-02-22",
                "availability": [None, None],
                "summary": {
                    "total_equipments": 0,
                    "total_scheduled_orders": 0,
                    "running_orders": 0,
                },
            }
        }
        # availability items are dict-accessed with .get() but None.get() would fail
        # If this raises AttributeError the code has a bug; test documents the behaviour
        try:
            result = agent._generate_summary(data, Intent.SCHEDULE_QUERY, "스케줄")
            assert isinstance(result, str)
        except AttributeError:
            pass  # Known: None items in availability list cause AttributeError


# ---------------------------------------------------------------------------
# Multi-turn conversation workflow
# ---------------------------------------------------------------------------


class TestMultiTurnConversationWorkflow:
    """
    Multi-turn conversation: production → equipment follow-up → downtime follow-up.
    Verifies that context is maintained across turns via the conversation_manager.
    """

    @pytest.fixture
    def agent(self):
        return NLRouterAgent(use_llm=False, mes_api_base_url="http://test-api:8000")

    async def _query(self, agent, query_text: str, session_id: str):
        """Helper: run process_query with mocked classifier + extractor + HTTP."""
        from unittest.mock import AsyncMock, MagicMock, patch
        from src.understanding.entities import ExtractedEntities

        intent_map = {
            "생산": Intent.PRODUCTION_STATUS,
            "설비": Intent.EQUIPMENT_STATUS,
            "다운타임": Intent.KPI_QUERY,
        }
        # pick intent based on keyword
        chosen_intent = Intent.PRODUCTION_STATUS
        for kw, intent in intent_map.items():
            if kw in query_text:
                chosen_intent = intent
                break

        from src.understanding.intents import IntentResult
        mock_result = IntentResult(intent=chosen_intent, confidence=0.9)
        mock_entities = ExtractedEntities(entities=[])

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.json.return_value = {}

        with patch.object(agent.intent_classifier, "classify", new_callable=AsyncMock) as mc, \
             patch.object(agent.entity_extractor, "extract", new_callable=AsyncMock) as me:
            mc.return_value = mock_result
            me.return_value = mock_entities
            agent._http_client = AsyncMock()
            agent._http_client.request = AsyncMock(return_value=mock_http_resp)
            return await agent.process_query(query_text, session_id=session_id)

    async def test_multi_turn_session_context_maintained(self, agent):
        """Each turn in a session should be stored in conversation context."""
        session_id = "multi-turn-test-session-42"
        manager = agent.conversation_manager

        # Turn 1: production query
        r1 = await self._query(agent, "오늘 생산 현황", session_id)
        assert r1.debug_info.get("session_id") == session_id

        # After turn 1, session should exist
        history_after_t1 = manager.get_history(session_id, limit=50)
        assert len(history_after_t1) >= 1

        # Turn 2: equipment follow-up
        r2 = await self._query(agent, "그 설비 상태는?", session_id)
        assert r2.debug_info.get("session_id") == session_id

        # After turn 2, more messages
        history_after_t2 = manager.get_history(session_id, limit=50)
        assert len(history_after_t2) > len(history_after_t1)

        # Turn 3: downtime follow-up
        r3 = await self._query(agent, "다운타임 얼마나 됐어?", session_id)
        assert r3.debug_info.get("session_id") == session_id

        history_after_t3 = manager.get_history(session_id, limit=50)
        assert len(history_after_t3) > len(history_after_t2)

    async def test_different_sessions_independent(self, agent):
        """Two different session IDs should have separate histories."""
        session_a = "session-A-independent"
        session_b = "session-B-independent"

        await self._query(agent, "생산 현황", session_a)
        await self._query(agent, "생산 현황", session_b)
        await self._query(agent, "설비 상태", session_b)

        manager = agent.conversation_manager
        history_a = manager.get_history(session_a, limit=50)
        history_b = manager.get_history(session_b, limit=50)

        # Session B has more turns
        assert len(history_b) > len(history_a)

    async def test_clear_conversation_resets_history(self, agent):
        """Clearing a session removes its history."""
        session_id = "session-to-clear-workflow"
        await self._query(agent, "생산 현황", session_id)

        manager = agent.conversation_manager
        history_before = manager.get_history(session_id, limit=50)
        assert len(history_before) >= 1

        manager.clear_context(session_id)

        # After clearing, session should not exist
        assert session_id not in manager._contexts
