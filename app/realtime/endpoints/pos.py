import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.realtime.manager import manager
from app.realtime.channels import Channel

logger = logging.getLogger("realtime.pos")
router = APIRouter()


@router.websocket("/ws/pos/{session_id}")
async def pos_session_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
):
    """Real-time POS session updates.

    Streams live cart changes, payment status, receipt generation,
    and session sync across multiple terminals for the same branch.
    """
    from app.core.security.tokens import decode_access_token

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    branch_id = payload.get("branch_id", "default")

    if not user_id or not tenant_id:
        await websocket.close(code=4001, reason="Invalid token claims")
        return

    conn_id = await manager.connect(websocket, user_id, tenant_id)

    # Subscribe to session-specific and branch-wide POS channels
    session_channel = Channel.pos_session(tenant_id, session_id)
    branch_channel = Channel.pos_branch(tenant_id, branch_id)
    await manager.subscribe(conn_id, session_channel)
    await manager.subscribe(conn_id, branch_channel)

    await websocket.send_text(json.dumps({
        "type": "connected",
        "channel": "pos",
        "session_id": session_id,
        "branch_id": branch_id,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")

            if action == "cart_update":
                # Broadcast cart state to all terminals in this session
                await manager.send_to_channel(session_channel, {
                    "type": "cart_updated",
                    "session_id": session_id,
                    "user_id": user_id,
                    "items": message.get("items", []),
                    "subtotal": message.get("subtotal"),
                    "tax": message.get("tax"),
                    "total": message.get("total"),
                })

            elif action == "payment_initiated":
                await manager.send_to_channel(session_channel, {
                    "type": "payment_processing",
                    "session_id": session_id,
                    "method": message.get("method"),
                    "amount": message.get("amount"),
                })

            elif action == "payment_completed":
                await manager.send_to_channel(session_channel, {
                    "type": "payment_completed",
                    "session_id": session_id,
                    "transaction_id": message.get("transaction_id"),
                    "method": message.get("method"),
                    "amount": message.get("amount"),
                })
                # Notify branch for dashboard aggregation
                await manager.send_to_channel(branch_channel, {
                    "type": "sale_completed",
                    "session_id": session_id,
                    "amount": message.get("amount"),
                })

            elif action == "void_item":
                await manager.send_to_channel(session_channel, {
                    "type": "item_voided",
                    "session_id": session_id,
                    "item_id": message.get("item_id"),
                    "reason": message.get("reason"),
                    "voided_by": user_id,
                })

            elif action == "hold_order":
                await manager.send_to_channel(session_channel, {
                    "type": "order_held",
                    "session_id": session_id,
                    "order_ref": message.get("order_ref"),
                    "held_by": user_id,
                })

            elif action == "recall_order":
                await manager.send_to_channel(session_channel, {
                    "type": "order_recalled",
                    "session_id": session_id,
                    "order_ref": message.get("order_ref"),
                    "recalled_by": user_id,
                })

            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await manager.disconnect(conn_id)
    except Exception as e:
        logger.error("POS WS error session=%s user=%s: %s", session_id, user_id, str(e))
        await manager.disconnect(conn_id)
