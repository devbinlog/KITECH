# Cell-MES 품질 검사 데이터 연동 설계 구현 계획

> 작성일: 2026-05-19  
> 대상 시스템: Cell-MES (FastAPI + Next.js 14)  
> 목적: 검사 결과 자동 수집 및 Unit 단위 매칭 아키텍처 구현

---

## 1. 현황 분석

### 1.1 현재 구현된 품질 관리 구조

Cell-MES는 품질 관리 도메인으로 5개의 주요 화면과 API가 이미 구현되어 있다.

#### API 엔드포인트 현황

| 엔드포인트 | 메서드 | 역할 |
|-----------|--------|------|
| `/api/v1/quality/inspection-plans` | GET / POST | 검사 계획 목록 조회 / 생성 |
| `/api/v1/quality/inspection-plans/{plan_id}` | PUT / DELETE | 검사 계획 수정 / 삭제 |
| `/api/v1/quality/inspection-results` | GET / POST | 측정 결과 목록 조회 / 등록 |
| `/api/v1/quality/inspection-results/batch` | POST | 측정 결과 배치 등록 |
| `/api/v1/quality/ncr` | GET / POST | 부적합 보고서 목록 / 생성 |
| `/api/v1/quality/ncr/{ncr_id}` | PUT | 부적합 보고서 수정 |
| `/api/v1/quality/ncr/{ncr_id}/status` | PATCH | 부적합 상태 변경 |
| `/api/v1/quality/spc/charts/{characteristic}` | GET | SPC 차트 및 데이터 조회 |
| `/api/v1/quality/spc/capability` | GET | Cp/Cpk 공정 능력 분석 |
| `/api/v1/quality/traceability/{serial_no}` | GET | 시리얼 번호별 추적성 조회 |
| `/api/v1/quality/dashboard/summary` | GET | 품질 지표 대시보드 요약 |

#### 프론트엔드 화면 현황

| 화면 경로 | 구성 요소 |
|-----------|-----------|
| `/quality` | 대시보드: KPI 카드, 품질 추이 차트, 불량 유형 분포, 미해결 NCR |
| `/quality/inspection-plans` | 검사 계획 목록, 생성/수정/삭제 모달 |
| `/quality/inspection-results` | 측정 결과 목록, 등록 모달 (작업지시 선택 방식) |
| `/quality/spc` | SPC 관리도 시각화 (X-bar, R 차트) |
| `/quality/ncr` | 부적합 보고서 목록, 상태 관리 |

---

### 1.2 현재 데이터 연결 구조

```
WorkOrder (작업지시)
├── Unit (Unit 단위 분산 생산)
│   └── ProdResult (공정 실적)
│
└── InspectionResult (검사 결과)        ← 문제 지점
    ├── inspection_plan_id (검사 계획)
    ├── work_order_id (작업지시)         ← LOT 레벨 연결만 존재
    ├── lot_no (LOT 번호)
    ├── serial_no (시리얼 번호, 선택)
    └── unit_id 없음                     ← Unit 연결 부재
```

#### 문제 상황 예시

```
WorkOrder: LOT-2026-001 (target_qty=5)
├── Unit 1 (id=10, unit_no=1, status=DONE)
├── Unit 2 (id=11, unit_no=2, status=DONE)
├── Unit 3 (id=12, unit_no=3, status=DONE)
├── Unit 4 (id=13, unit_no=4, status=DONE)
└── Unit 5 (id=14, unit_no=5, status=RUNNING)

InspectionResult (id=100)
├── work_order_id → LOT-2026-001 (5개 Unit 전체를 가리킴)
├── lot_no = "LOT-2026-001"
├── serial_no = NULL
└── unit_id = 없음 (컬럼 자체 미존재)

→ 이 검사 결과가 어떤 Unit(부품)의 것인지 특정 불가
```

---

### 1.3 현재 화면에서의 데이터 출력 방식

#### 측정 결과 등록 화면 (`/quality/inspection-results`)

현재 등록 모달의 입력 흐름:

```
1. 검사 계획 선택 (inspection_plan_id)
2. 작업지시 선택 (work_order_id)
   └── lot_no 자동 채우기 (WorkOrder에서 가져옴)
3. 검사자명, 검사일시 입력
4. 측정값 입력 (각 항목별)
→ POST /api/v1/quality/inspection-results
  payload: { inspection_plan_id, work_order_id, measured_value, ... }
  ← unit_id 없음
```

#### 측정 결과 목록 화면 컬럼 구성

| 컬럼 | 데이터 소스 | 비고 |
|------|-------------|------|
| Lot No | WorkOrder.lot_no | 작업지시 번호 |
| 제품명 | InspectionPlan → Product.name | 간접 조회 |
| 검사계획 | InspectionPlan.characteristic | 검사 항목명 |
| 검사일시 | InspectionResult.measured_at | |
| 검사자 | measurement_metadata.inspector | JSON 필드 |
| 판정 | InspectionResult.is_conforming | OK/NG 배지 |

