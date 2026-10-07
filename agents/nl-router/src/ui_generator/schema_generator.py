"""UI Schema Generator for dynamic dashboard rendering"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..skills.skill_registry import OutputType

logger = logging.getLogger(__name__)


class Position(BaseModel):
    """Component position in grid layout"""

    row: int = 0
    col: int = 0
    width: int = 1
    height: int = 1


class UIComponent(BaseModel):
    """Single UI component definition"""

    type: str = Field(..., description="Component type (KPICard, DataTable, etc.)")
    props: Dict[str, Any] = Field(default_factory=dict, description="Component properties")
    position: Optional[Position] = None


class UISchema(BaseModel):
    """Complete UI schema for rendering"""

    layout: str = Field(default="dashboard", description="Layout type")
    title: str = Field(default="", description="Dashboard title")
    components: List[UIComponent] = Field(default_factory=list)
    summary_text: Optional[str] = Field(None, description="Natural language summary")


class UISchemaGenerator:
    """Generate UI schemas from query results"""

    def __init__(self):
        self._generators = {
            OutputType.DASHBOARD: self._generate_dashboard,
            OutputType.DETAIL: self._generate_detail,
            OutputType.LIST: self._generate_list,
            OutputType.STATUS_GRID: self._generate_status_grid,
            OutputType.GANTT: self._generate_gantt,
            OutputType.KPI_DASHBOARD: self._generate_kpi_dashboard,
            OutputType.CHART: self._generate_chart,
            OutputType.COMPARISON_CHART: self._generate_comparison_chart,
            OutputType.TRACEABILITY_TIMELINE: self._generate_traceability,
            OutputType.HELP: self._generate_help,
        }

    def generate(
        self,
        data: Dict[str, Any],
        output_type: OutputType,
        query: str = "",
    ) -> UISchema:
        """
        Generate UI schema from data

        Args:
            data: Query result data
            output_type: Desired output type
            query: Original user query

        Returns:
            UISchema for frontend rendering
        """
        generator = self._generators.get(output_type, self._generate_dashboard)
        return generator(data, query)

    def _generate_dashboard(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate production dashboard schema"""
        components = []

        # KPI Cards for daily status
        if "daily_status" in data:
            ds = data["daily_status"]
            kpis = ds.get("kpis", {})
            orders = ds.get("orders", {})
            results = ds.get("results", {})

            # Order summary cards
            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "총 작업지시",
                        "value": orders.get("total", 0),
                        "icon": "clipboard-list",
                    },
                    position=Position(row=0, col=0, width=1, height=1),
                )
            )

            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "완료",
                        "value": orders.get("completed", 0),
                        "icon": "check-circle",
                        "color": "green",
                    },
                    position=Position(row=0, col=1, width=1, height=1),
                )
            )

            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "수율",
                        "value": f"{kpis.get('yield_rate', 0):.1f}%",
                        "icon": "chart-line",
                    },
                    position=Position(row=0, col=2, width=1, height=1),
                )
            )

            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "양품 수량",
                        "value": f"{results.get('total_ok_qty', 0):,}",
                        "icon": "box",
                    },
                    position=Position(row=0, col=3, width=1, height=1),
                )
            )

            # Status distribution pie chart
            by_status = orders.get("by_status", {})
            if by_status:
                components.append(
                    UIComponent(
                        type="PieChart",
                        props={
                            "title": "작업 상태 분포",
                            "data": [
                                {"name": status, "value": count}
                                for status, count in by_status.items()
                            ],
                        },
                        position=Position(row=1, col=0, width=2, height=2),
                    )
                )

        return UISchema(
            layout="dashboard",
            title=self._generate_title(query, "생산 현황"),
            components=components,
        )

    def _generate_kpi_dashboard(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate KPI dashboard schema"""
        components = []

        # Handle both /kpis and /daily-status response formats
        kpi_data = {}
        if "kpis" in data:
            kpis = data["kpis"]
            kpi_data = kpis.get("today", {})
        elif "daily_status" in data:
            # daily-status endpoint returns kpis in a different structure
            ds = data["daily_status"]
            kpi_data = ds.get("kpis", {})

        if kpi_data:
            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "완료율",
                        "value": f"{kpi_data.get('completion_rate', 0):.1f}%",
                        "icon": "check-circle",
                    },
                )
            )

            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "수율",
                        "value": f"{kpi_data.get('yield_rate', 0):.1f}%",
                        "icon": "chart-line",
                    },
                )
            )

            components.append(
                UIComponent(
                    type="KPICard",
                    props={
                        "title": "설비 가동률",
                        "value": f"{kpi_data.get('equipment_utilization', 0):.1f}%",
                        "icon": "cog",
                    },
                )
            )

        if "trends" in data:
            trend_data = data["trends"].get("data", [])
            if trend_data:
                components.append(
                    UIComponent(
                        type="LineChart",
                        props={
                            "title": f"{data['trends'].get('metric', '').title()} 추이",
                            "data": trend_data,
                            "xKey": "date",
                            "yKey": "value",
                        },
                    )
                )

        if "utilization" in data:
            util_data = data["utilization"].get("equipment_utilization", [])
            if util_data:
                components.append(
                    UIComponent(
                        type="BarChart",
                        props={
                            "title": "설비별 가동률",
                            "data": [
                                {
                                    "name": u["equipment_name"],
                                    "value": u["utilization_rate"],
                                }
                                for u in util_data
                            ],
                        },
                    )
                )

        return UISchema(
            layout="dashboard",
            title=self._generate_title(query, "KPI 대시보드"),
            components=components,
        )

    def _generate_status_grid(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate equipment status grid schema"""
        components = []

        equipments = data.get("equipments", data.get("equipment_status", []))
        if isinstance(equipments, dict):
            equipments = [equipments]

        status_cards = []
        for eq in equipments:
            status_cards.append(
                {
                    "id": eq.get("id"),
                    "name": eq.get("eq_name") or eq.get("name"),
                    "type": eq.get("equipment_type"),
                    "status": eq.get("current_status") or eq.get("status"),
                    "metrics": eq.get("last_data", {}),
                }
            )

        if status_cards:
            components.append(
                UIComponent(
                    type="StatusCards",
                    props={
                        "title": "설비 상태",
                        "items": status_cards,
                    },
                )
            )

        return UISchema(
            layout="grid",
            title=self._generate_title(query, "설비 상태"),
            components=components,
        )

    def _generate_traceability(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate traceability timeline schema"""
        components = []

        traceability = data.get("traceability", data)
        lot_no = traceability.get("lot_no", "")

        # Summary cards
        summary = traceability.get("summary", {})
        components.append(
            UIComponent(
                type="KPICard",
                props={
                    "title": "총 양품",
                    "value": summary.get("total_ok_qty", 0),
                },
            )
        )

        components.append(
            UIComponent(
                type="KPICard",
                props={
                    "title": "총 불량",
                    "value": summary.get("total_ng_qty", 0),
                    "color": "red" if summary.get("total_ng_qty", 0) > 0 else "gray",
                },
            )
        )

        components.append(
            UIComponent(
                type="KPICard",
                props={
                    "title": "수율",
                    "value": f"{summary.get('yield_rate', 0):.1f}%",
                },
            )
        )

        # Timeline
        timeline = traceability.get("timeline", [])
        if timeline:
            components.append(
                UIComponent(
                    type="TraceabilityTimeline",
                    props={
                        "title": f"LOT {lot_no} 생산 이력",
                        "events": timeline,
                    },
                )
            )

        # Work order details
        work_order = traceability.get("work_order", {})
        if work_order:
            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": "작업지시 정보",
                        "columns": [
                            {"key": "field", "label": "항목"},
                            {"key": "value", "label": "값"},
                        ],
                        "data": [
                            {"field": "LOT No", "value": work_order.get("lot_no")},
                            {"field": "상태", "value": work_order.get("status")},
                            {"field": "목표수량", "value": work_order.get("target_qty")},
                        ],
                    },
                )
            )

        return UISchema(
            layout="detail",
            title=f"LOT {lot_no} 추적",
            components=components,
        )

    def _generate_comparison_chart(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate comparison chart schema"""
        components = []

        util_data = data.get("utilization", {}).get("equipment_utilization", [])
        if util_data:
            components.append(
                UIComponent(
                    type="BarChart",
                    props={
                        "title": "설비별 가동률 비교",
                        "data": [
                            {
                                "name": u["equipment_name"],
                                "utilization": u["utilization_rate"],
                                "yield": u.get("yield_rate", 0),
                            }
                            for u in util_data
                        ],
                        "bars": [
                            {"dataKey": "utilization", "name": "가동률", "color": "#3b82f6"},
                            {"dataKey": "yield", "name": "수율", "color": "#10b981"},
                        ],
                    },
                )
            )

            # Summary
            summary = data.get("utilization", {}).get("summary", {})
            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": "요약",
                        "columns": [
                            {"key": "metric", "label": "지표"},
                            {"key": "value", "label": "값"},
                        ],
                        "data": [
                            {"metric": "총 설비 수", "value": summary.get("total_equipment", 0)},
                            {
                                "metric": "평균 가동률",
                                "value": f"{summary.get('average_utilization', 0):.1f}%",
                            },
                            {"metric": "최고 성과", "value": summary.get("top_performer", "-")},
                            {"metric": "병목", "value": summary.get("bottleneck", "-")},
                        ],
                    },
                )
            )

        return UISchema(
            layout="dashboard",
            title=self._generate_title(query, "비교 분석"),
            components=components,
        )

    def _generate_chart(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate trend chart schema"""
        components = []

        trends = data.get("trends", {})
        trend_data = trends.get("data", [])

        if trend_data:
            metric = trends.get("metric", "value")
            components.append(
                UIComponent(
                    type="LineChart",
                    props={
                        "title": f"{metric.title()} 추이",
                        "data": trend_data,
                        "xKey": "date",
                        "yKey": "value",
                    },
                )
            )

        return UISchema(
            layout="single",
            title=self._generate_title(query, "추이 분석"),
            components=components,
        )

    def _generate_list(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate list/table schema"""
        components = []

        # Find list data in response
        list_data = None
        list_title = "목록"

        for key in ["products", "processes", "orders", "results", "equipments"]:
            if key in data and isinstance(data[key], list):
                list_data = data[key]
                list_title = {
                    "products": "제품 목록",
                    "processes": "공정 목록",
                    "orders": "작업지시 목록",
                    "results": "생산실적 목록",
                    "equipments": "설비 목록",
                }.get(key, "목록")
                break

        if list_data and len(list_data) > 0:
            # Auto-generate columns from first item
            first_item = list_data[0]
            columns = [
                {"key": k, "label": k.replace("_", " ").title()}
                for k in first_item.keys()
                if not k.startswith("_") and k not in ["id", "created_at", "updated_at"]
            ][:6]  # Limit to 6 columns

            components.append(
                UIComponent(
                    type="DataTable",
                    props={
                        "title": list_title,
                        "columns": columns,
                        "data": list_data,
                        "sortable": True,
                        "pagination": True,
                    },
                )
            )

        return UISchema(
            layout="single",
            title=self._generate_title(query, list_title),
            components=components,
        )

    def _generate_detail(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate detail view schema"""
        return self._generate_list(data, query)

    def _generate_gantt(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate Gantt chart schema"""
        components = []

        availability = data.get("availability", {})
        if availability:
            components.append(
                UIComponent(
                    type="GanttChart",
                    props={
                        "title": "스케줄",
                        "data": availability,
                    },
                )
            )

        return UISchema(
            layout="single",
            title=self._generate_title(query, "스케줄"),
            components=components,
        )

    def _generate_help(self, data: Dict[str, Any], query: str) -> UISchema:
        """Generate help message schema"""
        components = [
            UIComponent(
                type="HelpCard",
                props={
                    "title": "도움말",
                    "message": "다음과 같은 질문을 해보세요:",
                    "examples": [
                        "오늘 생산 현황 보여줘",
                        "CNC-001 설비 상태 어때?",
                        "이번 주 수율 추이",
                        "LOT-001 이력 조회",
                        "설비별 가동률 비교",
                    ],
                },
            )
        ]

        return UISchema(
            layout="single",
            title="도움말",
            components=components,
        )

    def _generate_title(self, query: str, default: str) -> str:
        """Generate title from query or use default"""
        if len(query) > 30:
            return query[:27] + "..."
        return query or default
