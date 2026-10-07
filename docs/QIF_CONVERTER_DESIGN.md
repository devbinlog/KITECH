# QIF 변환기 상세 설계

> Quality Information Framework (QIF) - ISO/TS 23619  
> PMI → QIF 변환을 통한 측정 시스템 표준화

## 개요

### QIF란?
DMSC(Dimensional Metrology Standards Consortium)에서 개발한 **품질 정보 교환 표준**.
XML 기반으로 CAD 시스템, CMM, 측정 소프트웨어 간 데이터 교환을 표준화한다.

### GD&T 14가지 분류

| 분류 | 기호 | 한글명 | 영문명 | 데이텀 | 측정장비 |
|------|------|--------|--------|--------|----------|
| **형상** | ⏤ | 진직도 | Straightness | ✗ | CMM, 다이얼 |
| | ⏥ | 평면도 | Flatness | ✗ | CMM, 정반 |
| | ○ | 진원도 | Circularity | ✗ | 진원도측정기 |
| | ⌭ | 원통도 | Cylindricity | ✗ | CMM, 진원도측정기 |
| **방향** | ⊥ | 직각도 | Perpendicularity | ✓ | CMM |
| | ∠ | 경사도 | Angularity | ✓ | CMM |
| | ∥ | 평행도 | Parallelism | ✓ | CMM, 다이얼 |
| **위치** | ⌖ | 위치도 | Position | ✓ | CMM |
| | ◎ | 동심도 | Concentricity | ✓ | CMM |
| | ⌯ | 대칭도 | Symmetry | ✓ | CMM |
| **흔들림** | ↗ | 원주흔들림 | Circular Runout | ✓ | 다이얼+회전 |
| | ↗↗ | 전체흔들림 | Total Runout | ✓ | 다이얼+회전 |
| **윤곽** | ⌒ | 선의윤곽도 | Line Profile | △ | CMM |
| | ⌓ | 면의윤곽도 | Surface Profile | △ | CMM, 스캐너 |

> △ = 데이텀 선택적 (있으면 위치+형상 제어, 없으면 형상만 제어)

### 재료 조건 (Material Condition Modifiers)

| 기호 | 코드 | 설명 | 적용 |
|------|------|------|------|
| Ⓜ | MMC | 최대 실체 조건 | 구멍: 최소 직경 / 축: 최대 직경 |
| Ⓛ | LMC | 최소 실체 조건 | 구멍: 최대 직경 / 축: 최소 직경 |
| (없음) | RFS | 실체 조건 무관 | 실제 크기와 무관하게 공차 적용 |

**보너스 공차**: MMC/LMC 사용 시, 실제 크기가 규격에서 벗어날수록 허용 공차 증가

```
예) 위치도 ⌖ 0.050 Ⓜ, 구멍 Ø10.0 +0.05/-0
- 구멍 Ø10.00 (MMC) → 위치도 공차 0.050
- 구멍 Ø10.03 → 위치도 공차 0.050 + 0.03 = 0.080
- 구멍 Ø10.05 (LMC) → 위치도 공차 0.050 + 0.05 = 0.100
```

### 왜 QIF인가?
| 현재 | QIF 도입 후 |
|------|-------------|
| PMI → 수동 검사계획 작성 | PMI → QIFPlan 자동 생성 |
| 측정 결과 CSV/엑셀 혼재 | QIFResults 표준 포맷 |
| SPC 데이터 시스템별 분산 | QIFStatistics 통합 |
| 장비별 다른 포맷 | 벤더 중립적 표준 |

---

## QIF 문서 타입

