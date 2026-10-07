---
template: design
version: 1.3
feature: n8n-yaml-editor-integration
date: 2026-05-02
author: xession
project: agents-workspace
version: 0.2.0
---

# n8n-yaml-editor-integration Design Document

> **Summary**: n8n editor의 시각·편집 UX를 React Flow 네이티브로 포팅해 시나리오 YAML을 MES 프론트엔드 안에서 편집 가능하게 만듦.
>
> **Project**: agents-workspace
> **Version**: 0.2.0
> **Author**: xession
> **Date**: 2026-05-02
> **Status**: Draft
> **Planning Doc**: [../../plans/2026-05-01-n8n-yaml-editor-integration.plan.md](../../plans/2026-05-01-n8n-yaml-editor-integration.plan.md)

---

## Context Anchor

> Plan 문서 Executive Summary에서 추출 (Plan은 plan-plus 포맷이라 별도 Anchor 섹션 없음 — 본 문서에서 정형화)

| Key | Value |
|-----|-------|
| **WHY** | 시나리오 YAML 편집을 위해 외부 n8n editor를 띄우거나 텍스트 편집기를 써야 하는 단절을 해소. n8n 편집 UX 보존이 1순위. |
| **WHO** | Cell-MES 운영자/엔지니어 (시나리오 마스터 편집자) |
| **RISK** | n8n Sustainable Use License 준수, n8n editor 코드 직접 포팅 시 라이선스 리스크. → React Flow + 시각 패턴 참조만으로 회피. |
| **SUCCESS** | 1) Edit 진입 한 클릭, 2) MES 안에서 편집 완결, 3) export 시 n8n 호환 100%, 4) n8n editor 편집 동작 풀 패리티 (실행 포함) |
| **SCOPE** | 도메인 노드 3종 (manualTrigger / scenarioConfig / scenarioStep) + Sticky notes + Test Execution + 모든 키보드 단축키 |

---

## 1. Overview

### 1.1 Design Goals

1. **시각 풀 패리티**: n8n editor 사용자가 동일 워크플로우 모델(노드 카드, connection 곡선, mini-map, tidy-up)을 그대로 인지할 수 있는 캔버스
2. **편집 풀 패리티**: Undo/Redo, Copy/Paste, Multi-select, Search palette, Expression autocomplete, Sticky notes, Test Execution 모두 V1 포함
3. **도메인 한정**: 3개 노드 타입 외 확장 미지원 (n8n 400+ 노드 재구현 회피)
4. **라이선스 안전**: 기존 n8n 코드 0줄 복사 — 시각/UX 패턴만 참조, 구현은 React Flow + Tailwind
5. **백엔드 재활용**: 기존 `scenario_converter.py` 양방향 컨버터 + `endpoints/converters.py` 그대로

### 1.2 Design Principles

- **Feature-folder colocation**: scenario-editor 기능 코드는 한 폴더(`components/scenario-editor/`) 안에 응집
- **Module boundaries**: canvas / nodes / panels / toolbar / execution / expression / store / hooks / utils 9개 모듈로 책임 분리
- **State separation**: 서버 상태(React Query) vs 에디터 로컬 상태(Zustand 3개 store, immer patch 기반 history)
- **Pure converters**: import/export/serialize 로직은 utils/ 순수 함수, React state와 디커플링
- **Progressive disclosure**: 기본은 캔버스 + 우측 패널, 고급 기능(execution panel / variable explorer)은 토글
- **Convention reuse**: 기존 cell-mes/frontend 컨벤션(Tailwind colors, ErrorBoundary, LoadingState, React Query 키) 그대로 따름

---

## 2. Architecture Options (v1.7.0)

### 2.0 Architecture Comparison

| Criteria | Option A: Minimal | Option B: Clean | Option C: Pragmatic |
|----------|:-:|:-:|:-:|
| **Approach** | scenarios/page.tsx 안에 통합 | Presentation/App/Domain/Infra 4계층 | feature 폴더 + 모듈 분리 |
| **New Files** | ~5 | ~50+ | ~38 |
| **Modified Files** | ~3 | ~10+ | ~5 |
| **Complexity** | 낮음 | 높음 | 중간 |
| **Maintainability** | 낮음 | 매우 높음 | 높음 |
| **Effort** | 6-8주 | 12-16주 | 8-12주 |
| **Risk** | 단일 거대 컴포넌트 폭주 | over-engineering | 낮음 (균형) |
| **Recommendation** | 빠른 polishing | 큰 멀티-feature 플랫폼 | **본 케이스 default** |