**현재 없는 컬럼:** Unit 번호, 시리얼 번호 — Unit 단위 추적 불가

#### 품질 대시보드 KPI 출력 방식

```
GET /api/v1/quality/dashboard/summary
└── 반환:
    ├── total_inspections: 전체 검사 건수
    ├── conforming_inspections: 합격 건수
    ├── quality_rate_percent: 합격률 (%)
    ├── open_ncrs: 미해결 NCR 건수
    └── active_spc_charts: 활성 SPC 차트 수
```

현재 대시보드는 LOT 단위 집계만 가능하며, Unit 단위 불량률 추적이 불가능하다.

---

## 2. 문제점 정의

### 2.1 구조적 문제

| 문제 | 영향 | 심각도 |
|------|------|--------|
| InspectionResult에 unit_id 없음 | Unit 단위 품질 추적 불가 | 높음 |
| 검사 결과 수동 입력 구조 | 입력 오류, 지연 발생 | 높음 |
| 측정 장비 파일과 MES 미연동 | 자동화 불가 | 높음 |
| 고정 파일명 장비 대응 방법 없음 | 중복 처리 위험 | 중간 |
| Unit 선택 UI 없음 | 수동 등록 시에도 Unit 특정 불가 | 중간 |

### 2.2 Unit 생산 방식과의 불일치

Cell-MES는 **Lot-Size 1 아키텍처**로 동작한다. 미들웨어는 `GET /orders/ready-units`로 Unit을 한 개씩 가져가서 개별 가공을 수행한다. 그러나 품질 결과는 여전히 LOT 전체(`work_order_id`)에 귀속되어 있어 "LOT 내 어떤 부품이 불량인가"를 특정할 수 없다.

---

## 3. 개선 방안

### 3.1 Phase 1: DB 스키마 수정 (즉시 적용)

**원칙: 변경 최소화 — Unit 모델 수정 없이 InspectionResult에만 unit_id 추가**

#### 3.1.1 모델 변경 (`models/quality.py`)

```python
class InspectionResult(Base):
    # 기존 필드 유지
    work_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("work_orders.id"), nullable=False)
    lot_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 추가: Unit 직접 연결
    unit_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("units.id"), nullable=True, index=True
    )
    
    # 추가: Relationship
    unit: Mapped[Optional["Unit"]] = relationship("Unit")
```

- `nullable=True`: LOT 레벨 등록 하위 호환 유지
- 인덱스 추가로 `unit_id` 기반 조회 성능 확보

#### 3.1.2 스키마 변경 (`schemas/quality.py`)

```python
class InspectionResultBase(BaseModel):
    # 기존 필드 유지
    work_order_id: int
    inspection_plan_id: int
    measured_value: float
    
    # 추가
    unit_id: Optional[int] = Field(None, description="Unit ID (Lot-Size 1 추적용)")
```

응답 스키마에 Unit 정보 임베드:

```python
class _UnitEmbedded(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    unit_no: int
    status: str

class InspectionResultResponse(InspectionResultBase):
    # 기존 필드 유지
    unit: Optional[_UnitEmbedded] = None   # 추가
```

#### 3.1.3 Alembic 마이그레이션 (`alembic/versions/007_add_unit_id_to_inspection_results.py`)

```python
def upgrade() -> None:
    op.add_column(
        "inspection_results",
        sa.Column("unit_id", sa.BigInteger(), nullable=True)
    )
    op.create_foreign_key(
        "fk_inspection_results_unit_id",
        "inspection_results", "units",
        ["unit_id"], ["id"]
    )
    op.create_index(
        "ix_inspection_results_unit_id",
        "inspection_results", ["unit_id"]
    )

def downgrade() -> None:
    op.drop_index("ix_inspection_results_unit_id")
    op.drop_constraint("fk_inspection_results_unit_id", "inspection_results")
    op.drop_column("inspection_results", "unit_id")
```

---

### 3.2 Phase 2: API 로직 개선 (단기)

#### 3.2.1 검사 결과 등록 API 변경 (`api/v1/endpoints/quality.py`)

`unit_id` 입력 시 `work_order_id`와 `lot_no`를 자동으로 채우는 로직 추가:

```
입력 처리 우선순위:
1순위: unit_id 입력
   → Unit 조회
   → work_order_id = unit.work_order_id (자동 채움)
   → lot_no = work_order.lot_no (자동 채움)

2순위: work_order_id만 입력 (기존 방식 유지)
   → unit_id = None으로 LOT 레벨 등록

방어 로직:
- unit_id와 work_order_id 불일치 → 400 에러
- 존재하지 않는 unit_id → 404 에러
```

#### 3.2.2 검사 결과 조회 API에 unit_id 필터 추가

```python
@router.get("/inspection-results")
async def get_inspection_results(
    work_order_id: Optional[int] = None,
    inspection_plan_id: Optional[int] = None,
    serial_no: Optional[str] = None,
    unit_id: Optional[int] = None,    # 추가
    ...
)
```

