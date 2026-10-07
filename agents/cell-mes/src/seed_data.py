"""
MES 통합 시드 데이터 생성 스크립트

기준일(base_date) 기반으로 모든 데이터를 일관되게 생성합니다.
마스터, 생산, 품질, 다운타임, 알람, 설비이력을 한 번에 생성합니다.

사용법:
    cd agents/cell-mes
    uv run python -m src.seed_data                    # 기준일 = 오늘
    uv run python -m src.seed_data --date 2026-02-10  # 기준일 = 2/10
    uv run python -m src.seed_data --days 60          # 60일치 데이터 생성
    uv run python -m src.seed_data --validate         # 검증만
"""

import argparse
import asyncio
import random
from datetime import datetime, timedelta, timezone, date
from sqlalchemy import select, delete, func, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import engine, AsyncSessionLocal
from src.app.db.base import Base
from src.app.models.equipment import Equipment, EqLog, EquipmentStatusHistory
from src.app.models.master import (
    ProcessCategory,
    Cell,
    StdProcess,
    Product,
    ProcessRouting,
    Scenario,
)
from src.app.models.production import WorkOrder, ProdResult
from src.app.models.user import User
from src.app.models.downtime import DowntimeReason, Downtime
from src.app.models.alarm import AlarmDefinition, Alarm
from src.app.models.quality import (
    InspectionPlan,
    InspectionResult,
    NonConformance,
    SPCChart,
    SPCDataPoint,
    MeasurementDevice,
)
from src.app.core.security import get_password_hash


# ============================================================
# 마스터 데이터 상수
# ============================================================

PROCESS_CATEGORIES = [
    {"code": "MACHINING", "name": "기계가공"},
    {"code": "INSPECTION", "name": "검사"},
    {"code": "LOGISTICS", "name": "물류"},
]

CELLS = [
    {"code": "CELL-01", "name": "CNC 셀 1", "location": "A동 1층"},
    {"code": "CELL-02", "name": "CNC 셀 2", "location": "A동 1층"},
]

EQUIPMENTS = [
    {
        "eq_code": "EQ-CNC-001",
        "aas_id": "aas:cnc:doosan-001",
        "eq_name": "CNC-001",
        "model_name": "Doosan DVF 5000",
        "equipment_type": "CNC",
        "location": "Building A",
        "cell_code": "CELL-01",
        "connection_config": {"ip": "192.168.1.101", "port": 502, "protocol": "modbus"},
        "spec_data": {
            "manufacturer": "Doosan",
            "max_rpm": 20000,
            "max_power_kw": 22,
            "work_area_mm": {"x": 850, "y": 520, "z": 510},
        },
        "last_data": {
            "spindle_rpm": 15000,
            "load_percent": 45.5,
            "temperature_c": 42,
            "feed_rate": 3000,
            "tool_no": 5,
        },
        "current_status": "RUN",
    },
    {
        "eq_code": "EQ-CNC-002",
        "aas_id": "aas:cnc:doosan-002",
        "eq_name": "CNC-002",
        "model_name": "Doosan DNM 500II",
        "equipment_type": "CNC",
        "location": "Building A",
        "cell_code": "CELL-01",
        "connection_config": {"ip": "192.168.1.102", "port": 502, "protocol": "modbus"},
        "spec_data": {
            "manufacturer": "Doosan",
            "max_rpm": 15000,
            "max_power_kw": 18.5,
            "work_area_mm": {"x": 1020, "y": 540, "z": 510},
        },
        "last_data": {
            "spindle_rpm": 12000,
            "load_percent": 38.2,
            "temperature_c": 38,
            "feed_rate": 2500,
            "tool_no": 3,
        },
        "current_status": "RUN",
    },
    {
        "eq_code": "EQ-CNC-003",
        "aas_id": "aas:cnc:hwacheon-001",
        "eq_name": "CNC-003",
        "model_name": "Hwacheon Hi-Tech 450C",
        "equipment_type": "CNC",
        "location": "Building A",
        "cell_code": "CELL-02",
        "connection_config": {"ip": "192.168.1.103", "port": 502, "protocol": "modbus"},
        "spec_data": {
            "manufacturer": "Hwacheon",
            "max_rpm": 18000,
            "max_power_kw": 15,
            "work_area_mm": {"x": 700, "y": 500, "z": 450},
        },
        "last_data": {
            "spindle_rpm": 0,
            "load_percent": 0,
            "temperature_c": 25,
            "feed_rate": 0,
            "tool_no": 1,
        },
        "current_status": "STOP",
    },
    {
        "eq_code": "EQ-CNC-004",
        "aas_id": "aas:cnc:mazak-001",
        "eq_name": "CNC-004",
        "model_name": "Mazak VTC-300C",
        "equipment_type": "CNC",
        "location": "Building A",
        "cell_code": "CELL-02",
        "connection_config": {"ip": "192.168.1.104", "port": 502, "protocol": "modbus"},
        "spec_data": {
            "manufacturer": "Mazak",
            "max_rpm": 12000,
            "max_power_kw": 22,
            "work_area_mm": {"x": 1050, "y": 530, "z": 510},
        },
        "last_data": {
            "spindle_rpm": 8500,
            "load_percent": 52.1,
            "temperature_c": 45,
            "feed_rate": 1800,
            "tool_no": 8,
        },
        "current_status": "RUN",
    },
    {
        "eq_code": "EQ-ROBOT-001",
        "aas_id": "aas:robot:fanuc-001",
        "eq_name": "ROBOT-001",
        "model_name": "FANUC M-20iD/25",
        "equipment_type": "ROBOT",
        "location": "Building A",
        "cell_code": "CELL-01",
        "connection_config": {"ip": "192.168.1.201", "port": 8193, "protocol": "ethernet_ip"},
        "spec_data": {
            "manufacturer": "FANUC",
            "payload_kg": 25,
            "reach_mm": 1831,
            "axes": 6,
            "repeatability_mm": 0.04,
        },
        "last_data": {
            "j1_angle": 45.2,
            "j2_angle": -30.5,
            "j3_angle": 60.0,
            "j4_angle": 0.0,
            "j5_angle": -45.0,
            "j6_angle": 90.0,
            "gripper_open": False,
            "cycle_count": 1523,
        },
        "current_status": "RUN",
    },
    {
        "eq_code": "EQ-ROBOT-002",
        "aas_id": "aas:robot:kuka-001",
        "eq_name": "ROBOT-002",
        "model_name": "KUKA KR 16 R2010",
        "equipment_type": "ROBOT",
        "location": "Building A",
        "cell_code": "CELL-01",
        "connection_config": {"ip": "192.168.1.202", "port": 7000, "protocol": "krl"},
        "spec_data": {
            "manufacturer": "KUKA",
            "payload_kg": 16,
            "reach_mm": 2010,
            "axes": 6,
            "repeatability_mm": 0.05,
        },
        "last_data": {
            "j1_angle": -15.0,
            "j2_angle": 45.0,
            "j3_angle": -30.0,
            "j4_angle": 0.0,
            "j5_angle": 60.0,
            "j6_angle": -90.0,
            "gripper_open": True,
            "cycle_count": 892,
        },
        "current_status": "STOP",
    },
    {
        "eq_code": "EQ-AMR-001",
        "aas_id": "aas:amr:mir-001",
        "eq_name": "AMR-001",
        "model_name": "MiR 250",
        "equipment_type": "AMR",
        "location": "Building A",
        "cell_code": None,
        "connection_config": {"ip": "192.168.1.150", "port": 80, "protocol": "rest"},
        "spec_data": {
            "manufacturer": "MiR",
            "payload_kg": 250,
            "max_speed_mps": 2.0,
            "battery_capacity_ah": 40,
        },
        "last_data": {
            "battery_percent": 78,
            "position_x": 12.5,
            "position_y": 8.3,
            "heading_deg": 45,
            "velocity_mps": 0.8,
            "mission_id": "M-2024-0145",
        },
        "current_status": "RUN",
    },
    {
        "eq_code": "EQ-AMR-002",
        "aas_id": "aas:amr:mir-002",
        "eq_name": "AMR-002",
        "model_name": "MiR 100",
        "equipment_type": "AMR",
        "location": "Building A",
        "cell_code": None,
        "connection_config": {"ip": "192.168.1.151", "port": 80, "protocol": "rest"},
        "spec_data": {
            "manufacturer": "MiR",
            "payload_kg": 100,
            "max_speed_mps": 1.5,
            "battery_capacity_ah": 24,
        },
        "last_data": {
            "battery_percent": 45,
            "position_x": 5.2,
            "position_y": 15.1,
            "heading_deg": 180,
            "velocity_mps": 0.0,
            "mission_id": None,
        },
        "current_status": "STOP",
    },
    {
        "eq_code": "EQ-PLC-001",
        "aas_id": "aas:plc:siemens-001",
        "eq_name": "PLC-001",
        "model_name": "Siemens S7-1500",
        "equipment_type": "PLC",
        "location": "Building A",
        "cell_code": "CELL-01",
        "connection_config": {"ip": "192.168.1.50", "port": 102, "protocol": "s7"},
        "spec_data": {
            "manufacturer": "Siemens",
            "cpu_model": "CPU 1515-2 PN",
            "memory_kb": 750,
            "io_points": 256,
        },
        "last_data": {
            "cpu_load_percent": 35,
            "cycle_time_ms": 5.2,
            "error_count": 0,
            "running_program": "MAIN_CTRL",
        },
        "current_status": "RUN",
    },
]

STD_PROCESSES = [
    {
        "code": "LOAD",
        "name": "소재 투입",
        "description": "원자재 또는 반제품을 가공 설비에 투입",
        "category_code": "LOGISTICS",
        "equipment_type": "ROBOT",
        "cycle_time_sec": 30,
        "setup_time_sec": 0,
    },
    {
        "code": "MILL",
        "name": "밀링 가공",
        "description": "CNC 밀링 머신으로 절삭 가공",
        "category_code": "MACHINING",
        "equipment_type": "CNC",
        "cycle_time_sec": 120,
        "setup_time_sec": 300,
    },
    {
        "code": "TURN",
        "name": "선반 가공",
        "description": "CNC 선반으로 회전 절삭 가공",
        "category_code": "MACHINING",
        "equipment_type": "CNC",
        "cycle_time_sec": 90,
        "setup_time_sec": 240,
    },
    {
        "code": "DRILL",
        "name": "드릴 가공",
        "description": "홀 가공 및 탭핑",
        "category_code": "MACHINING",
        "equipment_type": "CNC",
        "cycle_time_sec": 60,
        "setup_time_sec": 180,
    },
    {
        "code": "GRIND",
        "name": "연삭 가공",
        "description": "정밀 연삭 가공",
        "category_code": "MACHINING",
        "equipment_type": "CNC",
        "cycle_time_sec": 180,
        "setup_time_sec": 360,
    },
    {
        "code": "WASH",
        "name": "세척",
        "description": "가공 후 절삭유 및 칩 세척",
        "category_code": "MACHINING",
        "equipment_type": "ROBOT",
        "cycle_time_sec": 45,
        "setup_time_sec": 0,
    },
    {
        "code": "INSP",
        "name": "검사",
        "description": "치수 및 외관 검사",
        "category_code": "INSPECTION",
        "equipment_type": "ROBOT",
        "cycle_time_sec": 60,
        "setup_time_sec": 60,
    },
    {
        "code": "ASSEM",
        "name": "조립",
        "description": "부품 조립 작업",
        "category_code": "MACHINING",
        "equipment_type": "ROBOT",
        "cycle_time_sec": 120,
        "setup_time_sec": 120,
    },
    {
        "code": "PACK",
        "name": "포장",
        "description": "완제품 포장",
        "category_code": "LOGISTICS",
        "equipment_type": "ROBOT",
        "cycle_time_sec": 30,
        "setup_time_sec": 0,
    },
    {
        "code": "UNLOAD",
        "name": "제품 반출",
        "description": "완제품 반출 및 적재",
        "category_code": "LOGISTICS",
        "equipment_type": "AMR",
        "cycle_time_sec": 45,
        "setup_time_sec": 0,
    },
]

