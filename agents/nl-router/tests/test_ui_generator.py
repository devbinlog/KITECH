"""Tests for UI Schema Generator"""

import pytest
from src.ui_generator.schema_generator import (
    UISchemaGenerator,
    UISchema,
    UIComponent,
    Position,
)
from src.skills.skill_registry import OutputType


class TestUISchemaGenerator:
    """Tests for UISchemaGenerator"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return UISchemaGenerator()

    def test_generate_dashboard(self, generator):
        """Test dashboard generation"""
        data = {
            "daily_status": {
                "orders": {
                    "total": 15,
                    "completed": 8,
                    "by_status": {"DONE": 8, "RUNNING": 5, "READY": 2},
                },
                "kpis": {
                    "yield_rate": 98.5,
                },
                "results": {
                    "total_ok_qty": 1250,
                },
            }
        }

        schema = generator.generate(data, OutputType.DASHBOARD, "오늘 생산 현황")

        assert isinstance(schema, UISchema)
        assert schema.layout == "dashboard"
        assert len(schema.components) > 0

        # Check for KPI cards
        kpi_cards = [c for c in schema.components if c.type == "KPICard"]
        assert len(kpi_cards) >= 1

    def test_generate_kpi_dashboard(self, generator):
        """Test KPI dashboard generation"""
        data = {
            "kpis": {
                "today": {
                    "completion_rate": 85.0,
                    "yield_rate": 98.5,
                    "equipment_utilization": 72.3,
                }
            }
        }

        schema = generator.generate(data, OutputType.KPI_DASHBOARD, "KPI 조회")

        assert schema.layout == "dashboard"
        kpi_cards = [c for c in schema.components if c.type == "KPICard"]
        assert len(kpi_cards) >= 3

    def test_generate_status_grid(self, generator):
        """Test equipment status grid generation"""
        data = {
            "equipments": [
                {"id": 1, "eq_name": "CNC-001", "equipment_type": "CNC", "current_status": "RUN"},
                {"id": 2, "eq_name": "CNC-002", "equipment_type": "CNC", "current_status": "IDLE"},
            ]
        }

        schema = generator.generate(data, OutputType.STATUS_GRID, "설비 상태")

        assert schema.layout == "grid"
        status_cards = [c for c in schema.components if c.type == "StatusCards"]
        assert len(status_cards) == 1
        assert len(status_cards[0].props["items"]) == 2

    def test_generate_traceability(self, generator):
        """Test traceability timeline generation"""
        data = {
            "traceability": {
                "lot_no": "LOT-001",
                "summary": {
                    "total_ok_qty": 95,
                    "total_ng_qty": 5,
                    "yield_rate": 95.0,
                },
                "timeline": [
                    {
                        "id": 1,
                        "start_time": "2024-01-24T10:00:00",
                        "end_time": "2024-01-24T11:00:00",
                    },
                ],
                "work_order": {
                    "lot_no": "LOT-001",
                    "status": "DONE",
                    "target_qty": 100,
                },
            }
        }

        schema = generator.generate(data, OutputType.TRACEABILITY_TIMELINE, "LOT-001 이력")

        assert schema.layout == "detail"
        assert "LOT-001" in schema.title

        # Check for timeline component
        timeline = [c for c in schema.components if c.type == "TraceabilityTimeline"]
        assert len(timeline) == 1

    def test_generate_comparison_chart(self, generator):
        """Test comparison chart generation"""
        data = {
            "utilization": {
                "equipment_utilization": [
                    {"equipment_name": "CNC-001", "utilization_rate": 85.0, "yield_rate": 98.0},
                    {"equipment_name": "CNC-002", "utilization_rate": 72.0, "yield_rate": 96.0},
                ],
                "summary": {
                    "total_equipment": 2,
                    "average_utilization": 78.5,
                    "top_performer": "CNC-001",
                    "bottleneck": "CNC-002",
                },
            }
        }

        schema = generator.generate(data, OutputType.COMPARISON_CHART, "설비별 비교")

        assert schema.layout == "dashboard"
        bar_charts = [c for c in schema.components if c.type == "BarChart"]
        assert len(bar_charts) >= 1

    def test_generate_chart(self, generator):
        """Test trend chart generation"""
        data = {
            "trends": {
                "metric": "yield",
                "data": [
                    {"date": "2024-01-20", "value": 95.0},
                    {"date": "2024-01-21", "value": 96.0},
                    {"date": "2024-01-22", "value": 97.0},
                ],
            }
        }

        schema = generator.generate(data, OutputType.CHART, "수율 추이")

        assert schema.layout == "single"
        line_charts = [c for c in schema.components if c.type == "LineChart"]
        assert len(line_charts) == 1

    def test_generate_list(self, generator):
        """Test list/table generation"""
        data = {
            "products": [
                {"code": "PROD-001", "name": "제품1"},
                {"code": "PROD-002", "name": "제품2"},
            ]
        }

        schema = generator.generate(data, OutputType.LIST, "제품 목록")

        assert schema.layout == "single"
        tables = [c for c in schema.components if c.type == "DataTable"]
        assert len(tables) == 1
        assert tables[0].props["data"] == data["products"]

    def test_generate_help(self, generator):
        """Test help output generation"""
        schema = generator.generate({}, OutputType.HELP, "")

        assert schema.layout == "single"
        help_cards = [c for c in schema.components if c.type == "HelpCard"]
        assert len(help_cards) == 1
        assert "examples" in help_cards[0].props

    def test_generate_empty_data(self, generator):
        """Test generation with empty data"""
        schema = generator.generate({}, OutputType.DASHBOARD, "빈 데이터")

        assert isinstance(schema, UISchema)
        # Should still have valid schema structure
        assert schema.layout == "dashboard"


class TestUISchema:
    """Tests for UISchema model"""

    def test_schema_creation(self):
        """Test UISchema creation"""
        schema = UISchema(
            layout="dashboard",
            title="Test Dashboard",
            components=[
                UIComponent(
                    type="KPICard",
                    props={"title": "Test", "value": 100},
                )
            ],
        )

        assert schema.layout == "dashboard"
        assert schema.title == "Test Dashboard"
        assert len(schema.components) == 1

    def test_schema_defaults(self):
        """Test UISchema defaults"""
        schema = UISchema()

        assert schema.layout == "dashboard"
        assert schema.title == ""
        assert schema.components == []
        assert schema.summary_text is None


class TestUIComponent:
    """Tests for UIComponent model"""

    def test_component_creation(self):
        """Test UIComponent creation"""
        component = UIComponent(
            type="KPICard",
            props={"title": "수율", "value": "98.5%"},
            position=Position(row=0, col=0, width=1, height=1),
        )

        assert component.type == "KPICard"
        assert component.props["title"] == "수율"
        assert component.position.row == 0

    def test_component_without_position(self):
        """Test UIComponent without position"""
        component = UIComponent(
            type="DataTable",
            props={"data": []},
        )

        assert component.position is None


class TestPosition:
    """Tests for Position model"""

    def test_position_defaults(self):
        """Test Position defaults"""
        pos = Position()

        assert pos.row == 0
        assert pos.col == 0
        assert pos.width == 1
        assert pos.height == 1

    def test_position_custom(self):
        """Test Position with custom values"""
        pos = Position(row=1, col=2, width=2, height=2)

        assert pos.row == 1
        assert pos.col == 2
        assert pos.width == 2
        assert pos.height == 2
