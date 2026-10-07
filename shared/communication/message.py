"""Message definitions for inter-agent communication."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
from datetime import datetime, timezone


class MessageType(Enum):
    """Message types for agent communication."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"


@dataclass
class Message:
    """Message for inter-agent communication."""

    sender: str
    receiver: str
    message_type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: str = ""

    def __post_init__(self):
        """Generate message ID if not provided."""
        if not self.message_id:
            import uuid

            self.message_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
        }