---

### 3.3 Phase 3: 프론트엔드 화면 개선 (단기)

#### 3.3.1 측정 결과 등록 모달 개선

현재 입력 흐름 변경:

```
[현재]
작업지시 선택 → lot_no 자동 채우기 → 측정값 입력

[개선 후]
작업지시 선택 → Unit 선택 (선택사항)
                ├── Unit 선택 시: unit_no 표시, lot_no 자동 채우기
                └── Unit 미선택 시: LOT 레벨 등록 (기존 방식)
→ 측정값 입력
```

Unit 선택 드롭다운 구성:
```
작업지시 선택 후, 해당 WO의 DONE/RUNNING Unit 목록 표시
예: "Unit 1 (완료)", "Unit 2 (완료)", "Unit 3 (진행중)"
```

#### 3.3.2 측정 결과 목록 컬럼 추가

| 기존 컬럼 | 추가 컬럼 |
|-----------|-----------|
| Lot No | Unit 번호 (unit.unit_no) |
| 제품명 | - |
| 검사계획 | - |
| 검사일시 | - |
| 검사자 | - |
| 판정 | - |

Unit 정보가 없는 결과(LOT 레벨)는 "-"로 표시.

#### 3.3.3 작업지시 상세 화면에 품질 탭 추가

작업지시 상세 페이지(`/production/orders/{id}`)에 품질 탭을 추가하여 해당 WO의 Unit별 검사 결과를 한눈에 확인:

```
작업지시 상세 > [기본정보] [Unit 현황] [품질 결과] ← 추가

품질 결과 탭:
├── Unit 1: OK (외경 φ50.02mm / 규격 φ50±0.1)
├── Unit 2: OK (외경 φ49.98mm)
├── Unit 3: NG (외경 φ50.15mm → NCR-20260519-001 자동 생성)
├── Unit 4: 미검사
└── Unit 5: 미검사
```

---

### 3.4 Phase 4: 파일 자동 수집 아키텍처 (중기)

#### 3.4.1 배경

실제 가공 환경에서 측정 장비(CMM, Equator, 표면조도계 등)는 결과를 파일로 출력한다. 현재는 작업자가 파일을 보고 MES에 수동 입력하는 구조이므로 자동 수집 체계가 필요하다.

#### 3.4.2 공유 폴더 구조

```
/mes-data/
├── incoming/           ← 장비가 결과 파일을 출력하는 폴더
│   ├── equator/        ← Equator 전용
│   ├── cmm/            ← CMM 전용
│   └── manual/         ← 기타 장비
├── processed/          ← 처리 완료된 파일 이동
└── failed/             ← 매칭 실패 파일 격리
```

#### 3.4.3 File Watcher 처리 흐름

```
장비 파일 출력 → /incoming/equator/result.csv
      ↓
File Watcher 감지 (watchdog 라이브러리)
      ↓
SHA-256 해시 계산 → 기처리 여부 확인
      ↓
장비 어댑터로 파일 파싱 (MeasurementData 추출)
      ↓
Unit 매칭 수행 (아래 매칭 전략 참조)
      ↓
성공: POST /api/v1/quality/inspection-results (unit_id 포함)
      ↓
파일 이동: /incoming/ → /processed/
```

매칭 실패 시:
```
파일 이동: /incoming/ → /failed/
Alarm 테이블 기록
운영자에게 수동 매칭 UI 제공
```

#### 3.4.4 Unit 매칭 전략 (우선순위 순)

| 순위 | 매칭 기준 | 신뢰도 |
|------|-----------|--------|
| 1순위 | 파일 내 unit_id 직접 포함 | 최고 |
| 2순위 | 파일 내 lot_no + unit_no 포함 | 높음 |
| 3순위 | 파일 내 lot_no만 → 해당 WO의 RUNNING Unit 추론 | 중간 |
| 4순위 | 장비 ID + 시간 → 해당 장비 진행 중 Unit 추론 | 낮음 |

#### 3.4.5 장비 내부 저장소 접근 방법

Equator 등 Windows 기반 측정 장비는 결과를 내부 PC의 로컬 디스크에 저장한다. MES(Linux/Docker)가 이를 접근하는 방법:

| 방법 | 설명 | 권장 여부 |
|------|------|-----------|
| SMB/CIFS 마운트 | 장비 PC의 공유 폴더를 Linux에 마운트, Docker는 bind mount로 접근 | 권장 |
| Organiser 자동 내보내기 | Renishaw Organiser의 결과 저장 경로를 MES 공유 폴더로 설정 | 권장 |
| 경량 Agent | 장비 PC에 Python watchdog 스크립트 설치, MES API로 HTTP Push | 네트워크 공유 불가 시 |
| FTP 폴링 | 장비 PC에 FTP 서버 설치, MES가 주기적으로 폴링 | 최후 수단 |

