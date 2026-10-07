"""
MES 과거 실적 데이터 및 미래 작업지시 생성 스크립트

MES v5 Schema:
- WorkOrder: plan_start/plan_end → start_time/end_time
- WorkOrder: completed_qty, current_process 추가
- ProdResult: target_equipment_id 추가

- 지난 3개월 (11월, 12월, 1월) 실적 데이터 생성
- 2월말까지 대기 작업지시 생성

사용법:
    cd agents/cell-mes
    uv run python -m src.seed_historical_data
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone, date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import AsyncSessionLocal
from src.app.models.equipment import Equipment
from src.app.models.master import Product, Scenario
from src.app.models.production import WorkOrder, ProdResult


async def get_existing_data(session: AsyncSession):
    """기존 마스터 데이터 조회"""
    # 제품 조회
    result = await session.execute(select(Product))
    products = {p.code: p for p in result.scalars().all()}

    # 설비 조회 (CNC만)
    result = await session.execute(select(Equipment).where(Equipment.equipment_type == "CNC"))
    equipments = list(result.scalars().all())

    # 시나리오 조회
    result = await session.execute(select(Scenario))
    scenarios = {s.name: s for s in result.scalars().all()}

    return products, equipments, scenarios


async def get_max_lot_number(session: AsyncSession) -> int:
    """현재 최대 LOT 번호 조회"""
    result = await session.execute(select(func.max(WorkOrder.lot_no)))
    max_lot = result.scalar()
    if max_lot and "LOT-" in max_lot:
        try:
            return int(max_lot.split("-")[-1])
        except Exception:
            pass
    return 0


async def get_max_work_order_id(session: AsyncSession) -> int:
    """현재 최대 작업지시 ID 조회"""
    result = await session.execute(select(func.max(WorkOrder.id)))
    max_id = result.scalar()
    return max_id or 0


async def get_max_prod_result_id(session: AsyncSession) -> int:
    """현재 최대 생산실적 ID 조회"""
    result = await session.execute(select(func.max(ProdResult.id)))
    max_id = result.scalar()
    return max_id or 0


async def seed_historical_data(session: AsyncSession):
    """지난 3개월 실적 데이터 생성 (11월, 12월, 1월) - MES v5 스키마"""
    print("=" * 60)
    print("지난 3개월 실적 데이터 생성 (2025년 11월 ~ 2026년 1월)")
    print("=" * 60)

    products, equipments, scenarios = await get_existing_data(session)

    if not products:
        print("❌ 제품 데이터가 없습니다. 먼저 seed_data.py를 실행하세요.")
        return

    if not equipments:
        print("❌ CNC 설비 데이터가 없습니다.")
        return

    print(f"  제품: {len(products)}개")
    print(f"  CNC 설비: {len(equipments)}개")

    # 제품-시나리오 매핑
    product_scenario_map = {
        "PART-A100": "A100 표준 가공",
        "PART-B200": "B200 표준 가공",
        "PART-C300": "C300 정밀 가공",
        "ASSY-D100": "D100 조립 시나리오",
        "PART-E500": "E500 기어 가공",
    }

    lot_counter = await get_max_lot_number(session) + 1
    wo_id_counter = await get_max_work_order_id(session) + 1
    pr_id_counter = await get_max_prod_result_id(session) + 1
    product_codes = list(products.keys())

    # 3개월 데이터 생성 (2025-11-01 ~ 2026-01-31)
    start_date = date(2025, 11, 1)
    end_date = date(2026, 1, 31)

    current_date = start_date
    total_wo = 0
    total_results = 0

    while current_date <= end_date:
        # 주말은 작업량 감소
        is_weekend = current_date.weekday() >= 5
        daily_orders = random.randint(1, 3) if is_weekend else random.randint(3, 6)

        for _ in range(daily_orders):
            product_code = random.choice(product_codes)
            product = products[product_code]
            target_qty = random.choice([30, 50, 80, 100, 120, 150, 200])

            scenario_name = product_scenario_map.get(product_code)
            scenario = scenarios.get(scenario_name) if scenario_name else None

            # 작업 시간 (오전 8시 ~ 오후 6시)
            work_hour = random.randint(8, 17)
            work_datetime = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                work_hour,
                random.randint(0, 59),
                0,
                tzinfo=timezone.utc,
            )

            # 납기일: 작업일 + 3~10일
            due_date = work_datetime + timedelta(days=random.randint(3, 10))

            # MES v5: start_time/end_time (실제 실행 시간)
            start_time = work_datetime
            end_time = work_datetime + timedelta(hours=random.randint(4, 12))

            # 작업지시 생성 (모두 완료 상태)
            work_order = WorkOrder(
                id=wo_id_counter,  # SQLite BIGINT 위해 명시적 ID
                lot_no=f"LOT-2025-{lot_counter:05d}",
                product_id=product.id,
                scenario_id=scenario.id if scenario else None,
                target_qty=target_qty,
                qty=target_qty,
                priority=random.randint(1, 5),
                due_date=due_date,
                # MES v5 fields
                completed_qty=target_qty,
                current_process=None,  # 완료된 작업은 None
                start_time=start_time,
                end_time=end_time,
                status="DONE",
                created_at=work_datetime,
            )
            session.add(work_order)
            await session.flush()
            wo_id_counter += 1

            # 생산 실적 생성
            equipment = random.choice(equipments)

            # 수율 90~99% (가끔 낮은 수율)
            yield_rate = random.choices(
                [random.uniform(0.90, 0.99), random.uniform(0.75, 0.89)], weights=[90, 10]
            )[0]

            ok_qty = int(target_qty * yield_rate)
            ng_qty = target_qty - ok_qty

            # 작업 시간 (실제)
            actual_start = start_time + timedelta(minutes=random.randint(0, 30))
            actual_end = actual_start + timedelta(hours=random.randint(2, 8))

            prod_result = ProdResult(
                id=pr_id_counter,  # SQLite BIGINT 위해 명시적 ID
                work_order_id=work_order.id,
                equipment_id=equipment.id,
                target_equipment_id=equipment.id,  # MES v5: 스케줄러 배정 설비
                start_time=actual_start,
                end_time=actual_end,
                ok_qty=ok_qty,
                ng_qty=ng_qty,
            )
            session.add(prod_result)
            pr_id_counter += 1

            lot_counter += 1
            total_wo += 1
            total_results += 1

        current_date += timedelta(days=1)

    await session.commit()
    print("\n✅ 과거 데이터 생성 완료:")
    print(f"   - 작업지시: {total_wo}건")
    print(f"   - 생산실적: {total_results}건")

    return lot_counter, wo_id_counter


async def seed_future_work_orders(session: AsyncSession, lot_counter: int, wo_id_counter: int):
    """2월말까지 대기 작업지시 생성 - MES v5 스키마"""
    print("\n" + "=" * 60)
    print("2월 대기 작업지시 생성 (2026년 2월 2일 ~ 2월 28일)")
    print("=" * 60)

    products, equipments, scenarios = await get_existing_data(session)

    product_scenario_map = {
        "PART-A100": "A100 표준 가공",
        "PART-B200": "B200 표준 가공",
        "PART-C300": "C300 정밀 가공",
        "ASSY-D100": "D100 조립 시나리오",
        "PART-E500": "E500 기어 가공",
    }

    product_codes = list(products.keys())

    # 2월 2일 ~ 2월 28일 대기 작업지시
    start_date = date(2026, 2, 2)
    end_date = date(2026, 2, 28)

    current_date = start_date
    total_wo = 0

    while current_date <= end_date:
        # 주말은 작업량 감소
        is_weekend = current_date.weekday() >= 5
        daily_orders = random.randint(1, 2) if is_weekend else random.randint(2, 5)

        for _ in range(daily_orders):
            product_code = random.choice(product_codes)
            product = products[product_code]
            target_qty = random.choice([30, 50, 80, 100, 120, 150])

            scenario_name = product_scenario_map.get(product_code)
            scenario = scenarios.get(scenario_name) if scenario_name else None

            # 납기일: 해당 날짜 + 1~5일
            due_datetime = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                18,
                0,
                0,
                tzinfo=timezone.utc,
            )
            due_date = due_datetime + timedelta(days=random.randint(1, 5))

            # MES v5: READY 상태는 start_time/end_time이 None
            work_order = WorkOrder(
                id=wo_id_counter,  # SQLite BIGINT 위해 명시적 ID
                lot_no=f"LOT-2026-{lot_counter:05d}",
                product_id=product.id,
                scenario_id=scenario.id if scenario else None,
                target_qty=target_qty,
                qty=target_qty,
                priority=random.randint(1, 5),
                due_date=due_date,
                # MES v5 fields - READY 상태
                completed_qty=0,
                current_process=None,
                start_time=None,  # 스케줄링 전
                end_time=None,
                status="READY",  # 대기 상태
                created_at=datetime.now(timezone.utc),
            )
            session.add(work_order)
            wo_id_counter += 1

            lot_counter += 1
            total_wo += 1

        current_date += timedelta(days=1)

    await session.commit()
    print("\n✅ 대기 작업지시 생성 완료:")
    print(f"   - 작업지시: {total_wo}건 (상태: READY)")


async def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("MES 과거 실적 및 미래 작업지시 데이터 생성 (MES v5 스키마)")
    print("=" * 60 + "\n")

    async with AsyncSessionLocal() as session:
        # 1. 지난 3개월 실적 데이터
        result = await seed_historical_data(session)
        if result is None:
            print("❌ 마스터 데이터가 없습니다. seed_data.py를 먼저 실행하세요.")
            return
        lot_counter, wo_id_counter = result

        # 2. 2월 대기 작업지시
        await seed_future_work_orders(session, lot_counter, wo_id_counter)

    print("\n" + "=" * 60)
    print("✅ 모든 데이터 생성 완료!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
