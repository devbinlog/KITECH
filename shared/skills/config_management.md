# Config Management

YAML/JSON 설정 파일 로딩, 검증, 환경변수 치환, fallback 기본값 처리.

## Critical Rules

1. **YAML은 `yaml.safe_load` 사용** - 임의 코드 실행 방지
2. **필수 필드 누락 시 즉시 에러 반환** - 묵시적 기본값 사용 금지
3. **환경변수 치환은 `${VAR_NAME}` 패턴** - 미설정 시 원본 유지

## Instructions

### Step 1: 파일 포맷 자동 감지 후 로딩

```python
def load_config(file_path, required_fields=None):
    if file_path.endswith((".yaml", ".yml")):
        config = yaml.safe_load(open(file_path))
    elif file_path.endswith(".json"):
        config = json.load(open(file_path))
    else:
        return {"status": "error", "errors": [f"Unsupported format: {file_path}"]}

    if required_fields:
        missing = [f for f in required_fields if f not in config]
        if missing:
            return {"status": "error", "errors": [f"Missing fields: {missing}"]}

    return {"status": "success", "data": {"parsed_config": config}}
```

### Step 2: Pydantic 모델로 검증

```python
from pydantic import BaseModel, ValidationError

class ConfigModel(BaseModel):
    agent_name: str
    timeout_seconds: int = 60
    features: list[str] = []

try:
    validated = ConfigModel(**config)
except ValidationError as e:
    return {"status": "error", "errors": [str(e)]}
```

### Step 3: 환경변수 치환

```python
import os, re

def substitute_env_vars(config, prefix=""):
    pattern = r"\$\{(" + prefix + r"[A-Z0-9_]*)\}"
    def replace_env(match):
        return os.getenv(match.group(1), match.group(0))
    if isinstance(config, dict):
        return {k: substitute_env_vars(v, prefix) for k, v in config.items()}
    elif isinstance(config, str):
        return re.sub(pattern, replace_env, config)
    return config
```

## Examples

**에이전트 초기화:**
```python
class CAMRunnerAgent:
    def __init__(self, config_file="config/cam_runner.yaml"):
        result = load_config(config_file, required_fields=["tool_library"])
        if result["status"] == "error":
            raise ValueError(f"Config error: {result['errors']}")
        self.config = result["data"]["parsed_config"]
```

**기본값 병합:**
```python
defaults = {"timeout": 60, "log_level": "INFO"}
loaded = {"timeout": 30}
merged = {**defaults, **loaded}  # {"timeout": 30, "log_level": "INFO"}
```

**YAML + 환경변수:**
```yaml
agent:
  name: cam-runner
  log_level: ${AGENT_LOG_LEVEL}
  api_key: ${AGENT_API_KEY}
```

**중첩 접근:**
```python
def get_nested(config, path):
    keys = path.split(".")
    value = config
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value

timeout = get_nested(config, "agent.timeout_seconds")
```

---

## 환경변수 통합 패턴 (agents-workspace)

### 중앙 설정 파일 구조

```
프로젝트 루트/
├── .env.example     # 템플릿 (커밋 O)
├── .env.dev         # 개발 환경 (커밋 O)
├── .env.prod        # 운영 환경 (커밋 X 권장)
└── shared/config/   # 공통 설정 모듈
    ├── base.py      # BaseAppSettings
    └── services.py  # ServiceURLs
```

### Pydantic Settings 기반 설정

```python
# shared/config/base.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseAppSettings(BaseSettings):
    """모든 서비스의 기본 설정."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 알 수 없는 환경변수 무시
    )
    
    # 환경
    ENV: str = "development"
    DEBUG: bool = False
    
    # 서비스 URL
    CELL_MES_URL: str = "http://localhost:8000"
    NL_ROUTER_URL: str = "http://localhost:8001"
    CELL_SCHEDULER_URL: str = "http://localhost:8002"
    REDIS_URL: str = "redis://localhost:6379"
    
    # 인증
    SECRET_KEY: str = "change-in-production"
    INTERNAL_SERVICE_KEY: str = "change-in-production"
    
    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"
```

### 환경별 설정 파일 로드

```python
import os

def get_env_file() -> str:
    """ENV 환경변수에 따라 설정 파일 결정."""
    if env_file := os.getenv("ENV_FILE"):
        return env_file
    
    env = os.getenv("ENV", "development").lower()
    if env == "production":
        return ".env.prod"
    return ".env.dev"

settings = Settings(_env_file=get_env_file())
```

### CORS Origins 처리 (문자열 → 리스트)

```python
from pydantic import field_validator

class Settings(BaseSettings):
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            return ",".join(v)
        return v
    
    def get_cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]
```

### 서비스 URL 헬퍼

```python
# shared/config/services.py
from dataclasses import dataclass
from functools import lru_cache

@dataclass
class ServiceURLs:
    cell_mes: str = "http://localhost:8000"
    nl_router: str = "http://localhost:8001"
    cell_scheduler: str = "http://localhost:8002"
    
    def get_mes_api_url(self, path: str = "") -> str:
        base = self.cell_mes.rstrip("/")
        return f"{base}/{path.lstrip('/')}" if path else base

@lru_cache()
def get_service_urls() -> ServiceURLs:
    return ServiceURLs(
        cell_mes=os.getenv("CELL_MES_URL", "http://localhost:8000"),
        nl_router=os.getenv("NL_ROUTER_URL", "http://localhost:8001"),
        cell_scheduler=os.getenv("CELL_SCHEDULER_URL", "http://localhost:8002"),
    )
```

### 환경변수 주요 항목

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ENV` | 환경 (development/production) | development |
| `CELL_MES_URL` | MES 서비스 URL | http://localhost:8000 |
| `REDIS_URL` | Redis 연결 URL | redis://localhost:6379 |
| `DATABASE_URL` | DB 연결 URL | sqlite+aiosqlite:///./data/mes.db |
| `INTERNAL_SERVICE_KEY` | 내부 서비스 인증 키 | (변경 필수) |
| `CORS_ORIGINS` | 허용 Origin (쉼표 구분) | http://localhost:3000 |

## 관련 스킬

- [service_management.md](service_management.md) - 서비스 관리
- [ddd_patterns.md](ddd_patterns.md) - DDD 설정 패턴
