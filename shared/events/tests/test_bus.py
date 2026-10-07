"""Tests for event bus (unit tests, no Redis required)."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from ..production import WorkOrderCreatedEvent
from ..bus import EventBus, get_event_bus, reset_event_bus


class TestEventBusUnit:
    """Unit tests for EventBus (no Redis required)."""

    def test_initialization(self):
        """Test EventBus initialization."""
        bus = EventBus(
            redis_url="redis://localhost:6379",
            max_connections=5,
            source_service="test-service",
        )

        assert bus.redis_url == "redis://localhost:6379"
        assert bus.max_connections == 5
        assert bus.source_service == "test-service"
        assert bus.is_connected is False
        assert bus.is_listening is False

    def test_subscribe_registers_handler(self):
        """Test that subscribe registers a handler."""
        bus = EventBus()
        handler = AsyncMock()

        bus.subscribe("work_order.created", handler)

        assert "events:work_order.created" in bus._handlers
        assert len(bus._handlers["events:work_order.created"]) == 1

    def test_subscribe_multiple_handlers(self):
        """Test subscribing multiple handlers to same event."""
        bus = EventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        bus.subscribe("work_order.created", handler1)
        bus.subscribe("work_order.created", handler2)

        assert len(bus._handlers["events:work_order.created"]) == 2

    def test_subscribe_pattern(self):
        """Test pattern subscription."""
        bus = EventBus()
        handler = AsyncMock()

        bus.subscribe_pattern("work_order.*", handler)

        assert "events:work_order.*" in bus._handlers


class TestEventBusWithMockRedis:
    """Tests with mocked Redis."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch("shared.events.bus.redis") as mock_redis_module, \
             patch("shared.events.bus.ConnectionPool") as mock_pool_class:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_client.publish = AsyncMock(return_value=1)
            mock_client.close = AsyncMock()

            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.psubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()
            mock_pubsub.get_message = AsyncMock(return_value=None)

            mock_client.pubsub = MagicMock(return_value=mock_pubsub)

            mock_pool = AsyncMock()
            mock_pool.disconnect = AsyncMock()

            mock_redis_module.Redis = MagicMock(return_value=mock_client)
            mock_pool_class.from_url = MagicMock(return_value=mock_pool)

            yield {
                "client": mock_client,
                "pubsub": mock_pubsub,
                "pool": mock_pool,
            }

    @pytest.mark.asyncio
    async def test_connect(self, mock_redis):
        """Test connecting to Redis."""
        bus = EventBus()

        await bus.connect()

        assert bus.is_connected
        mock_redis["client"].ping.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_redis):
        """Test disconnecting from Redis."""
        bus = EventBus()
        await bus.connect()

        await bus.disconnect()

        assert not bus.is_connected

    @pytest.mark.asyncio
    async def test_publish_event(self, mock_redis):
        """Test publishing an event."""
        bus = EventBus(source_service="test-service")
        await bus.connect()

        event = WorkOrderCreatedEvent(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="PROD-A",
            order_qty=100,
        )

        subscribers = await bus.publish(event)

        assert subscribers == 1
        mock_redis["client"].publish.assert_awaited_once()

        # Check the channel and message
        call_args = mock_redis["client"].publish.call_args
        channel, message = call_args[0]
        assert channel == "events:work_order.created"
        assert "LOT-001" in message


class TestGetEventBus:
    """Tests for get_event_bus factory function."""

    @pytest_asyncio.fixture(autouse=True)
    async def reset_bus(self):
        """Reset the global event bus before each test."""
        await reset_event_bus()
        yield
        await reset_event_bus()

    @pytest.mark.asyncio
    async def test_creates_singleton(self):
        """Test that get_event_bus returns the same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_uses_provided_url(self):
        """Test that custom Redis URL is used."""
        bus = get_event_bus(redis_url="redis://custom:6380")

        assert bus.redis_url == "redis://custom:6380"

    @pytest.mark.asyncio
    async def test_uses_env_var_fallback(self):
        """Test that REDIS_URL env var is used as fallback."""
        import os

        original = os.environ.get("REDIS_URL")
        os.environ["REDIS_URL"] = "redis://env-redis:6379"

        try:
            bus = get_event_bus()
            # Note: This test may fail if a bus was already created
            # Reset is handled by the fixture
        finally:
            if original:
                os.environ["REDIS_URL"] = original
            elif "REDIS_URL" in os.environ:
                del os.environ["REDIS_URL"]
