# Manufacturing Agent Skills Catalog

에이전트 시스템의 스킬 라이브러리. Domain Skills (런타임)과 Development Skills (코드 패턴) 두 카테고리.

## Quick Navigation

### Domain Skills (Runtime)

| Skill | File | Purpose |
|-------|------|---------|
| G-Code Analysis | [gcode_analysis.md](gcode_analysis.md) | Parse G-code, extract blocks, calculate Ap/Ae |
| CAM Computation | [cam_computation.md](cam_computation.md) | Analyze tool paths, engagement metrics |
| Manufacturing Scheduling | [manufacturing_scheduling.md](manufacturing_scheduling.md) | CP-SAT based job scheduling |
| Schedule Visualization | [schedule_visualization.md](schedule_visualization.md) | Gantt charts, utilization dashboards |
| Workflow Orchestration | [workflow_orchestration.md](workflow_orchestration.md) | LangGraph DAG orchestration, state threading |

### Development Skills (Code Maintenance)

| Skill | File | Purpose |
|-------|------|---------|
| **uv Workspace** | [uv_workspace.md](uv_workspace.md) | **uv workspace 관리 규칙, 트러블슈팅 (필독)** |
| Service Management | [service_management.md](service_management.md) | 서비스 시작/중지, 인증, DB 관리 |
| Test-Driven Updates | [test_driven_updates.md](test_driven_updates.md) | 코드 변경 + 테스트 동기화 워크플로우 |
| Test Implementation | [test_implementation.md](test_implementation.md) | pytest 픽스처, mocking, 커버리지 |
| Config Management | [config_management.md](config_management.md) | YAML/JSON 로딩, 검증, 환경변수 |
| Data Validation | [data_validation.md](data_validation.md) | Dataclass 정의, 타입 검증, 에러 수집 |
| Error Handling | [error_handling.md](error_handling.md) | AnalysisResult, 에러 축적, 로깅 |
| Code Documentation | [code_documentation.md](code_documentation.md) | Google 스타일 docstring |
| Performance Optimization | [performance_optimization.md](performance_optimization.md) | 프로파일링, CP-SAT 튜닝 |
| Dependency Integration | [dependency_integration.md](dependency_integration.md) | 선택적 의존성, fallback, 버전 관리 |

## Skill Structure

모든 스킬 마크다운은 다음 구조를 따름:

```markdown
# Skill Name
한 줄 설명

## Critical Rules
1. 가장 중요한 규칙들 (번호 목록)

## Instructions
### Step 1: ...
### Step 2: ...

## Examples
구체적인 코드 예시

## Troubleshooting (해당 시)
문제별 해결 방법

## Anti-patterns (해당 시)
❌ 잘못된 패턴 vs ✅ 올바른 패턴
```

## 스킬 선택 가이드

| 작업 | 스킬 |
|------|------|
| uv 꼬임/의존성 문제 | [uv_workspace.md](uv_workspace.md) |
| 서비스 관리/트러블슈팅 | [service_management.md](service_management.md) |
| 테스트 작성 | [test_implementation.md](test_implementation.md) |
| 코드 변경 + 테스트 동기화 | [test_driven_updates.md](test_driven_updates.md) |
| 설정 파일 로딩 | [config_management.md](config_management.md) |
| JSON/dict 검증 | [data_validation.md](data_validation.md) |
| 에러 처리 | [error_handling.md](error_handling.md) |
| Docstring 작성 | [code_documentation.md](code_documentation.md) |
| 성능 최적화 | [performance_optimization.md](performance_optimization.md) |
| 라이브러리 관리 | [dependency_integration.md](dependency_integration.md) |

## Maintenance

### 새 스킬 추가

1. `shared/skills/`에 마크다운 파일 생성 (위 구조 따르기)
2. `__init__.py`에 스킬 등록
3. 이 README 테이블에 추가

### 스킬 업데이트

- input/output 계약 호환성 유지
- 호환성 깨지는 변경은 버전 노트 추가
