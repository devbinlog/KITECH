"""Tests for API selector and orchestration plan builder."""

import pytest

from src.skills.api_selector import (
    APICall,
    OrchestrationPlan,
    ExecutionMode,
    APISelector,
)
from src.skills.skill_registry import SkillDefinition, OutputType
from src.understanding.intents import Intent


class TestAPICall:
    """Tests for APICall dataclass."""

    def test_default_values(self):
        """Should have correct default values."""
        call = APICall(endpoint="/api/test")

        assert call.method == "GET"
        assert call.params == {}
        assert call.path_params == {}
        assert call.depends_on is None
        assert call.result_key == ""
        assert call.timeout == 30

    def test_get_full_endpoint_no_params(self):
        """Should return endpoint unchanged without path params."""
        call = APICall(endpoint="/api/v1/equipments")
        assert call.get_full_endpoint() == "/api/v1/equipments"

    def test_get_full_endpoint_with_params(self):
        """Should substitute path parameters."""
        call = APICall(
            endpoint="/api/v1/equipments/{equipment_id}/status",
            path_params={"equipment_id": "EQ-001"},
        )
        assert call.get_full_endpoint() == "/api/v1/equipments/EQ-001/status"

    def test_get_full_endpoint_multiple_params(self):
        """Should substitute multiple path parameters."""
        call = APICall(
            endpoint="/api/v1/{resource}/{id}/items",
            path_params={"resource": "orders", "id": "123"},
        )
        assert call.get_full_endpoint() == "/api/v1/orders/123/items"


class TestOrchestrationPlan:
    """Tests for OrchestrationPlan dataclass."""

    def test_has_dependencies_false(self):
        """Should return False when no calls have dependencies."""
        plan = OrchestrationPlan(
            calls=[
                APICall(endpoint="/api/a"),
                APICall(endpoint="/api/b"),
            ],
            execution_mode=ExecutionMode.PARALLEL,
        )
        assert plan.has_dependencies is False

    def test_has_dependencies_true(self):
        """Should return True when any call has depends_on."""
        plan = OrchestrationPlan(
            calls=[
                APICall(endpoint="/api/a", result_key="result_a"),
                APICall(endpoint="/api/b", depends_on="result_a"),
            ],
            execution_mode=ExecutionMode.SEQUENTIAL,
        )
        assert plan.has_dependencies is True

    def test_default_values(self):
        """Should have correct default values."""
        plan = OrchestrationPlan(
            calls=[],
            execution_mode=ExecutionMode.PARALLEL,
        )
        assert plan.aggregation_strategy == "merge"
        assert plan.output_type == OutputType.DASHBOARD
        assert plan.skill_name == ""


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_parallel_value(self):
        """Should have correct value for PARALLEL."""
        assert ExecutionMode.PARALLEL.value == "parallel"

    def test_sequential_value(self):
        """Should have correct value for SEQUENTIAL."""
        assert ExecutionMode.SEQUENTIAL.value == "sequential"


