import asyncio
import json
import logging

import redis.asyncio as redis

from backend.api.websocket.manager import manager
from backend.core.config import settings

logger = logging.getLogger(__name__)


async def relay_judge_status_events(stop_event: asyncio.Event):
    """Relay Redis pub/sub judge events to in-process WebSocket clients."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(settings.JUDGE_STATUS_CHANNEL)
    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                continue
            try:
                payload = json.loads(message["data"])
                await manager.broadcast_event(
                    payload["submission_id"],
                    payload.get("type", "progress"),
                    payload.get("data", {}),
                )
            except Exception as exc:
                logger.warning("Failed to relay judge status event: %s", exc)
    finally:
        await pubsub.unsubscribe(settings.JUDGE_STATUS_CHANNEL)
        await pubsub.close()
        await client.close()
