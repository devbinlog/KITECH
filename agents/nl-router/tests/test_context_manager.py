"""Tests for Conversation Manager"""

import pytest
from datetime import datetime, timedelta, timezone

from src.context.conversation_manager import (
    ConversationManager,
    ConversationContext,
    ConversationMessage,
    get_conversation_manager,
)


class TestConversationMessage:
    """Tests for ConversationMessage"""

    def test_message_creation(self):
        """Test basic message creation"""
        msg = ConversationMessage(role="user", content="오늘 생산 현황 보여줘")

        assert msg.role == "user"
        assert msg.content == "오늘 생산 현황 보여줘"
        assert msg.timestamp is not None
        assert msg.entities == {}

    def test_message_with_entities(self):
        """Test message with entities"""
        msg = ConversationMessage(
            role="assistant",
            content="오늘 생산 현황입니다.",
            intent="PRODUCTION_STATUS",
            entities={"date": "today", "scope": "all"},
        )

        assert msg.intent == "PRODUCTION_STATUS"
        assert msg.entities["date"] == "today"

    def test_message_to_dict(self):
        """Test message serialization"""
        msg = ConversationMessage(
            role="user", content="설비 상태 조회", entities={"equipment_id": "CNC-001"}
        )

        data = msg.to_dict()

        assert data["role"] == "user"
        assert data["content"] == "설비 상태 조회"
        assert data["entities"]["equipment_id"] == "CNC-001"
        assert "timestamp" in data


class TestConversationContext:
    """Tests for ConversationContext"""

    def test_context_creation(self):
        """Test context creation"""
        context = ConversationContext(session_id="session_123", user_id="user_456")

        assert context.session_id == "session_123"
        assert context.user_id == "user_456"
        assert len(context.messages) == 0

    def test_add_message(self):
        """Test adding messages to context"""
        context = ConversationContext(session_id="test")
        msg = ConversationMessage(role="user", content="Hello")

        context.add_message(msg)

        assert len(context.messages) == 1
        assert context.messages[0].content == "Hello"

    def test_entity_tracking(self):
        """Test that entities are tracked across messages"""
        context = ConversationContext(session_id="test")

        # Add message with entities
        msg1 = ConversationMessage(
            role="user", content="CNC-001 상태 조회", entities={"equipment_id": "CNC-001"}
        )
        context.add_message(msg1)

        assert context.active_entities["equipment_id"] == "CNC-001"

        # Add another message with more entities
        msg2 = ConversationMessage(
            role="user", content="오늘 이력 보여줘", entities={"date": "today"}
        )
        context.add_message(msg2)

        # Both entities should be active
        assert context.active_entities["equipment_id"] == "CNC-001"
        assert context.active_entities["date"] == "today"

    def test_get_recent_messages(self):
        """Test getting recent messages"""
        context = ConversationContext(session_id="test")

        # Add 15 messages
        for i in range(15):
            context.add_message(ConversationMessage(role="user", content=f"Message {i}"))

        recent = context.get_recent_messages(5)

        assert len(recent) == 5
        assert recent[0].content == "Message 10"
        assert recent[4].content == "Message 14"

    def test_context_summary(self):
        """Test context summary generation"""
        context = ConversationContext(session_id="test")

        context.add_message(ConversationMessage(role="user", content="오늘 생산 현황"))
        context.add_message(
            ConversationMessage(
                role="assistant", content="오늘 생산 현황입니다.", entities={"date": "today"}
            )
        )

        summary = context.get_context_summary()

        assert "오늘 생산 현황" in summary
        assert "User:" in summary
        assert "Assistant:" in summary

    def test_context_expiration(self):
        """Test context expiration check"""
        context = ConversationContext(session_id="test")

        # Fresh context should not be expired
        assert not context.is_expired(30)

        # Simulate old activity
        context.last_activity = datetime.now(timezone.utc) - timedelta(minutes=31)

        assert context.is_expired(30)

    def test_message_limit(self):
        """Test message deque limit"""
        context = ConversationContext(session_id="test")

        # Add more than 50 messages
        for i in range(60):
            context.add_message(ConversationMessage(role="user", content=f"Message {i}"))

        # Should only keep last 50
        assert len(context.messages) == 50
        assert context.messages[0].content == "Message 10"


