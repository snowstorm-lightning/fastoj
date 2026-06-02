import logging
from typing import Any

from backend.core.database import SessionLocal
from backend.models import SubmissionResult, SubmissionStatus
from backend.services.queue_service import queue_service
from backend.services.submission_service import SubmissionService
from backend.worker.tasks.judge_task import JudgeTask

logger = logging.getLogger(__name__)


class JudgeTaskConsumer:
    """Consumes judge tasks from the queue and processes them."""

    def __init__(self):
        self.judge_task = JudgeTask()

    def process_task(self, task: dict[str, Any], message_id: str | None = None):
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
                if message_id:
                    queue_service.ack_task(message_id)
                return

            if submission.status == SubmissionStatus.FINISHED and submission.testcase_results:
                logger.info("Submission %s already judged; acking duplicate task", submission_id)
                if message_id:
                    queue_service.ack_task(message_id)
                return

            # Update status to judging
            service.update_submission_status(
                submission_id,
                SubmissionStatus.JUDGING,
            )

            queue_service.publish_status(
                submission_id,
                "judging",
                {"status": "judging", "progress": 0},
            )

            # Execute judge task
            result = self.judge_task.execute(
                submission_id=submission_id,
                problem_id=str(submission.problem_id),
                code=task.get("code") or submission.code,
                language=submission.language,
                use_hidden=task.get("use_hidden", True),
                db=db,
                run_testcases=task.get("run_testcases"),
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

            queue_service.publish_status(
                submission_id,
                "result",
                {
                    "status": "finished",
                    "result": result.get("result").value if result.get("result") else None,
                    "execute_time": result.get("execute_time", 0),
                    "memory_used": result.get("memory_used", 0),
                    "score": result.get("score", 0),
                },
            )
            if message_id:
                queue_service.ack_task(message_id)

            logger.info(f"Completed judging submission {submission_id}: {result.get('result')}")

        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}")
            error_message = str(e)
            terminal_failure = True

            try:
                if message_id:
                    terminal_failure = queue_service.retry_or_dead_letter(message_id, task, error_message)
            except Exception as retry_error:
                logger.error(f"Failed to retry or dead-letter task: {retry_error}")

            try:
                service = SubmissionService(db)
                if terminal_failure:
                    service.update_submission_status(
                        submission_id,
                        SubmissionStatus.FINISHED,
                        result=SubmissionResult.SE,
                        error_message=error_message,
                    )
                else:
                    service.update_submission_status(submission_id, SubmissionStatus.PENDING)
            except Exception as update_error:
                logger.error(f"Failed to update submission status: {update_error}")

            try:
                if terminal_failure:
                    queue_service.publish_status(
                        submission_id,
                        "error",
                        {"status": "finished", "result": "se", "message": error_message, "code": "JUDGE_ERROR"},
                    )
                else:
                    queue_service.publish_status(
                        submission_id,
                        "pending",
                        {"status": "pending", "message": "Judge task will retry"},
                    )
            except Exception:
                pass

        finally:
            db.close()