**Docker 컨테이너 환경에서의 SMB 마운트:**
```
[장비 PC - Windows]  → SMB 공유 설정
      ↓
[MES 호스트 OS - Linux]  → cifs 마운트 (/mnt/equator-results/)
      ↓
[Docker Container]  → bind mount (volumes: /mnt/equator-results:/mes-data/equator-raw)
```

> **참고:** cifs 마운트는 컨테이너 환경과 무관한 Linux의 일반적인 Windows 공유 폴더 접근 방법이다. 컨테이너는 호스트 OS가 마운트한 경로를 일반 로컬 폴더처럼 인식한다.

#### 3.4.6 고정 파일명 장비 대응

일부 장비는 항상 동일한 파일명(`result.csv`, `output.txt`)으로 덮어쓰기 방식으로 저장한다. 이 경우:

```
권장 조합: SHA-256 해시 비교 + 폴더 분리

1. SHA-256 해시 비교:
   - 파일 처리 시 해시값을 DB에 기록
   - 동일 해시 파일은 재처리 방지

2. 폴더 분리:
   - 장비별 전용 폴더 구성
   - 처리 즉시 /processed/로 이동
   → 새 파일과 처리 완료 파일이 겹치지 않음
```

#### 3.4.7 장비 어댑터 패턴

새 장비 추가 시 어댑터만 추가하고 핵심 로직은 변경하지 않는 설계.  
어댑터는 장비 고유 포맷을 파싱하여 공통 `MeasurementData` 리스트로 변환한다.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MeasurementData:
    """어댑터가 공통으로 반환하는 측정 결과 단위."""
    feature_id: str          # InspectionFeatureMapping 조회 키
    actual: float            # 실측값
    nominal: float           # 기준값
    lo_tol: Optional[float]  # 하한 공차 (없으면 None — 형상 공차류)
    hi_tol: Optional[float]  # 상한 공차
    deviation: Optional[float]
    is_conforming: bool      # 장비가 판정한 합불 (없으면 actual/nominal/tol로 계산)

class BaseAdapter:
    device_type: str  # 서브클래스에서 지정

    def parse(self, file_path: str) -> list[MeasurementData]:
        raise NotImplementedError
```

##### OMMJsonAdapter (OMM — JSON)

실제 파일 구조 (`drilljig_result_3.json`):
```json
{
  "GDT_measurement": {
    "3d_model_ID": "TEST",
    "gdt_result": [
      { "geometric_tolerance": "PARALLELISM_TOLERANCE1", "gdt_result": 95.309 },
      { "geometric_tolerance": "DIMENSIONAL_LOCATIONA1", "gdt_result": 44.0 },
      { "geometric_tolerance": "DIMENSIONAL_SIZE1",      "gdt_result": 20.01 },
      { "geometric_tolerance": "DIMENSIONAL_LOCATIONA2", "gdt_result": 26.248 }
    ]
  }
}
```

- `geometric_tolerance` 값이 곧 `feature_id` — PMI 어노테이션 ID와 동일
- 합불 판정값 없음 → `InspectionPlan.lsl` / `usl`과 비교해서 계산
- 좌표 데이터(`gdt_point_coordinate`, `gdt_point_measurement`)는 `measurement_metadata`에 저장

```python
class OMMJsonAdapter(BaseAdapter):
    device_type = "OMM"

    def parse(self, file_path: str) -> list[MeasurementData]:
        import json
        with open(file_path) as f:
            data = json.load(f)
        results = []
        for item in data["GDT_measurement"]["gdt_result"]:
            results.append(MeasurementData(
                feature_id    = item["geometric_tolerance"],
                actual        = float(item["gdt_result"]),
                nominal       = None,   # InspectionPlan에서 조회
                lo_tol        = None,
                hi_tol        = None,
                deviation     = None,
                is_conforming = None,   # InspectionPlan lsl/usl 비교 후 결정
            ))
        return results
```

##### EquatorRTFAdapter (EQUATOR — RTF)

실제 파일 구조 (`test_m.RTF`):
```
(mm)           ACTUAL   NOMINAL   LO-TOL   HI-TOL  DEVIATION  GRAPHIC
──────────────────────────────────────────────────────────────────────
Plane:PLN002                         ← \cf0 (파란색) = feature 참조 라인
Flatness        0.000     0.050                                 *---  ← \cf2 (초록=합격) / \cf3 (빨강=불합격)
Circle:CIR001
Diameter       40.000    40.000    -0.050   +0.050     0.000  ---*---
Point:PNT002--Point:PNT003
Length-Zavg    20.000    20.000    -0.050   +0.050    -0.000  ---*---
Point:PNT004--Point:PNT005
Length_Yavg    43.999    44.000    -0.050   +0.050    -0.001  ---*---
```

- RTF 색상 코드로 합불 판정이 파일에 이미 포함: `\cf2`=합격, `\cf3`=불합격
- feature 참조 라인(`\cf0`)의 ID (`PLN002`, `CIR001`)가 `feature_id` — OMM의 `geometric_tolerance`와 **완전히 다른 네이밍 체계**
- 형상 공차(Flatness 등)는 LO-TOL/HI-TOL 없이 NOMINAL만 존재

```python
import re

