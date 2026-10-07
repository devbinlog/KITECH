# n8n YAML Editor — Frontend 통합

| 항목 | 값 |
|---|---|
| 생성일 | 2026-05-01 |
| 작성 방식 | `/bkit:plan-plus` (Brainstorming-Enhanced Planning) |
| 다음 단계 | `/pdca design n8n-yaml-editor-integration` |
| 예상 공수 | **40–57일 (약 8–12주)** |

---

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | 시나리오 마스터의 YAML 파일을 편집하려면 외부 n8n editor를 띄우거나 텍스트 에디터로 직접 손봐야 함. iframe 임베드는 디자인 통합이 안 되고, 텍스트 편집은 비주얼·검증·실행 모두 빈약. |
| **Solution** | n8n editor의 편집 UX를 React/Next.js 네이티브로 포팅하되, **도메인은 3개 노드 타입**(`manualTrigger`/`scenarioConfig`/`scenarioStep`)으로 좁힘. React Flow 기반 캔버스 + Monaco 표현식/JSON 에디터 + n8n REST 연동 Test Execution. |
| **Function / UX / Effect** | • 시나리오 페이지에서 ✏️ Edit2 → 풀페이지 캔버스 에디터<br>• n8n 시각 언어(노드 카드/연결 곡선/Mini-map/Tidy up) 그대로 + 프로젝트 Tailwind 디자인 시스템과 일관<br>• 편집 풀 패리티: Undo/Redo, Copy/Paste, Multi-select, Search palette, Keyboard shortcuts, 인라인 validation, autosave<br>• Expression autocomplete + Variable Explorer<br>• Sticky notes로 워크플로우 주석<br>• Test Execution: n8n REST에 워크플로우 실행 → 노드별 status/input/output 인라인 표시 |
| **Core Value** | 시나리오 편집을 **외부 도구 없이 MES 안에서 끝내는 통합 경험**. n8n editor의 풍부한 편집 UX를 보존하면서 디자인·라이선스·컨테이너 의존성을 우리 통제 하에 둠. |

---

## 1. User Intent Discovery (Phase 1)

| 질문 | 답변 |
|---|---|
| **Q1. 통합 방식** | iframe 임베드 X, n8n editor를 React/Next.js로 포팅 (변환 통합) |
| **Q2. 접근 방식** | Approach A — React Flow + 도메인 3개 노드 |
| **Q3. 우선순위 재조정** | "최소한의 작업"은 권고, **편집 기능 보존이 1순위** |

**Target users:** Cell-MES 운영자/엔지니어 (시나리오 마스터 편집자).
**Success criteria:**
1. 시나리오 페이지에서 클릭 한 번에 시각 에디터 진입
2. 외부 n8n editor 없이 시나리오 YAML 편집·저장 완결
3. 저장된 YAML을 기존 n8n 컨테이너로 export/import 시 100% 호환
4. n8n editor에서 가능한 편집 동작이 V1 에디터에서도 모두 가능 (실행 포함)

---

## 2. Alternatives Explored (Phase 2)

| 안 | 요약 | 결과 |
|---|---|---|
| **A. React Flow + 도메인 3개 노드** | n8n 시각 언어 보존, 라이선스 안전, 기존 컨버터 재활용 | ✅ **채택** |
| B. Vue editor를 React 안에 마운트 (veaury) | 코드 거의 안 씀, but 디자인 통일 불가 + 번들 폭탄 | ❌ |
| C. n8n editor 전체 React 풀 포팅 | 완벽 보존이지만 2-3개월 + 라이선스 리스크 + 95% 코드 낭비 | ❌ |
| 보조: 단순 Monaco YAML 에디터 | 가장 미니멀, but "n8n 통합" 요구 미충족 | ❌ |

---

## 3. YAGNI Review (Phase 3)

### V1 IN — 베이스라인 (협상 불가)
- React Flow 캔버스 (pan/zoom/드래그/연결)
- 3개 도메인 노드 카드 (manualTrigger / scenarioConfig / scenarioStep) — n8n 시각 스타일
- 우측 ParameterPanel (id/name/action/acquire/routing/paramsJson)
- Add Step / Delete / Save / Cancel
- YAML 로드 (`/yaml-to-n8n`) / YAML 저장 (`/n8n-to-yaml` + 신규 PUT)
- 시나리오 페이지 진입점 (`/master/scenarios/[id]/edit`)
- 한글 라벨 + Tailwind 디자인 통합
- Loading / Error / Dirty-state 경고 / 기존 LoadingState/ErrorBoundary 재활용

