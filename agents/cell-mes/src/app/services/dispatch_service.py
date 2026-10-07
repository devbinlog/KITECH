"""Dispatch Queue Daemon for Lot-Size 1 Architecture."""

import asyncio
import logging

from sqlalchemy import select, func

from ..db.session import AsyncSessionLocal
from ..models.production import WorkOrder, Unit

logger = logging.getLogger(__name__)

async def run_dispatch_loop():
    """Main producer loop to populate exactly 1 READY unit per active WorkOrder."""
    interval = 2.0  # 2 second intervals
    logger.info("Starting Dispatch Daemon Service (Lot-Size 1) (간격: %.1fs)", interval)
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # 1. Fetch all RUNNING work orders
                result = await db.execute(
                    select(WorkOrder)
                    .where(WorkOrder.status == "RUNNING")
                )
                active_orders = result.scalars().all()

                for order in active_orders:
                    # 2. Check if we reached the target quantity
                    unit_count_result = await db.execute(
                        select(func.count(Unit.id)).where(Unit.work_order_id == order.id)
                    )
                    total_dispatched_units = unit_count_result.scalar() or 0
                    
                    if total_dispatched_units >= order.target_qty:
                        continue
                    
                    # 3. Count units occupying the ready queue slot.
                    # SCENARIO_HOLD is hidden from middleware but still prevents
                    # generating a replacement READY unit for this order.
                    ready_count_result = await db.execute(
                        select(func.count(Unit.id)).where(
                            Unit.work_order_id == order.id,
                            Unit.status.in_(["READY", "SCENARIO_HOLD"])
                        )
                    )
                    ready_count = ready_count_result.scalar() or 0
                    
                    # 4. If 0 READY units, we create exactly 1
                    if ready_count == 0:
                        next_unit_no = total_dispatched_units + 1
                        logger.info(f"Dispatch Daemon: Generating Unit {next_unit_no} for WorkOrder {order.lot_no}")
                        
                        new_unit = Unit(
                            work_order_id=order.id,
                            unit_no=next_unit_no,
                            scenario_id=order.scenario_id,
                            status="READY"
                        )
                        db.add(new_unit)
                        await db.commit()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in DispatchDaemon loop: {e}", exc_info=True)
            
        await asyncio.sleep(interval)
        
    logger.info("Dispatch Daemon Service 종료")