**Selected**: **Option C — Pragmatic Balance**
**Rationale**: 본 기능은 단일 feature(scenario editor) + n8n editor 패리티라는 명확한 경계가 있음. 4계층(B)까지 가면 도메인이 React Flow 노드/엣지 모델에 거의 일대일 매핑되는데 추가 추상화는 의미 약함. A는 38 파일을 단일 페이지에 못 담음. C가 sweet spot.

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Browser (Next.js 14, React 18)                      │
│  /master/scenarios/[id]/edit                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ScenarioEditorPage                                            │ │
│  │  ┌──────────┐  ┌──────────────────────┐  ┌─────────────────┐ │ │
│  │  │ Toolbar  │  │ ScenarioCanvas       │  │ ParameterPanel  │ │ │
│  │  │ (Save/   │  │ (React Flow:         │  │ (Step/Config/   │ │ │
│  │  │ Run/...) │  │  3 node types,       │  │  Sticky form +  │ │ │
│  │  │          │  │  edges, mini-map,    │  │  Monaco editor) │ │ │
│  │  └──────────┘  │  controls)           │  └─────────────────┘ │ │
│  │                └──────────────────────┘                       │ │
│  │  ┌──────────────────────────────────────────────────────────┐│ │
│  │  │  ExecutionPanel (collapsible, bottom)                    ││ │
│  │  └──────────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────────┘ │
│      │ Zustand stores: useEditorStore / useHistoryStore /            │
│      │                 useExecutionStore                             │
└──────┼──────────────────────────────────────────────────────────────┘
       │ HTTP (React Query)
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                Cell-MES (FastAPI :8000)                              │
│  /api/v1/masters/scenarios/{id}/content    (GET, PUT 신규)          │
│  /api/v1/masters/scenarios/actions          (GET 신규)              │
│  /api/v1/converters/yaml-to-n8n             (POST 기존)             │
│  /api/v1/converters/n8n-to-yaml             (POST 기존)             │
│  /api/v1/scenarios/{id}/test-runs           (POST 신규)             │
│  /api/v1/scenarios/test-runs/{id}           (GET, /cancel POST 신규)│
└─────────────────┬───────────────────────────────────┬───────────────┘
                  │                                   │
                  ▼                                   ▼
        scenario_converter.py                n8n_runner.py (신규)
        (기존, sticky note 처리만 추가)         │
                                               ▼
                                    ┌───────────────────────┐
                                    │  n8n :5678 (REST API) │
                                    └───────────────────────┘
```

### 2.2 Data Flow

```
[로드]
  GET /scenarios/{id}/content (YAML text)
    → POST /converters/yaml-to-n8n (workflow JSON)
    → setNodes/setEdges (React Flow state)

[편집]
  Node param change
    → useHistoryStore.push (immer patch)
    → useEditorStore.markDirty + validate
    → useAutoSave debounce 2s

[저장]
  workflow JSON serialize
    → POST /converters/n8n-to-yaml (YAML text)
    → PUT /scenarios/{id}/content (server: safe_load + .bak + write)

[Test Run]
  workflow JSON
    → POST /scenarios/{id}/test-runs
    → cell-mes → n8n REST /workflows/run
    → poll GET /test-runs/{exec_id} (1s × 120s max)
    → useExecutionStore update (per-node status/input/output)
    → NodeStatusIndicator + ExecutionPanel render
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| ScenarioEditorPage | useScenarioLoader, useScenarioSaver, ScenarioCanvas, ParameterPanel, EditorToolbar | 페이지 컴포지션 |
| ScenarioCanvas | reactflow, custom Node 컴포넌트 3종, edges, store | 캔버스 렌더 |
| ParameterPanel | useEditorStore (selected), ExpressionInput (Monaco) | 노드 폼 편집 |
| useScenarioLoader | React Query, /converters/yaml-to-n8n | YAML→nodes |
| useScenarioSaver | React Query, /converters/n8n-to-yaml, /scenarios/{id}/content | nodes→YAML+save |
| useTestRunner | React Query, /scenarios/{id}/test-runs, polling | 실행 트리거+폴링 |
| useExpressionSuggestions | useEditorStore.nodes, /scenarios/actions | suggestion provider |

---

## 3. Data Model

### 3.1 Entity Definition (Frontend Types)

```typescript
// 시나리오 YAML 도메인 모델 (서버 컨버터와 1:1)
export interface ScenarioYaml {
  name: string;
  desc?: string;
  assets: Asset[];
  steps: Step[];
  notes?: StickyNote[];        // 신규 (V1 — Sticky notes)
}

export interface Asset {
  id: string;     // e.g. "ANT", "UR"
  name: string;   // e.g. "ANT_ROBOT"
}

export interface Step {
  id: string;
  name?: string;
  acquire?: AcquireRoles;
  action?: string;             // e.g. "{{acq.main}}/api/move"
  params?: Record<string, unknown>;
  routing?: RoutingRule[];
}

export type AcquireRoles = Partial<Record<"main"|"sub1"|"sub2"|"sub3", string[]>>;

export interface RoutingRule {
  when: string | null;
  then: ThenAction[];
}

export type ThenAction = { next: string } | { alarm: string } | Record<string, unknown>;

export interface StickyNote {
  x: number; y: number;
  w: number; h: number;
  text: string;
  color: "yellow" | "blue" | "pink" | "green";
}

// React Flow 표현 (n8n JSON 호환)
export interface RFNode {
  id: string;
  type: "manualTrigger" | "scenarioConfig" | "scenarioStep" | "stickyNote";
  position: { x: number; y: number };
  data: ManualTriggerData | ScenarioConfigData | ScenarioStepData | StickyNoteData;
}

export interface ScenarioStepData {
  stepId: string;
  stepName: string;
  action: string;
  paramsJson: string;          // Monaco 편집 위해 string 보관, save 시 JSON.parse
  acquire: AcquireRoles;
  routing: { values: RoutingValue[] };
  errors?: ValidationError[];   // validate.ts 산출
}

// Test Execution 결과
export interface ExecutionState {
  executionId: string | null;
  status: "idle" | "queued" | "running" | "success" | "error" | "cancelled";
  nodes: Record<string, NodeExecutionState>;
  startedAt?: string;
  finishedAt?: string;
}

export interface NodeExecutionState {
  status: "pending" | "running" | "success" | "error";
  input?: unknown;
  output?: unknown;
  error?: string;
  durationMs?: number;
}
```

