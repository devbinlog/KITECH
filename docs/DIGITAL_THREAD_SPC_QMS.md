# Digital Thread + MES + SPC/QMS 통합 설계

## 개요

Digital Thread 기반의 제조 데이터 추적성과 SPC/QMS 품질 관리 기능 통합 설계 문서.

## Digital Thread Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Digital Thread Flow                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  STEP/PMI  →  CAM/NC  →  Machining  →  Inspection  →  SPC/QMS              │
│     │           │           │             │              │                  │
│  치수/공차    가공조건     실시간모니터링    측정결과       품질분석          │
│     │           │           │             │              │                  │
│     └───────────┴───────────┴─────────────┴──────────────┘                  │
│                         Full Traceability                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 추천 기능 (MVP)

### SPC 기능

| 기능 | 복잡도 | Digital Thread 연계 | 가치 |
|------|--------|---------------------|------|
| **Control Chart (X-bar, R)** | ⭐⭐ | 측정 데이터 → 자동 차트 | 높음 |
| **Cp/Cpk 계산** | ⭐ | PMI 공차 → 자동 계산 | 높음 |
| **관리 이탈 감지** | ⭐⭐ | 알림 → 작업 중지 연계 | 높음 |
| **추세 분석** | ⭐⭐ | 가공조건 변화 상관관계 | 중간 |

### QMS 기능

| 기능 | 복잡도 | Digital Thread 연계 | 가치 |
|------|--------|---------------------|------|
| **검사 계획 자동생성** | ⭐⭐⭐ | PMI → 검사항목 추출 | 매우 높음 |
| **초도품 검사 (FAI)** | ⭐⭐ | 전수검사 → 합격 판정 | 높음 |
| **부적합 보고서 (NCR)** | ⭐⭐ | WO/Lot/Machine 연결 | 높음 |
| **시정조치 (CAPA)** | ⭐⭐⭐ | NCR → 원인 → 조치 이력 | 중간 |

---

## 📐 데이터 모델

### 1. 검사 계획 (PMI 연계)

```python
class InspectionPlan(Base):
    """PMI에서 자동 생성되는 검사 계획"""
    __tablename__ = "inspection_plans"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Digital Thread 연계
    pmi_source = Column(String)       # STEP 파일 경로
    feature_id = Column(String)       # PMI Feature ID
    
    # 검사 항목
    characteristic = Column(String)   # "외경", "깊이", "위치도"
    nominal = Column(Float)           # 기준값
    usl = Column(Float)               # 상한 (Upper Spec Limit)
    lsl = Column(Float)               # 하한 (Lower Spec Limit)
    
    # 검사 방법
    inspection_type = Column(String)  # "OMM", "EQUATOR", "CMM", "CALIPER"
    sampling_plan = Column(String)    # "FIRST_ARTICLE", "PERIODIC", "100%"
    frequency = Column(Integer)       # n개당 1회
```

### 2. 측정 결과

```python
class InspectionResult(Base):
    """실제 측정 결과"""
    __tablename__ = "inspection_results"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("inspection_plans.id"))
    work_order_id = Column(Integer, ForeignKey("work_orders.id"))
    
    # Digital Thread 연계
    lot_no = Column(String)
    serial_no = Column(String)        # 개별 추적
    machine_id = Column(Integer)
    nc_program_id = Column(String)
    
    # 측정 소스
    source = Column(String)           # "OMM", "EQUATOR", "MANUAL"
    device_id = Column(Integer, ForeignKey("measurement_devices.id"))
    
    # 측정값
    measured_value = Column(Float)
    measured_at = Column(DateTime)
    measured_by = Column(String)
    
    # 판정
    is_conforming = Column(Boolean)
    deviation = Column(Float)         # 기준값 대비 편차
```

### 3. SPC 관리도

```python
class SPCChart(Base):
    """관리도 정의"""
    __tablename__ = "spc_charts"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("inspection_plans.id"))
    
    chart_type = Column(String)       # "XBAR_R", "XBAR_S", "P", "NP"
    subgroup_size = Column(Integer, default=5)
    
    # 관리한계 (자동 계산 또는 수동)
    ucl = Column(Float)               # 상한 관리한계
    cl = Column(Float)                # 중심선
    lcl = Column(Float)               # 하한 관리한계
    
    # 공정능력
    cp = Column(Float)
    cpk = Column(Float)
    pp = Column(Float)
    ppk = Column(Float)


class SPCDataPoint(Base):
    """관리도 데이터 포인트"""
    __tablename__ = "spc_data_points"
    
    id = Column(Integer, primary_key=True)
    chart_id = Column(Integer, ForeignKey("spc_charts.id"))
    
    subgroup_no = Column(Integer)
    x_bar = Column(Float)             # 평균
    r_value = Column(Float)           # 범위
    s_value = Column(Float)           # 표준편차
    
    # 이상 감지
    is_out_of_control = Column(Boolean, default=False)
    violated_rules = Column(JSON)     # ["RULE_1", "RULE_2"]
    
    recorded_at = Column(DateTime)
```

### 4. 부적합 관리

