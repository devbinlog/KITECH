"""Tests for quality management functionality."""

import pytest
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.quality import (
    InspectionPlan,
    InspectionResult,
    SPCChart,
    SPCDataPoint,
    InspectionType,
    SPCControlType,
    NCRStatus,
)
from src.app.models.master import Product
from src.app.models.production import WorkOrder
from src.app.models.equipment import Equipment
from src.app.services.quality_service import QualityService


@pytest.fixture
async def test_product(db_session: AsyncSession) -> Product:
    """Create a test product."""
    product = Product(code="TEST-PRODUCT", name="Test Product", unit="EA")
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def test_equipment(db_session: AsyncSession) -> Equipment:
    """Create a test equipment."""
    equipment = Equipment(
        aas_id="TEST-CNC-001",
        eq_name="Test CNC Machine",
        model_name="CNC-2000",
        equipment_type="CNC",
        connection_config={"ip": "192.168.1.100", "port": 8080},
        spec_data={"max_spindle_speed": 8000, "axes": 3},
        current_status="RUN",
    )
    db_session.add(equipment)
    await db_session.commit()
    await db_session.refresh(equipment)
    return equipment


@pytest.fixture
async def test_work_order(db_session: AsyncSession, test_product: Product) -> WorkOrder:
    """Create a test work order."""
    work_order = WorkOrder(
        lot_no="WO-TEST-001",
        product_id=test_product.id,
        target_qty=100,
        qty=100,
        priority=5,
        status="RUNNING",
    )
    db_session.add(work_order)
    await db_session.commit()
    await db_session.refresh(work_order)
    return work_order


