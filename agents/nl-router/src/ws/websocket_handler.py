"""
WebSocket Handler for NL Router

Handles WebSocket connections and message processing for real-time updates.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any, Callable, Awaitable

from fastapi import WebSocket, WebSocketDisconnect

from .connection import ConnectionManager, ChannelType

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles different types of WebSocket messages"""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self._handlers: Dict[str, Callable[[str, Dict], Awaitable[Dict]]] = {
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "query": self._handle_query,
            "ping": self._handle_ping,
        }

    async def handle(self, client_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route message to appropriate handler"""
        action = message.get("action", "")
        handler = self._handlers.get(action)

        if not handler:
            return {
                "type": "error",
                "error": f"Unknown action: {action}",
                "supported_actions": list(self._handlers.keys()),
            }

        try:
            return await handler(client_id, message)
        except Exception as e:
            logger.error(f"Error handling {action} from {client_id}: {e}")
            return {
                "type": "error",
                "error": str(e),
            }

    async def _handle_subscribe(self, client_id: str, message: Dict) -> Dict:
        """Handle subscription request"""
        channel_name = message.get("channel", "")
        filters = message.get("filters", {})

        try:
            channel = ChannelType(channel_name)
        except ValueError:
            return {
                "type": "error",
                "error": f"Invalid channel: {channel_name}",
                "available_channels": [c.value for c in ChannelType],
            }

        success = self.manager.subscribe(client_id, channel, filters)

        return {
            "type": "subscribed" if success else "error",
            "channel": channel_name,
            "filters": filters,
        }

    async def _handle_unsubscribe(self, client_id: str, message: Dict) -> Dict:
        """Handle unsubscription request"""
        channel_name = message.get("channel", "")

        try:
            channel = ChannelType(channel_name)
        except ValueError:
            return {
                "type": "error",
                "error": f"Invalid channel: {channel_name}",
            }

        success = self.manager.unsubscribe(client_id, channel)

        return {
            "type": "unsubscribed" if success else "error",
            "channel": channel_name,
        }

    async def _handle_query(self, client_id: str, message: Dict) -> Dict:
        """Handle NL query request via WebSocket"""
        query = message.get("query", "")

        if not query:
            return {
                "type": "error",
                "error": "Query is required",
            }

        # This would integrate with NL Router agent
        # For now, return acknowledgment
        return {
            "type": "query_received",
            "query": query,
            "request_id": str(uuid.uuid4()),
            "message": "Query is being processed. Results will be pushed when ready.",
        }

    async def _handle_ping(self, client_id: str, message: Dict) -> Dict:
        """Handle ping request"""
        return {
            "type": "pong",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class WebSocketHandler:
    """
    Handles individual WebSocket connection lifecycle

    Usage:
        handler = WebSocketHandler(connection_manager)
        await handler.handle_connection(websocket, "client_123")
    """

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self.message_handler = MessageHandler(connection_manager)

    async def handle_connection(
        self, websocket: WebSocket, client_id: Optional[str] = None, user_id: Optional[str] = None
    ):
        """Handle WebSocket connection lifecycle"""
        # Generate client ID if not provided
        if not client_id:
            client_id = f"client_{uuid.uuid4().hex[:8]}"

        # Accept connection
        await self.manager.connect(websocket, client_id, user_id)

        # Send welcome message
        await self.manager.send_to_client(
            client_id,
            {
                "type": "connected",
                "client_id": client_id,
                "available_channels": [c.value for c in ChannelType],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        try:
            while True:
                # Receive message
                data = await websocket.receive_json()

                # Handle message
                response = await self.message_handler.handle(client_id, data)

                # Send response
                await self.manager.send_to_client(client_id, response)

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            await self.manager.disconnect(client_id)


class WebSocketManager:
    """
    High-level WebSocket manager for the application

    Usage:
        ws_manager = WebSocketManager()

        # Start background tasks
        await ws_manager.start()

        # Broadcast equipment status
        await ws_manager.broadcast_equipment_status({
            "equipment_id": "CNC-001",
            "status": "RUN",
            "metrics": {"load": 45}
        })

        # Stop on shutdown
        await ws_manager.stop()
    """

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.handler = WebSocketHandler(self.connection_manager)
        self._ping_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start background tasks"""
        self._running = True
        self._ping_task = asyncio.create_task(self._ping_loop())
        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop background tasks and close connections"""
        self._running = False

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for client_id in list(self.connection_manager._connections.keys()):
            await self.connection_manager.disconnect(client_id)

        logger.info("WebSocket manager stopped")

    async def _ping_loop(self):
        """Periodic ping to check connection health"""
        while self._running:
            await asyncio.sleep(30)  # Ping every 30 seconds
            await self.connection_manager.ping_all()

    async def handle_websocket(
        self, websocket: WebSocket, client_id: Optional[str] = None, user_id: Optional[str] = None
    ):
        """Handle incoming WebSocket connection"""
        await self.handler.handle_connection(websocket, client_id, user_id)

    # Convenience methods for broadcasting different types of updates

    async def broadcast_equipment_status(self, data: Dict[str, Any]):
        """Broadcast equipment status update"""
        await self.connection_manager.broadcast(ChannelType.EQUIPMENT_STATUS, data)

    async def broadcast_production_result(self, data: Dict[str, Any]):
        """Broadcast production result update"""
        await self.connection_manager.broadcast(ChannelType.PRODUCTION_RESULTS, data)

    async def broadcast_kpi_update(self, data: Dict[str, Any]):
        """Broadcast KPI update"""
        await self.connection_manager.broadcast(ChannelType.KPI_UPDATES, data)

    async def broadcast_work_order_status(self, data: Dict[str, Any]):
        """Broadcast work order status change"""
        await self.connection_manager.broadcast(ChannelType.WORK_ORDER_STATUS, data)

    async def broadcast_alert(self, data: Dict[str, Any]):
        """Broadcast alert to all subscribers"""
        await self.connection_manager.broadcast(ChannelType.ALERTS, data)

    async def send_query_result(self, client_id: str, result: Dict[str, Any]):
        """Send NL query result to specific client"""
        await self.connection_manager.send_to_client(
            client_id,
            {
                "type": "query_result",
                "data": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket manager status"""
        return {
            "running": self._running,
            **self.connection_manager.get_status(),
        }


# Global WebSocket manager instance
_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
