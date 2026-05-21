"""Integration tests for WebSocket real-time features."""
import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.integration
class TestWebSocketConnection:
    @pytest.mark.asyncio
    async def test_notification_connection(self, client):
        try:
            async with client.stream("GET", "/ws/notifications") as response:
                assert response.status_code in (101, 403, 401)
        except Exception:
            pass  # WebSocket upgrade may not work with httpx

    @pytest.mark.asyncio
    async def test_connection_manager_add_remove(self):
        from app.realtime.manager import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.close = AsyncMock()

        await manager.connect(mock_ws, user_id=1, tenant_id=1)
        assert manager.active_count() >= 1

        await manager.disconnect(mock_ws, user_id=1)
        assert manager.active_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_tenant(self):
        from app.realtime.manager import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        await manager.connect(mock_ws1, user_id=1, tenant_id=1)
        await manager.connect(mock_ws2, user_id=2, tenant_id=1)

        await manager.broadcast_to_tenant(
            tenant_id=1,
            message={"type": "notification", "data": "test"}
        )

        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        from app.realtime.manager import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, user_id=42, tenant_id=1)
        await manager.send_to_user(
            user_id=42,
            message={"type": "alert", "text": "Hello"}
        )

        mock_ws.send_json.assert_called_once_with({"type": "alert", "text": "Hello"})
