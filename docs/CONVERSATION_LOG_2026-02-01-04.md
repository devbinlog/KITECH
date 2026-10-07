# agents-workspace 전체 대화 로그

**기간**: 2026-02-01 ~ 2026-02-04  
**주제**: Physical AI 논문, NLM 개발, 패키지 관리, Digital Thread + SPC/QMS

---

# 2026-02-01

## 오전: Physical AI Review 논문 작업

### 논문 구조 완성

**최종 파일**: `Draft_Paper/03_Physical_AI_Review_v4.md`

**구조 (6 Chapters, ~23 pages):**

| Ch | Title | 내용 |
|----|-------|------|
| 1 | Introduction | 배경, Physical AI 정의 |
| 2 | Methodology | 4가지 물리-AI 통합 방식 (Algorithm 1-6) |
| 3 | Data-Efficient Learning | Transfer/Meta/Few-shot Learning |
| 4 | Applications | 6개 분야 TRL 평가 |
| 5 | Future Directions | 5대 발전 방향 |
| 6 | Conclusion | 기술 선택 가이드, 전망 |

### 버전 히스토리

| Version | 변경사항 |
|---------|----------|
| v1 (00_) | 최초 초안 |
| v2 (01_) | 절삭역학 깊이 + 채터 이론 + Meta-Learning 추가 |
| v3 (02_) | Pseudo code 변환, 일관성 검토 |
| v4 (03_) | 최종본 - v1 구조 유지, Ch.2 절삭역학 축소 통합 |

### 사용자 피드백
> "챕터 2가 리뷰논문 치고는 빈약해. v1의 관점은 유지하면서 최종본의 챕터 2 관점의 중요도를 좀 낮춰서 합쳐줬으면 좋겠어"

**조치**: 기존 Ch.2 (절삭역학 기초 4p) → Ch.2 방법론의 서브섹션으로 축소 통합

---

## 오후: 브라우저 자동화 및 논문 다운로드

### 설정 완료
- Brave 브라우저 설치 (`brew install --cask brave-browser`)
- CDP(Chrome DevTools Protocol) 연결 설정
- agent-browser CLI 설치 (`npm install -g agent-browser`)

### 논문 다운로드 시도
- Unpaywall API로 OA 논문 검색
- 다운로드 완료: 4편 (Raissi, Karniadakis, Cuomo, Zhu)
- 다운로드 필요: ~21편 (정인이 회사에서 받기로)

### 전문가 관점 리뷰
`Draft_Paper/Expert_Review_Perspectives.md` 작성:
- 절삭가공 대가 관점 (Altintas/Budak)
- ML/자율제조 대가 관점 (Jay Lee/Karniadakis)

---

## 저녁: Cell-MES 및 NL-Router 개발

### Cell-MES 프론트엔드 수정
- 표준공정 페이지 삭제 기능 추가
- StatusGrid/StatusCards/TraceabilityTimeline - config.color undefined 에러 수정

### NLM 자연어 패턴 확장

**추가된 역할별 패턴:**

**👷 현장작업자:**
```
"라인 살아있어?" → daily_status
"이거 망가졌어" → equipment_status
"다음 뭐야?" → work_orders
"빨간불 들어왔어" → equipment_status
```

**🏭 공장관리자:**
```
"병목 설비 어디야?" → equipment_status
"목표 달성률" → daily_status
"경영진 보고용 자료" → kpi
```

**👔 사장님:**
```
"오늘 잘 돌아가?" → daily_status
"납기 지킬 수 있어?" → schedule
"야근해야 해?" → kpi
```

### NL-Router ↔ Cell-MES 연동 완료

**문제 해결:**
1. pkill 패턴 수정: `uvicorn.*:8000` → `port 8000`
2. uv workspace에 nl-router 추가
3. 내부 서비스 인증: `X-Internal-Service-Key` 헤더
4. URL 경로 중복: base_url에서 `/api/v1` 제거
5. 날짜 파싱: "today" 문자열 처리 추가

**최종 테스트 결과**: ✅ 모든 쿼리 정상 분류

---

## NLM Retriever 개선

### 작업 내용
- KeywordRetriever 패턴 확장
- 동의어 사전 추가: 구어체 표현

### 테스트 결과
- 초기: 75% 정확도
- 패턴 추가 후: 93.8%
- "살아있" 동의어 수정 후: 100% ✅

---

# 2026-02-02

## agents-workspace 프로덕션 준비