```python
class NonConformance(Base):
    """부적합 보고서"""
    __tablename__ = "non_conformances"
    
    id = Column(Integer, primary_key=True)
    ncr_no = Column(String, unique=True)  # "NCR-2026-0001"
    
    # Digital Thread 연계 (추적성)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"))
    lot_no = Column(String)
    serial_no = Column(String)
    machine_id = Column(Integer)
    inspection_result_id = Column(Integer, ForeignKey("inspection_results.id"))
    
    # 부적합 내용
    defect_type = Column(String)      # "DIMENSION", "SURFACE", "MATERIAL"
    characteristic = Column(String)   # 어떤 항목
    specified_value = Column(Float)
    actual_value = Column(Float)
    
    # 처리
    disposition = Column(String)      # "REWORK", "SCRAP", "USE_AS_IS", "RETURN"
    status = Column(String)           # "OPEN", "REVIEWING", "CLOSED"
    
    # 원인 분석 (5 Why)
    root_cause = Column(Text)
    corrective_action = Column(Text)
```

---

## 📏 측정 시스템 통합

### 측정 소스별 특성

| 항목 | OMM (On-Machine) | Renishaw Equator |
|------|------------------|------------------|
| **타이밍** | 가공 중/직후 | 가공 완료 후 |
| **목적** | 공구 보정, 빠른 피드백 | 최종 검사, SPC |
| **정밀도** | ±5-10μm (기계 상태 의존) | ±2μm (온도 보정) |
| **연동 방식** | DPRNT/매크로변수/파일 | EZ-IO/MODUS/CSV |
| **데이터** | 단일 치수 위주 | 복합 형상 가능 |

### 측정 장비 마스터

```python
class MeasurementSource(str, Enum):
    OMM = "OMM"              # On-Machine Measurement
    EQUATOR = "EQUATOR"      # Renishaw Equator
    CMM = "CMM"              # 좌표측정기
    MANUAL = "MANUAL"        # 수동 측정


class MeasurementDevice(Base):
    """측정 장비 마스터"""
    __tablename__ = "measurement_devices"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)             # "EQUATOR-01", "CNC01-PROBE"
    source_type = Column(Enum(MeasurementSource))
    
    # 장비별 설정
    machine_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    serial_number = Column(String)
    calibration_due = Column(Date)
    
    # 연동 설정
    connection_type = Column(String)  # "FILE", "EZ_IO", "MACRO_VAR", "FOCAS"
    connection_config = Column(JSON)  # {"path": "/data/equator/", "format": "csv"}
```

### OMM 피드백 루프

```python
class ToolOffsetHistory(Base):
    """공구 보정 이력 (OMM 피드백)"""
    __tablename__ = "tool_offset_history"
    
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("equipment.id"))
    tool_id = Column(String)          # T01, T02...
    
    # 트리거
    triggered_by = Column(String)     # "OMM_AUTO", "OPERATOR", "SPC_ALERT"
    inspection_result_id = Column(Integer, ForeignKey("inspection_results.id"))
    
    # 보정 내용
    offset_type = Column(String)      # "LENGTH", "DIAMETER", "WEAR"
    previous_value = Column(Float)
    new_value = Column(Float)
    adjustment = Column(Float)
    
    # 결과
    applied_at = Column(DateTime)
    verified = Column(Boolean, default=False)
```

---

## 🔗 Digital Thread 연계 상세 설계

### Digital Thread 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Digital Thread Architecture                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Design     │    │     CAM      │    │  Machining   │    │  Inspection  │       │
│  │              │    │              │    │              │    │              │       │
│  │ STEP AP242   │───▶│  NCL/APT    │───▶│  G-code      │───▶│  Results     │       │
│  │ + PMI        │    │  + Toolpath  │    │  + Monitoring│    │  + SPC       │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                   │                │
│         ▼                   ▼                   ▼                   ▼                │
│  ┌──────────────────────────────────────────────────────────────────────────┐       │
│  │                         Traceability Layer                                │       │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │       │
│  │  │PartID   │─│ProgramID│─│MachineID│─│SerialNo │─│ResultID │            │       │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │       │
│  └──────────────────────────────────────────────────────────────────────────┘       │
│                                      │                                               │
│                                      ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐       │
│  │                          Quality Analytics                                │       │
│  │     SPC Charts  │  Cp/Cpk  │  Trend Analysis  │  Root Cause  │  CAPA    │       │
│  └──────────────────────────────────────────────────────────────────────────┘       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 에이전트 간 데이터 흐름

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  step-pmi-      │     │  digital-thread │     │    cell-mes     │
│  reader         │────▶│  project-mgr    │────▶│                 │
│                 │     │                 │     │                 │
│  STEP AP242     │     │  프로젝트 통합   │     │  MES 연동       │
│  PMI 추출       │     │  파일 관리       │     │  검사계획 생성   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  cam-runner     │     │  gcode-parser   │     │  monitoring-    │
│                 │────▶│                 │────▶│  data-replayer  │
│  CAM 분석       │     │  G-code 파싱    │     │                 │
│  Cycle Time     │     │  공구경로 추출   │     │  TDMS/LOG 분석  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

### 1. PMI → 검사계획 자동생성 (상세)

#### 지원 PMI 유형

| PMI 유형 | 검사항목 | 측정장비 | 샘플링 |
|----------|----------|----------|--------|
| 치수 (Dimension) | 외경, 내경, 길이, 깊이 | OMM, Equator | Periodic |
| 진직도 (Straightness) | 축 진직도 | CMM | First Article |
| 평면도 (Flatness) | 면 평면도 | CMM | First Article |
| 진원도 (Circularity) | 원통 진원도 | 진원도측정기 | Periodic |
| 원통도 (Cylindricity) | 베어링부 원통도 | CMM | First Article |
| 직각도 (Perpendicularity) | 구멍 직각도 | CMM | Periodic |
| 평행도 (Parallelism) | 면 평행도 | CMM | Periodic |
| 위치도 (Position) | 홀 위치도 | CMM, Equator | 100% |
| 동심도 (Concentricity) | 축 동심도 | CMM | Periodic |
| 원주흔들림 (Runout) | 회전체 흔들림 | 다이얼+V블록 | Periodic |
| 면윤곽도 (Surface Profile) | 곡면 형상 | CMM, 3D스캐너 | First Article |