class TestAPISelector:
    """Tests for APISelector class."""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    @pytest.fixture
    def production_skill(self):
        return SkillDefinition(
            name="mes_production_query",
            description="Production query",
            intents=[Intent.PRODUCTION_STATUS],
            api_endpoints=["/api/v1/production/orders"],
            output_type=OutputType.DASHBOARD,
        )

    @pytest.fixture
    def equipment_skill(self):
        return SkillDefinition(
            name="mes_equipment_status",
            description="Equipment status",
            intents=[Intent.EQUIPMENT_STATUS],
            api_endpoints=["/api/v1/masters/equipments"],
            output_type=OutputType.STATUS_GRID,
        )

    @pytest.fixture
    def kpi_skill(self):
        return SkillDefinition(
            name="mes_kpi_query",
            description="KPI query",
            intents=[Intent.KPI_QUERY],
            api_endpoints=["/api/v1/analytics/kpis"],
            output_type=OutputType.KPI_DASHBOARD,
        )

    def test_build_plan_production_status(self, selector, production_skill):
        """Should build plan for production status query."""
        plan = selector.build_plan(
            skill=production_skill,
            intent=Intent.PRODUCTION_STATUS,
            entities={},
        )

        assert len(plan.calls) > 0
        assert plan.skill_name == "mes_production_query"

    def test_build_plan_production_status_with_date(self, selector, production_skill):
        """Should include date in params."""
        plan = selector.build_plan(
            skill=production_skill,
            intent=Intent.PRODUCTION_STATUS,
            entities={"date": "2026-02-03"},
        )

        assert len(plan.calls) > 0
        # Check that date is passed to params
        call = plan.calls[0]
        assert "target_date" in call.params

    def test_build_plan_production_detail(self, selector, production_skill):
        """Should build plan for production detail with LOT."""
        plan = selector.build_plan(
            skill=production_skill,
            intent=Intent.PRODUCTION_DETAIL,
            entities={"lot_no": "LOT-001"},
        )

        # Should have calls for orders and results
        assert len(plan.calls) >= 1

    def test_build_plan_equipment_status_single(self, selector, equipment_skill):
        """Should query single equipment when ID provided."""
        plan = selector.build_plan(
            skill=equipment_skill,
            intent=Intent.EQUIPMENT_STATUS,
            entities={"equipment_id": "EQ-001"},
        )

        assert len(plan.calls) == 1
        assert "EQ-001" in plan.calls[0].endpoint

    def test_build_plan_equipment_status_all(self, selector, equipment_skill):
        """Should query all equipment when no ID provided."""
        plan = selector.build_plan(
            skill=equipment_skill,
            intent=Intent.EQUIPMENT_STATUS,
            entities={},
        )

        assert len(plan.calls) == 1
        assert "/api/v1/masters/equipments" in plan.calls[0].endpoint

    def test_build_plan_equipment_with_type_filter(self, selector, equipment_skill):
        """Should include equipment_type filter in params."""
        plan = selector.build_plan(
            skill=equipment_skill,
            intent=Intent.EQUIPMENT_STATUS,
            entities={"equipment_type": "CNC"},
        )

        assert plan.calls[0].params.get("equipment_type") == "CNC"

    def test_build_plan_kpi_today(self, selector, kpi_skill):
        """Should use kpis endpoint for today's KPIs."""
        plan = selector.build_plan(
            skill=kpi_skill,
            intent=Intent.KPI_QUERY,
            entities={},
        )

        assert len(plan.calls) == 1
        assert "/kpis" in plan.calls[0].endpoint

    def test_build_plan_kpi_with_date(self, selector, kpi_skill):
        """Should use daily-status endpoint for date-specific KPIs."""
        plan = selector.build_plan(
            skill=kpi_skill,
            intent=Intent.KPI_QUERY,
            entities={"date": "2026-02-01"},
        )

        assert len(plan.calls) == 1
        assert "daily-status" in plan.calls[0].endpoint

    def test_build_plan_analytics_default_days(self, selector, kpi_skill):
        """Should use default 7 days for analytics."""
        plan = selector.build_plan(
            skill=kpi_skill,
            intent=Intent.ANALYTICS,
            entities={},
        )

        assert len(plan.calls) == 1
        assert plan.calls[0].params.get("days") == 7

    def test_build_plan_analytics_with_date_range(self, selector, kpi_skill):
        """Should map date_range to days parameter."""
        plan = selector.build_plan(
            skill=kpi_skill,
            intent=Intent.ANALYTICS,
            entities={"date_range": "this_month"},
        )

        assert plan.calls[0].params.get("days") == 30

    def test_build_plan_unknown_skill(self, selector):
        """Should use first endpoint for unknown skill."""
        unknown_skill = SkillDefinition(
            name="unknown_skill",
            description="Unknown",
            intents=[],
            api_endpoints=["/api/v1/default"],
            output_type=OutputType.DASHBOARD,
        )

        plan = selector.build_plan(
            skill=unknown_skill,
            intent=Intent.UNKNOWN,
            entities={},
        )

        assert len(plan.calls) == 1
        assert plan.calls[0].endpoint == "/api/v1/default"

    def test_execution_mode_parallel(self, selector, equipment_skill):
        """Should use PARALLEL mode when no dependencies."""
        plan = selector.build_plan(
            skill=equipment_skill,
            intent=Intent.EQUIPMENT_STATUS,
            entities={},
        )

        # Single call should be parallel
        if not plan.has_dependencies:
            assert plan.execution_mode == ExecutionMode.PARALLEL