PRODUCTS = [
    {
        "code": "PART-A100",
        "name": "알루미늄 브라켓 A형",
        "unit": "EA",
        "routings": [
            {"process_code": "LOAD", "sequence": 10},
            {"process_code": "MILL", "sequence": 20},
            {"process_code": "DRILL", "sequence": 30},
            {"process_code": "WASH", "sequence": 40},
            {"process_code": "INSP", "sequence": 50},
            {"process_code": "UNLOAD", "sequence": 60},
        ],
    },
    {
        "code": "PART-B200",
        "name": "스틸 샤프트 B형",
        "unit": "EA",
        "routings": [
            {"process_code": "LOAD", "sequence": 10},
            {"process_code": "TURN", "sequence": 20},
            {"process_code": "GRIND", "sequence": 30},
            {"process_code": "WASH", "sequence": 40},
            {"process_code": "INSP", "sequence": 50},
            {"process_code": "UNLOAD", "sequence": 60},
        ],
    },
    {
        "code": "PART-C300",
        "name": "티타늄 플레이트 C형",
        "unit": "EA",
        "routings": [
            {"process_code": "LOAD", "sequence": 10},
            {"process_code": "MILL", "sequence": 20},
            {"process_code": "DRILL", "sequence": 30},
            {"process_code": "GRIND", "sequence": 40},
            {"process_code": "WASH", "sequence": 50},
            {"process_code": "INSP", "sequence": 60},
            {"process_code": "UNLOAD", "sequence": 70},
        ],
    },
    {
        "code": "ASSY-D100",
        "name": "구동 어셈블리",
        "unit": "SET",
        "routings": [
            {"process_code": "LOAD", "sequence": 10},
            {"process_code": "ASSEM", "sequence": 20},
            {"process_code": "INSP", "sequence": 30},
            {"process_code": "PACK", "sequence": 40},
            {"process_code": "UNLOAD", "sequence": 50},
        ],
    },
    {
        "code": "PART-E500",
        "name": "정밀 기어",
        "unit": "EA",
        "routings": [
            {"process_code": "LOAD", "sequence": 10},
            {"process_code": "TURN", "sequence": 20},
            {"process_code": "MILL", "sequence": 30},
            {"process_code": "GRIND", "sequence": 40},
            {"process_code": "WASH", "sequence": 50},
            {"process_code": "INSP", "sequence": 60},
            {"process_code": "UNLOAD", "sequence": 70},
        ],
    },
]

SCENARIOS = [
    {
        "code": "SCN-001",
        "product_code": "PART-A100",
        "name": "A100 표준 가공",
        "file_path": "scenarios/a100_standard.json",
    },
    {
        "code": "SCN-002",
        "product_code": "PART-A100",
        "name": "A100 급속 가공",
        "file_path": "scenarios/a100_fast.json",
    },
    {
        "code": "SCN-003",
        "product_code": "PART-B200",
        "name": "B200 표준 가공",
        "file_path": "scenarios/b200_standard.json",
    },
    {
        "code": "SCN-004",
        "product_code": "PART-C300",
        "name": "C300 정밀 가공",
        "file_path": "scenarios/c300_precision.json",
    },
    {
        "code": "SCN-005",
        "product_code": "ASSY-D100",
        "name": "D100 조립 시나리오",
        "file_path": "scenarios/d100_assembly.json",
    },
    {
        "code": "SCN-006",
        "product_code": "PART-E500",
        "name": "E500 기어 가공",
        "file_path": "scenarios/e500_gear.json",
    },
]

DOWNTIME_REASONS = [
    {"code": "DT-PM", "name": "예방 보전", "category": "PLANNED", "description": "정기 예방 보전"},
    {"code": "DT-BRK", "name": "휴식 시간", "category": "PLANNED", "description": "교대 휴식"},
    {
        "code": "DT-MTG",
        "name": "미팅/교육",
        "category": "PLANNED",
        "description": "정기 미팅 또는 교육",
    },
    {
        "code": "DT-SETUP",
        "name": "품목 변경",
        "category": "SETUP",
        "description": "다른 품목으로 셋업 변경",
    },
    {
        "code": "DT-TOOL",
        "name": "공구 교체",
        "category": "SETUP",
        "description": "공구 마모로 인한 교체",
    },
    {"code": "DT-JIG", "name": "지그 교체", "category": "SETUP", "description": "지그/픽스처 교체"},
    {"code": "DT-MECH", "name": "기계 고장", "category": "UNPLANNED", "description": "기계적 고장"},
    {
        "code": "DT-ELEC",
        "name": "전기 고장",
        "category": "UNPLANNED",
        "description": "전기/전자 고장",
    },
    {
        "code": "DT-PROG",
        "name": "프로그램 오류",
        "category": "UNPLANNED",
        "description": "NC 프로그램 오류",
    },
    {
        "code": "DT-MAT",
        "name": "자재 대기",
        "category": "UNPLANNED",
        "description": "원자재 공급 대기",
    },
    {
        "code": "DT-QUAL",
        "name": "품질 문제",
        "category": "UNPLANNED",
        "description": "품질 이상으로 인한 정지",
    },
    {"code": "DT-OTHER", "name": "기타", "category": "UNPLANNED", "description": "기타 사유"},
]

ALARM_DEFINITIONS = [
    {
        "code": "ALM-SPINDLE-TEMP",
        "name": "스핀들 과열",
        "severity": "CRITICAL",
        "category": "EQUIPMENT",
        "description": "스핀들 온도 임계값 초과",
        "recommended_action": "즉시 가공 중지 후 냉각 필요",
        "auto_stop": True,
    },
    {
        "code": "ALM-SPINDLE-LOAD",
        "name": "스핀들 과부하",
        "severity": "WARNING",
        "category": "EQUIPMENT",
        "description": "스핀들 부하 80% 초과",
        "recommended_action": "이송 속도 조정 권장",
    },
    {
        "code": "ALM-COOLANT-LOW",
        "name": "절삭유 부족",
        "severity": "WARNING",
        "category": "EQUIPMENT",
        "description": "절삭유 탱크 잔량 부족",
        "recommended_action": "절삭유 보충 필요",
    },
    {
        "code": "ALM-AXIS-ERROR",
        "name": "축 이상",
        "severity": "EMERGENCY",
        "category": "EQUIPMENT",
        "description": "축 구동 오류 감지",
        "recommended_action": "즉시 설비 점검 필요",
        "auto_stop": True,
    },
    {
        "code": "ALM-CYCLE-OVER",
        "name": "사이클 타임 초과",
        "severity": "INFO",
        "category": "PROCESS",
        "description": "표준 사이클 타임 대비 20% 초과",
    },
    {
        "code": "ALM-TOOL-LIFE",
        "name": "공구 수명 경고",
        "severity": "WARNING",
        "category": "PROCESS",
        "description": "공구 수명 90% 도달",
        "recommended_action": "공구 교체 준비",
    },
    {
        "code": "ALM-SPC-OOC",
        "name": "SPC 관리 이탈",
        "severity": "CRITICAL",
        "category": "QUALITY",
        "description": "SPC 관리한계 이탈",
        "recommended_action": "공정 점검 및 조치 필요",
    },
    {
        "code": "ALM-NG-RATE",
        "name": "불량률 초과",
        "severity": "WARNING",
        "category": "QUALITY",
        "description": "불량률 기준 초과",
    },
    {
        "code": "ALM-DOOR-OPEN",
        "name": "도어 개방",
        "severity": "EMERGENCY",
        "category": "SAFETY",
        "description": "가공 중 안전 도어 개방 감지",
        "auto_stop": True,
    },
    {
        "code": "ALM-ESTOP",
        "name": "비상 정지",
        "severity": "EMERGENCY",
        "category": "SAFETY",
        "description": "비상 정지 버튼 작동",
        "auto_stop": True,
    },
]

# 검사 특성 (제품별 품질 검사용)
INSPECTION_CHARACTERISTICS = [
    {"name": "외경", "nominal": 50.0, "lsl": 49.95, "usl": 50.05, "unit": "mm"},
    {"name": "내경", "nominal": 25.0, "lsl": 24.97, "usl": 25.03, "unit": "mm"},
    {"name": "길이", "nominal": 100.0, "lsl": 99.9, "usl": 100.1, "unit": "mm"},
    {"name": "표면조도", "nominal": 1.6, "lsl": 0.8, "usl": 3.2, "unit": "Ra"},
]

# 제품-시나리오 매핑
PRODUCT_SCENARIO_MAP = {
    "PART-A100": "A100 표준 가공",
    "PART-B200": "B200 표준 가공",
    "PART-C300": "C300 정밀 가공",
    "ASSY-D100": "D100 조립 시나리오",
    "PART-E500": "E500 기어 가공",
}


# ============================================================
# 유틸리티 함수
# ============================================================


def make_lot_no(base_date: date, seq: int) -> str:
    """기준일 기반 LOT 번호 생성: LOT-YYYYMMDD-NNN"""
    return f"LOT-{base_date.strftime('%Y%m%d')}-{seq:03d}"


def make_lot_no_for_date(target_date: date, seq: int) -> str:
    """특정 날짜 기반 LOT 번호 생성"""
    return f"LOT-{target_date.strftime('%Y%m%d')}-{seq:03d}"


def make_ncr_no(base_date: date, seq: int) -> str:
    """기준일 기반 NCR 번호 생성: NCR-YYYYMMDD-NNN"""
    return f"NCR-{base_date.strftime('%Y%m%d')}-{seq:03d}"


def date_to_datetime(d: date, hour: int = 8, minute: int = 0) -> datetime:
    """date를 timezone-aware datetime으로 변환"""
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)


# ============================================================
# 데이터 삭제
# ============================================================


async def clear_existing_data(session: AsyncSession):
    """기존 데이터 전체 삭제 (FK 역순)"""
    print("기존 데이터 삭제 중...")

    # 품질 데이터
    await session.execute(delete(SPCDataPoint))
    await session.execute(delete(SPCChart))
    await session.execute(delete(NonConformance))
    await session.execute(delete(InspectionResult))
    await session.execute(delete(InspectionPlan))
    await session.execute(delete(MeasurementDevice))

    # 알람/다운타임
    await session.execute(delete(Alarm))
    await session.execute(delete(AlarmDefinition))
    await session.execute(delete(Downtime))
    await session.execute(delete(DowntimeReason))

    # 설비 이력
    await session.execute(delete(EquipmentStatusHistory))

    # 생산
    await session.execute(delete(ProdResult))
    await session.execute(delete(WorkOrder))

    # 마스터
    await session.execute(delete(Scenario))
    await session.execute(delete(ProcessRouting))
    await session.execute(delete(Product))
    await session.execute(delete(StdProcess))
    await session.execute(delete(ProcessCategory))
    await session.execute(delete(EqLog))
    await session.execute(delete(Equipment))
    await session.execute(delete(Cell))
    await session.execute(delete(User))

    await session.commit()
    print("기존 데이터 삭제 완료")


# ============================================================
# 마스터 데이터 시드
# ============================================================


async def seed_users(session: AsyncSession):
    """기본 사용자 데이터 시드"""
    print("사용자 데이터 생성 중...")
    users_data = [
        {"username": "admin", "password": "admin123", "role": "ADMIN"},
        {"username": "operator", "password": "operator123", "role": "OPERATOR"},
    ]
    for user_data in users_data:
        user = User(
            username=user_data["username"],
            password_hash=get_password_hash(user_data["password"]),
            role=user_data["role"],
        )
        session.add(user)
    await session.commit()
    print(f"  {len(users_data)}명의 사용자 생성 완료 (admin/admin123, operator/operator123)")


async def seed_process_categories(session: AsyncSession) -> dict[str, ProcessCategory]:
    """공정 카테고리 데이터 시드"""
    print("공정 카테고리 데이터 생성 중...")
    category_map = {}
    for cat_data in PROCESS_CATEGORIES:
        category = ProcessCategory(code=cat_data["code"], name=cat_data["name"])
        session.add(category)
        category_map[cat_data["code"]] = category
    await session.commit()
    print(f"  {len(PROCESS_CATEGORIES)}개 공정 카테고리 생성 완료")
    return category_map