### 3.2 Entity Relationships

```
ScenarioYaml 1 ──── N Asset
            1 ──── N Step
            1 ──── N StickyNote
Step        1 ──── N RoutingRule
RoutingRule 1 ──── N ThenAction
```

### 3.3 Backend Model (변경 없음)

기존 cell-mes의 Scenario master 테이블/모델 재사용. YAML 파일은 `file_path` 컬럼이 가리키는 디스크 파일.
신규 `notes` 키는 YAML 파일에 옵션 필드로 추가됨 (DB 스키마 무변경).

---

## 4. API Specification

### 4.1 Endpoint List

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/masters/scenarios/{id}/content` | YAML 텍스트 | JWT | 기존 |
| PUT | `/api/v1/masters/scenarios/{id}/content` | YAML 저장 | JWT | **신규** |
| GET | `/api/v1/masters/scenarios/actions` | Action 카탈로그 | JWT | **신규** |
| POST | `/api/v1/converters/yaml-to-n8n` | YAML → workflow JSON | JWT | 기존 (sticky 처리 추가) |
| POST | `/api/v1/converters/n8n-to-yaml` | workflow JSON → YAML | JWT | 기존 (sticky 처리 추가) |
| POST | `/api/v1/scenarios/{id}/test-runs` | n8n 실행 트리거 | JWT | **신규** |
| GET | `/api/v1/scenarios/test-runs/{exec_id}` | 실행 상태 폴링 | JWT | **신규** |
| POST | `/api/v1/scenarios/test-runs/{exec_id}/cancel` | 실행 취소 | JWT | **신규** |

### 4.2 Detailed Specification

#### `PUT /api/v1/masters/scenarios/{id}/content`

**Request:**
```json
{
  "content": "name: Cell1\nsteps:\n  - id: 1-1\n    ..."
}
```

**Response (200 OK):**
```json
{
  "id": 42,
  "file_path": "scenarios/cell1.yaml",
  "size_bytes": 9778,
  "saved_at": "2026-05-02T15:23:11Z",
  "backup_created": true
}
```

**Errors:**
- `400 VALIDATION_ERROR`: `yaml.safe_load` 실패 → `details.line/column/message`
- `404 NOT_FOUND`: 시나리오 ID 없음
- `409 CONFLICT`: 동시 저장 충돌 (옵션 — V1 단일 사용자 가정 시 X)

#### `GET /api/v1/masters/scenarios/actions`

**Response (200):**
```json
{
  "data": [
    { "key": "{{acq.main}}/api/move", "category": "robot", "description": "Move to position" },
    { "key": "{{acq.sub1}}/api/grip", "category": "gripper", "description": "Close gripper" }
  ]
}
```
캐시는 클라이언트 React Query (`staleTime: Infinity`).

#### `POST /api/v1/scenarios/{id}/test-runs`

**Request:**
```json
{
  "workflow": { "name": "...", "nodes": [...], "connections": {...} }
}
```

**Response (202 Accepted):**
```json
{
  "execution_id": "exec_abc123",
  "status": "queued"
}
```

#### `GET /api/v1/scenarios/test-runs/{exec_id}`

**Response (200):**
```json
{
  "execution_id": "exec_abc123",
  "status": "running",
  "started_at": "2026-05-02T15:24:00Z",
  "nodes": {
    "node-uuid-1": { "status": "success", "output": {...}, "duration_ms": 234 },
    "node-uuid-2": { "status": "running" }
  }
}
```

#### `POST /api/v1/scenarios/test-runs/{exec_id}/cancel`

**Response (200):**
```json
{ "execution_id": "exec_abc123", "status": "cancelled" }
```

---

## 5. UI/UX Design

### 5.1 Screen Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header (기존 layout: 상단 nav, 사이드바)                            │
├──┬──────────────────────────────────────────────┬──────────────────┤
│  │  Toolbar: Save • Cancel • Export • Import • Run • Tidy • ?     │
│  ├──────────────────────────────────────────────┼──────────────────┤
│V │                                              │                  │
│a │                                              │                  │
│r │           ScenarioCanvas                     │                  │
│i │           (React Flow + 3 node types)        │  ParameterPanel  │
│a │                                              │  (선택 노드 폼)   │
│b │           [Mini-map 우상단]                  │                  │
│l │           [Controls 우하단]                  │  - Step ID/Name  │
│e │                                              │  - Action select │
│  │                                              │  - Acquire roles │
│  │                                              │  - Routing rules │
│  │                                              │  - paramsJson    │
│  │                                              │    (Monaco)      │
│  │                                              │                  │
├──┴──────────────────────────────────────────────┴──────────────────┤
│  ExecutionPanel (collapsible, 실행 결과)                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 User Flow

```
시나리오 마스터 목록(/master/scenarios)
  → ✏️ Edit 클릭
  → /master/scenarios/{id}/edit (풀페이지)
  → 캔버스 로드 (YAML→n8n→React Flow)
  → 노드 클릭 → 우측 패널에서 편집
  → autosave (2s debounce)
  → Run 버튼 → ExecutionPanel에서 결과 확인
  → Save & Close → /master/scenarios로 복귀