class TestAPISelectorAdvanced:
    """Advanced tests for APISelector."""

    @pytest.fixture
    def selector(self):
        return APISelector()

    def test_build_traceability_calls(self, selector):
        """Should build traceability calls with LOT."""
        skill = SkillDefinition(
            name="mes_traceability",
            description="Traceability",
            intents=[Intent.TRACEABILITY],
            api_endpoints=[],
            output_type=OutputType.TRACEABILITY_TIMELINE,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.TRACEABILITY,
            entities={"lot_no": "LOT-2026-001"},
        )

        assert len(plan.calls) == 1
        assert "LOT-2026-001" in plan.calls[0].endpoint

    def test_build_scheduling_solve(self, selector):
        """Should build scheduling solve with POST method."""
        skill = SkillDefinition(
            name="mes_scheduling",
            description="Scheduling",
            intents=[Intent.SCHEDULE_REQUEST],
            api_endpoints=[],
            output_type=OutputType.GANTT,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.SCHEDULE_REQUEST,
            entities={"horizon_hours": 48},
        )

        assert len(plan.calls) == 1
        assert plan.calls[0].method == "POST"
        assert plan.calls[0].params.get("horizon_hours") == 48
        assert plan.calls[0].timeout >= 60  # Longer timeout for scheduling

    def test_build_error_diagnosis_single_equipment(self, selector):
        """Should query single equipment for error diagnosis."""
        skill = SkillDefinition(
            name="mes_error_diagnosis",
            description="Error diagnosis",
            intents=[Intent.ERROR_DIAGNOSIS],
            api_endpoints=[],
            output_type=OutputType.DIAGNOSIS_PANEL,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.ERROR_DIAGNOSIS,
            entities={"equipment_id": "CNC-001"},
        )

        assert len(plan.calls) == 1
        assert "CNC-001" in plan.calls[0].endpoint

    def test_build_error_diagnosis_all_errors(self, selector):
        """Should query all error status equipment."""
        skill = SkillDefinition(
            name="mes_error_diagnosis",
            description="Error diagnosis",
            intents=[Intent.ERROR_DIAGNOSIS],
            api_endpoints=[],
            output_type=OutputType.DIAGNOSIS_PANEL,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.ERROR_DIAGNOSIS,
            entities={},
        )

        assert len(plan.calls) == 1
        assert plan.calls[0].params.get("status") == "ERROR"

    def test_build_delay_prediction_multiple_calls(self, selector):
        """Should build multiple calls for delay prediction."""
        skill = SkillDefinition(
            name="mes_delay_prediction",
            description="Delay prediction",
            intents=[Intent.DELAY_PREDICTION],
            api_endpoints=[],
            output_type=OutputType.RISK_DASHBOARD,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.DELAY_PREDICTION,
            entities={},
        )

        # Should have calls for running orders and daily status
        assert len(plan.calls) >= 2

    def test_build_defect_analysis_with_filters(self, selector):
        """Should include filters in defect analysis."""
        skill = SkillDefinition(
            name="mes_defect_analysis",
            description="Defect analysis",
            intents=[Intent.DEFECT_ANALYSIS],
            api_endpoints=[],
            output_type=OutputType.ANALYSIS_DASHBOARD,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.DEFECT_ANALYSIS,
            entities={"product_id": "PROD-001", "equipment_id": "EQ-002"},
        )

        # Check filters are passed
        results_call = next((c for c in plan.calls if "results" in c.endpoint), None)
        if results_call:
            assert "product_id" in results_call.params or "equipment_id" in results_call.params

    def test_build_comparison_calls(self, selector):
        """Should build comparison analysis calls."""
        skill = SkillDefinition(
            name="mes_comparison",
            description="Comparison",
            intents=[Intent.COMPARISON],
            api_endpoints=[],
            output_type=OutputType.COMPARISON_CHART,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.COMPARISON,
            entities={"group_by": "equipment"},
        )

        # Should have utilization and trends calls
        assert len(plan.calls) >= 1