async def seed_cells(session: AsyncSession) -> dict[str, Cell]:
    """제조 셀 데이터 시드"""
    print("제조 셀 데이터 생성 중...")
    cell_map = {}
    for cell_data in CELLS:
        cell = Cell(
            code=cell_data["code"],
            name=cell_data["name"],
            location=cell_data.get("location"),
        )
        session.add(cell)
        cell_map[cell_data["code"]] = cell
    await session.commit()
    print(f"  {len(CELLS)}개 제조 셀 생성 완료")
    return cell_map


async def seed_equipments(
    session: AsyncSession, cell_map: dict[str, Cell], base_date: date
) -> dict[str, Equipment]:
    """설비 데이터 시드"""
    print("설비 데이터 생성 중...")
    eq_map = {}
    base_dt = date_to_datetime(base_date)
    for eq_data in EQUIPMENTS:
        cell_code = eq_data.get("cell_code")
        cell_id = cell_map[cell_code].id if cell_code and cell_code in cell_map else None
        eq = Equipment(
            eq_code=eq_data["eq_code"],
            aas_id=eq_data["aas_id"],
            eq_name=eq_data["eq_name"],
            model_name=eq_data["model_name"],
            equipment_type=eq_data["equipment_type"],
            location=eq_data.get("location"),
            cell_id=cell_id,
            connection_config=eq_data["connection_config"],
            spec_data=eq_data["spec_data"],
            last_data=eq_data["last_data"],
            current_status=eq_data["current_status"],
            last_connected_at=base_dt if eq_data["current_status"] == "RUN" else None,
        )
        session.add(eq)
        eq_map[eq_data["eq_name"]] = eq
    await session.commit()
    print(f"  {len(EQUIPMENTS)}개 설비 생성 완료")
    return eq_map


async def seed_std_processes(
    session: AsyncSession, category_map: dict[str, ProcessCategory]
) -> dict[str, StdProcess]:
    """표준 공정 데이터 시드"""
    print("표준 공정 데이터 생성 중...")
    process_map = {}
    for proc_data in STD_PROCESSES:
        category_code = proc_data.get("category_code")
        category_id = (
            category_map[category_code].id
            if category_code and category_code in category_map
            else None
        )
        proc = StdProcess(
            code=proc_data["code"],
            name=proc_data["name"],
            description=proc_data["description"],
            category_id=category_id,
            equipment_type=proc_data.get("equipment_type"),
            cycle_time_sec=proc_data.get("cycle_time_sec", 60),
            setup_time_sec=proc_data.get("setup_time_sec", 0),
        )
        session.add(proc)
        process_map[proc_data["code"]] = proc
    await session.commit()
    print(f"  {len(STD_PROCESSES)}개 표준 공정 생성 완료")
    return process_map


async def seed_products_and_routings(
    session: AsyncSession, process_map: dict[str, StdProcess]
) -> dict[str, Product]:
    """제품 및 공정 라우팅 데이터 시드"""
    print("제품 및 공정 라우팅 데이터 생성 중...")
    product_map = {}
    for prod_data in PRODUCTS:
        product = Product(
            code=prod_data["code"],
            name=prod_data["name"],
            unit=prod_data["unit"],
        )
        session.add(product)
        await session.flush()
        for routing_data in prod_data["routings"]:
            std_process = process_map[routing_data["process_code"]]
            routing = ProcessRouting(
                product_id=product.id,
                std_process_id=std_process.id,
                sequence=routing_data["sequence"],
                revision="A",
            )
            session.add(routing)
        product_map[prod_data["code"]] = product
    await session.commit()
    print(f"  {len(PRODUCTS)}개 제품 및 라우팅 생성 완료")
    return product_map


async def seed_scenarios(
    session: AsyncSession, product_map: dict[str, Product]
) -> dict[str, Scenario]:
    """시나리오 데이터 시드"""
    print("시나리오 데이터 생성 중...")
    scenario_map = {}
    for scen_data in SCENARIOS:
        product = product_map.get(scen_data["product_code"])
        scenario = Scenario(
            code=scen_data["code"],
            product_id=product.id if product else None,
            name=scen_data["name"],
            file_path=scen_data["file_path"],
            is_active=True,
        )
        session.add(scenario)
        scenario_map[scen_data["name"]] = scenario
    await session.commit()
    print(f"  {len(SCENARIOS)}개 시나리오 생성 완료")
    return scenario_map


async def seed_downtime_reasons(session: AsyncSession) -> dict[str, DowntimeReason]:
    """다운타임 사유 코드 시드"""
    print("다운타임 사유 코드 생성 중...")
    reason_map = {}
    for reason_data in DOWNTIME_REASONS:
        reason = DowntimeReason(
            code=reason_data["code"],
            name=reason_data["name"],
            category=reason_data["category"],
            description=reason_data.get("description"),
            is_active=True,
        )
        session.add(reason)
        reason_map[reason_data["code"]] = reason
    await session.commit()
    print(f"  {len(DOWNTIME_REASONS)}개 다운타임 사유 생성 완료")
    return reason_map


async def seed_alarm_definitions(session: AsyncSession) -> dict[str, AlarmDefinition]:
    """알람 정의 시드"""
    print("알람 정의 생성 중...")
    alarm_def_map = {}
    for alarm_data in ALARM_DEFINITIONS:
        alarm_def = AlarmDefinition(
            code=alarm_data["code"],
            name=alarm_data["name"],
            severity=alarm_data["severity"],
            category=alarm_data["category"],
            description=alarm_data.get("description"),
            recommended_action=alarm_data.get("recommended_action"),
            auto_stop=alarm_data.get("auto_stop", False),
            is_active=True,
        )
        session.add(alarm_def)
        alarm_def_map[alarm_data["code"]] = alarm_def
    await session.commit()
    print(f"  {len(ALARM_DEFINITIONS)}개 알람 정의 생성 완료")
    return alarm_def_map


# ============================================================
# 작업지시 & 생산실적 시드
# ============================================================


