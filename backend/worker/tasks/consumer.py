import logging
from typing import Any

from backend.api.websocket.manager import manager
from backend.core.database import SessionLocal
from backend.models import SubmissionStatus
from backend.services.submission_service import SubmissionService
from backend.worker.tasks.judge_task import JudgeTask

logger = logging.getLogger(__name__)


class JudgeTaskConsumer:
    """Consumes judge tasks from the queue and processes them."""

    def __init__(self):
        self.judge_task = JudgeTask()

    def process_task(self, task: dict[str, Any]):
        """Process a single judge task."""
        submission_id = task.get("submission_id")
        if not submission_id:
            logger.error("Task missing submission_id")
            return

        db = SessionLocal()
        try:
            service = SubmissionService(db)

            # Get submission
            submission = service.get_submission_for_judge(submission_id)
            if not submission:
                logger.error(f"Submission {submission_id} not found")
                return

            # Update status to judging
            service.update_submission_status(
                submission_id,
                SubmissionStatus.JUDGING,
            )

            # Notify via WebSocket
            import asyncio

            async def notify():
                await manager.send_status_update(
                    submission_id,
                    "judging",
                    progress=0,
                    current_testcase=0,
                    total_testcases=0,
                )

            asyncio.run(notify())

            # Execute judge task
            result = self.judge_task.execute(
                submission_id=submission_id,
                problem_id=str(submission.problem_id),
                code=submission.code,
                language=submission.language,
                use_hidden=task.get("use_hidden", True),
                db=db,
            )

            # Update submission with results
            service.update_submission_status(
                submission_id,
                SubmissionStatus.FINISHED,
                result=result.get("result"),
                error_message=result.get("error_message"),
                execute_time=result.get("execute_time"),
                memory_used=result.get("memory_used"),
                score=result.get("score", 0),
            )

            # Notify final result via WebSocket
            async def notify_result():
                await manager.send_result(
                    submission_id,
                    "finished",
                    result=result.get("result").value if result.get("result") else None,
                    execute_time=result.get("execute_time", 0),
                    memory_used=result.get("memory_used", 0),
                    score=result.get("score", 0),
                )

            asyncio.run(notify_result())

            logger.info(f"Completed judging submission {submission_id}: {result.get('result')}")

        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}")
            error_message = str(e)

            # Update status to error
            try:
                service = SubmissionService(db)
                service.update_submission_status(
                    submission_id,
                    SubmissionStatus.FINISHED,
                    error_message=error_message,
                )
            except Exception as update_error:
                logger.error(f"Failed to update submission status: {update_error}")

            # Notify error via WebSocket
            async def notify_error():
                await manager.send_error(submission_id, error_message, "JUDGE_ERROR")

            try:
                asyncio.run(notify_error())
            except Exception:
                pass

        finally:
            db.close()
