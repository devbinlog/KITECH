"""test_system_prompts.py — Tests for system_prompts module."""
import pytest


# ---------------------------------------------------------------------------
# INTENT_HINTS completeness
# ---------------------------------------------------------------------------

EXPECTED_INTENT_KEYS = [
    "production_status",
    "equipment_status",
    "work_order_list",
    "spc_query",
    "ncr_query",
    "schedule_solve",
    "schedule_view",
    "alarm_query",
    "gcode_parse",
    "cam_analyze",
    "step_pmi",
    "unknown",
]


def test_intent_hints_all_keys_present():
    """INTENT_HINTS must contain all 12 expected intent keys."""
    from src.core.system_prompts import INTENT_HINTS

    for key in EXPECTED_INTENT_KEYS:
        assert key in INTENT_HINTS, f"Missing intent key: {key}"


def test_intent_hints_all_values_nonempty():
    """All INTENT_HINTS values must be non-empty strings."""
    from src.core.system_prompts import INTENT_HINTS

    for key, value in INTENT_HINTS.items():
        assert isinstance(value, str) and value.strip(), f"Empty hint for intent: {key}"


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------

def test_build_system_prompt_contains_base():
    """build_system_prompt includes the base prompt text."""
    from src.core.system_prompts import build_system_prompt, SYSTEM_PROMPT_BASE

    prompt = build_system_prompt("production_status", ["cell-mes__get_equipment_utilization"])
    assert SYSTEM_PROMPT_BASE in prompt


def test_build_system_prompt_contains_intent_hint():
    """build_system_prompt includes the intent-specific hint."""
    from src.core.system_prompts import build_system_prompt, INTENT_HINTS

    intent = "equipment_status"
    prompt = build_system_prompt(intent, ["cell-mes__list_equipments"])
    assert INTENT_HINTS[intent] in prompt


def test_build_system_prompt_contains_all_tools():
    """build_system_prompt lists all provided tool names."""
    from src.core.system_prompts import build_system_prompt

    tools = ["cell-mes__list_work_orders", "cell-mes__list_equipments", "cell-mes__list_alarms"]
    prompt = build_system_prompt("work_order_list", tools)

    for tool in tools:
        assert tool in prompt


def test_build_system_prompt_unknown_intent_graceful():
    """build_system_prompt handles intents not in INTENT_HINTS without error."""
    from src.core.system_prompts import build_system_prompt

    # Should not raise even for unmapped intent
    prompt = build_system_prompt("totally_new_intent", ["some_tool"])
    assert "some_tool" in prompt


def test_build_system_prompt_empty_tools():
    """build_system_prompt works with empty tool list."""
    from src.core.system_prompts import build_system_prompt

    prompt = build_system_prompt("unknown", [])
    assert "[사용 가능한 tools]" in prompt


# ---------------------------------------------------------------------------
# RESULT_SUMMARY_TEMPLATES
# ---------------------------------------------------------------------------

TEMPLATE_TEST_CASES = [
    ("production_status", {"utilization_rate": 87.5}, "87.5"),
    ("equipment_status", {"total": 10, "running": 7, "idle": 3}, "10"),
    ("work_order_list", {"total": 42}, "42"),
    ("spc_query", {"total": 15}, "15"),
    ("ncr_query", {"total": 3}, "3"),
    ("alarm_query", {"total": 5}, "5"),
]


@pytest.mark.parametrize("intent,result_data,expected_substr", TEMPLATE_TEST_CASES)
def test_result_summary_template_formats(intent, result_data, expected_substr):
    """RESULT_SUMMARY_TEMPLATES format strings render without error."""
    from src.core.system_prompts import RESULT_SUMMARY_TEMPLATES

    assert intent in RESULT_SUMMARY_TEMPLATES, f"Template missing for intent: {intent}"
    template = RESULT_SUMMARY_TEMPLATES[intent]
    rendered = template.format(result=result_data, tool="some_tool")
    assert expected_substr in rendered