```

### 5.3 Component List

| Component | Location | Responsibility |
|-----------|----------|----------------|
| ScenarioEditorPage | `app/(main)/master/scenarios/[id]/edit/page.tsx` | 페이지 컨테이너, Loader/Saver/Toolbar 조립 |
| ScenarioCanvas | `components/scenario-editor/canvas/` | React Flow 래퍼 |
| ManualTriggerNode/ScenarioConfigNode/ScenarioStepNode/StickyNoteNode | `components/scenario-editor/nodes/` | 4개 커스텀 노드 카드 |
| ParameterPanel + sub-forms | `components/scenario-editor/panels/` | 우측 사이드 패널 |
| EditorToolbar | `components/scenario-editor/toolbar/` | 상단 액션 바 |
| ExpressionInput | `components/scenario-editor/expression/` | Monaco + autocomplete |
| useEditorStore / useHistoryStore / useExecutionStore | `components/scenario-editor/store/` | Zustand stores |
| useScenarioLoader / Saver / Runner / etc. | `components/scenario-editor/hooks/` | React Query hooks |
| validate / nodeFactory / tidyUp / n8nJsonIO / yamlPreview / stickyNoteIO | `components/scenario-editor/utils/` | 순수 함수 |

### 5.4 Page UI Checklist

#### `/master/scenarios/[id]/edit` — Editor Page

**Toolbar:**
- [ ] Button: Save (Ctrl+S 단축키, 저장 중 spinner, 저장 완료 시 "saved at HH:MM" 표시)
- [ ] Button: Cancel (dirty 시 confirm dialog)
- [ ] Button: Export → n8n JSON 파일 다운로드
- [ ] Button: Import → n8n JSON 업로드 (replace confirm)
- [ ] Button: Run (n8n에 실행 요청)
- [ ] Button: Tidy up (auto-layout)
- [ ] Button: ? (Keyboard shortcuts modal)
- [ ] SaveStatusIndicator: dirty(주황) / saving(파란) / saved at HH:MM(녹색)
- [ ] RunStatusIndicator: idle(회색) / running(파란) / success(녹색) / error(빨강) / cancelled(회색)

**Canvas (React Flow):**
- [ ] Pan / Zoom / Fit-to-view (Controls 패널)
- [ ] Mini-map 우상단 (드래그로 viewport 이동 가능)
- [ ] Background dot grid
- [ ] 마우스 휠 zoom in/out
- [ ] Space + drag = pan
- [ ] 박스 셀렉트 (드래그로 영역 선택)
- [ ] Shift + 클릭 multi-select
- [ ] 우클릭 컨텍스트 메뉴 (Delete, Duplicate, Disable, Add Sticky)

**Nodes:**
- [ ] ManualTriggerNode: 번개 아이콘, 단일 output 핸들, "Manual Trigger" 라벨, 회색 카드
- [ ] ScenarioConfigNode: 톱니 아이콘, single input + single output, 노드 안에 assets 칩 미리보기 (최대 4개)
- [ ] ScenarioStepNode: 스텝 ID + 이름, action 미리보기, routing 룰 개수만큼 출력 핸들, NodeBadge (validation errors), Disable 토글 (호버 시 표시)
- [ ] StickyNoteNode: 색상 배경 (yellow/blue/pink/green), free text, 우하단 리사이즈 핸들, 편집 시 textarea
- [ ] NodeStatusIndicator: 실행 중 ⏳ / 성공 ✓ / 실패 ✗ 오버레이

**Edges:**
- [ ] 베지에 곡선 connection
- [ ] When 표현식 라벨 (truncate, 마우스오버 시 전체 표시)
- [ ] 자석 효과: source 핸들에서 드래그 시 적합한 input 핸들로 스냅
- [ ] 클릭 + Delete 키로 엣지 삭제

**Parameter Panel:**
- [ ] 선택 노드 종류에 따라 form 분기 (Step/Config/Sticky)
- [ ] StepParameterForm: id, name, action(dropdown + custom input), acquire(main/sub1/sub2/sub3 chip 멀티셀렉트), routing(when textarea + then JSON), paramsJson(Monaco)
- [ ] ConfigParameterForm: assets list (id+name 페어, add/remove)
- [ ] StickyParameterForm: text(textarea), color(swatches 4종), w/h(number)
- [ ] 인라인 validation 에러 (필드 하단 빨간 텍스트)
- [ ] Variable Explorer (좌측 또는 사이드 토글): assets, prev step ids, common vars 트리

**Search Palette (Ctrl+K):**
- [ ] 모달 오픈
- [ ] Fuzzy search input
- [ ] 결과 카테고리: Actions(서버 카탈로그), Step IDs(현재 시나리오), Variables
- [ ] 선택 시 viewport 중앙에 노드 추가 또는 패널에 삽입

**Keyboard Shortcuts (Help modal로도 확인):**
- [ ] Ctrl+S Save / Ctrl+Z Undo / Ctrl+Y Redo / Ctrl+C Copy / Ctrl+V Paste / Ctrl+X Cut / Ctrl+D Duplicate / Ctrl+A Select all / Ctrl+K Search / Delete Delete selected / Esc Deselect / Ctrl+0 Reset zoom / Ctrl+= Zoom in / Ctrl+- Zoom out / F2 Rename / ? Show shortcuts

**Execution Panel (collapsible bottom):**
- [ ] Status badge (idle/queued/running/success/error/cancelled)
- [ ] Cancel 버튼 (running 상태일 때)
- [ ] 노드별 상태 리스트 (선택 시 ExecutionDataViewer로 input/output JSON 표시)
- [ ] PinOutputControl: 다음 실행에서 mock으로 사용

**Dirty/Navigation:**
- [ ] dirty 상태에서 페이지 이탈 시 confirm dialog
- [ ] beforeunload 핸들러
- [ ] 자동 저장 (debounce 2s)

---

## 6. Error Handling

### 6.1 Error Code Definition

| Code | Message | Cause | Handling |
|------|---------|-------|----------|
| `VALIDATION_ERROR` (400) | YAML 형식이 잘못되었습니다 | safe_load 실패 / 필수 필드 누락 | 인라인 + toast, dirty 유지 |
| `NOT_FOUND` (404) | 시나리오를 찾을 수 없습니다 | 잘못된 ID, 삭제됨 | router.replace('/master/scenarios') |
| `UNAUTHORIZED` (401) | 인증 만료 | JWT 만료 | 로그인 페이지 redirect |
| `RUNNER_UNAVAILABLE` (503) | n8n 서버 응답 없음 | n8n 컨테이너 다운 | toast + Retry 버튼 |
| `EXEC_TIMEOUT` (408) | 실행이 120초를 초과했습니다 | 폴링 max 도달 | toast + Cancel |
| `ROUNDTRIP_LOSS` (warning) | 일부 정보가 변환 시 손실됩니다 (주석 등) | YAML 주석은 보존 불가 | toast (info), 저장은 계속 |

### 6.2 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "YAML 형식이 잘못되었습니다",
    "details": {
      "line": 14,
      "column": 8,
      "field": "steps[2].acquire"
    }
  }
}
```