#### 변환 로직

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class InspectionType(str, Enum):
    """측정 장비 유형"""
    OMM = "OMM"           # On-Machine Measurement
    EQUATOR = "EQUATOR"   # Renishaw Equator (비교측정)
    CMM = "CMM"           # 좌표측정기
    ROUNDNESS = "ROUNDNESS"  # 진원도측정기
    MANUAL = "MANUAL"     # 수동 (캘리퍼, 마이크로미터)


class SamplingPlan(str, Enum):
    """샘플링 계획"""
    FIRST_ARTICLE = "FIRST_ARTICLE"  # 초도품만
    PERIODIC = "PERIODIC"            # n개당 1개
    FULL = "100%"                    # 전수검사


@dataclass
class InspectionPlanConfig:
    """PMI 유형별 검사계획 설정"""
    inspection_type: InspectionType
    sampling_plan: SamplingPlan
    frequency: Optional[int] = None  # PERIODIC일 때 n개당 1개
    critical: bool = False           # CTQ 여부


# PMI 유형 → 검사계획 매핑
PMI_TO_INSPECTION_CONFIG: dict[str, InspectionPlanConfig] = {
    # 치수 - OMM으로 빠른 피드백
    "diameter": InspectionPlanConfig(InspectionType.OMM, SamplingPlan.PERIODIC, 10),
    "length": InspectionPlanConfig(InspectionType.OMM, SamplingPlan.PERIODIC, 10),
    "depth": InspectionPlanConfig(InspectionType.OMM, SamplingPlan.PERIODIC, 10),
    
    # 형상 공차 - CMM 초도품
    "straightness": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.FIRST_ARTICLE),
    "flatness": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.FIRST_ARTICLE),
    "circularity": InspectionPlanConfig(InspectionType.ROUNDNESS, SamplingPlan.PERIODIC, 50),
    "cylindricity": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.FIRST_ARTICLE, critical=True),
    
    # 방향 공차 - CMM 주기적
    "perpendicularity": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.PERIODIC, 20),
    "parallelism": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.PERIODIC, 20),
    "angularity": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.PERIODIC, 20),
    
    # 위치 공차 - 전수 또는 높은 빈도
    "position": InspectionPlanConfig(InspectionType.EQUATOR, SamplingPlan.FULL, critical=True),
    "concentricity": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.PERIODIC, 20),
    "symmetry": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.PERIODIC, 20),
    
    # 흔들림 - 회전체 검사
    "circular_runout": InspectionPlanConfig(InspectionType.MANUAL, SamplingPlan.PERIODIC, 10),
    "total_runout": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.PERIODIC, 20),
    
    # 윤곽 - 초도품 + 주기적
    "line_profile": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.FIRST_ARTICLE),
    "surface_profile": InspectionPlanConfig(InspectionType.CMM, SamplingPlan.FIRST_ARTICLE, critical=True),
}


async def generate_inspection_plan_from_pmi(
    pmi_data: dict,
    product_id: int,
    override_config: Optional[dict] = None,
) -> list[InspectionPlan]:
    """
    PMI 데이터에서 검사계획 자동 생성
    
    Args:
        pmi_data: step-pmi-reader 출력 JSON
        product_id: 제품 ID
        override_config: 특정 특성에 대한 설정 오버라이드
    
    Returns:
        생성된 InspectionPlan 리스트
    """
    plans = []
    source_file = pmi_data.get("file_name", "unknown.step")
    
    # 치수 공차 처리
    for dim in pmi_data.get("dimensions", []):
        pmi_type = dim.get("type", "length").lower()
        config = PMI_TO_INSPECTION_CONFIG.get(pmi_type, 
            InspectionPlanConfig(InspectionType.MANUAL, SamplingPlan.PERIODIC, 10))
        
        # 오버라이드 적용
        if override_config and dim["name"] in override_config:
            config = override_config[dim["name"]]
        
        plan = InspectionPlan(
            product_id=product_id,
            pmi_source=source_file,
            feature_id=dim.get("feature_id"),
            characteristic=dim["name"],
            characteristic_type="DIMENSION",
            nominal=dim["nominal"],
            usl=dim["nominal"] + dim.get("upper_tol", 0),
            lsl=dim["nominal"] + dim.get("lower_tol", 0),
            inspection_type=config.inspection_type.value,
            sampling_plan=config.sampling_plan.value,
            frequency=config.frequency,
            is_critical=config.critical,
        )
        plans.append(plan)
    
    # 기하 공차 처리
    for gdt in pmi_data.get("geometric_tolerances", []):
        pmi_type = gdt.get("tolerance_type", "position").lower()
        config = PMI_TO_INSPECTION_CONFIG.get(pmi_type,
            InspectionPlanConfig(InspectionType.CMM, SamplingPlan.FIRST_ARTICLE))
        
        plan = InspectionPlan(
            product_id=product_id,
            pmi_source=source_file,
            feature_id=gdt.get("feature_id"),
            characteristic=gdt["name"],
            characteristic_type="GDT",
            tolerance_type=gdt["tolerance_type"],
            nominal=0,  # GD&T는 공칭값 없음
            usl=gdt["value"],
            lsl=0,  # 단측 공차
            datum_refs=gdt.get("datum_refs", []),
            material_condition=gdt.get("material_condition"),
            inspection_type=config.inspection_type.value,
            sampling_plan=config.sampling_plan.value,
            frequency=config.frequency,
            is_critical=config.critical or gdt.get("is_ctq", False),
        )
        plans.append(plan)
    
    return plans
