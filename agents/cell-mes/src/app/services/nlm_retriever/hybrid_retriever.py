"""
Hybrid retrieval combining sparse (BM25) and dense (embedding) search.

Uses Reciprocal Rank Fusion (RRF) to combine results from multiple retrievers.
"""

import logging
from typing import List, Optional, Dict
from collections import defaultdict

from .base import BaseRetriever, RetrievalResult, IntentExample, RetrieverRegistry

logger = logging.getLogger(__name__)


@RetrieverRegistry.register_retriever("bm25")
class BM25Retriever(BaseRetriever):
    """
    BM25-based sparse retriever.

    Good for exact keyword matching, complements dense retrieval.
    """

    def __init__(
        self,
        name: str = "bm25",
        k1: float = 1.5,
        b: float = 0.75,
    ):
        super().__init__(name)
        self.k1 = k1
        self.b = b

        self._tokenized_examples: List[List[str]] = []
        self._intent_labels: List[str] = []
        self._example_queries: List[str] = []
        self._bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for Korean + English."""
        import re

        # Split on whitespace and punctuation, keep Korean characters together
        tokens = re.findall(r"[가-힣]+|[a-zA-Z]+|[0-9]+", text.lower())
        return tokens

    def initialize(self, examples: List[IntentExample]) -> None:
        """Initialize BM25 index."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("rank-bm25 required. Install with: pip install rank-bm25")

        self._examples = examples
        self._example_queries = [ex.query for ex in examples]
        self._intent_labels = [ex.intent for ex in examples]

        # Tokenize all examples
        self._tokenized_examples = [self._tokenize(query) for query in self._example_queries]

        # Build BM25 index
        self._bm25 = BM25Okapi(
            self._tokenized_examples,
            k1=self.k1,
            b=self.b,
        )

        self._initialized = True
        logger.info(f"BM25 retriever initialized with {len(examples)} examples")

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
        """Retrieve using BM25 scoring."""
        if not self._initialized or self._bm25 is None:
            raise RuntimeError("Retriever not initialized.")

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # Get top indices
        top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])

        # Aggregate by intent
        intent_scores: Dict[str, tuple] = {}
        for idx in top_indices:
            intent = self._intent_labels[idx]
            score = float(scores[idx])
            matched = self._example_queries[idx]

            if intent not in intent_scores or score > intent_scores[intent][0]:
                intent_scores[intent] = (score, matched)

        # Normalize and return
        if not intent_scores:
            return [RetrievalResult(intent="unknown", score=0.3)]

        max_score = max(s[0] for s in intent_scores.values())
        results = []

        for intent, (score, matched) in sorted(intent_scores.items(), key=lambda x: -x[1][0])[
            :top_k
        ]:
            normalized = score / max_score if max_score > 0 else 0
            results.append(
                RetrievalResult(
                    intent=intent,
                    score=normalized,
                    matched_query=matched,
                    metadata={"bm25_score": score},
                )
            )

        return results


@RetrieverRegistry.register_retriever("hybrid")
class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever combining multiple retrievers with RRF.

    Reciprocal Rank Fusion formula:
        RRF(d) = Σ 1 / (k + rank(d))

    where k is a constant (default 60) and rank is the position in each list.
    """

    def __init__(
        self,
        name: str = "hybrid",
        retrievers: Optional[List[BaseRetriever]] = None,
        rrf_k: int = 60,
        weights: Optional[List[float]] = None,
    ):
        super().__init__(name)
        self.retrievers = retrievers or []
        self.rrf_k = rrf_k
        self.weights = weights  # Optional weights for each retriever

    def add_retriever(self, retriever: BaseRetriever, weight: float = 1.0) -> None:
        """Add a retriever to the ensemble."""
        self.retrievers.append(retriever)
        if self.weights is None:
            self.weights = [1.0] * len(self.retrievers)
        else:
            self.weights.append(weight)

    def initialize(self, examples: List[IntentExample]) -> None:
        """Initialize all sub-retrievers."""
        self._examples = examples

        for retriever in self.retrievers:
            if not retriever.is_initialized:
                retriever.initialize(examples)

        self._initialized = True
        logger.info(f"Hybrid retriever initialized with {len(self.retrievers)} sub-retrievers")

    def retrieve(
        self, query: str, top_k: int = 5, retriever_top_k: int = 10, **kwargs
    ) -> List[RetrievalResult]:
        """
        Retrieve from all sub-retrievers and fuse with RRF.

        Args:
            query: User query
            top_k: Final number of results
            retriever_top_k: Results to get from each retriever
        """
        if not self._initialized:
            raise RuntimeError("Retriever not initialized.")

        if not self.retrievers:
            return [RetrievalResult(intent="unknown", score=0.3)]

        # Get results from all retrievers
        all_results: List[List[RetrievalResult]] = []
        for retriever in self.retrievers:
            try:
                results = retriever.retrieve(query, top_k=retriever_top_k, **kwargs)
                all_results.append(results)
            except Exception as e:
                logger.warning(f"Retriever {retriever.name} failed: {e}")
                all_results.append([])

        # Apply RRF
        rrf_scores: Dict[str, float] = defaultdict(float)
        intent_metadata: Dict[str, Dict] = {}

        weights = self.weights or [1.0] * len(all_results)

        for i, results in enumerate(all_results):
            weight = weights[i] if i < len(weights) else 1.0

            for rank, result in enumerate(results, start=1):
                # RRF score: weight * 1/(k + rank)
                rrf_scores[result.intent] += weight / (self.rrf_k + rank)

                # Keep best matched query and metadata
                if result.intent not in intent_metadata:
                    intent_metadata[result.intent] = {
                        "matched_query": result.matched_query,
                        "source_scores": {},
                    }
                intent_metadata[result.intent]["source_scores"][self.retrievers[i].name] = (
                    result.score
                )

        if not rrf_scores:
            return [RetrievalResult(intent="unknown", score=0.3)]

        # Normalize RRF scores
        max_rrf = max(rrf_scores.values())

        results = []
        for intent, score in sorted(rrf_scores.items(), key=lambda x: -x[1])[:top_k]:
            normalized = score / max_rrf if max_rrf > 0 else 0
            meta = intent_metadata.get(intent, {})

            results.append(
                RetrievalResult(
                    intent=intent,
                    score=normalized,
                    matched_query=meta.get("matched_query"),
                    metadata={
                        "rrf_score": score,
                        "source_scores": meta.get("source_scores", {}),
                    },
                )
            )

        return results

    @classmethod
    def create_default(
        cls,
        examples: List[IntentExample],
        use_bm25: bool = True,
        use_embedding: bool = True,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu",
    ) -> "HybridRetriever":
        """
        Create a default hybrid retriever with BM25 + Embedding.

        Args:
            examples: Training examples
            use_bm25: Include BM25 retriever
            use_embedding: Include embedding retriever
            embedding_model: Model for embedding retriever
            device: Device for embedding model

        Returns:
            Initialized HybridRetriever
        """
        from .embedding_retriever import EmbeddingRetriever

        hybrid = cls(name="hybrid_default")

        if use_bm25:
            bm25 = BM25Retriever()
            hybrid.add_retriever(bm25, weight=0.4)

        if use_embedding:
            embedding = EmbeddingRetriever(
                model_name=embedding_model,
                device=device,
            )
            hybrid.add_retriever(embedding, weight=0.6)

        hybrid.initialize(examples)

        return hybrid