---

## 7. Security Considerations

- [x] **JWT 인증**: 기존 `X-Internal-Service-Key` 또는 사용자 JWT 그대로 사용
- [x] **YAML 안전 파싱**: 서버는 `yaml.safe_load`만 사용 (객체 deserialize 위험 차단)
- [x] **파일 경로 escape**: PUT content는 scenario.file_path를 변경하지 않음 (path traversal 차단)
- [x] **n8n REST API key**: `N8N_API_KEY` 환경변수, frontend에 노출 X (cell-mes proxy)
- [x] **입력 길이 제한**: YAML content max 1MB, paramsJson max 100KB
- [x] **XSS 방지**: 노드 텍스트 / sticky note 텍스트 React 기본 escape에 의존 (innerHTML 사용 금지)
- [x] **CORS**: 기존 정책 그대로 (cell-mes는 frontend origin만 허용)
- [ ] Test execution 격리: n8n 임시 워크플로우 prefix `__test__` (운영과 충돌 방지)

---

## 8. Test Plan (v2.3.0)

### 8.1 Test Scope

| Type | Target | Tool | Phase |
|------|--------|------|-------|
| L1: API Tests | 신규 5개 endpoint (PUT content, GET actions, test-runs ×3) | Playwright request / curl | Do |
| L2: UI Action Tests | Editor page 인터랙션 (드래그, 셀렉트, 단축키, 패널 편집) | Playwright | Do |
| L3: E2E Scenario Tests | 시나리오 편집 → 저장 → 실행 → 결과 확인 풀 플로우 | Playwright | Do |
| Unit (extra) | 순수 함수 (validate, nodeFactory, tidyUp, n8nJsonIO, stickyNoteIO) | Vitest | Do |

### 8.2 L1: API Test Scenarios

| # | Endpoint | Method | Test Description | Expected Status | Expected Response |
|---|----------|--------|-----------------|:--------------:|-------------------|
| 1 | `/scenarios/{id}/content` | PUT | 유효한 YAML 저장 | 200 | `.saved_at` 존재, `.backup_created=true` |
| 2 | `/scenarios/{id}/content` | PUT | 잘못된 YAML | 400 | `.error.code=VALIDATION_ERROR`, `.details.line` |
| 3 | `/scenarios/9999/content` | PUT | 없는 ID | 404 | `.error.code=NOT_FOUND` |
| 4 | `/scenarios/actions` | GET | Action 카탈로그 반환 | 200 | `.data` is array, length > 0 |
| 5 | `/scenarios/{id}/test-runs` | POST | 실행 트리거 | 202 | `.execution_id` 존재, `.status=queued` |
| 6 | `/scenarios/test-runs/{exec_id}` | GET | 폴링 응답 | 200 | `.status` ∈ {queued, running, success, error}, `.nodes` 객체 |
| 7 | `/scenarios/test-runs/{exec_id}/cancel` | POST | 실행 취소 | 200 | `.status=cancelled` |
| 8 | `/converters/yaml-to-n8n` | POST | sticky note 포함 YAML | 200 | workflow.nodes에 type=stickyNote 노드 존재 |
| 9 | `/converters/n8n-to-yaml` | POST | sticky note 포함 workflow | 200 | YAML에 `notes:` 키 존재, 좌표/색상 보존 |

### 8.3 L2: UI Action Test Scenarios