async def seed_work_orders_and_results(
    session: AsyncSession,
    product_map: dict[str, Product],
    scenario_map: dict[str, Scenario],
    eq_map: dict[str, Equipment],
    base_date: date,
    days: int = 30,
) -> list[tuple]:
    """작업지시 및 생산 실적 데이터 시드 (기준일 기반)"""
    print(f"작업지시 및 생산 실적 데이터 생성 중 (기준일: {base_date}, {days}일간)...")

    cnc_equipments = [eq for name, eq in eq_map.items() if "CNC" in name]
    product_codes = list(product_map.keys())

    work_order_configs = []
    daily_lot_counters = {}  # 일자별 LOT 순번 추적

    # 과거 days일 + 오늘 데이터 생성
    for days_ago in range(days, -1, -1):
        target_date = base_date - timedelta(days=days_ago)
        is_weekend = target_date.weekday() >= 5
        daily_orders = random.randint(1, 3) if is_weekend else random.randint(2, 5)

        if target_date not in daily_lot_counters:
            daily_lot_counters[target_date] = 0

        for _ in range(daily_orders):
            daily_lot_counters[target_date] += 1
            product_code = random.choice(product_codes)
            target_qty = random.choice([20, 30, 40, 50, 60, 80, 100, 120, 150])

            # 상태 결정 (기준일 기반)
            if days_ago == 0:
                status = random.choices(
                    ["DONE", "RUNNING", "READY", "PAUSE", "ERROR"],
                    weights=[40, 30, 15, 10, 5],
                )[0]
            elif days_ago == 1:
                status = random.choices(["DONE", "RUNNING", "PAUSE"], weights=[80, 15, 5])[0]
            else:
                status = random.choices(["DONE", "ERROR"], weights=[95, 5])[0]

            work_order_configs.append(
                {
                    "lot_no": make_lot_no_for_date(target_date, daily_lot_counters[target_date]),
                    "product_code": product_code,
                    "target_qty": target_qty,
                    "status": status,
                    "days_ago": days_ago,
                    "target_date": target_date,
                }
            )

    # 기준일 추가 READY 3건 (스케줄러 테스트용)
    for i in range(3):
        daily_lot_counters[base_date] = daily_lot_counters.get(base_date, 0) + 1
        work_order_configs.append(
            {
                "lot_no": make_lot_no_for_date(base_date, daily_lot_counters[base_date]),
                "product_code": random.choice(product_codes),
                "target_qty": random.choice([50, 80, 100]),
                "status": "READY",
                "days_ago": 0,
                "target_date": base_date,
            }
        )

    # 기준일 추가 스케줄링된 작업지시 6건 (Gantt 차트용) — start_time 고정
    scheduled_slots = [
        {"hour": 7,  "status": "DONE",    "target_qty": 80},
        {"hour": 8,  "status": "DONE",    "target_qty": 100},
        {"hour": 11, "status": "RUNNING", "target_qty": 60},
        {"hour": 12, "status": "RUNNING", "target_qty": 120},
        {"hour": 13, "status": "DONE",    "target_qty": 50},
        {"hour": 16, "status": "RUNNING", "target_qty": 150},
    ]
    for slot in scheduled_slots:
        daily_lot_counters[base_date] = daily_lot_counters.get(base_date, 0) + 1
        work_order_configs.append(
            {
                "lot_no": make_lot_no_for_date(base_date, daily_lot_counters[base_date]),
                "product_code": random.choice(product_codes),
                "target_qty": slot["target_qty"],
                "status": slot["status"],
                "days_ago": 0,
                "target_date": base_date,
                "fixed_hour": slot["hour"],
            }
        )

    work_orders = []
    work_order_id = 1

    for wo_config in work_order_configs:
        product = product_map[wo_config["product_code"]]
        scenario_name = PRODUCT_SCENARIO_MAP.get(wo_config["product_code"])
        scenario = scenario_map.get(scenario_name) if scenario_name else None

        fixed_hour = wo_config.get("fixed_hour")
        work_date = date_to_datetime(wo_config["target_date"], hour=fixed_hour if fixed_hour is not None else 8)
        if fixed_hour is None:
            work_date += timedelta(minutes=random.randint(0, 120))
        due_offset = random.randint(1, 7)
        due_date = work_date + timedelta(days=due_offset)

        start_time = None
        end_time = None
        completed_qty = 0
        current_process = None

        if wo_config["status"] not in ["READY"]:
            start_time = work_date
            if wo_config["status"] == "DONE":
                end_time = work_date + timedelta(hours=random.randint(4, 24))
                completed_qty = wo_config["target_qty"]
            elif wo_config["status"] == "RUNNING":
                completed_qty = int(wo_config["target_qty"] * random.uniform(0.3, 0.7))
                current_process = random.choice(["MILL", "TURN", "DRILL", "GRIND"])

        priority = random.randint(1, 10)

        wo = WorkOrder(
            id=work_order_id,
            lot_no=wo_config["lot_no"],
            product_id=product.id,
            scenario_id=scenario.id if scenario else None,
            target_qty=wo_config["target_qty"],
            qty=wo_config["target_qty"],
            priority=priority,
            due_date=due_date,
            completed_qty=completed_qty,
            current_process=current_process,
            start_time=start_time,
            end_time=end_time,
            remarks=f"Test order for {wo_config['product_code']}",
            status=wo_config["status"],
        )
        session.add(wo)
        await session.flush()
        work_orders.append((wo, wo_config, product))
        work_order_id += 1

    await session.commit()
    print(f"  {len(work_orders)}개 작업지시 생성 완료")

    status_counts = {}
    for _, cfg, _ in work_orders:
        status_counts[cfg["status"]] = status_counts.get(cfg["status"], 0) + 1
    print(f"  상태별 분포: {status_counts}")

    # ── 다운타임 윈도우 사전 생성 (seed_downtimes()와 동기화) ──────────────
    # seed_downtimes()가 오늘 생성할 다운타임 슬롯을 미리 계산하여
    # ProdResult가 모든 다운타임을 피할 수 있도록 한다.
    # 동일한 시드(42)를 사용해 seed_downtimes()와 같은 결과를 보장한다.
    def _pre_generate_today_downtime_windows(
        cnc_eqs: list,
        target_date: date,
    ) -> dict[int, list[tuple[datetime, datetime]]]:
        """seed_downtimes()가 오늘 생성할 다운타임 슬롯을 사전 계산한다.

        Returns:
            설비ID → [(start, end), ...] 매핑. ongoing(end=None)은 하루 끝(23:59)까지로 처리.
        """
        rng = random.Random(42)
        windows: dict[int, list[tuple[datetime, datetime]]] = {}

        # 고정 슬롯: 모든 CNC 설비에 공통
        fixed_slots = [
            {"hour": 9,  "minute": 30, "duration": 30},  # 공구교체
            {"hour": 14, "minute": 0,  "duration": 30},  # 예방보전
        ]

        ongoing_assigned = False

        for idx, eq in enumerate(cnc_eqs):
            eq_windows: list[tuple[datetime, datetime]] = []

            for slot in fixed_slots:
                s = date_to_datetime(target_date, hour=slot["hour"], minute=slot["minute"])
                e = s + timedelta(minutes=slot["duration"])
                eq_windows.append((s, e))

            # 비계획 정지 (50% 확률) — seed_downtimes()와 동일 RNG 순서
            if rng.random() < 0.5:
                unplanned_hour = rng.choice([10, 11, 15, 16])
                unplanned_minute = rng.randint(0, 45)
                unplanned_duration = rng.randint(15, 20)
                s = date_to_datetime(target_date, hour=unplanned_hour, minute=unplanned_minute)
                e = s + timedelta(minutes=unplanned_duration)
                eq_windows.append((s, e))

            # ongoing 다운타임: 첫 번째 설비의 14:00 슬롯 → 하루 끝까지 차단
            # 프론트엔드는 end_time=NULL → 23:59:59로 렌더링하므로 동일하게 맞춤
            if (not ongoing_assigned) and (idx == 0):
                ongoing_start = date_to_datetime(target_date, hour=14, minute=0)
                ongoing_end = date_to_datetime(target_date, hour=23, minute=59)
                eq_windows[1] = (ongoing_start, ongoing_end)
                ongoing_assigned = True

            windows[eq.id] = eq_windows

        return windows

    downtime_windows_by_eq = _pre_generate_today_downtime_windows(cnc_equipments, base_date)

    def _find_available_slot(
        preferred_start: datetime,
        duration: timedelta,
        target_date: date,
        equipment_slots: list[tuple[datetime, datetime]],
        eq_id: int | None = None,
    ) -> datetime:
        """정렬된 블록 리스트를 단일 순회하여 빈 슬롯을 찾는다.

        다운타임 윈도우 + 기존 설비 점유 슬롯을 합쳐서 정렬 후,
        충돌이 없는 첫 번째 위치를 반환한다.
        """
        # 모든 차단 구간을 합쳐서 시작 시간 기준 정렬
        all_blocked: list[tuple[datetime, datetime]] = list(equipment_slots)
        if eq_id is not None and eq_id in downtime_windows_by_eq:
            all_blocked.extend(downtime_windows_by_eq[eq_id])
        all_blocked.sort(key=lambda x: x[0])

        start = preferred_start
        for block_start, block_end in all_blocked:
            end = start + duration
            if end <= block_start:
                break  # 이후 블록과 충돌 불가
            if start < block_end:
                start = block_end + timedelta(minutes=random.randint(8, 15))

        return start

    # 생산 실적 생성
    print("생산 실적 데이터 생성 중...")
    result_count = 0
    result_id = 1
    equipment_occupied: dict[tuple, list[tuple[datetime, datetime]]] = {}
    # 설비별 마지막 RUNNING ProdResult 추적 (end_time=None 후보)
    # key: equipment_id, value: (ProdResult, process_duration)
    equipment_latest_running: dict[int, tuple] = {}

    # DONE/ERROR/PAUSE 먼저, RUNNING 마지막으로 처리
    # → RUNNING WO의 마지막 스텝이 설비 타임라인 끝에 위치하여 ONGOING 표시 가능
    _status_order = {"DONE": 0, "ERROR": 1, "PAUSE": 2, "RUNNING": 3, "READY": 4}
    sorted_wos = sorted(work_orders, key=lambda x: _status_order.get(x[1]["status"], 5))

    for wo, wo_config, product in sorted_wos:
        if wo_config["status"] == "READY":
            continue

        routings_result = await session.execute(
            select(ProcessRouting)
            .where(ProcessRouting.product_id == product.id)
            .order_by(ProcessRouting.sequence)
        )
        routings = routings_result.scalars().all()

        if wo_config["status"] == "DONE":
            progress_pct = 1.0
        elif wo_config["status"] == "RUNNING":
            progress_pct = random.uniform(0.3, 0.7)
        elif wo_config["status"] == "PAUSE":
            progress_pct = random.uniform(0.4, 0.6)
        elif wo_config["status"] == "ERROR":
            progress_pct = random.uniform(0.2, 0.5)
        else:
            progress_pct = 0

        completed_routings = int(len(routings) * progress_pct)
        if completed_routings == 0 and wo_config["status"] != "READY":
            completed_routings = 1

        base_time = date_to_datetime(wo_config["target_date"], hour=8)
        base_time += timedelta(minutes=random.randint(0, 120))

        for i, routing in enumerate(routings[:completed_routings]):
            equipment = cnc_equipments[(i + random.randint(0, 1)) % len(cnc_equipments)]
            process_duration = timedelta(minutes=random.randint(20, 60))
            pr_start_time = base_time + timedelta(hours=i * 1.5, minutes=random.randint(0, 30))

            # 다운타임 및 동일-설비 겹침 방지 (모든 날짜에 적용)
            target_d = wo_config["target_date"]
            day_cutoff = date_to_datetime(target_d, hour=22, minute=0)
            eq_key = (target_d, equipment.id)
            equipment_occupied.setdefault(eq_key, [])
            # 다운타임 윈도우는 오늘만 적용 (과거에는 다운타임 시드 없음)
            dt_eq_id = equipment.id if target_d == base_date else None
            candidate_start = _find_available_slot(
                pr_start_time, process_duration,
                target_d, equipment_occupied[eq_key],
                eq_id=dt_eq_id,
            )

            # 설비 폴백: 슬롯이 22시 이후로 밀리면 다른 설비 시도
            if candidate_start >= day_cutoff:
                best_start = candidate_start
                best_eq = equipment
                for alt_eq in cnc_equipments:
                    if alt_eq.id == equipment.id:
                        continue
                    alt_eq_key = (target_d, alt_eq.id)
                    equipment_occupied.setdefault(alt_eq_key, [])
                    alt_dt_eq_id = alt_eq.id if target_d == base_date else None
                    alt_start = _find_available_slot(
                        pr_start_time, process_duration,
                        target_d, equipment_occupied[alt_eq_key],
                        eq_id=alt_dt_eq_id,
                    )
                    if alt_start < best_start:
                        best_start = alt_start
                        best_eq = alt_eq
                equipment = best_eq
                eq_key = (target_d, equipment.id)
                candidate_start = best_start

            pr_start_time = candidate_start

            # 항상 추정 종료시간 설정 (NULL end_time은 후처리에서 설비당 1개만 부여)
            is_last_step = (i == completed_routings - 1)
            pr_end_time = pr_start_time + process_duration

            base_yield = 0.95 + (wo_config["days_ago"] % 7) * 0.005
            yield_rate = random.uniform(base_yield - 0.03, min(0.99, base_yield + 0.02))

            if wo_config["status"] == "DONE" or i < completed_routings - 1:
                ok_qty = int(wo_config["target_qty"] * yield_rate)
                ng_qty = wo_config["target_qty"] - ok_qty
            else:
                ok_qty = int(wo_config["target_qty"] * progress_pct * yield_rate)
                ng_qty = random.randint(0, max(1, int(ok_qty * 0.03)))

            result = ProdResult(
                id=result_id,
                work_order_id=wo.id,
                process_routing_id=routing.id,
                equipment_id=equipment.id,
                target_equipment_id=equipment.id,
                ok_qty=ok_qty,
                ng_qty=ng_qty,
                start_time=pr_start_time,
                end_time=pr_end_time,
            )
            session.add(result)
            result_count += 1
            result_id += 1

            # 점유 슬롯 등록 (모든 날짜, RUNNING도 추정 종료시간으로 등록)
            effective_end = pr_end_time or (pr_start_time + process_duration)
            date_eq_key = (wo_config["target_date"], equipment.id)
            equipment_occupied.setdefault(date_eq_key, []).append(
                (pr_start_time, effective_end)
            )

            # RUNNING WO의 마지막 스텝 → 설비별 가장 늦은 것만 NULL end_time 후보
            if is_last_step and wo_config["status"] == "RUNNING":
                prev = equipment_latest_running.get(equipment.id)
                if prev is None or pr_start_time > prev[0].start_time:
                    equipment_latest_running[equipment.id] = (result, process_duration)

    # 후처리: 설비당 1개의 RUNNING ProdResult만 end_time=NULL (진행 중 표시)
    # 조건: (1) 이후에 다른 작업이 없고, (2) 이후에 다운타임도 없어야
    for eq_id, (pr_obj, dur) in equipment_latest_running.items():
        estimated_end = pr_obj.start_time + dur
        # 이후 ProdResult 체크 (오늘 날짜 기준)
        today_eq_key = (base_date, eq_id)
        eq_slots = equipment_occupied.get(today_eq_key, [])
        has_later_pr = any(
            slot_start >= estimated_end
            for slot_start, _slot_end in eq_slots
            if slot_start != pr_obj.start_time
        )
        # 이후 다운타임 체크
        dt_windows = downtime_windows_by_eq.get(eq_id, [])
        has_later_dt = any(
            dt_start >= estimated_end
            for dt_start, _dt_end in dt_windows
        )
        if not has_later_pr and not has_later_dt:
            pr_obj.end_time = None

    await session.commit()
    print(f"  {result_count}개 생산 실적 생성 완료")
    return work_orders


# ============================================================
# 품질 데이터 시드
# ============================================================


async def seed_inspection_plans(
    session: AsyncSession,
    product_map: dict[str, Product],
) -> list[InspectionPlan]:
    """검사계획 생성 — 제품 3개 x 특성 4개 = 12개"""
    print("검사계획 생성 중...")
    plans = []

    inspection_types = ["IN_PROCESS", "FINAL", "IN_PROCESS", "FINAL"]

    for product in list(product_map.values())[:3]:
        for idx, char_data in enumerate(INSPECTION_CHARACTERISTICS):
            plan = InspectionPlan(
                product_id=product.id,
                characteristic=f"{product.name}_{char_data['name']}",
                nominal=char_data["nominal"],
                lsl=char_data["lsl"],
                usl=char_data["usl"],
                unit=char_data["unit"],
                inspection_type=inspection_types[idx],
                sampling_plan="PERIODIC",
                frequency=10,
                enable_spc=True,
                spc_control_type="X_BAR_R",
                is_active=True,
            )
            session.add(plan)
            plans.append(plan)

    await session.flush()
    print(f"  {len(plans)}개 검사계획 생성 완료")
    return plans


