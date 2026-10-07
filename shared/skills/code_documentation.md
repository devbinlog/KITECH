# Code Documentation

Google/NumPy 스타일 docstring, 함수 시그니처, 파라미터, 리턴 타입, 사용 예시 작성.

## Critical Rules

1. **Google 스타일 사용** - 프로젝트 전체 통일
2. **Args, Returns, Raises 필수** - public 함수에 모두 포함
3. **실행 가능한 예시** - 의사 코드가 아닌 실제 동작하는 코드
4. **타입 힌트 필수** - Python type annotation 항상 포함

## Instructions

### 함수 Docstring (Google Style)

```python
def analyze_gcode(
    gcode_text: str,
    encoding: str = "utf-8",
    coordinate_system: str = "absolute"
) -> AnalysisResult:
    """Parses G-code and extracts block-level metrics.

    Args:
        gcode_text: Raw G-code as string or file path.
        encoding: Character encoding. Default: "utf-8".
        coordinate_system: "absolute" or "incremental". Default: "absolute".

    Returns:
        AnalysisResult with:
        - data.blocks: List of GcodeBlock objects
        - data.total_distance: Sum of motion distances (mm)
        - data.max_Ap: Maximum axial depth of cut (mm)

    Raises:
        FileNotFoundError: If file path doesn't exist.
        ValueError: If no valid G-code blocks found.

    Example:
        >>> result = analyze_gcode("G00 X10 Y20\\nG01 Z-5 F100")
        >>> result.status
        'success'
        >>> len(result.data["blocks"])
        2
    """
```

### 클래스 Docstring

```python
class CAMRunnerAgent(BaseAgent):
    """Analyzes cutting tool paths and calculates engagement metrics.

    Attributes:
        tool_library: Cutter definitions keyed by tool ID.
        advanced_mode: If True, use OpenCAMLib for stock-aware analysis.

    Example:
        >>> agent = CAMRunnerAgent()
        >>> result = agent.execute({"blocks": [...], "tool": {...}})
    """
```

### 모듈 Docstring

```python
"""G-Code Analysis Agent

G-code 파싱 및 블록 단위 분석 모듈.
- GcodeParser: 코어 파싱 로직
- GcodeBlock: 개별 블록 데이터
- AnalysisResult: 표준 출력 포맷
"""
```

## Best Practices

1. **1-2문장 설명** - 디테일은 Notes 섹션으로
2. **실제 코드 예시** - doctest로 실행 가능해야 함
3. **관련 함수 참조** - See Also 사용
4. **버전 추적** - `Added in v2.1`, `Deprecated since v2.0`

## Docstring 검증

```bash
uv run ruff check --select=D agents/    # docstring 누락 체크
```