| # | Page | Action | Expected Result | Data Verification |
|---|------|--------|----------------|-------------------|
| 1 | edit | 페이지 진입 | 캔버스 + 모든 §5.4 요소 렌더 | scenario YAML 파싱되어 노드 표시 |
| 2 | edit | Step 노드 클릭 | ParameterPanel에 form 표시 | id/name/action 필드 채워짐 |
| 3 | edit | acquire main 칩 변경 → 2초 대기 | autosave 동작 | SaveStatusIndicator "saved at HH:MM" |
| 4 | edit | Ctrl+Z | 직전 변경 undo | 칩이 이전 값으로 복귀 |
| 5 | edit | 노드 선택 후 Ctrl+C → Ctrl+V | 복제 노드 추가 (ID 유니크화) | step_id에 -copy 접미사 |
| 6 | edit | 박스 셀렉트 후 Delete | 다중 노드 삭제 | edges도 정리 |
| 7 | edit | Ctrl+K → "1-1" 검색 → Enter | 노드 추가/포커스 | viewport 중앙에 노드 |
| 8 | edit | Run 클릭 | n8n 호출 → polling | RunStatusIndicator → success / 노드 ✓ |
| 9 | edit | Sticky 추가 → 텍스트 편집 → Save | YAML에 notes 배열 저장 | 재로드 시 sticky 보존 |

### 8.4 L3: E2E Scenario Test Scenarios

| # | Scenario | Steps | Success Criteria |
|---|----------|-------|-----------------|
| 1 | 라운드트립 | scenarios 목록 → Edit → 변경 X → Save → 재로드 | 캔버스 노드 수/연결 동일 |
| 2 | 신규 step 추가 | Edit → Ctrl+K → Add → 파라미터 채움 → Save → 재로드 | 새 step이 YAML에 포함 |
| 3 | 잘못된 YAML 거부 | Edit → paramsJson에 invalid JSON → Save 시도 | 400 + 인라인 에러 표시, dirty 유지 |
| 4 | n8n 호환성 | Save → /converters/n8n-to-yaml 호출 → n8n editor에 import | n8n에서 정상 렌더 + 실행 가능 |
| 5 | Test Run + Cancel | Run → 실행 중 → Cancel 클릭 | status=cancelled, ExecutionPanel 갱신 |
| 6 | Sticky 보존 | Sticky 3개 추가 → Save → DB scenario file 확인 | YAML notes[]에 3개 |
| 7 | Dirty navigation | 변경 후 뒤로가기 | confirm dialog 표시 |

### 8.5 Seed Data Requirements

| Entity | Minimum Count | Key Fields Required |
|--------|:------------:|---------------------|
| Scenario master | 3 | code, name, file_path (YAML 파일 존재해야 함) |
| Scenario YAML 파일 | 3 | name, assets(2+), steps(5+) — cell1_scenario.yaml 활용 |
| Action 카탈로그 | 5 | key 5종 (move/grip/release/wait/check) |

---

## 9. Clean Architecture (Lite)

> Option C는 4계층 풀 분리 대신 feature 폴더 + 모듈 응집을 채택. 각 모듈은 단방향 import만 허용.

### 9.1 Layer Structure (Feature-Internal)

| Layer | Responsibility | Location |
|-------|---------------|----------|
| **Page** | URL 진입점, 컨테이너 | `app/(main)/master/scenarios/[id]/edit/` |
| **Components** | 캔버스/노드/엣지/패널/툴바/실행 UI | `components/scenario-editor/{canvas,nodes,edges,panels,toolbar,execution,expression}/` |
| **State** | Zustand stores | `components/scenario-editor/store/` |
| **Hooks** | 서버 통신 + 키보드 + autosave | `components/scenario-editor/hooks/` |
| **Utils** | 순수 함수 (validate, nodeFactory, tidyUp, IO) | `components/scenario-editor/utils/` |

### 9.2 Dependency Rules

```
Page ─→ Components ─→ State ─→ (no deps)
       └─→ Hooks ─→ Utils ─→ (no deps)
       └─→ Hooks ─→ services/ (api client)
       └─→ Utils ─→ types/
```

**Rule**:
- Utils는 React/Zustand 의존 금지 (순수)
- State는 Hooks 의존 금지 (Hooks가 store 호출)
- Components는 Utils/State/Hooks 자유롭게 import

### 9.3 File Import Rules

| From | Can Import | Cannot Import |
|------|-----------|---------------|
| Page | Components, Hooks | Utils 직접 (Hooks 통해) |
| Components | State, Hooks, Utils, types | services/ 직접 (Hooks 통해) |
| Hooks | Utils, State, services/ | Components |
| State | Utils, types | Components, Hooks, services/ |
| Utils | types only | 모든 외부 (React, Zustand 등) |

### 9.4 This Feature's Layer Assignment

| Component | Layer | Location |
|-----------|-------|----------|
| ScenarioEditorPage | Page | `app/(main)/master/scenarios/[id]/edit/page.tsx` |
| ScenarioCanvas | Components/canvas | `components/scenario-editor/canvas/ScenarioCanvas.tsx` |
| useEditorStore | State | `components/scenario-editor/store/useEditorStore.ts` |
| useScenarioLoader | Hooks | `components/scenario-editor/hooks/useScenarioLoader.ts` |
| validate | Utils | `components/scenario-editor/utils/validate.ts` |
| ScenarioYaml type | types | `types/scenario.ts` (전역) |

---

## 10. Coding Convention Reference

### 10.1 Naming Conventions

