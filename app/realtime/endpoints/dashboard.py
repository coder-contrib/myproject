import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.realtime.manager import manager
from app.realtime.channels import Channel

logger = logging.getLogger("realtime.dashboard")
router = APIRouter()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    branch_id: str = Query(default=None),
):
    """Live dashboard metrics WebSocket endpoint.

    Streams real-time KPIs: revenue, order count, active POS sessions,
    low stock alerts, and top-selling products. Optionally scoped to a branch.
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

    # Subscribe to dashboard channels
    dashboard_channel = Channel.dashboard(tenant_id)
    await manager.subscribe(conn_id, dashboard_channel)

    if branch_id:
        branch_dashboard = Channel.dashboard_branch(tenant_id, branch_id)
        await manager.subscribe(conn_id, branch_dashboard)

    # Also subscribe to inventory and sales for live feed
    await manager.subscribe(conn_id, Channel.inventory(tenant_id))
    await manager.subscribe(conn_id, Channel.sales(tenant_id))

    await websocket.send_text(json.dumps({
        "type": "connected",
        "channel": "dashboard",
        "tenant_id": tenant_id,
        "branch_id": branch_id,
    }))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")

            if action == "request_snapshot":
                # Client requests current metrics snapshot
                await websocket.send_text(json.dumps({
                    "type": "snapshot_requested",
                    "status": "processing",
                }))

            elif action == "set_filters":
                # Client updates their dashboard filter preferences
                filters = message.get("filters", {})
                await websocket.send_text(json.dumps({
                    "type": "filters_applied",
                    "filters": filters,
                }))

            elif action == "subscribe_metric":
                metric_channel = message.get("channel")
                if metric_channel:
                    await manager.subscribe(conn_id, metric_channel)
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channel": metric_channel,
                    }))

            elif action == "unsubscribe_metric":
                metric_channel = message.get("channel")
                if metric_channel:
                    await manager.unsubscribe(conn_id, metric_channel)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscribed",
                        "channel": metric_channel,
                    }))

            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await manager.disconnect(conn_id)
    except Exception as e:
        logger.error("Dashboard WS error user=%s: %s", user_id, str(e))
        await manager.disconnect(conn_id)
