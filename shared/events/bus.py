"""
Redis-based event bus for service communication.

Provides pub/sub functionality with:
- Automatic reconnection
- Connection pooling
- JSON serialization
- Type-safe event handling
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from .base import Event

logger = logging.getLogger(__name__)

# Type variable for event handlers
E = TypeVar("E", bound=Event)
EventHandler = Callable[[Event], Any]


class EventBus:
    """
    Redis-based event bus for publishing and subscribing to domain events.

    Features:
    - Async pub/sub using Redis
    - Automatic JSON serialization
    - Connection pooling
    - Graceful reconnection
    - Pattern-based subscriptions

    Example:
        bus = EventBus("redis://localhost:6379")
        await bus.connect()

        # Subscribe to events
        async def handle_order(event: WorkOrderCreatedEvent):
            print(f"New order: {event.lot_no}")

        bus.subscribe("work_order.created", handle_order)

        # Publish events
        event = WorkOrderCreatedEvent(work_order_id=1, lot_no="LOT-001", ...)
        await bus.publish(event)

        # Start listening
        await bus.start_listening()
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_connections: int = 10,
        decode_responses: bool = True,
        source_service: str = "",
    ):
        """
        Initialize the event bus.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
            decode_responses: Whether to decode Redis responses
            source_service: Service name for event metadata
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self.source_service = source_service

        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """
        Establish connection to Redis.

        Creates a connection pool for efficient connection reuse.
        """
        if self._client is not None:
            return

        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            self._pubsub = self._client.pubsub()

            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Close Redis connection and cleanup.
        """
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None

        if self._client:
            await self._client.close()
            self._client = None

        if self._pool:
            await self._pool.disconnect()
            self._pool = None

        logger.info("Disconnected from Redis")

    async def publish(self, event: Event) -> int:
        """
        Publish an event to Redis.

        Args:
            event: Event to publish

        Returns:
            Number of subscribers that received the message
        """
        if self._client is None:
            await self.connect()

        # Add source service to metadata
        if self.source_service and not event.metadata.source_service:
            event = event.with_source(self.source_service)

        channel = event.to_channel()
        message = event.model_dump_json()

        try:
            subscribers = await self._client.publish(channel, message)
            logger.debug(f"Published {event.event_type} to {subscribers} subscribers")
            return subscribers

        except redis.ConnectionError as e:
            logger.error(f"Failed to publish event: {e}")
            # Try to reconnect
            await self._reconnect()
            return await self._client.publish(channel, message)

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        event_class: Optional[Type[Event]] = None,
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to (e.g., "work_order.created")
            handler: Async function to handle the event
            event_class: Optional event class for deserialization
        """
        channel = f"events:{event_type}"

        if channel not in self._handlers:
            self._handlers[channel] = []

        # Wrap handler to deserialize event
        async def wrapped_handler(message: Dict[str, Any]) -> None:
            try:
                if event_class:
                    event = event_class.model_validate_json(message["data"])
                else:
                    event = Event.model_validate_json(message["data"])

                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result

            except Exception as e:
                logger.exception(f"Error in event handler for {event_type}: {e}")

        self._handlers[channel].append(wrapped_handler)
        logger.debug(f"Subscribed to {event_type}")

    def subscribe_pattern(self, pattern: str, handler: EventHandler) -> None:
        """
        Subscribe to events matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "work_order.*", "*.created")
            handler: Async function to handle events
        """
        channel_pattern = f"events:{pattern}"

        if channel_pattern not in self._handlers:
            self._handlers[channel_pattern] = []

        self._handlers[channel_pattern].append(handler)
        logger.debug(f"Subscribed to pattern {pattern}")

    async def start_listening(self) -> None:
        """
        Start listening for events.

        This starts a background task that processes incoming messages.
        Call disconnect() to stop listening.
        """
        if self._running:
            return

        if self._client is None:
            await self.connect()

        # Subscribe to all registered channels
        channels = [ch for ch in self._handlers.keys() if "*" not in ch]
        patterns = [ch for ch in self._handlers.keys() if "*" in ch]

        if channels:
            await self._pubsub.subscribe(*channels)
        if patterns:
            await self._pubsub.psubscribe(*patterns)

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info(f"Started listening on {len(channels)} channels, {len(patterns)} patterns")

    async def _listen_loop(self) -> None:
        """
        Main event listening loop.
        """
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message is not None:
                    await self._handle_message(message)

            except redis.ConnectionError:
                logger.warning("Lost connection to Redis, reconnecting...")
                await self._reconnect()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.exception(f"Error in listen loop: {e}")
                await asyncio.sleep(1.0)

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Process a received message.
        """
        msg_type = message.get("type")

        if msg_type == "message":
            channel = message.get("channel", "")
            handlers = self._handlers.get(channel, [])

        elif msg_type == "pmessage":
            pattern = message.get("pattern", "")
            handlers = self._handlers.get(pattern, [])
        else:
            return

        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.exception(f"Handler error: {e}")

    async def _reconnect(self, max_retries: int = 5, delay: float = 1.0) -> None:
        """
        Attempt to reconnect to Redis.
        """
        for attempt in range(max_retries):
            try:
                await self.disconnect()
                await self.connect()

                # Re-subscribe to channels
                channels = [ch for ch in self._handlers.keys() if "*" not in ch]
                patterns = [ch for ch in self._handlers.keys() if "*" in ch]

                if channels:
                    await self._pubsub.subscribe(*channels)
                if patterns:
                    await self._pubsub.psubscribe(*patterns)

                logger.info("Reconnected to Redis")
                return

            except redis.ConnectionError:
                logger.warning(f"Reconnect attempt {attempt + 1} failed")
                await asyncio.sleep(delay * (attempt + 1))

        raise redis.ConnectionError("Failed to reconnect to Redis after max retries")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._client is not None

    @property
    def is_listening(self) -> bool:
        """Check if actively listening for events."""
        return self._running


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus(
    redis_url: Optional[str] = None,
    source_service: str = "",
) -> EventBus:
    """
    Get the global event bus instance.

    Creates a new instance if one doesn't exist.

    Args:
        redis_url: Redis connection URL (uses REDIS_URL env var if not provided)
        source_service: Service name for event metadata

    Returns:
        EventBus instance
    """
    global _event_bus

    if _event_bus is None:
        import os

        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        _event_bus = EventBus(redis_url=url, source_service=source_service)

    return _event_bus


async def reset_event_bus() -> None:
    """
    Reset the global event bus (for testing).
    """
    global _event_bus
    if _event_bus is not None:
        await _event_bus.disconnect()
        _event_bus = None