```

#### CTQ (Critical To Quality) 자동 판별

```python
def is_ctq_characteristic(pmi_item: dict) -> bool:
    """CTQ 특성 자동 판별"""
    
    # 1. 공차가 매우 타이트한 경우
    if "upper_tol" in pmi_item and "lower_tol" in pmi_item:
        total_tol = abs(pmi_item["upper_tol"]) + abs(pmi_item["lower_tol"])
        if total_tol < 0.02:  # 20μm 이하
            return True
    
    # 2. GD&T 공차값이 작은 경우
    if pmi_item.get("tolerance_type") in ["position", "cylindricity", "surface_profile"]:
        if pmi_item.get("value", 1) < 0.05:  # 50μm 이하
            return True
    
    # 3. 베어링, 씰, 끼워맞춤 관련 피처
    critical_keywords = ["bearing", "seal", "fit", "베어링", "씰", "끼워맞춤"]
    name = pmi_item.get("name", "").lower()
    if any(kw in name for kw in critical_keywords):
        return True
    
    # 4. 데이텀 피처
    if pmi_item.get("is_datum", False):
        return True
    
    return False
```

---

### 2. 전체 추적성 (Full Traceability) 상세

#### 추적성 ER 다이어그램

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Product   │──1:N──│ ProcessRoute│──N:1──│  StdProcess │
│             │       │             │       │             │
│ product_id  │       │ sequence    │       │ process_name│
│ part_no     │       │ cycle_time  │       │ equip_type  │
│ pmi_file    │       │             │       │             │
└──────┬──────┘       └─────────────┘       └─────────────┘
       │
       │1:N
       ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  WorkOrder  │──1:N──│  ProdResult │──N:1──│  Equipment  │
│             │       │             │       │             │
│ wo_id       │       │ lot_no      │       │ machine_id  │
│ qty_order   │       │ serial_no   │       │ machine_name│
│ status      │       │ qty_good    │       │ cell_id     │
└──────┬──────┘       └──────┬──────┘       └─────────────┘
       │                     │
       │                     │1:N
       │                     ▼
       │              ┌─────────────┐       ┌─────────────┐
       │              │ Inspection  │──N:1──│ Inspection  │
       │              │ Result      │       │ Plan        │
       │              │             │       │             │
       │              │ measured_val│       │ nominal     │
       │              │ deviation   │       │ usl/lsl     │
       │              │ is_conform  │       │ pmi_source  │
       │              └──────┬──────┘       └─────────────┘
       │                     │
       │                     │1:1 (optional)
       │                     ▼
       │              ┌─────────────┐       ┌─────────────┐
       └──────────────│    NCR      │──1:N──│   CAPA      │
                      │             │       │             │
                      │ ncr_no      │       │ action_type │
                      │ disposition │       │ due_date    │
                      │ root_cause  │       │ status      │
                      └─────────────┘       └─────────────┘
```

#### 추적성 쿼리 구현

