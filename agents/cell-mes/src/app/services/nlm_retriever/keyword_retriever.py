"""
Keyword-based retriever using pattern matching and synonyms.

This is the original NLM approach - fast, no ML models required.
"""

import re
from typing import List, Dict, Set
from .base import BaseRetriever, RetrievalResult, IntentExample, RetrieverRegistry


@RetrieverRegistry.register_retriever("keyword")
class KeywordRetriever(BaseRetriever):
    """
    Rule-based retriever using keywords, patterns, and synonyms.

    Scoring:
        - Keyword match: +2 points
        - Pattern match: +3 points
        - Category match: +2 points
    """

    # Synonym dictionary
    SYNONYMS: Dict[str, List[str]] = {
        # 생산 관련
        "생산": ["생산", "제조", "만들", "찍", "가공", "산출", "생산량", "제작"],
        "실적": ["실적", "현황", "상황", "상태", "결과", "성과", "성적"],
        "양품": ["양품", "ok", "정상", "합격", "good", "pass"],
        "불량": ["불량", "ng", "부적합", "불합격", "bad", "fail", "defect"],
        # 설비 관련
        "설비": ["설비", "장비", "기계", "머신", "machine", "equipment", "라인", "호기"],
        "가동": ["가동", "운전", "작동", "돌아", "running", "run", "동작", "작업중"],
        "정지": ["정지", "멈춤", "스톱", "stop", "다운", "down", "중지", "중단", "멈췄"],
        "고장": [
            "고장",
            "에러",
            "error",
            "알람",
            "alarm",
            "이상",
            "문제",
            "fault",
            "trouble",
            "망가",
            "터졌",
            "안 돼",
            "안돼",
            "빨간불",
            "소리 나",
            "이상해",
        ],
        "대기": ["대기", "유휴", "idle", "놀", "쉬", "빈", "여유", "available"],
        # 품질 관련
        "수율": ["수율", "yield", "양품률", "품질", "quality"],
        # 작업 관련
        "작업": ["작업", "오더", "order", "지시", "wo", "job", "task", "할 일", "할일"],
        "진행": ["진행", "진행중", "running", "in progress", "작업중", "하는중", "하고 있"],
        "완료": ["완료", "끝", "done", "complete", "finished", "종료", "끝났", "끝나면"],
        "대기중": ["대기", "대기중", "ready", "waiting", "pending", "할", "다음"],
        # 스케줄
        "스케줄": ["스케줄", "일정", "schedule", "계획", "plan", "예정"],
        # KPI
        "kpi": ["kpi", "지표", "indicator", "성과지표", "metric", "대시보드", "dashboard"],
        # 분석
        "분석": ["분석", "analysis", "원인", "이유", "왜"],
        "추이": ["추이", "추세", "trend", "변화", "트렌드"],
        "비교": ["비교", "대비", "vs", "compare", "차이"],
        # 사장님 관점
        "요약": ["요약", "핵심", "결론", "한 줄로", "간단히", "핵심만"],
        "납기": ["납기", "출하", "약속", "기한", "마감", "딜리버리", "delivery"],
        "고객": ["고객", "클레임", "불만", "반품", "컴플레인", "claim"],
    }

    # Intent patterns
    INTENT_PATTERNS: Dict[str, Dict] = {
        "daily_status": {
            "keywords": [
                "현황",
                "상황",
                "상태",
                "실적",
                "어때",
                "어떻게",
                "핵심",
                "요약",
                "살아있",
                "돌아가",
            ],
            "patterns": [
                r"(생산|제조).*현황",
                r"현황.*(보여|알려|어때)",
                r"(오늘|어제|금일|전일).*(어때|어떻게|현황|상태|실적)",
                r"잘\s*되고\s*있",
                r"문제\s*없",
                r"라인\s*살아있",  # "라인 살아있어?"
                r"살아있어",  # "살아있어?" 단독
                r"잘\s*돌아가",  # "오늘 잘 돌아가?"
                r"공장\s*(전체|어때)",
                r"전체\s*(라인|현황|상태)",
                r"한\s*줄로",
                r"핵심만",
                r"결론이\s*뭐",
            ],
        },
        "production_count": {
            "keywords": ["생산량", "수량", "개수", "몇 개", "양품", "목표"],
            "patterns": [
                r"몇\s*개.*(만들|나왔|더|해야)",  # "몇 개 더 해야 해?"
                r"(생산량|수량).*(알려|어때|얼마)",
                r"(얼마나|몇\s*개)\s*(찍|만들|나왔)",
                r"(남은|남아있).*(거|수량)",
                r"목표\s*달성",  # "목표 달성률"
                r"계획\s*대비",
            ],
        },
        "equipment_status": {
            "keywords": ["설비", "장비", "기계", "가동률", "호기", "병목"],
            "patterns": [
                r"(설비|장비|기계|머신).*(상태|현황|어때|가동)",
                r"가동률",
                r"병목.*(설비|어디|분석)",
                r"설비\s*투자",
                r"노후\s*설비",
            ],
        },
        "equipment_error": {
            "keywords": ["고장", "에러", "알람", "이상", "망가", "터졌", "빨간불"],
            "patterns": [
                r"(고장|에러|알람|이상|문제).*(설비|장비|있)",
                r"(이거|기계|장비)\s*(망가졌|이상해|안\s*돌아|멈췄|터졌)",
                r"빨간불\s*(들어왔|켜졌)",
            ],
        },
        "defect_analysis": {
            "keywords": ["불량", "ng", "클레임", "반품", "불만"],
            "patterns": [
                r"불량.*(분석|현황|원인|어때|몇|얼마)",
                r"클레임",
                r"고객.*불만",
                r"반품",
            ],
        },
        "work_orders": {
            "keywords": ["작업지시", "오더", "order", "할 일"],
            "patterns": [
                r"작업.*(지시|현황|목록|뭐)",
                r"뭐\s*해(\?|$)",
                r"지금\s*뭐\s*해야",
            ],
        },
        "work_orders_pending": {
            "keywords": ["대기", "다음", "그 다음"],
            "patterns": [
                r"대기.*(작업|오더|중)",
                r"다음\s*뭐",
                r"그\s*다음",
                r"끝나면\s*뭐",
            ],
        },
        "schedule": {
            "keywords": ["스케줄", "일정", "계획", "납기", "출하"],
            "patterns": [
                r"(스케줄|일정|계획).*(보여|알려|어때)",
                r"납기\s*(지킬|맞출|어때)",
                r"출하\s*(언제|뭐)",
            ],
        },
        "compare_status": {
            "keywords": ["비교", "대비", "vs", "차이"],
            "patterns": [
                r"(어제|전일).*(오늘|금일)",
                r"(비교|대비|차이)",
                r"저번\s*달보다",
                r"나아졌",
            ],
        },
        "trend": {
            "keywords": ["추이", "추세", "트렌드", "변화"],
            "patterns": [
                r"(추이|추세|트렌드|변화)",
                r"그래프",
                r"(이번주|지난주|이번달|지난달).*(뭘|무엇|어떤|했)",
            ],
        },
        "kpi": {
            "keywords": ["kpi", "지표", "대시보드", "성과", "리스크"],
            "patterns": [
                r"kpi",
                r"대시보드",
                r"숫자로",
                r"돈\s*(벌|이익)",
                r"(제일|가장)\s*(큰|심각)\s*문제",
            ],
        },
        "yield_status": {
            "keywords": ["수율", "yield", "양품률"],
            "patterns": [
                r"수율.*(얼마|어때|몇)",
            ],
        },
        "greeting": {
            "keywords": ["안녕", "하이", "hi", "hello"],
            "patterns": [r"^안녕", r"^하이", r"^hi", r"^hello"],
        },
        "help": {
            "keywords": ["도움", "help", "사용법", "기능"],
            "patterns": [r"(도움|help|사용법)", r"뭘.*할.*수"],
        },
    }

    def __init__(self, name: str = "keyword"):
        super().__init__(name)
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}

    def initialize(self, examples: List[IntentExample]) -> None:
        """Initialize with examples and compile patterns."""
        self._examples = examples

        # Compile regex patterns for efficiency
        for intent, config in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in config.get("patterns", [])
            ]

        self._initialized = True

    def _expand_synonyms(self, query: str) -> Set[str]:
        """Expand query with synonyms."""
        query_lower = query.lower()
        words = {query_lower}

        for key, synonyms in self.SYNONYMS.items():
            for syn in synonyms:
                if syn in query_lower:
                    words.add(key)
                    words.update(synonyms)

        return words

    def _score_intent(self, query: str, intent: str, expanded_words: Set[str]) -> float:
        """Score an intent for a query."""
        config = self.INTENT_PATTERNS.get(intent, {})
        score = 0.0
        query_lower = query.lower()

        # Keyword matching (+2 per keyword)
        for keyword in config.get("keywords", []):
            if keyword.lower() in query_lower or keyword.lower() in expanded_words:
                score += 2

        # Pattern matching (+3 per pattern)
        for pattern in self._compiled_patterns.get(intent, []):
            if pattern.search(query_lower):
                score += 3

        return score

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
        """Retrieve intents using keyword and pattern matching."""
        if not self._initialized:
            raise RuntimeError("Retriever not initialized. Call initialize() first.")

        expanded = self._expand_synonyms(query)

        # Score all intents
        scores = {}
        for intent in self.INTENT_PATTERNS:
            score = self._score_intent(query, intent, expanded)
            if score > 0:
                scores[intent] = score

        if not scores:
            return [RetrievalResult(intent="unknown", score=0.3)]

        # Normalize scores and sort
        _max_score = max(scores.values())  # noqa: F841 - reserved for future normalization
        results = []
        for intent, score in sorted(scores.items(), key=lambda x: -x[1])[:top_k]:
            # Normalize to 0-1 range
            normalized = min(score / 10.0, 1.0)  # Assume max reasonable score is 10
            results.append(
                RetrievalResult(intent=intent, score=normalized, metadata={"raw_score": score})
            )

        return results

    def add_pattern(self, intent: str, pattern: str) -> None:
        """Add a new pattern to an intent."""
        if intent not in self.INTENT_PATTERNS:
            self.INTENT_PATTERNS[intent] = {"keywords": [], "patterns": []}

        self.INTENT_PATTERNS[intent]["patterns"].append(pattern)

        # Recompile
        if intent not in self._compiled_patterns:
            self._compiled_patterns[intent] = []
        self._compiled_patterns[intent].append(re.compile(pattern, re.IGNORECASE))

    def add_keyword(self, intent: str, keyword: str) -> None:
        """Add a new keyword to an intent."""
        if intent not in self.INTENT_PATTERNS:
            self.INTENT_PATTERNS[intent] = {"keywords": [], "patterns": []}

        self.INTENT_PATTERNS[intent]["keywords"].append(keyword)
