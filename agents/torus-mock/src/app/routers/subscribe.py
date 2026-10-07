"""Subscribe router: subscribeData / unsubscribeData / WebSocket.

Maps TORUS subscribeData → POST /api/v1/subscribe
Maps TORUS unsubscribeData → DELETE /api/v1/subscribe/{id}
Maps TORUS hot-link push → WebSocket /ws/subscribe
"""

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..schemas import SubscribeRequest, SubscribeResponse
from ..services.subscription_manager import get_subscription_manager

router = APIRouter(tags=["subscribe"])


@router.post("/api/v1/subscribe", response_model=SubscribeResponse)
async def subscribe_data(request: SubscribeRequest):
    """Subscribe to data changes (subscribeData)."""
    manager = get_subscription_manager()
    # Use a generated client ID for REST-based subscriptions
    client_id = f"rest-{uuid.uuid4().hex[:8]}"
    sub_id = manager.subscribe(
        client_id=client_id,
        address=request.address,
        filter_str=request.filter,
        interval_ms=request.interval,
    )
    return SubscribeResponse(
        subscriptionId=sub_id,
        address=request.address,
        filter=request.filter,
        interval=request.interval,
    )


@router.delete("/api/v1/subscribe/{subscription_id}")
async def unsubscribe_data(subscription_id: str):
    """Unsubscribe from data changes (unsubscribeData)."""
    manager = get_subscription_manager()
    success = manager.unsubscribe(subscription_id)
    return {"success": success, "subscriptionId": subscription_id}


@router.get("/api/v1/subscribe")
async def list_subscriptions():
    """List all active subscriptions."""
    manager = get_subscription_manager()
    return {"subscriptions": manager.get_subscriptions()}


@router.websocket("/ws/subscribe")
async def websocket_subscribe(websocket: WebSocket):
    """WebSocket endpoint for real-time data push.

    Client sends JSON messages to subscribe:
      {"action": "subscribe", "address": "...", "filter": "...", "interval": 1000}
      {"action": "unsubscribe", "subscriptionId": "..."}

    Server pushes data changes:
      {"subscriptionId": "...", "address": "...", "value": ...}
    """
    manager = get_subscription_manager()
    client_id = f"ws-{uuid.uuid4().hex[:8]}"

    await manager.connect(client_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                sub_id = manager.subscribe(
                    client_id=client_id,
                    address=data.get("address", ""),
                    filter_str=data.get("filter", ""),
                    interval_ms=data.get("interval", 1000),
                )
                await websocket.send_json(
                    {
                        "action": "subscribed",
                        "subscriptionId": sub_id,
                    }
                )

            elif action == "unsubscribe":
                sub_id = data.get("subscriptionId", "")
                manager.unsubscribe(sub_id)
                await websocket.send_json(
                    {
                        "action": "unsubscribed",
                        "subscriptionId": sub_id,
                    }
                )

            elif action == "list":
                subs = manager.get_subscriptions(client_id)
                await websocket.send_json(
                    {
                        "action": "subscriptions",
                        "subscriptions": subs,
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
