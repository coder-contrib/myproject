import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

from app.realtime.manager import manager
from app.realtime.channels import Channel

logger = logging.getLogger("realtime.notifications")
router = APIRouter()


@router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Live notifications WebSocket endpoint.

    Clients connect with ?token=<jwt> and receive real-time notifications
    including order updates, stock alerts, system messages, and user mentions.
    """
    from app.core.security.tokens import decode_access_token

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        await websocket.close(code=4001, reason="Invalid token claims")
        return

    conn_id = await manager.connect(websocket, user_id, tenant_id)

    # Auto-subscribe to user's notification channel
    notification_channel = Channel.notifications(tenant_id, user_id)
    await manager.subscribe(conn_id, notification_channel)

    # Send connection confirmation
    await websocket.send_text(json.dumps({
        "type": "connected",
        "channel": "notifications",
        "user_id": user_id,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")

            if action == "mark_read":
                notification_id = message.get("notification_id")
                await websocket.send_text(json.dumps({
                    "type": "ack",
                    "action": "mark_read",
                    "notification_id": notification_id,
                }))

            elif action == "subscribe":
                channel = message.get("channel")
                if channel:
                    await manager.subscribe(conn_id, channel)
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channel": channel,
                    }))

            elif action == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    await manager.unsubscribe(conn_id, channel)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscribed",
                        "channel": channel,
                    }))

            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await manager.disconnect(conn_id)
    except Exception as e:
        logger.error("Notification WS error for user=%s: %s", user_id, str(e))
        await manager.disconnect(conn_id)
