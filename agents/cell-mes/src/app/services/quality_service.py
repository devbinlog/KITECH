"""Quality service for SPC calculations and quality management."""

import statistics
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from ..models.quality import (
    InspectionPlan,
    InspectionResult,
    SPCChart,
    SPCDataPoint,
    NonConformance,
    SPCControlType,
    NCRStatus,
)
from ..models.production import WorkOrder
from ..schemas.quality import (
    SPCCapabilityAnalysis,
    SPCViolationRule,
    QualityTraceabilityRecord,
)


class QualityService:
    """Quality management service with SPC capabilities."""

    # SPC Constants (D2, D3, D4, A2 factors for different sample sizes)
    SPC_CONSTANTS = {
        2: {"D2": 1.128, "D3": 0, "D4": 3.267, "A2": 1.880},
        3: {"D2": 1.693, "D3": 0, "D4": 2.574, "A2": 1.023},
        4: {"D2": 2.059, "D3": 0, "D4": 2.282, "A2": 0.729},
        5: {"D2": 2.326, "D3": 0, "D4": 2.114, "A2": 0.577},
        6: {"D2": 2.534, "D3": 0, "D4": 2.004, "A2": 0.483},
        7: {"D2": 2.704, "D3": 0.076, "D4": 1.924, "A2": 0.419},
        8: {"D2": 2.847, "D3": 0.136, "D4": 1.864, "A2": 0.373},
        9: {"D2": 2.970, "D3": 0.184, "D4": 1.816, "A2": 0.337},
        10: {"D2": 3.078, "D3": 0.223, "D4": 1.777, "A2": 0.308},
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_spc_limits(
        self, inspection_plan_id: int, recalculate: bool = False
    ) -> Optional[SPCChart]:
        """Calculate SPC control limits for an inspection plan.

        Args:
            inspection_plan_id: ID of the inspection plan
            recalculate: Whether to recalculate existing limits

        Returns:
            SPCChart with calculated control limits
        """
        # Get inspection plan
        result = await self.db.execute(
            select(InspectionPlan).where(InspectionPlan.id == inspection_plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            return None

        # Check if SPC chart already exists
        existing_chart_result = await self.db.execute(
            select(SPCChart).where(
                and_(SPCChart.inspection_plan_id == inspection_plan_id, SPCChart.is_active)
            )
        )
        existing_chart = existing_chart_result.scalar_one_or_none()

        if existing_chart and not recalculate:
            return existing_chart

        # Get recent inspection results for calculation
        results_query = (
            select(InspectionResult)
            .where(InspectionResult.inspection_plan_id == inspection_plan_id)
            .order_by(desc(InspectionResult.measured_at))
            .limit(100)
        )  # Use last 100 samples

        results_result = await self.db.execute(results_query)
        results = results_result.scalars().all()

        sample_size = 5  # Default subgroup size
        if len(results) < sample_size * 5:  # Need at least 5 subgroups
            return None

        # Group results into subgroups
        subgroups = self._group_into_subgroups(results, sample_size)

        if len(subgroups) < 5:
            return None

        # Calculate control limits based on chart type
        if plan.spc_control_type == SPCControlType.X_BAR_R:
            limits = self._calculate_xbar_r_limits(subgroups, sample_size)
        elif plan.spc_control_type == SPCControlType.X_BAR_S:
            limits = self._calculate_xbar_s_limits(subgroups, sample_size)
        else:
            # For P-chart and C-chart implementation
            return None

        # Create or update SPC chart
        if existing_chart:
            # Update existing chart
            existing_chart.center_line = limits["center_line"]
            existing_chart.upper_control_limit = limits["ucl"]
            existing_chart.lower_control_limit = limits["lcl"]
            existing_chart.range_center_line = limits.get("range_center_line")
            existing_chart.range_upper_control_limit = limits.get("range_ucl")
            existing_chart.range_lower_control_limit = limits.get("range_lcl")
            existing_chart.sample_count = len(subgroups)
            existing_chart.last_calculation_date = datetime.now(timezone.utc)
            existing_chart.revision += 1
            chart = existing_chart
        else:
            # Create new chart
            chart = SPCChart(
                inspection_plan_id=inspection_plan_id,
                center_line=limits["center_line"],
                upper_control_limit=limits["ucl"],
                lower_control_limit=limits["lcl"],
                range_center_line=limits.get("range_center_line"),
                range_upper_control_limit=limits.get("range_ucl"),
                range_lower_control_limit=limits.get("range_lcl"),
                chart_type=plan.spc_control_type,
                sample_count=len(subgroups),
                last_calculation_date=datetime.now(timezone.utc),
            )
            self.db.add(chart)

        await self.db.commit()
        await self.db.refresh(chart)
        return chart

    def _group_into_subgroups(
        self, results: List[InspectionResult], sample_size: int
    ) -> List[List[float]]:
        """Group inspection results into subgroups for SPC analysis."""
        subgroups = []
        current_group = []

        # Sort by measured time — normalize to UTC so naive and tz-aware datetimes
        # compare correctly (SQLite returns naive datetimes even with timezone=True columns)
        def _to_utc(dt: datetime) -> datetime:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        sorted_results = sorted(results, key=lambda r: _to_utc(r.measured_at))

        for result in sorted_results:
            current_group.append(result.measured_value)

            if len(current_group) == sample_size:
                subgroups.append(current_group.copy())
                current_group = []

        return subgroups

    def _calculate_xbar_r_limits(
        self, subgroups: List[List[float]], sample_size: int
    ) -> Dict[str, float]:
        """Calculate X-bar R chart control limits."""
        if sample_size not in self.SPC_CONSTANTS:
            raise ValueError(f"Unsupported sample size: {sample_size}")

        constants = self.SPC_CONSTANTS[sample_size]

        # Calculate X-bar (mean of subgroup means)
        subgroup_means = [statistics.mean(group) for group in subgroups]
        grand_mean = statistics.mean(subgroup_means)

        # Calculate R-bar (mean of subgroup ranges)
        subgroup_ranges = [max(group) - min(group) for group in subgroups]
        mean_range = statistics.mean(subgroup_ranges)

        # X-bar chart limits
        ucl_xbar = grand_mean + constants["A2"] * mean_range
        lcl_xbar = grand_mean - constants["A2"] * mean_range

        # R chart limits
        ucl_r = constants["D4"] * mean_range
        lcl_r = constants["D3"] * mean_range

        return {
            "center_line": grand_mean,
            "ucl": ucl_xbar,
            "lcl": lcl_xbar,
            "range_center_line": mean_range,
            "range_ucl": ucl_r,
            "range_lcl": lcl_r,
        }

    def _calculate_xbar_s_limits(
        self, subgroups: List[List[float]], sample_size: int
    ) -> Dict[str, float]:
        """Calculate X-bar S chart control limits."""
        # Calculate subgroup means and standard deviations
        subgroup_means = [statistics.mean(group) for group in subgroups]
        subgroup_stds = [statistics.stdev(group) for group in subgroups]

        grand_mean = statistics.mean(subgroup_means)
        mean_std = statistics.mean(subgroup_stds)

        # ISO 7870 table values for X-bar S chart constants (A3, B3, B4)
        # These are exact tabulated values, not approximations.
        # Source: ISO 7870-2:2013, Table B.2
        XBAR_S_CONSTANTS = {
            2:  {"A3": 2.659, "B3": 0,     "B4": 3.267},
            3:  {"A3": 1.954, "B3": 0,     "B4": 2.568},
            4:  {"A3": 1.628, "B3": 0,     "B4": 2.266},
            5:  {"A3": 1.427, "B3": 0,     "B4": 2.089},
            6:  {"A3": 1.287, "B3": 0.030, "B4": 1.970},
            7:  {"A3": 1.182, "B3": 0.118, "B4": 1.882},
            8:  {"A3": 1.099, "B3": 0.185, "B4": 1.815},
            9:  {"A3": 1.032, "B3": 0.239, "B4": 1.761},
            10: {"A3": 0.975, "B3": 0.284, "B4": 1.716},
        }
        if sample_size not in XBAR_S_CONSTANTS:
            raise ValueError(f"Unsupported sample size for X-bar S chart: {sample_size}")
        s_consts = XBAR_S_CONSTANTS[sample_size]
        A3 = s_consts["A3"]
        B3 = s_consts["B3"]
        B4 = s_consts["B4"]

        return {
            "center_line": grand_mean,
            "ucl": grand_mean + A3 * mean_std,
            "lcl": grand_mean - A3 * mean_std,
            "range_center_line": mean_std,
            "range_ucl": B4 * mean_std,
            "range_lcl": B3 * mean_std,
        }

    async def calculate_capability_indices(
        self, inspection_plan_id: int
    ) -> Optional[SPCCapabilityAnalysis]:
        """Calculate Cp, Cpk, Pp, Ppk capability indices."""
        # Get inspection plan
        result = await self.db.execute(
            select(InspectionPlan).where(InspectionPlan.id == inspection_plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan or plan.lsl is None or plan.usl is None:
            return None

        # Get recent measurements
        results_query = (
            select(InspectionResult)
            .where(InspectionResult.inspection_plan_id == inspection_plan_id)
            .order_by(desc(InspectionResult.measured_at))
            .limit(100)
        )

        results_result = await self.db.execute(results_query)
        results = results_result.scalars().all()

        if len(results) < 30:  # Need sufficient data for capability analysis
            return None

        values = [r.measured_value for r in results]
        mean_value = statistics.mean(values)
        # overall_std_dev (Pp/Ppk): overall/long-term stdev of all data
        overall_std_dev = statistics.stdev(values)

        usl = plan.usl
        lsl = plan.lsl
        target = plan.nominal or (usl + lsl) / 2

        # Within-subgroup stdev for Cp/Cpk: estimated from subgroup ranges using D2 constant
        # This represents short-term process variation (common cause only).
        sample_size = 5  # default subgroup size (must match calculate_spc_limits)
        subgroups = self._group_into_subgroups(list(results), sample_size)
        if len(subgroups) >= 2 and sample_size in self.SPC_CONSTANTS:
            d2 = self.SPC_CONSTANTS[sample_size]["D2"]
            subgroup_ranges = [max(g) - min(g) for g in subgroups]
            mean_range = statistics.mean(subgroup_ranges)
            within_std_dev = mean_range / d2 if d2 > 0 else overall_std_dev
        else:
            within_std_dev = overall_std_dev

        # Cp/Cpk: short-term capability (within-subgroup stdev)
        cp = (usl - lsl) / (6 * within_std_dev) if within_std_dev > 0 else None
        cpu = (usl - mean_value) / (3 * within_std_dev) if within_std_dev > 0 else None
        cpl = (mean_value - lsl) / (3 * within_std_dev) if within_std_dev > 0 else None
        cpk = min(cpu, cpl) if cpu is not None and cpl is not None else None

        # Pp/Ppk: long-term performance (overall stdev)
        pp = (usl - lsl) / (6 * overall_std_dev) if overall_std_dev > 0 else None
        ppu = (usl - mean_value) / (3 * overall_std_dev) if overall_std_dev > 0 else None
        ppl = (mean_value - lsl) / (3 * overall_std_dev) if overall_std_dev > 0 else None
        ppk = min(ppu, ppl) if ppu is not None and ppl is not None else None

        return SPCCapabilityAnalysis(
            characteristic=plan.characteristic,
            sample_count=len(results),
            mean=mean_value,
            std_deviation=overall_std_dev,
            cp=cp,
            cpk=cpk,
            pp=pp,
            ppk=ppk,
            lsl=lsl,
            usl=usl,
            nominal=target,
            analysis_date=datetime.now(timezone.utc),
        )

    async def check_western_electric_rules(
        self, spc_chart_id: int, recent_points: int = 20
    ) -> List[SPCViolationRule]:
        """Check Western Electric Rules for SPC violations.

        Returns list of violated rules with details.
        """
        # Get SPC chart and data points
        chart_result = await self.db.execute(
            select(SPCChart)
            .options(selectinload(SPCChart.data_points))
            .where(SPCChart.id == spc_chart_id)
        )
        chart = chart_result.scalar_one_or_none()
        if not chart:
            return []

        # Get recent data points
        points_query = (
            select(SPCDataPoint)
            .where(SPCDataPoint.spc_chart_id == spc_chart_id)
            .order_by(desc(SPCDataPoint.subgroup_number))
            .limit(recent_points)
        )
        points_result = await self.db.execute(points_query)
        points = list(reversed(points_result.scalars().all()))  # Chronological order

        if len(points) < 9:  # Need at least 9 points for all rules
            return []

        violations = []

        # Rule 1: One point beyond 3-sigma limits
        violations.extend(self._check_rule_1(points, chart))

        # Rule 2: Nine points in a row on same side of center line
        violations.extend(self._check_rule_2(points, chart))

        # Rule 3: Six points in a row steadily increasing or decreasing
        violations.extend(self._check_rule_3(points, chart))

        # Rule 4: Fourteen points in a row alternating up and down
        violations.extend(self._check_rule_4(points, chart))

        # Rule 5: Two out of three consecutive points beyond 2-sigma
        violations.extend(self._check_rule_5(points, chart))

        # Rule 6: Four out of five consecutive points beyond 1-sigma
        violations.extend(self._check_rule_6(points, chart))

        # Rule 7: Fifteen points in a row within 1-sigma of center line
        violations.extend(self._check_rule_7(points, chart))

        # Rule 8: Eight points in a row beyond 1-sigma on both sides
        violations.extend(self._check_rule_8(points, chart))

        return violations

    def _check_rule_1(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 1: One point beyond 3-sigma (control limits)."""
        violations = []
        violated_points = []

        for i, point in enumerate(points):
            if (
                point.mean_value > chart.upper_control_limit
                or point.mean_value < chart.lower_control_limit
            ):
                violated_points.append(point.subgroup_number)

        if violated_points:
            violations.append(
                SPCViolationRule(
                    rule_number=1,
                    rule_description="One or more points beyond control limits (3-sigma)",
                    violated_points=violated_points,
                    severity="ALERT",
                )
            )

        return violations

    def _check_rule_2(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 2: Nine points in a row on same side of center line."""
        violations = []

        if len(points) < 9:
            return violations

        for i in range(len(points) - 8):
            window = points[i : i + 9]
            all_above = all(p.mean_value > chart.center_line for p in window)
            all_below = all(p.mean_value < chart.center_line for p in window)

            if all_above or all_below:
                violations.append(
                    SPCViolationRule(
                        rule_number=2,
                        rule_description="Nine points in a row on same side of center line",
                        violated_points=[p.subgroup_number for p in window],
                        severity="WARNING",
                    )
                )
                break  # Only report first occurrence

        return violations

    def _check_rule_3(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 3: Six points in a row steadily increasing or decreasing."""
        violations = []

        if len(points) < 6:
            return violations

        for i in range(len(points) - 5):
            window = points[i : i + 6]
            values = [p.mean_value for p in window]

            increasing = all(values[j] < values[j + 1] for j in range(5))
            decreasing = all(values[j] > values[j + 1] for j in range(5))

            if increasing or decreasing:
                violations.append(
                    SPCViolationRule(
                        rule_number=3,
                        rule_description="Six points in a row steadily increasing or decreasing",
                        violated_points=[p.subgroup_number for p in window],
                        severity="WARNING",
                    )
                )
                break

        return violations

    def _check_rule_4(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 4: Fourteen points in a row alternating up and down."""
        violations = []

        if len(points) < 14:
            return violations

        for i in range(len(points) - 13):
            window = points[i : i + 14]
            values = [p.mean_value for p in window]

            alternating = True
            for j in range(12):
                if j % 2 == 0:  # Even index: should be increasing then decreasing
                    if not (values[j] < values[j + 1] and values[j + 1] > values[j + 2]):
                        alternating = False
                        break

            if alternating:
                violations.append(
                    SPCViolationRule(
                        rule_number=4,
                        rule_description="Fourteen points alternating up and down",
                        violated_points=[p.subgroup_number for p in window],
                        severity="WARNING",
                    )
                )
                break

        return violations

    def _check_rule_5(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 5: Two out of three consecutive points beyond 2-sigma."""
        violations = []

        if len(points) < 3:
            return violations

        sigma = (chart.upper_control_limit - chart.center_line) / 3
        upper_2sigma = chart.center_line + 2 * sigma
        lower_2sigma = chart.center_line - 2 * sigma

        for i in range(len(points) - 2):
            window = points[i : i + 3]
            beyond_2sigma = 0
            violated_points = []

            for point in window:
                if point.mean_value > upper_2sigma or point.mean_value < lower_2sigma:
                    beyond_2sigma += 1
                    violated_points.append(point.subgroup_number)

            if beyond_2sigma >= 2:
                violations.append(
                    SPCViolationRule(
                        rule_number=5,
                        rule_description="Two out of three consecutive points beyond 2-sigma",
                        violated_points=violated_points,
                        severity="WARNING",
                    )
                )
                break

        return violations

    def _check_rule_6(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 6: Four out of five consecutive points beyond 1-sigma."""
        violations = []

        if len(points) < 5:
            return violations

        sigma = (chart.upper_control_limit - chart.center_line) / 3
        upper_1sigma = chart.center_line + sigma
        lower_1sigma = chart.center_line - sigma

        for i in range(len(points) - 4):
            window = points[i : i + 5]
            beyond_1sigma = 0
            violated_points = []

            for point in window:
                if point.mean_value > upper_1sigma or point.mean_value < lower_1sigma:
                    beyond_1sigma += 1
                    violated_points.append(point.subgroup_number)

            if beyond_1sigma >= 4:
                violations.append(
                    SPCViolationRule(
                        rule_number=6,
                        rule_description="Four out of five consecutive points beyond 1-sigma",
                        violated_points=violated_points,
                        severity="WARNING",
                    )
                )
                break

        return violations

    def _check_rule_7(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 7: Fifteen points in a row within 1-sigma of center line."""
        violations = []

        if len(points) < 15:
            return violations

        sigma = (chart.upper_control_limit - chart.center_line) / 3
        upper_1sigma = chart.center_line + sigma
        lower_1sigma = chart.center_line - sigma

        for i in range(len(points) - 14):
            window = points[i : i + 15]
            all_within_1sigma = all(lower_1sigma <= p.mean_value <= upper_1sigma for p in window)

            if all_within_1sigma:
                violations.append(
                    SPCViolationRule(
                        rule_number=7,
                        rule_description="Fifteen points in a row within 1-sigma (lack of variation)",
                        violated_points=[p.subgroup_number for p in window],
                        severity="WARNING",
                    )
                )
                break

        return violations

    def _check_rule_8(self, points: List[SPCDataPoint], chart: SPCChart) -> List[SPCViolationRule]:
        """Rule 8: Eight points in a row beyond 1-sigma on both sides."""
        violations = []

        if len(points) < 8:
            return violations

        sigma = (chart.upper_control_limit - chart.center_line) / 3
        upper_1sigma = chart.center_line + sigma
        lower_1sigma = chart.center_line - sigma

        for i in range(len(points) - 7):
            window = points[i : i + 8]
            all_beyond_1sigma = all(
                p.mean_value > upper_1sigma or p.mean_value < lower_1sigma for p in window
            )

            if all_beyond_1sigma:
                violations.append(
                    SPCViolationRule(
                        rule_number=8,
                        rule_description="Eight points in a row beyond 1-sigma on both sides",
                        violated_points=[p.subgroup_number for p in window],
                        severity="WARNING",
                    )
                )
                break

        return violations

    async def auto_generate_ncr(
        self,
        violation_rules: List[SPCViolationRule],
        inspection_plan_id: int,
        work_order_id: Optional[int] = None,
    ) -> NonConformance:
        """Auto-generate NCR based on SPC violations."""
        # Get inspection plan for context
        result = await self.db.execute(
            select(InspectionPlan).where(InspectionPlan.id == inspection_plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"Inspection plan {inspection_plan_id} not found")

        # Generate NCR number
        ncr_no = f"NCR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

        # Build description
        rule_descriptions = [
            f"Rule {rule.rule_number}: {rule.rule_description}" for rule in violation_rules
        ]
        description = (
            f"Automatic NCR generated due to SPC rule violations.\n\n"
            f"Characteristic: {plan.characteristic}\n"
            f"Violations detected:\n" + "\n".join(f"- {desc}" for desc in rule_descriptions)
        )

        # Create NCR
        ncr = NonConformance(
            ncr_no=ncr_no,
            work_order_id=work_order_id,
            inspection_plan_id=inspection_plan_id,
            defect_type="Process Control",
            characteristic=plan.characteristic,
            description=f"SPC Rule Violations - {plan.characteristic}\n{description}",
            status=NCRStatus.OPEN,
            reported_by="SPC_SYSTEM",
            is_auto_generated=True,
            trigger_data={
                "violation_rules": [rule.model_dump() for rule in violation_rules],
                "inspection_plan_id": inspection_plan_id,
                "detection_time": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.db.add(ncr)
        await self.db.commit()
        await self.db.refresh(ncr)

        return ncr

    async def get_quality_traceability(
        self, serial_number: str
    ) -> Optional[QualityTraceabilityRecord]:
        """Get complete quality traceability for a serial number."""
        # Find inspection results for this serial number
        results_query = (
            select(InspectionResult)
            .options(
                selectinload(InspectionResult.inspection_plan),
                selectinload(InspectionResult.work_order).selectinload(WorkOrder.product),
            )
            .where(InspectionResult.serial_no == serial_number)
        )

        results_result = await self.db.execute(results_query)
        inspection_results = results_result.scalars().all()

        if not inspection_results:
            return None

        # Get work order info
        work_order = inspection_results[0].work_order

        # Find associated NCRs
        ncr_query = select(NonConformance).where(NonConformance.work_order_id == work_order.id)
        ncr_result = await self.db.execute(ncr_query)
        ncrs = ncr_result.scalars().all()

        # Calculate overall quality status
        conforming_results = [r for r in inspection_results if r.is_conforming]
        total_results = len(inspection_results)
        quality_score = (len(conforming_results) / total_results * 100) if total_results > 0 else 0

        # Determine overall status
        open_ncrs = [ncr for ncr in ncrs if ncr.status in [NCRStatus.OPEN, NCRStatus.IN_PROGRESS]]
        if open_ncrs:
            overall_status = "FAIL"
        elif quality_score < 95:
            overall_status = "CONDITIONAL"
        else:
            overall_status = "PASS"

        # Convert to schema objects
        from ..schemas.quality import InspectionResultResponse, NonConformanceResponse

        return QualityTraceabilityRecord(
            serial_no=serial_number,
            work_order_id=work_order.id,
            lot_number=work_order.lot_no,
            product_name=work_order.product.name if work_order.product else "Unknown",
            inspection_results=[
                InspectionResultResponse.model_validate(r) for r in inspection_results
            ],
            ncr_records=[NonConformanceResponse.model_validate(ncr) for ncr in ncrs],
            overall_status=overall_status,
            quality_score=quality_score,
            traced_at=datetime.now(timezone.utc),
        )
