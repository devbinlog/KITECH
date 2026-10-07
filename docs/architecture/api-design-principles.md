# API Design Principles — Library Agent Services

> 적용 대상: 본 워크스페이스의 모든 library-agent 서비스 (gcode-parser, cam-runner,
> step-pmi-reader, monitoring-data-replayer, cell-schedule-visualizer, torus-mock).
> 기존 cell-mes / nl-router / scheduler / dtp는 점진적으로 본 원칙에 정합화 권고.

본 문서는 미래 **agent-orchestrator-centric 아키텍처 전환**을 매끄럽게 하기 위한
설계 원칙을 정의합니다. 모든 endpoint는 LLM tool-calling 친화적이어야 합니다.

## 1. Idempotency First

같은 입력에 같은 출력. 부작용 0.

```python
# ✅ Good
@router.post("/parse", dependencies=[Depends(require_internal)])
async def parse(req: ParseRequest) -> ParseResponse:
    """Parse G-code to block-level analysis. Idempotent."""
    return parser.parse(req.gcode)

# ❌ Bad — global counter mutation
_counter = 0
@router.post("/parse")
async def parse(req: ParseRequest) -> ParseResponse:
    global _counter
    _counter += 1   # NO — non-deterministic
    ...
```

부작용이 본질적으로 필요한 경우(예: file write):
- 입력에 식별자(예: `request_id`, `output_filename`) 포함 → 같은 식별자 재호출 시 같은 결과
- 또는 응답에 결과의 stable hash 포함

## 2. Pydantic Schemas

모든 input/output은 Pydantic v2 BaseModel.

```python
from pydantic import BaseModel, Field

class ParseRequest(BaseModel):
    """Input for /parse.

    Attributes:
        gcode: Raw G-code text (UTF-8). Multi-line OK.
        machine: Optional machine name to scope dialect parsing.
    """
    gcode: str = Field(..., min_length=1, description="Raw G-code text")
    machine: Optional[str] = Field(None, description="Optional machine name for dialect")

class ParseResponse(BaseModel):
    blocks: List[Block]
    total_distance_mm: float
    machine_time_sec: float
```

이유:
- LLM이 OpenAPI schema를 읽고 자동으로 tool descriptor 생성
- Validation은 자동 (pydantic이 처리)
- IDE/타입 체커 친화적

## 3. Standard Error Envelope

성공: 도메인 응답 그대로 (예: ParseResponse).

실패: 일관된 envelope로 감싸기.

```json
{
  "error": {
    "code": "invalid_gcode",
    "message": "Block 12 has malformed G command",
    "hint": "Check for missing arguments or unknown G-codes."
  }
}
```

`code`: machine-readable identifier (snake_case)
`message`: human-readable description
`hint`: optional remediation suggestion (LLM이 이 hint를 보고 다음 행동 결정 가능)

`shared.common.service_base.error_envelope(...)` 헬퍼 사용.

## 4. Rich Docstrings (LLM Tool 친화)

모든 endpoint 함수에 docstring 필수. LLM이 tool 설명을 추출.

```python
@router.post("/analyze", dependencies=[Depends(require_internal)])
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Calculate cycle time + Ap/Ae for a CAM toolpath.

    Use this when you have parsed G-code and need to estimate machining
    duration. Idempotent — same input always yields same output.

    Returns the per-block cycle time (seconds), total distance (mm), and
    Ap (axial) / Ae (radial) engagement parameters. Use these for
    capacity planning or scheduler input.
    """
    ...
```

## 5. Versioning

URL prefix `/api/v1/`. 호환되지 않는 변경 시 `/api/v2/`로 새 endpoint 신설.

기존 endpoint 즉시 삭제 금지 — 최소 1 cycle (한 달) 동안 양쪽 운영.

## 6. Authentication

모든 도메인 endpoint에 `Depends(require_internal)` 적용. 
`/health`, `/docs`, `/capabilities`는 예외 (read-only 메타데이터).

```python
from shared.common.service_base import require_internal

@router.post("/parse", dependencies=[Depends(require_internal)])
async def parse(req: ParseRequest) -> ParseResponse:
    ...
```

호출자(cell-mes, 미래 orchestrator)는 `X-Internal-Key` 헤더로 auth.

## 7. Tracing

`X-Trace-Id` 헤더 자동 전파됨 (TraceIdMiddleware). 핸들러 안에서 `trace_id`를
명시적으로 다룰 필요 없음. 로깅 시 자동 inclusion.

다만 다른 서비스 호출 시 trace_id 전달 권고:

```python
from shared.common.tracing import get_trace_id

async def call_other(...):
    headers = {
        "X-Internal-Key": os.environ["INTERNAL_SERVICE_KEY"],
        "X-Trace-Id": get_trace_id() or "",
    }
    async with httpx.AsyncClient() as c:
        return await c.post("http://cam-runner:8011/api/v1/analyze", ...)
```

## 8. Capabilities Declaration

모든 서비스는 `/capabilities` endpoint로 자신의 도구를 노출. `make_capability()`
헬퍼 사용.

```python
from shared.common.service_base import create_app, make_capability

CAPABILITIES = [
    make_capability(
        name="parse_gcode",
        description="Parse raw G-code text into structured blocks.",
        path="/api/v1/parse",
        method="POST",
        input_schema_ref="#/components/schemas/ParseRequest",
        idempotent=True,
    ),
]

app = create_app(name="gcode-parser", ..., capabilities=CAPABILITIES)
```

## 9. Logging

모든 핸들러는 `logging` 모듈 사용. `print()` 금지 (DTP 사례 — code-reviewer audit).

```python
import logging
logger = logging.getLogger(__name__)

@router.post("/parse")
async def parse(req: ParseRequest):
    logger.info("parse.start", extra={"gcode_size": len(req.gcode)})
    try:
        result = parser.parse(req.gcode)
    except ValueError as exc:
        logger.warning("parse.invalid_input: %s", exc)
        raise HTTPException(400, str(exc))
    logger.info("parse.done", extra={"blocks": len(result.blocks)})
    return result
```

## 10. Testing

각 서비스는 최소 다음 pytest 커버리지:
- `/health` 200 OK
- `/capabilities` 응답 형식 검증
- 핵심 endpoint 1개 — 정상 입력 → 200, 잘못된 입력 → 400, 인증 없음 → 401, 인증 정합 → 200

`shared.common.service_base.create_app`을 import해서 TestClient 생성.

---

## Quick Reference Checklist (PR 체크)

- [ ] Pydantic 모델로 입출력
- [ ] Idempotent (또는 명시적 식별자)
- [ ] `/health`, `/docs`, `/capabilities` 노출
- [ ] 도메인 endpoint에 `Depends(require_internal)`
- [ ] 풍부한 docstring
- [ ] `error_envelope(...)` 사용
- [ ] `print()` 0건, `logging` 사용
- [ ] X-Trace-Id 미들웨어 (자동)
- [ ] pytest 4종 (health/capabilities/200/401)
