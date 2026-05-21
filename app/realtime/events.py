"""Event emitters for pushing real-time updates through WebSocket channels."""
import json
import logging
from typing import Optional

from app.realtime.manager import manager
from app.realtime.channels import Channel

logger = logging.getLogger("realtime.events")


class NotificationEvent:
    """Emit real-time notifications to users."""

    @staticmethod
    async def send(
        tenant_id: str,
        user_id: str,
        title: str,
        body: str,
        category: str = "general",
        data: Optional[dict] = None,
    ):
        channel = Channel.notifications(tenant_id, user_id)
        await manager.send_to_channel(channel, {
            "type": "notification",
            "title": title,
            "body": body,
            "category": category,
            "data": data or {},
        })

    @staticmethod
    async def send_to_tenant(
        tenant_id: str,
        title: str,
        body: str,
        category: str = "system",
    ):
        await manager.send_to_tenant(tenant_id, {
            "type": "notification",
            "title": title,
            "body": body,
            "category": category,
        })


class POSEvent:
    """Emit real-time POS updates."""

    @staticmethod
    async def sale_completed(
        tenant_id: str,
        session_id: str,
        branch_id: str,
        amount: str,
        items_count: int,
        payment_method: str,
    ):
        session_channel = Channel.pos_session(tenant_id, session_id)
        branch_channel = Channel.pos_branch(tenant_id, branch_id)

        sale_data = {
            "type": "sale_completed",
            "session_id": session_id,
            "branch_id": branch_id,
            "amount": amount,
            "items_count": items_count,
            "payment_method": payment_method,
        }

        await manager.send_to_channel(session_channel, sale_data)
        await manager.send_to_channel(branch_channel, sale_data)

        # Also push to dashboard channel
        dashboard_channel = Channel.dashboard(tenant_id)
        await manager.send_to_channel(dashboard_channel, {
            "type": "metric_update",
            "metric": "revenue",
            "delta": amount,
            "branch_id": branch_id,
        })

    @staticmethod
    async def session_opened(tenant_id: str, session_id: str, branch_id: str, cashier: str):
        branch_channel = Channel.pos_branch(tenant_id, branch_id)
        await manager.send_to_channel(branch_channel, {
            "type": "session_opened",
            "session_id": session_id,
            "cashier": cashier,
        })

    @staticmethod
    async def session_closed(tenant_id: str, session_id: str, branch_id: str, total_sales: str):
        branch_channel = Channel.pos_branch(tenant_id, branch_id)
        await manager.send_to_channel(branch_channel, {
            "type": "session_closed",
            "session_id": session_id,
            "total_sales": total_sales,
        })


class DashboardEvent:
    """Emit real-time dashboard metric updates."""

    @staticmethod
    async def revenue_update(
        tenant_id: str,
        total_today: str,
        delta: str,
        branch_id: Optional[str] = None,
    ):
        channel = Channel.dashboard(tenant_id)
        payload = {
            "type": "metric_update",
            "metric": "revenue",
            "total_today": total_today,
            "delta": delta,
        }

        await manager.send_to_channel(channel, payload)

        if branch_id:
            branch_channel = Channel.dashboard_branch(tenant_id, branch_id)
            payload["branch_id"] = branch_id
            await manager.send_to_channel(branch_channel, payload)

    @staticmethod
    async def order_count_update(tenant_id: str, total_today: int, delta: int = 1):
        channel = Channel.dashboard(tenant_id)
        await manager.send_to_channel(channel, {
            "type": "metric_update",
            "metric": "order_count",
            "total_today": total_today,
            "delta": delta,
        })

    @staticmethod
    async def low_stock_alert(
        tenant_id: str,
        product_id: str,
        product_name: str,
        current_qty: int,
        reorder_level: int,
    ):
        channel = Channel.inventory(tenant_id)
        await manager.send_to_channel(channel, {
            "type": "low_stock_alert",
            "product_id": product_id,
            "product_name": product_name,
            "current_qty": current_qty,
            "reorder_level": reorder_level,
        })

        # Also push to dashboard
        dashboard_channel = Channel.dashboard(tenant_id)
        await manager.send_to_channel(dashboard_channel, {
            "type": "alert",
            "alert_type": "low_stock",
            "product_name": product_name,
            "current_qty": current_qty,
        })

    @staticmethod
    async def active_sessions_update(tenant_id: str, count: int):
        channel = Channel.dashboard(tenant_id)
        await manager.send_to_channel(channel, {
            "type": "metric_update",
            "metric": "active_pos_sessions",
            "count": count,
        })

    @staticmethod
    async def top_products_update(tenant_id: str, products: list[dict]):
        channel = Channel.dashboard(tenant_id)
        await manager.send_to_channel(channel, {
            "type": "metric_update",
            "metric": "top_products",
            "products": products,
        })
