import inspect
import logging
from typing import Any

from backend.core.database import SessionLocal
from backend.models import SubmissionResult, SubmissionStatus
from backend.services.queue_service import TaskAlreadyHandledError, queue_service
from backend.services.submission_service import SubmissionService
from backend.worker.tasks.judge_task import JudgeTask

logger = logging.getLogger(__name__)


def handle_task_failure(
    task: dict[str, Any],
    message_id: str | None,
    error_message: str,
    db=None,
) -> bool:
    """Retry/dead-letter a failed task and update submission state.

    Returns true when the failure is terminal.
    """
    submission_id = task.get("submission_id")
    terminal_failure = True
    owns_db = db is None
    db = db or SessionLocal()
    try:
        service = SubmissionService(db)
        try:
            submission = service.get_submission_for_judge(submission_id) if submission_id else None
            existing_results = list(getattr(submission, "testcase_results", []) or []) if submission else []
            if existing_results:
                if getattr(submission, "status", None) != SubmissionStatus.FINISHED:
                    result = JudgeTask().summarize_existing_results(db, existing_results)
                    service.update_submission_status(
                        submission_id,
                        SubmissionStatus.FINISHED,
                        result=result.get("result"),
                        error_message=result.get("error_message"),
                        execute_time=result.get("execute_time"),
                        memory_used=result.get("memory_used"),
                        score=result.get("score", 0),
                    )
                    try:
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
                    except Exception:
                        pass
                if message_id:
                    try:
                        queue_service.ack_task(message_id)
                    except Exception as ack_error:
                        logger.error(f"Failed to ack recovered duplicate task: {ack_error}")
                return True
        except Exception as recovery_error:
            logger.error(f"Failed to recover already persisted judge results: {recovery_error}")

        try:
            if message_id:
                terminal_failure = queue_service.retry_or_dead_letter(message_id, task, error_message)
        except TaskAlreadyHandledError as handled_error:
            logger.info("Judge task failure already handled elsewhere: %s", handled_error)
            return True
        except Exception as retry_error:
            logger.error(f"Failed to retry or dead-letter task: {retry_error}")

        try:
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

        return terminal_failure
    finally:
        if owns_db:
            db.close()


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
            judge_kwargs = {
                "submission_id": submission_id,
                "problem_id": str(submission.problem_id),
                "code": task.get("code") or submission.code,
                "language": submission.language,
                "use_hidden": task.get("use_hidden", True),
                "db": db,
                "run_testcases": task.get("run_testcases"),
            }
            execute_signature = inspect.signature(self.judge_task.execute)
            if "judge_mode" in execute_signature.parameters or any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in execute_signature.parameters.values()
            ):
                judge_kwargs["judge_mode"] = str(task.get("judge_mode") or "acm")
            result = self.judge_task.execute(**judge_kwargs)

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
            handle_task_failure(task, message_id, str(e), db=db)

        finally:
            db.close()
