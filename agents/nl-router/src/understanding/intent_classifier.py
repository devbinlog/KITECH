"""Intent classifier using LLM and rule-based fallback"""

import re
import logging
from typing import Dict, Any, Optional, List

from .intents import Intent, IntentResult
from ..llm.llm_client import LLMClient, get_llm_client
from ..llm.prompts import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


# Keyword patterns for rule-based classification
# 현장작업자/공장관리자/사장님 구어체 패턴 포함
INTENT_KEYWORDS = {
    Intent.PRODUCTION_STATUS: [
        # 기본
        r"생산\s*현황",
        r"작업\s*지시",
        r"작업\s*목록",
        r"생산\s*실적",
        r"오늘\s*생산",
        r"production\s*status",
        r"work\s*order",
        r"생산량",
        r"몇\s*개\s*남았",
        r"생산\s*결과",
        # 현장작업자 구어체
        r"라인\s*살아있",
        r"돌아가\?",
        r"잘\s*돌아가",
        r"잘\s*되고\s*있",
        r"문제\s*없",
        r"상황\s*어때",
        r"오늘\s*어때",
        # 공장관리자
        r"공장\s*전체",
        r"전체\s*라인",
        r"전체\s*현황",
        # 사장님
        r"핵심만",
        r"결론이\s*뭐",
        r"한\s*줄로",
        # 생산량/목표 관련
        r"몇\s*개\s*더\s*해야",
        r"목표\s*달성",
        r"달성률",
        r"계획\s*대비",
        # 오늘 할 일 / 작업해야 할 것
        r"작업해야",
        r"해야\s*할\s*게",
        r"오늘.*뭐야",
        r"할\s*일",
    ],
    Intent.PRODUCTION_DETAIL: [
        r"LOT.+상세",
        r"작업.+상세",
        r"LOT.+정보",
        # 현장작업자
        r"다음\s*뭐야",
        r"다음\s*뭐\?",
        r"그\s*다음",
        r"끝나면\s*뭐",
        r"다음\s*작업",
        r"할\s*거\s*뭐",
    ],
    Intent.EQUIPMENT_STATUS: [
        r"설비\s*상태",
        r"장비\s*상태",
        r"장비들?\s*상태",
        r"equipment\s*status",
        r"CNC.+상태",
        r"로봇.+상태",
        r"ROBOT.+상태",
        r"robot.+상태",
        r"PLC.+상태",
        r"AMR.+상태",
        r"[A-Z]+-\d+\s*상태",
        # 공장관리자
        r"병목\s*설비",
        r"병목\s*어디",
        r"효율\s*(낮|떨어)",
        r"설비\s*투자",
        r"노후\s*설비",
        r"전체\s*설비",
        r"라인\s*가동",
        # 설비 가동/상태 관련 구어체
        r"가동\s*중",
        r"가동중",
        r"설비들?\s*상태",
        r"설비.*어때",
        r"몇\s*대.*가동",
        r"가동.*몇\s*대",
        # 가동 중인 설비 수 (상태 조건이 있음)
        r"가동.*설비.*몇",
        r"가동.*설비",
        r"돌아가.*설비",
        r"설비.*돌아가",
        r"돌아가는.*몇",
        r"상태.*어때",
    ],
    Intent.EQUIPMENT_LIST: [
        r"설비\s*목록",
        r"장비\s*목록",
        r"설비\s*리스트",
        # 설비 수량 관련 (단순 수량 질문)
        r"설비\s*수",
        r"전체\s*설비\s*수",
        r"장비\s*수",
        r"장비.*몇\s*(개|대)",
        r"몇\s*(개|대).*장비",
        r"설비.{0,3}몇\s*(개|대)",
        r"몇\s*(개|대).*설비",
    ],
    Intent.KPI_QUERY: [
        r"가동률",
        r"수율",
        r"KPI",
        r"지표",
        r"utilization",
        r"yield",
        r"완료율",
        # 사장님
        r"숫자로\s*보여",
        r"실적\s*어때",
        r"돈\s*(벌|이익)",
        r"야근\s*해야",
        r"제일\s*큰\s*문제",
    ],
    Intent.ANALYTICS: [
        r"추이",
        r"트렌드",
        r"trend",
        r"변화",
        # 기간별 질문
        r"이번\s*주\s*뭘",
        r"지난\s*주",
        r"이번\s*달",
        r"지난\s*달",
    ],
    Intent.COMPARISON: [
        r"비교",
        r"compare",
        r"설비별",
        r"제품별",
        r"대비",
        r"vs",
        r"야간\s*주간",
        r"주간\s*야간",
        r"차이",
        # 사장님
        r"저번\s*달보다",
        r"나아졌",
        r"좋아졌",
        r"성장하고",
    ],
    Intent.TRACEABILITY: [
        r"추적",
        r"이력",
        r"traceability",
        r"history",
        r"LOT.+이력",
        r"어디\s*갔",
        r"어디까지",
    ],
    Intent.SCHEDULE_QUERY: [
        r"스케줄",
        r"일정",
        r"schedule",
        r"계획",
        r"언제까지",
        # 사장님
        r"납기\s*지킬",
        r"납기\s*맞출",
        r"출하\s*언제",
        r"고객\s*약속",
        r"늦어지는\s*거",
    ],
    Intent.MASTER_DATA_QUERY: [
        r"제품\s*정보",
        r"공정\s*정보",
        r"마스터",
        r"master",
    ],
    Intent.ACTION_REQUEST: [
        r"생성해",
        r"만들어",
        r"동기화",
        r"sync",
        r"create",
    ],
    # 신규 인텐트 키워드 - 현장작업자 고장신고 포함
    Intent.ERROR_DIAGNOSIS: [
        r"알람",
        r"에러",
        r"멈춰",
        r"이상",
        r"왜\s*안\s*돼",
        r"error",
        r"alarm",
        r"고장",
        r"문제",
        r"왜\s*그래",
        r"진동",
        # 현장작업자 고장 신고 구어체
        r"망가졌",
        r"터졌",
        r"빨간불",
        r"안\s*돌아",
        r"이거\s*망가",
        r"소리\s*나",
        r"이상한\s*소리",
        r"멈췄어",
        r"안\s*돼",
        r"기계\s*이상",
    ],
    Intent.DELAY_PREDICTION: [
        r"지연",
        r"늦을",
        r"마감",
        r"납기\s*지연",
        r"위험\s*오더",
        r"delay",
        r"늦어질",
        r"안\s*될\s*것\s*같",
        r"야근",  # 사장님: 야근해야 해?
    ],
    Intent.DEFECT_ANALYSIS: [
        r"불량",
        r"원인",
        r"defect",
        r"불량률",
        r"왜\s*나왔",
        r"치수\s*불량",
        r"외관\s*불량",
        # 사장님
        r"클레임",
        r"고객\s*불만",
        r"반품",
        r"품질\s*문제",
        # 품질 이슈 관련
        r"품질\s*이슈",
        r"NCR",
        r"처리\s*안\s*된",
        r"미처리",
        r"이슈.*몇\s*건",
    ],
    Intent.TOOL_MANAGEMENT: [
        r"공구",
        r"인서트",
        r"수명",
        r"교체",
        r"tool",
        r"재고",
    ],
    Intent.HELP: [
        # 사용법/도움말 요청
        r"어떻게\s*해",
        r"어떻게\s*하",
        r"사용법",
        r"도움말",
        r"help",
        r"뭐\s*할\s*수\s*있",
        r"기능.*뭐",
        r"무엇.*할\s*수",
        r"방법.*알려",
        r"등록.*어떻게",
        r"조회.*어떻게",
    ],
}


