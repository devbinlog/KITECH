"""NL Router Agent - Main orchestrator for natural language query processing"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import httpx

from .understanding import IntentClassifier, EntityExtractor, Intent
from .skills import APISelector, OrchestrationPlan, get_skill_registry
from .ui_generator import UISchemaGenerator
from .llm import LLMClient
from .context import get_conversation_manager
from .core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of processing a natural language query"""

    success: bool
    intent: Intent
    entities: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    ui_schema: Optional[Dict[str, Any]] = None
    text_response: str = ""
    errors: list = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)


class NLRouterAgent:
    """
    Main NL Router Agent that orchestrates:
    1. Query understanding (intent classification + entity extraction)
    2. Skill matching
    3. API orchestration
    4. UI schema generation
    """

    def __init__(
        self,
        mes_api_base_url: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        use_llm: bool = True,
    ):
        self.mes_api_base_url = mes_api_base_url or settings.CELL_MES_URL
        self.llm_client = llm_client

        # Initialize components
        self.intent_classifier = IntentClassifier(llm_client=llm_client, use_llm=use_llm)
        self.entity_extractor = EntityExtractor(
            llm_client=llm_client, use_llm=False
        )  # Rule-based is faster
        self.skill_registry = get_skill_registry()
        self.api_selector = APISelector(base_url=mes_api_base_url)
        self.ui_generator = UISchemaGenerator()

        # Conversation context manager
        self.conversation_manager = get_conversation_manager()

        # HTTP client for API calls
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.mes_api_base_url,
                timeout=30.0,
            )
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> QueryResult:
        """
        Process a natural language query

        Args:
            query: User's natural language query
            session_id: Session ID for conversation context tracking
            user_id: User ID for context association
            auth_token: Authentication token for MES API

        Returns:
            QueryResult with data and UI schema
        """
        debug_info = {"query": query, "session_id": session_id}
        errors = []

        # Get conversation context if session_id provided
        context_dict = None
        if session_id:
            conv_context = self.conversation_manager.get_context(session_id, user_id)
            context_dict = {
                "summary": conv_context.get_context_summary(),
                "active_entities": conv_context.active_entities,
            }
            debug_info["context_active_entities"] = conv_context.active_entities

        try:
            # 1. Classify intent (with context)
            intent_result = await self.intent_classifier.classify(query, context_dict)
            debug_info["intent_result"] = {
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "entities": intent_result.entities,
            }

            # 2. Extract additional entities (with context for implicit reference resolution)
            extracted = await self.entity_extractor.extract(query, context=context_dict)
            entities = {**extracted.to_dict(), **intent_result.entities}
            debug_info["extracted_entities"] = entities

            # Update active entities in conversation context
            if session_id:
                # Add user message
                self.conversation_manager.add_user_message(session_id, query, entities=entities)

            # Handle clarification needed
            if intent_result.requires_clarification:
                clarification_response = "질문을 더 명확히 해주세요: " + ", ".join(
                    intent_result.suggested_questions
                )
                # Add clarification response to conversation history so follow-up
                # answers have the context of what was asked, including the partially
                # classified intent and entities so the next turn can continue from here.
                if session_id:
                    self.conversation_manager.add_assistant_message(
                        session_id,
                        clarification_response,
                        intent=intent_result.intent.value,
                        entities=entities,
                    )
                debug_info["clarification"] = {
                    "intent": intent_result.intent.value,
                    "entities": entities,
                    "suggested_questions": intent_result.suggested_questions,
                }
                return QueryResult(
                    success=True,
                    intent=intent_result.intent,
                    entities=entities,
                    text_response=clarification_response,
                    debug_info=debug_info,
                )

            # Handle unknown intent
            if intent_result.intent == Intent.UNKNOWN:
                ui_schema = self.ui_generator.generate({}, intent_result.intent.value, query)
                return QueryResult(
                    success=True,
                    intent=intent_result.intent,
                    entities=entities,
                    ui_schema=ui_schema.model_dump(),
                    text_response="죄송합니다. 질문을 이해하지 못했습니다. 다음과 같은 질문을 해보세요: '오늘 생산 현황', '설비 상태', 'LOT-001 이력'",
                    debug_info=debug_info,
                )

            # 3. Match skill
            skill = self.skill_registry.get_best_skill(intent_result.intent, entities)
            if not skill:
                return QueryResult(
                    success=False,
                    intent=intent_result.intent,
                    entities=entities,
                    text_response=f"'{intent_result.intent.value}' 인텐트를 처리할 스킬을 찾지 못했습니다.",
                    errors=["No matching skill found"],
                    debug_info=debug_info,
                )
            debug_info["matched_skill"] = skill.name

            # Check for missing required entities
            missing = skill.get_missing_entities(entities)
            if missing:
                return QueryResult(
                    success=False,
                    intent=intent_result.intent,
                    entities=entities,
                    text_response=f"다음 정보가 필요합니다: {', '.join(missing)}",
                    errors=[f"Missing required entities: {missing}"],
                    debug_info=debug_info,
                )

            # 4. Build orchestration plan
            plan = self.api_selector.build_plan(skill, intent_result.intent, entities)
            debug_info["api_plan"] = {
                "calls": [{"endpoint": c.endpoint, "params": c.params} for c in plan.calls],
                "execution_mode": plan.execution_mode.value,
            }

            # 5. Execute API calls
            data = await self._execute_plan(plan, auth_token)
            debug_info["api_results"] = list(data.keys())

            # Handle API errors
            if "_errors" in data:
                errors.extend(data.pop("_errors"))

            # 6. Generate UI schema
            ui_schema = self.ui_generator.generate(data, plan.output_type, query)

            # 7. Generate text response
            text_response = self._generate_summary(data, intent_result.intent, query)

            # 8. Add assistant message to conversation context
            if session_id:
                self.conversation_manager.add_assistant_message(
                    session_id=session_id,
                    content=text_response,
                    intent=intent_result.intent.value,
                    entities=entities,
                    ui_schema=ui_schema.model_dump(),
                )

            return QueryResult(
                success=True,
                intent=intent_result.intent,
                entities=entities,
                data=data,
                ui_schema=ui_schema.model_dump(),
                text_response=text_response,
                errors=errors,
                debug_info=debug_info,
            )

        except Exception as e:
            logger.exception(f"Error processing query: {query}")
            return QueryResult(
                success=False,
                intent=Intent.UNKNOWN,
                text_response=f"쿼리 처리 중 오류가 발생했습니다: {str(e)}",
                errors=[str(e)],
                debug_info=debug_info,
            )

    async def _execute_plan(
        self,
        plan: OrchestrationPlan,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute API orchestration plan by calling MES endpoints sequentially.

        Args:
            plan: OrchestrationPlan containing API calls to execute.
            auth_token: Optional JWT token for authorization header.

        Returns:
            Dictionary mapping result_key to API response data.
            Includes '_errors' key if any calls failed.
        """
        results = {}
        errors = []

        # Always include internal service key for MES API calls
        headers = {
            "X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY,
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        for call in plan.calls:
            try:
                endpoint = call.get_full_endpoint()
                logger.debug(f"Executing API call: {call.method} {endpoint} params={call.params}")

                response = await self.http_client.request(
                    method=call.method,
                    url=endpoint,
                    params=call.params if call.method == "GET" else None,
                    json=call.params if call.method != "GET" else None,
                    headers=headers,
                    timeout=call.timeout,
                )

                if 200 <= response.status_code < 300:
                    # Accept any 2xx response as success:
                    # - 200 OK (GET responses)
                    # - 201 Created (POST operations like creating work orders)
                    # - 204 No Content (DELETE operations)
                    if response.status_code == 204 or not response.content:
                        results[call.result_key] = {}
                    else:
                        try:
                            results[call.result_key] = response.json()
                        except ValueError as e:
                            logger.warning(f"Failed to decode JSON from {endpoint}: {e}")
                            results[call.result_key] = {}
                else:
                    error_msg = f"API error {response.status_code}: {endpoint}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    results[call.result_key] = {}

            except httpx.RequestError as e:
                error_msg = f"Request failed for {call.endpoint}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                results[call.result_key] = {}
                # Reset client on connection-level errors so next call gets a fresh connection
                if isinstance(e, (httpx.ConnectError, httpx.RemoteProtocolError)):
                    if self._http_client:
                        await self._http_client.aclose()
                    self._http_client = None

        if errors:
            results["_errors"] = errors

        return results

    def _generate_summary(
        self,
        data: Dict[str, Any],
        intent: Intent,
        query: str,
    ) -> str:
        """Generate natural language summary of API results.

        Produces a Korean-language summary appropriate to the intent type
        (production status, equipment status, scheduling, etc.).

        Args:
            data: API response data dictionary.
            intent: Classified user intent.
            query: Original user query string.

        Returns:
            Korean natural language summary string.
        """
        # Simple rule-based summary generation
        if intent == Intent.PRODUCTION_STATUS:
            ds = data.get("daily_status") or {}
            orders = ds.get("orders") or {}
            kpis = ds.get("kpis") or {}
            return (
                f"오늘 총 {orders.get('total', 0)}건의 작업지시 중 "
                f"{orders.get('completed', 0)}건이 완료되었습니다. "
                f"수율은 {float(kpis.get('yield_rate') or 0):.1f}%입니다."
            )

        elif intent == Intent.EQUIPMENT_STATUS:
            equipments = data.get("equipments") or []
            if isinstance(equipments, dict):
                eq = equipments
                return f"{eq.get('eq_name', '설비')}의 현재 상태는 {eq.get('current_status', '알 수 없음')}입니다."
            elif equipments:
                running = sum(1 for e in equipments if e.get("current_status") == "RUN")
                return f"총 {len(equipments)}대의 설비 중 {running}대가 가동 중입니다."
            return "설비 정보를 조회했습니다."

        elif intent == Intent.KPI_QUERY:
            kpis = (data.get("kpis") or {}).get("today") or {}
            return (
                f"오늘 KPI: 완료율 {float(kpis.get('completion_rate') or 0):.1f}%, "
                f"수율 {float(kpis.get('yield_rate') or 0):.1f}%, "
                f"가동률 {float(kpis.get('equipment_utilization') or 0):.1f}%"
            )

        elif intent == Intent.TRACEABILITY:
            trace = data.get("traceability") or {}
            summary = trace.get("summary") or {}
            return (
                f"LOT {trace.get('lot_no', '')} 조회 결과: "
                f"양품 {summary.get('total_ok_qty', 0)}개, "
                f"불량 {summary.get('total_ng_qty', 0)}개, "
                f"수율 {float(summary.get('yield_rate') or 0):.1f}%"
            )

        elif intent == Intent.COMPARISON:
            util = data.get("utilization") or {}
            summary = util.get("summary") or {}
            return (
                f"총 {summary.get('total_equipment', 0)}대 설비의 평균 가동률은 "
                f"{float(summary.get('average_utilization') or 0):.1f}%입니다. "
                f"최고 성과: {summary.get('top_performer', '-')}, "
                f"병목: {summary.get('bottleneck', '-')}"
            )

        elif intent == Intent.SCHEDULE_QUERY:
            # 스케줄 조회 응답 처리 (data.schedule에 있을 수 있음)
            schedule_data = data.get("schedule") or data  # schedule 키가 있으면 사용
            summary = schedule_data.get("summary") or {}
            availability = schedule_data.get("availability") or []
            date = schedule_data.get("date", "오늘")

            total_equipments = summary.get("total_equipments", 0)
            total_scheduled = summary.get("total_scheduled_orders", 0)
            running = summary.get("running_orders", 0)

            # 설비별 상세 정보 생성
            details = []
            for eq in availability[:5]:  # 최대 5개 설비만 표시
                if not eq or not isinstance(eq, dict):
                    continue
                eq_name = eq.get("equipment_name", "")
                schedule = eq.get("schedule", [])
                if schedule:
                    running_slots = sum(1 for s in schedule if isinstance(s, dict) and s.get("status") == "RUNNING")
                    total_slots = len(schedule)
                    products = list(set(s.get("product", "") for s in schedule if isinstance(s, dict) and s.get("product")))
                    product_str = ", ".join(products[:2]) if products else "-"
                    details.append(f"  • {eq_name}: {total_slots}건 ({product_str})")

            response = f"📅 {date} 스케줄 현황\n\n"
            response += f"총 {total_equipments}대 설비 중 {total_scheduled}건의 작업이 스케줄되어 있습니다.\n"
            response += f"현재 진행 중: {running}건\n"

            if details:
                response += f"\n📋 설비별 작업:\n" + "\n".join(details)

            return response

        elif intent == Intent.PRODUCTION_DETAIL:
            detail = data.get("production_detail", data)
            lot_no = detail.get("lot_no", "")
            status = detail.get("status", "알 수 없음")
            target = detail.get("target_qty", 0)
            ok_qty = detail.get("ok_qty", 0)
            ng_qty = detail.get("ng_qty", 0)
            return (
                f"LOT {lot_no} 상세: 상태 {status}, "
                f"목표 {target}개, 양품 {ok_qty}개, 불량 {ng_qty}개"
            )

        elif intent == Intent.EQUIPMENT_LIST:
            eq_list = data.get("equipment_list") or data.get("equipments") or []
            if isinstance(eq_list, dict):
                eq_list = eq_list.get("items") or []
            if not isinstance(eq_list, list):
                eq_list = []
            count = len(eq_list)
            details = []
            for eq in eq_list[:5]:
                if not isinstance(eq, dict):
                    continue
                name = eq.get("name", eq.get("eq_name", ""))
                eq_type = eq.get("equipment_type", eq.get("type", ""))
                status = eq.get("status", eq.get("current_status", ""))
                details.append(f"{name}({eq_type}): {status}")
            detail_str = ", ".join(details) if details else "-"
            return f"총 {count}대 설비: {detail_str}"

        elif intent == Intent.SCHEDULE_REQUEST:
            req = data.get("schedule_request", data)
            solver = req.get("solver", "기본")
            horizon = req.get("horizon_hours", req.get("horizon", 24))
            status = req.get("status", "완료")
            return f"스케줄링 요청 {status}: solver={solver}, horizon={horizon}시간"

        elif intent == Intent.MASTER_DATA_QUERY:
            master = data.get("master_data", data)
            products = master.get("products") or []
            if not isinstance(products, list):
                products = []
            processes = master.get("processes") or []
            if not isinstance(processes, list):
                processes = []
            product_count = len(products)
            process_count = len(processes)
            items = []
            for p in products[:3]:
                if isinstance(p, dict):
                    items.append(p.get("name", ""))
            item_str = ", ".join(items) if items else "-"
            return (
                f"마스터 데이터: 제품 {product_count}건, 공정 {process_count}건"
                f" (제품: {item_str})"
            )

        elif intent == Intent.ANALYTICS:
            analytics = data.get("analytics", data)
            period = analytics.get("period", "최근")
            trend = analytics.get("trend") or {}
            if not isinstance(trend, dict):
                trend = {}
            raw_change_rate = trend.get("change_rate", 0)
            change_rate = float(raw_change_rate or 0) if raw_change_rate is not None else 0.0
            direction = "상승" if change_rate >= 0 else "하락"
            return f"{period} 트렌드 분석: {abs(change_rate):.1f}% {direction}"

        elif intent == Intent.ERROR_DIAGNOSIS:
            diag = data.get("diagnosis", data)
            alarm_code = diag.get("alarm_code", diag.get("error_code", "-"))
            equipment = diag.get("equipment_name", diag.get("eq_name", "-"))
            cause = diag.get("cause", diag.get("probable_cause", "원인 분석 중"))
            return f"알람 {alarm_code} ({equipment}): {cause}"

        elif intent == Intent.DELAY_PREDICTION:
            prediction = data.get("delay_prediction", data)
            delayed = prediction.get("delayed_orders") or []
            if not isinstance(delayed, list):
                delayed = []
            count = prediction.get("total_delayed", len(delayed))
            first = delayed[0] if delayed else {}
            most_critical = first.get("lot_no", "-") if isinstance(first, dict) else "-"
            return f"지연 위험 오더 {count}건, 가장 위험: {most_critical}"

        elif intent == Intent.DEFECT_ANALYSIS:
            defects = data.get("defect_analysis", data)
            raw_defect_rate = defects.get("defect_rate")
            defect_rate = float(raw_defect_rate) if raw_defect_rate is not None else 0.0
            main_cause = defects.get("main_cause", defects.get("top_cause", "-"))
            return f"불량률 {defect_rate:.1f}%, 주요 원인: {main_cause}"

        elif intent == Intent.TOOL_MANAGEMENT:
            tools = data.get("tool_management", data)
            raw_remaining = tools.get("avg_remaining_life")
            if raw_remaining is None:
                raw_remaining = tools.get("remaining_life")
            remaining = float(raw_remaining) if raw_remaining is not None else 0.0
            need_replace = tools.get("need_replacement", 0)
            return f"공구 잔여 수명 평균 {remaining:.1f}%, 교체 필요 {need_replace}건"

        elif intent == Intent.ACTION_REQUEST:
            action = data.get("action_result", data)
            action_type = action.get("action_type", action.get("type", "실행"))
            result_status = action.get("result", action.get("status", "완료"))
            return f"액션 '{action_type}' {result_status}"

        elif intent == Intent.HELP:
            return (
                "사용 가능한 질문 예시:\n"
                "• '오늘 생산 현황' - 생산 요약\n"
                "• '설비 상태' - 설비 모니터링\n"
                "• 'LOT-001 이력' - LOT 추적\n"
                "• '가동률' - KPI 조회\n"
                "• '스케줄 조회' - 오늘 스케줄"
            )

        return "조회가 완료되었습니다."


# Singleton instance
_nl_router: Optional[NLRouterAgent] = None


def get_nl_router(
    mes_api_base_url: Optional[str] = None,
    use_llm: bool = True,
) -> NLRouterAgent:
    """Get global NL Router instance"""
    global _nl_router
    if _nl_router is None:
        _nl_router = NLRouterAgent(
            mes_api_base_url=mes_api_base_url or settings.CELL_MES_URL,
            use_llm=use_llm,
        )
    return _nl_router
