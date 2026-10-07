# NL-Router 테스트 전략

## 테스트 피라미드

```
        ┌─────────────┐
        │   E2E      │  ← 실제 사용자 시나리오 (느림, 비쌈)
        │  테스트    │     5-10개 핵심 워크플로우
        ├─────────────┤
        │  통합      │  ← API 응답 정합성 (중간)
        │  테스트    │     Intent별 1-2개
        ├─────────────┤
        │   단위     │  ← 개별 함수 검증 (빠름, 저렴)
        │  테스트    │     모든 Intent 커버
        └─────────────┘
```

## 테스트 체크리스트

### 새 Intent 추가 시 필수 체크리스트

- [ ] `intents.py`에 Intent enum 추가
- [ ] `intent_classifier.py`에 분류 패턴 추가
- [ ] `api_selector.py`에 API 매핑 추가
- [ ] `nl_router_agent.py`의 `_generate_summary()`에 핸들러 추가
- [ ] **단위 테스트**: `test_nl_router_agent.py`에 응답 포맷 테스트 추가
- [ ] **E2E 테스트**: `ai-validation.spec.ts`에 검증 테스트 추가

### 자동 검증 (CI/CD)

```bash
# 테스트 커버리지 갭 체크 (PR 차단 가능)
python scripts/generate_intent_tests.py --check

# 실패 조건:
# - 핸들러 없는 Intent 존재
# - 단위 테스트 없는 핸들러 존재
```

## Intent별 테스트 매트릭스

| Intent | 핸들러 | 단위테스트 | E2E | 비고 |
|--------|--------|-----------|-----|------|
| PRODUCTION_STATUS | ✅ | ✅ | ✅ | - |
| PRODUCTION_DETAIL | ✅ | ✅ | ❌ | 2/15 추가 |
| EQUIPMENT_STATUS | ✅ | ✅ | ✅ | - |
| EQUIPMENT_LIST | ✅ | ✅ | ❌ | 2/15 추가 |
| KPI_QUERY | ✅ | ✅ | ✅ | - |
| SCHEDULE_QUERY | ✅ | ✅ | ✅ | - |
| SCHEDULE_REQUEST | ✅ | ✅ | ❌ | 2/15 추가 |
| MASTER_DATA_QUERY | ✅ | ✅ | ❌ | 2/15 추가 |
| TRACEABILITY | ✅ | ✅ | ✅ | - |
| COMPARISON | ✅ | ✅ | ❌ | TODO: E2E |
| ANALYTICS | ✅ | ✅ | ❌ | 2/15 추가 |
| ERROR_DIAGNOSIS | ✅ | ✅ | ❌ | 2/15 추가 |
| DELAY_PREDICTION | ✅ | ✅ | ❌ | 2/15 추가 |
| DEFECT_ANALYSIS | ✅ | ✅ | ❌ | 2/15 추가 |
| TOOL_MANAGEMENT | ✅ | ✅ | ❌ | 2/15 추가 |
| ACTION_REQUEST | ✅ | ✅ | ❌ | 2/15 추가 |
| HELP | ✅ | ✅ | ❌ | 2/15 추가 |
| UNKNOWN | (fallback) | ✅ | - | - |

## 테스트 생성 워크플로우

### 1. 갭 분석
```bash
python scripts/generate_intent_tests.py --check
```

### 2. 템플릿 생성
```bash
python scripts/generate_intent_tests.py --generate > missing_tests.txt
```

### 3. 템플릿 커스터마이징
- 각 Intent의 실제 API 응답 구조 확인
- 필수 키워드/숫자 검증 추가
- 엣지 케이스 추가 (빈 데이터, 에러 등)

### 4. 테스트 실행
```bash
# 단위 테스트
uv run pytest tests/test_nl_router_agent.py -v

# E2E 테스트
cd ../cell-mes/frontend && npx playwright test e2e/validation/ai-validation.spec.ts
```

## 권장 테스트 비율

- **단위 테스트**: Intent당 3-5개
  - 정상 데이터
  - 빈 데이터
  - 부분 데이터
  - 에러 케이스
  
- **E2E 테스트**: Intent당 1-2개
  - 기본 질문
  - API 데이터 정합성

## CI/CD 통합

```yaml
# .github/workflows/test.yml
- name: Check test coverage gaps
  run: |
    cd agents/nl-router
    python scripts/generate_intent_tests.py --check
    if [ $? -ne 0 ]; then
      echo "❌ 테스트 커버리지 갭 발견!"
      exit 1
    fi

- name: Run unit tests
  run: uv run pytest agents/nl-router/tests/ -v

- name: Run E2E tests
  run: npx playwright test e2e/validation/
```
