import json
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        await websocket.accept()
        if tenant_id not in self._connections:
            self._connections[tenant_id] = set()
        self._connections[tenant_id].add(websocket)

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        if tenant_id in self._connections:
            self._connections[tenant_id].discard(websocket)
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)

    async def send_to_user(self, user_id: str, message: dict):
        connections = self._user_connections.get(user_id, set())
        for connection in connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                connections.discard(connection)

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        connections = self._connections.get(tenant_id, set())
        for connection in connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                connections.discard(connection)

    async def broadcast_all(self, message: dict):
        for tenant_connections in self._connections.values():
            for connection in tenant_connections.copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    tenant_connections.discard(connection)


manager = ConnectionManager()
