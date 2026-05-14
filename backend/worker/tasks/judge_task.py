import json
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.core.languages import Language
from backend.models import Problem, SubmissionResult, TestCaseResult
from backend.sandbox.executor import SandboxExecutor
from backend.services.problem_service import ProblemService

logger = logging.getLogger(__name__)


class JudgeTask:
    """Executes the judge process for a submission."""

    def __init__(self):
        self.executor = SandboxExecutor()

    def execute(
        self,
        submission_id: str,
        problem_id: str,
        code: str,
        language: str,
        use_hidden: bool,
        db: Session,
    ) -> dict[str, Any]:
        """Execute the judge task."""
        try:
            # Get problem and testcases
            problem_service = ProblemService(db)
            problem = db.query(Problem).filter(Problem.id == problem_id).first()

            if not problem:
                return {
                    "result": SubmissionResult.SE,
                    "error_message": f"Problem {problem_id} not found",
                    "execute_time": 0,
                    "memory_used": 0,
                    "score": 0,
                }

            if not Language.is_supported(language):
                return {
                    "result": SubmissionResult.SE,
                    "error_message": f"Unsupported language: {language}",
                    "execute_time": 0,
                    "memory_used": 0,
                    "score": 0,
                }

            existing_results = (
                db.query(TestCaseResult).filter(TestCaseResult.submission_id == submission_id).count()
            )
            if existing_results:
                logger.info("Submission %s already has testcase results; skipping duplicate write", submission_id)
                return {
                    "result": SubmissionResult.SE,
                    "error_message": "Duplicate judge task ignored",
                    "execute_time": 0,
                    "memory_used": 0,
                    "score": 0,
                }

            # Get testcases based on use_hidden flag
            if use_hidden:
                testcases = problem_service.get_all_testcases(problem_id)
            else:
                testcases = problem_service.get_public_testcases(problem_id)

            if not testcases:
                return {
                    "result": SubmissionResult.WA,
                    "error_message": "No testcases available",
                    "execute_time": 0,
                    "memory_used": 0,
                    "score": 0,
                }

            # Execute testcases using sandbox
            results = []
            total_score = 0
            total_execute_time = 0
            max_memory_used = 0

            for i, testcase in enumerate(testcases):
                result = self._execute_testcase(
                    code=code,
                    language=language,
                    input_data=testcase.input,  # type: ignore[arg-type]
                    expected_output=testcase.output,  # type: ignore[arg-type]
                    time_limit=int(problem.time_limit),  # type: ignore[arg-type]
                    memory_limit=int(problem.memory_limit),  # type: ignore[arg-type]
                )

                # Check if output matches (for AC status)
                if result.get("status") == "ac":
                    actual_output = (result.get("output") or "").strip()
                    expected_output = (testcase.output or "").strip()  # type: ignore[arg-type]
                    if not _outputs_match(actual_output, expected_output):
                        result["status"] = "wa"

                # Store testcase result
                testcase_result = TestCaseResult(
                    id=uuid.uuid4(),
                    submission_id=submission_id,
                    testcase_id=testcase.id,
                    status=SubmissionResult(result.get("status", "wa")),
                    input=testcase.input if not testcase.is_hidden else None,  # type: ignore[arg-type]
                    expected_output=testcase.output if not testcase.is_hidden else None,  # type: ignore[arg-type]
                    actual_output=result.get("output") if not testcase.is_hidden else None,
                    execute_time=result.get("execute_time"),
                    memory_used=result.get("memory_used"),
                    is_hidden=testcase.is_hidden,
                )
                db.add(testcase_result)
                results.append(result)

                total_execute_time += result.get("execute_time", 0)
                max_memory_used = max(max_memory_used, result.get("memory_used", 0))

                if result.get("status") == "ac":
                    total_score += testcase.score  # type: ignore[assignment]

                try:
                    from backend.services.queue_service import queue_service

                    queue_service.publish_status(
                        submission_id,
                        "progress",
                        {
                            "status": "judging",
                            "current_testcase": i + 1,
                            "total_testcases": len(testcases),
                            "progress": int(((i + 1) / len(testcases)) * 100),
                            "last_status": result.get("status"),
                        },
                    )
                except Exception:
                    pass

                # Stop on first failure if not hidden
                if result.get("status") != "ac" and not testcase.is_hidden:
                    break

            db.commit()

            # Determine final result
            final_result = SubmissionResult.AC
            first_error_message = None
            for r in results:
                status = r.get("status")
                if status == "ce":
                    final_result = SubmissionResult.CE
                    first_error_message = r.get("error_message")
                    break
                elif status == "re":
                    final_result = SubmissionResult.RE
                    first_error_message = r.get("error_message")
                    break
                elif status == "tle":
                    final_result = SubmissionResult.TLE
                    first_error_message = r.get("error_message")
                    break
                elif status == "mle":
                    final_result = SubmissionResult.MLE
                    first_error_message = r.get("error_message")
                    break
                elif status == "se":
                    final_result = SubmissionResult.SE
                    first_error_message = r.get("error_message")
                    break
                elif status != "ac":
                    final_result = SubmissionResult.WA

            return {
                "result": final_result,
                "error_message": first_error_message,
                "execute_time": total_execute_time,
                "memory_used": max_memory_used,
                "score": total_score,
            }

        except Exception as e:
            logger.error(f"Error executing judge task: {e}")
            return {
                "result": SubmissionResult.SE,
                "error_message": str(e),
                "execute_time": 0,
                "memory_used": 0,
                "score": 0,
            }

    def _execute_testcase(
        self,
        code: str,
        language: str,
        input_data: str,
        expected_output: str,
        time_limit: int,
        memory_limit: int,
    ) -> dict[str, Any]:
        """Execute a single testcase using the sandbox executor."""
        return self.executor.execute(
            code=code,
            language=language,
            input_data=input_data,
            time_limit=time_limit,
            memory_limit=memory_limit,
        )


def _outputs_match(actual_output: str, expected_output: str) -> bool:
    if actual_output == expected_output:
        return True
    try:
        return json.loads(actual_output) == json.loads(expected_output)
    except json.JSONDecodeError:
        return False