### 1. QIFPlan (검사 계획)
측정해야 할 특성과 방법 정의

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QIFDocument xmlns="http://qifstandards.org/xsd/qif3">
  <QPId>PLAN-2026-001</QPId>
  <Version>
    <TimeCreated>2026-02-08T12:00:00</TimeCreated>
  </Version>
  <MeasurementPlan>
    <PartId>PART-001</PartId>
    <PlanId>INSP-PLAN-001</PlanId>
    
    <CharacteristicNominals>
      <!-- PMI에서 추출된 치수 -->
      <CharacteristicNominal id="CN1">
        <Name>외경 D1</Name>
        <CharacteristicType>Diameter</CharacteristicType>
        <TargetValue>50.000</TargetValue>
        <ToleranceDefinition>
          <PlusMinusTolerance>
            <Plus>0.020</Plus>
            <Minus>0.020</Minus>
          </PlusMinusTolerance>
        </ToleranceDefinition>
      </CharacteristicNominal>
      
      <CharacteristicNominal id="CN2">
        <Name>위치도 H1</Name>
        <CharacteristicType>PositionTolerance</CharacteristicType>
        <ToleranceValue>0.050</ToleranceValue>
        <MaterialCondition>MMC</MaterialCondition>
        <DatumReferenceFrame>
          <DatumRef>A</DatumRef>
          <DatumRef>B</DatumRef>
        </DatumReferenceFrame>
      </CharacteristicNominal>
    </CharacteristicNominals>
    
    <MeasurementMethods>
      <Method id="M1" characteristicRef="CN1">
        <DeviceType>Equator</DeviceType>
        <SamplingPlan>
          <Type>Periodic</Type>
          <Frequency>5</Frequency>  <!-- 5개당 1개 -->
        </SamplingPlan>
      </Method>
    </MeasurementMethods>
  </MeasurementPlan>
</QIFDocument>
```

### 2. QIFResults (측정 결과)
실제 측정값 기록

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QIFDocument xmlns="http://qifstandards.org/xsd/qif3">
  <QPId>RESULT-2026-001</QPId>
  <MeasurementResults>
    <InspectionTraceability>
      <ReferencedQIFPlanId>PLAN-2026-001</ReferencedQIFPlanId>
      <WorkOrderId>WO-2026-0123</WorkOrderId>
      <LotNumber>LOT-001</LotNumber>
      <SerialNumber>SN-001</SerialNumber>
    </InspectionTraceability>
    
    <MeasuredCharacteristics>
      <MeasuredCharacteristic characteristicRef="CN1">
        <MeasuredValue>50.012</MeasuredValue>
        <Deviation>0.012</Deviation>
        <Status>PASS</Status>
        <MeasurementTime>2026-02-08T14:30:00</MeasurementTime>
        <MeasuredBy>EQUATOR-01</MeasuredBy>
      </MeasuredCharacteristic>
      
      <MeasuredCharacteristic characteristicRef="CN2">
        <MeasuredValue>0.032</MeasuredValue>
        <Status>PASS</Status>
        <ActualDatums>
          <Datum name="A">Established</Datum>
          <Datum name="B">Established</Datum>
        </ActualDatums>
      </MeasuredCharacteristic>
    </MeasuredCharacteristics>
    
    <OverallStatus>CONFORMING</OverallStatus>
  </MeasurementResults>
</QIFDocument>
```

### 2-1. GD&T 특성별 XML 예시

#### 형상 공차 (Form Tolerances)

```xml
<!-- 진직도 (Straightness) - 데이텀 불필요 -->
<CharacteristicNominal id="CN10">
  <Name>축 진직도</Name>
  <CharacteristicType>StraightnessCharacteristic</CharacteristicType>
  <ToleranceValue>0.010</ToleranceValue>
  <FeatureRef>AXIS-01</FeatureRef>
</CharacteristicNominal>

<!-- 평면도 (Flatness) - 데이텀 불필요 -->
<CharacteristicNominal id="CN11">
  <Name>상면 평면도</Name>
  <CharacteristicType>FlatnessCharacteristic</CharacteristicType>
  <ToleranceValue>0.015</ToleranceValue>
  <FeatureRef>SURFACE-TOP</FeatureRef>
</CharacteristicNominal>

<!-- 진원도 (Circularity) - 데이텀 불필요 -->
<CharacteristicNominal id="CN12">
  <Name>외경 진원도</Name>
  <CharacteristicType>CircularityCharacteristic</CharacteristicType>
  <ToleranceValue>0.008</ToleranceValue>
  <FeatureRef>CYL-01</FeatureRef>
</CharacteristicNominal>

<!-- 원통도 (Cylindricity) - 데이텀 불필요, 가장 엄격한 형상 공차 -->
<CharacteristicNominal id="CN13">
  <Name>베어링부 원통도</Name>
  <CharacteristicType>CylindricityCharacteristic</CharacteristicType>
  <ToleranceValue>0.005</ToleranceValue>
  <FeatureRef>CYL-BEARING</FeatureRef>
</CharacteristicNominal>
```