async def seed_measurement_devices(
    session: AsyncSession,
    base_date: date,
) -> list[MeasurementDevice]:
    """측정 장비 생성 — CMM, 표면조도, 높이게이지, 버니어캘리퍼스"""
    print("측정 장비 생성 중...")
    devices_data = [
        {
            "name": "Zeiss Contura G2",
            "source_type": "CMM",
            "serial_number": "CMM-ZC-20210347",
            "calibration_due": date_to_datetime(base_date.replace(month=6, day=30) if base_date.month <= 6 else base_date.replace(year=base_date.year + 1, month=6, day=30)),
            "connection_config": {"connection_type": "FILE", "path": "/data/cmm/zeiss/", "format": "dmo"},
        },
        {
            "name": "Mitutoyo SJ-410",
            "source_type": "MANUAL",
            "serial_number": "SJ-410-A193042",
            "calibration_due": date_to_datetime(base_date.replace(month=12, day=31) if base_date.month <= 12 else date_to_datetime(base_date.replace(year=base_date.year + 1, month=12, day=31))),
            "connection_config": {"connection_type": "MANUAL", "format": "csv"},
        },
        {
            "name": "Mitutoyo QM-Height 600",
            "source_type": "MANUAL",
            "serial_number": "QMH-600-B042711",
            "calibration_due": date_to_datetime(base_date.replace(month=9, day=30) if base_date.month <= 9 else date_to_datetime(base_date.replace(year=base_date.year + 1, month=9, day=30))),
            "connection_config": {"connection_type": "MANUAL", "format": "manual"},
        },
        {
            "name": "Mitutoyo CD-15CX Digital Caliper",
            "source_type": "MANUAL",
            "serial_number": "CDP-15-C083901",
            "calibration_due": date_to_datetime(base_date.replace(month=3, day=31) if base_date.month <= 3 else date_to_datetime(base_date.replace(year=base_date.year + 1, month=3, day=31))),
            "connection_config": {"connection_type": "MANUAL", "format": "manual"},
        },
    ]

    devices = []
    for data in devices_data:
        dev = MeasurementDevice(
            name=data["name"],
            source_type=data["source_type"],
            serial_number=data["serial_number"],
            calibration_due=data["calibration_due"],
            connection_config=data["connection_config"],
            is_active=True,
        )
        session.add(dev)
        devices.append(dev)

    await session.flush()
    print(f"  {len(devices)}개 측정 장비 생성 완료")
    return devices


async def seed_inspection_results(
    session: AsyncSession,
    plans: list[InspectionPlan],
    work_orders: list[tuple],
    eq_map: dict[str, Equipment],
    base_date: date,
    devices: list[MeasurementDevice] | None = None,
) -> list[InspectionResult]:
    """측정결과 생성 — 완료된 WO의 검사계획별 20~30개 측정값, 시계열 순 정렬"""
    print("측정결과 생성 중...")
    results = []

    done_wos = [(wo, cfg, prod) for wo, cfg, prod in work_orders if cfg["status"] == "DONE"]
    if not done_wos:
        print("  완료된 작업지시 없음, 측정결과 생성 건너뜀")
        return results

    equipments = list(eq_map.values())

    # 계획 인덱스 1, 3 에 드리프트 패턴 적용 (공구 마모 시뮬레이션)
    drift_plan_indices = {1, 3}

    # 장비 타입별 측정 소스 매핑
    device_by_type: dict[str, MeasurementDevice | None] = {
        "CMM": None,
        "MANUAL": None,
    }
    if devices:
        for dev in devices:
            if dev.source_type == "CMM" and device_by_type["CMM"] is None:
                device_by_type["CMM"] = dev
            elif dev.source_type == "MANUAL" and device_by_type["MANUAL"] is None:
                device_by_type["MANUAL"] = dev

    result_id = 1
    for plan_idx, plan in enumerate(plans):
        num_results = random.randint(20, 30)
        nominal = float(plan.nominal)
        usl = float(plan.usl)
        lsl = float(plan.lsl)
        tolerance = (usl - lsl) / 2
        sigma = tolerance / 3

        is_drift_plan = plan_idx in drift_plan_indices
        drift_range = usl - nominal  # 드리프트 최대 편차: nominal → USL 방향

        # 시계열 순 날짜 생성: 30일 전 → 오늘 방향으로 정렬
        days_offsets = sorted((random.randint(0, 30) for _ in range(num_results)), reverse=True)

        # 장비 소스 결정 (CMM 계획은 CMM 장비로)
        use_cmm = plan_idx == 0
        meas_source = "CMM" if use_cmm else "OMM"
        meas_device = device_by_type["CMM"] if use_cmm else device_by_type["MANUAL"]

        # Filter done_wos to match this plan's product
        plan_product_wos = [(wo, cfg, prod) for wo, cfg, prod in done_wos if prod.id == plan.product_id]
        if not plan_product_wos:
            plan_product_wos = done_wos  # fallback if no match

        for i, days_back in enumerate(days_offsets):
            wo, cfg, prod = random.choice(plan_product_wos)
            eq = random.choice(equipments) if equipments else None

            # 드리프트 패턴: 시간이 지날수록 USL 방향으로 평균이 이동
            if is_drift_plan:
                progress = i / max(num_results - 1, 1)  # 0.0 → 1.0
                drift_offset = drift_range * 0.7 * progress  # 최대 공차의 70%까지 드리프트
                center = nominal + drift_offset
            else:
                center = nominal

            measured_value = random.gauss(center, sigma)
            deviation = measured_value - nominal
            is_conforming = lsl <= measured_value <= usl

            measured_at = date_to_datetime(
                base_date - timedelta(days=days_back),
                hour=random.randint(8, 17),
                minute=random.randint(0, 59),
            )
            inspector = random.choice(["김철수", "이영희", "박민수", "정수진"])

            result_obj = InspectionResult(
                id=result_id,  # SQLite BigInteger 위해 명시적 ID
                inspection_plan_id=plan.id,
                work_order_id=wo.id,
                equipment_id=eq.id if eq else None,
                device_id=meas_device.id if meas_device else None,
                lot_no=wo.lot_no,
                serial_no=f"SN-{random.randint(10000, 99999)}",
                measured_value=round(measured_value, 4),
                deviation=round(deviation, 4),
                is_conforming=is_conforming,
                measured_at=measured_at,
                source=meas_source,
                measurement_metadata={"inspector": inspector, "method": meas_source, "conditions": "standard"},
            )
            session.add(result_obj)
            results.append(result_obj)
            result_id += 1

    await session.flush()
    conforming = sum(1 for r in results if r.is_conforming)
    print(
        f"  {len(results)}개 측정결과 생성 완료 "
        f"(적합: {conforming}, 부적합: {len(results) - conforming})"
    )
    return results


async def seed_spc_data(
    session: AsyncSession,
    plans: list[InspectionPlan],
    work_orders: list[tuple],
    base_date: date,
) -> tuple[list[SPCChart], list[SPCDataPoint]]:
    """SPC 차트 및 데이터포인트 생성 — 4가지 패턴 (정상/경고/트렌드/이탈)"""
    print("SPC 차트 생성 중...")
    charts = []
    data_points = []

    done_wos = [(wo, cfg, prod) for wo, cfg, prod in work_orders if cfg["status"] == "DONE"]

    # 계획 인덱스별 패턴: 0=정상, 1=경고, 2=트렌드(Rule3), 3+=이탈(Rule1)
    PATTERN_NORMAL = "normal"
    PATTERN_WARNING = "warning"
    PATTERN_TREND = "trend"
    PATTERN_OOC = "out_of_control"

    def get_pattern(plan_idx: int) -> str:
        patterns = [PATTERN_NORMAL, PATTERN_WARNING, PATTERN_TREND, PATTERN_OOC]
        return patterns[plan_idx % len(patterns)]

    global_dp_id = 1

    for plan_idx, plan in enumerate(plans):
        nominal = float(plan.nominal)
        usl = float(plan.usl)
        lsl = float(plan.lsl)
        sigma = (usl - lsl) / 6

        # X-bar R 관리한계 (A2=0.577, n=5, d2=2.326)
        a2 = 0.577
        r_bar = sigma * 2.326
        ucl = nominal + a2 * r_bar
        lcl = nominal - a2 * r_bar
        uwl = nominal + (ucl - nominal) * 2 / 3  # 2σ 경고선
        lwl = nominal - (nominal - lcl) * 2 / 3

        chart = SPCChart(
            inspection_plan_id=plan.id,
            chart_type="X_BAR_R",
            center_line=nominal,
            upper_control_limit=round(ucl, 4),
            lower_control_limit=round(lcl, 4),
            upper_warning_limit=round(uwl, 4),
            lower_warning_limit=round(lwl, 4),
            range_center_line=round(r_bar, 4),
            range_upper_control_limit=round(r_bar * 2.114, 4),
            range_lower_control_limit=0.0,
            sample_count=25,
            is_active=True,
        )
        session.add(chart)
        await session.flush()
        charts.append(chart)

        pattern = get_pattern(plan_idx)

        # 트렌드 패턴: 서브그룹 19~25 가 꾸준히 증가
        trend_start_sg = 19
        trend_slope = (ucl - nominal) / (25 - trend_start_sg + 1)

        # 경고 패턴: 2~3개 포인트를 경고 구간(2σ~3σ)에 배치
        warning_sgs = {6, 14, 21}

        # 이탈 패턴: 서브그룹 8, 19 는 UCL 초과
        ooc_sgs = {8, 19}

        plan_product_wos = [(wo, cfg, prod) for wo, cfg, prod in done_wos if prod.id == plan.product_id]
        if not plan_product_wos:
            plan_product_wos = done_wos  # fallback

        dp_id = global_dp_id
        for sg in range(1, 26):
            values = [random.gauss(nominal, sigma) for _ in range(5)]
            x_bar = sum(values) / len(values)
            r_value = max(values) - min(values)

            is_out = False
            violation_rules: list[str] = []

            if pattern == PATTERN_NORMAL:
                # 완전 정상 — 모두 관리 내
                pass

            elif pattern == PATTERN_WARNING:
                if sg in warning_sgs:
                    # 2σ~3σ 구간 (경고 구간)에 x_bar 배치
                    x_bar = nominal + (ucl - nominal) * random.uniform(0.67, 0.95)

            elif pattern == PATTERN_TREND:
                if sg >= trend_start_sg:
                    # 선형 증가 트렌드
                    step = sg - trend_start_sg + 1
                    x_bar = nominal + trend_slope * step * random.uniform(0.85, 1.10)
                    if sg >= 22:
                        # 후반 포인트 중 일부는 UCL 근접/초과
                        if x_bar > ucl:
                            is_out = True
                            violation_rules = ["RULE_3_TREND_7"]

            elif pattern == PATTERN_OOC:
                if sg in ooc_sgs:
                    x_bar = ucl + sigma * random.uniform(0.4, 0.8)
                    is_out = True
                    violation_rules = ["RULE_1_BEYOND_3SIGMA"]

            # 재계산 (x_bar를 패턴으로 덮어쓴 경우 range는 원본 유지)
            std_dev = (sum((v - sum(values) / len(values)) ** 2 for v in values) / (len(values) - 1)) ** 0.5

            recorded_at = date_to_datetime(
                base_date - timedelta(days=25 - sg),
                hour=random.randint(8, 16),
            )

            wo_for_dp = random.choice(plan_product_wos)[0] if plan_product_wos else None

            dp = SPCDataPoint(
                id=dp_id,
                spc_chart_id=chart.id,
                subgroup_number=sg,
                mean_value=round(x_bar, 4),
                range_value=round(r_value, 4),
                standard_deviation=round(std_dev, 4),
                sample_size=5,
                raw_values=[round(v, 4) for v in values],
                is_out_of_control=is_out,
                violation_rules=violation_rules if violation_rules else None,
                work_order_id=wo_for_dp.id if wo_for_dp else None,
                lot_number=wo_for_dp.lot_no if wo_for_dp else None,
                created_at=recorded_at,
            )
            session.add(dp)
            data_points.append(dp)
            dp_id += 1

        global_dp_id = dp_id

    await session.flush()
    print(f"  {len(charts)}개 SPC 차트, {len(data_points)}개 데이터포인트 생성 완료")
    return charts, data_points


