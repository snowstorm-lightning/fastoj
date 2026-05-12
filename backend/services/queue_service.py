import json
from typing import Any

import redis

from backend.core.config import settings


class QueueService:
    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.queue_name = settings.JUDGE_QUEUE_NAME

    def connect(self):
        """Connect to Redis."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )

    def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None

    def push_task(self, task_data: dict[str, Any]) -> str:
        """Push a task to the queue."""
        self.connect()
        task_json = json.dumps(task_data)
        self.redis_client.lpush(self.queue_name, task_json)  # type: ignore[union-attr]
        return task_data.get("submission_id", "")

    def pop_task(self, timeout: int = 0) -> dict[str, Any] | None:
        """Pop a task from the queue. Blocks if timeout > 0."""
        self.connect()
        if timeout > 0:
            result = self.redis_client.brpop(self.queue_name, timeout=timeout)  # type: ignore[union-attr]
            if result:
                _, task_json = result  # type: ignore[misc]
                return json.loads(task_json)  # type: ignore[arg-type]
        else:
            result = self.redis_client.rpop(self.queue_name)  # type: ignore[union-attr]
            if result:
                return json.loads(result)  # type: ignore[arg-type]
        return None

    def get_queue_length(self) -> int:
        """Get the length of the queue."""
        self.connect()
        return self.redis_client.llen(self.queue_name)  # type: ignore[union-attr,return-value]

    def publish_result(self, channel: str, message: dict[str, Any]):
        """Publish a message to a channel (for WebSocket)."""
        self.connect()
        self.redis_client.publish(channel, json.dumps(message))  # type: ignore[union-attr]

    def subscribe(self, channel: str):
        """Subscribe to a channel."""
        self.connect()
        return self.redis_client.pubsub()  # type: ignore[union-attr]


queue_service = QueueService()
