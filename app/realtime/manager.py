import json
import logging
import asyncio
from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("realtime")


@dataclass
class ClientConnection:
    websocket: WebSocket
    user_id: str
    tenant_id: str
    channels: set[str] = field(default_factory=set)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, ClientConnection] = {}
        self._channels: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        tenant_id: str,
    ) -> str:
        await websocket.accept()
        conn_id = f"{tenant_id}:{user_id}:{id(websocket)}"

        async with self._lock:
            self._connections[conn_id] = ClientConnection(
                websocket=websocket,
                user_id=user_id,
                tenant_id=tenant_id,
            )

        logger.info("WebSocket connected: %s (user=%s, tenant=%s)", conn_id, user_id, tenant_id)
        return conn_id

    async def disconnect(self, conn_id: str):
        async with self._lock:
            conn = self._connections.pop(conn_id, None)
            if conn:
                for channel in conn.channels:
                    self._channels.get(channel, set()).discard(conn_id)
                    if not self._channels.get(channel):
                        self._channels.pop(channel, None)

        logger.info("WebSocket disconnected: %s", conn_id)

    async def subscribe(self, conn_id: str, channel: str):
        async with self._lock:
            conn = self._connections.get(conn_id)
            if conn:
                conn.channels.add(channel)
                if channel not in self._channels:
                    self._channels[channel] = set()
                self._channels[channel].add(conn_id)

    async def unsubscribe(self, conn_id: str, channel: str):
        async with self._lock:
            conn = self._connections.get(conn_id)
            if conn:
                conn.channels.discard(channel)
                self._channels.get(channel, set()).discard(conn_id)

    async def send_to_user(self, tenant_id: str, user_id: str, message: dict):
        targets = []
        async with self._lock:
            for conn_id, conn in self._connections.items():
                if conn.tenant_id == tenant_id and conn.user_id == user_id:
                    targets.append(conn.websocket)

        await self._broadcast_to(targets, message)

    async def send_to_channel(self, channel: str, message: dict):
        targets = []
        async with self._lock:
            conn_ids = self._channels.get(channel, set()).copy()
            for conn_id in conn_ids:
                conn = self._connections.get(conn_id)
                if conn:
                    targets.append(conn.websocket)

        await self._broadcast_to(targets, message)

    async def send_to_tenant(self, tenant_id: str, message: dict):
        targets = []
        async with self._lock:
            for conn in self._connections.values():
                if conn.tenant_id == tenant_id:
                    targets.append(conn.websocket)

        await self._broadcast_to(targets, message)

    async def broadcast(self, message: dict):
        targets = []
        async with self._lock:
            targets = [conn.websocket for conn in self._connections.values()]

        await self._broadcast_to(targets, message)

    async def _broadcast_to(self, targets: list[WebSocket], message: dict):
        payload = json.dumps(message, default=str)
        disconnected = []

        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

    def get_connection_count(self) -> int:
        return len(self._connections)

    def get_channel_count(self, channel: str) -> int:
        return len(self._channels.get(channel, set()))

    def get_user_connections(self, tenant_id: str, user_id: str) -> int:
        return sum(
            1 for conn in self._connections.values()
            if conn.tenant_id == tenant_id and conn.user_id == user_id
        )


manager = ConnectionManager()