### V1 IN — 추가 (사용자 결정)
- 멀티 셀렉트 / 박스 셀렉트 / Bulk 삭제
- 노드 Copy / Paste / Cut / Duplicate
- Undo / Redo (히스토리 ~50)
- Auto-layout / Tidy up (dagre 클라이언트)
- Mini-map
- Node Search Palette (Ctrl+K)
- Expression autocomplete + Variable Explorer
- 인라인 Validation badge
- Autosave (debounced 2s) + Save status indicator
- Export / Import n8n JSON
- YAML 미리보기 모달
- Keyboard shortcuts (Cmd+S/Z/Y/C/V/X/D/A/K, Delete, Esc, Space-drag, Ctrl+0/=/-)
- Right-click context menu
- **Sticky notes (워크플로우 주석)**
- **Test Execution (n8n REST 연동, 노드별 status/input/output, Pin output, Cancel)**

### V2+ OUT — 미루기
- Routing 조건식 GUI 빌더 (V1: textarea)
- 버전 히스토리 / 워크플로우 audit log
- Multi-tab workflows (여러 시나리오 동시)
- 다크 모드
- 모바일 / 터치 최적화
- Workflow tags / categorization

---

## 4. Brainstorming Log (Phase 1–4 핵심 결정)

| # | 결정 | 근거 |
|---|---|---|
| 1 | iframe 임베드 거부 | 디자인 통합 / 보안 설정 / Vue↔React 격리 모두 단점 |
| 2 | Vue 마운트(veaury) 거부 | 본질적으로 iframe과 동일, 디자인 통일 불가 |
| 3 | 도메인 3개 노드만 지원 | 우리 시나리오 YAML이 사용하는 노드 타입은 3개 한정 |
| 4 | React Flow 채택 (n8n의 @vue-flow와 동일 author @xyflow) | 시각 언어 호환 + 라이선스 안전 |
| 5 | 기존 `scenario_converter.py` 재활용 | 양방향 컨버터 이미 검증됨, 신규 변환 로직 작성 회피 |
| 6 | "최소 작업" 권고 → 기능 보존 우선 전환 | 사용자 명시 |
| 7 | Test Execution V1 포함 | n8n editor의 핵심 UX. 백엔드 n8n_runner + 폴링 +7-10일 감수 |
| 8 | Sticky notes V1 포함, YAML 스키마 확장 (안 a) | 사이드카 파일 대비 단일 파일 운영 단순 |
| 9 | Routing GUI 빌더 V2+ 보류 | textarea로 V1 충분. GUI 빌더는 별도 큰 기능 |

---

## 5. 배경 & 컨텍스트

- **이미 깔린 인프라 (V1 작업 시작 전 확인된 자산)**
  - n8n 컨테이너 :5678 (`agents/n8n-yaml/`, 커스텀 노드 `n8n-nodes-scenario` 포함)
  - 백엔드 `endpoints/converters.py` (yaml↔n8n JSON 양방향, 미커밋)
  - 시나리오 마스터 CRUD + Preview UI (`/master/scenarios`)
- **부족한 것**
  - 시나리오 행에 Edit 액션 없음
  - YAML 저장 PUT API 없음
  - 캔버스 기반 편집 UI 없음
- **제약 조건**
  - 라이선스: n8n Sustainable Use License → 시각 패턴 참조만, 코드 복붙 X
  - 호환성: 저장된 YAML이 기존 n8n 컨테이너에서 정상 실행되어야 함

---

## 6. 아키텍처

### 6-1 위치 / 라우팅
- 신규: `app/(main)/master/scenarios/[id]/edit/page.tsx` (Next.js App Router 다이내믹 라우트)
- 진입: 기존 `master/scenarios/page.tsx`에 `Edit2` 컬럼/액션 추가 → `router.push`
- 풀페이지 (모달 X) — 캔버스+사이드 패널 동시 렌더 필요

### 6-2 시각 언어 정책
- n8n editor 노드 카드/connection 곡선/캔버스 grid는 시각만 참조
- 컴포넌트는 프로젝트 Tailwind + 기존 디자인 시스템(statusColors 등)으로 작성

