"""Tests for WebSocket Handler"""

import pytest
from unittest.mock import AsyncMock

from src.ws.connection import (
    ConnectionManager,
    Connection,
    Subscription,
    ChannelType,
)
from src.ws.websocket_handler import (
    WebSocketManager,
    MessageHandler,
    get_websocket_manager,
)


class TestChannelType:
    """Tests for ChannelType enum"""

    def test_channel_types(self):
        """Test channel type values"""
        assert ChannelType.EQUIPMENT_STATUS.value == "equipment_status"
        assert ChannelType.PRODUCTION_RESULTS.value == "production_results"
        assert ChannelType.KPI_UPDATES.value == "kpi_updates"
        assert ChannelType.WORK_ORDER_STATUS.value == "work_order_status"
        assert ChannelType.ALERTS.value == "alerts"


class TestSubscription:
    """Tests for Subscription dataclass"""

    def test_subscription_creation(self):
        """Test subscription creation with defaults"""
        sub = Subscription(channel=ChannelType.EQUIPMENT_STATUS)

        assert sub.channel == ChannelType.EQUIPMENT_STATUS
        assert sub.filters == {}
        assert sub.created_at is not None

    def test_subscription_with_filters(self):
        """Test subscription with filters"""
        sub = Subscription(
            channel=ChannelType.EQUIPMENT_STATUS, filters={"equipment_ids": ["CNC-001"]}
        )

        assert sub.filters == {"equipment_ids": ["CNC-001"]}


