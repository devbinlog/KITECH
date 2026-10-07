"""Subscription Manager — manages data subscriptions and WebSocket push.

Handles subscribeData/unsubscribeData and pushes changes to connected clients.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from .address_parser import parse_address, resolve_value
from .machine_store import get_store


@dataclass
class Subscription:
    """A single data subscription."""

    id: str
    address: str
    filter: str
    interval_ms: int = 1000
    last_value: Any = None


class SubscriptionManager:
    """Manages subscriptions and WebSocket connections."""

    def __init__(self) -> None:
        self.subscriptions: Dict[str, Subscription] = {}
        self.connections: Dict[str, WebSocket] = {}  # client_id → WebSocket
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id → {sub_ids}
        self._push_task: Optional[asyncio.Task] = None
        self._running = False

    def subscribe(
        self,
        client_id: str,
        address: str,
        filter_str: str = "",
        interval_ms: int = 1000,
    ) -> str:
        """Create a new subscription."""
        sub_id = str(uuid.uuid4())[:8]
        sub = Subscription(
            id=sub_id,
            address=address,
            filter=filter_str,
            interval_ms=interval_ms,
        )
        self.subscriptions[sub_id] = sub

        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()
        self.client_subscriptions[client_id].add(sub_id)

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription."""
        if subscription_id not in self.subscriptions:
            return False

        del self.subscriptions[subscription_id]

        # Remove from client mapping
        for client_id, sub_ids in self.client_subscriptions.items():
            sub_ids.discard(subscription_id)

        return True

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection."""
        await websocket.accept()
        self.connections[client_id] = websocket
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection and its subscriptions."""
        self.connections.pop(client_id, None)
        sub_ids = self.client_subscriptions.pop(client_id, set())
        for sub_id in sub_ids:
            self.subscriptions.pop(sub_id, None)

    async def start_push_loop(self) -> None:
        """Start the background push loop."""
        if self._running:
            return
        self._running = True
        self._push_task = asyncio.create_task(self._push_loop())

    async def stop_push_loop(self) -> None:
        """Stop the background push loop."""
        self._running = False
        if self._push_task:
            self._push_task.cancel()
            try:
                await self._push_task
            except asyncio.CancelledError:
                pass

    async def _push_loop(self) -> None:
        """Push subscribed data to connected clients."""
        while self._running:
            try:
                await self._push_updates()
                await asyncio.sleep(0.5)  # Base interval
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    async def _push_updates(self) -> None:
        """Check all subscriptions and push changed values."""
        store = get_store()
        disconnected = []

        for client_id, ws in self.connections.items():
            sub_ids = self.client_subscriptions.get(client_id, set())
            for sub_id in list(sub_ids):
                sub = self.subscriptions.get(sub_id)
                if not sub:
                    continue

                # Resolve current value
                parsed = parse_address(sub.address, sub.filter)
                machine_ids = parsed.filters.get("machine", [1])

                for mid in machine_ids:
                    machine = store.get_machine(mid)
                    if not machine:
                        continue

                    results = resolve_value(machine, parsed)
                    for result in results:
                        if result.success and result.value != sub.last_value:
                            sub.last_value = result.value
                            try:
                                await ws.send_json(
                                    {
                                        "subscriptionId": sub_id,
                                        "address": sub.address,
                                        "filter": sub.filter,
                                        "value": result.value,
                                        "path": result.path,
                                    }
                                )
                            except Exception:
                                disconnected.append(client_id)
                                break

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_subscriptions(self, client_id: Optional[str] = None) -> List[Dict]:
        """List active subscriptions."""
        if client_id:
            sub_ids = self.client_subscriptions.get(client_id, set())
            subs = [self.subscriptions[sid] for sid in sub_ids if sid in self.subscriptions]
        else:
            subs = list(self.subscriptions.values())

        return [
            {
                "subscriptionId": s.id,
                "address": s.address,
                "filter": s.filter,
                "interval": s.interval_ms,
            }
            for s in subs
        ]


# ─── Singleton ───────────────────────────────────────────────────────────────

_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """Get the singleton SubscriptionManager instance."""
    global _manager
    if _manager is None:
        _manager = SubscriptionManager()
    return _manager
