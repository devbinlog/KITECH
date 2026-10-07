"""Base class for all agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """Initialize the agent.

        Args:
            name: Agent name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}

    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data to process

        Returns:
            Processing result dictionary
        """
        pass

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        return True
