# Development Guidelines Template

> 다른 연구/개발 프로젝트에서 재사용 가능한 개발 가이드라인 템플릿

---

## 1. Package Manager: uv (필수)

Python 프로젝트에서는 반드시 **uv**를 사용합니다.

### 기본 명령어

```bash
# 의존성 동기화
uv sync

# 스크립트 실행
uv run python script.py

# 테스트 실행
uv run pytest tests/ -v

# 린트/포맷
uv run black src/
uv run flake8 src/
```

### uv 사용 이유
- pip 대비 10-100배 빠른 설치 속도
- 정확한 락 파일 관리 (`uv.lock`)
- 가상환경 자동 관리
- 재현 가능한 빌드 환경

### 절대 사용 금지
```bash
# ❌ WRONG
pip install package
pip freeze > requirements.txt

# ✅ CORRECT
uv add package
uv sync
```

---

## 2. 핵심 원칙

### 2.1 Test-Driven Updates

코드 변경 시 반드시 다음 워크플로우를 따릅니다:

```
1. 변경 전 테스트 실행 → 현재 상태 확인
2. 코드 변경
3. 변경 후 테스트 실행 → 변경 검증
4. 포맷 및 린트
5. 커밋
```

### 2.2 테스트 커버리지

- 신규 기능: 최소 80% 커버리지
- 버그 수정: 해당 케이스를 커버하는 테스트 추가
- 리팩토링: 기존 테스트 통과 필수

### 2.3 코드 품질

```bash
# 매 커밋 전 실행
uv run pytest tests/ -v          # 테스트 통과
uv run black src/ --check        # 포맷 확인
uv run flake8 src/               # 린트 확인
```

---

## 3. 코드 변경 워크플로우

### Step 1: 변경 전 상태 확인
```bash
uv run pytest tests/ -v
# 결과: X tests passed, 0 failed
```

### Step 2: 코드 변경
- 최소한의 변경으로 목표 달성
- 불필요한 리팩토링 금지
- 변경 범위 명확히 제한

### Step 3: 변경 검증
```bash
uv run pytest tests/ -v
# 결과: X+N tests passed, 0 failed (N개 신규 테스트)
```

### Step 4: 포맷 및 린트
```bash
uv run black src/
uv run flake8 src/
```

### Step 5: 커밋
```bash
git add -A
git commit -m "feat: Add feature X

- Specific change 1
- Specific change 2

Tests:
- Added N tests for feature X
- All tests passing

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 4. 테스트 작성 가이드

### 4.1 테스트 구조

```
tests/
├── unit/              # 단위 테스트
│   ├── test_models.py
│   └── test_services.py
├── integration/       # 통합 테스트
│   └── test_api.py
├── conftest.py        # 공통 픽스처
└── fixtures/          # 테스트 데이터
    └── sample_data.json
```

### 4.2 테스트 명명 규칙

```python
def test_<function_name>_<scenario>_<expected_result>():
    """
    Given: 초기 상태
    When: 동작 수행
    Then: 예상 결과 검증
    """
    pass
```

예시:
```python
def test_calculate_total_with_discount_returns_discounted_price():
    # Given
    items = [Item(price=100), Item(price=200)]
    discount = 0.1

    # When
    result = calculate_total(items, discount)

    # Then
    assert result == 270  # (100 + 200) * 0.9
```

### 4.3 픽스처 활용

```python
# conftest.py
import pytest

@pytest.fixture
def sample_user():
    return User(id=1, name="Test User")

@pytest.fixture
def db_session():
    session = create_test_session()
    yield session
    session.rollback()
```

### 4.4 비동기 테스트

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == expected_value
```

---

## 5. 코드 스타일

### 5.1 Python

- **Formatter**: Black
- **Linter**: Flake8
- **Line Length**: 100
- **Import Order**: isort

```python
# pyproject.toml
[tool.black]
line-length = 100

[tool.flake8]
max-line-length = 100
exclude = [".venv", "__pycache__"]
```

### 5.2 TypeScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checking**: Strict mode

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "printWidth": 100
}
```

---

## 6. 커밋 메시지 형식

### 형식
```
<type>: <subject>

<body>

Tests:
- <test changes>

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Type 종류
| Type | 설명 |
|------|------|
| feat | 새로운 기능 |
| fix | 버그 수정 |
| refactor | 리팩토링 (기능 변경 없음) |
| test | 테스트 추가/수정 |
| docs | 문서 변경 |
| style | 코드 스타일 변경 |
| chore | 빌드/설정 변경 |

### 예시
```
feat: Add user authentication

- Implement JWT token generation
- Add login/logout endpoints
- Create auth middleware

Tests:
- Added 12 tests for auth module
- All 45 tests passing

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 7. 프로젝트 구조 템플릿

### Python Backend

```
project/
├── src/
│   ├── __init__.py
│   ├── main.py              # 진입점
│   ├── config.py            # 설정
│   ├── models/              # 데이터 모델
│   ├── services/            # 비즈니스 로직
│   ├── api/                 # API 엔드포인트
│   └── utils/               # 유틸리티
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── pyproject.toml
├── uv.lock
└── README.md
```

### Frontend (Next.js)

```
frontend/
├── app/                     # App Router
│   ├── layout.tsx
│   ├── page.tsx
│   └── (routes)/
├── components/              # 재사용 컴포넌트
├── services/                # API 클라이언트
├── types/                   # TypeScript 타입
├── lib/                     # 유틸리티
├── package.json
└── tsconfig.json
```

### Monorepo

```
workspace/
├── apps/
│   ├── backend/
│   └── frontend/
├── packages/
│   └── shared/
├── tests/
│   └── integration/
├── pyproject.toml           # 루트 설정
└── package.json             # 프론트엔드 워크스페이스
```

---

## 8. 환경 설정

### 8.1 환경 변수

```bash
# .env.example (커밋)
DATABASE_URL=postgresql://user:pass@localhost:5432/db
API_KEY=your_api_key_here
DEBUG=false