async def seed_ncr(
    session: AsyncSession,
    work_orders: list[tuple],
    inspection_results: list[InspectionResult],
    plans: list[InspectionPlan],
    eq_map: dict[str, Equipment],
    base_date: date,
) -> list[NonConformance]:
    """NCR 부적합 보고서 생성 — 12건, 현실적 상태 분포 및 상세 근본원인"""
    print("NCR 생성 중...")
    ncr_list = []

    done_wos = [(wo, cfg, prod) for wo, cfg, prod in work_orders if cfg["status"] == "DONE"]
    if not done_wos:
        print("  완료된 작업지시 없음, NCR 생성 건너뜀")
        return ncr_list

    equipments = [eq for eq in eq_map.values() if eq.equipment_type == "CNC"]

    # 12개 NCR 템플릿 — 결함 유형 및 실측값 오프셋 포함
    ncr_templates = [
        {
            "defect_type": "DIMENSION",
            "characteristic": "외경",
            "description": "외경 규격 초과 — CNC 가공 후 직경 측정값이 USL을 초과함",
            "disposition": "REWORK",
            "defect_qty": 3,
            "value_offset": 0.08,
        },
        {
            "defect_type": "SURFACE",
            "characteristic": "표면조도",
            "description": "표면 스크래치 발생 — 척 교환 중 공작물 접촉에 의한 표면 손상",
            "disposition": "SCRAP",
            "defect_qty": 1,
            "value_offset": 1.2,
        },
        {
            "defect_type": "DIMENSION",
            "characteristic": "내경",
            "description": "진원도 불량 — 보링 바 진동으로 내경 원형도 벗어남",
            "disposition": "REWORK",
            "defect_qty": 2,
            "value_offset": -0.06,
        },
        {
            "defect_type": "DIMENSION",
            "characteristic": "홀 위치도",
            "description": "홀 가공 위치 편차 — 공작물 고정 지그 마모로 위치 오차 발생",
            "disposition": "REWORK",
            "defect_qty": 4,
            "value_offset": 0.12,
        },
        {
            "defect_type": "MATERIAL",
            "characteristic": "경도",
            "description": "경도 미달 — 입고 소재 열처리 불량으로 규격 이하 경도 확인",
            "disposition": "RETURN",
            "defect_qty": 10,
            "value_offset": -5.0,
        },
        {
            "defect_type": "DIMENSION",
            "characteristic": "외경",
            "description": "끼워맞춤 불량 — 외경 공차 누적으로 조립 시 간섭 발생",
            "disposition": "REWORK",
            "defect_qty": 2,
            "value_offset": 0.05,
        },
        {
            "defect_type": "SURFACE",
            "characteristic": "표면조도",
            "description": "가공 흔적 잔류 — 공구 마모 말기에 피드 마크 과다 발생",
            "disposition": "REWORK",
            "defect_qty": 3,
            "value_offset": 0.8,
        },
        {
            "defect_type": "DIMENSION",
            "characteristic": "단차",
            "description": "단차 치수 불량 — 공정 간 기준면 재설정 오류로 단차 오차 발생",
            "disposition": "REWORK",
            "defect_qty": 2,
            "value_offset": -0.09,
        },
        {
            "defect_type": "DIMENSION",
            "characteristic": "나사 유효경",
            "description": "나사 유효경 불량 — 탭 마모로 나사산 유효경이 LSL 미달",
            "disposition": "SCRAP",
            "defect_qty": 5,
            "value_offset": -0.07,
        },
        {
            "defect_type": "SURFACE",
            "characteristic": "평면도",
            "description": "평면도 불량 — 가공 중 공작물 열팽창으로 기준면 변형",
            "disposition": "REWORK",
            "defect_qty": 1,
            "value_offset": 0.04,
        },
        {
            "defect_type": "DIMENSION",
            "characteristic": "홈 폭",
            "description": "홈 폭 과소 — 엔드밀 측면 마모로 홈 폭이 LSL 미달",
            "disposition": "REWORK",
            "defect_qty": 3,
            "value_offset": -0.11,
        },
        {
            "defect_type": "MATERIAL",
            "characteristic": "재질 성분",
            "description": "재질 부적합 — 납품 소재 성분 성적서와 실측치 불일치 확인",
            "disposition": "RETURN",
            "defect_qty": 20,
            "value_offset": -2.5,
        },
    ]

    # 상태 분포: OPEN 3, IN_PROGRESS 3, CLOSED 4, CANCELLED 2
    statuses = [
        "OPEN", "OPEN", "OPEN",
        "IN_PROGRESS", "IN_PROGRESS", "IN_PROGRESS",
        "CLOSED", "CLOSED", "CLOSED", "CLOSED",
        "CANCELLED", "CANCELLED",
    ]

    # CLOSED NCR별 근본원인 / 시정조치 (각각 다르게)
    closed_details = [
        {
            "root_cause": "공구 수명 관리 기준 미준수 — 가공 사이클 수 초과 후에도 공구 미교체",
            "corrective_action": "공구 교체 주기 단축 (500 → 400 사이클), IoT 센서 기반 자동 알람 설정",
        },
        {
            "root_cause": "척 조우 마모로 클램핑 압력 불균일 — 정기 점검 일정 누락",
            "corrective_action": "척 조우 교체 및 PM 점검 체크리스트에 클램핑 압력 측정 항목 추가",
        },
        {
            "root_cause": "가공 프로그램 오프셋 미보정 — 스핀들 열팽창 보정값 적용 누락",
            "corrective_action": "열팽창 보정 루틴 NC 프로그램에 통합, 가공 전 자동 보정 절차 표준화",
        },
        {
            "root_cause": "입고 소재 수입검사 샘플링 불충분 — 배치 대표 샘플 미채취",
            "corrective_action": "수입검사 절차 개정 (샘플 수 N→2N), 공급업체 성적서 이중 확인 의무화",
        },
    ]

    # 부적합 측정결과 필터 (NCR 연결용)
    nc_results = [r for r in inspection_results if not r.is_conforming]

    ncr_id = 1
    closed_detail_idx = 0
    used_result_ids: set[int] = set()

    for i, template in enumerate(ncr_templates):
        eq = random.choice(equipments) if equipments else None
        days_back = random.randint(1, 28)
        ncr_date = base_date - timedelta(days=days_back)

        # 연결할 측정결과/검사계획 — 비적합 결과 우선 연결
        linked_plan = plans[i % len(plans)] if plans else None

        # Find an unused non-conforming result, preferring one matching the plan's product
        available_nc = [r for r in nc_results if r.id not in used_result_ids]
        if not available_nc:
            available_nc = nc_results  # allow reuse if exhausted
        linked_result = available_nc[i % len(available_nc)] if available_nc else None
        if linked_result:
            used_result_ids.add(linked_result.id)

        # Match WO to the linked inspection plan's product
        if linked_plan:
            plan_product_wos = [(wo, cfg, prod) for wo, cfg, prod in done_wos if prod.id == linked_plan.product_id]
            if not plan_product_wos:
                plan_product_wos = done_wos
        else:
            plan_product_wos = done_wos
        wo, _, prod = random.choice(plan_product_wos)

        # 검사계획의 nominal 기반으로 실측값 계산
        nominal = float(linked_plan.nominal) if linked_plan and linked_plan.nominal else 50.0
        specified_value = nominal
        actual_value = round(nominal + template["value_offset"], 4)

        status = statuses[i]
        closed_at = None
        root_cause = None
        corrective_action = None

        if status == "CLOSED":
            detail = closed_details[closed_detail_idx % len(closed_details)]
            closed_detail_idx += 1
            close_days = random.randint(3, 10)
            closed_at = date_to_datetime(
                ncr_date + timedelta(days=close_days),
                hour=random.randint(9, 17),
            )
            root_cause = detail["root_cause"]
            corrective_action = detail["corrective_action"]

        ncr = NonConformance(
            id=ncr_id,  # SQLite BigInteger 위해 명시적 ID
            ncr_no=make_ncr_no(ncr_date, i + 1),
            work_order_id=wo.id,
            lot_no=wo.lot_no,
            serial_no=f"SN-{random.randint(10000, 99999)}",
            machine_id=eq.id if eq else None,
            inspection_result_id=linked_result.id if linked_result else None,
            inspection_plan_id=linked_plan.id if linked_plan else None,
            defect_type=template["defect_type"],
            characteristic=template["characteristic"],
            specified_value=specified_value,
            actual_value=actual_value,
            disposition=template["disposition"],
            trigger_data={"defect_qty": template["defect_qty"]},
            status=status,
            description=template["description"],
            root_cause=root_cause,
            corrective_action=corrective_action,
            reported_by="품질관리팀",
            assigned_to="가공팀" if status not in ("CANCELLED",) else None,
            reported_at=date_to_datetime(ncr_date, hour=random.randint(9, 16)),
            due_date=date_to_datetime(ncr_date + timedelta(days=14)),
            closed_at=closed_at,
        )
        session.add(ncr)
        ncr_list.append(ncr)
        ncr_id += 1

    await session.flush()
    status_dist: dict[str, int] = {}
    for n in ncr_list:
        status_dist[n.status] = status_dist.get(n.status, 0) + 1
    print(f"  {len(ncr_list)}개 NCR 생성 완료 (상태: {status_dist})")
    return ncr_list


# ============================================================
# 다운타임 이벤트 시드
# ============================================================