class TestConversationManager:
    """Tests for ConversationManager"""

    @pytest.fixture
    def manager(self):
        """Create conversation manager"""
        return ConversationManager(max_contexts=10, context_timeout_minutes=30)

    def test_get_context_creates_new(self, manager):
        """Test getting context creates new if not exists"""
        context = manager.get_context("session_123", "user_456")

        assert context.session_id == "session_123"
        assert context.user_id == "user_456"

    def test_get_context_returns_existing(self, manager):
        """Test getting context returns existing"""
        context1 = manager.get_context("session_123")
        context1.add_message(ConversationMessage(role="user", content="Hello"))

        context2 = manager.get_context("session_123")

        assert context1 is context2
        assert len(context2.messages) == 1

    def test_add_user_message(self, manager):
        """Test adding user message"""
        manager.get_context("session_123")

        msg = manager.add_user_message("session_123", "오늘 생산 현황", entities={"date": "today"})

        assert msg.role == "user"
        assert msg.content == "오늘 생산 현황"

        context = manager.get_context("session_123")
        assert len(context.messages) == 1

    def test_add_assistant_message(self, manager):
        """Test adding assistant message"""
        manager.get_context("session_123")

        msg = manager.add_assistant_message(
            "session_123",
            "오늘 생산 현황입니다.",
            intent="PRODUCTION_STATUS",
            entities={"date": "today"},
            ui_schema={"layout": "dashboard", "components": []},
        )

        assert msg.role == "assistant"
        assert msg.intent == "PRODUCTION_STATUS"
        assert msg.ui_schema is not None

    def test_get_history(self, manager):
        """Test getting conversation history"""
        manager.add_user_message("session_123", "Query 1")
        manager.add_assistant_message("session_123", "Response 1")
        manager.add_user_message("session_123", "Query 2")

        history = manager.get_history("session_123")

        assert len(history) == 3
        assert history[0]["content"] == "Query 1"
        assert history[1]["content"] == "Response 1"

    def test_get_history_empty(self, manager):
        """Test getting history for non-existent session"""
        history = manager.get_history("nonexistent")
        assert history == []

    def test_clear_context(self, manager):
        """Test clearing context"""
        manager.add_user_message("session_123", "Hello")
        manager.clear_context("session_123")

        history = manager.get_history("session_123")
        assert history == []

    def test_max_contexts_limit(self, manager):
        """Test max contexts limit evicts oldest"""
        # Create max contexts
        for i in range(10):
            ctx = manager.get_context(f"session_{i}")
            ctx.last_activity = datetime.now(timezone.utc) - timedelta(minutes=i)

        # Create one more
        manager.get_context("session_new")

        # Should have evicted the oldest (session_9)
        assert "session_9" not in manager._contexts
        assert "session_new" in manager._contexts

    def test_get_status(self, manager):
        """Test getting manager status"""
        manager.add_user_message("session_1", "Hello")
        manager.add_user_message("session_2", "World")

        status = manager.get_status()

        assert status["total_contexts"] == 2
        assert status["max_contexts"] == 10
        assert len(status["contexts"]) == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, manager):
        """Test cleanup of expired contexts"""
        manager.get_context("active")
        expired_ctx = manager.get_context("expired")
        expired_ctx.last_activity = datetime.now(timezone.utc) - timedelta(minutes=31)

        await manager._cleanup_expired_contexts()

        assert "active" in manager._contexts
        assert "expired" not in manager._contexts


class TestGlobalConversationManager:
    """Tests for global conversation manager"""

    def test_get_conversation_manager_singleton(self):
        """Test get_conversation_manager returns same instance"""
        import src.context.conversation_manager as cm_module

        # Reset global instance
        cm_module._conversation_manager = None

        manager1 = get_conversation_manager()
        manager2 = get_conversation_manager()

        assert manager1 is manager2


# ============================================================================
# 보강된 테스트: 데이터 정합성 검증
# ============================================================================