class EquatorRTFAdapter(BaseAdapter):
    device_type = "EQUATOR"

    def parse(self, file_path: str) -> list[MeasurementData]:
        with open(file_path, encoding="cp1252") as f:
            content = f.read()

        results = []
        current_feature_ref = None
        line_pattern = re.compile(r'\\(cf[023])\s+(.*?)\\par', re.DOTALL)

        for match in line_pattern.finditer(content):
            cf_tag = match.group(1)
            text   = match.group(2).strip()

            if re.match(r'^[-=]+$', text) or not text:
                continue
            if any(skip in text for skip in ('ACTUAL', 'Duration', 'Start Template')):
                continue

            if cf_tag == 'cf0':
                m = re.match(r'\w+:(\w+)', text)
                if m:
                    current_feature_ref = m.group(1)   # "PLN002", "CIR001"

            elif cf_tag in ('cf2', 'cf3') and current_feature_ref:
                m = re.match(
                    r'([\w\-_]+)\s+([\d.]+)\s+([\d.]+)'
                    r'(?:\s+([-+][\d.]+))?(?:\s+([-+][\d.]+))?'
                    r'(?:\s+([-+]?[\d.]+))?',
                    text,
                )
                if m:
                    actual, nominal = float(m.group(2)), float(m.group(3))
                    lo  = float(m.group(4)) if m.group(4) else None
                    hi  = float(m.group(5)) if m.group(5) else None
                    dev = float(m.group(6)) if m.group(6) else None
                    results.append(MeasurementData(
                        feature_id    = current_feature_ref,
                        actual        = actual,
                        nominal       = nominal,
                        lo_tol        = lo,
                        hi_tol        = hi,
                        deviation     = dev,
                        is_conforming = (cf_tag == 'cf2'),
                    ))
                    current_feature_ref = None

        return results
```

어댑터 설정은 `MeasurementDevice.connection_config` JSON으로 관리:
```json
{
  "adapter": "EquatorRTFAdapter",
  "watch_path": "/mes-data/equator/",
  "file_pattern": "*.RTF"
}
```
```json
{
  "adapter": "OMMJsonAdapter",
  "watch_path": "/mes-data/omm/",
  "file_pattern": "*.json"
}
```

---

### 3.5 InspectionFeatureMapping: 장비별 Feature ID 매핑 테이블

> 2026-05-21 설계 추가

#### 3.5.1 왜 필요한가

`InspectionPlan.feature_id` (단일 문자열)로는 다중 장비 환경을 처리할 수 없다.  
같은 검사 항목이라도 장비마다 고유한 식별자 체계를 사용하기 때문이다:

```
InspectionPlan: "홀A 위치도" (nominal=44.0, lsl=43.95, usl=44.05)
  ↑ 같은 검사 항목인데
  OMM 결과 파일:     "geometric_tolerance": "DIMENSIONAL_LOCATIONA1"
  EQUATOR 결과 파일: feature 참조:          "PNT004"
```

`feature_id = "DIMENSIONAL_LOCATIONA1"` 하나만 저장하면 EQUATOR의 `"PNT004"`를 매칭할 방법이 없다.  
패턴 파싱 (`DIMENSIONAL_LOCATION → "위치도"`) 으로 대체하는 것도 불가능하다 — 같은 제품에 위치도 항목이 여러 개일 경우 어느 형상 요소인지 구분할 수 없기 때문이다.

#### 3.5.2 테이블 설계

```python
class InspectionFeatureMapping(Base):
    """장비 타입별 feature ID → InspectionPlan 매핑."""

    __tablename__ = "inspection_feature_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspection_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspection_plans.id"), nullable=False, index=True
    )
    device_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "OMM", "EQUATOR", "CMM", "MANUAL"

    feature_id: Mapped[str] = mapped_column(String(200), nullable=False)
    # OMM:     "DIMENSIONAL_LOCATIONA1"  (PMI 어노테이션 ID)
    # EQUATOR: "PNT004"                  (Equator 프로그램 내부 이름)
    # CMM:     "LOC_A1"                  (CMM 측정 프로그램 이름)

    __table_args__ = (
        UniqueConstraint("inspection_plan_id", "device_type",
                         name="uq_feature_mapping_plan_device"),
    )

    inspection_plan: Mapped["InspectionPlan"] = relationship("InspectionPlan")