```python
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional


@dataclass
class DesignTrace:
    """설계 추적 정보"""
    cad_file: str
    pmi_file: Optional[str]
    pmi_features: int
    revision: str
    released_at: datetime


@dataclass
class CAMTrace:
    """CAM 추적 정보"""
    nc_program_id: str
    nc_program_file: str
    cam_file: Optional[str]
    toolpath_count: int
    estimated_cycle_time: float


@dataclass
class MachiningTrace:
    """가공 추적 정보"""
    machine_id: str
    machine_name: str
    cell: str
    operator: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    actual_cycle_time: float
    setup_time: float


@dataclass
class MonitoringTrace:
    """모니터링 추적 정보"""
    spindle_load_avg: float
    spindle_load_max: float
    feed_override_avg: float
    tool_changes: int
    tool_wear_mm: Optional[float]
    vibration_level: Optional[float]
    coolant_temp: Optional[float]


@dataclass
class InspectionTrace:
    """검사 추적 정보"""
    results: list[dict]
    total_characteristics: int
    conforming_count: int
    non_conforming_count: int
    inspection_time: datetime
    inspector: Optional[str]


@dataclass
class QualityTrace:
    """품질 추적 정보"""
    ncr_list: list[str]
    ncr_open_count: int
    cpk_values: dict[str, float]  # characteristic → cpk
    overall_quality_score: float


@dataclass
class FullTraceability:
    """전체 추적성 데이터"""
    serial_no: str
    lot_no: str
    work_order_id: str
    product: dict
    design: DesignTrace
    cam: CAMTrace
    machining: MachiningTrace
    monitoring: Optional[MonitoringTrace]
    inspection: InspectionTrace
    quality: QualityTrace
    
    def to_dict(self) -> dict:
        """JSON 직렬화용"""
        return {
            "serial_no": self.serial_no,
            "lot_no": self.lot_no,
            "work_order_id": self.work_order_id,
            "product": self.product,
            "design": asdict(self.design),
            "cam": asdict(self.cam),
            "machining": asdict(self.machining),
            "monitoring": asdict(self.monitoring) if self.monitoring else None,
            "inspection": asdict(self.inspection),
            "quality": asdict(self.quality),
        }


async def get_full_traceability(
    db: AsyncSession,
    serial_no: str,
) -> FullTraceability:
    """
    개별 부품(시리얼 넘버)의 전체 제조 이력 조회
    
    설계 → CAM → 가공 → 모니터링 → 검사 → 품질 전 과정 추적
    """
    
    # 1. ProdResult에서 시작 (serial_no 기준)
    result_query = (
        select(ProdResult)
        .options(
            selectinload(ProdResult.work_order).selectinload(WorkOrder.product),
            selectinload(ProdResult.equipment),
        )
        .where(ProdResult.serial_no == serial_no)
    )
    prod_result = (await db.execute(result_query)).scalar_one_or_none()
    
    if not prod_result:
        raise ValueError(f"Serial number not found: {serial_no}")
    
    work_order = prod_result.work_order
    product = work_order.product
    equipment = prod_result.equipment
    
    # 2. 설계 정보 (Product + PMI)
    design = DesignTrace(
        cad_file=product.cad_file or f"{product.part_no}.step",
        pmi_file=product.pmi_file,
        pmi_features=await count_pmi_features(db, product.id),
        revision=product.revision or "A",
        released_at=product.created_at,
    )
    
    # 3. CAM 정보 (NC Program)
    nc_program = await get_nc_program(db, product.id, equipment.equipment_type)
    cam = CAMTrace(
        nc_program_id=nc_program.program_id if nc_program else "N/A",
        nc_program_file=nc_program.file_path if nc_program else "",
        cam_file=nc_program.cam_source if nc_program else None,
        toolpath_count=nc_program.toolpath_count if nc_program else 0,
        estimated_cycle_time=nc_program.cycle_time if nc_program else 0,
    )
    
    # 4. 가공 정보
    machining = MachiningTrace(
        machine_id=equipment.equipment_id,
        machine_name=equipment.equipment_name,
        cell=equipment.cell.cell_name if equipment.cell else "N/A",
        operator=prod_result.operator_id,
        start_time=prod_result.start_time,
        end_time=prod_result.end_time,
        actual_cycle_time=(
            (prod_result.end_time - prod_result.start_time).total_seconds()
            if prod_result.end_time else 0
        ),
        setup_time=prod_result.setup_time or 0,
    )
    
    # 5. 모니터링 데이터 (있는 경우)
    monitoring_data = await get_monitoring_data(
        db, equipment.id, prod_result.start_time, prod_result.end_time
    )
    monitoring = None
    if monitoring_data:
        monitoring = MonitoringTrace(
            spindle_load_avg=monitoring_data.spindle_load_avg,
            spindle_load_max=monitoring_data.spindle_load_max,
            feed_override_avg=monitoring_data.feed_override_avg,
            tool_changes=monitoring_data.tool_changes,
            tool_wear_mm=monitoring_data.tool_wear,
            vibration_level=monitoring_data.vibration,
            coolant_temp=monitoring_data.coolant_temp,
        )
    
    # 6. 검사 결과
    inspection_results = await get_inspection_results(
        db, work_order.id, serial_no
    )
    inspection = InspectionTrace(
        results=[r.to_dict() for r in inspection_results],
        total_characteristics=len(inspection_results),
        conforming_count=sum(1 for r in inspection_results if r.is_conforming),
        non_conforming_count=sum(1 for r in inspection_results if not r.is_conforming),
        inspection_time=inspection_results[0].measured_at if inspection_results else None,
        inspector=inspection_results[0].measured_by if inspection_results else None,
    )
    
    # 7. 품질 정보 (NCR, SPC)
    ncr_list = await get_ncr_by_serial(db, serial_no)
    cpk_values = await get_cpk_values(db, product.id)
    
    quality = QualityTrace(
        ncr_list=[n.ncr_no for n in ncr_list],
        ncr_open_count=sum(1 for n in ncr_list if n.status == "OPEN"),
        cpk_values=cpk_values,
        overall_quality_score=calculate_quality_score(
            inspection.conforming_count,
            inspection.total_characteristics,
            len(ncr_list),
        ),
    )
    
    return FullTraceability(
        serial_no=serial_no,
        lot_no=prod_result.lot_no,
        work_order_id=work_order.wo_id,
        product={
            "id": product.id,
            "part_no": product.part_no,
            "part_name": product.part_name,
        },
        design=design,
        cam=cam,
        machining=machining,
        monitoring=monitoring,
        inspection=inspection,
        quality=quality,
    )


async def get_lot_traceability(
    db: AsyncSession,
    lot_no: str,
) -> dict:
    """
    Lot 단위 추적성 - 동일 Lot의 모든 시리얼 요약
    """
    # Lot에 속한 모든 시리얼 조회
    serials_query = (
        select(ProdResult.serial_no)
        .where(ProdResult.lot_no == lot_no)
        .distinct()
    )
    serial_nos = (await db.execute(serials_query)).scalars().all()
    
    # 집계 통계
    total_qty = len(serial_nos)
    conforming_qty = 0
    ncr_count = 0
    
    for sn in serial_nos:
        trace = await get_full_traceability(db, sn)
        if trace.inspection.non_conforming_count == 0:
            conforming_qty += 1
        ncr_count += len(trace.quality.ncr_list)
    
    return {
        "lot_no": lot_no,
        "total_qty": total_qty,
        "conforming_qty": conforming_qty,
        "non_conforming_qty": total_qty - conforming_qty,
        "yield_rate": conforming_qty / total_qty if total_qty > 0 else 0,
        "ncr_count": ncr_count,
        "serial_numbers": list(serial_nos),
    }
```