#### 방향 공차 (Orientation Tolerances)

```xml
<!-- 직각도 (Perpendicularity) - 데이텀 필요 -->
<CharacteristicNominal id="CN20">
  <Name>구멍 직각도</Name>
  <CharacteristicType>PerpendicularityCharacteristic</CharacteristicType>
  <ToleranceValue>0.020</ToleranceValue>
  <MaterialCondition>MMC</MaterialCondition>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
  </DatumReferenceFrame>
  <FeatureRef>HOLE-01</FeatureRef>
</CharacteristicNominal>

<!-- 평행도 (Parallelism) - 데이텀 필요 -->
<CharacteristicNominal id="CN21">
  <Name>하면 평행도</Name>
  <CharacteristicType>ParallelismCharacteristic</CharacteristicType>
  <ToleranceValue>0.012</ToleranceValue>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
  </DatumReferenceFrame>
  <FeatureRef>SURFACE-BOTTOM</FeatureRef>
</CharacteristicNominal>

<!-- 경사도 (Angularity) - 데이텀 필요 -->
<CharacteristicNominal id="CN22">
  <Name>테이퍼면 경사도</Name>
  <CharacteristicType>AngularityCharacteristic</CharacteristicType>
  <ToleranceValue>0.025</ToleranceValue>
  <NominalAngle>45.0</NominalAngle>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>
```

#### 위치 공차 (Location Tolerances)

```xml
<!-- 위치도 (Position) - 가장 흔한 GD&T -->
<CharacteristicNominal id="CN30">
  <Name>볼트홀 위치도</Name>
  <CharacteristicType>PositionCharacteristic</CharacteristicType>
  <ToleranceValue>0.050</ToleranceValue>
  <ToleranceZoneShape>Cylindrical</ToleranceZoneShape>
  <MaterialCondition>MMC</MaterialCondition>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
    <SecondaryDatum>B</SecondaryDatum>
    <TertiaryDatum>C</TertiaryDatum>
  </DatumReferenceFrame>
  <NominalLocation>
    <X>25.000</X>
    <Y>30.000</Y>
  </NominalLocation>
</CharacteristicNominal>

<!-- 동심도/동축도 (Concentricity/Coaxiality) -->
<CharacteristicNominal id="CN31">
  <Name>내경 동축도</Name>
  <CharacteristicType>ConcentricityCharacteristic</CharacteristicType>
  <ToleranceValue>0.015</ToleranceValue>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>

<!-- 대칭도 (Symmetry) -->
<CharacteristicNominal id="CN32">
  <Name>키홈 대칭도</Name>
  <CharacteristicType>SymmetryCharacteristic</CharacteristicType>
  <ToleranceValue>0.030</ToleranceValue>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>
```

#### 흔들림 공차 (Runout Tolerances)

```xml
<!-- 원주 흔들림 (Circular Runout) - 회전체 검사 -->
<CharacteristicNominal id="CN40">
  <Name>외경 원주흔들림</Name>
  <CharacteristicType>CircularRunoutCharacteristic</CharacteristicType>
  <ToleranceValue>0.020</ToleranceValue>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
    <SecondaryDatum>B</SecondaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>

<!-- 전체 흔들림 (Total Runout) - 원주흔들림보다 엄격 -->
<CharacteristicNominal id="CN41">
  <Name>베어링 저널 전체흔들림</Name>
  <CharacteristicType>TotalRunoutCharacteristic</CharacteristicType>
  <ToleranceValue>0.010</ToleranceValue>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
    <SecondaryDatum>B</SecondaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>
```

#### 윤곽 공차 (Profile Tolerances)

