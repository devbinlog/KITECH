"""Integration-style workflow tests for production and quality lifecycles."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.production import WorkOrder, ProdResult
from src.app.models.quality import (
    InspectionPlan,
    InspectionResult,
    NonConformance,
    NCRStatus,
    InspectionType,
)


# ---------------------------------------------------------------------------
# Production lifecycle workflow
# ---------------------------------------------------------------------------


class TestProductionWorkflow:
    """Test WorkOrder lifecycle: create → READY → SCHEDULED → RUNNING → DONE."""

    @pytest.mark.asyncio
    async def test_work_order_full_lifecycle_state_transitions(
        self, db_session: AsyncSession, sample_product
    ):
        """WorkOrder goes through all expected state transitions."""
        # 1. Create in READY
        order = WorkOrder(
            lot_no="WF-LOT-001",
            product_id=sample_product.id,
            target_qty=50,
            status="READY",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.status == "READY"
        assert order.id is not None

        # 2. READY → SCHEDULED
        assert order.can_transition_to("SCHEDULED") is True
        order.status = "SCHEDULED"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "SCHEDULED"

        # 3. SCHEDULED → RUNNING
        assert order.can_transition_to("RUNNING") is True
        order.status = "RUNNING"
        order.start_time = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "RUNNING"
        assert order.start_time is not None

        # 4. Add production results
        result = ProdResult(
            work_order_id=order.id,
            ok_qty=45,
            ng_qty=5,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.id is not None
        assert result.ok_qty == 45
        assert result.ng_qty == 5
        assert result.total_qty == 50
        assert result.yield_rate == pytest.approx(90.0)

        # 5. RUNNING → DONE
        assert order.can_transition_to("DONE") is True
        order.status = "DONE"
        order.end_time = datetime.now(timezone.utc)
        order.completed_qty = 45
        await db_session.commit()
        await db_session.refresh(order)

        assert order.status == "DONE"
        assert order.end_time is not None
        assert order.completed_qty == 45

        # 6. DONE is terminal – no further transitions
        assert order.can_transition_to("RUNNING") is False
        assert order.can_transition_to("READY") is False
        assert order.can_transition_to("PAUSE") is False

    @pytest.mark.asyncio
    async def test_work_order_pause_resume_workflow(
        self, db_session: AsyncSession, sample_product
    ):
        """WorkOrder can be paused and resumed while RUNNING."""
        order = WorkOrder(
            lot_no="WF-LOT-002",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # RUNNING → PAUSE
        assert order.can_transition_to("PAUSE") is True
        order.status = "PAUSE"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "PAUSE"

        # PAUSE → RUNNING
        assert order.can_transition_to("RUNNING") is True
        order.status = "RUNNING"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "RUNNING"

        # RUNNING → DONE
        assert order.can_transition_to("DONE") is True
        order.status = "DONE"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "DONE"

    @pytest.mark.asyncio
    async def test_work_order_error_recovery_workflow(
        self, db_session: AsyncSession, sample_product
    ):
        """WorkOrder recovers from ERROR state back to RUNNING."""
        order = WorkOrder(
            lot_no="WF-LOT-003",
            product_id=sample_product.id,
            target_qty=80,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # RUNNING → ERROR
        assert order.can_transition_to("ERROR") is True
        order.status = "ERROR"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "ERROR"

        # ERROR → RUNNING (recovery)
        assert order.can_transition_to("RUNNING") is True
        order.status = "RUNNING"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "RUNNING"

    @pytest.mark.asyncio
    async def test_prod_result_yield_rate_zero_qty(
        self, db_session: AsyncSession, sample_work_order
    ):
        """ProdResult with zero qty returns yield_rate of 0.0."""
        result = ProdResult(
            work_order_id=sample_work_order.id,
            ok_qty=0,
            ng_qty=0,
        )
        assert result.yield_rate == 0.0
        assert result.total_qty == 0

    @pytest.mark.asyncio
    async def test_multiple_prod_results_for_one_work_order(
        self, db_session: AsyncSession, sample_work_order
    ):
        """Multiple ProdResults can be associated with a single WorkOrder."""
        results = [
            ProdResult(work_order_id=sample_work_order.id, ok_qty=30, ng_qty=2),
            ProdResult(work_order_id=sample_work_order.id, ok_qty=25, ng_qty=1),
        ]
        for r in results:
            db_session.add(r)
        await db_session.commit()

        for r in results:
            await db_session.refresh(r)

        assert results[0].id is not None
        assert results[1].id is not None
        assert results[0].id != results[1].id

    @pytest.mark.asyncio
    async def test_cancel_from_scheduled(self, db_session: AsyncSession, sample_product):
        """WorkOrder can be cancelled from SCHEDULED state."""
        order = WorkOrder(
            lot_no="WF-LOT-CANCEL-001",
            product_id=sample_product.id,
            target_qty=10,
            status="SCHEDULED",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.can_transition_to("CANCEL") is True
        order.status = "CANCEL"
        await db_session.commit()
        await db_session.refresh(order)
        assert order.status == "CANCEL"

        # CANCEL is terminal
        assert order.can_transition_to("RUNNING") is False
        assert order.can_transition_to("READY") is False


# ---------------------------------------------------------------------------
# Quality workflow
# ---------------------------------------------------------------------------


class TestQualityWorkflow:
    """Test InspectionPlan → InspectionResult → NCR lifecycle."""

    @pytest_asyncio.fixture
    async def inspection_plan(self, db_session: AsyncSession, sample_product) -> InspectionPlan:
        plan = InspectionPlan(
            product_id=sample_product.id,
            characteristic="외경",
            nominal=25.0,
            usl=25.05,
            lsl=24.95,
            unit="mm",
            inspection_type=InspectionType.IN_PROCESS,
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        return plan

    @pytest.mark.asyncio
    async def test_inspection_plan_creation(
        self, db_session: AsyncSession, inspection_plan: InspectionPlan
    ):
        """InspectionPlan is created with correct attributes."""
        assert inspection_plan.id is not None
        assert inspection_plan.characteristic == "외경"
        assert inspection_plan.nominal == pytest.approx(25.0)
        assert inspection_plan.usl == pytest.approx(25.05)
        assert inspection_plan.lsl == pytest.approx(24.95)
        assert inspection_plan.is_active is True

    @pytest.mark.asyncio
    async def test_conforming_inspection_result(
        self,
        db_session: AsyncSession,
        inspection_plan: InspectionPlan,
        sample_work_order: WorkOrder,
    ):
        """Conforming measurement is recorded correctly."""
        result = InspectionResult(
            inspection_plan_id=inspection_plan.id,
            work_order_id=sample_work_order.id,
            measured_value=25.01,
            deviation=0.01,
            is_conforming=True,
            source="MANUAL",
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.id is not None
        assert result.is_conforming is True
        assert result.measured_value == pytest.approx(25.01)

    @pytest.mark.asyncio
    async def test_nonconforming_inspection_result(
        self,
        db_session: AsyncSession,
        inspection_plan: InspectionPlan,
        sample_work_order: WorkOrder,
    ):
        """Non-conforming measurement is recorded with correct flag."""
        result = InspectionResult(
            inspection_plan_id=inspection_plan.id,
            work_order_id=sample_work_order.id,
            measured_value=25.10,  # exceeds USL 25.05
            deviation=0.10,
            is_conforming=False,
            source="CMM",
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.is_conforming is False
        assert result.measured_value == pytest.approx(25.10)

    @pytest.mark.asyncio
    async def test_ncr_creation_from_inspection(
        self,
        db_session: AsyncSession,
        inspection_plan: InspectionPlan,
        sample_work_order: WorkOrder,
    ):
        """NCR can be created from a non-conforming inspection result."""
        # First record the inspection result
        inspection_result = InspectionResult(
            inspection_plan_id=inspection_plan.id,
            work_order_id=sample_work_order.id,
            measured_value=25.10,
            deviation=0.10,
            is_conforming=False,
            source="MANUAL",
        )
        db_session.add(inspection_result)
        await db_session.commit()
        await db_session.refresh(inspection_result)

        # Create NCR linked to inspection result
        ncr = NonConformance(
            ncr_no="NCR-2026-0001",
            work_order_id=sample_work_order.id,
            lot_no=sample_work_order.lot_no,
            inspection_result_id=inspection_result.id,
            inspection_plan_id=inspection_plan.id,
            defect_type="DIMENSION",
            characteristic="외경",
            specified_value=25.0,
            actual_value=25.10,
            description="외경 치수 초과: 25.10mm (USL: 25.05mm)",
            disposition="REWORK",
            status=NCRStatus.OPEN,
            reported_by="operator1",
        )
        db_session.add(ncr)
        await db_session.commit()
        await db_session.refresh(ncr)

        assert ncr.id is not None
        assert ncr.ncr_no == "NCR-2026-0001"
        assert ncr.status == NCRStatus.OPEN
        assert ncr.defect_type == "DIMENSION"

    @pytest.mark.asyncio
    async def test_ncr_status_transitions(
        self,
        db_session: AsyncSession,
        sample_work_order: WorkOrder,
    ):
        """NCR goes through status lifecycle: OPEN → IN_PROGRESS → CLOSED."""
        ncr = NonConformance(
            ncr_no="NCR-2026-0002",
            defect_type="SURFACE",
            characteristic="표면조도",
            description="표면 스크래치 발생",
            disposition="REWORK",
            status=NCRStatus.OPEN,
            reported_by="inspector1",
        )
        db_session.add(ncr)
        await db_session.commit()
        await db_session.refresh(ncr)
        assert ncr.status == NCRStatus.OPEN

        # OPEN → IN_PROGRESS
        ncr.status = NCRStatus.IN_PROGRESS
        ncr.assigned_to = "engineer1"
        ncr.root_cause = "공구 마모"
        await db_session.commit()
        await db_session.refresh(ncr)
        assert ncr.status == NCRStatus.IN_PROGRESS
        assert ncr.assigned_to == "engineer1"

        # IN_PROGRESS → CLOSED
        ncr.status = NCRStatus.CLOSED
        ncr.corrective_action = "공구 교체 및 재작업"
        ncr.closed_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(ncr)
        assert ncr.status == NCRStatus.CLOSED
        assert ncr.closed_at is not None
        assert ncr.corrective_action is not None

    @pytest.mark.asyncio
    async def test_ncr_verified_status(self, db_session: AsyncSession):
        """NCR can be set to VERIFIED state."""
        ncr = NonConformance(
            ncr_no="NCR-2026-0003",
            defect_type="MATERIAL",
            characteristic="경도",
            description="경도 불량",
            disposition="SCRAP",
            status=NCRStatus.OPEN,
            reported_by="qc_team",
        )
        db_session.add(ncr)
        await db_session.commit()
        await db_session.refresh(ncr)

        ncr.status = NCRStatus.VERIFIED
        await db_session.commit()
        await db_session.refresh(ncr)
        assert ncr.status == NCRStatus.VERIFIED

    @pytest.mark.asyncio
    async def test_ncr_cancelled_status(self, db_session: AsyncSession):
        """NCR can be cancelled."""
        ncr = NonConformance(
            ncr_no="NCR-2026-0004",
            defect_type="DIMENSION",
            characteristic="길이",
            description="길이 오차 (측정 오류 의심)",
            disposition="PENDING",
            status=NCRStatus.OPEN,
            reported_by="operator2",
        )
        db_session.add(ncr)
        await db_session.commit()
        await db_session.refresh(ncr)

        ncr.status = NCRStatus.CANCELLED
        await db_session.commit()
        await db_session.refresh(ncr)
        assert ncr.status == NCRStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_auto_generated_ncr(self, db_session: AsyncSession):
        """Auto-generated NCR (from SPC alert) has correct flag set."""
        ncr = NonConformance(
            ncr_no="NCR-2026-AUTO-001",
            defect_type="DIMENSION",
            characteristic="외경",
            description="SPC 관리한계 초과 자동 생성",
            disposition="PENDING",
            status=NCRStatus.OPEN,
            reported_by="SYSTEM",
            is_auto_generated=True,
            trigger_data={"rule": "Western Electric Rule 1", "value": 25.15, "ucl": 25.05},
        )
        db_session.add(ncr)
        await db_session.commit()
        await db_session.refresh(ncr)

        assert ncr.is_auto_generated is True
        assert ncr.trigger_data["rule"] == "Western Electric Rule 1"

    @pytest.mark.asyncio
    async def test_multiple_inspection_results_for_plan(
        self,
        db_session: AsyncSession,
        inspection_plan: InspectionPlan,
        sample_work_order: WorkOrder,
    ):
        """Multiple inspection results can be linked to the same plan."""
        values = [24.98, 25.00, 25.02, 25.01, 24.99]
        for val in values:
            r = InspectionResult(
                inspection_plan_id=inspection_plan.id,
                work_order_id=sample_work_order.id,
                measured_value=val,
                is_conforming=(inspection_plan.lsl <= val <= inspection_plan.usl),
                source="CMM",
            )
            db_session.add(r)

        await db_session.commit()

        from sqlalchemy import select
        stmt = select(InspectionResult).where(
            InspectionResult.inspection_plan_id == inspection_plan.id
        )
        rows = (await db_session.execute(stmt)).scalars().all()
        assert len(rows) == 5
        assert all(r.is_conforming for r in rows)
