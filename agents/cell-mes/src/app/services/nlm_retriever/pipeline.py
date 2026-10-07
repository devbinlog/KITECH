"""
Retrieval Pipeline for composing retrievers and rankers.

Supports:
    - Single retriever
    - Retriever + Ranker chain
    - Multiple retrievers with fusion + Ranker
    - Fallback chains
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .base import (
    BaseRetriever,
    BaseRanker,
    RetrievalResult,
    IntentExample,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for retrieval pipeline."""

    # Retriever settings
    retriever_type: str = "keyword"  # keyword, embedding, bm25, hybrid
    retriever_top_k: int = 10
    retriever_kwargs: Dict[str, Any] = field(default_factory=dict)

    # Ranker settings (optional)
    ranker_type: Optional[str] = None  # None, cross_encoder
    ranker_top_k: int = 5
    ranker_kwargs: Dict[str, Any] = field(default_factory=dict)

    # Fallback
    fallback_retriever_type: Optional[str] = None
    min_confidence: float = 0.3  # Use fallback if below this

    # General
    device: str = "cpu"

    @classmethod
    def default_keyword(cls) -> "PipelineConfig":
        """Default config using keyword retriever only (fast, no ML)."""
        return cls(retriever_type="keyword")

    @classmethod
    def default_semantic(cls, device: str = "cpu") -> "PipelineConfig":
        """Default config using embedding retriever."""
        return cls(
            retriever_type="embedding",
            retriever_kwargs={"device": device},
            device=device,
        )

    @classmethod
    def default_hybrid_rerank(cls, device: str = "cpu") -> "PipelineConfig":
        """Default config: Hybrid retrieval + Cross-encoder re-ranking."""
        return cls(
            retriever_type="hybrid",
            retriever_top_k=20,
            retriever_kwargs={"device": device},
            ranker_type="cross_encoder",
            ranker_top_k=5,
            ranker_kwargs={"device": device},
            device=device,
        )