class TestContextStorageConsistency:
    """Context 저장/복원 정합성 테스트"""

    @pytest.fixture
    def manager(self):
        return ConversationManager(max_contexts=10, context_timeout_minutes=30)

    def test_message_order_preserved(self, manager):
        """메시지 순서가 보존됨"""
        session_id = "test_order"

        manager.add_user_message(session_id, "첫 번째")
        manager.add_assistant_message(session_id, "응답 1")
        manager.add_user_message(session_id, "두 번째")
        manager.add_assistant_message(session_id, "응답 2")

        history = manager.get_history(session_id)

        assert history[0]["content"] == "첫 번째"
        assert history[1]["content"] == "응답 1"
        assert history[2]["content"] == "두 번째"
        assert history[3]["content"] == "응답 2"

    def test_entity_persistence_across_messages(self, manager):
        """메시지 간 엔티티 지속성"""
        session_id = "test_entity"

        # 첫 메시지에서 설비 언급
        manager.add_user_message(
            session_id,
            "CNC-001 상태 조회",
            entities={"equipment_id": "CNC-001"},
        )

        # 후속 메시지에서 추가 엔티티
        manager.add_user_message(
            session_id,
            "오늘 가동률은?",
            entities={"date": "today", "metric": "utilization"},
        )

        context = manager.get_context(session_id)

        # 모든 엔티티가 active_entities에 있어야 함
        assert context.active_entities.get("equipment_id") == "CNC-001"
        assert context.active_entities.get("date") == "today"
        assert context.active_entities.get("metric") == "utilization"

    def test_entity_update_overwrites_old(self, manager):
        """새 엔티티가 기존 엔티티를 덮어씀"""
        session_id = "test_overwrite"

        manager.add_user_message(
            session_id,
            "CNC-001 상태",
            entities={"equipment_id": "CNC-001"},
        )

        manager.add_user_message(
            session_id,
            "ROBOT-002 상태",
            entities={"equipment_id": "ROBOT-002"},
        )

        context = manager.get_context(session_id)

        # 최신 값으로 업데이트됨
        assert context.active_entities["equipment_id"] == "ROBOT-002"

    def test_ui_schema_stored_in_message(self, manager):
        """UI 스키마가 메시지에 저장됨"""
        session_id = "test_ui"

        ui_schema = {
            "layout": "dashboard",
            "components": [{"type": "KPICard", "props": {"value": 95}}],
        }

        manager.add_assistant_message(
            session_id,
            "생산 현황입니다.",
            ui_schema=ui_schema,
        )

        context = manager.get_context(session_id)
        last_msg = context.messages[-1]

        assert last_msg.ui_schema == ui_schema


class TestConversationContinuity:
    """대화 이력 연속성 테스트"""

    @pytest.fixture
    def manager(self):
        return ConversationManager(max_contexts=10, context_timeout_minutes=30)

    def test_conversation_resumes_after_gap(self, manager):
        """대화 중단 후 재개"""
        session_id = "test_resume"

        # 첫 대화
        manager.add_user_message(session_id, "CNC-001 상태", entities={"equipment_id": "CNC-001"})
        manager.add_assistant_message(session_id, "CNC-001은 가동 중입니다.")

        # 컨텍스트 조회 (중단 후 재개 시뮬레이션)
        context = manager.get_context(session_id)

        # 이전 엔티티 유지
        assert context.active_entities.get("equipment_id") == "CNC-001"

        # 대화 재개
        manager.add_user_message(session_id, "그 설비 이력 보여줘")

        history = manager.get_history(session_id)
        assert len(history) == 3

    def test_clear_resets_completely(self, manager):
        """컨텍스트 초기화 시 완전 리셋"""
        session_id = "test_clear"

        manager.add_user_message(session_id, "테스트", entities={"date": "today"})
        manager.add_assistant_message(session_id, "응답")

        # 초기화
        manager.clear_context(session_id)

        history = manager.get_history(session_id)
        assert history == []

    def test_summary_reflects_current_state(self, manager):
        """요약이 현재 상태를 반영"""
        session_id = "test_summary"

        manager.add_user_message(session_id, "오늘 생산 현황")
        manager.add_assistant_message(session_id, "오늘 100개 생산했습니다.")
        manager.add_user_message(session_id, "불량은 몇 개야?")

        context = manager.get_context(session_id)
        summary = context.get_context_summary()

        # 모든 대화 내용이 요약에 포함
        assert "오늘 생산 현황" in summary
        assert "불량" in summary


class TestSessionIsolation:
    """세션 격리 테스트"""

    @pytest.fixture
    def manager(self):
        return ConversationManager(max_contexts=10, context_timeout_minutes=30)

    def test_different_sessions_independent(self, manager):
        """다른 세션은 독립적"""
        session1 = "user_1"
        session2 = "user_2"

        manager.add_user_message(session1, "CNC-001", entities={"equipment_id": "CNC-001"})
        manager.add_user_message(session2, "ROBOT-002", entities={"equipment_id": "ROBOT-002"})

        ctx1 = manager.get_context(session1)
        ctx2 = manager.get_context(session2)

        assert ctx1.active_entities["equipment_id"] == "CNC-001"
        assert ctx2.active_entities["equipment_id"] == "ROBOT-002"

    def test_session_messages_not_leaked(self, manager):
        """세션 메시지가 다른 세션으로 누출되지 않음"""
        session1 = "private_1"
        session2 = "private_2"

        manager.add_user_message(session1, "비밀 정보")

        history2 = manager.get_history(session2)

        assert history2 == []
        assert len(manager.get_history(session1)) == 1


