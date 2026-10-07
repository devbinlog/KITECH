---
template: plan-plus
feature: mock-tool-calling-demo
date: 2026-05-03
author: xession
project: agents-workspace
phase: plan
---

# mock-tool-calling-demo — Plan-Plus

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | Mock LLM이 fixed text만 반환해서 LangGraph의 ToolNode / streaming / SqliteSaver 인프라가 활용되지 않음. 사용자에게 진짜 LLM 없이도 tool calling 동작을 보여주지 못함. 향후 SLM(Llama 3.2/Qwen 2.5) 도입 시 동일한 코드 path 보장 필요. |
| **Solution** | Mock LLM을 nl-router /classify 호출 → intent → tool 매핑 → AIMessage(tool_calls=[…]) 반환하도록 업그레이드. LangGraph ToolNode가 실제 호출 + ToolMessage wrap. Mock이 결과 자연어 요약. nl-router intent + intent→tool 매핑 + tool subset selection은 SLM 모드에서도 영구 재사용. Default pipeline은 단순 ReAct (Mock/SLM 친화), 강한 LLM에서만 ORCHESTRATOR_PIPELINE=multi_agent 옵션. |
| **Function / UX / Effect** | • Mock 모드에서 "오늘 생산 현황 보여줘" → cell-mes__get_equipment_utilization 자동 호출 → "오늘 설비 가동률은 66.67% 입니다" 답변<br>• 12 internal services / 37 tools 중 intent 기반 5-7 subset만 model에 bind (SLM context 부담 감소)<br>• Mock ↔ SLM(Ollama) ↔ 강한 LLM 전환은 env 1줄<br>• Multi-agent (planner/executor/critic) 보존하되 ORCHESTRATOR_PIPELINE=multi_agent 일 때만 활성<br>• Mock에서도 LangGraph ToolNode/SqliteSaver/astream 모두 작동 (실제 인프라 데모) |
| **Core Value** | **Mock으로 SLM의 모든 기능을 시연**. SLM 도입 시 코드 변경 0 — 모델만 swap. nl-router intent classify를 영구 보조 인프라로 격상해 SLM의 약점(complex reasoning) 보강. JSON 파싱 신뢰도 낮은 SLM 환경에서 multi-agent 회피 + 단순 ReAct로 latency/정확도 양립. |

## Context Anchor

| Key | Value |
|---|---|
| **WHY** | Mock 모드에서 LangGraph 인프라 전체를 시연하기 위함 + SLM 최종 목표에 대비한 코드 path 통일 |
| **WHO** | 데모 시 — admin, 평가자. 운영 시 — 자연어 질의 사용자. dev — env로 모드 전환 |
| **RISK** | nl-router classify 실패 시 fallback / intent 매핑 누락 시 동작 / SLM JSON 신뢰도 / Multi-agent latency 누적 |
| **SUCCESS** | Mock에서 "오늘 생산 현황" → 실제 cell-mes endpoint 호출 + 결과 자연어 요약 / SLM 모드 (Ollama) 가동 시 동일 path / multi-agent env로 활성 가능 |
| **SCOPE** | core/intent_router.py + config/intent_tool_mapping.yaml + core/system_prompts.py + Mock LLM 업그레이드 + graph/ 단일 ReAct + env-driven multi-agent toggle. **OOS: 실제 SLM 모델 다운로드/벤치마크, structured output (Pydantic enforcement), Web UI tool call 시각화 강화** |

---

## 1. User Intent Discovery

### Q1. Mock 수준
선택: **C + LangGraph 같이 활용** (nl-router /classify + LangGraph ToolNode)

### Q2. 데모 흐름
선택: **단순 ReAct** (planner/critic 스킵)

### Q3 (사용자 추가 질문) — Multi-agent 가능 여부
- 답변: SLM에서도 가능하나 **JSON 신뢰도 + latency + 오류 누적 3 트레이드오프**
- 결정: **env-driven toggle** — default react, 강한 LLM 시 multi_agent 옵션

## 2. Alternatives Explored

| 옵션 | 선택? |
|---|:-:|
| A: 간단 키워드 3-5 패턴 | ❌ 너무 단순 |
| B: 구조화 키워드 매칭 | ❌ nl-router 재발명 |
| **C: nl-router /classify 활용 + LangGraph** | ✅ |
| D: 시나리오 단일 스크립트 | ❌ 데모 부적합 |

| Pipeline | 선택? |
|---|:-:|
| Mock 전용 ReAct | ❌ Mock-only 의미 적음 |
| Multi-agent 항상 | ❌ SLM에 부담 |
| **단순 ReAct default + multi-agent env 옵션** | ✅ |

## 3. YAGNI Review

### Included (Must)
1. core/intent_router.py — nl-router HTTP client + intent → tool mapping loader
2. config/intent_tool_mapping.yaml — intent → tool name + args extraction rules
3. core/system_prompts.py — intent별 system prompt 템플릿 + few-shot
4. core/llm_provider.py 업그레이드 — Mock LLM이 intent_router 활용
5. graph/ 단일 ReAct 통일 — multi-agent는 env-driven plugin
6. graph/state.py — `active_tools: List[str]` 필드 추가
7. tests — intent_router / llm_provider mock+SLM / graph 단일 ReAct

### Out of Scope
- 실제 Ollama 모델 다운로드 (사용자가 호스트에서)
- 실제 SLM end-to-end 벤치마크 (다음 사이클)
- Pydantic structured output 강제
- Web UI tool call 시각화 강화
- nl-router의 12 skill 외 신규 intent 추가
- intent confidence < threshold 시 재질의 UI