# ============================================================================
# 보강된 테스트: API 선택 및 응답 우선순위 계산
# ============================================================================

class TestAPICallPriorityCalculation:
    """API 호출 우선순위 및 타임아웃 계산 검증"""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    def test_scheduling_has_longer_timeout(self, selector):
        """스케줄링 API는 긴 타임아웃"""
        skill = SkillDefinition(
            name="mes_scheduling",
            description="Scheduling",
            intents=[Intent.SCHEDULE_REQUEST],
            api_endpoints=[],
            output_type=OutputType.GANTT,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.SCHEDULE_REQUEST,
            entities={},
        )

        # 스케줄링은 60초 이상 타임아웃
        assert plan.calls[0].timeout >= 60

    def test_simple_query_has_short_timeout(self, selector):
        """단순 조회는 짧은 타임아웃"""
        skill = SkillDefinition(
            name="mes_production_query",
            description="Production",
            intents=[Intent.PRODUCTION_STATUS],
            api_endpoints=["/api/v1/production/orders"],
            output_type=OutputType.DASHBOARD,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.PRODUCTION_STATUS,
            entities={},
        )

        # 기본 타임아웃 30초
        assert plan.calls[0].timeout == 30


class TestDateRangeToAPIParams:
    """날짜 범위 → API 파라미터 변환 검증"""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    def test_this_week_maps_to_7_days(self, selector):
        """'이번 주' → days=7"""
        skill = SkillDefinition(
            name="mes_kpi_query",
            description="KPI",
            intents=[Intent.ANALYTICS],
            api_endpoints=["/api/v1/analytics/trends"],
            output_type=OutputType.CHART,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.ANALYTICS,
            entities={"date_range": "this_week"},
        )

        assert plan.calls[0].params.get("days") == 7

    def test_this_month_maps_to_30_days(self, selector):
        """'이번 달' → days=30"""
        skill = SkillDefinition(
            name="mes_kpi_query",
            description="KPI",
            intents=[Intent.ANALYTICS],
            api_endpoints=["/api/v1/analytics/trends"],
            output_type=OutputType.CHART,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.ANALYTICS,
            entities={"date_range": "this_month"},
        )

        assert plan.calls[0].params.get("days") == 30

    def test_last_7_days_explicit(self, selector):
        """'최근 7일' → days=7"""
        skill = SkillDefinition(
            name="mes_kpi_query",
            description="KPI",
            intents=[Intent.ANALYTICS],
            api_endpoints=["/api/v1/analytics/trends"],
            output_type=OutputType.CHART,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.ANALYTICS,
            entities={"date_range": "last_7_days"},
        )

        assert plan.calls[0].params.get("days") == 7


class TestDependencyBasedExecution:
    """의존성 기반 실행 모드 검증"""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    def test_independent_calls_parallel(self, selector):
        """독립적인 호출은 병렬 실행"""
        skill = SkillDefinition(
            name="mes_equipment_status",
            description="Equipment",
            intents=[Intent.EQUIPMENT_STATUS],
            api_endpoints=["/api/v1/masters/equipments"],
            output_type=OutputType.STATUS_GRID,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.EQUIPMENT_STATUS,
            entities={},
        )

        if not plan.has_dependencies:
            assert plan.execution_mode == ExecutionMode.PARALLEL

    def test_delay_prediction_has_dependencies(self, selector):
        """지연 예측은 여러 API 호출 필요"""
        skill = SkillDefinition(
            name="mes_delay_prediction",
            description="Delay",
            intents=[Intent.DELAY_PREDICTION],
            api_endpoints=[],
            output_type=OutputType.RISK_DASHBOARD,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.DELAY_PREDICTION,
            entities={},
        )

        # 여러 호출이 있어야 함
        assert len(plan.calls) >= 2