기존 cell-mes/frontend 컨벤션 그대로:

| Target | Rule | Example |
|--------|------|---------|
| Components | PascalCase | `ScenarioCanvas`, `ManualTriggerNode` |
| Hooks | camelCase + `use` prefix | `useScenarioLoader`, `useAutoSave` |
| Stores | camelCase + `use` prefix + `Store` | `useEditorStore` |
| Utils functions | camelCase | `validateNode`, `tidyUp` |
| Types | PascalCase | `ScenarioYaml`, `RFNode` |
| Files (component) | PascalCase.tsx | `ScenarioCanvas.tsx` |
| Files (hook/util) | camelCase.ts | `useScenarioLoader.ts`, `validate.ts` |
| Folders | kebab-case | `scenario-editor/`, `scenario-editor/canvas/` |

### 10.2 Import Order (TS/TSX)

```typescript
// 1. External
import { useCallback, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import { Editor as MonacoEditor } from "@monaco-editor/react";

// 2. Absolute
import { api } from "@/lib/api";
import { ErrorBoundary, LoadingState } from "@/components";

// 3. Feature-internal
import { useEditorStore } from "../store/useEditorStore";
import { validateNodes } from "../utils/validate";

// 4. Type imports
import type { ScenarioYaml, RFNode } from "@/types/scenario";

// 5. Styles
import "reactflow/dist/style.css";
```

### 10.3 Environment Variables

| Var | Purpose | Scope |
|-----|---------|-------|
| `NEXT_PUBLIC_API_URL` | cell-mes 베이스 URL | Browser |
| `N8N_API_KEY` | n8n REST 인증 | cell-mes server |
| `N8N_BASE_URL` | n8n 컨테이너 URL | cell-mes server |

### 10.4 This Feature's Conventions

| Item | Convention Applied |
|------|-------------------|
| Component naming | PascalCase, 1 component per file |
| File organization | feature folder + 9 modules |
| State management | Zustand 3 stores + React Query |
| Error handling | ErrorBoundary + toast (sonner or 기존 패턴) |
| Form state | uncontrolled with onChange → store dispatch (no react-hook-form 도입) |

---

## 11. Implementation Guide

### 11.1 File Structure

```
agents/cell-mes/frontend/
├── app/(main)/master/scenarios/[id]/edit/
│   └── page.tsx                                    # ScenarioEditorPage
├── components/scenario-editor/
│   ├── canvas/
│   │   ├── ScenarioCanvas.tsx
│   │   ├── MiniMap.tsx
│   │   ├── Background.tsx
│   │   ├── Controls.tsx
│   │   └── ConnectionLine.tsx
│   ├── nodes/
│   │   ├── ManualTriggerNode.tsx
│   │   ├── ScenarioConfigNode.tsx
│   │   ├── ScenarioStepNode.tsx
│   │   ├── StickyNoteNode.tsx
│   │   ├── NodeBadge.tsx
│   │   ├── NodeStatusIndicator.tsx
│   │   └── NodeContextMenu.tsx
│   ├── edges/
│   │   └── RoutingEdge.tsx
│   ├── panels/
│   │   ├── ParameterPanel.tsx
│   │   ├── StepParameterForm.tsx
│   │   ├── ConfigParameterForm.tsx
│   │   ├── StickyParameterForm.tsx
│   │   ├── RoutingRulesEditor.tsx
│   │   ├── AcquireRolesEditor.tsx
│   │   ├── NodeSearchPalette.tsx
│   │   ├── VariableExplorer.tsx
│   │   └── ExecutionPanel.tsx
│   ├── toolbar/
│   │   ├── EditorToolbar.tsx
│   │   ├── SaveStatusIndicator.tsx
│   │   ├── RunStatusIndicator.tsx
│   │   └── KeyboardShortcutsHelp.tsx
│   ├── execution/
│   │   ├── useTestRunner.ts
│   │   ├── ExecutionDataViewer.tsx
│   │   ├── PinOutputControl.tsx
│   │   └── runStateMachine.ts
│   ├── expression/
│   │   ├── ExpressionInput.tsx
│   │   ├── useExpressionSuggestions.ts
│   │   └── expressionFunctions.ts
│   ├── store/
│   │   ├── useEditorStore.ts
│   │   ├── useHistoryStore.ts
│   │   └── useExecutionStore.ts
│   ├── hooks/
│   │   ├── useScenarioLoader.ts
│   │   ├── useScenarioSaver.ts
│   │   ├── useKeyboardShortcuts.ts
│   │   ├── useAutoSave.ts
│   │   ├── useClipboard.ts
│   │   └── useUndoRedo.ts
│   └── utils/
│       ├── validate.ts
│       ├── nodeFactory.ts
│       ├── tidyUp.ts
│       ├── n8nJsonIO.ts
│       ├── yamlPreview.ts
│       └── stickyNoteIO.ts
└── types/
    └── scenario.ts                                 # 신규 (도메인 모델 + RF 모델)

agents/cell-mes/src/
├── app/api/v1/endpoints/
│   └── scenarios.py                                # 기존 + test-runs 추가
├── app/api/v1/endpoints/masters.py                 # PUT content / actions 추가
└── app/services/
    ├── scenario_converter.py                       # 기존 + sticky note 처리
    └── n8n_runner.py                               # 신규 (n8n REST 클라이언트)

docker-compose.yml                                   # n8n env vars 추가
```