class TestConnection:
    """Tests for Connection dataclass"""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket"""
        ws = AsyncMock()
        return ws

    def test_connection_creation(self, mock_websocket):
        """Test connection creation"""
        conn = Connection(websocket=mock_websocket, client_id="test_client", user_id="user_123")

        assert conn.client_id == "test_client"
        assert conn.user_id == "user_123"
        assert conn.subscriptions == {}

    def test_is_subscribed(self, mock_websocket):
        """Test checking subscription status"""
        conn = Connection(websocket=mock_websocket, client_id="test")

        assert conn.is_subscribed(ChannelType.EQUIPMENT_STATUS) is False

        conn.subscriptions[ChannelType.EQUIPMENT_STATUS] = Subscription(
            channel=ChannelType.EQUIPMENT_STATUS
        )

        assert conn.is_subscribed(ChannelType.EQUIPMENT_STATUS) is True

    def test_matches_filter_no_subscription(self, mock_websocket):
        """Test filter matching without subscription"""
        conn = Connection(websocket=mock_websocket, client_id="test")

        result = conn.matches_filter(ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001"})

        assert result is False

    def test_matches_filter_no_filters(self, mock_websocket):
        """Test filter matching with empty filters (matches all)"""
        conn = Connection(websocket=mock_websocket, client_id="test")
        conn.subscriptions[ChannelType.EQUIPMENT_STATUS] = Subscription(
            channel=ChannelType.EQUIPMENT_STATUS, filters={}
        )

        result = conn.matches_filter(ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001"})

        assert result is True

    def test_matches_filter_with_list(self, mock_websocket):
        """Test filter matching with list filter"""
        conn = Connection(websocket=mock_websocket, client_id="test")
        conn.subscriptions[ChannelType.EQUIPMENT_STATUS] = Subscription(
            channel=ChannelType.EQUIPMENT_STATUS, filters={"equipment_id": ["CNC-001", "CNC-002"]}
        )

        assert (
            conn.matches_filter(ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001"}) is True
        )
        assert (
            conn.matches_filter(ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-003"}) is False
        )

    def test_matches_filter_exact_match(self, mock_websocket):
        """Test filter matching with exact value"""
        conn = Connection(websocket=mock_websocket, client_id="test")
        conn.subscriptions[ChannelType.EQUIPMENT_STATUS] = Subscription(
            channel=ChannelType.EQUIPMENT_STATUS, filters={"status": "RUN"}
        )

        assert conn.matches_filter(ChannelType.EQUIPMENT_STATUS, {"status": "RUN"}) is True
        assert conn.matches_filter(ChannelType.EQUIPMENT_STATUS, {"status": "IDLE"}) is False


class TestConnectionManager:
    """Tests for ConnectionManager"""

    @pytest.fixture
    def manager(self):
        """Create connection manager"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket"""
        ws = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test accepting connection"""
        conn = await manager.connect(mock_websocket, "client_1", "user_1")

        assert conn.client_id == "client_1"
        assert conn.user_id == "user_1"
        assert manager.connection_count == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting"""
        await manager.connect(mock_websocket, "client_1")
        await manager.disconnect("client_1")

        assert manager.connection_count == 0
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_subscriptions(self, manager, mock_websocket):
        """Test disconnect removes subscriptions"""
        await manager.connect(mock_websocket, "client_1")
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)

        await manager.disconnect("client_1")

        assert "client_1" not in manager._channel_subscribers[ChannelType.EQUIPMENT_STATUS]

    def test_subscribe(self, manager, mock_websocket):
        """Test subscribing to channel"""
        manager._connections["client_1"] = Connection(
            websocket=mock_websocket, client_id="client_1"
        )

        result = manager.subscribe(
            "client_1", ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001"}
        )

        assert result is True
        assert "client_1" in manager._channel_subscribers[ChannelType.EQUIPMENT_STATUS]

    def test_subscribe_nonexistent_client(self, manager):
        """Test subscribe fails for nonexistent client"""
        result = manager.subscribe("nonexistent", ChannelType.EQUIPMENT_STATUS)
        assert result is False

    def test_unsubscribe(self, manager, mock_websocket):
        """Test unsubscribing from channel"""
        manager._connections["client_1"] = Connection(
            websocket=mock_websocket, client_id="client_1"
        )
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)

        result = manager.unsubscribe("client_1", ChannelType.EQUIPMENT_STATUS)

        assert result is True
        assert "client_1" not in manager._channel_subscribers[ChannelType.EQUIPMENT_STATUS]

    @pytest.mark.asyncio
    async def test_send_to_client(self, manager, mock_websocket):
        """Test sending message to specific client"""
        await manager.connect(mock_websocket, "client_1")

        await manager.send_to_client("client_1", {"type": "test"})

        mock_websocket.send_json.assert_called_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """Test broadcasting to channel subscribers"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client_1")
        await manager.connect(ws2, "client_2")
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)
        manager.subscribe("client_2", ChannelType.EQUIPMENT_STATUS)

        await manager.broadcast(
            ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001", "status": "RUN"}
        )

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_with_filter(self, manager):
        """Test broadcast respects filters"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client_1")
        await manager.connect(ws2, "client_2")
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS, {"equipment_id": ["CNC-001"]})
        manager.subscribe("client_2", ChannelType.EQUIPMENT_STATUS, {"equipment_id": ["CNC-002"]})

        await manager.broadcast(
            ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001", "status": "RUN"}
        )

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_excludes_clients(self, manager):
        """Test broadcast excludes specified clients"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client_1")
        await manager.connect(ws2, "client_2")
        manager.subscribe("client_1", ChannelType.ALERTS)
        manager.subscribe("client_2", ChannelType.ALERTS)

        await manager.broadcast(
            ChannelType.ALERTS, {"message": "test"}, exclude_clients={"client_1"}
        )

        ws1.send_json.assert_not_called()
        ws2.send_json.assert_called_once()

    def test_get_subscribers(self, manager, mock_websocket):
        """Test getting list of subscribers"""
        manager._connections["client_1"] = Connection(
            websocket=mock_websocket, client_id="client_1"
        )
        manager._connections["client_2"] = Connection(
            websocket=mock_websocket, client_id="client_2"
        )
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)
        manager.subscribe("client_2", ChannelType.EQUIPMENT_STATUS)

        subscribers = manager.get_subscribers(ChannelType.EQUIPMENT_STATUS)

        assert len(subscribers) == 2
        assert "client_1" in subscribers
        assert "client_2" in subscribers

    def test_get_status(self, manager, mock_websocket):
        """Test getting connection status"""
        manager._connections["client_1"] = Connection(
            websocket=mock_websocket, client_id="client_1", user_id="user_1"
        )
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)

        status = manager.get_status()

        assert status["total_connections"] == 1
        assert status["channels"]["equipment_status"] == 1
        assert len(status["connections"]) == 1


class TestMessageHandler:
    """Tests for MessageHandler"""

    @pytest.fixture
    def manager(self):
        """Create connection manager"""
        return ConnectionManager()

    @pytest.fixture
    def handler(self, manager):
        """Create message handler"""
        return MessageHandler(manager)

    @pytest.mark.asyncio
    async def test_handle_subscribe(self, handler, manager):
        """Test handling subscribe message"""
        ws = AsyncMock()
        manager._connections["client_1"] = Connection(websocket=ws, client_id="client_1")

        result = await handler.handle(
            "client_1",
            {
                "action": "subscribe",
                "channel": "equipment_status",
                "filters": {"equipment_id": "CNC-001"},
            },
        )

        assert result["type"] == "subscribed"
        assert result["channel"] == "equipment_status"

    @pytest.mark.asyncio
    async def test_handle_subscribe_invalid_channel(self, handler, manager):
        """Test handling subscribe with invalid channel"""
        ws = AsyncMock()
        manager._connections["client_1"] = Connection(websocket=ws, client_id="client_1")

        result = await handler.handle(
            "client_1", {"action": "subscribe", "channel": "invalid_channel"}
        )

        assert result["type"] == "error"
        assert "Invalid channel" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_unsubscribe(self, handler, manager):
        """Test handling unsubscribe message"""
        ws = AsyncMock()
        manager._connections["client_1"] = Connection(websocket=ws, client_id="client_1")
        manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)

        result = await handler.handle(
            "client_1", {"action": "unsubscribe", "channel": "equipment_status"}
        )

        assert result["type"] == "unsubscribed"

    @pytest.mark.asyncio
    async def test_handle_query(self, handler):
        """Test handling query message"""
        result = await handler.handle("client_1", {"action": "query", "query": "오늘 생산 현황"})

        assert result["type"] == "query_received"
        assert "request_id" in result

    @pytest.mark.asyncio
    async def test_handle_ping(self, handler):
        """Test handling ping message"""
        result = await handler.handle("client_1", {"action": "ping"})

        assert result["type"] == "pong"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_handle_unknown_action(self, handler):
        """Test handling unknown action"""
        result = await handler.handle("client_1", {"action": "unknown"})

        assert result["type"] == "error"
        assert "Unknown action" in result["error"]


class TestWebSocketManager:
    """Tests for WebSocketManager"""

    @pytest.fixture
    def ws_manager(self):
        """Create WebSocket manager"""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_start_stop(self, ws_manager):
        """Test starting and stopping manager"""
        await ws_manager.start()
        assert ws_manager._running is True

        await ws_manager.stop()
        assert ws_manager._running is False

    @pytest.mark.asyncio
    async def test_broadcast_equipment_status(self, ws_manager):
        """Test broadcasting equipment status"""
        ws = AsyncMock()
        await ws_manager.connection_manager.connect(ws, "client_1")
        ws_manager.connection_manager.subscribe("client_1", ChannelType.EQUIPMENT_STATUS)

        await ws_manager.broadcast_equipment_status({"equipment_id": "CNC-001", "status": "RUN"})

        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_production_result(self, ws_manager):
        """Test broadcasting production result"""
        ws = AsyncMock()
        await ws_manager.connection_manager.connect(ws, "client_1")
        ws_manager.connection_manager.subscribe("client_1", ChannelType.PRODUCTION_RESULTS)

        await ws_manager.broadcast_production_result({"lot_no": "LOT-001", "ok_qty": 100})

        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_kpi_update(self, ws_manager):
        """Test broadcasting KPI update"""
        ws = AsyncMock()
        await ws_manager.connection_manager.connect(ws, "client_1")
        ws_manager.connection_manager.subscribe("client_1", ChannelType.KPI_UPDATES)

        await ws_manager.broadcast_kpi_update({"metric": "utilization", "value": 85.5})

        ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_query_result(self, ws_manager):
        """Test sending query result to specific client"""
        ws = AsyncMock()
        await ws_manager.connection_manager.connect(ws, "client_1")

        await ws_manager.send_query_result("client_1", {"answer": "test"})

        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "query_result"
        assert call_args["data"]["answer"] == "test"

    def test_get_status(self, ws_manager):
        """Test getting manager status"""
        status = ws_manager.get_status()

        assert "running" in status
        assert "total_connections" in status
        assert "channels" in status


class TestGlobalWebSocketManager:
    """Tests for global WebSocket manager instance"""

    def test_get_websocket_manager_singleton(self):
        """Test get_websocket_manager returns same instance"""
        import src.ws.websocket_handler as ws_module

        # Reset global instance
        ws_module._ws_manager = None

        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()

        assert manager1 is manager2
