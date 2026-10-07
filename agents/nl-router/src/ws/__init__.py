"""WebSocket module for real-time updates"""

from .websocket_handler import WebSocketHandler, WebSocketManager, get_websocket_manager
from .connection import ConnectionManager

__all__ = [
    "WebSocketHandler",
    "WebSocketManager",
    "ConnectionManager",
    "get_websocket_manager",
]
