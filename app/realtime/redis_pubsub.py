import os
import json
import asyncio
import logging

import redis.asyncio as aioredis

from app.realtime.manager import manager

logger = logging.getLogger("realtime.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisPubSub:
    """Bridges Redis pub/sub with WebSocket connections for cross-process messaging."""

    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._listener_task: asyncio.Task | None = None
        self._running = False

    async def connect(self):
        self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe("__system__")
        self._running = True
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("Redis pub/sub connected")

    async def disconnect(self):
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("Redis pub/sub disconnected")

    async def subscribe(self, channel: str):
        if self._pubsub:
            await self._pubsub.subscribe(channel)

    async def unsubscribe(self, channel: str):
        if self._pubsub:
            await self._pubsub.unsubscribe(channel)

    async def publish(self, channel: str, message: dict):
        if self._redis:
            await self._redis.publish(channel, json.dumps(message, default=str))

    async def _listen(self):
        while self._running:
            try:
                if self._pubsub:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    if message and message["type"] == "message":
                        channel = message["channel"]
                        if channel == "__system__":
                            continue
                        data = json.loads(message["data"])
                        await manager.send_to_channel(channel, data)
                else:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Redis listener error: %s", e)
                await asyncio.sleep(1)


pubsub = RedisPubSub()