### 6-3 상태 관리
- 서버 상태: React Query (기존 컨벤션)
- 에디터 로컬 상태: React Flow `useNodesState`/`useEdgesState` + Zustand 3개 store
  - `useEditorStore` — selection, clipboard, dirty, errors
  - `useHistoryStore` — undo/redo 스택 (immer patch)
  - `useExecutionStore` — executionId, 노드별 상태, 실행 로그
- Dirty 추적: `beforeunload` + Next.js navigation guard

### 6-4 라이선스
- Sustainable Use License: SaaS 재판매 X, 시각 참조 OK, React Flow는 MIT
- 우리 제품을 n8n 호환 SaaS로 판매하지 않으므로 안전

---

## 7. 컴포넌트 구조 (~38 파일)

```
agents/cell-mes/frontend/components/scenario-editor/
├── ScenarioEditorPage.tsx
├── canvas/
│   ├── ScenarioCanvas.tsx       # React Flow 래퍼
│   ├── MiniMap.tsx
│   ├── Background.tsx
│   ├── Controls.tsx             # zoom + tidy up
│   └── ConnectionLine.tsx
├── nodes/
│   ├── ManualTriggerNode.tsx
│   ├── ScenarioConfigNode.tsx
│   ├── ScenarioStepNode.tsx
│   ├── StickyNoteNode.tsx
│   ├── NodeBadge.tsx
│   ├── NodeStatusIndicator.tsx  # 실행 상태 오버레이
│   └── NodeContextMenu.tsx
├── edges/
│   └── RoutingEdge.tsx          # when 라벨
├── panels/
│   ├── ParameterPanel.tsx
│   ├── StepParameterForm.tsx
│   ├── ConfigParameterForm.tsx
│   ├── StickyParameterForm.tsx
│   ├── RoutingRulesEditor.tsx   # textarea (V1)
│   ├── AcquireRolesEditor.tsx
│   ├── NodeSearchPalette.tsx    # Ctrl+K
│   ├── VariableExplorer.tsx
│   └── ExecutionPanel.tsx       # 하단 실행 결과
├── toolbar/
│   ├── EditorToolbar.tsx
│   ├── SaveStatusIndicator.tsx
│   ├── RunStatusIndicator.tsx
│   └── KeyboardShortcutsHelp.tsx
├── execution/
│   ├── useTestRunner.ts
│   ├── ExecutionDataViewer.tsx
│   ├── PinOutputControl.tsx
│   └── runStateMachine.ts
├── expression/
│   ├── ExpressionInput.tsx       # Monaco
│   ├── useExpressionSuggestions.ts
│   └── expressionFunctions.ts
├── store/
│   ├── useEditorStore.ts
│   ├── useHistoryStore.ts
│   └── useExecutionStore.ts
├── hooks/
│   ├── useScenarioLoader.ts
│   ├── useScenarioSaver.ts
│   ├── useKeyboardShortcuts.ts
│   ├── useAutoSave.ts
│   ├── useClipboard.ts
│   └── useUndoRedo.ts
└── utils/
    ├── validate.ts
    ├── nodeFactory.ts
    ├── tidyUp.ts                # dagre
    ├── n8nJsonIO.ts
    ├── yamlPreview.ts
    └── stickyNoteIO.ts
```

---

## 8. 백엔드 API (cell-mes)

| 엔드포인트 | 신규/수정 | 비고 |
|---|---|---|
| `GET  /masters/scenarios/{id}/content` | 기존 | YAML 텍스트 |
| `POST /converters/yaml-to-n8n` | **수정** | sticky note 노드 추가 처리 |
| `POST /converters/n8n-to-yaml` | **수정** | sticky note 노드 추출 |
| `PUT  /masters/scenarios/{id}/content` | 🆕 | YAML 저장 (safe_load 검증 + .bak 1세대 백업) |
| `GET  /masters/scenarios/actions` | 🆕 | Action 카탈로그 (cache-first) |
| `POST /scenarios/{id}/test-runs` | 🆕 | n8n REST에 워크플로우 실행 트리거 |
| `GET  /scenarios/test-runs/{execution_id}` | 🆕 | 폴링: 노드별 status/input/output/error |
| `POST /scenarios/test-runs/{execution_id}/cancel` | 🆕 | 실행 취소 |