### 11.2 Implementation Order

1. [ ] **M0 — Backend foundation**: `PUT /scenarios/{id}/content` + `GET /scenarios/actions` + scenario_converter sticky 처리 + L1 테스트
2. [ ] **M1 — Editor scaffold**: 라우트 진입점, 페이지 컨테이너, types/scenario.ts, useScenarioLoader/Saver, ScenarioCanvas (빈 캔버스)
3. [ ] **M2 — Nodes & Edges**: ManualTrigger / ScenarioConfig / ScenarioStep / StickyNote 노드 + RoutingEdge + 자석 connection + Background/Mini-map/Controls
4. [ ] **M3 — Parameter Panel**: ParameterPanel + Step/Config/Sticky form + RoutingRulesEditor + AcquireRolesEditor + 인라인 validation
5. [ ] **M4 — Editor State**: useEditorStore + useHistoryStore (immer) + useAutoSave + dirty navigation guard + Save/Cancel 토스트
6. [ ] **M5 — Manipulation**: Multi-select + Copy/Paste/Cut/Duplicate + Undo/Redo 키보드 + box select + Bulk delete
7. [ ] **M6 — Search & Layout**: NodeSearchPalette (Ctrl+K) + tidy up (dagre) + KeyboardShortcutsHelp + Auto-layout 버튼
8. [ ] **M7 — Expression & Variables**: ExpressionInput (Monaco) + useExpressionSuggestions + VariableExplorer + paramsJson Monaco
9. [ ] **M8 — Sticky notes**: StickyNoteNode + StickyParameterForm + stickyNoteIO + 컨버터 sticky 라운드트립 검증
10. [ ] **M9 — Test Execution backend**: n8n_runner.py + `/test-runs` 3개 endpoint + n8n env vars + L1 테스트
11. [ ] **M10 — Test Execution UI**: ExecutionPanel + useTestRunner + NodeStatusIndicator + RunStatusIndicator + PinOutput + Cancel
12. [ ] **M11 — Export/Import**: Export n8n JSON 다운로드 + Import 파일 업로드 + YAML 미리보기 모달
13. [ ] **M12 — Polish & QA**: L2/L3 Playwright 테스트 작성 + 디자인 폴리싱 + 성능 최적화 (큰 시나리오) + 접근성

### 11.3 Session Guide

> Auto-generated. 13 모듈 → 권장 5-7 세션. 각 세션은 1-2 모듈씩 묶음.

#### Module Map

| Module | Scope Key | Description | Estimated Turns |
|--------|-----------|-------------|:---------------:|
| Backend foundation | `m0-backend` | PUT/GET endpoints + sticky converter + L1 tests | 25-35 |
| Editor scaffold | `m1-scaffold` | 라우트, 페이지, types, Loader/Saver, 빈 캔버스 | 30-40 |
| Nodes & Edges | `m2-nodes` | 4종 노드 + 엣지 + Background/Mini-map | 40-55 |
| Parameter Panel | `m3-panel` | 사이드 패널 + 3종 form + validation | 40-55 |
| Editor State | `m4-state` | 3 stores + autosave + dirty guard | 30-40 |
| Manipulation | `m5-manipulation` | Multi-select + Copy/Paste + Undo/Redo | 35-45 |
| Search & Layout | `m6-search-layout` | Search palette + tidy up + shortcuts help | 25-35 |
| Expression & Variables | `m7-expression` | Monaco + autocomplete + Variable Explorer | 35-45 |
| Sticky notes | `m8-sticky` | Sticky 노드 + 컨버터 라운드트립 | 20-30 |
| Test Execution backend | `m9-exec-backend` | n8n_runner + 3 endpoints | 25-35 |
| Test Execution UI | `m10-exec-ui` | ExecutionPanel + status indicators | 30-40 |
| Export/Import | `m11-io` | n8n JSON IO + YAML preview | 15-25 |
| Polish & QA | `m12-polish` | L2/L3 + 폴리싱 + 성능 + 접근성 | 30-50 |

#### Recommended Session Plan

| Session | Phase | Scope | Turns | 비고 |
|---------|-------|-------|:-----:|------|
| 1 | Plan + Design | (완료) | (완료) | plan-plus + /pdca design |
| 2 | Do | `--scope m0-backend` | 25-35 | M0 — 백엔드 인프라 먼저 |
| 3 | Do | `--scope m1-scaffold,m2-nodes` | 70-95 | M1+M2 — 캔버스 가시화 |
| 4 | Do | `--scope m3-panel,m4-state` | 70-95 | M3+M4 — 편집 가능 상태 |
| 5 | Do | `--scope m5-manipulation,m6-search-layout` | 60-80 | M5+M6 — 풍부한 편집 UX |
| 6 | Do | `--scope m7-expression,m8-sticky` | 55-75 | M7+M8 — 고급 입력 + Sticky |
| 7 | Do | `--scope m9-exec-backend,m10-exec-ui` | 55-75 | M9+M10 — Test Run |
| 8 | Do | `--scope m11-io,m12-polish` | 45-75 | M11+M12 — 마무리 |
| 9 | Check + Report | 전체 | 30-40 | gap-detector + report |

**Total: 9 세션 / 410-570 turns / 약 6-8주**

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-05-02 | Initial draft from plan-plus + /pdca design Option C | xession |
