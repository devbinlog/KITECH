"""
WebSocket Routes for NL Router

Provides real-time communication endpoints.
"""

from typing import Optional

from fastapi import APIRouter, WebSocket, Query

from ...ws import get_websocket_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Optional client identifier"),
    user_id: Optional[str] = Query(None, description="Optional user identifier"),
):
    """
    WebSocket endpoint for real-time updates

    ## Connection
    Connect to `ws://host:port/ws?client_id=xxx&user_id=yyy`

    ## Message Format
    All messages are JSON with an `action` field:

    ### Subscribe to channel
    ```json
    {
        "action": "subscribe",
        "channel": "equipment_status",
        "filters": {"equipment_ids": ["CNC-001", "CNC-002"]}
    }
    ```

    ### Unsubscribe from channel
    ```json
    {
        "action": "unsubscribe",
        "channel": "equipment_status"
    }
    ```

    ### Send NL query
    ```json
    {
        "action": "query",
        "query": "오늘 생산 현황 보여줘"
    }
    ```

    ### Ping
    ```json
    {
        "action": "ping"
    }
    ```

    ## Available Channels
    - `equipment_status`: Real-time equipment status updates
    - `production_results`: Production result notifications
    - `kpi_updates`: KPI metric updates
    - `work_order_status`: Work order status changes
    - `alerts`: System alerts and notifications

    ## Response Messages
    - `connected`: Initial connection confirmation
    - `subscribed`: Subscription confirmation
    - `unsubscribed`: Unsubscription confirmation
    - `update`: Channel update (data broadcast)
    - `query_result`: NL query result
    - `pong`: Ping response
    - `error`: Error message
    """
    ws_manager = get_websocket_manager()
    await ws_manager.handle_websocket(websocket, client_id, user_id)


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection status

    Returns current connection count, channel subscriptions, and connected clients.
    """
    ws_manager = get_websocket_manager()
    return ws_manager.get_status()
