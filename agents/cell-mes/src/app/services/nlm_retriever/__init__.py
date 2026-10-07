"""
NLM Retriever Module

Pluggable retrieval and re-ranking system for Natural Language MES queries.
Supports multiple retrieval strategies without LLM dependency.

Architecture:
    Query → Retriever(s) → Ranker(s) → Top-K Results

Available Components:
    - KeywordRetriever: Rule-based pattern matching (current NLM)
    - EmbeddingRetriever: Bi-encoder semantic search
    - BM25Retriever: Sparse keyword search
    - HybridRetriever: BM25 + Dense with RRF fusion
    - CrossEncoderRanker: Re-ranking with cross-encoder
    - Pipeline: Compose retriever + ranker chains
"""

from .base import (
    BaseRetriever,
    BaseRanker,
    RetrievalResult,
    IntentExample,
)
from .pipeline import RetrievalPipeline
from .keyword_retriever import KeywordRetriever
from .embedding_retriever import EmbeddingRetriever
from .cross_encoder_ranker import CrossEncoderRanker
from .hybrid_retriever import HybridRetriever, BM25Retriever

__all__ = [
    # Base classes
    "BaseRetriever",
    "BaseRanker",
    "RetrievalResult",
    "IntentExample",
    # Retrievers
    "KeywordRetriever",
    "EmbeddingRetriever",
    "BM25Retriever",
    "HybridRetriever",
    # Rankers
    "CrossEncoderRanker",
    # Pipeline
    "RetrievalPipeline",
]
