"""Tests for SubscriptionManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.app.services.subscription_manager import (
    SubscriptionManager,
    Subscription,
    get_subscription_manager,
)
from src.app.services.machine_store import get_store, reset_store


@pytest.fixture(autouse=True)
def setup_store():
    """Reset and load store for each test."""
    from pathlib import Path

    reset_store()
    store = get_store()
    store.load_from_json(Path(__file__).parent.parent / "data" / "default_machines.json")
    yield
    reset_store()


class TestSubscription:
    """Test Subscription dataclass."""

    def test_subscription_creation(self):
        """Test subscription creation with defaults."""
        sub = Subscription(
            id="test-123",
            address="data://machine/channel/axis/machinePosition",
            filter="machine=1&channel=1&axis=1",
        )

        assert sub.id == "test-123"
        assert sub.address == "data://machine/channel/axis/machinePosition"
        assert sub.filter == "machine=1&channel=1&axis=1"
        assert sub.interval_ms == 1000
        assert sub.last_value is None

    def test_subscription_with_custom_interval(self):
        """Test subscription with custom interval."""
        sub = Subscription(
            id="test-456",
            address="test",
            filter="",
            interval_ms=500,
        )

        assert sub.interval_ms == 500


class TestSubscriptionManagerInit:
    """Test SubscriptionManager initialization."""

    def test_init_empty(self):
        """Test empty initialization."""
        mgr = SubscriptionManager()

        assert len(mgr.subscriptions) == 0
        assert len(mgr.connections) == 0
        assert len(mgr.client_subscriptions) == 0


class TestSubscriptionManagerSubscribe:
    """Test subscribe/unsubscribe functionality."""

    def test_subscribe_creates_subscription(self):
        """Test subscribe creates a new subscription."""
        mgr = SubscriptionManager()
        sub_id = mgr.subscribe(
            client_id="client-1",
            address="data://machine/channel/axis/machinePosition",
            filter_str="machine=1",
            interval_ms=500,
        )

        assert sub_id in mgr.subscriptions
        assert sub_id in mgr.client_subscriptions["client-1"]

    def test_subscribe_multiple_same_client(self):
        """Test multiple subscriptions for same client."""
        mgr = SubscriptionManager()
        sub_id1 = mgr.subscribe("client-1", "addr1", "filter1")
        sub_id2 = mgr.subscribe("client-1", "addr2", "filter2")

        assert len(mgr.client_subscriptions["client-1"]) == 2
        assert sub_id1 in mgr.client_subscriptions["client-1"]
        assert sub_id2 in mgr.client_subscriptions["client-1"]

    def test_unsubscribe_removes_subscription(self):
        """Test unsubscribe removes subscription."""
        mgr = SubscriptionManager()
        sub_id = mgr.subscribe("client-1", "addr1", "filter1")

        result = mgr.unsubscribe(sub_id)

        assert result is True
        assert sub_id not in mgr.subscriptions

    def test_unsubscribe_nonexistent_returns_false(self):
        """Test unsubscribe for nonexistent returns False."""
        mgr = SubscriptionManager()

        result = mgr.unsubscribe("nonexistent-id")

        assert result is False


class TestSubscriptionManagerConnection:
    """Test WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connect_registers_websocket(self):
        """Test connect registers the WebSocket."""
        mgr = SubscriptionManager()
        mock_ws = AsyncMock()

        await mgr.connect("client-1", mock_ws)

        mock_ws.accept.assert_called_once()
        assert "client-1" in mgr.connections
        assert "client-1" in mgr.client_subscriptions

    def test_disconnect_removes_client(self):
        """Test disconnect removes client and subscriptions."""
        mgr = SubscriptionManager()
        mgr.connections["client-1"] = MagicMock()
        mgr.client_subscriptions["client-1"] = {"sub-1", "sub-2"}
        mgr.subscriptions["sub-1"] = Subscription("sub-1", "addr", "")
        mgr.subscriptions["sub-2"] = Subscription("sub-2", "addr", "")

        mgr.disconnect("client-1")

        assert "client-1" not in mgr.connections
        assert "client-1" not in mgr.client_subscriptions
        assert "sub-1" not in mgr.subscriptions
        assert "sub-2" not in mgr.subscriptions

    def test_disconnect_nonexistent_is_safe(self):
        """Test disconnecting nonexistent client is safe."""
        mgr = SubscriptionManager()

        # Should not raise
        mgr.disconnect("nonexistent")


class TestSubscriptionManagerGetSubscriptions:
    """Test get_subscriptions functionality."""

    def test_get_subscriptions_all(self):
        """Test get all subscriptions."""
        mgr = SubscriptionManager()
        mgr.subscribe("client-1", "addr1", "filter1", 500)
        mgr.subscribe("client-2", "addr2", "filter2", 1000)

        subs = mgr.get_subscriptions()

        assert len(subs) == 2

    def test_get_subscriptions_by_client(self):
        """Test get subscriptions for specific client."""
        mgr = SubscriptionManager()
        mgr.subscribe("client-1", "addr1", "filter1")
        mgr.subscribe("client-1", "addr2", "filter2")
        mgr.subscribe("client-2", "addr3", "filter3")

        subs = mgr.get_subscriptions(client_id="client-1")

        assert len(subs) == 2

    def test_get_subscriptions_empty_client(self):
        """Test get subscriptions for client with none."""
        mgr = SubscriptionManager()

        subs = mgr.get_subscriptions(client_id="no-subs")

        assert len(subs) == 0

    def test_get_subscriptions_format(self):
        """Test subscription format in response."""
        mgr = SubscriptionManager()
        sub_id = mgr.subscribe("client-1", "addr1", "filter1", 500)

        subs = mgr.get_subscriptions()

        assert subs[0]["subscriptionId"] == sub_id
        assert subs[0]["address"] == "addr1"
        assert subs[0]["filter"] == "filter1"
        assert subs[0]["interval"] == 500


class TestSubscriptionManagerSingleton:
    """Test singleton pattern."""

    def test_get_subscription_manager_returns_same_instance(self):
        """Test get_subscription_manager returns singleton."""
        mgr1 = get_subscription_manager()
        mgr2 = get_subscription_manager()

        assert mgr1 is mgr2
