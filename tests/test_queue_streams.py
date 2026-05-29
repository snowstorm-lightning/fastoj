import json

from backend.services.queue_service import QueueService


class FakeRedis:
    def __init__(self):
        self.added = []
        self.acked = []
        self.groups = []
        self.published = []
        self.values = {}

    def xgroup_create(self, *args, **kwargs):
        self.groups.append((args, kwargs))

    def xadd(self, stream, fields):
        self.added.append((stream, fields))
        return "1-0"

    def xack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))

    def publish(self, channel, payload):
        self.published.append((channel, json.loads(payload)))

    def xlen(self, _stream):
        return len(self.added)

    def set(self, key, value, ex=None):
        self.values[key] = {"value": value, "ex": ex}

    def delete(self, key):
        self.values.pop(key, None)

    def scan_iter(self, match=None, count=None):
        prefix = (match or "").rstrip("*")
        for key in list(self.values):
            if not match or key.startswith(prefix):
                yield key


def test_queue_enqueue_and_ack():
    queue = QueueService()
    queue.redis_client = FakeRedis()
    message_id = queue.push_task({"submission_id": "s1"})
    queue.ack_task(message_id)
    assert message_id == "1-0"
    assert queue.redis_client.acked[0][2] == "1-0"


def test_retry_then_dead_letter(monkeypatch):
    queue = QueueService()
    queue.redis_client = FakeRedis()
    monkeypatch.setattr("backend.services.queue_service.settings.JUDGE_TASK_MAX_RETRIES", 1)
    queue.retry_or_dead_letter("1-0", {"submission_id": "s1"}, "boom")
    streams = [item[0] for item in queue.redis_client.added]
    assert queue.dead_letter_name in streams
    assert queue.redis_client.acked


def test_publish_status_event():
    queue = QueueService()
    queue.redis_client = FakeRedis()
    queue.publish_status("s1", "judging", {"progress": 10})
    _, payload = queue.redis_client.published[0]
    assert payload["submission_id"] == "s1"
    assert payload["type"] == "judging"


def test_worker_heartbeat_marks_and_clears_live_worker():
    queue = QueueService()
    queue.redis_client = FakeRedis()

    assert queue.has_live_worker() is False

    queue.mark_worker_alive()
    assert queue.has_live_worker() is True
    key = queue.worker_heartbeat_key()
    assert queue.redis_client.values[key]["ex"] > 0

    queue.clear_worker_alive()
    assert queue.has_live_worker() is False
