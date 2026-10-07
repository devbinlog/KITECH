"""llm_provider.py — LLM provider abstraction for agent-orchestrator.

Supports Anthropic, OpenAI, Ollama, and Mock (deterministic fallback).
Provider is selected via LLM_PROVIDER env var. If the required API key is
missing, or no provider is set, falls back to _MockChatModel automatically.
"""
from __future__ import annotations

import os
from typing import Any, Iterator, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


# ---------------------------------------------------------------------------
# Mock model — deterministic, no network
# ---------------------------------------------------------------------------


class _MockChatModel(BaseChatModel):
    """Deterministic fake model — returns a fixed 'LLM not configured' message.

    Used when no LLM_PROVIDER is set or when API key is missing.
    Enables service boot and tests without real LLM access.
    """

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Sync path: fixed fallback (real calls go through _agenerate)
        last_content = messages[-1].content if messages else ""
        response_text = (
            f"LLM 미설정 — Mock 응답입니다. "
            f"실제 LLM을 사용하려면 LLM_PROVIDER 환경변수를 설정하세요. "
            f"입력: {str(last_content)[:100]}"
        )
        msg = AIMessage(content=response_text)
        return ChatResult(generations=[ChatGeneration(message=msg)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        from langchain_core.messages import HumanMessage, ToolMessage
        from .intent_router import classify_intent, build_tool_call, summarize_tool_result

        # Tool result path: last message is a ToolMessage → produce natural-language summary
        if messages and isinstance(messages[-1], ToolMessage):
            try:
                import json as _j
                content = messages[-1].content
                result = _j.loads(content) if isinstance(content, str) else content
            except Exception:
                result = {"raw": str(messages[-1].content)[:200]}
            # Find tool name from the preceding AIMessage that had tool_calls
            tool_name = "unknown"
            for m in reversed(messages[:-1]):
                tcs = getattr(m, "tool_calls", None)
                if tcs:
                    tool_name = tcs[0].get("name", "unknown")
                    break
            summary = summarize_tool_result("unknown", tool_name, result)
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=summary))])

        # Human message path: classify intent and emit tool_call or plain text
        last_human = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        if not last_human:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="입력이 없습니다."))])

        intent_data = await classify_intent(str(last_human.content))
        intent = intent_data.get("intent", "unknown")

        # nl-router rule-based fallback gives low confidence even when intent is correct.
        # Trust the intent classification itself; "unknown" is the explicit give-up signal.
        if intent == "unknown":
            return ChatResult(generations=[ChatGeneration(message=AIMessage(
                content="요청 의도를 파악하지 못했습니다. 예: '오늘 생산 현황', '설비 상태'."
            ))])

        tool_call = build_tool_call(intent_data)
        if not tool_call:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(
                content=f"의도 '{intent}'에 매핑된 tool이 없습니다."
            ))])

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[tool_call]))])

    def bind_tools(self, tools: Any, **kwargs: Any) -> "_MockChatModel":
        """Mock provider doesn't actually use tools — return self to satisfy interface.

        Real providers (ChatAnthropic, ChatOpenAI, ChatOllama) implement this
        natively. Mock fallback ignores the tools and produces fixed responses.
        """
        return self


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------


def get_chat_model() -> BaseChatModel:
    """Return a configured BaseChatModel based on environment variables.

    Selection logic:
    - LLM_PROVIDER=anthropic → ChatAnthropic (fallback to Mock if no API key)
    - LLM_PROVIDER=openai   → ChatOpenAI (fallback to Mock if no API key)
    - LLM_PROVIDER=ollama   → ChatOllama (no key required)
    - anything else          → _MockChatModel

    Env vars:
        LLM_PROVIDER:       anthropic | openai | ollama (default: unset → mock)
        LLM_MODEL:          model name override (provider-specific default if unset)
        LLM_TEMPERATURE:    float, default 0.1
        ANTHROPIC_API_KEY:  required for anthropic provider
        OPENAI_API_KEY:     required for openai provider
        OLLAMA_BASE_URL:    default http://host.docker.internal:11434
    """
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    model_name = os.getenv("LLM_MODEL", "").strip()
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            return _MockChatModel()
        from langchain_anthropic import ChatAnthropic  # type: ignore[import]

        return ChatAnthropic(
            model=model_name or "claude-3-5-sonnet-20241022",
            temperature=temperature,
        )

    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            return _MockChatModel()
        from langchain_openai import ChatOpenAI  # type: ignore[import]

        return ChatOpenAI(
            model=model_name or "gpt-4o-mini",
            temperature=temperature,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama  # type: ignore[import]

        return ChatOllama(
            model=model_name or "llama3.2",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
        )

    else:
        return _MockChatModel()


def get_llm_status() -> str:
    """Return a status string for /health endpoint.

    Returns:
        'active:anthropic', 'active:openai', 'active:ollama', or 'mock'
    """
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    if provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        return "active:anthropic"
    elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return "active:openai"
    elif provider == "ollama":
        return "active:ollama"
    return "mock"
