"""WebSocket output handler for real-time streaming."""

import asyncio
import json
from typing import Optional, Set
from datetime import datetime, timezone

import websockets
from websockets.asyncio.server import serve, ServerConnection

from ..models.monitoring_data import MonitoringRecord


class WebSocketOutput:
    """
    WebSocket server for streaming monitoring records in real-time.

    Clients connect and receive JSON-formatted MonitoringRecord data.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
    ):
        """
        Initialize WebSocket output handler.

        Args:
            host: Host to bind server
            port: Port to bind server
        """
        self.host = host
        self.port = port
        self._server = None
        self._clients: Set[ServerConnection] = set()
        self._records_sent = 0
        self._is_running = False
        self._server_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start WebSocket server."""
        if self._is_running:
            return

        self._server = await serve(
            self._handle_client,
            self.host,
            self.port,
        )
        self._is_running = True
        print(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop WebSocket server."""
        if not self._is_running:
            return

        # Close all client connections
        for client in list(self._clients):
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()

        # Close server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        self._is_running = False
        print("WebSocket server stopped")

    async def _handle_client(self, websocket: ServerConnection) -> None:
        """Handle new client connection."""
        self._clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"Client connected: {client_addr}")

        try:
            # Send welcome message
            await websocket.send(
                json.dumps(
                    {
                        "type": "connected",
                        "message": "Connected to Monitoring Data Replayer",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            )

            # Keep connection alive and handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Invalid JSON",
                            }
                        )
                    )
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            print(f"Client disconnected: {client_addr}")

    async def _handle_message(self, websocket: ServerConnection, data: dict) -> None:
        """Handle incoming message from client."""
        msg_type = data.get("type", "")

        if msg_type == "ping":
            await websocket.send(
                json.dumps(
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            )
        elif msg_type == "status":
            await websocket.send(
                json.dumps(
                    {
                        "type": "status",
                        "clients_connected": len(self._clients),
                        "records_sent": self._records_sent,
                        "is_running": self._is_running,
                    }
                )
            )

    async def broadcast(self, record: MonitoringRecord) -> int:
        """
        Broadcast record to all connected clients.

        Args:
            record: MonitoringRecord to broadcast

        Returns:
            Number of clients that received the record
        """
        if not self._clients:
            return 0

        message = json.dumps(
            {
                "type": "record",
                "data": record.to_dict(),
            }
        )

        sent_count = 0
        dead_clients = set()

        for client in self._clients:
            try:
                await client.send(message)
                sent_count += 1
            except websockets.exceptions.ConnectionClosed:
                dead_clients.add(client)
            except Exception:
                dead_clients.add(client)

        # Remove dead clients
        self._clients -= dead_clients
        self._records_sent += sent_count

        return sent_count

    async def send_status(self, status: dict) -> None:
        """Send status update to all clients."""
        if not self._clients:
            return

        message = json.dumps(
            {
                "type": "status",
                **status,
            }
        )

        dead_clients = set()
        for client in self._clients:
            try:
                await client.send(message)
            except Exception:
                dead_clients.add(client)

        self._clients -= dead_clients

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)

    @property
    def records_sent(self) -> int:
        """Get total number of records sent."""
        return self._records_sent

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._is_running

    def get_statistics(self) -> dict:
        """Get server statistics."""
        return {
            "host": self.host,
            "port": self.port,
            "is_running": self._is_running,
            "clients_connected": len(self._clients),
            "records_sent": self._records_sent,
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