```

#### 3.5.3 데이터 예시

| plan_id | device_type | feature_id |
|---------|-------------|------------|
| 5 | OMM | `DIMENSIONAL_LOCATIONA1` |
| 5 | EQUATOR | `PNT004` |
| 5 | CMM | `LOC_A1` |
| 6 | OMM | `DIMENSIONAL_SIZE1` |
| 6 | EQUATOR | `CIR001` |

#### 3.5.4 매칭 로직

어댑터가 파일을 파싱한 뒤, `InspectionFeatureMapping`을 통해 `InspectionPlan`을 조회한다:

```python
async def resolve_plan(
    db: AsyncSession,
    device_type: str,
    feature_id: str,
    product_id: int,
) -> InspectionPlan | None:
    result = await db.execute(
        select(InspectionFeatureMapping)
        .join(InspectionPlan)
        .where(
            InspectionFeatureMapping.device_type == device_type,
            InspectionFeatureMapping.feature_id  == feature_id,
            InspectionPlan.product_id            == product_id,
        )
    )
    mapping = result.scalar_one_or_none()
    return mapping.inspection_plan if mapping else None
```

매핑이 없으면 → `failed/` 폴더 이동 + Alarm 등록 + 수동 매핑 대기.  
**패턴 기반 fallback 없음** — 매핑 테이블에 등록되지 않은 feature는 처리하지 않는다.

#### 3.5.5 기존 InspectionPlan.feature_id 처리

현재 `InspectionPlan.feature_id` 컬럼은 OMM 전용으로 이미 DB에 존재한다.  
마이그레이션 시 이 값을 `InspectionFeatureMapping`으로 이전한다:

```python
# alembic 마이그레이션 data migration 부분
def upgrade():
    # 1. 테이블 생성
    op.create_table("inspection_feature_mappings", ...)

    # 2. 기존 feature_id 데이터 이전 (OMM 타입으로)
    op.execute("""
        INSERT INTO inspection_feature_mappings (inspection_plan_id, device_type, feature_id)
        SELECT id, 'OMM', feature_id
        FROM inspection_plans
        WHERE feature_id IS NOT NULL
    """)

    # 3. 기존 컬럼 제거 (선택 — 하위 호환 필요 시 유지)
    op.drop_column("inspection_plans", "feature_id")
```

---

## 4. 변경 파일 목록

### Phase 1 (DB 스키마)

| 파일 | 변경 내용 |
|------|-----------|
| `src/app/models/quality.py` | ① InspectionResult에 unit_id FK + relationship 추가, ② InspectionFeatureMapping 모델 추가 |
| `src/app/schemas/quality.py` | InspectionResultBase에 unit_id 필드 추가, 응답에 _UnitEmbedded 추가 |
| `alembic/versions/007_add_unit_id_to_inspection_results.py` | InspectionResult.unit_id 마이그레이션 |
| `alembic/versions/008_add_inspection_feature_mappings.py` | InspectionFeatureMapping 테이블 생성 + 기존 feature_id 데이터 이전 |

### Phase 2 (API 로직)

| 파일 | 변경 내용 |
|------|-----------|
| `src/app/api/v1/endpoints/quality.py` | create_inspection_result: unit_id 입력 시 자동 매핑, get_inspection_results: unit_id 필터 추가 |

### Phase 3 (프론트엔드)

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/app/(main)/quality/inspection-results/page.tsx` | Unit 선택 드롭다운 추가, 목록에 Unit 번호 컬럼 추가 |
| `frontend/services/quality.ts` | unit_id 파라미터 추가 |
| `frontend/app/(main)/production/orders/[id]/page.tsx` | 품질 탭 추가 |

### Phase 4 (File Watcher)

| 파일 | 변경 내용 |
|------|-----------|
| `src/app/services/file_watcher/` | 신규: File Watcher 서비스 디렉토리 |
| `src/app/services/file_watcher/watcher.py` | watchdog 기반 파일 감지 서비스 |
| `src/app/services/file_watcher/adapters/base.py` | BaseAdapter + MeasurementData 공통 인터페이스 |
| `src/app/services/file_watcher/adapters/omm_json.py` | OMMJsonAdapter — JSON `geometric_tolerance` 파싱 |
| `src/app/services/file_watcher/adapters/equator_rtf.py` | EquatorRTFAdapter — RTF `\cf2`/`\cf3` 색상 기반 파싱 |
| `src/app/services/file_watcher/adapters/manual_csv.py` | ManualCSVAdapter (범용 CSV) |
| `src/app/services/file_watcher/feature_resolver.py` | InspectionFeatureMapping 조회 → InspectionPlan 반환 |
| `src/app/services/file_watcher/unit_matcher.py` | Unit 매칭 로직 |
| `src/app/services/file_watcher/device_resolver.py` | MeasurementDevice 실행 시점 라우팅 |
| `alembic/versions/009_add_cell_id_to_measurement_devices.py` | MeasurementDevice.cell_id 추가 (복수 장비 disambiguation) |
| `docker-compose.yml` | file-watcher 서비스 추가 |

---

## 5. 구현 우선순위 및 로드맵

### Phase 1 — 즉시 (리스크 최소)

