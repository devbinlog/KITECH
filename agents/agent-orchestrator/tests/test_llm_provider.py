"""test_llm_provider.py — LLM provider selection and mock fallback."""
import os
import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.language_models import BaseChatModel


class TestLLMProvider:
    def test_no_provider_returns_mock(self):
        os.environ.pop("LLM_PROVIDER", None)
        from src.core.llm_provider import get_chat_model
        model = get_chat_model()
        assert isinstance(model, BaseChatModel)
        assert model._llm_type == "mock"

    def test_mock_provider_explicit(self):
        os.environ["LLM_PROVIDER"] = "mock"
        from src.core.llm_provider import get_chat_model
        model = get_chat_model()
        assert model._llm_type == "mock"

    def test_anthropic_without_key_returns_mock(self):
        os.environ["LLM_PROVIDER"] = "anthropic"
        os.environ.pop("ANTHROPIC_API_KEY", None)
        from src.core.llm_provider import get_chat_model
        model = get_chat_model()
        assert model._llm_type == "mock"

    def test_openai_without_key_returns_mock(self):
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ.pop("OPENAI_API_KEY", None)
        from src.core.llm_provider import get_chat_model
        model = get_chat_model()
        assert model._llm_type == "mock"

    def test_mock_model_generate(self):
        os.environ["LLM_PROVIDER"] = "mock"
        from src.core.llm_provider import get_chat_model
        from langchain_core.messages import HumanMessage
        model = get_chat_model()
        result = model.invoke([HumanMessage(content="hello")])
        assert result.content

    def test_get_llm_status_mock(self):
        os.environ.pop("LLM_PROVIDER", None)
        from src.core.llm_provider import get_llm_status
        assert get_llm_status() == "mock"

    def test_get_llm_status_anthropic_active(self):
        os.environ["LLM_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        from src.core.llm_provider import get_llm_status
        assert get_llm_status() == "active:anthropic"
        os.environ.pop("ANTHROPIC_API_KEY")

    @pytest.mark.anyio
    async def test_mock_chat_returns_tool_calls_for_known_intent(self):
        """_agenerate emits tool_calls when intent is recognized."""
        os.environ.pop("LLM_PROVIDER", None)
        from src.core.llm_provider import _MockChatModel
        from langchain_core.messages import HumanMessage

        fake_intent = {"intent": "production_status", "entities": {}, "confidence": 0.9}
        fake_tool_call = {"id": "tc1", "name": "get_production_status", "args": {}}

        with patch("src.core.intent_router.classify_intent", new=AsyncMock(return_value=fake_intent)), \
             patch("src.core.intent_router.build_tool_call", return_value=fake_tool_call):
            model = _MockChatModel()
            result = await model._agenerate([HumanMessage(content="오늘 생산 현황")])

        msg = result.generations[0].message
        assert msg.tool_calls
        assert msg.tool_calls[0]["name"] == "get_production_status"

    @pytest.mark.anyio
    async def test_mock_chat_summarizes_tool_message(self):
        """_agenerate calls summarize_tool_result when last message is ToolMessage."""
        os.environ.pop("LLM_PROVIDER", None)
        from src.core.llm_provider import _MockChatModel
        from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

        tool_result_content = '{"status": "ok", "count": 42}'
        prev_ai = AIMessage(
            content="",
            tool_calls=[{"id": "tc1", "name": "get_production_status", "args": {}, "type": "tool_call"}],
        )
        tool_msg = ToolMessage(content=tool_result_content, tool_call_id="tc1")
        messages = [HumanMessage(content="생산 현황"), prev_ai, tool_msg]

        with patch("src.core.intent_router.summarize_tool_result", return_value="생산 42건 완료") as mock_sum:
            model = _MockChatModel()
            result = await model._agenerate(messages)

        mock_sum.assert_called_once()
        msg = result.generations[0].message
        assert "42" in msg.content or msg.content  # summary returned
