# STEP PMI Reader Agent

STEP AP242 파일에서 PMI(Product Manufacturing Information) 추출 에이전트

## Quick Start

```bash
cd agents/step-pmi-reader
uv sync
uv run pytest tests/
```

## Usage

```python
from src.step_pmi_reader_agent import StepPmiReaderAgent

agent = StepPmiReaderAgent()
result = agent.process("part.stp")

print(result["data"]["datums"])              # 데이텀 정보
print(result["data"]["geometric_tolerances"]) # GD&T
print(result["data"]["dimensional_tolerances"]) # 치수 공차
print(result["data"]["surface_finishes"])    # 표면 거칠기
```

## Examples

예제 스크립트는 `examples/` 디렉토리에 있습니다:

| Script | Description |
|--------|-------------|
| `01_basic_usage.py` | 기본 사용법 - 파일 로드, PMI 추출, 결과 출력 |
| `02_json_export.py` | JSON 내보내기 3가지 방법 비교 |
| `03_batch_processing.py` | 여러 파일 병렬 처리 + 리포트 생성 |
| `04_pmi_analysis.py` | PMI 분석 - 제조 난이도 평가, 권장사항 |
| `05_inline_step_content.py` | 인라인 STEP 콘텐츠 처리 (API 연동용) |

```bash
# 예제 실행
uv run python examples/01_basic_usage.py
uv run python examples/04_pmi_analysis.py
```

## JSON Export

PMI 데이터를 JSON 파일로 내보내거나 JSON 문자열로 반환할 수 있습니다.

### 방법 1: process()에서 직접 저장

```python
# JSON 파일로 저장하면서 결과 반환
result = agent.process("part.stp", output_json="pmi_output.json")
print(result["output_file"])  # 저장된 파일 경로
```

### 방법 2: extract_pmi_json() 사용

```python
# JSON 파일로 저장
result = agent.extract_pmi_json("part.stp", output_path="pmi.json")

# JSON 문자열로 반환 (파일 저장 없음)
result = agent.extract_pmi_json("part.stp")
json_str = result["json"]  # JSON 문자열
```

### 방법 3: PMIData 객체 직접 사용

```python
# PMIData 객체 획득
pmi_data = agent.get_pmi_data("part.stp")

# JSON 문자열 변환
json_str = pmi_data.to_json(indent=2)

# 파일 저장
pmi_data.save_json("output/pmi.json")

# dict 변환 (API 응답용)
pmi_dict = pmi_data.to_dict()
```

## Supported PMI Types

### Datum Features
- DATUM, DATUM_FEATURE, DATUM_TARGET, DATUM_REFERENCE

### Geometric Tolerances (GD&T)
| Type | Description |
|------|-------------|
| POSITION | 위치도 |
| FLATNESS | 평면도 |
| PERPENDICULARITY | 직각도 |
| PARALLELISM | 평행도 |
| CONCENTRICITY | 동심도 |
| SYMMETRY | 대칭도 |
| CYLINDRICITY | 원통도 |
| CIRCULARITY | 진원도 |
| STRAIGHTNESS | 진직도 |
| SURFACE_PROFILE | 면의 윤곽도 |
| LINE_PROFILE | 선의 윤곽도 |
| ANGULARITY | 경사도 |
| RUNOUT | 원주 흔들림 |
| TOTAL_RUNOUT | 온 흔들림 |

### Dimensional Tolerances
- LINEAR_DIMENSION, DIMENSIONAL_SIZE
- ANGULAR_DIMENSION
- RADIAL_DIMENSION, DIAMETER_DIMENSION
- PLUS_MINUS_TOLERANCE

### Surface Finish
- SURFACE_ROUGHNESS (Ra)
- SURFACE_TEXTURE_PARAMETER
- MACHINING_ALLOWANCE

## Sample Files

`samples/` 디렉토리에 테스트용 샘플 파일이 있습니다:

| File | Description |
|------|-------------|
| `sample_ap242_pmi.stp` | 전체 PMI 포함 (datum, GD&T, 치수, 표면) |
| `sample_ap214.stp` | AP214 스키마 (PMI 없음) |
| `sample_minimal_pmi.stp` | 최소 PMI (datum 1개, tolerance 1개) |
| `sample_complex_gdt.stp` | 복잡한 GD&T (모든 tolerance 타입) |

## Output Format

```json
{
  "status": "success",
  "data": {
    "file_name": "part.stp",
    "schema": "AP242",
    "summary": {
      "datum_count": 3,
      "geometric_tolerance_count": 8,
      "dimensional_tolerance_count": 5,
      "surface_finish_count": 2,
      "annotation_count": 1
    },
    "datums": [
      {"id": "#100", "label": "A", "referenced_geometry": null}
    ],
    "geometric_tolerances": [
      {
        "id": "#200",
        "tolerance_type": "POSITION",
        "tolerance_value": 0.05,
        "unit": "mm",
        "datum_references": ["#100", "#101"],
        "modified_geometry": null
      }
    ],
    "dimensional_tolerances": [
      {
        "id": "#300",
        "dimension_type": "LINEAR",
        "nominal_value": 100.0,
        "upper_limit": 0.1,
        "lower_limit": -0.05,
        "unit": "mm"
      }
    ],
    "surface_finishes": [
      {"id": "#400", "roughness_value": 1.6, "unit": "um", "method": null}
    ],
    "annotations": [
      {"id": "#500", "type": "ANNOTATION_OCCURRENCE", "data": "..."}
    ]
  }
}
```

## Testing

```bash
# 전체 테스트 (66개)
uv run pytest tests/ -v

# 커버리지 포함
uv run pytest tests/ --cov=src

# 특정 테스트 클래스만
uv run pytest tests/ -k "TestParserMethods" -v
```

### Test Categories

- `TestStepPmiReaderInit` - 에이전트 초기화
- `TestStepPmiReaderProcess` - PMI 추출 기본
- `TestDifferentSamples` - 다양한 샘플 파일
- `TestStepPmiReaderEdgeCases` - 엣지 케이스
- `TestDataClasses` - 데이터 클래스
- `TestPMIDataStructure` - PMIData 구조
- `TestJsonExport` - JSON 내보내기
- `TestSchemaDetection` - 스키마 감지
- `TestParserMethods` - 개별 파서 메서드
- `TestErrorHandling` - 에러 처리

## Limitations

- 현재 텍스트 기반 파싱 (정규식)
- 복잡한 참조 해석 제한적
- Part21 형식만 지원 (XML 미지원)
- 멀티라인 엔티티 파싱 제한적

## Roadmap

- [ ] 실제 STEP 파서 라이브러리 연동 (OCC/pythonocc)
- [ ] AP242 Edition 2 지원
- [ ] 3D Annotation 추출
- [ ] PMI-Geometry 연결 관계 추출
