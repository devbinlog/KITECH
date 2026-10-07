"""
Conversation Manager for NL Router

Manages conversation context and history for natural language queries.
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Single message in a conversation"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    ui_schema: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "intent": self.intent,
            "entities": self.entities,
            "ui_schema": self.ui_schema,
        }


@dataclass
class ConversationContext:
    """Context for a single conversation session"""

    session_id: str
    user_id: Optional[str] = None
    messages: deque = field(default_factory=lambda: deque(maxlen=50))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active_entities: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: ConversationMessage):
        """Add message to conversation history"""
        self.messages.append(message)
        self.last_activity = datetime.now(timezone.utc)

        # Update active entities from message
        if message.entities:
            self.active_entities.update(message.entities)

    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        """Get recent messages"""
        messages = list(self.messages)
        return messages[-count:] if len(messages) > count else messages

    def get_context_summary(self) -> str:
        """Get summary of conversation context for LLM prompting"""
        if not self.messages:
            return ""

        recent = self.get_recent_messages(5)
        summary_parts = []

        for msg in recent:
            role_label = "User" if msg.role == "user" else "Assistant"
            summary_parts.append(f"{role_label}: {msg.content[:200]}")

        context = "\n".join(summary_parts)

        if self.active_entities:
            entities_str = ", ".join(f"{k}={v}" for k, v in self.active_entities.items())
            context += f"\n\nActive entities: {entities_str}"

        return context

    def get_active_entity(self, key: str) -> Optional[Any]:
        """Get an active entity value"""
        return self.active_entities.get(key)

    def clear_entities(self):
        """Clear active entities"""
        self.active_entities.clear()

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if context has expired due to inactivity"""
        elapsed = datetime.now(timezone.utc) - self.last_activity
        return elapsed > timedelta(minutes=timeout_minutes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "active_entities": self.active_entities,
            "preferences": self.preferences,
        }


class ConversationManager:
    """
    Manages multiple conversation contexts

    Usage:
        manager = ConversationManager()

        # Get or create context
        context = manager.get_context("session_123", "user_456")

        # Add messages
        manager.add_user_message("session_123", "오늘 생산 현황 보여줘")
        manager.add_assistant_message("session_123", "오늘 생산 현황입니다.",
                                      intent="PRODUCTION_STATUS",
                                      entities={"date": "today"})

        # Get context for prompting
        summary = context.get_context_summary()
    """

    def __init__(
        self,
        max_contexts: int = 1000,
        context_timeout_minutes: int = 30,
        cleanup_interval_seconds: int = 300,
    ):
        self._contexts: Dict[str, ConversationContext] = {}
        self._max_contexts = max_contexts
        self._context_timeout = context_timeout_minutes
        self._cleanup_interval = cleanup_interval_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        # Single threading.RLock protects all _contexts mutations.
        # Using a threading lock (not asyncio.Lock) so both async cleanup
        # and sync get_context/add_*_message callers share the same guard,
        # eliminating the TOCTOU race that existed when two different locks were used.
        self._lock = threading.RLock()

    async def start(self):
        """Start background cleanup task"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Conversation manager started")

    async def stop(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Conversation manager stopped")

    async def _cleanup_loop(self):
        """Periodically clean up expired contexts"""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            await self._cleanup_expired_contexts()

    async def _cleanup_expired_contexts(self):
        """Remove expired conversation contexts"""
        with self._lock:
            expired = [
                session_id
                for session_id, context in self._contexts.items()
                if context.is_expired(self._context_timeout)
            ]

            for session_id in expired:
                del self._contexts[session_id]

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired conversation contexts")

    def get_context(self, session_id: str, user_id: Optional[str] = None) -> ConversationContext:
        """Get or create conversation context"""
        with self._lock:
            if session_id not in self._contexts:
                # Check max contexts limit
                if len(self._contexts) >= self._max_contexts:
                    # User-scoped LRU eviction: prefer evicting the oldest context
                    # belonging to a user who has multiple active sessions, so that
                    # single-session users are not unfairly displaced.
                    target_user_id = user_id
                    candidate = None
                    if target_user_id:
                        # Find oldest context belonging to the same user (other session)
                        user_contexts = [
                            (sid, ctx)
                            for sid, ctx in self._contexts.items()
                            if ctx.user_id == target_user_id
                        ]
                        if user_contexts:
                            candidate = min(user_contexts, key=lambda x: x[1].last_activity)
                    if candidate is None:
                        # Fall back to globally oldest context
                        candidate = min(self._contexts.items(), key=lambda x: x[1].last_activity)
                    del self._contexts[candidate[0]]
                    logger.debug(f"Evicted oldest context: {candidate[0]} (user={candidate[1].user_id})")

                self._contexts[session_id] = ConversationContext(session_id=session_id, user_id=user_id)
                logger.info(f"Created new conversation context: {session_id}")

            return self._contexts[session_id]

    def add_user_message(
        self, session_id: str, content: str, entities: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add user message to conversation"""
        context = self.get_context(session_id)

        message = ConversationMessage(role="user", content=content, entities=entities or {})

        context.add_message(message)
        return message

    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        ui_schema: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Add assistant message to conversation"""
        context = self.get_context(session_id)

        message = ConversationMessage(
            role="assistant",
            content=content,
            intent=intent,
            entities=entities or {},
            ui_schema=ui_schema,
            metadata=metadata or {},
        )

        context.add_message(message)
        return message

    def get_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if session_id not in self._contexts:
            return []

        context = self._contexts[session_id]
        messages = context.get_recent_messages(limit)
        return [m.to_dict() for m in messages]

    def clear_context(self, session_id: str):
        """Clear a conversation context"""
        if session_id in self._contexts:
            del self._contexts[session_id]
            logger.info(f"Cleared conversation context: {session_id}")

    def get_status(self) -> Dict[str, Any]:
        """Get conversation manager status"""
        return {
            "total_contexts": len(self._contexts),
            "max_contexts": self._max_contexts,
            "timeout_minutes": self._context_timeout,
            "contexts": [
                {
                    "session_id": ctx.session_id,
                    "user_id": ctx.user_id,
                    "message_count": len(ctx.messages),
                    "last_activity": ctx.last_activity.isoformat(),
                    "active_entities": list(ctx.active_entities.keys()),
                }
                for ctx in self._contexts.values()
            ],
        }


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get global conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
