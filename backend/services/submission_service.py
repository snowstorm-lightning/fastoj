import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.languages import Language
from backend.models import Problem, Submission, SubmissionStatus
from backend.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionListItem,
    TestCaseResultResponse,
)
from backend.services.function_mode import wrap_function_submission
from backend.services.queue_service import queue_service

logger = logging.getLogger(__name__)


class SubmissionService:
    def __init__(self, db: Session):
        self.db = db

    def create_submission(
        self, submission_data: SubmissionCreate, user_id: str, ip_address: str | None = None
    ) -> Submission:
        """Create a new submission and queue it for judging."""
        if submission_data.run_testcases:
            raise ValueError("Custom run testcases are only supported for public runs")
        # Verify problem exists
        if not Language.is_supported(submission_data.language):
            raise ValueError(f"Unsupported language: {submission_data.language}")
        problem = self.db.query(Problem).filter(Problem.id == submission_data.problem_id).first()
        if not problem:
            raise ValueError("Problem not found")
        judge_code = self._prepare_judge_code(submission_data, problem)

        # Create submission
        submission = Submission(
            id=uuid.uuid4(),
            user_id=user_id,
            problem_id=submission_data.problem_id,
            code=submission_data.code,
            language=submission_data.language,
            status=SubmissionStatus.PENDING,
            ip_address=ip_address,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)

        # Update problem total submissions
        problem.total_submissions = problem.total_submissions + 1  # type: ignore[assignment]
        self.db.commit()

        self._queue_or_judge_now(submission, use_hidden=True, judge_code=judge_code)

        return submission

    def create_run(
        self, submission_data: SubmissionCreate, user_id: str, ip_address: str | None = None
    ) -> Submission:
        """Create a run (test with public testcases only)."""
        # Verify problem exists
        if not Language.is_supported(submission_data.language):
            raise ValueError(f"Unsupported language: {submission_data.language}")
        problem = self.db.query(Problem).filter(Problem.id == submission_data.problem_id).first()
        if not problem:
            raise ValueError("Problem not found")
        judge_code = self._prepare_judge_code(submission_data, problem)

        # Create submission
        submission = Submission(
            id=uuid.uuid4(),
            user_id=user_id,
            problem_id=submission_data.problem_id,
            code=submission_data.code,
            language=submission_data.language,
            status=SubmissionStatus.PENDING,
            ip_address=ip_address,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)

        self._queue_or_judge_now(
            submission,
            use_hidden=False,
            judge_code=judge_code,
            run_testcases=[{"input": item.input} for item in (submission_data.run_testcases or [])] or None,
        )

        return submission

    def _prepare_judge_code(self, submission_data: SubmissionCreate, problem: Problem) -> str:
        if submission_data.judge_mode == "function":
            return wrap_function_submission(
                submission_data.code,
                submission_data.language,
                problem.slug,  # type: ignore[arg-type]
                problem.function_signature,  # type: ignore[arg-type]
            )
        return submission_data.code

    def _queue_or_judge_now(
        self,
        submission: Submission,
        use_hidden: bool,
        judge_code: str | None = None,
        run_testcases: list[dict[str, str]] | None = None,
    ) -> None:
        """Queue a judge task, or execute it inline when Redis/worker is unavailable."""
        task = {
            "submission_id": str(submission.id),
            "problem_id": str(submission.problem_id),
            "code": judge_code or submission.code,
            "language": submission.language,
            "use_hidden": use_hidden,
        }
        if run_testcases and not use_hidden:
            task["run_testcases"] = run_testcases

        if settings.JUDGE_ASYNC:
            try:
                queue_service.push_task(task)
                queue_service.publish_status(
                    str(submission.id),
                    "pending",
                    {"status": "pending", "progress": 0},
                )
                return
            except Exception as exc:
                logger.warning("Judge queue unavailable; running submission inline: %s", exc)

        from backend.worker.tasks.judge_task import JudgeTask

        self.update_submission_status(str(submission.id), SubmissionStatus.JUDGING)
        result = JudgeTask().execute(
            submission_id=str(submission.id),
            problem_id=str(submission.problem_id),
            code=judge_code or submission.code,
            language=submission.language,
            use_hidden=use_hidden,
            db=self.db,
            run_testcases=run_testcases,
        )
        self.update_submission_status(
            str(submission.id),
            SubmissionStatus.FINISHED,
            result=result.get("result"),
            error_message=result.get("error_message"),
            execute_time=result.get("execute_time"),
            memory_used=result.get("memory_used"),
            score=result.get("score", 0),
        )

    def get_submission(
        self,
        submission_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> SubmissionDetail | None:
        """Get submission by ID."""
        query = self.db.query(Submission).filter(Submission.id == submission_id)
        if not is_admin:
            query = query.filter(Submission.user_id == user_id)
        submission = query.first()
        if not submission:
            return None

        return self._to_detail(submission)

    def get_submission_for_judge(self, submission_id: str) -> Submission | None:
        """Get submission for judge worker (without user check)."""
        return (
            self.db.query(Submission)
            .filter(Submission.id == submission_id)
            .first()
        )

    def get_user_submissions(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        problem_id: str | None = None,
        language: str | None = None,
        result: str | None = None,
        status: str | None = None,
    ) -> tuple[list[SubmissionListItem], int]:
        """Get user's submissions with filters."""
        query = self.db.query(Submission).filter(Submission.user_id == user_id)

        if problem_id:
            query = query.filter(Submission.problem_id == problem_id)
        if language:
            query = query.filter(Submission.language == language)
        if result:
            query = query.filter(Submission.result == result)  # type: ignore[arg-type]
        if status:
            query = query.filter(Submission.status == status)  # type: ignore[arg-type]

        total = query.count()

        offset = (page - 1) * page_size
        query = query.order_by(Submission.created_at.desc()).offset(offset).limit(page_size)

        submissions = query.all()

        result_list = []
        for s in submissions:
            result_list.append(
                SubmissionListItem(
                    id=str(s.id),
                    problem={
                        "id": str(s.problem.id),
                        "title": s.problem.title,  # type: ignore[arg-type]
                        "slug": s.problem.slug,  # type: ignore[arg-type]
                    },
                    language=s.language,  # type: ignore[arg-type]
                    status=s.status.value,
                    result=s.result.value if s.result else None,
                    error_message=s.error_message,  # type: ignore[arg-type]
                    score=s.score,  # type: ignore[arg-type]
                    execute_time=s.execute_time,  # type: ignore[arg-type]
                    created_at=s.created_at.isoformat(),
                )
            )

        return result_list, total

    def update_submission_status(
        self,
        submission_id: str,
        status: SubmissionStatus,
        result=None,
        error_message: str | None = None,
        execute_time: int | None = None,
        memory_used: int | None = None,
        score: int = 0,
    ) -> Submission:
        """Update submission status and result."""
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise ValueError("Submission not found")

        submission.status = status  # type: ignore[assignment]
        if result:
            submission.result = result  # type: ignore[assignment]
        if error_message:
            submission.error_message = error_message  # type: ignore[assignment]
        if execute_time:
            submission.execute_time = execute_time  # type: ignore[assignment]
        if memory_used:
            submission.memory_used = memory_used  # type: ignore[assignment]
        submission.score = score  # type: ignore[assignment]

        if status == SubmissionStatus.FINISHED:
            submission.finished_at = datetime.utcnow()  # type: ignore[assignment]

            # Update problem accepted count if AC
            if result and result.value == "ac":
                problem = self.db.query(Problem).filter(Problem.id == submission.problem_id).first()
                if problem:
                    problem.accepted_submissions = problem.accepted_submissions + 1  # type: ignore[assignment]
                    self.db.commit()

        self.db.commit()
        self.db.refresh(submission)

        return submission

    def _to_detail(self, submission: Submission) -> SubmissionDetail:
        """Convert submission to detail response."""
        return SubmissionDetail(
            id=str(submission.id),
            problem_id=str(submission.problem_id),
            user_id=str(submission.user_id),
            code=submission.code,  # type: ignore[arg-type]
            language=submission.language,  # type: ignore[arg-type]
            status=submission.status.value,
            result=submission.result.value if submission.result else None,
            error_message=submission.error_message,  # type: ignore[arg-type]
            execute_time=submission.execute_time,  # type: ignore[arg-type]
            memory_used=submission.memory_used,  # type: ignore[arg-type]
            score=submission.score,  # type: ignore[arg-type]
            created_at=submission.created_at.isoformat(),
            finished_at=submission.finished_at.isoformat() if submission.finished_at else None,
            testcase_results=[
                TestCaseResultResponse(
                    id=str(r.id),
                    testcase_id=str(r.testcase_id) if r.testcase_id else None,
                    status=r.status.value,
                    input=r.input,  # type: ignore[arg-type]
                    expected_output=r.expected_output,  # type: ignore[arg-type]
                    actual_output=r.actual_output,  # type: ignore[arg-type]
                    execute_time=r.execute_time,  # type: ignore[arg-type]
                    memory_used=r.memory_used,  # type: ignore[arg-type]
                    is_hidden=r.is_hidden,  # type: ignore[arg-type]
                )
                for r in sorted(submission.testcase_results, key=lambda item: item.created_at or datetime.min)
            ],
        )