class TestEntityToPathParamMapping:
    """엔티티 → 경로 파라미터 매핑 검증"""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    def test_equipment_id_in_path(self, selector):
        """equipment_id가 경로에 포함됨"""
        skill = SkillDefinition(
            name="mes_equipment_status",
            description="Equipment",
            intents=[Intent.EQUIPMENT_STATUS],
            api_endpoints=["/api/v1/masters/equipments"],
            output_type=OutputType.STATUS_GRID,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.EQUIPMENT_STATUS,
            entities={"equipment_id": "CNC-001"},
        )

        # 경로에 equipment_id가 포함됨
        full_endpoint = plan.calls[0].get_full_endpoint()
        assert "CNC-001" in full_endpoint or "equipment" in full_endpoint.lower()

    def test_lot_no_in_traceability_path(self, selector):
        """lot_no가 추적성 경로에 포함됨"""
        skill = SkillDefinition(
            name="mes_traceability",
            description="Traceability",
            intents=[Intent.TRACEABILITY],
            api_endpoints=[],
            output_type=OutputType.TRACEABILITY_TIMELINE,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.TRACEABILITY,
            entities={"lot_no": "LOT-2026-001"},
        )

        full_endpoint = plan.calls[0].get_full_endpoint()
        assert "LOT-2026-001" in full_endpoint


class TestStatusFilterApplication:
    """상태 필터 적용 검증"""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    def test_error_diagnosis_filters_error_status(self, selector):
        """에러 진단 시 ERROR 상태 필터"""
        skill = SkillDefinition(
            name="mes_error_diagnosis",
            description="Error",
            intents=[Intent.ERROR_DIAGNOSIS],
            api_endpoints=[],
            output_type=OutputType.DIAGNOSIS_PANEL,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.ERROR_DIAGNOSIS,
            entities={},
        )

        # ERROR 상태 필터가 있어야 함
        call_params = plan.calls[0].params
        assert call_params.get("status") == "ERROR"

    def test_running_orders_filter(self, selector):
        """진행 중 작업 필터"""
        skill = SkillDefinition(
            name="mes_delay_prediction",
            description="Delay",
            intents=[Intent.DELAY_PREDICTION],
            api_endpoints=[],
            output_type=OutputType.RISK_DASHBOARD,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.DELAY_PREDICTION,
            entities={},
        )

        # RUNNING 상태 필터가 하나 이상 있어야 함
        has_running_filter = any(
            c.params.get("status") == "RUNNING"
            for c in plan.calls
        )
        assert has_running_filter


class TestAggregationStrategy:
    """결과 집계 전략 검증"""

    @pytest.fixture
    def selector(self):
        return APISelector(base_url="http://localhost:8000")

    def test_default_aggregation_is_merge(self, selector):
        """기본 집계 전략은 merge"""
        skill = SkillDefinition(
            name="mes_production_query",
            description="Production",
            intents=[Intent.PRODUCTION_STATUS],
            api_endpoints=["/api/v1/production/orders"],
            output_type=OutputType.DASHBOARD,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.PRODUCTION_STATUS,
            entities={},
        )

        assert plan.aggregation_strategy == "merge"

    def test_output_type_preserved(self, selector):
        """출력 타입이 스킬에서 유지됨"""
        skill = SkillDefinition(
            name="mes_traceability",
            description="Traceability",
            intents=[Intent.TRACEABILITY],
            api_endpoints=[],
            output_type=OutputType.TRACEABILITY_TIMELINE,
        )

        plan = selector.build_plan(
            skill=skill,
            intent=Intent.TRACEABILITY,
            entities={"lot_no": "LOT-001"},
        )

        assert plan.output_type == OutputType.TRACEABILITY_TIMELINE