#### 추적성 타임라인 뷰

```python
async def get_traceability_timeline(
    db: AsyncSession,
    serial_no: str,
) -> list[dict]:
    """
    시리얼 넘버의 제조 타임라인 (시각화용)
    """
    trace = await get_full_traceability(db, serial_no)
    
    timeline = []
    
    # 1. 작업지시 생성
    timeline.append({
        "event": "WORK_ORDER_CREATED",
        "timestamp": trace.machining.start_time - timedelta(hours=24),  # 예상
        "description": f"작업지시 {trace.work_order_id} 생성",
        "data": {"wo_id": trace.work_order_id, "qty": 1},
    })
    
    # 2. 가공 시작
    timeline.append({
        "event": "MACHINING_START",
        "timestamp": trace.machining.start_time,
        "description": f"{trace.machining.machine_name}에서 가공 시작",
        "data": {
            "machine": trace.machining.machine_id,
            "nc_program": trace.cam.nc_program_id,
        },
    })
    
    # 3. 가공 완료
    if trace.machining.end_time:
        timeline.append({
            "event": "MACHINING_END",
            "timestamp": trace.machining.end_time,
            "description": f"가공 완료 (Cycle: {trace.machining.actual_cycle_time:.0f}s)",
            "data": {"cycle_time": trace.machining.actual_cycle_time},
        })
    
    # 4. 검사 수행
    if trace.inspection.inspection_time:
        timeline.append({
            "event": "INSPECTION",
            "timestamp": trace.inspection.inspection_time,
            "description": f"검사 완료 ({trace.inspection.conforming_count}/{trace.inspection.total_characteristics} 적합)",
            "data": {
                "conforming": trace.inspection.conforming_count,
                "total": trace.inspection.total_characteristics,
            },
        })
    
    # 5. NCR 발생 (있는 경우)
    for ncr_no in trace.quality.ncr_list:
        ncr = await get_ncr(db, ncr_no)
        timeline.append({
            "event": "NCR_CREATED",
            "timestamp": ncr.created_at,
            "description": f"부적합 보고서 {ncr_no} 발생",
            "data": {"ncr_no": ncr_no, "status": ncr.status},
        })
    
    # 시간순 정렬
    timeline.sort(key=lambda x: x["timestamp"])
    
    return timeline
```

---

### 3. 에이전트 연계 상세

#### step-pmi-reader → cell-mes 연동

```python
# agents/cell-mes/src/app/services/pmi_integration.py

from pathlib import Path
from step_pmi_reader import extract_pmi  # libs/step-pmi-reader
from qif_converter import convert_pmi_to_qifplan  # libs/qif-converter


async def process_step_file(
    db: AsyncSession,
    step_file: Path,
    product_id: int,
) -> dict:
    """
    STEP 파일 처리 파이프라인
    
    1. PMI 추출 (step-pmi-reader)
    2. 검사계획 자동생성
    3. QIF 변환 (선택)
    4. DB 저장
    """
    
    # 1. PMI 추출
    pmi_data = await extract_pmi(step_file)
    
    # 2. 검사계획 생성
    plans = await generate_inspection_plan_from_pmi(pmi_data, product_id)
    
    # 3. DB 저장
    for plan in plans:
        db.add(plan)
    await db.commit()
    
    # 4. QIF 생성 (옵션)
    qif_xml = convert_pmi_to_qifplan(
        pmi_data,
        plan_id=f"PLAN-{product_id}-{datetime.now().strftime('%Y%m%d')}",
    )
    
    # QIF 파일 저장
    qif_path = step_file.parent / f"{step_file.stem}_inspection_plan.qif"
    qif_path.write_bytes(qif_xml)
    
    return {
        "pmi_features": len(pmi_data.get("dimensions", [])) + len(pmi_data.get("geometric_tolerances", [])),
        "inspection_plans_created": len(plans),
        "qif_file": str(qif_path),
    }
```

#### monitoring-data-replayer → cell-mes 연동

```python
# agents/cell-mes/src/app/services/monitoring_integration.py

from monitoring_data_replayer import parse_tdms, parse_log


async def import_monitoring_data(
    db: AsyncSession,
    tdms_file: Path,
    work_order_id: int,
) -> dict:
    """
    모니터링 데이터 가져오기
    
    1. TDMS/LOG 파싱
    2. 작업지시와 연결
    3. 이상 감지
    """
    
    # 1. 파싱
    if tdms_file.suffix == ".tdms":
        data = await parse_tdms(tdms_file)
    else:
        data = await parse_log(tdms_file)
    
    # 2. MonitoringData 저장
    monitoring = MonitoringData(
        work_order_id=work_order_id,
        spindle_load_avg=data.spindle_load.mean(),
        spindle_load_max=data.spindle_load.max(),
        feed_override_avg=data.feed_override.mean(),
        vibration_level=data.vibration.max() if data.vibration else None,
        recorded_at=data.timestamps[0],
    )
    db.add(monitoring)
    
    # 3. 이상 감지
    anomalies = detect_anomalies(data)
    if anomalies:
        # 알림 생성
        await create_monitoring_alert(db, work_order_id, anomalies)
    
    await db.commit()
    
    return {
        "data_points": len(data.timestamps),
        "anomalies_detected": len(anomalies),
    }
```

---

## 🔄 Closed-Loop 워크플로우