## 4. Brainstorming Log

| Phase | 결정 |
|---|---|
| Phase 0 | Mock LLM의 fixed text 한계 확인 + LangGraph 인프라 활용 못하는 상황 |
| Phase 1-Q1 | C + LangGraph 결합 |
| Phase 1-Q2 | 단순 ReAct |
| Phase 1-Q3 | Multi-agent SLM 트레이드오프 — env-driven toggle |
| Phase 2 | 단일 ReAct default + multi-agent 옵션 보존 |
| Phase 3 | YAGNI: nl-router 재활용, system_prompts 신규, tool subset selection |

## 5. Architecture & Module Map

### 신규 파일

```
agents/agent-orchestrator/
├── src/
│   ├── core/
│   │   ├── intent_router.py          # 신규 — nl-router HTTP + mapping loader
│   │   ├── system_prompts.py         # 신규 — intent별 prompt template + few-shot
│   │   ├── llm_provider.py           # 수정 — _MockChatModel 업그레이드
│   ├── graph/
│   │   ├── state.py                  # 수정 — active_tools 필드
│   │   ├── nodes.py                  # 수정 — intent_classify_node 신규
│   │   ├── builder.py                # 수정 — env로 react vs multi_agent
│   ├── config/
│   │   └── intent_tool_mapping.yaml  # 신규 (또는 root config/)
└── tests/
    ├── test_intent_router.py         # 신규
    ├── test_llm_provider.py          # 수정
    └── test_graph.py                 # 수정
```

### 데이터 흐름

```
[User] "오늘 생산 현황 보여줘"
   │
   ▼ WS /ws/chat
agent-orchestrator
   │
   ▼ Mock LLM ainvoke (1차)
   │ ① intent_router.classify(message) — HTTP nl-router/classify
   │   → {intent: "production_status", entities: {date: "2026-05-03"}}
   │ ② intent → tool 매핑 (yaml)
   │   → tool: cell-mes__get_equipment_utilization, args: {date: "2026-05-03"}
   │ ③ AIMessage(content="", tool_calls=[{id, name, args}])
   │
   ▼ LangGraph builder (단순 ReAct)
   reasoning_node
   ↓
   should_continue: tool_calls 있음 → tool_call
   ↓
   ToolNode 실행 (StructuredTool wrapping)
   → HTTP POST cell-mes:8000/api/v1/analytics/equipment-utilization
   → 200 {utilization_rate: 66.67, ...}
   → ToolMessage(content=json, tool_call_id=...)
   ↓
   reasoning_node (2차)
   ↓
   ▼ Mock LLM ainvoke (2차 — last message가 ToolMessage)
   │ ④ tool result 받음 → 자연어 요약 (system_prompts)
   │   → AIMessage(content="오늘 설비 가동률은 66.67% 입니다.", tool_calls=[])
   │
   ▼ should_continue: tool_calls 없음 → END
   │
   ▼ astream chunks → WebSocket → User
[User] 답변
```

### Multi-agent (env-driven, 옵션)

```python
# graph/builder.py
pipeline = os.getenv("ORCHESTRATOR_PIPELINE", "react")
if pipeline == "multi_agent":
    return build_planner_executor_critic_graph(model, tools)
else:
    return build_react_graph(model, tools)  # default — SLM/Mock 친화
```

## 6. Implementation Order

```
1. Sub-agent A (병렬): NEW files — intent_router + yaml + system_prompts + tests
2. Sub-agent B (병렬): MODIFY files — llm_provider + graph/* + tests
   (A의 인터페이스는 사전 명시 — 충돌 0)
3. Main: docker compose build + 가동 + 사용자 시나리오 검증
4. Commit
```

## 7. Success Criteria

| # | Criteria |
|---|---|
| 1 | Mock 모드에서 "오늘 생산 현황" → cell-mes__get_equipment_utilization 호출 |
| 2 | "설비 상태" → cell-mes__list_equipments 호출 |
| 3 | "작업지시 목록" → cell-mes__list_work_orders 호출 |
| 4 | tool 결과 자연어 요약 (한국어) |
| 5 | unknown intent → "의도 파악 못함" 안내 응답 |
| 6 | nl-router 다운 시 graceful (fallback to default tools or "LLM 미설정") |
| 7 | ORCHESTRATOR_PIPELINE=multi_agent 시 기존 planner/executor/critic 동작 |
| 8 | LLM_PROVIDER=ollama + LLM_MODEL=qwen2.5:7b-instruct 시 동일 path 동작 (호스트 ollama serve 필요) |
| 9 | pytest 회귀 0 + 신규 테스트 PASS |

## 8. Risk

| 위험 | 완화 |
|---|---|
| nl-router /classify 실패 | try/except → fallback "unknown" intent |
| intent 매핑 누락 | yaml에 default fallback tool 정의 |
| SLM JSON 파싱 실패 | Mock에서는 dict로 직접 만듦 / SLM은 별도 사이클에서 with_structured_output |
| Multi-agent backward compat | ORCHESTRATOR_PIPELINE 미설정 시 기존 multi-agent 동작 보장 (또는 react default) — 결정: react default, multi_agent 명시적 opt-in |
| frontend rebuild 필요 여부 | frontend는 변경 0 (chunk 형식 동일) |

## 9. Out of Scope (재확인)

- 실 SLM 다운로드 (사용자 환경)
- Pydantic structured output 강제
- intent confidence threshold UI
- Markdown 렌더링
- C 그룹 audit 보안 패치 (별도 사이클)