```xml
<!-- 선의 윤곽도 (Profile of a Line) - 2D 단면 -->
<CharacteristicNominal id="CN50">
  <Name>캠 프로파일</Name>
  <CharacteristicType>LineProfileCharacteristic</CharacteristicType>
  <ToleranceValue>0.040</ToleranceValue>
  <ToleranceDistribution>Bilateral</ToleranceDistribution>
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
    <SecondaryDatum>B</SecondaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>

<!-- 면의 윤곽도 (Profile of a Surface) - 3D 전체 표면 -->
<CharacteristicNominal id="CN51">
  <Name>블레이드 곡면</Name>
  <CharacteristicType>SurfaceProfileCharacteristic</CharacteristicType>
  <ToleranceValue>0.050</ToleranceValue>
  <ToleranceDistribution>Unilateral</ToleranceDistribution>
  <UnilateralOffset>-0.050</UnilateralOffset>  <!-- 안쪽으로만 -->
  <DatumReferenceFrame>
    <PrimaryDatum>A</PrimaryDatum>
    <SecondaryDatum>B</SecondaryDatum>
    <TertiaryDatum>C</TertiaryDatum>
  </DatumReferenceFrame>
</CharacteristicNominal>
```

---

### 3. QIFStatistics (SPC 데이터)
통계적 품질 관리 데이터

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QIFDocument xmlns="http://qifstandards.org/xsd/qif3">
  <QPId>STATS-2026-001</QPId>
  <StatisticalStudy>
    <StudyId>SPC-CHART-001</StudyId>
    <CharacteristicRef>CN1</CharacteristicRef>
    <StudyType>XBarR</StudyType>
    <SubgroupSize>5</SubgroupSize>
    
    <ControlLimits>
      <XBarChart>
        <UCL>50.025</UCL>
        <CL>50.005</CL>
        <LCL>49.985</LCL>
      </XBarChart>
      <RChart>
        <UCL>0.042</UCL>
        <CL>0.020</CL>
        <LCL>0</LCL>
      </RChart>
    </ControlLimits>
    
    <ProcessCapability>
      <Cp>1.67</Cp>
      <Cpk>1.45</Cpk>
      <Pp>1.55</Pp>
      <Ppk>1.38</Ppk>
    </ProcessCapability>
    
    <Subgroups>
      <Subgroup number="1">
        <XBar>50.008</XBar>
        <Range>0.018</Range>
        <OutOfControl>false</OutOfControl>
      </Subgroup>
      <Subgroup number="2">
        <XBar>50.002</XBar>
        <Range>0.022</Range>
        <OutOfControl>false</OutOfControl>
      </Subgroup>
    </Subgroups>
  </StatisticalStudy>
</QIFDocument>
```

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        QIF Converter                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ step-pmi-    │    │   Cell-MES   │    │  SPC Engine  │       │
│  │ reader JSON  │    │   Results    │    │    Stats     │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                  QIF Converter Core                   │       │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐    │       │
│  │  │ PMI Parser │ │ Result     │ │ Stats          │    │       │
│  │  │ → QIFPlan  │ │ → QIFRes   │ │ → QIFStatistics│    │       │
│  │  └────────────┘ └────────────┘ └────────────────┘    │       │
│  └──────────────────────────────────────────────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                   QIF XML Output                      │       │
│  │   QIFPlan.xml    QIFResults.xml   QIFStatistics.xml  │       │
│  └──────────────────────────────────────────────────────┘       │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               ▼
                    ┌──────────────────┐
                    │  외부 시스템 연동  │
                    │  CMM / Polyworks │
                    │  / Calypso 등    │
                    └──────────────────┘
```

---

## 모듈 설계

### 디렉토리 구조

```
libs/qif-converter/
├── pyproject.toml
├── src/
│   └── qif_converter/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── base.py           # QIFDocument 기본 클래스
│       │   ├── types.py          # CharacteristicType enum
│       │   └── exceptions.py     # QIF 관련 예외
│       ├── builders/
│       │   ├── __init__.py
│       │   ├── plan_builder.py   # QIFPlan 생성
│       │   ├── result_builder.py # QIFResults 생성
│       │   └── stats_builder.py  # QIFStatistics 생성
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── pmi_parser.py     # step-pmi-reader JSON → QIF
│       │   └── qif_parser.py     # QIF XML 파싱
│       ├── exporters/
│       │   ├── __init__.py
│       │   ├── xml_exporter.py   # QIF XML 출력
│       │   └── json_exporter.py  # QIF JSON 출력 (비표준)
│       └── validators/
│           ├── __init__.py
│           └── schema_validator.py  # XSD 검증
└── tests/
    ├── test_plan_builder.py
    ├── test_result_builder.py
    └── fixtures/
        ├── sample_pmi.json
        └── expected_qifplan.xml
```

### 핵심 클래스