async def seed_downtimes(
    session: AsyncSession,
    eq_map: dict[str, Equipment],
    reason_map: dict[str, DowntimeReason],
    work_orders: list[tuple],
    base_date: date,
    days: int = 30,
) -> list[Downtime]:
    """다운타임 이벤트 생성 — 최근 N일간 설비별 이벤트 + 오늘 단기 블록"""
    print(f"다운타임 이벤트 생성 중 (최근 {days}일)...")
    downtimes = []

    cnc_equipments = [eq for name, eq in eq_map.items() if "CNC" in name]
    reason_codes = list(reason_map.keys())

    # 카테고리별 사유 코드 그룹
    planned_codes = [c for c in reason_codes if reason_map[c].category == "PLANNED"]
    setup_codes = [c for c in reason_codes if reason_map[c].category == "SETUP"]
    unplanned_codes = [c for c in reason_codes if reason_map[c].category == "UNPLANNED"]

    # RUNNING 또는 DONE인 WO 목록
    active_wos = [wo for wo, cfg, _ in work_orders if cfg["status"] in ["DONE", "RUNNING"]]

    # ── 1. 과거 이력 다운타임 (1일 이전 ~ days일 전) ──────────────────────────
    # (equipment_id, date) → [(start, end), ...] — 이미 배치된 다운타임 추적
    past_dt_slots: dict[tuple[int, date], list[tuple[datetime, datetime]]] = {}

    for equipment in cnc_equipments:
        # 설비당 5~8개 다운타임 이벤트
        num_events = random.randint(5, 8)
        for _ in range(num_events):
            days_back = random.randint(1, days)  # 오늘(0)은 아래에서 별도 처리
            event_date = base_date - timedelta(days=days_back)

            # 카테고리 선택: PLANNED 40%, SETUP 30%, UNPLANNED 30%
            category_choice = random.choices(
                ["PLANNED", "SETUP", "UNPLANNED"], weights=[40, 30, 30]
            )[0]

            if category_choice == "PLANNED" and planned_codes:
                code = random.choice(planned_codes)
            elif category_choice == "SETUP" and setup_codes:
                code = random.choice(setup_codes)
            else:
                code = (
                    random.choice(unplanned_codes)
                    if unplanned_codes
                    else random.choice(reason_codes)
                )

            reason = reason_map[code]

            # 기간: PLANNED 30~90분, SETUP 15~60분, UNPLANNED 10~90분
            if category_choice == "PLANNED":
                duration = random.randint(30, 90)
            elif category_choice == "SETUP":
                duration = random.randint(15, 60)
            else:
                duration = random.randint(10, 90)

            # ProdResult 겹침 방지: 해당 설비/날짜의 기존 ProdResult 조회 후 빈 시간 배치
            day_start = date_to_datetime(event_date, hour=0)
            day_end = date_to_datetime(event_date, hour=23, minute=59)
            existing_pr = await session.execute(
                select(ProdResult.start_time, ProdResult.end_time)
                .where(
                    and_(
                        ProdResult.equipment_id == equipment.id,
                        ProdResult.start_time >= day_start,
                        ProdResult.start_time <= day_end,
                        ProdResult.end_time.isnot(None),
                    )
                )
            )
            occupied_slots = [
                (
                    r.start_time.replace(tzinfo=timezone.utc) if r.start_time.tzinfo is None else r.start_time,
                    r.end_time.replace(tzinfo=timezone.utc) if r.end_time.tzinfo is None else r.end_time,
                )
                for r in existing_pr.all()
            ]

            start_hour = random.randint(6, 20)
            start_time = date_to_datetime(event_date, hour=start_hour, minute=random.randint(0, 59))
            end_time = start_time + timedelta(minutes=duration)

            # 최대 20회 재시도로 ProdResult 및 기존 다운타임과 겹치지 않는 시간 찾기
            placed_dt_key = (equipment.id, event_date)
            placed_dt_slots = past_dt_slots.get(placed_dt_key, [])
            all_blocked = occupied_slots + placed_dt_slots
            for _retry in range(20):
                overlap_found = False
                for blk_start, blk_end in all_blocked:
                    if start_time < blk_end and end_time > blk_start:
                        overlap_found = True
                        break
                if not overlap_found:
                    break
                start_hour = random.randint(6, 20)
                start_time = date_to_datetime(event_date, hour=start_hour, minute=random.randint(0, 59))
                end_time = start_time + timedelta(minutes=duration)
            else:
                # 재시도 후에도 겹치면 이 다운타임 건너뜀
                overlap_found = any(
                    start_time < blk_end and end_time > blk_start
                    for blk_start, blk_end in all_blocked
                )
                if overlap_found:
                    continue

            wo_for_dt = random.choice(active_wos) if active_wos else None

            # 성공적으로 배치된 슬롯 추적 (같은 날 DT-DT 겹침 방지)
            past_dt_slots.setdefault(placed_dt_key, []).append((start_time, end_time))

            dt = Downtime(
                equipment_id=equipment.id,
                reason_id=reason.id,
                work_order_id=wo_for_dt.id if wo_for_dt else None,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration,
                remarks=f"{reason.name} - {equipment.eq_name}",
                reported_by="operator",
            )
            session.add(dt)
            downtimes.append(dt)

    # ── 2. 오늘(base_date) 단기 다운타임 — 스케줄러 테스트용 ─────────────────
    # 오전 공구 교체: 09:30~10:00 (30분)
    # 오후 예방 보전: 14:00~14:30 (30분)
    # 선택적 비계획 정지: 랜덤 15~20분
    today_slots = [
        {"hour": 9,  "minute": 30, "duration": 30, "category": "SETUP",    "code": "DT-TOOL"},
        {"hour": 14, "minute": 0,  "duration": 30, "category": "PLANNED",  "code": "DT-PM"},
    ]

    ongoing_assigned = False  # 진행중 이벤트는 설비 1개에만 할당
    # _pre_generate_today_downtime_windows()와 동일한 시드를 사용하여
    # ProdResult 생성 시 예측한 다운타임 슬롯과 일치시킨다.
    dt_rng = random.Random(42)

    for idx, equipment in enumerate(cnc_equipments):
        slots_for_eq = list(today_slots)  # 모든 설비에 오전/오후 슬롯 부여

        # 선택적 비계획 정지 (설비당 50% 확률) — dt_rng 사용으로 시간이 동기화됨
        if dt_rng.random() < 0.5:
            unplanned_hour = dt_rng.choice([10, 11, 15, 16])
            unplanned_minute = dt_rng.randint(0, 45)
            unplanned_duration = dt_rng.randint(15, 20)
            slots_for_eq.append({
                "hour": unplanned_hour,
                "minute": unplanned_minute,
                "duration": unplanned_duration,
                "category": "UNPLANNED",
                "code": random.choice(unplanned_codes) if unplanned_codes else "DT-OTHER",
            })

        # 오늘 해당 설비의 ProdResult 점유 슬롯 조회 (비계획 다운타임 겹침 방지)
        today_start = date_to_datetime(base_date, hour=0)
        today_end = date_to_datetime(base_date, hour=23, minute=59)
        today_pr = await session.execute(
            select(ProdResult.start_time, ProdResult.end_time)
            .where(
                and_(
                    ProdResult.equipment_id == equipment.id,
                    ProdResult.start_time >= today_start,
                    ProdResult.start_time <= today_end,
                    ProdResult.end_time.isnot(None),
                )
            )
        )
        today_occupied = [
            (
                r.start_time.replace(tzinfo=timezone.utc) if r.start_time.tzinfo is None else r.start_time,
                r.end_time.replace(tzinfo=timezone.utc) if r.end_time.tzinfo is None else r.end_time,
            )
            for r in today_pr.all()
        ]

        for slot in slots_for_eq:
            code = slot["code"]
            # code가 reason_map에 없으면 같은 카테고리에서 대체
            if code not in reason_map:
                cat = slot["category"]
                fallback_pool = (
                    planned_codes if cat == "PLANNED"
                    else setup_codes if cat == "SETUP"
                    else unplanned_codes
                )
                code = random.choice(fallback_pool) if fallback_pool else random.choice(reason_codes)

            reason = reason_map[code]
            start_time = date_to_datetime(base_date, hour=slot["hour"], minute=slot["minute"])
            duration = slot["duration"]
            end_time = start_time + timedelta(minutes=duration)

            # ProdResult와 겹치면 시간 조정 (모든 슬롯 타입에 적용)
            candidate_hours = [10, 11, 12, 13, 15, 16, 17, 18]
            for _retry in range(len(candidate_hours) * 2):
                overlap_found = False
                if end_time is not None:
                    for pr_start, pr_end in today_occupied:
                        if start_time < pr_end and end_time > pr_start:
                            overlap_found = True
                            break
                if not overlap_found:
                    break
                # 다른 시간으로 재시도
                new_hour = candidate_hours[_retry % len(candidate_hours)]
                start_time = date_to_datetime(base_date, hour=new_hour, minute=random.randint(0, 45))
                end_time = start_time + timedelta(minutes=duration)

            # 첫 번째 설비의 오후 슬롯을 진행중 이벤트로 전환 (end_time=None)
            is_ongoing = (not ongoing_assigned) and (slot["hour"] == 14) and (idx == 0)
            if is_ongoing:
                end_time = None
                duration = None
                ongoing_assigned = True

            wo_for_dt = random.choice(active_wos) if active_wos else None

            dt = Downtime(
                equipment_id=equipment.id,
                reason_id=reason.id,
                work_order_id=wo_for_dt.id if wo_for_dt else None,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration,
                remarks=f"{reason.name} - {equipment.eq_name}",
                reported_by="operator",
            )
            session.add(dt)
            downtimes.append(dt)

    await session.flush()
    print(f"  {len(downtimes)}개 다운타임 이벤트 생성 완료")
    return downtimes


# ============================================================
# 알람 이벤트 시드
# ============================================================


async def seed_alarms(
    session: AsyncSession,
    eq_map: dict[str, Equipment],
    alarm_def_map: dict[str, AlarmDefinition],
    work_orders: list[tuple],
    base_date: date,
    days: int = 30,
) -> list[Alarm]:
    """알람 이벤트 생성 — 최근 N일간 15~25건"""
    print(f"알람 이벤트 생성 중 (최근 {days}일)...")
    alarms = []

    cnc_equipments = [eq for name, eq in eq_map.items() if "CNC" in name]
    alarm_codes = list(alarm_def_map.keys())

    active_wos = [wo for wo, cfg, _ in work_orders if cfg["status"] in ["DONE", "RUNNING"]]

    num_alarms = random.randint(15, 25)
    for i in range(num_alarms):
        days_back = random.randint(0, days)
        event_date = base_date - timedelta(days=days_back)

        alarm_code = random.choice(alarm_codes)
        alarm_def = alarm_def_map[alarm_code]
        equipment = random.choice(cnc_equipments)

        occurred_at = date_to_datetime(
            event_date, hour=random.randint(6, 22), minute=random.randint(0, 59)
        )

        # 상태 분포: RESOLVED 70%, ACKNOWLEDGED 15%, ACTIVE 15%
        status = random.choices(["RESOLVED", "ACKNOWLEDGED", "ACTIVE"], weights=[70, 15, 15])[0]

        acknowledged_at = None
        resolved_at = None
        acknowledged_by = None
        resolved_by = None
        resolution_note = None

        if status in ["ACKNOWLEDGED", "RESOLVED"]:
            acknowledged_at = occurred_at + timedelta(minutes=random.randint(1, 30))
            acknowledged_by = "operator"

        if status == "RESOLVED":
            resolved_at = acknowledged_at + timedelta(minutes=random.randint(5, 120))
            resolved_by = "operator"
            resolution_note = f"{alarm_def.name} 조치 완료"

        # 알람값 생성
        if "TEMP" in alarm_code:
            value = f"{random.uniform(65, 85):.1f}°C"
        elif "LOAD" in alarm_code:
            value = f"{random.uniform(80, 95):.1f}%"
        elif "COOLANT" in alarm_code:
            value = f"{random.uniform(5, 20):.1f}%"
        else:
            value = None

        message = f"{equipment.eq_name} - {alarm_def.description}"
        wo_for_alarm = random.choice(active_wos) if active_wos else None

        alarm = Alarm(
            definition_id=alarm_def.id,
            equipment_id=equipment.id,
            work_order_id=wo_for_alarm.id if wo_for_alarm else None,
            status=status,
            occurred_at=occurred_at,
            acknowledged_at=acknowledged_at,
            resolved_at=resolved_at,
            message=message,
            value=value,
            acknowledged_by=acknowledged_by,
            resolved_by=resolved_by,
            resolution_note=resolution_note,
        )
        session.add(alarm)
        alarms.append(alarm)

    await session.flush()
    status_dist = {}
    for a in alarms:
        status_dist[a.status] = status_dist.get(a.status, 0) + 1
    print(f"  {len(alarms)}개 알람 이벤트 생성 완료 (상태: {status_dist})")
    return alarms


# ============================================================
# 설비 상태 이력 시드
# ============================================================


async def seed_equipment_status_history(
    session: AsyncSession,
    eq_map: dict[str, Equipment],
    work_orders: list[tuple],
    base_date: date,
    days: int = 30,
) -> list[EquipmentStatusHistory]:
    """설비 상태 변경 이력 생성 — OEE 분석 가능한 데이터"""
    print(f"설비 상태 이력 생성 중 (최근 {days}일)...")
    histories = []

    cnc_equipments = [eq for name, eq in eq_map.items() if "CNC" in name]
    statuses = ["RUN", "IDLE", "STOP", "SETUP", "MAINTENANCE"]
    status_weights = [40, 20, 15, 15, 10]

    active_wos = [wo for wo, cfg, _ in work_orders if cfg["status"] in ["DONE", "RUNNING"]]

    for equipment in cnc_equipments:
        # 설비당 하루 6~12번 상태 변경 → 30일간
        prev_status = None

        for days_back in range(days, -1, -1):
            event_date = base_date - timedelta(days=days_back)
            transitions_per_day = random.randint(6, 12)

            for t in range(transitions_per_day):
                new_status = random.choices(statuses, weights=status_weights)[0]
                while new_status == prev_status:
                    new_status = random.choices(statuses, weights=status_weights)[0]

                hour = 6 + int(t * (16 / transitions_per_day))
                minute = random.randint(0, 59)
                changed_at = date_to_datetime(event_date, hour=min(hour, 22), minute=minute)

                prev_duration = random.randint(10, 120) if prev_status else None

                reasons = {
                    "RUN": "가공 시작",
                    "IDLE": "대기 중",
                    "STOP": "정지",
                    "SETUP": "셋업 진행",
                    "MAINTENANCE": "보전 작업",
                }

                wo_for_hist = (
                    random.choice(active_wos) if active_wos and new_status == "RUN" else None
                )

                history = EquipmentStatusHistory(
                    equipment_id=equipment.id,
                    previous_status=prev_status,
                    new_status=new_status,
                    changed_at=changed_at,
                    previous_duration_minutes=prev_duration,
                    reason=reasons.get(new_status, "상태 변경"),
                    work_order_id=wo_for_hist.id if wo_for_hist else None,
                    changed_by="system",
                )
                session.add(history)
                histories.append(history)
                prev_status = new_status

    await session.flush()
    print(f"  {len(histories)}개 설비 상태 이력 생성 완료")
    return histories


# ============================================================
# 검증
# ============================================================