- [ ] `InspectionResult.unit_id` 컬럼 추가 (Alembic 007)
- [ ] 스키마 업데이트 (unit_id 필드, _UnitEmbedded 응답)
- [ ] API에 unit_id 자동 매핑 로직 추가
- [ ] 기존 동작 하위 호환 확인 (unit_id 없이 등록 시 정상 동작 여부)
- [ ] `InspectionFeatureMapping` 테이블 생성 (Alembic 008)
- [ ] 기존 `InspectionPlan.feature_id` 데이터를 OMM 타입으로 이전

### Phase 2 — 단기 (2~4주)

- [ ] 측정 결과 등록 모달에 Unit 선택 UI 추가
- [ ] 측정 결과 목록에 Unit 번호 컬럼 추가
- [ ] 작업지시 상세에 품질 탭 추가
- [ ] unit_id 기반 필터링 지원

### Phase 3 — 중기 (4~8주)

- [ ] File Watcher 서비스 구현 (ManualCSVAdapter 우선)
- [ ] 공유 폴더 구조 설정
- [ ] SHA-256 해시 기반 중복 처리 방지
- [ ] 매칭 실패 격리 및 알람 연동

### Phase 4 — 장기 (8주 이상)

- [ ] `OMMJsonAdapter` 구현 (`geometric_tolerance` → `feature_id` 직접 매핑)
- [ ] `EquatorRTFAdapter` 구현 (RTF `\cf2`/`\cf3` 색상 파싱)
- [ ] `feature_resolver.py` 구현 (InspectionFeatureMapping 조회)
- [ ] `device_resolver.py` 구현 (MeasurementDevice 실행 시점 라우팅)
- [ ] `MeasurementDevice.cell_id` 추가 (Alembic 009) — 복수 장비 환경 disambiguation
- [ ] 수동 매핑 UI 제공 (feature_id 미등록 항목 처리)
- [ ] SMB 마운트 또는 장비 PC Agent 구성
- [ ] CMM 어댑터 구현
- [ ] 장비 직접 HTTP Push 방식으로 전환 (최종 목표)

---

## 6. 기대 효과

### 품질 데이터 정합성

| 현재 | 개선 후 |
|------|---------|
| LOT 단위 품질 관리 | Unit 단위 품질 추적 |
| "LOT 내 어느 부품이 불량?" 불가 | 불량 Unit 특정 → 재작업 범위 최소화 |
| 수동 입력 오류 위험 | 자동 수집으로 입력 오류 제거 |

### 업무 효율화

- 수동 측정값 입력 작업 제거
- 가공 완료 즉시 자동 검사 결과 연동
- 불량 발생 시 자동 NCR 생성 (기존 기능) + Unit 추적 연계

### 확장성

- 장비 추가 시 어댑터만 추가 (핵심 코드 변경 없음)
- 고정 파일명 / 동적 파일명 장비 모두 대응
- 파일 기반 자동화 → 장비 직접 HTTP Push 방식으로 전환 용이

---

## 7. 측정 장치 라우팅 설계 원칙

> 2026-05-21 분석 추가  
> 참조 문서: `docs/DIGITAL_THREAD_SPC_QMS.md`, `docs/QIF_CONVERTER_DESIGN.md`

### 7.1 왜 InspectionPlan에 device_id가 없는가

`InspectionPlan`에 특정 장비 인스턴스의 FK(`device_id`)가 없는 것은 **의도된 설계**이다.

| 시점 | 알 수 있는 것 | 알 수 없는 것 |
|------|-------------|-------------|
| 검사 계획 수립 (CAD/PMI → STEP 자동 생성) | 어떤 **종류**의 장비가 필요한가 (EQUATOR/CMM/OMM) | **어느 셀**의 **몇 번** 장비인지 |
| 실제 측정 실행 시 | 유닛이 어느 셀에서 가공됐는가 | - |

기존 설계 문서(`DIGITAL_THREAD_SPC_QMS.md`)의 `PMI_TO_INSPECTION_CONFIG` 매핑은 PMI 특성 유형 → `inspection_type` 문자열로 연결한다:

```python
PMI_TO_INSPECTION_CONFIG = {
    "diameter":    {"inspection_type": "OMM"},
    "position":    {"inspection_type": "EQUATOR"},
    "surface":     {"inspection_type": "CMM"},
    "roundness":   {"inspection_type": "EQUATOR"},
}
```

QIF XML 표준 역시 `<DeviceType>Equator</DeviceType>` (타입 문자열)을 사용하며 특정 장비 인스턴스를 지정하지 않는다.

**결론:** `InspectionPlan.inspection_type` (문자열) 이 올바른 추상화 수준이며, 특정 장비 인스턴스 선택은 실행 시점에 수행된다.

---

### 7.2 전체 파이프라인: 장치 라우팅 → 파일 수집 → 검사 항목 매칭

Unit DONE 시점부터 `InspectionResult` 생성까지의 전체 흐름:

```
Unit DONE
  ↓
[1단계: 장치 라우팅] device_resolver.py
  제품의 InspectionPlan 목록에서 사용하는 device_type 목록 추출
  → MeasurementDevice.source_type 으로 장비 조회
  → 단일: 바로 선택 / 복수: cell_id 기반 disambiguation
  → AmbiguousDeviceError → Alarm + 수동 처리
  ↓
[2단계: 파일 수집] watcher.py / FTP / SMB
  MeasurementDevice.connection_config 기반으로 결과 파일 취득
  ↓
[3단계: 파싱] 장비별 어댑터
  OMMJsonAdapter   → geometric_tolerance 값이 feature_id
  EquatorRTFAdapter → PLN002 / CIR001 등이 feature_id
  반환: list[MeasurementData(feature_id, actual, nominal, ...)]
  ↓
[4단계: 검사 항목 매칭] feature_resolver.py
  (device_type, feature_id) → InspectionFeatureMapping → InspectionPlan
  매핑 없음 → failed/ 이동 + Alarm (패턴 fallback 없음)
  ↓
[5단계: 합불 판정 및 결과 저장]
  EquatorRTF: \cf2/\cf3 색상으로 판정 이미 포함
  OMMJson:    InspectionPlan.lsl / usl 과 비교하여 계산
  → POST InspectionResult (unit_id, plan_id, actual, is_conforming, ...)
  ↓
[6단계: NCR 자동 생성]
  is_conforming = False → NonConformance 자동 생성 (기존 로직)
```

`device_resolver.py` 구현 (`src/app/services/file_watcher/device_resolver.py`):

```python
async def resolve_device(
    db: AsyncSession,
    device_type: str,   # InspectionFeatureMapping에서 사용할 device_type
    unit: Unit,
) -> MeasurementDevice:
    candidates = (await db.execute(
        select(MeasurementDevice).where(
            MeasurementDevice.source_type == device_type,
            MeasurementDevice.is_active   == True,
        )
    )).scalars().all()

    if len(candidates) == 0:
        raise NoDeviceFoundError(device_type)
    if len(candidates) == 1:
        return candidates[0]

    # 복수 장비 → 셀 기반 disambiguation
    cell_id = await _get_unit_cell_id(db, unit)
    if cell_id:
        cell_devices = [d for d in candidates if d.cell_id == cell_id]
        if len(cell_devices) == 1:
            return cell_devices[0]

    raise AmbiguousDeviceError(device_type, len(candidates))
```

---

### 7.3 현재 MeasurementDevice 모델의 갭

현재 `MeasurementDevice` 테이블에는 위치/셀 정보가 없어, 동일 타입 장비가 복수일 경우 disambiguation이 불가능하다.

**현재 모델** (`src/app/models/quality.py`):
```python
class MeasurementDevice(Base):
    name: str
    source_type: str          # "OMM" / "EQUATOR" / "CMM" / "MANUAL"
    connection_config: dict   # {"connection_type": "FILE"/"FTP", "path": "..."}
    is_active: bool
    # cell_id 없음 ← 복수 장비 환경에서 disambiguation 불가
```

**개선 방향** (Phase 4 스코프):
- `cell_id` FK 추가 (`nullable=True`로 하위 호환 유지)
- 단일 장비 환경에서는 `cell_id` 없이도 동작

---

### 7.4 device_id를 InspectionPlan에 추가하지 않는 이유 요약

| 항목 | device_id on InspectionPlan | inspection_type (현재 설계) |
|------|------------------------------|----------------------------|
| 계획 생성 시점 | 특정 장비 인스턴스 불명 → 입력 불가 | 장비 타입만 지정 → 가능 |
| CAD/PMI 자동 생성 | 지원 불가 | 지원 가능 (PMI_TO_INSPECTION_CONFIG) |
| QIF 표준 | 비표준 | 표준 준수 |
| 장비 교체 시 | 모든 InspectionPlan 수정 필요 | 영향 없음 |
| 실행 유연성 | 고정 장비만 사용 가능 | 여러 장비 중 최적 선택 가능 |

---

## 8. 제약 사항 및 리스크

| 항목 | 내용 | 대응 방안 |
|------|------|-----------|
| 미들웨어 Unit 상태와의 동기화 | Unit이 DONE 되기 전 검사 결과 등록 가능 여부 | unit_id 등록 시 status 검증 추가 여부 결정 필요 |
| 측정 파일 포맷 다양성 | 장비마다 CSV 컬럼 구조가 다름 | 어댑터 패턴으로 포맷별 파서 분리 |
| 네트워크 공유 설정 | 공장 보안 정책에 따라 SMB 마운트 제한 가능 | 경량 Agent 방식 대안 준비 |
| DB 롤백 일관성 | File Watcher가 API 호출 실패 시 파일 처리 상태 불일치 | 멱등성 보장 (해시 기반 재처리 방지) |