class TestMessageLimitBehavior:
    """메시지 제한 동작 테스트"""

    def test_oldest_messages_evicted_first(self):
        """오래된 메시지가 먼저 제거됨"""
        context = ConversationContext(session_id="test_evict")

        # 55개 메시지 추가 (제한 50개)
        for i in range(55):
            context.add_message(
                ConversationMessage(role="user", content=f"Message {i}")
            )

        # 50개만 유지
        assert len(context.messages) == 50

        # 가장 오래된 5개가 제거됨
        assert context.messages[0].content == "Message 5"
        assert context.messages[-1].content == "Message 54"

    def test_entities_preserved_despite_eviction(self):
        """메시지 제거 후에도 엔티티 보존"""
        context = ConversationContext(session_id="test_entity_preserve")

        # 초기 메시지에 엔티티 설정
        context.add_message(
            ConversationMessage(
                role="user",
                content="CNC-001",
                entities={"equipment_id": "CNC-001"},
            )
        )

        # 50개 추가하여 초기 메시지 제거
        for i in range(55):
            context.add_message(
                ConversationMessage(role="user", content=f"Msg {i}")
            )

        # 초기 메시지는 제거됐지만 엔티티는 유지
        assert context.active_entities.get("equipment_id") == "CNC-001"


class TestContextExpiration:
    """컨텍스트 만료 테스트"""

    @pytest.fixture
    def manager(self):
        return ConversationManager(max_contexts=5, context_timeout_minutes=30)

    def test_expired_context_removed(self, manager):
        """만료된 컨텍스트 제거"""
        session_id = "test_expire"

        manager.add_user_message(session_id, "테스트")

        # 만료 시뮬레이션
        context = manager.get_context(session_id)
        context.last_activity = datetime.now(timezone.utc) - timedelta(minutes=31)

        # 만료 확인
        assert context.is_expired(30)

    def test_activity_updates_timestamp(self, manager):
        """활동 시 타임스탬프 업데이트"""
        session_id = "test_activity"

        manager.add_user_message(session_id, "첫 메시지")
        ctx = manager.get_context(session_id)
        first_activity = ctx.last_activity

        # 잠시 대기
        import time
        time.sleep(0.01)

        manager.add_user_message(session_id, "두 번째 메시지")
        ctx = manager.get_context(session_id)

        assert ctx.last_activity > first_activity


class TestMultiTurnConversation:
    """다중 턴 대화 시나리오 테스트"""

    @pytest.fixture
    def manager(self):
        return ConversationManager(max_contexts=10, context_timeout_minutes=30)

    def test_equipment_inquiry_workflow(self, manager):
        """설비 조회 워크플로우: 설비 지정 → 상세 조회"""
        session_id = "equipment_flow"

        # Turn 1: 설비 지정
        manager.add_user_message(
            session_id,
            "CNC-001 상태 알려줘",
            entities={"equipment_id": "CNC-001"},
        )
        manager.add_assistant_message(
            session_id,
            "CNC-001은 가동 중입니다. 가동률 85%",
        )

        # Turn 2: 컨텍스트 기반 후속 질문
        manager.add_user_message(
            session_id,
            "그 설비 이력 보여줘",
        )

        ctx = manager.get_context(session_id)

        # equipment_id가 컨텍스트에 유지되어야 함
        assert ctx.active_entities["equipment_id"] == "CNC-001"

    def test_production_inquiry_workflow(self, manager):
        """생산 조회 워크플로우: 현황 → 상세"""
        session_id = "production_flow"

        # Turn 1: 전체 현황
        manager.add_user_message(
            session_id,
            "오늘 생산 현황",
            entities={"date": "today"},
        )
        manager.add_assistant_message(
            session_id,
            "오늘 총 500개 생산, 완료율 80%",
        )

        # Turn 2: 특정 LOT 상세
        manager.add_user_message(
            session_id,
            "LOT-2026-001 상세 보여줘",
            entities={"lot_no": "LOT-2026-001"},
        )

        ctx = manager.get_context(session_id)

        # 날짜와 LOT 둘 다 유지
        assert ctx.active_entities["date"] == "today"
        assert ctx.active_entities["lot_no"] == "LOT-2026-001"

    def test_comparison_workflow(self, manager):
        """비교 워크플로우: 단일 조회 → 비교"""
        session_id = "comparison_flow"

        # Turn 1: 첫 번째 설비
        manager.add_user_message(
            session_id,
            "CNC-001 가동률",
            entities={"equipment_id": "CNC-001", "metric": "utilization"},
        )

        # Turn 2: 비교 요청
        manager.add_user_message(
            session_id,
            "다른 CNC 설비랑 비교해줘",
            entities={"group_by": "equipment"},
        )

        ctx = manager.get_context(session_id)

        # 기존 메트릭 유지 + 그룹핑 추가
        assert ctx.active_entities["metric"] == "utilization"
        assert ctx.active_entities["group_by"] == "equipment"
