import logging
import signal
import sys

from backend.services.queue_service import queue_service
from backend.worker.tasks.consumer import JudgeTaskConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JudgeWorker:
    """Main judge worker that processes submission tasks from the queue."""

    def __init__(self):
        self.running = False
        self.consumer = None

    def start(self):
        """Start the judge worker."""
        logger.info("Starting Judge Worker...")
        self.running = True

        # Connect to Redis
        queue_service.connect()

        # Create task consumer
        self.consumer = JudgeTaskConsumer()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Judge Worker started successfully")

        # Main loop
        while self.running:
            try:
                queue_service.mark_worker_alive()
                queue_service.reclaim_pending()
                stream_task = queue_service.pop_stream_task(timeout_ms=5000)
                if stream_task:
                    message_id, task = stream_task
                    logger.info(f"Received task: {task.get('submission_id')}")
                    self.consumer.process_task(task, message_id)
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
        queue_service.clear_worker_alive()
        queue_service.disconnect()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)


if __name__ == "__main__":
    worker = JudgeWorker()
    worker.start()