```
가공 시작
    │
    ▼
초도품 OMM 측정 ────────────────┐
    │                          │
    ▼                          ▼
편차 > 임계값?  ──Yes──▶  공구 보정 자동 적용
    │                          │
    No                         │
    │                          │
    ▼                          ▼
가공 계속  ◀───────────────────┘
    │
    ▼
Equator 최종 검사
    │
    ▼
SPC 차트 업데이트
    │
    ▼
추세 이상? ──Yes──▶  경고 알림 + 원인 분석
```

---

## 📊 API 엔드포인트 상세

### Digital Thread 핵심 API

#### PMI → 검사계획 자동생성

```http
POST /api/v1/digital-thread/generate-inspection-plans
Content-Type: multipart/form-data

step_file: (binary)
product_id: 123
generate_qif: true
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pmi_features_extracted": 24,
    "inspection_plans_created": 24,
    "plans": [
      {
        "id": 101,
        "characteristic": "외경 D1",
        "characteristic_type": "DIMENSION",
        "nominal": 50.0,
        "usl": 50.02,
        "lsl": 49.98,
        "inspection_type": "OMM",
        "sampling_plan": "PERIODIC",
        "frequency": 10,
        "is_critical": false
      },
      {
        "id": 102,
        "characteristic": "위치도 H1",
        "characteristic_type": "GDT",
        "tolerance_type": "position",
        "nominal": 0,
        "usl": 0.05,
        "lsl": 0,
        "datum_refs": ["A", "B", "C"],
        "material_condition": "MMC",
        "inspection_type": "EQUATOR",
        "sampling_plan": "100%",
        "is_critical": true
      }
    ],
    "qif_file": "/data/qif/PLAN-123-20260209.qif"
  }
}
```

#### 전체 추적성 조회

```http
GET /api/v1/digital-thread/traceability/{serial_no}
```

**Response:**
```json
{
  "serial_no": "SN-2026-00123",
  "lot_no": "LOT-001",
  "work_order_id": "WO-2026-0042",
  "product": {
    "id": 15,
    "part_no": "SHAFT-001",
    "part_name": "Main Shaft"
  },
  "design": {
    "cad_file": "SHAFT-001.step",
    "pmi_file": "SHAFT-001_pmi.json",
    "pmi_features": 24,
    "revision": "B",
    "released_at": "2026-01-15T09:00:00"
  },
  "cam": {
    "nc_program_id": "NC-SHAFT-001-v2",
    "nc_program_file": "/nc/SHAFT-001-v2.nc",
    "cam_file": "SHAFT-001.ncl",
    "toolpath_count": 8,
    "estimated_cycle_time": 2700
  },
  "machining": {
    "machine_id": "EQ-5",
    "machine_name": "CNC-01 (Mazak)",
    "cell": "CELL-01",
    "operator": "OP-001",
    "start_time": "2026-02-09T08:30:00",
    "end_time": "2026-02-09T09:15:00",
    "actual_cycle_time": 2680,
    "setup_time": 300
  },
  "monitoring": {
    "spindle_load_avg": 45.2,
    "spindle_load_max": 78.5,
    "feed_override_avg": 98.5,
    "tool_changes": 4,
    "tool_wear_mm": 0.12,
    "vibration_level": 2.3,
    "coolant_temp": 22.5
  },
  "inspection": {
    "results": [
      {
        "characteristic": "외경 D1",
        "nominal": 50.0,
        "measured_value": 50.008,
        "deviation": 0.008,
        "is_conforming": true
      }
    ],
    "total_characteristics": 24,
    "conforming_count": 24,
    "non_conforming_count": 0,
    "inspection_time": "2026-02-09T09:30:00",
    "inspector": "EQUATOR-01"
  },
  "quality": {
    "ncr_list": [],
    "ncr_open_count": 0,
    "cpk_values": {
      "외경 D1": 1.67,
      "위치도 H1": 1.45
    },
    "overall_quality_score": 100.0
  }
}
```

#### Lot 추적성 조회

```http
GET /api/v1/digital-thread/traceability/lot/{lot_no}
```

**Response:**
```json
{
  "lot_no": "LOT-001",
  "total_qty": 50,
  "conforming_qty": 48,
  "non_conforming_qty": 2,
  "yield_rate": 0.96,
  "ncr_count": 2,
  "serial_numbers": ["SN-2026-00101", "SN-2026-00102", "..."]
}
```

#### 추적성 타임라인

```http
GET /api/v1/digital-thread/traceability/{serial_no}/timeline
```

**Response:**
```json
{
  "serial_no": "SN-2026-00123",
  "timeline": [
    {
      "event": "WORK_ORDER_CREATED",
      "timestamp": "2026-02-08T14:00:00",
      "description": "작업지시 WO-2026-0042 생성",
      "data": {"wo_id": "WO-2026-0042", "qty": 50}
    },
    {
      "event": "MACHINING_START",
      "timestamp": "2026-02-09T08:30:00",
      "description": "CNC-01 (Mazak)에서 가공 시작",
      "data": {"machine": "EQ-5", "nc_program": "NC-SHAFT-001-v2"}
    },
    {
      "event": "MACHINING_END",
      "timestamp": "2026-02-09T09:15:00",
      "description": "가공 완료 (Cycle: 2680s)",
      "data": {"cycle_time": 2680}
    },
    {
      "event": "INSPECTION",
      "timestamp": "2026-02-09T09:30:00",
      "description": "검사 완료 (24/24 적합)",
      "data": {"conforming": 24, "total": 24}
    }
  ]
}
```

### 검사 계획 API