```python
# src/qif_converter/core/base.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import xml.etree.ElementTree as ET


class CharacteristicType(str, Enum):
    """QIF 특성 유형 - GD&T 14가지 + 치수"""
    
    # === 치수 (Dimensional) ===
    DIAMETER = "DiameterCharacteristic"
    RADIUS = "RadiusCharacteristic"
    LENGTH = "LengthCharacteristic"
    DISTANCE = "DistanceCharacteristic"
    ANGLE = "AngleCharacteristic"
    WIDTH = "WidthCharacteristic"
    DEPTH = "DepthCharacteristic"
    
    # === 형상 공차 (Form) - 4가지 ===
    STRAIGHTNESS = "StraightnessCharacteristic"      # 진직도
    FLATNESS = "FlatnessCharacteristic"              # 평면도
    CIRCULARITY = "CircularityCharacteristic"        # 진원도
    CYLINDRICITY = "CylindricityCharacteristic"      # 원통도
    
    # === 방향 공차 (Orientation) - 3가지 ===
    PERPENDICULARITY = "PerpendicularityCharacteristic"  # 직각도
    ANGULARITY = "AngularityCharacteristic"              # 경사도
    PARALLELISM = "ParallelismCharacteristic"            # 평행도
    
    # === 위치 공차 (Location) - 3가지 ===
    POSITION = "PositionCharacteristic"              # 위치도
    CONCENTRICITY = "ConcentricityCharacteristic"    # 동심도/동축도
    SYMMETRY = "SymmetryCharacteristic"              # 대칭도
    
    # === 흔들림 공차 (Runout) - 2가지 ===
    CIRCULAR_RUNOUT = "CircularRunoutCharacteristic"  # 원주 흔들림
    TOTAL_RUNOUT = "TotalRunoutCharacteristic"        # 전체 흔들림
    
    # === 윤곽 공차 (Profile) - 2가지 ===
    LINE_PROFILE = "LineProfileCharacteristic"        # 선의 윤곽도
    SURFACE_PROFILE = "SurfaceProfileCharacteristic"  # 면의 윤곽도


class MaterialCondition(str, Enum):
    """재료 조건"""
    MMC = "MMC"  # Maximum Material Condition
    LMC = "LMC"  # Least Material Condition
    RFS = "RFS"  # Regardless of Feature Size


@dataclass
class ToleranceDefinition:
    """공차 정의"""
    upper: float
    lower: float
    tolerance_type: str = "bilateral"  # bilateral, unilateral_plus, unilateral_minus


@dataclass
class DatumReference:
    """데이텀 참조"""
    name: str  # A, B, C
    material_condition: Optional[MaterialCondition] = None
    precedence: int = 1  # 1=Primary, 2=Secondary, 3=Tertiary


@dataclass
class CharacteristicNominal:
    """검사 특성 정의 (PMI에서 추출)"""
    id: str
    name: str
    char_type: CharacteristicType
    
    # 치수 공차용
    target_value: Optional[float] = None
    tolerance: Optional[ToleranceDefinition] = None
    
    # GD&T 공차용
    tolerance_value: Optional[float] = None  # 단일 공차값 (ex: 위치도 0.05)
    tolerance_zone_shape: str = "Cylindrical"  # Cylindrical, Spherical, Linear
    
    # 데이텀 참조
    datum_refs: list[DatumReference] = field(default_factory=list)
    
    # 재료 조건
    material_condition: Optional[MaterialCondition] = None
    
    # 피처 참조
    feature_id: Optional[str] = None
    feature_type: Optional[str] = None  # Hole, Surface, Axis, Plane
    
    # 추가 속성
    nominal_location: Optional[tuple[float, float, float]] = None  # 위치도용 XYZ
    nominal_angle: Optional[float] = None  # 경사도용
    unilateral_offset: Optional[float] = None  # 편측 공차용
    
    def requires_datum(self) -> bool:
        """데이텀이 필요한 공차인지 확인"""
        no_datum_types = {
            CharacteristicType.STRAIGHTNESS,
            CharacteristicType.FLATNESS,
            CharacteristicType.CIRCULARITY,
            CharacteristicType.CYLINDRICITY,
        }
        return self.char_type not in no_datum_types


@dataclass
class MeasuredCharacteristic:
    """측정 결과"""
    characteristic_ref: str
    measured_value: float
    deviation: float
    status: str  # PASS, FAIL
    measured_at: datetime
    measured_by: str  # 장비 ID


@dataclass
class SubgroupData:
    """SPC 서브그룹 데이터"""
    number: int
    x_bar: float
    range_value: float
    std_dev: Optional[float] = None
    out_of_control: bool = False
    violated_rules: list[str] = field(default_factory=list)
```

