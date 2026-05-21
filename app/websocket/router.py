from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security.jwt import decode_token
from app.websocket.manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    try:
        payload = decode_token(token)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["sub"]
    tenant_id = payload["tenant_id"]

    await manager.connect(websocket, tenant_id, user_id)
    logger.info(f"WebSocket connected: user={user_id} tenant={tenant_id}")

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif event_type == "subscribe":
                channel = data.get("channel")
                logger.info(f"User {user_id} subscribed to {channel}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id, user_id)
        logger.info(f"WebSocket disconnected: user={user_id}")