async def validate_seed_data(session: AsyncSession) -> dict[str, list[str]]:
    """시드 데이터 연결 무결성 검증"""
    issues = {"errors": [], "warnings": []}

    # 1. 라우팅 없는 제품 확인
    products_without_routing = await session.execute(
        select(Product).where(
            ~exists(select(ProcessRouting.id).where(ProcessRouting.product_id == Product.id))
        )
    )
    for p in products_without_routing.scalars():
        issues["warnings"].append(f"제품 '{p.code}'에 라우팅이 없습니다")

    # 2. 존재하지 않는 product_id 참조하는 작업지시 확인
    orphan_orders = await session.execute(
        select(WorkOrder).where(
            ~exists(select(Product.id).where(Product.id == WorkOrder.product_id))
        )
    )
    for o in orphan_orders.scalars():
        issues["errors"].append(
            f"작업지시 '{o.lot_no}'가 존재하지 않는 제품(ID:{o.product_id})을 참조합니다"
        )

    # 3. 존재하지 않는 std_process_id 참조하는 라우팅 확인
    orphan_routings = await session.execute(
        select(ProcessRouting).where(
            ~exists(select(StdProcess.id).where(StdProcess.id == ProcessRouting.std_process_id))
        )
    )
    for r in orphan_routings.scalars():
        issues["errors"].append(
            f"라우팅(ID:{r.id})이 존재하지 않는 표준공정(ID:{r.std_process_id})을 참조합니다"
        )

    # 4. 존재하지 않는 product_id 참조하는 시나리오 확인
    orphan_scenarios = await session.execute(
        select(Scenario).where(
            and_(
                Scenario.product_id.isnot(None),
                ~exists(select(Product.id).where(Product.id == Scenario.product_id)),
            )
        )
    )
    for s in orphan_scenarios.scalars():
        issues["errors"].append(
            f"시나리오 '{s.name}'이 존재하지 않는 제품(ID:{s.product_id})을 참조합니다"
        )

    # 5. 존재하지 않는 scenario_id 참조하는 작업지시 확인
    orphan_wo_scenarios = await session.execute(
        select(WorkOrder).where(
            and_(
                WorkOrder.scenario_id.isnot(None),
                ~exists(select(Scenario.id).where(Scenario.id == WorkOrder.scenario_id)),
            )
        )
    )
    for o in orphan_wo_scenarios.scalars():
        issues["warnings"].append(
            f"작업지시 '{o.lot_no}'가 존재하지 않는 시나리오(ID:{o.scenario_id})를 참조합니다"
        )

    # 6. 중복 lot_no 확인
    duplicate_lots = await session.execute(
        select(WorkOrder.lot_no, func.count(WorkOrder.id).label("cnt"))
        .group_by(WorkOrder.lot_no)
        .having(func.count(WorkOrder.id) > 1)
    )
    for lot_no, count in duplicate_lots.all():
        issues["errors"].append(f"중복된 lot_no '{lot_no}' ({count}건)")

    # 7. 중복 제품 코드 확인
    duplicate_product_codes = await session.execute(
        select(Product.code, func.count(Product.id).label("cnt"))
        .group_by(Product.code)
        .having(func.count(Product.id) > 1)
    )
    for code, count in duplicate_product_codes.all():
        issues["errors"].append(f"중복된 제품 코드 '{code}' ({count}건)")

    # 8. 중복 표준공정 코드 확인
    duplicate_process_codes = await session.execute(
        select(StdProcess.code, func.count(StdProcess.id).label("cnt"))
        .group_by(StdProcess.code)
        .having(func.count(StdProcess.id) > 1)
    )
    for code, count in duplicate_process_codes.all():
        issues["errors"].append(f"중복된 표준공정 코드 '{code}' ({count}건)")

    # 9. 검사계획 무결성 확인
    orphan_plans = await session.execute(
        select(InspectionPlan).where(
            ~exists(select(Product.id).where(Product.id == InspectionPlan.product_id))
        )
    )
    for p in orphan_plans.scalars():
        issues["errors"].append(
            f"검사계획 '{p.characteristic}'이 존재하지 않는 제품(ID:{p.product_id})을 참조합니다"
        )

    # 10. NCR 무결성 확인
    ncr_count = await session.execute(select(func.count(NonConformance.id)))
    ncr_total = ncr_count.scalar()

    # 11. 다운타임 무결성 확인
    dt_count = await session.execute(select(func.count(Downtime.id)))
    dt_total = dt_count.scalar()

    # 12. 알람 무결성 확인
    alarm_count = await session.execute(select(func.count(Alarm.id)))
    alarm_total = alarm_count.scalar()

    # 13. ProdResult-Downtime 시간 겹침 확인
    overlap_query = await session.execute(
        select(
            ProdResult.id.label("pr_id"),
            Downtime.id.label("dt_id"),
            ProdResult.equipment_id,
        )
        .select_from(ProdResult)
        .join(
            Downtime,
            and_(
                ProdResult.equipment_id == Downtime.equipment_id,
                ProdResult.start_time < Downtime.end_time,
                ProdResult.end_time > Downtime.start_time,
            ),
        )
        .where(ProdResult.end_time.isnot(None))
        .where(Downtime.end_time.isnot(None))
    )
    overlaps = overlap_query.all()
    for pr_id, dt_id, eq_id in overlaps:
        issues["warnings"].append(
            f"ProdResult(ID:{pr_id})와 Downtime(ID:{dt_id})이 설비(ID:{eq_id})에서 시간 겹침"
        )

    # 요약 정보 추가
    wo_count = await session.execute(select(func.count(WorkOrder.id)))
    pr_count = await session.execute(select(func.count(ProdResult.id)))
    ip_count = await session.execute(select(func.count(InspectionPlan.id)))
    ir_count = await session.execute(select(func.count(InspectionResult.id)))
    spc_count = await session.execute(select(func.count(SPCChart.id)))
    esh_count = await session.execute(select(func.count(EquipmentStatusHistory.id)))

    print("\n데이터 현황:")
    print(f"  작업지시: {wo_count.scalar()}건")
    print(f"  생산실적: {pr_count.scalar()}건")
    print(f"  검사계획: {ip_count.scalar()}건")
    print(f"  측정결과: {ir_count.scalar()}건")
    print(f"  SPC 차트: {spc_count.scalar()}건")
    print(f"  NCR: {ncr_total}건")
    print(f"  다운타임: {dt_total}건")
    print(f"  알람: {alarm_total}건")
    print(f"  설비상태이력: {esh_count.scalar()}건")

    return issues


async def run_validation():
    """독립 실행용 검증 함수"""
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("MES 시드 데이터 무결성 검증")
        print("=" * 60)

        issues = await validate_seed_data(session)

        if issues["errors"]:
            print(f"\n  {len(issues['errors'])}개 오류 발견:")
            for err in issues["errors"]:
                print(f"    - {err}")
        else:
            print("\n  오류 없음")

        if issues["warnings"]:
            print(f"\n  {len(issues['warnings'])}개 경고:")
            for warn in issues["warnings"]:
                print(f"    - {warn}")
        else:
            print("\n  경고 없음")

        print("\n" + "=" * 60)
        total_issues = len(issues["errors"]) + len(issues["warnings"])
        if total_issues == 0:
            print("검증 완료: 모든 데이터 연결이 올바릅니다.")
        else:
            print(f"검증 완료: {len(issues['errors'])}개 오류, {len(issues['warnings'])}개 경고")

        return issues


# ============================================================
# 메인 함수
# ============================================================


async def main(base_date: date | None = None, days: int = 30):
    """메인 시드 함수

    Args:
        base_date: 기준일 (None이면 오늘)
        days: 생성할 데이터 기간 (일)
    """
    if base_date is None:
        base_date = date.today()

    print("=" * 60)
    print(f"MES 통합 시드 데이터 생성 (기준일: {base_date}, {days}일간)")
    print("=" * 60)

    # DB 테이블 생성 (없으면)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            # 1. 기존 데이터 삭제
            await clear_existing_data(session)

            # 2. 마스터 데이터
            await seed_users(session)
            category_map = await seed_process_categories(session)
            cell_map = await seed_cells(session)
            eq_map = await seed_equipments(session, cell_map, base_date)
            process_map = await seed_std_processes(session, category_map)
            product_map = await seed_products_and_routings(session, process_map)
            scenario_map = await seed_scenarios(session, product_map)
            reason_map = await seed_downtime_reasons(session)
            alarm_def_map = await seed_alarm_definitions(session)

            # 3. 작업지시 & 생산실적
            work_orders = await seed_work_orders_and_results(
                session, product_map, scenario_map, eq_map, base_date, days
            )

            # 4. 품질 데이터
            plans = await seed_inspection_plans(session, product_map)
            devices = await seed_measurement_devices(session, base_date)
            inspection_results = await seed_inspection_results(
                session, plans, work_orders, eq_map, base_date, devices
            )
            await seed_spc_data(session, plans, work_orders, base_date)
            await seed_ncr(session, work_orders, inspection_results, plans, eq_map, base_date)

            # 5. 다운타임 이벤트
            await seed_downtimes(session, eq_map, reason_map, work_orders, base_date, days)

            # 6. 알람 이벤트
            await seed_alarms(session, eq_map, alarm_def_map, work_orders, base_date, days)

            # 7. 설비 상태 이력
            await seed_equipment_status_history(session, eq_map, work_orders, base_date, days)

            # 8. 검증
            await session.commit()

            print("\n" + "=" * 60)
            print("MES 통합 시드 데이터 생성 완료!")
            print("=" * 60)

            print("\n생성된 데이터 요약:")
            print(f"  - 기준일: {base_date}")
            print(f"  - 데이터 기간: {days}일")
            print(f"  - 공정 카테고리: {len(PROCESS_CATEGORIES)}개")
            print(f"  - 제조 셀: {len(CELLS)}개")
            print(f"  - 설비: {len(EQUIPMENTS)}개 (CNC 4, ROBOT 2, AMR 2, PLC 1)")
            print(f"  - 표준 공정: {len(STD_PROCESSES)}개")
            print(f"  - 제품: {len(PRODUCTS)}개")
            print(f"  - 시나리오: {len(SCENARIOS)}개")
            print(f"  - 다운타임 사유: {len(DOWNTIME_REASONS)}개")
            print(f"  - 알람 정의: {len(ALARM_DEFINITIONS)}개")
            print(f"  - 작업지시: {len(work_orders)}건")
            print(f"  - 검사계획: {len(plans)}개")
            print("  - NCR: 12건")
            print("  - 측정 장비: 4개")
            print("  + 생산실적, 측정결과, SPC, 다운타임, 알람, 설비이력")

            # 무결성 검증
            print("\n데이터 무결성 검증 중...")
            issues = await validate_seed_data(session)
            if issues["errors"]:
                print(f"  {len(issues['errors'])}개 오류 발견 - 확인 필요")
                for err in issues["errors"]:
                    print(f"    - {err}")
            if issues["warnings"]:
                print(f"  {len(issues['warnings'])}개 경고")
            if not issues["errors"] and not issues["warnings"]:
                print("  모든 데이터 연결이 올바릅니다.")

        except Exception as e:
            print(f"오류 발생: {e}")
            raise


def parse_args():
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="MES 통합 시드 데이터 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  uv run python -m src.seed_data                     # 기준일 = 오늘, 30일간
  uv run python -m src.seed_data --date 2026-02-10   # 기준일 = 2/10
  uv run python -m src.seed_data --days 60           # 60일간 데이터 생성
  uv run python -m src.seed_data --validate          # 검증만 수행
        """,
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="기준일 (YYYY-MM-DD 형식, 기본값: 오늘)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="생성할 데이터 기간 (일, 기본값: 30)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="데이터 검증만 수행 (시드 생성 없음)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.validate:
        asyncio.run(run_validation())
    else:
        base_date = None
        if args.date:
            try:
                base_date = date.fromisoformat(args.date)
            except ValueError:
                print(f"잘못된 날짜 형식: {args.date} (YYYY-MM-DD 형식을 사용하세요)")
                exit(1)

        asyncio.run(main(base_date=base_date, days=args.days))