### Plan Builder

```python
# src/qif_converter/builders/plan_builder.py

from lxml import etree
from typing import Optional
from ..core.base import CharacteristicNominal, ToleranceDefinition


class QIFPlanBuilder:
    """PMI 데이터 → QIFPlan XML 변환"""
    
    QIF_NS = "http://qifstandards.org/xsd/qif3"
    
    def __init__(self, plan_id: str, part_id: str):
        self.plan_id = plan_id
        self.part_id = part_id
        self.characteristics: list[CharacteristicNominal] = []
        self.measurement_methods: dict[str, dict] = {}
    
    def add_characteristic_from_pmi(self, pmi_dimension: dict) -> str:
        """PMI dimension을 CharacteristicNominal로 변환"""
        char_id = f"CN{len(self.characteristics) + 1}"
        
        char = CharacteristicNominal(
            id=char_id,
            name=pmi_dimension["name"],
            char_type=self._map_pmi_type(pmi_dimension["type"]),
            target_value=pmi_dimension["nominal"],
            tolerance=ToleranceDefinition(
                upper=pmi_dimension.get("upper_tol", 0),
                lower=pmi_dimension.get("lower_tol", 0),
            ),
            feature_id=pmi_dimension.get("feature_id"),
            datum_refs=pmi_dimension.get("datums", []),
        )
        self.characteristics.append(char)
        return char_id
    
    def set_measurement_method(
        self,
        char_id: str,
        device_type: str,
        sampling_type: str = "Periodic",
        frequency: int = 5
    ):
        """측정 방법 설정"""
        self.measurement_methods[char_id] = {
            "device_type": device_type,
            "sampling_type": sampling_type,
            "frequency": frequency,
        }
    
    def build(self) -> str:
        """QIFPlan XML 생성"""
        nsmap = {None: self.QIF_NS}
        root = etree.Element("QIFDocument", nsmap=nsmap)
        
        # Header
        etree.SubElement(root, "QPId").text = self.plan_id
        version = etree.SubElement(root, "Version")
        etree.SubElement(version, "TimeCreated").text = datetime.now().isoformat()
        
        # MeasurementPlan
        plan = etree.SubElement(root, "MeasurementPlan")
        etree.SubElement(plan, "PartId").text = self.part_id
        etree.SubElement(plan, "PlanId").text = self.plan_id
        
        # Characteristics
        chars_elem = etree.SubElement(plan, "CharacteristicNominals")
        for char in self.characteristics:
            self._build_characteristic(chars_elem, char)
        
        # Methods
        methods_elem = etree.SubElement(plan, "MeasurementMethods")
        for char_id, method in self.measurement_methods.items():
            self._build_method(methods_elem, char_id, method)
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    
    def _map_pmi_type(self, pmi_type: str) -> CharacteristicType:
        """PMI 타입 → QIF CharacteristicType 매핑 (GD&T 14가지 + 치수)"""
        mapping = {
            # 치수
            "diameter": CharacteristicType.DIAMETER,
            "radius": CharacteristicType.RADIUS,
            "length": CharacteristicType.LENGTH,
            "distance": CharacteristicType.DISTANCE,
            "angle": CharacteristicType.ANGLE,
            "width": CharacteristicType.WIDTH,
            "depth": CharacteristicType.DEPTH,
            
            # 형상 공차 (Form) - 데이텀 불필요
            "straightness": CharacteristicType.STRAIGHTNESS,
            "flatness": CharacteristicType.FLATNESS,
            "circularity": CharacteristicType.CIRCULARITY,
            "roundness": CharacteristicType.CIRCULARITY,  # 별칭
            "cylindricity": CharacteristicType.CYLINDRICITY,
            
            # 방향 공차 (Orientation) - 데이텀 필요
            "perpendicularity": CharacteristicType.PERPENDICULARITY,
            "angularity": CharacteristicType.ANGULARITY,
            "parallelism": CharacteristicType.PARALLELISM,
            
            # 위치 공차 (Location) - 데이텀 필요
            "position": CharacteristicType.POSITION,
            "true_position": CharacteristicType.POSITION,  # 별칭
            "concentricity": CharacteristicType.CONCENTRICITY,
            "coaxiality": CharacteristicType.CONCENTRICITY,  # 별칭
            "symmetry": CharacteristicType.SYMMETRY,
            
            # 흔들림 공차 (Runout) - 데이텀 필요
            "circular_runout": CharacteristicType.CIRCULAR_RUNOUT,
            "runout": CharacteristicType.CIRCULAR_RUNOUT,  # 기본은 원주 흔들림
            "total_runout": CharacteristicType.TOTAL_RUNOUT,
            
            # 윤곽 공차 (Profile)
            "line_profile": CharacteristicType.LINE_PROFILE,
            "profile_of_line": CharacteristicType.LINE_PROFILE,
            "surface_profile": CharacteristicType.SURFACE_PROFILE,
            "profile_of_surface": CharacteristicType.SURFACE_PROFILE,
            "profile": CharacteristicType.SURFACE_PROFILE,  # 기본은 면의 윤곽도
        }
        return mapping.get(pmi_type.lower(), CharacteristicType.LENGTH)
    
    def _build_characteristic(self, parent, char: CharacteristicNominal):
        """개별 특성 XML 빌드"""
        elem = etree.SubElement(parent, "CharacteristicNominal", id=char.id)
        etree.SubElement(elem, "Name").text = char.name
        etree.SubElement(elem, "CharacteristicType").text = char.char_type.value
        etree.SubElement(elem, "TargetValue").text = str(char.target_value)
        
        tol = etree.SubElement(elem, "ToleranceDefinition")
        pm = etree.SubElement(tol, "PlusMinusTolerance")
        etree.SubElement(pm, "Plus").text = str(char.tolerance.upper)
        etree.SubElement(pm, "Minus").text = str(abs(char.tolerance.lower))
        
        if char.datum_refs:
            drf = etree.SubElement(elem, "DatumReferenceFrame")
            for datum in char.datum_refs:
                etree.SubElement(drf, "DatumRef").text = datum
    
    def _build_method(self, parent, char_id: str, method: dict):
        """측정 방법 XML 빌드"""
        elem = etree.SubElement(parent, "Method", id=f"M{char_id[2:]}", characteristicRef=char_id)
        etree.SubElement(elem, "DeviceType").text = method["device_type"]
        
        sampling = etree.SubElement(elem, "SamplingPlan")
        etree.SubElement(sampling, "Type").text = method["sampling_type"]
        etree.SubElement(sampling, "Frequency").text = str(method["frequency"])
```