### 테스트 결과
- **전체**: 413개 통과
- gcode-parser: 46 passed
- cam-runner: 54 passed, 20 skipped
- cell-scheduler: 75 passed, 10 skipped
- cell-schedule-visualizer: 61 passed
- nl-router: 165 passed
- orchestrator: 12 passed (신규)

### 정적 분석
- Ruff: 142개 에러 중 114개 자동 수정
- 복잡도: A등급 (CC 3.24)
- 커버리지: 평균 64%

### 문서화 완료
- README.md 전체 업데이트
- docs/ARCHITECTURE.md 생성
- 에이전트별 README 7개 생성

### 설정 환경 분리
- `.env.example`, `.env.dev`, `.env.prod`

### 공통 모듈 생성
- `shared/common/logging_config.py`
- `shared/common/error_handling.py`

### step-pmi-reader 신규 에이전트
- STEP AP242 파일에서 PMI 정보 추출
- 지원: 데이텀, GD&T 12종, 치수 공차, 표면 거칠기
- 18개 테스트 통과

---

# 2026-02-03

## Digital Thread 프로젝트

### 신규 에이전트 개발

**digital-thread-project-manager:**
- ISO_api 코드 이식
- CAM→XML 변환
- 14 tests passed

**monitoring-data-replayer:**
- TDMS/LOG 파싱
- 리플레이 엔진
- 30 tests passed

### PMI-Toolpath 연계 설계

**아키텍처:**
1. PMI 추출 (STEP AP242)
2. Surface 매칭 (PMI → CAD Face → Workingstep)
3. NC 동기화 (NC 라인 ↔ 모니터링 시간)
4. 품질 분석 (리스크 평가)

---

## 저녁: 테스트 실패 분석 및 수정

### 테스트 실패 원인

```
ValueError: file_path must not contain path traversal sequences
```

**원인**: `validate_safe_path()`가 `/`로 시작하는 경로 거부

**수정:**
```python
# ❌ 이전
file_path="/scenarios/test.xml"

# ✅ 수정
file_path="scenarios/test.xml"
```

**수정 파일:**
- tests/conftest.py
- tests/test_api/test_scenarios.py
- tests/test_api/test_routings.py
- tests/test_scheduler_integration.py

### uv workspace 문제 발견

```bash
uv sync
# 결과: Uninstalled 106 packages ← 워크스페이스 멤버 전부 삭제!
```

**해결:**
```bash
uv sync --all-packages  # 전체 워크스페이스 동기화
```

### pyproject.toml 수정

**cell-scheduler, step-pmi-reader:**
```toml
# 추가됨
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**nl-router:**
- 중복 `[project.optional-dependencies]` 제거
- `[dependency-groups]`만 유지

### 최종 테스트 결과

| Agent | Passed | Skipped |
|-------|--------|---------|
| gcode-parser | 46 | 0 |
| cam-runner | 54 | 24 |
| cell-scheduler | 151 | 10 |
| cell-mes | 333 | 1 |
| nl-router | 289 | 0 |
| digital-thread-project-manager | 85 | 1 |
| monitoring-data-replayer | 30 | 0 |
| step-pmi-reader | 18 | 0 |
| **Total** | **1,006** | **36** |

---

## 컨테이너화 논의

### 사용자
> "프로젝트가 대형으로 바뀌면서 패키지 꼬이는게 심하네 컨테이너로 해결할 수 있을까?"

### 현재 문제점 vs 컨테이너 해결

| 문제 | 현재 | 컨테이너 |
|------|------|----------|
| 패키지 꼬임 | uv workspace 복잡 | 서비스별 독립 |
| Import 충돌 | 루트 테스트 불가 | 컨테이너 격리 |
| 포트 관리 | 수동 .env | compose 자동 |
| 서비스 조율 | start/stop 스크립트 | compose up/down |

### 추천 구조

```
agents-workspace/
├── services/              # 컨테이너
│   ├── cell-mes/
│   ├── nl-router/
│   └── cell-scheduler/
├── libs/                  # 공유 라이브러리
│   ├── gcode-parser/
│   ├── cam-runner/
│   └── ...
├── shared/
└── docker-compose.yml
```

---

## Digital Thread + SPC/QMS 설계

### 사용자
> "Digital thread와 연계해서 mes에 spc, qms 일부 기능만 넣으려고 해"

### Digital Thread Flow

```
STEP/PMI → CAM/NC → Machining → Inspection → SPC/QMS
   │          │          │           │           │
 치수/공차  가공조건   실시간모니터링  측정결과    품질분석
   └──────────┴──────────┴───────────┴───────────┘
                    Full Traceability
