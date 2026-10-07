"""
Embedding-based retriever using Bi-encoder for semantic search.

Uses sentence-transformers for encoding queries and examples,
then finds similar examples via cosine similarity.
"""

import logging
from typing import List, Optional, Dict
import numpy as np

from .base import BaseRetriever, RetrievalResult, IntentExample, RetrieverRegistry

logger = logging.getLogger(__name__)


@RetrieverRegistry.register_retriever("embedding")
class EmbeddingRetriever(BaseRetriever):
    """
    Semantic retriever using sentence embeddings.

    Models (Korean-friendly):
        - paraphrase-multilingual-MiniLM-L12-v2 (recommended)
        - distiluse-base-multilingual-cased-v1
        - sentence-transformers/LaBSE
    """

    DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(
        self,
        name: str = "embedding",
        model_name: Optional[str] = None,
        device: str = "cpu",
        normalize_embeddings: bool = True,
    ):
        super().__init__(name)
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        self.normalize_embeddings = normalize_embeddings

        self._model = None
        self._example_embeddings: Optional[np.ndarray] = None
        self._intent_labels: List[str] = []
        self._example_queries: List[str] = []

    def initialize(self, examples: List[IntentExample]) -> None:
        """Initialize model and encode all examples."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers required. Install with: pip install sentence-transformers"
            )

        logger.info(f"Loading embedding model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name, device=self.device)

        self._examples = examples
        self._example_queries = [ex.query for ex in examples]
        self._intent_labels = [ex.intent for ex in examples]

        # Encode all examples
        logger.info(f"Encoding {len(examples)} examples...")
        self._example_embeddings = self._model.encode(
            self._example_queries,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )

        self._initialized = True
        logger.info("Embedding retriever initialized")

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
        """Retrieve similar examples using cosine similarity."""
        if not self._initialized or self._model is None:
            raise RuntimeError("Retriever not initialized. Call initialize() first.")

        # Encode query
        query_embedding = self._model.encode(
            query,
            normalize_embeddings=self.normalize_embeddings,
        )

        # Compute cosine similarity
        if self.normalize_embeddings:
            # Dot product = cosine similarity for normalized vectors
            similarities = np.dot(self._example_embeddings, query_embedding)
        else:
            # Manual cosine similarity
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            example_norms = self._example_embeddings / np.linalg.norm(
                self._example_embeddings, axis=1, keepdims=True
            )
            similarities = np.dot(example_norms, query_norm)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][: top_k * 2]  # Get extra for dedup

        # Aggregate by intent (take max score per intent)
        intent_scores: Dict[str, tuple] = {}  # intent -> (score, matched_query)

        for idx in top_indices:
            intent = self._intent_labels[idx]
            score = float(similarities[idx])
            matched = self._example_queries[idx]

            if intent not in intent_scores or score > intent_scores[intent][0]:
                intent_scores[intent] = (score, matched)

        # Sort by score and return top-k
        results = []
        for intent, (score, matched) in sorted(intent_scores.items(), key=lambda x: -x[1][0])[
            :top_k
        ]:
            # Convert similarity to 0-1 range (similarity can be negative)
            normalized_score = (score + 1) / 2  # Map [-1, 1] to [0, 1]
            results.append(
                RetrievalResult(
                    intent=intent,
                    score=normalized_score,
                    matched_query=matched,
                    metadata={"raw_similarity": score},
                )
            )

        return results

    def add_examples(self, examples: List[IntentExample]) -> None:
        """Add more examples and update embeddings."""
        if not self._initialized or self._model is None:
            raise RuntimeError("Retriever not initialized.")

        self._examples.extend(examples)
        new_queries = [ex.query for ex in examples]
        new_intents = [ex.intent for ex in examples]

        # Encode new examples
        new_embeddings = self._model.encode(
            new_queries,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )

        # Append to existing
        self._example_queries.extend(new_queries)
        self._intent_labels.extend(new_intents)
        self._example_embeddings = np.vstack([self._example_embeddings, new_embeddings])

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text."""
        if not self._initialized or self._model is None:
            raise RuntimeError("Retriever not initialized.")

        return self._model.encode(
            text,
            normalize_embeddings=self.normalize_embeddings,
        )
