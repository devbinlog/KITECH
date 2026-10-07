"""
Base classes for NLM retrieval system.

Defines abstract interfaces for retrievers and rankers,
allowing pluggable implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class IntentType(str, Enum):
    """Supported intent types."""

    DAILY_STATUS = "daily_status"
    PRODUCTION_COUNT = "production_count"
    CURRENT_STATUS = "current_status"
    COMPARE_STATUS = "compare_status"
    TREND = "trend"
    EQUIPMENT_STATUS = "equipment_status"
    EQUIPMENT_ERROR = "equipment_error"
    EQUIPMENT_IDLE = "equipment_idle"
    YIELD_STATUS = "yield_status"
    DEFECT_ANALYSIS = "defect_analysis"
    LOT_TRACE = "lot_trace"
    WORK_ORDERS = "work_orders"
    WORK_ORDERS_IN_PROGRESS = "work_orders_in_progress"
    WORK_ORDERS_PENDING = "work_orders_pending"
    WORK_ORDERS_COMPLETED = "work_orders_completed"
    SCHEDULE = "schedule"
    SCHEDULE_DELAY = "schedule_delay"
    KPI = "kpi"
    REPORT = "report"
    GREETING = "greeting"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class IntentExample:
    """An example query with its intent label."""

    query: str
    intent: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional: pre-computed embedding (set by retriever)
    embedding: Optional[List[float]] = field(default=None, repr=False)


@dataclass
class RetrievalResult:
    """Result from retrieval or re-ranking."""

    intent: str
    score: float
    matched_query: Optional[str] = None  # The example query that matched
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure score is between 0 and 1
        self.score = max(0.0, min(1.0, self.score))


class BaseRetriever(ABC):
    """
    Abstract base class for retrievers.

    A retriever takes a query and returns candidate intents with scores.
    """

    def __init__(self, name: str = "base"):
        self.name = name
        self._examples: List[IntentExample] = []
        self._initialized = False

    @abstractmethod
    def initialize(self, examples: List[IntentExample]) -> None:
        """
        Initialize the retriever with example queries.

        Args:
            examples: List of IntentExample objects
        """
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[RetrievalResult]:
        """
        Retrieve top-k intent candidates for a query.

        Args:
            query: User's natural language query
            top_k: Number of results to return

        Returns:
            List of RetrievalResult sorted by score descending
        """
        pass

    def add_examples(self, examples: List[IntentExample]) -> None:
        """Add more examples after initialization."""
        self._examples.extend(examples)
        # Subclasses should override to update their index

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, examples={len(self._examples)})"


class BaseRanker(ABC):
    """
    Abstract base class for re-rankers.

    A ranker takes retrieval results and re-orders them for better accuracy.
    """

    def __init__(self, name: str = "base"):
        self.name = name
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the ranker (load models, etc.)."""
        pass

    @abstractmethod
    def rerank(
        self, query: str, candidates: List[RetrievalResult], top_k: int = 5, **kwargs
    ) -> List[RetrievalResult]:
        """
        Re-rank candidate results.

        Args:
            query: Original user query
            candidates: Results from retriever
            top_k: Number of results to return

        Returns:
            Re-ranked list of RetrievalResult
        """
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class RetrieverRegistry:
    """Registry for retriever and ranker implementations."""

    _retrievers: Dict[str, type] = {}
    _rankers: Dict[str, type] = {}

    @classmethod
    def register_retriever(cls, name: str):
        """Decorator to register a retriever class."""

        def decorator(klass):
            cls._retrievers[name] = klass
            return klass

        return decorator

    @classmethod
    def register_ranker(cls, name: str):
        """Decorator to register a ranker class."""

        def decorator(klass):
            cls._rankers[name] = klass
            return klass

        return decorator

    @classmethod
    def get_retriever(cls, name: str) -> type:
        if name not in cls._retrievers:
            raise ValueError(
                f"Unknown retriever: {name}. Available: {list(cls._retrievers.keys())}"
            )
        return cls._retrievers[name]

    @classmethod
    def get_ranker(cls, name: str) -> type:
        if name not in cls._rankers:
            raise ValueError(f"Unknown ranker: {name}. Available: {list(cls._rankers.keys())}")
        return cls._rankers[name]

    @classmethod
    def list_retrievers(cls) -> List[str]:
        return list(cls._retrievers.keys())

    @classmethod
    def list_rankers(cls) -> List[str]:
        return list(cls._rankers.keys())
