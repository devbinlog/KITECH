"""
Cross-encoder re-ranker for improved accuracy.

Cross-encoders process query-document pairs together,
allowing for richer interactions than bi-encoders.
Much slower but more accurate - use for re-ranking top candidates.
"""

import logging
from typing import List, Optional, Dict

from .base import BaseRanker, RetrievalResult, RetrieverRegistry

logger = logging.getLogger(__name__)


@RetrieverRegistry.register_ranker("cross_encoder")
class CrossEncoderRanker(BaseRanker):
    """
    Re-ranker using Cross-encoder models.

    Architecture:
        Query + Candidate → [CLS] Query [SEP] Candidate [SEP] → Score

    Models:
        - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, English)
        - cross-encoder/ms-marco-MiniLM-L-12-v2 (balanced)
        - cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (multilingual!)
    """

    # Multilingual model that works with Korean
    DEFAULT_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    def __init__(
        self,
        name: str = "cross_encoder",
        model_name: Optional[str] = None,
        device: str = "cpu",
        max_length: int = 256,
    ):
        super().__init__(name)
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        self.max_length = max_length

        self._model = None

        # Intent descriptions for re-ranking
        # Cross-encoder compares query against these descriptions
        self._intent_descriptions: Dict[str, str] = {
            "daily_status": "오늘 생산 현황, 일일 실적, 생산량, 양품/불량 수량",
            "production_count": "생산량, 몇 개 만들었는지, 수량 조회",
            "current_status": "현재 가동 상태, 지금 돌아가는 것, 실시간 현황",
            "compare_status": "어제와 오늘 비교, 전일 대비, 실적 비교",
            "trend": "추이, 추세, 기간별 변화, 그래프, 지난주/지난달 분석",
            "equipment_status": "설비 상태, 장비 가동률, 기계 현황, 병목",
            "equipment_error": "설비 고장, 에러, 알람, 기계 이상, 문제",
            "equipment_idle": "유휴 설비, 대기중 장비, 사용 가능한 기계",
            "yield_status": "수율, 양품률, 품질 지표",
            "defect_analysis": "불량 분석, NG 현황, 클레임, 반품, 품질 문제",
            "lot_trace": "LOT 이력 추적, 로트 조회, 제품 추적",
            "work_orders": "작업지시, 오더 현황, 할 일 목록",
            "work_orders_in_progress": "진행중인 작업, 지금 하고 있는 작업",
            "work_orders_pending": "대기 작업, 다음 할 일, 예정 작업",
            "work_orders_completed": "완료된 작업, 끝난 작업",
            "schedule": "스케줄, 일정, 납기, 출하 계획",
            "schedule_delay": "지연 작업, 늦어진 일정, 납기 위험",
            "kpi": "KPI 지표, 대시보드, 성과, 핵심 지표",
            "report": "리포트, 보고서, 실적 요약",
            "greeting": "인사, 안녕",
            "help": "도움말, 사용법, 기능 안내",
            "unknown": "알 수 없는 질문",
        }

    def initialize(self) -> None:
        """Load the cross-encoder model."""
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "sentence-transformers required. Install with: pip install sentence-transformers"
            )

        logger.info(f"Loading cross-encoder model: {self.model_name}")
        self._model = CrossEncoder(
            self.model_name,
            device=self.device,
            max_length=self.max_length,
        )

        self._initialized = True
        logger.info("Cross-encoder ranker initialized")

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_k: int = 5,
        use_descriptions: bool = True,
        **kwargs,
    ) -> List[RetrievalResult]:
        """
        Re-rank candidates using cross-encoder.

        Args:
            query: User query
            candidates: Initial retrieval results
            top_k: Number of results to return
            use_descriptions: If True, compare against intent descriptions.
                            If False, compare against matched_query if available.

        Returns:
            Re-ranked results
        """
        if not self._initialized or self._model is None:
            raise RuntimeError("Ranker not initialized. Call initialize() first.")

        if not candidates:
            return []

        # Prepare pairs for cross-encoder
        pairs = []
        for candidate in candidates:
            if use_descriptions:
                # Compare query against intent description
                description = self._intent_descriptions.get(
                    candidate.intent, candidate.matched_query or candidate.intent
                )
            else:
                # Compare query against matched example query
                description = candidate.matched_query or self._intent_descriptions.get(
                    candidate.intent, candidate.intent
                )

            pairs.append((query, description))

        # Get cross-encoder scores
        scores = self._model.predict(pairs)

        # Combine with original scores (weighted)
        # Cross-encoder score is more reliable, so give it more weight
        original_weight = kwargs.get("original_weight", 0.3)
        cross_weight = 1.0 - original_weight

        results = []
        for i, candidate in enumerate(candidates):
            # Normalize cross-encoder score to 0-1
            # Cross-encoder scores can be any range, use sigmoid
            ce_score = self._sigmoid(float(scores[i]))

            # Weighted combination
            combined_score = original_weight * candidate.score + cross_weight * ce_score

            results.append(
                RetrievalResult(
                    intent=candidate.intent,
                    score=combined_score,
                    matched_query=candidate.matched_query,
                    metadata={
                        **candidate.metadata,
                        "original_score": candidate.score,
                        "cross_encoder_score": ce_score,
                        "raw_ce_score": float(scores[i]),
                    },
                )
            )

        # Sort by combined score
        results.sort(key=lambda x: -x.score)

        return results[:top_k]

    def _sigmoid(self, x: float) -> float:
        """Sigmoid function for normalizing scores."""
        import math

        try:
            return 1 / (1 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0

    def set_intent_description(self, intent: str, description: str) -> None:
        """Update or add an intent description."""
        self._intent_descriptions[intent] = description

    def get_intent_descriptions(self) -> Dict[str, str]:
        """Get all intent descriptions."""
        return self._intent_descriptions.copy()