### PMI → QIF 변환 함수

```python
# src/qif_converter/converters/pmi_to_qif.py

from pathlib import Path
from ..builders.plan_builder import QIFPlanBuilder


def convert_pmi_to_qifplan(
    pmi_json: dict,
    plan_id: str,
    default_device: str = "Equator",
    default_frequency: int = 5,
) -> str:
    """
    step-pmi-reader JSON → QIFPlan XML 변환
    
    Args:
        pmi_json: step-pmi-reader 출력 JSON
        plan_id: 검사 계획 ID
        default_device: 기본 측정 장비
        default_frequency: 기본 샘플링 주기
    
    Returns:
        QIFPlan XML 문자열
    """
    part_id = pmi_json.get("file_name", "UNKNOWN").replace(".step", "")
    
    builder = QIFPlanBuilder(plan_id=plan_id, part_id=part_id)
    
    # Dimensions → Characteristics
    for dim in pmi_json.get("dimensions", []):
        char_id = builder.add_characteristic_from_pmi(dim)
        builder.set_measurement_method(
            char_id=char_id,
            device_type=default_device,
            frequency=default_frequency,
        )
    
    # GD&T → Characteristics
    for gdt in pmi_json.get("geometric_tolerances", []):
        char_id = builder.add_characteristic_from_pmi({
            "name": gdt["name"],
            "type": gdt["tolerance_type"],
            "nominal": 0,  # GD&T는 공칭값 없음
            "upper_tol": gdt["value"],
            "lower_tol": 0,
            "datums": gdt.get("datum_refs", []),
            "feature_id": gdt.get("feature_id"),
        })
        builder.set_measurement_method(char_id, "CMM")  # GD&T는 보통 CMM
    
    return builder.build()


async def generate_qifplan_from_step(
    step_file: Path,
    plan_id: str,
) -> str:
    """
    STEP 파일 → PMI 추출 → QIFPlan 생성 (end-to-end)
    """
    from step_pmi_reader import extract_pmi  # libs/step-pmi-reader
    
    pmi_data = await extract_pmi(step_file)
    return convert_pmi_to_qifplan(pmi_data, plan_id)
```

