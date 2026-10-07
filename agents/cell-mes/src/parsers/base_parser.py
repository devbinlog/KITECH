"""Base parser for equipment data."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class BaseParser(ABC):
    """Abstract base class for equipment data parsers."""

    @abstractmethod
    def parse(self, raw_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Parse raw equipment data.

        Args:
            raw_data: Raw data from middleware

        Returns:
            Tuple of (parsed_data, status)
            - parsed_data: Normalized data dictionary
            - status: Equipment status (RUN, STOP, ERROR)
        """
        pass