class RetrievalPipeline:
    """
    Composable retrieval pipeline.

    Usage:
        # Simple keyword retrieval
        pipeline = RetrievalPipeline.from_config(PipelineConfig.default_keyword())
        pipeline.initialize(examples)
        results = pipeline.retrieve("오늘 생산 현황")

        # Hybrid + Re-ranking
        config = PipelineConfig.default_hybrid_rerank(device="cuda")
        pipeline = RetrievalPipeline.from_config(config)
        pipeline.initialize(examples)
        results = pipeline.retrieve("오늘 생산 현황")
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        ranker: Optional[BaseRanker] = None,
        fallback_retriever: Optional[BaseRetriever] = None,
        min_confidence: float = 0.3,
    ):
        self.retriever = retriever
        self.ranker = ranker
        self.fallback_retriever = fallback_retriever
        self.min_confidence = min_confidence

        self._initialized = False
        self._examples: List[IntentExample] = []

    def initialize(self, examples: List[IntentExample]) -> None:
        """Initialize all components with examples."""
        self._examples = examples

        # Initialize retriever
        if not self.retriever.is_initialized:
            logger.info(f"Initializing retriever: {self.retriever.name}")
            self.retriever.initialize(examples)

        # Initialize fallback
        if self.fallback_retriever and not self.fallback_retriever.is_initialized:
            logger.info(f"Initializing fallback: {self.fallback_retriever.name}")
            self.fallback_retriever.initialize(examples)

        # Initialize ranker
        if self.ranker and not self.ranker.is_initialized:
            logger.info(f"Initializing ranker: {self.ranker.name}")
            self.ranker.initialize()

        self._initialized = True
        logger.info("Pipeline initialized")

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
        """
        Run the retrieval pipeline.

        Args:
            query: User query
            top_k: Number of results to return

        Returns:
            List of RetrievalResult
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        # Step 1: Initial retrieval
        retriever_top_k = kwargs.get("retriever_top_k", top_k * 2)
        results = self.retriever.retrieve(query, top_k=retriever_top_k)

        # Step 2: Check if we need fallback
        if self.fallback_retriever and results:
            if results[0].score < self.min_confidence:
                logger.info(f"Low confidence ({results[0].score:.2f}), trying fallback")
                fallback_results = self.fallback_retriever.retrieve(query, top_k=retriever_top_k)
                # Merge results, preferring higher scores
                results = self._merge_results(results, fallback_results, top_k=retriever_top_k)

        # Step 3: Re-ranking
        if self.ranker and results:
            logger.debug(f"Re-ranking {len(results)} candidates")
            results = self.ranker.rerank(query, results, top_k=top_k, **kwargs)
        else:
            results = results[:top_k]

        return results

    def _merge_results(
        self,
        primary: List[RetrievalResult],
        secondary: List[RetrievalResult],
        top_k: int,
    ) -> List[RetrievalResult]:
        """Merge results from two retrievers, keeping best scores per intent."""
        intent_best: Dict[str, RetrievalResult] = {}

        for result in primary + secondary:
            if result.intent not in intent_best:
                intent_best[result.intent] = result
            elif result.score > intent_best[result.intent].score:
                intent_best[result.intent] = result

        merged = sorted(intent_best.values(), key=lambda x: -x.score)
        return merged[:top_k]

    def get_best_intent(self, query: str, **kwargs) -> tuple[str, float]:
        """
        Get the single best intent and confidence.

        Returns:
            (intent, confidence) tuple
        """
        results = self.retrieve(query, top_k=1, **kwargs)
        if results:
            return results[0].intent, results[0].score
        return "unknown", 0.0

    @classmethod
    def from_config(cls, config: PipelineConfig) -> "RetrievalPipeline":
        """
        Create a pipeline from configuration.

        Args:
            config: PipelineConfig object

        Returns:
            Uninitialized RetrievalPipeline (call initialize() with examples)
        """
        # Create retriever
        retriever = cls._create_retriever(
            config.retriever_type,
            config.device,
            config.retriever_kwargs,
        )

        # Create ranker
        ranker = None
        if config.ranker_type:
            ranker = cls._create_ranker(
                config.ranker_type,
                config.device,
                config.ranker_kwargs,
            )

        # Create fallback
        fallback = None
        if config.fallback_retriever_type:
            fallback = cls._create_retriever(
                config.fallback_retriever_type,
                config.device,
                {},
            )

        return cls(
            retriever=retriever,
            ranker=ranker,
            fallback_retriever=fallback,
            min_confidence=config.min_confidence,
        )

    @staticmethod
    def _create_retriever(
        retriever_type: str,
        device: str,
        kwargs: Dict[str, Any],
    ) -> BaseRetriever:
        """Create a retriever instance."""
        from .keyword_retriever import KeywordRetriever
        from .embedding_retriever import EmbeddingRetriever
        from .hybrid_retriever import BM25Retriever, HybridRetriever

        # Remove device from kwargs to avoid duplication
        kwargs = {k: v for k, v in kwargs.items() if k != "device"}

        if retriever_type == "keyword":
            return KeywordRetriever(**kwargs)
        elif retriever_type == "embedding":
            return EmbeddingRetriever(device=device, **kwargs)
        elif retriever_type == "bm25":
            return BM25Retriever(**kwargs)
        elif retriever_type == "hybrid":
            # Create default hybrid with BM25 + Embedding
            hybrid = HybridRetriever()
            hybrid.add_retriever(BM25Retriever(), weight=0.4)
            hybrid.add_retriever(
                EmbeddingRetriever(device=device),
                weight=0.6,
            )
            return hybrid
        else:
            raise ValueError(f"Unknown retriever type: {retriever_type}")

    @staticmethod
    def _create_ranker(
        ranker_type: str,
        device: str,
        kwargs: Dict[str, Any],
    ) -> BaseRanker:
        """Create a ranker instance."""
        from .cross_encoder_ranker import CrossEncoderRanker

        # Remove device from kwargs to avoid duplication
        kwargs = {k: v for k, v in kwargs.items() if k != "device"}

        if ranker_type == "cross_encoder":
            return CrossEncoderRanker(device=device, **kwargs)
        else:
            raise ValueError(f"Unknown ranker type: {ranker_type}")

    def __repr__(self) -> str:
        parts = [f"retriever={self.retriever.name}"]
        if self.ranker:
            parts.append(f"ranker={self.ranker.name}")
        if self.fallback_retriever:
            parts.append(f"fallback={self.fallback_retriever.name}")
        return f"RetrievalPipeline({', '.join(parts)})"
