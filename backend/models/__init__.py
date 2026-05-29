import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    JUDGING = "judging"
    FINISHED = "finished"


class SubmissionResult(str, enum.Enum):
    AC = "ac"
    WA = "wa"
    TLE = "tle"
    MLE = "mle"
    CE = "ce"
    RE = "re"
    SE = "se"


class Language(str, enum.Enum):
    PYTHON = "python"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GOLANG = "golang"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    locale = Column(String(10), nullable=False, default="zh")
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submissions = relationship("Submission", back_populates="user")


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (
        Index('idx_problems_created_at', 'created_at'),
        Index('idx_problems_difficulty', 'difficulty'),
        Index('idx_problems_slug', 'slug'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    difficulty = Column(SQLEnum(Difficulty), nullable=False, index=True)  # type: ignore[var-annotated]
    time_limit = Column(Integer, default=1000)
    memory_limit = Column(Integer, default=256)
    total_submissions = Column(Integer, default=0)
    accepted_submissions = Column(Integer, default=0)
    tags = Column(ARRAY(String(50)), default=list)  # type: ignore[var-annotated]
    hint = Column(Text, nullable=True)
    mode = Column(String(20), nullable=False, default="acm")
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    function_signature = Column(String(500), nullable=True)
    source = Column(String(200), nullable=True)
    is_public = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    testcases = relationship("TestCase", back_populates="problem")
    submissions = relationship("Submission", back_populates="problem")
    solutions = relationship("Solution", back_populates="problem")


class TestCase(Base):
    __tablename__ = "testcases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False, index=True)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False)
    is_sample = Column(Boolean, default=False)
    score = Column(Integer, default=10)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    problem = relationship("Problem", back_populates="testcases")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index('idx_submissions_user_problem', 'user_id', 'problem_id'),
        Index('idx_submissions_created_at', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False, index=True)
    code = Column(Text, nullable=False)
    language = Column(String(20), nullable=False)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)  # type: ignore[var-annotated]
    result = Column(SQLEnum(SubmissionResult), nullable=True)  # type: ignore[var-annotated]
    error_message = Column(Text, nullable=True)
    execute_time = Column(Integer, nullable=True)
    memory_used = Column(Integer, nullable=True)
    score = Column(Integer, default=0)
    ip_address = Column(String(45), nullable=True)
    judge_version = Column(String(20), default="v1")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    testcase_results = relationship("TestCaseResult", back_populates="submission")


class TestCaseResult(Base):
    __tablename__ = "testcase_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False, index=True)
    testcase_id = Column(UUID(as_uuid=True), ForeignKey("testcases.id"), nullable=True)
    status = Column(SQLEnum(SubmissionResult), nullable=False)  # type: ignore[var-annotated]
    input = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    actual_output = Column(Text, nullable=True)
    execute_time = Column(Integer, nullable=True)
    memory_used = Column(Integer, nullable=True)
    is_hidden = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    submission = relationship("Submission", back_populates="testcase_results")


class Solution(Base):
    __tablename__ = "solutions"
    __table_args__ = (
        Index('idx_solutions_problem_language', 'problem_id', 'language', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False, index=True)
    language = Column(String(20), nullable=False)
    code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    time_complexity = Column(String(50), nullable=True)
    space_complexity = Column(String(50), nullable=True)
    is_official = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    problem = relationship("Problem", back_populates="solutions")


class ProblemDraft(Base):
    __tablename__ = "problem_drafts"
    __table_args__ = (
        Index("idx_problem_drafts_created_at", "created_at"),
        Index("idx_problem_drafts_status", "status"),
        Index("idx_problem_drafts_slug", "slug"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)
    tags = Column(Text, nullable=False, default="[]")
    mode = Column(String(20), nullable=False)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    function_signature = Column(String(500), nullable=True)
    time_limit = Column(Integer, default=1000)
    memory_limit = Column(Integer, default=256)
    hint = Column(Text, nullable=True)
    official_solution_language = Column(String(20), nullable=False)
    official_solution_code = Column(Text, nullable=False)
    official_solution_explanation = Column(Text, nullable=False)
    official_solutions_json = Column(Text, nullable=False, default="[]")
    target_languages_json = Column(Text, nullable=False, default="[]")
    time_complexity = Column(String(50), nullable=True)
    space_complexity = Column(String(50), nullable=True)
    testcases_json = Column(Text, nullable=False, default="[]")
    validation_report_json = Column(Text, nullable=False, default="{}")
    status = Column(String(30), nullable=False, default="draft")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    approved_problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("AgentRun", back_populates="draft")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("idx_agent_runs_created_at", "created_at"),
        Index("idx_agent_runs_type_status", "run_type", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="running")
    input_json = Column(Text, nullable=False, default="{}")
    output_json = Column(Text, nullable=False, default="{}")
    error_message = Column(Text, nullable=True)
    model_profile = Column(String(30), nullable=False, default="default")
    locale = Column(String(10), nullable=False, default="en")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("problem_drafts.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    draft = relationship("ProblemDraft", back_populates="runs")
    steps = relationship("AgentStep", back_populates="run", order_by="AgentStep.step_index")


class AgentStep(Base):
    __tablename__ = "agent_steps"
    __table_args__ = (
        Index("idx_agent_steps_run_index", "run_id", "step_index"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    step_type = Column(String(30), nullable=False)
    tool_name = Column(String(100), nullable=True)
    input_json = Column(Text, nullable=False, default="{}")
    output_json = Column(Text, nullable=False, default="{}")
    status = Column(String(30), nullable=False, default="running")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("AgentRun", back_populates="steps")