# .env (커밋 제외)
DATABASE_URL=postgresql://real:credentials@host:5432/prod
```

### 8.2 설정 관리

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 9. 정리 가이드라인

### 9.1 임시 파일 정리

```bash
# 정리 대상
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name ".coverage" -delete
```

### 9.2 정리 스크립트

```bash
#!/bin/bash
# scripts/cleanup.sh

echo "Cleaning up temporary files..."

# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null

# Coverage
rm -rf htmlcov .coverage .coverage.*

# Build artifacts
rm -rf dist build *.egg-info

echo "Cleanup complete!"
```

### 9.3 .gitignore 권장

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.env

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp

# Build
dist/
build/
*.egg-info/

# OS
.DS_Store
Thumbs.db
```

---

## 10. CI/CD 템플릿

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest tests/ -v --cov

      - name: Check formatting
        run: uv run black --check src/

      - name: Run linter
        run: uv run flake8 src/
```

---

## 11. 문서화

### 11.1 코드 문서화

```python
def process_data(data: List[Dict], options: ProcessOptions) -> Result:
    """
    데이터를 처리하고 결과를 반환합니다.

    Args:
        data: 처리할 데이터 목록
        options: 처리 옵션

    Returns:
        처리 결과 객체

    Raises:
        ValidationError: 데이터 유효성 검사 실패 시
        ProcessingError: 처리 중 오류 발생 시

    Example:
        >>> result = process_data([{"id": 1}], ProcessOptions())
        >>> print(result.status)
        'success'
    """
    pass
```

### 11.2 README 구조

```markdown
# Project Name

Brief description of the project.

## Quick Start

```bash
uv sync
uv run python src/main.py
```

## Features

- Feature 1
- Feature 2

## Installation

...

## Usage

...

## Testing

```bash
uv run pytest tests/ -v
```

## Contributing

...

## License

...
```

---

## 12. 보안 가이드라인

### 12.1 민감 정보 관리

- API 키, 비밀번호는 환경 변수 사용
- `.env` 파일 절대 커밋 금지
- 시크릿은 별도 관리 시스템 사용 (예: AWS Secrets Manager)

### 12.2 의존성 보안

```bash
# 취약점 스캔
uv run pip-audit

# 정기 업데이트
uv lock --upgrade
```

### 12.3 코드 보안

- SQL Injection 방지: ORM 파라미터 바인딩 사용
- XSS 방지: 출력 이스케이프
- CSRF 방지: 토큰 검증

---

## 13. 성능 가이드라인

### 13.1 데이터베이스

- N+1 쿼리 방지: `selectinload`, `joinedload` 사용
- 인덱스 활용
- 불필요한 컬럼 제외

### 13.2 API

- 페이지네이션 필수
- 응답 캐싱 고려
- 비동기 처리 활용

### 13.3 프론트엔드

- 이미지 최적화
- 코드 스플리팅
- 메모이제이션

---

## 14. 체크리스트

### 코드 리뷰 전

- [ ] 테스트 통과
- [ ] 린트/포맷 통과
- [ ] 커버리지 유지/향상
- [ ] 문서 업데이트 (필요 시)

### 배포 전

- [ ] 전체 테스트 스위트 통과
- [ ] 환경 변수 설정 확인
- [ ] 마이그레이션 준비 (필요 시)
- [ ] 롤백 계획 수립

### PR 작성

- [ ] 명확한 제목
- [ ] 변경 사항 요약
- [ ] 테스트 방법 기술
- [ ] 스크린샷 첨부 (UI 변경 시)

---

## 15. 프로젝트 시작 가이드

### 새 프로젝트 초기화

```bash
# 1. 프로젝트 디렉토리 생성
mkdir my-project && cd my-project

# 2. uv 초기화
uv init

# 3. 기본 의존성 추가
uv add pytest black flake8

# 4. 개발 의존성 추가
uv add --dev pytest-cov pytest-asyncio

# 5. 디렉토리 구조 생성
mkdir -p src tests/unit tests/integration

# 6. 초기 설정 파일 생성
touch src/__init__.py tests/conftest.py

# 7. Git 초기화
git init
echo ".venv/\n__pycache__/\n.env" > .gitignore

# 8. 첫 커밋
git add -A
git commit -m "chore: Initial project setup"
```

### pyproject.toml 템플릿

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"
dependencies = []

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "flake8>=7.0.0",
]

[tool.black]
line-length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 부록: 빠른 참조

### 자주 사용하는 명령어

| 명령어 | 설명 |
|--------|------|
| `uv sync` | 의존성 동기화 |
| `uv run pytest tests/ -v` | 테스트 실행 |
| `uv run pytest tests/ --cov` | 커버리지 측정 |
| `uv run black src/` | 코드 포맷 |
| `uv run flake8 src/` | 린트 실행 |
| `uv add package` | 패키지 추가 |
| `uv lock --upgrade` | 락 파일 업데이트 |

### 문제 해결

| 문제 | 해결 방법 |
|------|----------|
| 의존성 충돌 | `uv lock --upgrade` 실행 |
| 테스트 실패 | 로그 확인, 픽스처 검토 |
| 린트 오류 | `uv run black src/` 자동 수정 |
| Import 오류 | `uv sync` 재실행 |

---

*이 문서는 프로젝트에 맞게 수정하여 사용하세요.*