```http
# 제품별 검사계획 조회
GET /api/v1/quality/inspection-plans?product_id=123

# 개별 검사계획 조회
GET /api/v1/quality/inspection-plans/{plan_id}

# 검사계획 수동 생성
POST /api/v1/quality/inspection-plans
{
  "product_id": 123,
  "characteristic": "외경 D1",
  "characteristic_type": "DIMENSION",
  "nominal": 50.0,
  "usl": 50.02,
  "lsl": 49.98,
  "inspection_type": "OMM",
  "sampling_plan": "PERIODIC",
  "frequency": 10
}

# 검사계획 수정
PATCH /api/v1/quality/inspection-plans/{plan_id}
{
  "frequency": 5,
  "is_critical": true
}
```

### 측정 결과 API

```http
# 측정결과 등록
POST /api/v1/measurement/results
{
  "plan_id": 101,
  "work_order_id": 42,
  "lot_no": "LOT-001",
  "serial_no": "SN-2026-00123",
  "measured_value": 50.008,
  "source": "EQUATOR",
  "device_id": 1
}

# 작업지시별 측정결과 조회
GET /api/v1/measurement/results?work_order_id=42

# 시리얼별 측정결과 조회
GET /api/v1/measurement/results?serial_no=SN-2026-00123

# 벌크 등록 (Equator CSV 등)
POST /api/v1/measurement/results/bulk
Content-Type: multipart/form-data

file: (csv binary)
work_order_id: 42
source: EQUATOR
```

### SPC API

```http
# 관리도 조회
GET /api/v1/quality/spc/charts?plan_id=101

# 관리한계 자동계산
POST /api/v1/quality/spc/calculate-limits
{
  "plan_id": 101,
  "method": "XBAR_R",
  "subgroup_size": 5,
  "data_count": 25
}

# 공정능력 조회
GET /api/v1/quality/spc/capability?product_id=123

# SPC 데이터 포인트 추가
POST /api/v1/quality/spc/data-points
{
  "chart_id": 10,
  "subgroup_no": 26,
  "values": [50.002, 50.008, 50.005, 50.001, 50.006]
}
```

### 부적합 관리 API

```http
# NCR 생성
POST /api/v1/quality/ncr
{
  "work_order_id": 42,
  "serial_no": "SN-2026-00123",
  "inspection_result_id": 1001,
  "defect_type": "DIMENSION",
  "characteristic": "외경 D1",
  "specified_value": 50.0,
  "actual_value": 50.035
}

# NCR 조회
GET /api/v1/quality/ncr?status=OPEN
GET /api/v1/quality/ncr/{ncr_no}

# 처분 결정
PATCH /api/v1/quality/ncr/{ncr_no}/disposition
{
  "disposition": "REWORK",
  "root_cause": "공구 마모로 인한 치수 초과",
  "corrective_action": "공구 교체 및 보정값 재설정"
}

# NCR 종결
PATCH /api/v1/quality/ncr/{ncr_no}/close
{
  "verified_by": "QC-001",
  "verification_notes": "재가공 후 재검사 적합 확인"
}
```

### 모니터링 데이터 API

```http
# 모니터링 데이터 업로드
POST /api/v1/monitoring/upload
Content-Type: multipart/form-data

file: (tdms or log binary)
work_order_id: 42
machine_id: 5

# 모니터링 데이터 조회
GET /api/v1/monitoring/data?work_order_id=42
GET /api/v1/monitoring/data?machine_id=5&from=2026-02-09T00:00:00&to=2026-02-09T23:59:59

# 이상 알림 조회
GET /api/v1/monitoring/alerts?status=OPEN
```

---

## 🎯 구현 우선순위

### Phase 1 (1주): 검사 데이터 기반
- [ ] InspectionPlan, InspectionResult 모델
- [ ] 수동 검사결과 입력 API
- [ ] 작업지시별 검사현황 조회

### Phase 2 (1주): SPC 기초
- [ ] Control Chart (X-bar R)
- [ ] Cp/Cpk 자동 계산
- [ ] 관리 이탈 알림 (Western Electric Rules)

### Phase 3 (1주): 측정 시스템 연동
- [ ] measurement-collector 서비스 구축
- [ ] OMM DPRNT 파싱
- [ ] Equator CSV 연동

### Phase 4 (1주): Digital Thread 연계

#### Day 1-2: PMI → 검사계획 자동생성
- [ ] `pmi_integration.py` 서비스 모듈 생성
- [ ] PMI 유형별 검사계획 매핑 테이블 구현
- [ ] GD&T 14가지 공차 유형 지원
- [ ] CTQ 자동 판별 로직
- [ ] `POST /api/v1/digital-thread/generate-inspection-plans` API

#### Day 3-4: 전체 추적성 쿼리
- [ ] `FullTraceability` 데이터 클래스
- [ ] `get_full_traceability()` 함수 (시리얼 기준)
- [ ] `get_lot_traceability()` 함수 (Lot 기준)
- [ ] `get_traceability_timeline()` 함수 (타임라인)
- [ ] 추적성 API 3개 엔드포인트

#### Day 5: 에이전트 연동
- [ ] step-pmi-reader → cell-mes 연동 테스트
- [ ] monitoring-data-replayer → cell-mes 연동 테스트
- [ ] E2E 테스트 (STEP 업로드 → 검사계획 → 측정 → 추적성 조회)

### Phase 5 (1주): QMS 확장
- [ ] NCR 관리
- [ ] CAPA 연결
- [ ] 품질 대시보드

---

*Created: 2026-02-04*  
*Updated: 2026-02-09 - Digital Thread 연계 상세 설계 추가*