---

## API 엔드포인트

```python
# agents/cell-mes/src/app/api/v1/endpoints/qif.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from qif_converter import convert_pmi_to_qifplan, QIFResultBuilder, QIFStatsBuilder


router = APIRouter(prefix="/qif", tags=["QIF"])


@router.post("/plans/from-pmi", response_class=Response)
async def create_qifplan_from_pmi(
    pmi_file: UploadFile = File(...),
    plan_id: str = None,
):
    """PMI JSON → QIFPlan XML 변환"""
    content = await pmi_file.read()
    pmi_data = json.loads(content)
    
    if not plan_id:
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    xml_content = convert_pmi_to_qifplan(pmi_data, plan_id)
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={plan_id}.xml"}
    )


@router.get("/results/{work_order_id}", response_class=Response)
async def export_qif_results(work_order_id: int, db: AsyncSession = Depends(get_db)):
    """작업지시 측정결과 → QIFResults XML"""
    results = await get_inspection_results(db, work_order_id)
    
    builder = QIFResultBuilder(
        result_id=f"RESULT-WO{work_order_id}",
        work_order_id=str(work_order_id),
    )
    
    for r in results:
        builder.add_measured_characteristic(
            characteristic_ref=f"CN{r.plan.id}",
            value=r.measured_value,
            status="PASS" if r.is_conforming else "FAIL",
            measured_at=r.measured_at,
            device_id=r.device_id,
        )
    
    return Response(content=builder.build(), media_type="application/xml")


@router.get("/statistics/{chart_id}", response_class=Response)
async def export_qif_statistics(chart_id: int, db: AsyncSession = Depends(get_db)):
    """SPC 차트 → QIFStatistics XML"""
    chart = await get_spc_chart(db, chart_id)
    data_points = await get_spc_data_points(db, chart_id)
    
    builder = QIFStatsBuilder(
        study_id=f"SPC-{chart_id}",
        characteristic_ref=f"CN{chart.plan_id}",
        chart_type=chart.chart_type,
        subgroup_size=chart.subgroup_size,
    )
    
    builder.set_control_limits(ucl=chart.ucl, cl=chart.cl, lcl=chart.lcl)
    builder.set_capability(cp=chart.cp, cpk=chart.cpk)
    
    for dp in data_points:
        builder.add_subgroup(
            number=dp.subgroup_no,
            x_bar=dp.x_bar,
            range_value=dp.r_value,
            out_of_control=dp.is_out_of_control,
        )
    
    return Response(content=builder.build(), media_type="application/xml")
```

---

## 구현 계획

### Phase 1: 기초 (1일)
- [ ] `libs/qif-converter/` 패키지 생성
- [ ] `QIFPlanBuilder` 구현
- [ ] PMI → QIFPlan 변환 함수
- [ ] 단위 테스트 (10개)

### Phase 2: 결과 변환 (0.5일)
- [ ] `QIFResultBuilder` 구현
- [ ] InspectionResult → QIFResults 변환
- [ ] API 엔드포인트

### Phase 3: 통계 변환 (0.5일)
- [ ] `QIFStatsBuilder` 구현
- [ ] SPCChart → QIFStatistics 변환
- [ ] API 엔드포인트

### Phase 4: 통합 (1일)
- [ ] MES API에 QIF 엔드포인트 추가
- [ ] step-pmi-reader 연동 테스트
- [ ] E2E 테스트

---

## 참고 자료

- [QIF Standard (DMSC)](https://qifstandards.org/)
- [ISO/TS 23619:2023](https://www.iso.org/standard/76395.html)
- [QIF 3.0 XSD Schema](https://qifstandards.org/schema/)

---

*Created: 2026-02-08*
