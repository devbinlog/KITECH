"""system_prompts.py — Intent-aware system prompt templates + result summary templates."""

# Intent별 system prompt — SLM에 줄 때 동적 prepend
SYSTEM_PROMPT_BASE = """당신은 제조 MES 시스템의 자연어 어시스턴트입니다.
사용자의 질문을 받아 적절한 tool을 호출해 답변합니다.
한국어로 간결하게 답변하세요. 숫자는 그대로 인용하세요."""

INTENT_HINTS = {
    "production_status": "사용자가 생산 현황을 묻습니다. 설비 가동률 또는 작업지시 목록을 조회하세요.",
    "equipment_status": "사용자가 설비 상태를 묻습니다. list_equipments tool을 사용하세요.",
    "work_order_list": "사용자가 작업지시 목록을 묻습니다. list_work_orders 사용.",
    "spc_query": "사용자가 SPC/품질을 묻습니다. list_inspection_results 사용.",
    "ncr_query": "사용자가 NCR을 묻습니다. list_ncrs 사용.",
    "schedule_solve": "사용자가 스케줄링을 요청합니다. solve_schedule 사용.",
    "schedule_view": "사용자가 스케줄 현황을 묻습니다. list_solvers 사용.",
    "alarm_query": "사용자가 알람을 묻습니다. list_alarms 사용.",
    "gcode_parse": "사용자가 G-code 분석을 요청합니다. parse_gcode 사용.",
    "cam_analyze": "사용자가 CAM 사이클 타임을 묻습니다. analyze_cam_path 사용.",
    "step_pmi": "사용자가 STEP 파일 PMI를 묻습니다. extract_pmi 사용.",
    "unknown": "사용자 의도가 명확하지 않습니다. 정중히 다시 질문해 달라고 안내하세요.",
}


def build_system_prompt(intent: str, tool_names: list) -> str:
    """Compose system prompt: base + intent hint + active tools list."""
    hint = INTENT_HINTS.get(intent, "")
    tool_lines = "\n".join(f"- {name}" for name in tool_names)
    return f"""{SYSTEM_PROMPT_BASE}

[현재 의도]
{hint}

[사용 가능한 tools]
{tool_lines}
"""


# 결과 요약 템플릿 — Mock LLM이 사용 (Real LLM은 자체 자연어 생성)
RESULT_SUMMARY_TEMPLATES = {
    "production_status": "오늘 설비 가동률은 {result[utilization_rate]}% 입니다.",
    "equipment_status": "설비 {result[total]}대 중 {result[running]}대 가동 중, {result[idle]}대 대기 중입니다.",
    "work_order_list": "작업지시가 {result[total]}건 조회되었습니다.",
    "spc_query": "검사 결과 {result[total]}건이 조회되었습니다.",
    "ncr_query": "NCR이 {result[total]}건 등록되어 있습니다.",
    "alarm_query": "알람이 {result[total]}건 발생했습니다.",
}
