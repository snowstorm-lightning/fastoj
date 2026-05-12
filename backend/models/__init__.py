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
    testcase_id = Column(UUID(as_uuid=True), ForeignKey("testcases.id"), nullable=False)
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