@pytest.fixture
async def test_inspection_plan(db_session: AsyncSession, test_product: Product) -> InspectionPlan:
    """Create a test inspection plan."""
    plan = InspectionPlan(
        product_id=test_product.id,
        characteristic="Diameter",
        lsl=9.8,
        usl=10.2,
        nominal=10.0,
        unit="mm",
        inspection_type=InspectionType.IN_PROCESS,
        enable_spc=True,
        spc_control_type=SPCControlType.X_BAR_R,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


class TestInspectionPlans:
    """Test inspection plan functionality."""

    async def test_create_inspection_plan(self, client, auth_headers, test_product: Product):
        """Test creating an inspection plan."""
        plan_data = {
            "product_id": test_product.id,
            "characteristic": "Length",
            "lsl": 49.5,
            "usl": 50.5,
            "nominal": 50.0,
            "unit": "mm",
            "inspection_type": "IN_PROCESS",
            "enable_spc": True,
            "spc_control_type": "X_BAR_R",
        }

        response = await client.post("/api/v1/quality/inspection-plans", json=plan_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["characteristic"] == "Length"
        assert data["product_id"] == test_product.id
        assert data["lsl"] == 49.5
        assert data["enable_spc"] is True

    async def test_get_inspection_plans_by_product(
        self, client, auth_headers, test_inspection_plan: InspectionPlan
    ):
        """Test getting inspection plans for a product."""
        response = await client.get(
            f"/api/v1/quality/inspection-plans/{test_inspection_plan.product_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["characteristic"] == "Diameter"


class TestInspectionResults:
    """Test inspection result functionality."""

    async def test_create_inspection_result_conforming(
        self, client, auth_headers, test_inspection_plan: InspectionPlan, test_work_order: WorkOrder
    ):
        """Test creating a conforming inspection result."""
        result_data = {
            "inspection_plan_id": test_inspection_plan.id,
            "work_order_id": test_work_order.id,
            "measured_value": 10.0,  # Within specification
            "serial_no": "SN001",
        }

        response = await client.post("/api/v1/quality/inspection-results", json=result_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["measured_value"] == 10.0
        assert data["is_conforming"] is True

    async def test_create_inspection_result_non_conforming(
        self, client, auth_headers, test_inspection_plan: InspectionPlan, test_work_order: WorkOrder
    ):
        """Test creating a non-conforming inspection result."""
        result_data = {
            "inspection_plan_id": test_inspection_plan.id,
            "work_order_id": test_work_order.id,
            "measured_value": 10.5,  # Above specification max (10.2)
            "serial_no": "SN002",
        }

        response = await client.post("/api/v1/quality/inspection-results", json=result_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["measured_value"] == 10.5
        assert data["is_conforming"] is False

    async def test_batch_create_inspection_results(
        self, client, auth_headers, test_inspection_plan: InspectionPlan, test_work_order: WorkOrder
    ):
        """Test batch creation of inspection results."""
        batch_data = {
            "inspection_plan_id": test_inspection_plan.id,
            "work_order_id": test_work_order.id,
            "results": [
                {"measured_value": 10.0, "serial_no": "SN001"},
                {"measured_value": 10.1, "serial_no": "SN002"},
                {"measured_value": 9.9, "serial_no": "SN003"},
            ],
        }

        response = await client.post("/api/v1/quality/inspection-results/batch", json=batch_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["created_count"] == 3
        assert len(data["created_results"]) == 3


class TestSPCFunctionality:
    """Test SPC calculation and analysis functionality."""

    async def test_spc_limit_calculation(
        self,
        db_session: AsyncSession,
        test_inspection_plan: InspectionPlan,
        test_work_order: WorkOrder,
    ):
        """Test SPC control limit calculation."""
        quality_service = QualityService(db_session)

        # Create sample data (5 subgroups of 5 samples each)
        sample_values = [
            [10.0, 10.1, 9.9, 10.0, 10.1],  # Subgroup 1
            [9.9, 10.0, 10.1, 10.0, 9.9],  # Subgroup 2
            [10.1, 10.0, 10.0, 10.1, 10.0],  # Subgroup 3
            [10.0, 9.9, 10.1, 10.0, 10.0],  # Subgroup 4
            [10.0, 10.1, 10.0, 9.9, 10.1],  # Subgroup 5
        ]

        # Create inspection results
        for subgroup_idx, subgroup in enumerate(sample_values):
            for sample_idx, value in enumerate(subgroup):
                result = InspectionResult(
                    inspection_plan_id=test_inspection_plan.id,
                    work_order_id=test_work_order.id,
                    measured_value=value,
                    is_conforming=True,
                    serial_no=f"SN{subgroup_idx:02d}{sample_idx:02d}",
                    measured_at=datetime.now(timezone.utc)
                    - timedelta(minutes=subgroup_idx * 10 + sample_idx),
                )
                db_session.add(result)

        await db_session.commit()

        # Calculate SPC limits
        spc_chart = await quality_service.calculate_spc_limits(test_inspection_plan.id)
        assert spc_chart is not None
        assert spc_chart.chart_type == SPCControlType.X_BAR_R
        assert spc_chart.center_line == pytest.approx(10.0, abs=0.1)
        assert spc_chart.upper_control_limit > spc_chart.center_line
        assert spc_chart.lower_control_limit < spc_chart.center_line

    async def test_capability_calculation(
        self,
        db_session: AsyncSession,
        test_inspection_plan: InspectionPlan,
        test_work_order: WorkOrder,
    ):
        """Test capability index calculation (Cp, Cpk)."""
        quality_service = QualityService(db_session)

        # Create normally distributed sample data around target
        import random

        random.seed(42)

        for i in range(50):  # Need sufficient data for capability analysis
            value = random.gauss(10.0, 0.05)  # Mean=10.0, StdDev=0.05
            result = InspectionResult(
                inspection_plan_id=test_inspection_plan.id,
                work_order_id=test_work_order.id,
                measured_value=value,
                is_conforming=9.8 <= value <= 10.2,
                serial_no=f"SN{i:03d}",
                measured_at=datetime.now(timezone.utc) - timedelta(minutes=i),
            )
            db_session.add(result)

        await db_session.commit()

        # Calculate capability
        capability = await quality_service.calculate_capability_indices(test_inspection_plan.id)
        assert capability is not None
        assert capability.sample_count == 50
        assert capability.mean == pytest.approx(10.0, abs=0.1)
        assert capability.cp is not None and capability.cp > 0
        assert capability.cpk is not None and capability.cpk > 0


class TestWesternElectricRules:
    """Test Western Electric Rules violation detection."""

    async def test_rule_1_violation(
        self, db_session: AsyncSession, test_inspection_plan: InspectionPlan
    ):
        """Test Rule 1: Point beyond control limits."""
        quality_service = QualityService(db_session)

        # Create SPC chart with known limits
        spc_chart = SPCChart(
            inspection_plan_id=test_inspection_plan.id,
            center_line=10.0,
            upper_control_limit=10.3,
            lower_control_limit=9.7,
            chart_type=SPCControlType.X_BAR_R,
            sample_count=10,
        )
        db_session.add(spc_chart)
        await db_session.commit()
        await db_session.refresh(spc_chart)

        # Create data points with one out of control
        data_points = [
            SPCDataPoint(
                spc_chart_id=spc_chart.id,
                subgroup_number=i,
                mean_value=10.5 if i == 5 else 10.0,  # Point 5 is out of control
                sample_size=5,
            )
            for i in range(1, 11)
        ]

        for point in data_points:
            db_session.add(point)
        await db_session.commit()

        # Check violations
        violations = await quality_service.check_western_electric_rules(spc_chart.id)
        assert len(violations) == 1
        assert violations[0].rule_number == 1
        assert 5 in violations[0].violated_points

    async def test_rule_2_violation(
        self, db_session: AsyncSession, test_inspection_plan: InspectionPlan
    ):
        """Test Rule 2: Nine points on same side of center line."""
        quality_service = QualityService(db_session)

        # Create SPC chart
        spc_chart = SPCChart(
            inspection_plan_id=test_inspection_plan.id,
            center_line=10.0,
            upper_control_limit=10.3,
            lower_control_limit=9.7,
            chart_type=SPCControlType.X_BAR_R,
            sample_count=12,
        )
        db_session.add(spc_chart)
        await db_session.commit()
        await db_session.refresh(spc_chart)

        # Create data points with 9 consecutive points above center line
        data_points = [
            SPCDataPoint(
                spc_chart_id=spc_chart.id,
                subgroup_number=i,
                mean_value=10.1 if 2 <= i <= 10 else 9.9,  # Points 2-10 above center
                sample_size=5,
            )
            for i in range(1, 13)
        ]

        for point in data_points:
            db_session.add(point)
        await db_session.commit()

        # Check violations
        violations = await quality_service.check_western_electric_rules(spc_chart.id)
        assert len(violations) == 1
        assert violations[0].rule_number == 2


class TestNCRManagement:
    """Test Non-Conformance Report functionality."""

    async def test_create_ncr(self, client: AsyncClient, auth_headers, test_work_order: WorkOrder):
        """Test creating an NCR."""
        ncr_data = {
            "work_order_id": test_work_order.id,
            "defect_type": "DIMENSION",
            "characteristic": "Dimensional tolerance",
            "description": "Part dimensions exceed specification limits",
            "reported_by": "Quality Inspector",
        }

        response = await client.post("/api/v1/quality/ncr", json=ncr_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["defect_type"] == "DIMENSION"
        assert data["status"] == "OPEN"
        assert data["is_auto_generated"] is False
        assert "NCR-" in data["ncr_no"]

    async def test_auto_generate_ncr(
        self,
        db_session: AsyncSession,
        test_inspection_plan: InspectionPlan,
        test_work_order: WorkOrder,
    ):
        """Test automatic NCR generation from SPC violations."""
        quality_service = QualityService(db_session)

        # Create mock violation rules
        from src.app.schemas.quality import SPCViolationRule

        violations = [
            SPCViolationRule(
                rule_number=1,
                rule_description="Point beyond control limits",
                violated_points=[5],
                severity="ALERT",
            )
        ]

        # Auto-generate NCR
        ncr = await quality_service.auto_generate_ncr(
            violations, test_inspection_plan.id, test_work_order.id
        )

        assert ncr is not None
        assert ncr.is_auto_generated is True
        assert ncr.status == NCRStatus.OPEN
        assert ncr.defect_type == "Process Control"
        assert "SPC Rule Violations" in ncr.description


class TestQualityTraceability:
    """Test quality traceability functionality."""

    async def test_quality_traceability(
        self,
        db_session: AsyncSession,
        test_inspection_plan: InspectionPlan,
        test_work_order: WorkOrder,
    ):
        """Test quality traceability for a serial number."""
        quality_service = QualityService(db_session)
        serial_no = "TRACE-001"

        # Create inspection result
        result = InspectionResult(
            inspection_plan_id=test_inspection_plan.id,
            work_order_id=test_work_order.id,
            measured_value=10.0,
            is_conforming=True,
            serial_no=serial_no,
        )
        db_session.add(result)
        await db_session.commit()

        # Get traceability
        traceability = await quality_service.get_quality_traceability(serial_no)

        assert traceability is not None
        assert traceability.serial_no == serial_no
        assert len(traceability.inspection_results) == 1
        assert traceability.overall_status == "PASS"
        assert traceability.quality_score == 100.0  # 100% conforming


class TestQualityAPI:
    """Test quality API endpoints."""

    async def test_get_spc_capability_analysis(
        self, client: AsyncClient, auth_headers, test_inspection_plan: InspectionPlan
    ):
        """Test SPC capability analysis endpoint."""
        response = await client.get(
            "/api/v1/quality/spc/capability",
            params={"product_id": test_inspection_plan.product_id},
            headers=auth_headers,
        )
        # May return empty if insufficient data, but should not error
        assert response.status_code == 200

    async def test_quality_dashboard_summary(self, client: AsyncClient, auth_headers):
        """Test quality dashboard summary endpoint."""
        response = await client.get("/api/v1/quality/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_inspections" in data
        assert "quality_rate_percent" in data
        assert "open_ncrs" in data
        assert "active_spc_charts" in data

    async def test_traceability_api(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_inspection_plan: InspectionPlan,
        test_work_order: WorkOrder,
    ):
        """Test quality traceability API endpoint."""
        serial_no = "API-TRACE-001"

        # Create inspection result first
        result = InspectionResult(
            inspection_plan_id=test_inspection_plan.id,
            work_order_id=test_work_order.id,
            measured_value=10.0,
            is_conforming=True,
            serial_no=serial_no,
        )
        db_session.add(result)
        await db_session.commit()

        # Test traceability endpoint
        response = await client.get(f"/api/v1/quality/traceability/{serial_no}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["serial_no"] == serial_no
        assert data["overall_status"] == "PASS"
