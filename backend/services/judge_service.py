import logging
from typing import Any

from backend.models import SubmissionResult, TestCase
from backend.sandbox.executor import SandboxExecutor

logger = logging.getLogger(__name__)


class JudgeService:
    """Service that orchestrates the judging process."""

    def __init__(self):
        self.executor = SandboxExecutor()

    def judge(
        self,
        code: str,
        language: str,
        testcases: list[TestCase],
        time_limit: int = 1000,
        memory_limit: int = 256,
    ) -> dict[str, Any]:
        """
        Judge code against testcases.

        Args:
            code: Source code
            language: Programming language
            testcases: List of testcases to run
            time_limit: Time limit per testcase (ms)
            memory_limit: Memory limit (MB)

        Returns:
            Dict with result, execute_time, memory_used, score
        """
        total_score = 0
        total_execute_time = 0
        max_memory_used = 0
        final_result = SubmissionResult.AC
        error_message = None

        for testcase in testcases:
            try:
                result = self.executor.execute(
                    code=code,
                    language=language,
                    input_data=testcase.input,
                    time_limit=time_limit,
                    memory_limit=memory_limit,
                )

                status = result.get("status")

                # Check for compilation errors
                if status == "ce":
                    final_result = SubmissionResult.CE
                    error_message = result.get("error_message")
                    break

                # Check for runtime errors
                if status == "re":
                    final_result = SubmissionResult.RE
                    error_message = result.get("error_message")

                # Check for time limit exceeded
                if status == "tle":
                    final_result = SubmissionResult.TLE
                    break

                # Check for memory limit exceeded
                if status == "mle":
                    final_result = SubmissionResult.MLE
                    break

                # Check output
                if status == "ac":
                    expected = testcase.output.strip()  # type: ignore[arg-type]
                    actual = result.get("output", "").strip()

                    if expected == actual:
                        total_score += testcase.score  # type: ignore[assignment]
                    else:
                        final_result = SubmissionResult.WA
                        # Don't break - continue to show which testcase failed
                else:
                    final_result = SubmissionResult.WA

                total_execute_time += result.get("execute_time", 0)
                max_memory_used = max(max_memory_used, result.get("memory_used", 0))

            except Exception as e:
                logger.error(f"Error executing testcase: {e}")
                final_result = SubmissionResult.SE
                error_message = str(e)
                break

        return {
            "result": final_result,
            "execute_time": total_execute_time,
            "memory_used": max_memory_used,
            "score": total_score,
            "error_message": error_message,
        }
