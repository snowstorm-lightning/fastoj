import json

import pytest

from backend.services.queue_service import QueueService, TaskAlreadyHandledError


class FakeRedis:
    def __init__(self):
        self.added = []
        self.acked = []
        self.groups = []
        self.published = []
        self.values = {}
        self.eval_calls = []
        self.xack_result = 1

    def xgroup_create(self, *args, **kwargs):
        self.groups.append((args, kwargs))

    def xadd(self, stream, fields):
        self.added.append((stream, fields))
        return "1-0"

    def xack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))
        return self.xack_result

    def eval(self, script, numkeys, queue_name, target_stream, group_name, message_id, payload):
        self.eval_calls.append(
            {
                "script": script,
                "numkeys": numkeys,
                "queue_name": queue_name,
                "target_stream": target_stream,
                "group_name": group_name,
                "message_id": message_id,
                "payload": payload,
            }
        )
        acked = self.xack(queue_name, group_name, message_id)
        if not acked:
            return [0, False]
        new_message_id = self.xadd(target_stream, {"payload": payload})
        return [acked, new_message_id]

    def publish(self, channel, payload):
        self.published.append((channel, json.loads(payload)))

    def xlen(self, _stream):
        return len(self.added)

    def set(self, key, value, ex=None):
        self.values[key] = {"value": value, "ex": ex}

    def delete(self, key):
        self.values.pop(key, None)

    def get(self, key):
        item = self.values.get(key)
        return item["value"] if item else None

    def exists(self, key):
        return int(key in self.values)

    def scan_iter(self, match=None, count=None):
        prefix = (match or "").rstrip("*")
        for key in list(self.values):
            if not match or key.startswith(prefix):
                yield key

    def xpending_range(self, *args, **kwargs):
        return [
            {
                "message_id": "1-0",
                "consumer": "stale-worker",
                "time_since_delivered": 60000,
            }
        ]

    def xclaim(self, stream, group, consumer, min_idle_time, message_ids):
        return [
            (
                message_ids[0],
                {"payload": json.dumps({"submission_id": "s1", "attempt": 1})},
            )
        ]


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
    terminal = queue.retry_or_dead_letter("1-0", {"submission_id": "s1"}, "boom")
    streams = [item[0] for item in queue.redis_client.added]
    assert terminal is True
    assert queue.dead_letter_name in streams
    assert queue.redis_client.acked
    eval_call = queue.redis_client.eval_calls[0]
    assert eval_call["target_stream"] == queue.dead_letter_name


def test_retry_before_dead_letter_returns_non_terminal(monkeypatch):
    queue = QueueService()
    queue.redis_client = FakeRedis()
    monkeypatch.setattr("backend.services.queue_service.settings.JUDGE_TASK_MAX_RETRIES", 3)
    terminal = queue.retry_or_dead_letter("1-0", {"submission_id": "s1"}, "boom")
    streams = [item[0] for item in queue.redis_client.added]
    assert terminal is False
    assert queue.queue_name in streams
    assert queue.dead_letter_name not in streams
    assert queue.redis_client.acked
    eval_call = queue.redis_client.eval_calls[0]
    assert eval_call["target_stream"] == queue.queue_name


def test_retry_does_not_enqueue_when_original_message_already_acked(monkeypatch):
    queue = QueueService()
    queue.redis_client = FakeRedis()
    queue.redis_client.xack_result = 0
    monkeypatch.setattr("backend.services.queue_service.settings.JUDGE_TASK_MAX_RETRIES", 3)

    with pytest.raises(TaskAlreadyHandledError):
        queue.retry_or_dead_letter("1-0", {"submission_id": "s1"}, "boom")

    assert queue.redis_client.acked == [(queue.queue_name, queue.group_name, "1-0")]
    assert queue.redis_client.added == []


def test_claim_pending_returns_claimed_payload(monkeypatch):
    queue = QueueService()
    queue.redis_client = FakeRedis()
    monkeypatch.setattr("backend.services.queue_service.settings.JUDGE_PENDING_IDLE_MS", 30000)
    claimed = queue.claim_pending()
    assert claimed == [("1-0", {"submission_id": "s1", "attempt": 1})]


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


def test_active_task_marker_lifecycle(monkeypatch):
    queue = QueueService()
    queue.redis_client = FakeRedis()
    monkeypatch.setattr("backend.services.queue_service.settings.JUDGE_ACTIVE_TASK_TTL_SECONDS", 180)

    queue.mark_task_active("1-0", "s1", 1234.0)
    active = queue.get_active_task()
    assert active is not None
    assert active["consumer_name"] == queue.consumer_name
    assert active["message_id"] == "1-0"
    assert active["submission_id"] == "s1"
    assert active["deadline_at"] == 1234.0
    assert queue.redis_client.values[queue.active_task_key()]["ex"] == 180

    queue.touch_active_task(progress=50)
    touched = queue.get_active_task()
    assert touched is not None
    assert touched["progress"] == 50
    assert touched["last_progress_at"] >= active["last_progress_at"]

    queue.clear_task_active()
    assert queue.get_active_task() is None
