"""test_graph.py — LangGraph module unit tests with mock model."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage


# ---------------------------------------------------------------------------
# AgentState tests
# ---------------------------------------------------------------------------

class TestAgentState:
    def test_state_keys(self):
        from src.graph.state import AgentState
        keys = AgentState.__annotations__.keys()
        assert "messages" in keys
        assert "tools_used" in keys
        assert "session_id" in keys
        assert "trace_id" in keys

    def test_state_has_new_fields(self):
        from src.graph.state import AgentState
        keys = AgentState.__annotations__.keys()
        assert "active_tools" in keys
        assert "intent" in keys


# ---------------------------------------------------------------------------
# should_continue tests
# ---------------------------------------------------------------------------

class TestShouldContinue:
    def test_ends_when_no_tool_calls(self):
        from src.graph.nodes import should_continue
        msg = AIMessage(content="Hello")
        state = {"messages": [msg], "tools_used": [], "session_id": "", "trace_id": ""}
        assert should_continue(state) == "end"

    def test_tool_call_when_tool_calls_present(self):
        from src.graph.nodes import should_continue
        msg = AIMessage(content="", tool_calls=[{"name": "foo", "args": {}, "id": "1", "type": "tool_call"}])
        state = {"messages": [msg], "tools_used": [], "session_id": "", "trace_id": ""}
        assert should_continue(state) == "tool_call"

    def test_ends_on_empty_messages(self):
        from src.graph.nodes import should_continue
        state = {"messages": [], "tools_used": [], "session_id": "", "trace_id": ""}
        assert should_continue(state) == "end"


# ---------------------------------------------------------------------------
# make_reasoning_node tests
# ---------------------------------------------------------------------------

class TestReasoningNode:
    @pytest.mark.anyio
    async def test_reasoning_node_returns_message(self):
        from src.graph.nodes import make_reasoning_node
        mock_model = MagicMock()
        ai_msg = AIMessage(content="test response")
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)
        mock_model.bind_tools = MagicMock(return_value=mock_model)

        node = make_reasoning_node(mock_model, [])
        state = {
            "messages": [HumanMessage(content="hi")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
        }
        result = await node(state)
        assert result["messages"] == [ai_msg]

    @pytest.mark.anyio
    async def test_reasoning_node_sync_fallback(self):
        from src.graph.nodes import make_reasoning_node
        ai_msg = AIMessage(content="sync response")
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=NotImplementedError)
        mock_model.invoke = MagicMock(return_value=ai_msg)

        node = make_reasoning_node(mock_model, [])
        state = {
            "messages": [HumanMessage(content="hi")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
        }
        result = await node(state)
        assert result["messages"] == [ai_msg]


# ---------------------------------------------------------------------------
# intent_classify_node tests
# ---------------------------------------------------------------------------

class TestIntentClassifyNode:
    @pytest.mark.anyio
    async def test_intent_classify_node_sets_state(self):
        from src.graph.nodes import intent_classify_node
        from langchain_core.messages import SystemMessage

        fake_intent = {"intent": "production_status", "entities": {}, "confidence": 0.9}
        fake_tools = ["get_production_status", "list_lines"]
        fake_prompt = "You are an assistant."

        with patch("src.core.intent_router.classify_intent", new=AsyncMock(return_value=fake_intent)), \
             patch("src.core.intent_router.select_tools_for_intent", return_value=fake_tools), \
             patch("src.core.system_prompts.build_system_prompt", return_value=fake_prompt):
            state = {
                "messages": [HumanMessage(content="오늘 생산 현황")],
                "tools_used": [],
                "session_id": "s1",
                "trace_id": "t1",
                "active_tools": [],
                "intent": None,
            }
            result = await intent_classify_node(state)

        assert result["intent"] == "production_status"
        assert result["active_tools"] == fake_tools
        assert isinstance(result["messages"][0], SystemMessage)

    @pytest.mark.anyio
    async def test_intent_classify_node_no_human_message(self):
        from src.graph.nodes import intent_classify_node

        state = {
            "messages": [AIMessage(content="previous AI message")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "active_tools": [],
            "intent": None,
        }
        result = await intent_classify_node(state)
        assert result == {}


# ---------------------------------------------------------------------------
# build_agent_graph smoke test (default = react)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_build_agent_graph_no_tools():
    """Graph builds without errors when tools and checkpoint are unavailable."""
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ.pop("ORCHESTRATOR_PIPELINE", None)

    with patch("src.core.tool_loader.load_tools_from_registry", new=AsyncMock(side_effect=Exception("no registry"))):
        from src.graph.builder import build_agent_graph
        graph = await build_agent_graph()
        assert graph is not None


@pytest.mark.anyio
async def test_react_graph_default():
    """Default pipeline (no env set) builds a react graph with intent_classify node."""
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ.pop("ORCHESTRATOR_PIPELINE", None)

    import src.graph.builder as builder_mod
    import src.core.checkpoint as checkpoint_mod

    original_get_saver = checkpoint_mod.get_saver
    checkpoint_mod.get_saver = AsyncMock(side_effect=Exception("no saver"))
    try:
        graph = await builder_mod.build_agent_graph()
    finally:
        checkpoint_mod.get_saver = original_get_saver

    assert graph is not None
    node_names = set(graph.get_graph().nodes.keys())
    assert "intent_classify" in node_names
    assert "reasoning" in node_names


@pytest.mark.anyio
async def test_multi_agent_graph_when_env_set():
    """ORCHESTRATOR_PIPELINE=multi_agent builds planner/executor/critic graph."""
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["ORCHESTRATOR_PIPELINE"] = "multi_agent"

    import src.graph.builder as builder_mod
    import src.core.checkpoint as checkpoint_mod

    original_get_saver = checkpoint_mod.get_saver
    checkpoint_mod.get_saver = AsyncMock(side_effect=Exception("no saver"))
    try:
        graph = await builder_mod.build_agent_graph()
    finally:
        checkpoint_mod.get_saver = original_get_saver
        os.environ.pop("ORCHESTRATOR_PIPELINE", None)

    assert graph is not None
    node_names = set(graph.get_graph().nodes.keys())
    assert "planner" in node_names
    assert "executor" in node_names
    assert "critic" in node_names


# ---------------------------------------------------------------------------
# _try_parse_json helper
# ---------------------------------------------------------------------------

class TestTryParseJson:
    def test_plain_json(self):
        from src.graph.nodes import _try_parse_json
        result = _try_parse_json('{"verdict": "approved", "reason": "ok"}')
        assert result == {"verdict": "approved", "reason": "ok"}

    def test_fenced_json(self):
        from src.graph.nodes import _try_parse_json
        text = '```json\n{"intent": "test", "steps": []}\n```'
        result = _try_parse_json(text)
        assert result == {"intent": "test", "steps": []}

    def test_invalid_returns_none(self):
        from src.graph.nodes import _try_parse_json
        result = _try_parse_json("not json at all")
        assert result is None


# ---------------------------------------------------------------------------
# make_planner_node tests
# ---------------------------------------------------------------------------

class TestPlannerNode:
    @pytest.mark.anyio
    async def test_planner_returns_plan_when_json(self):
        from src.graph.nodes import make_planner_node
        plan_json = '{"intent": "check status", "steps": [{"order": 1, "description": "query", "tool": "get_status", "rationale": "need data"}]}'
        ai_msg = AIMessage(content=plan_json)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)

        node = make_planner_node(mock_model)
        state = {
            "messages": [HumanMessage(content="check machine status")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "plan": None,
            "revision_count": 0,
            "final_answer": None,
        }
        result = await node(state)
        assert result["plan"] is not None
        assert result["plan"]["intent"] == "check status"
        assert len(result["plan"]["steps"]) == 1

    @pytest.mark.anyio
    async def test_planner_plan_none_on_non_json(self):
        from src.graph.nodes import make_planner_node
        ai_msg = AIMessage(content="I will plan something")
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)

        node = make_planner_node(mock_model)
        state = {
            "messages": [HumanMessage(content="do something")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "plan": None,
            "revision_count": 0,
            "final_answer": None,
        }
        result = await node(state)
        assert result["plan"] is None

    @pytest.mark.anyio
    async def test_planner_sync_fallback(self):
        from src.graph.nodes import make_planner_node
        ai_msg = AIMessage(content='{"intent": "x", "steps": []}')
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=NotImplementedError)
        mock_model.invoke = MagicMock(return_value=ai_msg)

        node = make_planner_node(mock_model)
        state = {
            "messages": [HumanMessage(content="hi")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "plan": None,
            "revision_count": 0,
            "final_answer": None,
        }
        result = await node(state)
        assert result["plan"]["intent"] == "x"


# ---------------------------------------------------------------------------
# make_executor_node tests
# ---------------------------------------------------------------------------

class TestExecutorNode:
    @pytest.mark.anyio
    async def test_executor_returns_message(self):
        from src.graph.nodes import make_executor_node
        ai_msg = AIMessage(content="Final Answer: done")
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)
        mock_model.bind_tools = MagicMock(return_value=mock_model)

        node = make_executor_node(mock_model, [])
        state = {
            "messages": [HumanMessage(content="execute plan")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "plan": {"intent": "do x", "steps": []},
            "revision_count": 0,
            "final_answer": None,
        }
        result = await node(state)
        assert result["messages"] == [ai_msg]

    @pytest.mark.anyio
    async def test_executor_sync_fallback(self):
        from src.graph.nodes import make_executor_node
        ai_msg = AIMessage(content="sync answer")
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=NotImplementedError)
        mock_model.invoke = MagicMock(return_value=ai_msg)

        node = make_executor_node(mock_model, [])
        state = {
            "messages": [HumanMessage(content="go")],
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "plan": None,
            "revision_count": 0,
            "final_answer": None,
        }
        result = await node(state)
        assert result["messages"] == [ai_msg]


# ---------------------------------------------------------------------------
# make_critic_node tests
# ---------------------------------------------------------------------------

class TestCriticNode:
    def _make_state(self, extra_msgs=None, revision_count=0):
        msgs = [HumanMessage(content="request"), AIMessage(content="executor answer")]
        if extra_msgs:
            msgs += extra_msgs
        return {
            "messages": msgs,
            "tools_used": [],
            "session_id": "s1",
            "trace_id": "t1",
            "plan": None,
            "revision_count": revision_count,
            "final_answer": None,
        }

    @pytest.mark.anyio
    async def test_critic_approved_sets_final_answer(self):
        from src.graph.nodes import make_critic_node
        verdict_json = '{"verdict": "approved", "reason": "looks good"}'
        ai_msg = AIMessage(content=verdict_json)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)

        node = make_critic_node(mock_model)
        state = self._make_state()
        result = await node(state)
        assert result["final_answer"] == "executor answer"
        assert "revision_count" not in result

    @pytest.mark.anyio
    async def test_critic_revision_needed_increments_count(self):
        from src.graph.nodes import make_critic_node
        verdict_json = '{"verdict": "revision_needed", "reason": "incomplete", "revisions": ["add detail"]}'
        ai_msg = AIMessage(content=verdict_json)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)

        node = make_critic_node(mock_model)
        state = self._make_state(revision_count=0)
        result = await node(state)
        assert result["revision_count"] == 1
        assert "final_answer" not in result

    @pytest.mark.anyio
    async def test_critic_non_json_increments_count(self):
        from src.graph.nodes import make_critic_node
        ai_msg = AIMessage(content="something went wrong, needs revision")
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=ai_msg)

        node = make_critic_node(mock_model)
        state = self._make_state(revision_count=1)
        result = await node(state)
        assert result["revision_count"] == 2


# ---------------------------------------------------------------------------
# critic_routing tests
# ---------------------------------------------------------------------------

class TestCriticRouting:
    def test_routes_to_end_when_final_answer(self):
        from src.graph.nodes import critic_routing
        state = {"messages": [], "tools_used": [], "session_id": "", "trace_id": "",
                 "plan": None, "revision_count": 0, "final_answer": "done"}
        assert critic_routing(state) == "end"

    def test_routes_to_end_when_max_revisions(self):
        from src.graph.nodes import critic_routing
        state = {"messages": [], "tools_used": [], "session_id": "", "trace_id": "",
                 "plan": None, "revision_count": 2, "final_answer": None}
        assert critic_routing(state) == "end"

    def test_routes_to_executor_when_revision_needed(self):
        from src.graph.nodes import critic_routing
        state = {"messages": [], "tools_used": [], "session_id": "", "trace_id": "",
                 "plan": None, "revision_count": 1, "final_answer": None}
        assert critic_routing(state) == "executor"

    def test_routes_to_executor_when_zero_revisions(self):
        from src.graph.nodes import critic_routing
        state = {"messages": [], "tools_used": [], "session_id": "", "trace_id": "",
                 "plan": None, "revision_count": 0, "final_answer": None}
        assert critic_routing(state) == "executor"


# ---------------------------------------------------------------------------
# Integration: planner → executor → critic → END (multi_agent mode)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_build_agent_graph_3node_structure():
    """3-node multi_agent graph builds correctly with planner/executor/critic nodes."""
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["ORCHESTRATOR_PIPELINE"] = "multi_agent"

    import src.graph.builder as builder_mod
    import src.core.checkpoint as checkpoint_mod

    original_get_saver = checkpoint_mod.get_saver
    checkpoint_mod.get_saver = AsyncMock(side_effect=Exception("no saver"))
    try:
        graph = await builder_mod.build_agent_graph()
    finally:
        checkpoint_mod.get_saver = original_get_saver
        os.environ.pop("ORCHESTRATOR_PIPELINE", None)

    assert graph is not None
    node_names = set(graph.get_graph().nodes.keys())
    assert "planner" in node_names
    assert "executor" in node_names
    assert "critic" in node_names
