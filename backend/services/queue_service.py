import json
import socket
from typing import Any

import redis

from backend.core.config import settings


class QueueService:
    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.queue_name = settings.JUDGE_STREAM_NAME
        self.group_name = settings.JUDGE_CONSUMER_GROUP
        self.dead_letter_name = settings.JUDGE_DEAD_LETTER_STREAM
        self.status_channel = settings.JUDGE_STATUS_CHANNEL
        self.consumer_name = f"{socket.gethostname()}-worker"

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
        """Push a task to the Redis Stream queue."""
        self.connect()
        task_data.setdefault("attempt", 0)
        self.ensure_group()
        return self.redis_client.xadd(  # type: ignore[union-attr,return-value]
            self.queue_name,
            {"payload": json.dumps(task_data)},
        )

    def ensure_group(self) -> None:
        self.connect()
        try:
            self.redis_client.xgroup_create(self.queue_name, self.group_name, id="0", mkstream=True)  # type: ignore[union-attr]
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def pop_stream_task(self, timeout_ms: int = 5000) -> tuple[str, dict[str, Any]] | None:
        """Read one task from the consumer group."""
        self.connect()
        self.ensure_group()
        result = self.redis_client.xreadgroup(  # type: ignore[union-attr]
            self.group_name,
            self.consumer_name,
            {self.queue_name: ">"},
            count=1,
            block=timeout_ms,
        )
        if not result:
            return None
        _, messages = result[0]
        message_id, fields = messages[0]
        return message_id, json.loads(fields["payload"])

    def ack_task(self, message_id: str) -> None:
        self.connect()
        self.redis_client.xack(self.queue_name, self.group_name, message_id)  # type: ignore[union-attr]

    def retry_or_dead_letter(self, message_id: str, task_data: dict[str, Any], error: str) -> None:
        self.connect()
        attempt = int(task_data.get("attempt", 0)) + 1
        task_data["attempt"] = attempt
        task_data["last_error"] = error
        if attempt >= settings.JUDGE_TASK_MAX_RETRIES:
            self.redis_client.xadd(self.dead_letter_name, {"payload": json.dumps(task_data)})  # type: ignore[union-attr]
            self.ack_task(message_id)
            return
        self.redis_client.xadd(self.queue_name, {"payload": json.dumps(task_data)})  # type: ignore[union-attr]
        self.ack_task(message_id)

    def reclaim_pending(self) -> int:
        """Reclaim idle pending tasks for this consumer. Returns claimed count."""
        self.connect()
        self.ensure_group()
        try:
            pending = self.redis_client.xpending_range(  # type: ignore[union-attr]
                self.queue_name,
                self.group_name,
                min="-",
                max="+",
                count=10,
            )
        except redis.ResponseError:
            return 0
        claimed = 0
        for item in pending:
            if item.get("time_since_delivered", 0) < settings.JUDGE_PENDING_IDLE_MS:
                continue
            message_id = item["message_id"]
            self.redis_client.xclaim(  # type: ignore[union-attr]
                self.queue_name,
                self.group_name,
                self.consumer_name,
                settings.JUDGE_PENDING_IDLE_MS,
                [message_id],
            )
            claimed += 1
        return claimed

    def pop_task(self, timeout: int = 0) -> dict[str, Any] | None:
        """Compatibility wrapper returning only payload."""
        stream_task = self.pop_stream_task(timeout_ms=timeout * 1000 if timeout else 0)
        return stream_task[1] if stream_task else None

    def get_queue_length(self) -> int:
        """Get the length of the queue."""
        self.connect()
        return self.redis_client.xlen(self.queue_name)  # type: ignore[union-attr,return-value]

    def publish_result(self, channel: str, message: dict[str, Any]):
        """Publish a message to a channel (for WebSocket)."""
        self.connect()
        self.redis_client.publish(channel, json.dumps(message))  # type: ignore[union-attr]

    def publish_status(self, submission_id: str, event_type: str, data: dict[str, Any] | None = None):
        payload = {
            "type": event_type,
            "submission_id": submission_id,
            "data": data or {},
        }
        self.publish_result(self.status_channel, payload)

    def subscribe(self, channel: str | None = None):
        """Subscribe to a channel."""
        self.connect()
        pubsub = self.redis_client.pubsub()  # type: ignore[union-attr]
        pubsub.subscribe(channel or self.status_channel)
        return pubsub


queue_service = QueueService()