**신규 모듈**: `agents/cell-mes/src/app/services/n8n_runner.py`
- n8n REST API 클라이언트 (`http://n8n:5678/rest/...`)
- 인증: `N8N_API_KEY` 환경변수
- 임시 워크플로우 실행 + 폴링 + 결과 정제
- 실행 상태 인메모리 캐시 (V1)

**docker-compose.yml 수정**: n8n 환경변수 추가 (`N8N_API_KEY`, `N8N_PUBLIC_API_DISABLED=false`), cell-mes에 `N8N_BASE_URL`/`N8N_API_KEY` 주입.

---

## 9. 데이터 흐름 (요약)

| 시나리오 | 호출 순서 |
|---|---|
| **로드** | router → GET scenario meta → GET content → GET actions → POST yaml-to-n8n → setNodes/Edges → tidyUp(fallback) |
| **편집** | onChange → history push → markDirty → validate → autosave 디바운스 |
| **저장** | n8nJsonIO 직렬화 → POST n8n-to-yaml → PUT content → toast |
| **실행** | (autosave) → POST test-runs → 폴링 1s × 120s max → ExecutionStore 갱신 → 노드 오버레이 |
| **Sticky** | nodeFactory.createSticky → history push → 저장 시 yaml `notes[]` 배열로 매핑 |
| **Undo/Redo** | useHistoryStore.undo/redo → immer patch 역적용 |
| **Cancel** | dirty? confirm dialog : router.back |
| **Validation** | 매 변경 시 validate.ts → setErrors → NodeBadge/ParameterPanel 갱신 |

---

## 10. 의존성

| 패키지 | 용도 |
|---|---|
| `reactflow` | 캔버스 |
| `@monaco-editor/react` | paramsJson + Expression Monaco |
| `dagre` | tidy up 자동 레이아웃 |
| `zustand` | 에디터/히스토리/실행 store |
| `immer` | undo/redo immutable |
| `nanoid` | 신규 노드 ID |
| `react-markdown` | sticky note 마크다운 렌더 (선택) |

---

## 11. YAML 스키마 확장 (Sticky Notes)

기존 시나리오 YAML 루트에 `notes` 키 추가 (선택, 하위 호환):

```yaml
name: Cell-1 Production
desc: ...
assets:
  - id: M1
    name: Machine 1
notes:                              # ← 신규 (선택)
  - x: 100
    y: 200
    w: 240
    h: 180
    text: "FIXME: this branch needs review"
    color: yellow                   # yellow | blue | pink | green
steps:
  - id: S1
    ...
```

기존 파일은 `notes` 없으니 영향 없음. 외부 도구가 모르면 무시해도 OK.

---

## 12. Phasing & 공수

| 단계 | 일수 | 의존성 |
|---|---|---|
| 0. 셋업 (의존성 추가, 라우트 스캐폴드) | 1 | - |
| 1. 백엔드 PUT content + GET actions | 1-2 | - |
| 2. 컨버터 sticky note 처리 + YAML 스키마 확장 | 1-2 | 1 |
| 3. Canvas + 3개 노드 + 엣지 | 6-8 | 0 |
| 4. ParameterPanel + StepForm + Routing/Acquire | 5-7 | 3 |
| 5. Save / Autosave / Dirty guard / 미리보기 | 3-4 | 1, 4 |
| 6. Multi-select + Copy/Paste + Undo/Redo | 3-4 | 4 |
| 7. Auto-layout(dagre) + Mini-map + Validation badge | 2-3 | 3 |
| 8. Node Search Palette + Keyboard shortcuts | 2-3 | 4, 6 |
| 9. Expression autocomplete + Variable Explorer | 4-6 | 4 |
| 10. Sticky note (StickyNode + Form) | 2-3 | 2, 3 |
| 11. Export/Import n8n JSON | 1-2 | 5 |
| 12. **Test Execution** (n8n_runner + ExecutionPanel + Pin/Cancel) | 7-10 | 1, 4 |
| 13. QA / 통합 테스트 / 디자인 폴리싱 | 4-6 | all |
| **Total** | **42-60일 (≈8-12주)** | |

> 단계 1-2 백엔드 먼저 마무리, 그 다음 프론트는 3→4→5 순서로 작동 가능한 MVP를 만든 뒤 6, 7, ... 추가.

---

## 13. Acceptance Criteria

