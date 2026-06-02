import logging
import multiprocessing
import os
import signal
import sys
import threading
import time
from typing import Any

from backend.core.config import settings
from backend.sandbox.executor import cleanup_judge_containers
from backend.services.queue_service import queue_service
from backend.worker.tasks.consumer import JudgeTaskConsumer, handle_task_failure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _judge_child_entrypoint(task: dict[str, Any], message_id: str) -> None:
    """Run one judge task in an isolated child process."""
    queue_service.disconnect()
    os.environ["FASTOJ_JUDGE_SUBMISSION_ID"] = str(task.get("submission_id") or "")
    os.environ["FASTOJ_JUDGE_MESSAGE_ID"] = message_id
    JudgeTaskConsumer().process_task(task, message_id)


class JudgeWorker:
    """Main judge worker that processes submission tasks from the queue."""

    def __init__(self):
        self.running = False
        self.consumer = None
        self.heartbeat_thread: threading.Thread | None = None
        self.process_context = multiprocessing.get_context("spawn")
        self.process_factory = self.process_context.Process
        self.active_child_process = None
        self.active_child_task: dict[str, Any] | None = None
        self.active_child_message_id: str | None = None
        self.active_child_failure_handled = False

    def start(self):
        """Start the judge worker."""
        logger.info("Starting Judge Worker...")
        self.running = True

        # Connect to Redis
        queue_service.connect()

        # Create task consumer
        self.consumer = JudgeTaskConsumer()
        self._start_heartbeat()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Judge Worker started successfully")

        # Main loop
        while self.running:
            try:
                queue_service.mark_worker_alive()
                claimed_tasks = queue_service.claim_pending()
                if claimed_tasks:
                    logger.info("Claimed %s pending judge task(s)", len(claimed_tasks))
                for message_id, task in claimed_tasks:
                    logger.info(f"Received reclaimed task: {task.get('submission_id')}")
                    self.process_task(task, message_id)
                stream_task = queue_service.pop_stream_task(timeout_ms=5000)
                if stream_task:
                    message_id, task = stream_task
                    logger.info(f"Received task: {task.get('submission_id')}")
                    self.process_task(task, message_id)
                else:
                    # No task available, continue
                    pass
            except Exception as e:
                logger.error(f"Error processing task: {e}")

        logger.info("Judge Worker stopped")

    def stop(self):
        """Stop the judge worker."""
        logger.info("Stopping Judge Worker...")
        self.running = False
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)
        queue_service.clear_task_active()
        queue_service.clear_worker_alive()
        queue_service.disconnect()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._stop_active_child("Judge worker stopped while task was active")
        self.stop()
        sys.exit(0)

    def _start_heartbeat(self) -> None:
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="judge-worker-heartbeat",
            daemon=True,
        )
        self.heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        interval = max(1, settings.JUDGE_WORKER_HEARTBEAT_TTL_SECONDS // 3)
        while self.running:
            try:
                queue_service.mark_worker_alive()
            except Exception as exc:
                logger.error("Failed to refresh judge worker heartbeat: %s", exc)
            time.sleep(interval)

    def process_task(self, task: dict[str, Any], message_id: str) -> None:
        if settings.JUDGE_CHILD_PROCESS_ENABLED:
            self.process_task_in_child(task, message_id)
            return
        if self.consumer is None:
            self.consumer = JudgeTaskConsumer()
        self.consumer.process_task(task, message_id)

    def process_task_in_child(self, task: dict[str, Any], message_id: str) -> None:
        submission_id = str(task.get("submission_id") or "")
        if not submission_id:
            logger.error("Task missing submission_id; acking invalid message")
            queue_service.ack_task(message_id)
            return

        deadline_at = time.time() + settings.JUDGE_TASK_HARD_TIMEOUT_SECONDS
        process = None
        try:
            process = self.process_factory(target=_judge_child_entrypoint, args=(task, message_id))
            queue_service.mark_task_active(message_id, submission_id, deadline_at)
            self.active_child_process = process
            self.active_child_task = task
            self.active_child_message_id = message_id
            self.active_child_failure_handled = False
            process.start()
            process.join(timeout=settings.JUDGE_TASK_HARD_TIMEOUT_SECONDS)

            if process.is_alive():
                self._terminate_child(process, "Judge child exceeded hard timeout")
                self._cleanup_child_containers(task, message_id)
                self._handle_child_failure(
                    task,
                    message_id,
                    "Judge child process exceeded hard timeout",
                )
                return

            if process.exitcode == 0:
                logger.info("Judge child completed submission %s", submission_id)
                return

            self._handle_child_failure(
                task,
                message_id,
                f"Judge child process exited with code {process.exitcode}",
            )
        except Exception as exc:
            if process and self._process_is_alive(process):
                self._terminate_child(process, "Judge child supervision failed")
                self._cleanup_child_containers(task, message_id)
            self._handle_child_failure(
                task,
                message_id,
                f"Judge child process failed to start or supervise: {exc}",
            )
        finally:
            try:
                queue_service.clear_task_active()
            except Exception as exc:
                logger.error("Failed to clear active judge task: %s", exc)
            self.active_child_process = None
            self.active_child_task = None
            self.active_child_message_id = None
            self.active_child_failure_handled = False

    def _terminate_child(self, process, reason: str) -> None:
        logger.error("%s; terminating child", reason)
        process.terminate()
        process.join(timeout=settings.JUDGE_CHILD_TERMINATE_GRACE_SECONDS)
        if process.is_alive():
            logger.error("Judge child did not terminate gracefully; killing")
            process.kill()
            process.join(timeout=1)

    def _cleanup_child_containers(self, task: dict[str, Any], message_id: str) -> None:
        submission_id = str(task.get("submission_id") or "")
        if not submission_id:
            return
        removed = cleanup_judge_containers(submission_id, message_id)
        if removed:
            logger.warning("Removed %s leftover judge container(s) for submission %s", removed, submission_id)

    def _handle_child_failure(self, task: dict[str, Any], message_id: str, error_message: str) -> None:
        if self.active_child_failure_handled:
            return
        self.active_child_failure_handled = True
        logger.error("%s", error_message)
        try:
            handle_task_failure(task, message_id, error_message)
        except Exception as exc:
            logger.error("Failed to handle judge child failure: %s", exc)

    def _stop_active_child(self, error_message: str) -> None:
        process = self.active_child_process
        task = self.active_child_task
        message_id = self.active_child_message_id
        if not process or not task or not message_id:
            return
        if self._process_is_alive(process):
            self._terminate_child(process, error_message)
            self._cleanup_child_containers(task, message_id)
            self._handle_child_failure(task, message_id, error_message)
            return
        exitcode = getattr(process, "exitcode", None)
        if exitcode == 0:
            logger.info("Judge child already exited cleanly during shutdown; skipping failure handling")
            return
        if exitcode is not None:
            self._handle_child_failure(task, message_id, f"{error_message}; child exited with code {exitcode}")

    def _process_is_alive(self, process) -> bool:
        try:
            return bool(process.is_alive())
        except Exception:
            return False


if __name__ == "__main__":
    worker = JudgeWorker()
    worker.start()
