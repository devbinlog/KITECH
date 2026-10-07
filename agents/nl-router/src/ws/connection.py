"""
WebSocket Connection Manager

Manages WebSocket connections and broadcasts messages to subscribers.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Available subscription channels"""

    EQUIPMENT_STATUS = "equipment_status"
    PRODUCTION_RESULTS = "production_results"
    KPI_UPDATES = "kpi_updates"
    WORK_ORDER_STATUS = "work_order_status"
    ALERTS = "alerts"


@dataclass
class Subscription:
    """Subscription details for a channel"""

    channel: ChannelType
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Connection:
    """WebSocket connection with metadata"""

    websocket: WebSocket
    client_id: str
    user_id: Optional[str] = None
    subscriptions: Dict[ChannelType, Subscription] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_subscribed(self, channel: ChannelType) -> bool:
        """Check if connection is subscribed to channel"""
        return channel in self.subscriptions

    def matches_filter(self, channel: ChannelType, data: Dict[str, Any]) -> bool:
        """Check if data matches subscription filters"""
        if channel not in self.subscriptions:
            return False

        filters = self.subscriptions[channel].filters
        if not filters:
            return True

        # Check each filter criterion
        for key, value in filters.items():
            if key in data:
                if isinstance(value, list):
                    if data[key] not in value:
                        return False
                elif data[key] != value:
                    return False

        return True


class ConnectionManager:
    """
    Manages WebSocket connections and message routing

    Usage:
        manager = ConnectionManager()

        # Accept connection
        await manager.connect(websocket, "client_123")

        # Subscribe to channel
        manager.subscribe("client_123", ChannelType.EQUIPMENT_STATUS, {"equipment_ids": ["CNC-001"]})

        # Broadcast to channel
        await manager.broadcast(ChannelType.EQUIPMENT_STATUS, {"equipment_id": "CNC-001", "status": "RUN"})

        # Disconnect
        await manager.disconnect("client_123")
    """

    def __init__(self):
        self._connections: Dict[str, Connection] = {}
        self._channel_subscribers: Dict[ChannelType, Set[str]] = {
            channel: set() for channel in ChannelType
        }
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        """Get number of active connections"""
        return len(self._connections)

    async def connect(
        self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None
    ) -> Connection:
        """Accept and register a new connection"""
        await websocket.accept()

        connection = Connection(
            websocket=websocket,
            client_id=client_id,
            user_id=user_id,
        )

        async with self._lock:
            self._connections[client_id] = connection

        logger.info(f"WebSocket connected: {client_id} (user: {user_id})")
        return connection

    async def disconnect(self, client_id: str):
        """Remove and close a connection"""
        async with self._lock:
            if client_id in self._connections:
                connection = self._connections[client_id]

                # Remove from all channel subscribers
                for channel in connection.subscriptions:
                    self._channel_subscribers[channel].discard(client_id)

                # Close websocket
                try:
                    await connection.websocket.close()
                except Exception:
                    pass

                del self._connections[client_id]
                logger.info(f"WebSocket disconnected: {client_id}")

    def subscribe(
        self, client_id: str, channel: ChannelType, filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Subscribe a connection to a channel"""
        if client_id not in self._connections:
            return False

        connection = self._connections[client_id]
        connection.subscriptions[channel] = Subscription(channel=channel, filters=filters or {})
        self._channel_subscribers[channel].add(client_id)

        logger.info(f"Client {client_id} subscribed to {channel.value} with filters: {filters}")
        return True

    def unsubscribe(self, client_id: str, channel: ChannelType) -> bool:
        """Unsubscribe a connection from a channel"""
        if client_id not in self._connections:
            return False

        connection = self._connections[client_id]
        if channel in connection.subscriptions:
            del connection.subscriptions[channel]
            self._channel_subscribers[channel].discard(client_id)
            logger.info(f"Client {client_id} unsubscribed from {channel.value}")
            return True

        return False

    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id not in self._connections:
            return

        connection = self._connections[client_id]
        try:
            await connection.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to {client_id}: {e}")
            await self.disconnect(client_id)

    async def broadcast(
        self, channel: ChannelType, data: Dict[str, Any], exclude_clients: Optional[Set[str]] = None
    ):
        """Broadcast message to all subscribers of a channel"""
        exclude = exclude_clients or set()
        subscribers = self._channel_subscribers.get(channel, set())

        message = {
            "type": "update",
            "channel": channel.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Collect tasks for parallel sending
        tasks = []
        for client_id in subscribers:
            if client_id in exclude:
                continue

            connection = self._connections.get(client_id)
            if connection and connection.matches_filter(channel, data):
                tasks.append(self._send_with_error_handling(connection, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_with_error_handling(self, connection: Connection, message: Dict[str, Any]):
        """Send message with error handling"""
        try:
            await connection.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to {connection.client_id}: {e}")
            await self.disconnect(connection.client_id)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        tasks = []
        for connection in self._connections.values():
            tasks.append(self._send_with_error_handling(connection, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_connection(self, client_id: str) -> Optional[Connection]:
        """Get connection by client ID"""
        return self._connections.get(client_id)

    def get_subscribers(self, channel: ChannelType) -> List[str]:
        """Get list of subscribers for a channel"""
        return list(self._channel_subscribers.get(channel, set()))

    def get_status(self) -> Dict[str, Any]:
        """Get connection manager status"""
        return {
            "total_connections": len(self._connections),
            "channels": {
                channel.value: len(subscribers)
                for channel, subscribers in self._channel_subscribers.items()
            },
            "connections": [
                {
                    "client_id": conn.client_id,
                    "user_id": conn.user_id,
                    "subscriptions": [s.value for s in conn.subscriptions.keys()],
                    "connected_at": conn.connected_at.isoformat(),
                }
                for conn in self._connections.values()
            ],
        }

    async def ping_all(self):
        """Send ping to all connections to check health"""
        message = {
            "type": "ping",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        disconnected = []
        for client_id, connection in self._connections.items():
            try:
                await connection.websocket.send_json(message)
                connection.last_ping = datetime.now(timezone.utc)
            except Exception:
                disconnected.append(client_id)

        # Clean up dead connections
        for client_id in disconnected:
            await self.disconnect(client_id)
