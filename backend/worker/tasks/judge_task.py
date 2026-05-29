import json
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.core.languages import Language
from backend.models import Problem, Solution, SubmissionResult, TestCase, TestCaseResult
from backend.sandbox.executor import SandboxExecutor
from backend.services.function_mode import wrap_function_submission
from backend.services.problem_modes import FUNCTION_SIGNATURES
from backend.services.problem_service import ProblemService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeTestCase:
    input: str
    output: str
    is_hidden: bool = False
    score: int = 0
    id: uuid.UUID | None = None


REFERENCE_ACM_SOLUTIONS: dict[str, str] = {
    "next-permutation": """
import json
import sys

nums = json.loads(sys.stdin.read())
i = len(nums) - 2
while i >= 0 and nums[i] >= nums[i + 1]:
    i -= 1
if i >= 0:
    j = len(nums) - 1
    while nums[j] <= nums[i]:
        j -= 1
    nums[i], nums[j] = nums[j], nums[i]
nums[i + 1 :] = reversed(nums[i + 1 :])
print(json.dumps(nums, separators=(",", ":")))
""".strip(),
    "diameter-of-binary-tree": """
import json
import sys

values = json.loads(sys.stdin.read())
if not values:
    print(0)
    raise SystemExit
nodes = [None if value is None else [None, None] for value in values]
children = nodes[::-1]
root = children.pop()
for node in nodes:
    if node is None:
        continue
    if children:
        node[0] = children.pop()
    if children:
        node[1] = children.pop()
best = 0

def depth(node):
    global best
    if node is None:
        return 0
    left = depth(node[0])
    right = depth(node[1])
    best = max(best, left + right)
    return max(left, right) + 1

depth(root)
print(best)
""".strip(),
    "maximum-depth-of-binary-tree": """
import json
import sys

values = json.loads(sys.stdin.read())
if not values:
    print(0)
    raise SystemExit
nodes = [None if value is None else [None, None] for value in values]
children = nodes[::-1]
root = children.pop()
for node in nodes:
    if node is None:
        continue
    if children:
        node[0] = children.pop()
    if children:
        node[1] = children.pop()

def depth(node):
    if node is None:
        return 0
    return max(depth(node[0]), depth(node[1])) + 1

print(depth(root))
""".strip(),
    "majority-element": """
import json
import sys

nums = json.loads(sys.stdin.read())
candidate = None
count = 0
for value in nums:
    if count == 0:
        candidate = value
    count += 1 if value == candidate else -1
print(candidate)
""".strip(),
}


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
        run_testcases: list[dict[str, Any]] | None = None,
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

            # Get testcases based on use_hidden flag. Custom run cases are user
            # supplied and never participate in full hidden judging.
            if run_testcases and not use_hidden:
                public_testcases = problem_service.get_public_testcases(problem_id)
                testcases = self._custom_run_testcases(problem, db, run_testcases, public_testcases)
            elif use_hidden:
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

                    progress_payload = {
                        "status": "judging",
                        "progress": 90 if use_hidden and testcase.is_hidden else int(((i + 1) / len(testcases)) * 100),
                    }
                    if not use_hidden:
                        progress_payload.update(
                            {
                                "current_testcase": i + 1,
                                "total_testcases": len(testcases),
                                "last_status": result.get("status"),
                            }
                        )
                    queue_service.publish_status(submission_id, "progress", progress_payload)
                except Exception:
                    pass

                # Full submissions stop before hidden judging when a public case
                # fails. Public-only runs keep going so users can compare every
                # visible case in the result panel.
                if use_hidden and result.get("status") != "ac" and not testcase.is_hidden:
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

    def _custom_run_testcases(
        self,
        problem: Problem,
        db: Session,
        run_testcases: list[dict[str, Any]],
        public_testcases: list[TestCase],
    ) -> list[RuntimeTestCase]:
        public_outputs = {str(testcase.input): str(testcase.output) for testcase in public_testcases}
        return [
            RuntimeTestCase(
                input=str(item.get("input") or ""),
                output=self._expected_output_for_input(problem, db, str(item.get("input") or ""), public_outputs),
            )
            for item in run_testcases[:8]
        ]

    def _expected_output_for_input(
        self,
        problem: Problem,
        db: Session,
        input_data: str,
        public_outputs: dict[str, str],
    ) -> str:
        official = self._official_solution(problem, db)
        if official:
            language, code = official
            execution = self.executor.execute(
                code=code,
                language=language,
                input_data=input_data,
                time_limit=int(problem.time_limit),  # type: ignore[arg-type]
                memory_limit=int(problem.memory_limit),  # type: ignore[arg-type]
            )
            if execution.get("status") == "ac":
                return str(execution.get("output") or "").strip()
            if input_data in public_outputs:
                return public_outputs[input_data].strip()
            raise ValueError("Official solution failed to generate expected output for this input.")

        if input_data in public_outputs:
            return public_outputs[input_data].strip()

        raise ValueError("No official solution is available to generate expected output for this input.")

    def _official_solution(self, problem: Problem, db: Session) -> tuple[str, str] | None:
        solutions = (
            db.query(Solution)
            .filter(Solution.problem_id == problem.id, Solution.is_official == True)
            .all()
        )
        supported = [solution for solution in solutions if Language.is_supported(str(solution.language))]
        supported.sort(key=lambda solution: 0 if solution.language == "python" else 1)
        for solution in supported:
            return str(solution.language), self._prepare_official_code(problem, solution)

        reference = REFERENCE_ACM_SOLUTIONS.get(str(getattr(problem, "slug", "")))
        if reference:
            return "python", reference
        return None

    def _prepare_official_code(self, problem: Problem, solution: Solution) -> str:
        code = str(solution.code or "")
        language = str(solution.language)
        signature = _problem_function_signature(problem)
        if signature and self._looks_like_function_solution(code, language, signature):
            return wrap_function_submission(code, language, str(getattr(problem, "slug", "")), signature)
        return code

    def _looks_like_function_solution(self, code: str, language: str, function_signature: str) -> bool:
        function_name = _function_name_from_signature(function_signature)
        if not function_name:
            return False
        if language == "python":
            return bool(re.search(rf"\bdef\s+{re.escape(function_name)}\s*\(", code)) or "class Solution" in code
        if language in {"javascript", "typescript"}:
            camel_name = _camel_case(function_name)
            return bool(re.search(rf"\bfunction\s+({re.escape(function_name)}|{re.escape(camel_name)})\s*\(", code))
        if language in {"cpp", "c", "golang"}:
            return function_name in code or _camel_case(function_name) in code
        if language == "java":
            return "class Solution" in code
        return False

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


def _function_name_from_signature(function_signature: str) -> str | None:
    match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", function_signature)
    return match.group(1) if match else None


def _problem_function_signature(problem: Problem) -> str | None:
    return getattr(problem, "function_signature", None) or FUNCTION_SIGNATURES.get(str(getattr(problem, "slug", "")))


def _camel_case(name: str) -> str:
    return re.sub(r"_([A-Za-z0-9])", lambda match: match.group(1).upper(), name)


def _outputs_match(actual_output: str, expected_output: str) -> bool:
    if actual_output == expected_output:
        return True
    actual_is_json, actual_json = _json_value(actual_output)
    expected_is_json, expected_json = _json_value(expected_output)
    if expected_is_json and isinstance(expected_json, str) and actual_output == expected_json:
        return True
    if actual_is_json and isinstance(actual_json, str) and expected_output == actual_json:
        return True
    if actual_is_json and expected_is_json:
        return actual_json == expected_json
    return False


def _json_value(value: str) -> tuple[bool, Any]:
    try:
        return True, json.loads(value)
    except json.JSONDecodeError:
        return False, None
