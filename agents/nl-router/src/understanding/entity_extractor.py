"""Entity extractor for MES domain queries"""

import re
import logging
from datetime import date
from typing import Dict, Any, Optional, List

from .entities import (
    Entity,
    EntityType,
    ExtractedEntities,
    DATE_KEYWORDS,
    DATE_RANGE_KEYWORDS,
    STATUS_KEYWORDS,
    EQUIPMENT_TYPE_KEYWORDS,
    METRIC_KEYWORDS,
    GROUP_BY_KEYWORDS,
    DEFECT_KEYWORDS,
    SHIFT_KEYWORDS,
    TIME_RANGE_KEYWORDS,
)
from ..llm.llm_client import LLMClient, get_llm_client
from ..llm.prompts import ENTITY_EXTRACTION_PROMPT


# 암시적 참조 패턴 (컨텍스트에서 해결)
IMPLICIT_PATTERNS = {
    EntityType.EQUIPMENT_ID: [
        r"그\s*설비",
        r"해당\s*설비",
        r"이\s*설비",
        r"같은\s*설비",
        r"그\s*장비",
        r"그\s*기계",
    ],
    EntityType.LOT_NO: [
        r"그\s*LOT",
        r"해당\s*LOT",
        r"이\s*LOT",
        r"그\s*로트",
    ],
    EntityType.PRODUCT_ID: [
        r"그\s*제품",
        r"해당\s*제품",
        r"같은\s*제품",
    ],
    EntityType.WORK_ORDER_ID: [
        r"그\s*오더",
        r"해당\s*작업",
        r"이\s*작업",
        r"이번\s*오더",
    ],
}

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract and normalize entities from natural language queries"""

    def __init__(self, llm_client: Optional[LLMClient] = None, use_llm: bool = False):
        """
        Initialize extractor

        Args:
            llm_client: LLM client instance
            use_llm: Whether to use LLM for extraction (default: False - use rules only)
        """
        self.llm_client = llm_client
        self.use_llm = use_llm

    async def extract(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractedEntities:
        """
        Extract entities from query

        Args:
            query: User's natural language query
            context: Conversation context with active entities

        Returns:
            ExtractedEntities with all extracted entities
        """
        if self.use_llm:
            try:
                return await self._extract_with_llm(query)
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, using rule-based")

        return self._extract_with_rules(query, context)

    async def _extract_with_llm(self, query: str) -> ExtractedEntities:
        """Extract entities using LLM"""
        client = self.llm_client or get_llm_client()

        prompt = ENTITY_EXTRACTION_PROMPT.format(query=query)
        response = await client.complete(prompt)

        if isinstance(response, dict) and "entities" in response:
            entities = []
            for e in response["entities"]:
                try:
                    entity_type = EntityType(e["type"])
                    entities.append(
                        Entity(
                            type=entity_type,
                            value=e["value"],
                            raw_text=e.get("raw_text", e["value"]),
                            normalized=e.get("normalized"),
                        )
                    )
                except (ValueError, KeyError) as err:
                    logger.warning(f"Failed to parse entity: {e}, error: {err}")
                    continue

            return ExtractedEntities(entities=entities)

        return ExtractedEntities()

    def _extract_with_rules(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractedEntities:
        """Extract entities using regex patterns"""
        entities = []
        query_lower = query.lower()

        # Extract dates
        entities.extend(self._extract_dates(query, query_lower))

        # Extract date ranges
        entities.extend(self._extract_date_ranges(query, query_lower))

        # Extract LOT numbers
        entities.extend(self._extract_lot_numbers(query))

        # Extract equipment IDs
        entities.extend(self._extract_equipment_ids(query))

        # Extract equipment types
        entities.extend(self._extract_equipment_types(query, query_lower))

        # Extract status
        entities.extend(self._extract_status(query, query_lower))

        # Extract metrics
        entities.extend(self._extract_metrics(query, query_lower))

        # Extract group_by
        entities.extend(self._extract_group_by(query, query_lower))

        # Extract quantities
        entities.extend(self._extract_quantities(query))

        # Extract alarm codes (신규)
        entities.extend(self._extract_alarm_codes(query))

        # Extract defect types (신규)
        entities.extend(self._extract_defect_types(query, query_lower))

        # Extract shift/time range (신규)
        entities.extend(self._extract_shift(query, query_lower))

        # Resolve implicit references from context (신규)
        if context:
            entities.extend(self._resolve_implicit_references(query_lower, context))

        return ExtractedEntities(entities=entities)

    def _extract_dates(self, query: str, query_lower: str) -> List[Entity]:
        """Extract date entities"""
        entities = []

        # Check keyword dates
        for keyword, date_func in DATE_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.DATE,
                        value=keyword,
                        raw_text=keyword,
                        normalized=date_func().isoformat(),
                    )
                )

        # Check ISO format dates (YYYY-MM-DD)
        iso_pattern = r"\d{4}-\d{2}-\d{2}"
        for match in re.finditer(iso_pattern, query):
            try:
                parsed = date.fromisoformat(match.group())
                entities.append(
                    Entity(
                        type=EntityType.DATE,
                        value=match.group(),
                        raw_text=match.group(),
                        normalized=parsed.isoformat(),
                    )
                )
            except ValueError:
                continue

        # Check Korean date format (2024년 1월 24일)
        kr_pattern = r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일"
        kr_full_matches = set()
        for match in re.finditer(kr_pattern, query):
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                parsed = date(year, month, day)
                kr_full_matches.add(match.start())
                entities.append(
                    Entity(
                        type=EntityType.DATE,
                        value=match.group(),
                        raw_text=match.group(),
                        normalized=parsed.isoformat(),
                    )
                )
            except ValueError:
                continue

        # Check Korean date without year (2월 10일 -> current year)
        kr_md_pattern = r"(\d{1,2})월\s*(\d{1,2})일"
        for match in re.finditer(kr_md_pattern, query):
            # Skip if this is part of a full year-month-day match
            if re.search(r"\d{4}년\s*" + re.escape(match.group()), query):
                continue
            try:
                month, day = int(match.group(1)), int(match.group(2))
                parsed = date(date.today().year, month, day)
                entities.append(
                    Entity(
                        type=EntityType.DATE,
                        value=match.group(),
                        raw_text=match.group(),
                        normalized=parsed.isoformat(),
                    )
                )
            except ValueError:
                continue

        return entities

    def _extract_date_ranges(self, query: str, query_lower: str) -> List[Entity]:
        """Extract date range entities"""
        entities = []

        for keyword, normalized in DATE_RANGE_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.DATE_RANGE,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        # Check "최근 N일" pattern
        recent_pattern = r"최근\s*(\d+)\s*일"
        for match in re.finditer(recent_pattern, query):
            days = int(match.group(1))
            entities.append(
                Entity(
                    type=EntityType.DATE_RANGE,
                    value=match.group(),
                    raw_text=match.group(),
                    normalized=f"last_{days}_days",
                )
            )

        return entities

    def _extract_lot_numbers(self, query: str) -> List[Entity]:
        """Extract LOT number entities"""
        entities = []
        seen_normalized: set = set()

        # Both patterns are case-insensitive variants of the same match, so use
        # a single case-insensitive pattern and deduplicate by normalized value.
        pattern = r"LOT[-_\s]?[\w\d-]+"

        for match in re.finditer(pattern, query, re.IGNORECASE):
            lot_no = match.group().upper().replace(" ", "-")
            if lot_no in seen_normalized:
                continue
            seen_normalized.add(lot_no)
            entities.append(
                Entity(
                    type=EntityType.LOT_NO,
                    value=lot_no,
                    raw_text=match.group(),
                    normalized=lot_no,
                )
            )

        return entities

    def _extract_equipment_ids(self, query: str) -> List[Entity]:
        """Extract equipment ID entities"""
        entities = []

        # Pattern: CNC-001, ROBOT-001, PLC-001
        pattern = r"(CNC|ROBOT|PLC|cnc|robot|plc)[-_]?\d+"
        for match in re.finditer(pattern, query, re.IGNORECASE):
            eq_id = match.group().upper()
            # Normalize format: TYPE-NUMBER
            eq_id = re.sub(r"[-_]?(\d+)", r"-\1", eq_id)
            entities.append(
                Entity(
                    type=EntityType.EQUIPMENT_ID,
                    value=match.group(),
                    raw_text=match.group(),
                    normalized=eq_id,
                )
            )

        return entities

    def _extract_equipment_types(self, query: str, query_lower: str) -> List[Entity]:
        """Extract equipment type entities"""
        entities = []

        for keyword, normalized in EQUIPMENT_TYPE_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.EQUIPMENT_TYPE,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        return entities

    def _extract_status(self, query: str, query_lower: str) -> List[Entity]:
        """Extract status entities"""
        entities = []

        for keyword, normalized in STATUS_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.STATUS,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        return entities

    def _extract_metrics(self, query: str, query_lower: str) -> List[Entity]:
        """Extract metric entities"""
        entities = []

        for keyword, normalized in METRIC_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.METRIC,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        return entities

    def _extract_group_by(self, query: str, query_lower: str) -> List[Entity]:
        """Extract group_by entities"""
        entities = []

        for keyword, normalized in GROUP_BY_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.GROUP_BY,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        return entities

    def _extract_quantities(self, query: str) -> List[Entity]:
        """Extract quantity entities"""
        entities = []

        # Pattern: 100개, 1000EA, etc.
        patterns = [
            r"(\d+)\s*개",
            r"(\d+)\s*EA",
            r"(\d+)\s*ea",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, query):
                qty = int(match.group(1))
                entities.append(
                    Entity(
                        type=EntityType.QUANTITY,
                        value=match.group(),
                        raw_text=match.group(),
                        normalized=qty,
                    )
                )

        return entities

    def _extract_alarm_codes(self, query: str) -> List[Entity]:
        """Extract alarm code entities"""
        entities = []

        # Pattern: AL-001, ERR-001, E-123, 알람001
        patterns = [
            r"(AL|ERR|E)[-_]?\d+",
            r"알람\s*[-_]?\d+",
            r"에러\s*코드?\s*[-_]?\d+",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, query, re.IGNORECASE):
                alarm_code = match.group().upper().replace(" ", "")
                # 알람 텍스트를 AL- 형식으로 정규화
                alarm_code = re.sub(r"알람", "AL-", alarm_code)
                alarm_code = re.sub(r"에러코드?", "ERR-", alarm_code)
                entities.append(
                    Entity(
                        type=EntityType.ALARM_CODE,
                        value=match.group(),
                        raw_text=match.group(),
                        normalized=alarm_code,
                    )
                )

        return entities

    def _extract_defect_types(self, query: str, query_lower: str) -> List[Entity]:
        """Extract defect type entities"""
        entities = []

        for keyword, normalized in DEFECT_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.DEFECT_TYPE,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        return entities

    def _extract_shift(self, query: str, query_lower: str) -> List[Entity]:
        """Extract shift and time range entities"""
        entities = []

        # 근무조 추출
        for keyword, normalized in SHIFT_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.SHIFT,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        # 시간대 추출
        for keyword, normalized in TIME_RANGE_KEYWORDS.items():
            if keyword in query_lower:
                entities.append(
                    Entity(
                        type=EntityType.TIME_RANGE,
                        value=keyword,
                        raw_text=keyword,
                        normalized=normalized,
                    )
                )

        return entities

    def _resolve_implicit_references(
        self,
        query_lower: str,
        context: Dict[str, Any],
    ) -> List[Entity]:
        """
        컨텍스트에서 암시적 참조 해결

        예: "그 설비" -> 이전에 언급된 equipment_id
        """
        entities = []
        active_entities = context.get("active_entities", {})

        for entity_type, patterns in IMPLICIT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    # 컨텍스트에서 해당 엔티티 타입의 값 찾기
                    entity_key = entity_type.value
                    if entity_key in active_entities:
                        value = active_entities[entity_key]
                        entities.append(
                            Entity(
                                type=entity_type,
                                value=value,
                                raw_text=pattern,
                                normalized=value,
                                confidence=0.8,  # 컨텍스트 기반은 신뢰도 낮춤
                            )
                        )
                        logger.debug(
                            f"Resolved implicit reference: {pattern} -> {entity_key}={value}"
                        )
                    break  # 첫 번째 매칭된 패턴만 처리

        return entities
