"""Equipment status polling service."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.equipment import Equipment, EqLog
from ...clients.middleware_client import middleware_client


import copy

def _deep_merge(target, source):
    """
    딕셔너리를 재귀적으로 병합. 빈 딕셔너리나 None 등 Falsy 값으로 덮어쓰는 것을 방지.
    """
    result = copy.deepcopy(target)
    for k, v in source.items():
        if isinstance(v, dict) and k in result and isinstance(result[k], dict):
            # source의 v가 빈 dict이면 병합하지 않고 기존 정보 유지
            if v:
                result[k] = _deep_merge(result[k], v)
        else:
            # 새로운 값이 유효할 때만 덮어쓰기 (단, bool False, 0등은 유효할 수 있으니 단순 if v로는 위험하지만, 
            # 미들웨어 특성상 None이나 빈 dict, 빈 스트링이 문제이므로 기본 if 조건을 사용하되 Boolean이면 업데이트하도록 처리)
            if v or isinstance(v, (bool, int, float)):
                result[k] = copy.deepcopy(v)
    return result

def _parse_aas_item(aas_item: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """
    미들웨어 AAS 응답 항목을 MES last_data 형식으로 변환.

    Args:
        aas_item: /api/aas/view의 개별 항목 (`id`, `idShort`, `submodels`)

    Returns:
        (parsed_data, status) 튜플
    """
    submodels = aas_item.get("submodels", {})

    # 각 게이트웨이 서브모델 추출
    cnc = submodels.get("cncGateway", {})
    modbus = submodels.get("modbusGateway", {})
    robot = submodels.get("robotGateway", {})
    work_info = submodels.get("workInformation", {})

    is_connected = (
        cnc.get("isConnected")
        or modbus.get("isConnected")
        or robot.get("isConnected")
        or False
    )

    cnc_status = cnc.get("status", {})
    modbus_status = modbus.get("status", {})
    robot_status = robot.get("status", {})

    # 상태 결정 논리만 추출하고, 반환 데이터는 전체 submodels 원본을 넘김
    # 프론트엔드에서 확장성 있게 쓰기 위함
    parsed = submodels

    # 상태 결정 논리
    if not is_connected:
        status = "STOP"
    elif robot_status.get("status") in ("IDLE",):
        status = "IDLE"
    elif robot_status.get("status") in ("BUSY", "RUN", "RUNNING", "WORKING", "ACTIVE"):
        # 로봇이 작업 중인 경우 RUN으로 표시
        status = "RUN"
    elif cnc_status.get("doorState") == "open" and is_connected:
        status = "RUN"
    else:
        status = "IDLE"

    return parsed, status


async def poll_equipment_status(db: AsyncSession, equipment: Equipment) -> Equipment:
    """
    단일 설비 상태 폴링 (미들웨어 AAS view에서 해당 설비 찾아 갱신).

    Args:
        db: 데이터베이스 세션
        equipment: 갱신할 설비 객체

    Returns:
        갱신된 설비 객체
    """
    try:
        # AAS 전체 조회 후 aas_id로 매칭
        aas_list = await middleware_client.fetch_all_assets()
        matched = next(
            (item for item in aas_list if item.get("id") == equipment.aas_id),
            None,
        )

        if matched is None:
            logger.debug(
                "설비 '%s' (aas_id=%s)를 미들웨어에서 찾을 수 없음",
                equipment.eq_name,
                equipment.aas_id,
            )
            return equipment

        parsed_data, status = _parse_aas_item(matched)

        # 깜빡임 방지: 빈 데이터 무시 및 객체 병합
        is_empty_parsed = not parsed_data or len(parsed_data) == 0
        if is_empty_parsed and equipment.last_data:
            pass  # 기존 상태 유지
        else:
            current_data = equipment.last_data or {}
            if isinstance(current_data, dict) and isinstance(parsed_data, dict):
                equipment.last_data = _deep_merge(current_data, parsed_data)
            else:
                equipment.last_data = parsed_data

        equipment.current_status = status
        equipment.last_connected_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(equipment)

    except Exception as e:
        log = EqLog(
            equipment_id=equipment.id,
            level="WARN",
            message=f"폴링 실패: {str(e)}",
        )
        db.add(log)
        equipment.current_status = "ERROR"
        try:
            await db.commit()
            await db.refresh(equipment)
        except Exception as commit_err:
            await db.rollback()
            logger.error("설비 %s 오류 상태 커밋 실패: %s", equipment.id, commit_err)

    return equipment


async def poll_all_equipments(db: AsyncSession) -> List[Equipment]:
    """
    전체 설비 상태 일괄 폴링.
    미들웨어에서 한 번만 aas/view를 호출하여 모든 설비를 갱신합니다.

    Args:
        db: 데이터베이스 세션

    Returns:
        갱신된 설비 목록
    """
    # 미들웨어에서 전체 AAS 데이터 한 번에 가져오기
    try:
        aas_list = await middleware_client.fetch_all_assets()
    except Exception as e:
        logger.warning("미들웨어 AAS 목록 조회 실패: %s", e)
        return []

    # aas_id → aas_item 인덱스 생성
    aas_map: Dict[str, Dict[str, Any]] = {
        item["id"]: item for item in aas_list if "id" in item
    }

    # DB에서 활성 설비 전체 조회
    result = await db.execute(select(Equipment).where(Equipment.is_deleted.is_(False)))
    equipments = list(result.scalars().all())

    updated = []
    now = datetime.now(timezone.utc)

    for equipment in equipments:
        aas_item = aas_map.get(equipment.aas_id)
        if aas_item is None:
            # 미들웨어에 해당 설비 없음 → 건너뜀 (시드 데이터 설비는 aas_id가 다를 수 있음)
            continue

        try:
            parsed_data, status = _parse_aas_item(aas_item)
            
            # 깜빡임 방지: 만약 미들웨어가 일시적으로 빈 submodels를 주더라도,
            # 기존에 있던 유효한 상세 데이터가 있다면 무시 (비정상적인 응답일 수 있음)
            # 단, 연결 상태 변경 등은 감지해야 하므로 완전히 버리진 않고 병합하거나
            # submodels 자체가 완전히 비어있는 경우에만 스킵
            is_empty_parsed = not parsed_data or len(parsed_data) == 0
            
            if is_empty_parsed and equipment.last_data:
                # 미들웨어가 일시적으로 데이터를 주지 않았을 때: 기존 데이터 유지
                pass
            else:
                # 깊은 병합: 내부 중첩 dict까지 보호
                current_data = equipment.last_data or {}
                if isinstance(current_data, dict) and isinstance(parsed_data, dict):
                    equipment.last_data = _deep_merge(current_data, parsed_data)
                else:
                    equipment.last_data = parsed_data
                
            equipment.current_status = status
            equipment.last_connected_at = now
            updated.append(equipment)
        except Exception as e:
            logger.warning("설비 '%s' 데이터 파싱 오류: %s", equipment.eq_name, e)

    if updated:
        try:
            await db.commit()
            logger.debug("%d개 설비 상태 미들웨어 데이터로 갱신 완료", len(updated))
        except Exception as e:
            await db.rollback()
            logger.error("설비 상태 일괄 커밋 실패: %s", e)
            return []

    return updated