```

### SPC 기능

| 기능 | 복잡도 | 가치 |
|------|--------|------|
| Control Chart (X-bar, R) | ⭐⭐ | 높음 |
| Cp/Cpk 계산 | ⭐ | 높음 |
| 관리 이탈 감지 | ⭐⭐ | 높음 |

### QMS 기능

| 기능 | 복잡도 | 가치 |
|------|--------|------|
| 검사 계획 자동생성 | ⭐⭐⭐ | 매우 높음 |
| 초도품 검사 (FAI) | ⭐⭐ | 높음 |
| 부적합 보고서 (NCR) | ⭐⭐ | 높음 |

---

## 측정 시스템 통합 (OMM + Equator)

### 사용자
> "우리는 omm과 renishaw equator로 측정하는걸 고려해줘"

### 측정 소스별 특성

| 항목 | OMM | Equator |
|------|-----|---------|
| 타이밍 | 가공 중/직후 | 가공 완료 후 |
| 목적 | 공구 보정 | 최종 검사, SPC |
| 정밀도 | ±5-10μm | ±2μm |
| 연동 | DPRNT/매크로 | EZ-IO/CSV |

### Closed-Loop 워크플로우

```
가공 시작 → OMM 측정 → 편차 체크 → 공구 보정
    ↓
가공 계속 → Equator 최종 검사 → SPC 업데이트
    ↓
추세 이상? → 경고 알림
```

---

# 2026-02-04

## 프로젝트 구조 재설계

### 사용자
> "아까 컨테이너와 agent가 구조가 매치가 안되던데 괜찮은 구조를 추천해줘"

### 최종 추천 구조

```
agents-workspace/
│
├── services/                      # 🐳 컨테이너
│   ├── mes/                       # port 8000
│   ├── gateway/                   # port 8001
│   ├── scheduler/                 # port 8002
│   └── collector/                 # port 8003
│
├── libs/                          # 📦 라이브러리
│   ├── gcode-parser/
│   ├── cam-runner/
│   ├── step-pmi-reader/
│   ├── monitoring-replayer/
│   └── digital-thread/
│
├── shared/                        # 🔗 공유
│   ├── models/
│   └── utils/
│
├── workflows/                     # 🔄 Orchestrator
│
├── docker-compose.yml
└── pyproject.toml
```

### Service vs Library 구분

| 구분 | 특징 | 컨테이너 |
|------|------|----------|
| Service | HTTP API, 상태 유지 | ✅ |
| Library | import용 | ❌ |

### 의존성 규칙

```
Service → Library: import ✅
Service → Service: HTTP only ✅
Library → Service: ❌ 금지
```

### 마이그레이션 매핑

| 현재 | 새 구조 |
|------|---------|
| agents/cell-mes | services/mes |
| agents/nl-router | services/gateway |
| agents/cell-scheduler | services/scheduler |
| agents/gcode-parser | libs/gcode-parser |
| agents/cam-runner | libs/cam-runner |

---

## 문서화 요청

### 사용자
> "Digital Thread + SPC/QMS 내용 별도 md로 만들어줘"

**생성 파일**: `DIGITAL_THREAD_SPC_QMS.md`

---

## 대화 로그 요청

### 사용자
> "이제까지 너랑 한 모든 대화를 붙여서 md 파일로 내보내줘"

**생성 파일**: `CONVERSATION_LOG_2026-02-01-04.md` (이 파일)

---

# 핵심 교훈

## uv workspace 황금률

```
1. uv sync --all-packages  (항상!)
2. 멤버에 [build-system] 필수
3. [dependency-groups] 또는 [optional-dependencies] 중 택1
4. 테스트는 각 에이전트 디렉토리에서 개별 실행
```

## pyproject.toml 필수 요소

```toml
[project]
name = "agent-name"
version = "0.1.0"
requires-python = ">=3.10"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 테스트 파일 경로

```python
# ❌ 안 됨
file_path="/scenarios/test.xml"

# ✅ 됨
file_path="scenarios/test.xml"
```

---

# 다음 단계

1. [ ] 프로젝트 구조 마이그레이션 (services/, libs/)
2. [ ] measurement-collector 서비스 생성
3. [ ] Docker 컨테이너화
4. [ ] SPC/QMS 기능 구현
5. [ ] PMI → 검사계획 자동생성

---

*Generated: 2026-02-04 17:44 KST*