class IntentClassifier:
    """Classify user intent from natural language query"""

    def __init__(self, llm_client: Optional[LLMClient] = None, use_llm: bool = True):
        """
        Initialize classifier

        Args:
            llm_client: LLM client instance (uses global if None)
            use_llm: Whether to use LLM for classification (falls back to rules if False)
        """
        self.llm_client = llm_client
        self.use_llm = use_llm
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[Intent, List[re.Pattern]]:
        """Compile regex patterns for each intent from INTENT_KEYWORDS.

        Returns:
            Dictionary mapping Intent enum to compiled case-insensitive regex patterns.
        """
        return {
            intent: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for intent, patterns in INTENT_KEYWORDS.items()
        }

    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IntentResult:
        """
        Classify intent from query

        Args:
            query: User's natural language query
            context: Previous conversation context

        Returns:
            IntentResult with classified intent and entities
        """
        # Try LLM classification first
        if self.use_llm:
            try:
                result = await self._classify_with_llm(query, context)
                if result.confidence >= 0.7:
                    return result
                # Fall through to rule-based if confidence is low
                logger.info(f"LLM confidence low ({result.confidence}), using rule-based")
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}, using rule-based")

        # Rule-based fallback
        return self._classify_with_rules(query)

    async def _classify_with_llm(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IntentResult:
        """Classify user intent using LLM with structured prompt.

        Falls back to rule-based classification if LLM response cannot be parsed.

        Args:
            query: User's natural language query.
            context: Optional previous conversation context for multi-turn support.

        Returns:
            IntentResult with intent, confidence score, and extracted entities.
        """
        client = self.llm_client or get_llm_client()

        # Format prompt
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            query=query,
            context=str(context) if context else "None",
        )

        # Get LLM response
        response = await client.complete(prompt)

        # Parse response
        if isinstance(response, dict):
            intent_str = response.get("intent", "UNKNOWN")
            try:
                intent = Intent(intent_str.lower())
            except ValueError:
                intent = Intent.UNKNOWN

            return IntentResult(
                intent=intent,
                confidence=response.get("confidence", 0.5),
                entities=response.get("entities", {}),
                sub_intent=response.get("sub_intent"),
                reasoning=response.get("reasoning"),
                requires_clarification=response.get("requires_clarification", False),
                suggested_questions=response.get("suggested_questions", []),
            )

        # Failed to parse, return unknown
        return IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            reasoning="Failed to parse LLM response",
        )

    def _classify_with_rules(self, query: str) -> IntentResult:
        """Classify intent using keyword pattern matching (rule-based fallback).

        Scores each intent by the ratio of matched patterns, selects the highest.
        Confidence is capped at 0.9 for rule-based results.

        Args:
            query: User's natural language query.

        Returns:
            IntentResult with best matching intent and extracted entities.
        """
        query_lower = query.lower()
        scores: Dict[Intent, float] = {}

        for intent, patterns in self._compiled_patterns.items():
            matched = 0.0
            for pattern in patterns:
                if pattern.search(query_lower):
                    matched += 1.0
            if matched > 0:
                # Primary score: ratio of matched patterns (specificity).
                # Tie-break: add a small bonus per additional match so that
                # an intent with more absolute evidence beats one with the
                # same ratio but fewer patterns total.
                ratio = matched / len(patterns)
                scores[intent] = ratio + matched * 0.001

        if not scores:
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                reasoning="No matching keywords found",
            )

        # Get highest scoring intent
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent], 0.9)  # Cap at 0.9 for rule-based

        # Extract basic entities using patterns
        entities = self._extract_basic_entities(query)

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
            reasoning=f"Matched keywords for {best_intent.value}",
        )

    def _extract_basic_entities(self, query: str) -> Dict[str, Any]:
        """Extract basic entities (LOT number, equipment ID, dates) using regex.

        Args:
            query: User's natural language query.

        Returns:
            Dictionary of extracted entities (lot_no, equipment_id, date, date_range).
        """
        entities = {}

        # LOT number pattern
        lot_match = re.search(r"LOT[-_]?[\w\d-]+", query, re.IGNORECASE)
        if lot_match:
            entities["lot_no"] = lot_match.group()

        # Equipment ID pattern
        eq_match = re.search(r"(CNC|ROBOT|PLC)[-_]?\d+", query, re.IGNORECASE)
        if eq_match:
            entities["equipment_id"] = eq_match.group().upper()

        # Date keywords — use elif chain to avoid duplicate DATE entity values
        # when multiple date patterns match the same query (e.g. "오늘" and "today").
        if "오늘" in query or "today" in query.lower():
            entities["date"] = "today"
        elif "어제" in query or "yesterday" in query.lower():
            entities["date"] = "yesterday"

        # Date range keywords — only set if no specific date already matched,
        # to avoid ambiguous duplicate temporal entities in the same result.
        if "date" not in entities:
            if "이번 주" in query or "this week" in query.lower():
                entities["date_range"] = "this_week"
            elif "지난 주" in query or "last week" in query.lower():
                entities["date_range"] = "last_week"
            elif "최근 7일" in query or "last 7 days" in query.lower():
                entities["date_range"] = "last_7_days"
        else:
            # A specific date was already matched; only add range if it is
            # *additionally* specified and non-redundant (e.g. "오늘 이번 주" is
            # contradictory — prefer the more specific date).
            pass

        # Equipment type
        if "cnc" in query.lower() or "씨엔씨" in query:
            entities["equipment_type"] = "CNC"
        elif "로봇" in query or "robot" in query.lower():
            entities["equipment_type"] = "ROBOT"

        # Metrics
        if "가동률" in query or "utilization" in query.lower():
            entities["metric"] = "utilization"
        elif "수율" in query or "yield" in query.lower():
            entities["metric"] = "yield"
        elif "생산량" in query or "production" in query.lower():
            entities["metric"] = "production"

        # Group by
        if "설비별" in query or "by equipment" in query.lower():
            entities["group_by"] = "equipment"
        elif "제품별" in query or "by product" in query.lower():
            entities["group_by"] = "product"
        elif "일별" in query or "daily" in query.lower():
            entities["group_by"] = "day"

        return entities