1. ✅ 기존 시나리오 YAML 파일을 에디터에 로드 → 캔버스에 정확히 표시
2. ✅ 노드 추가/편집/삭제 후 저장 → YAML 파일이 동등하게 업데이트
3. ✅ 저장된 YAML을 n8n editor(외부)에서 import → 정상 실행
4. ✅ n8n editor에서 export한 워크플로우 JSON을 우리 에디터에 import → 캔버스 정확히 렌더
5. ✅ Undo/Redo가 노드 추가/삭제/이동/파라미터 변경 모두에서 동작
6. ✅ 멀티 셀렉트 → Ctrl+C/V로 노드 복제 (ID 자동 유니크화)
7. ✅ paramsJson Monaco에서 `{{$` 입력 시 expression suggestion 표시
8. ✅ 검증 에러 있는 노드는 배지 표시, 저장 시 서버 거부 시 토스트
9. ✅ Sticky note 추가/편집/저장 → YAML `notes` 배열에 보존
10. ✅ Test Run 실행 → n8n에서 실행 → 노드별 success/error 상태 표시
11. ✅ Dirty 상태에서 페이지 이탈 시 경고
12. ✅ Autosave가 2초 디바운스로 동작, Save status indicator 갱신
13. ✅ Mini-map / Tidy up / Keyboard shortcuts 모두 동작

---

## 14. Risks & Mitigations

| 리스크 | 완화 |
|---|---|
| n8n REST API 인증 변경/버전 호환 | n8n 버전 핀고정 + n8n_runner를 thin client로 격리 |
| Test Execution이 길어질 때 폴링 만료 | max 120s 제한 + Cancel 가능, 길면 사용자가 외부 n8n에서 직접 실행 |
| Expression 표현식 호환성 | n8n 표현식 일부만 지원 (단순 `{{$json.x}}` 류). 미지원은 raw 텍스트로 보존 |
| YAML 스키마 변경(notes)이 외부 도구 깰 가능성 | `notes` 옵션 키, 기존 yaml_to_n8n에서만 사용. 미존재 시 무시 |
| 라이선스 (n8n Sustainable Use) | 코드 복붙 X, 시각 참조만, React Flow 단독 사용. SaaS 재판매 안 함 |
| Vue 의존성 잘못 끌고 옴 | n8n editor-ui 패키지 의존성 0건 추가 강제. PR 체크리스트화 |
| Test Run이 운영 시나리오에 영향 | 임시 워크플로우 + 실행 후 정리. 운영 워크플로우와 격리된 prefix 사용 |
| 미커밋 컨버터 코드 손실 | **인계 안정화 단계에서 먼저 commit 필요** (별도 issue) |

---

## 15. Out of Scope (V2+)

- Routing 조건식 GUI 빌더 (when/then 시각 편집)
- 워크플로우 버전 히스토리 / audit log
- 멀티 탭 워크플로우 동시 편집
- 다크 모드
- 모바일 / 터치 최적화
- 워크플로우 태그 / 카테고리
- 에디터 내 실행 데이터(`pinData`) 영구 저장
- 실행 결과의 상세 timeline / metrics 분석

---

## 16. Pre-requisites (작업 시작 전 필수)

이 기능을 시작하기 전, **인계 안정화** 작업이 우선 필요:

1. 미커밋 작업 보존 commits (특히 `endpoints/converters.py`, `services/scenario_converter.py`, docker-compose, `agents/n8n-yaml/`)
2. Windows 환경에서 docker-compose up이 동작 확인 (Docker Desktop 설치 후)
3. n8n 컨테이너에서 `n8n-nodes-scenario` 커스텀 노드 정상 로드 확인
4. 기존 시나리오 YAML 파일 → `/yaml-to-n8n` API 호출 → n8n 임포트 round-trip 검증

---

## 17. Next Steps

1. `/pdca design n8n-yaml-editor-integration` — 본 Plan을 토대로 상세 Design 문서 생성
2. Design 단계에서 결정할 항목:
   - n8n REST API 정확한 엔드포인트/스키마 (n8n 버전 확정)
   - Action 카탈로그 데이터 모델
   - Expression suggestion provider 데이터 소스 정의
   - Test Run 실행 ID/상태 타임아웃 정책
   - Sticky note YAML 스키마 최종 확정 (color hex 허용 여부 등)
3. PRD 후 `/pdca do n8n-yaml-editor-integration`으로 구현 착수

---

*Generated by `/bkit:plan-plus` on 2026-05-01*
