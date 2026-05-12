"""initial schema

Revision ID: 20260512_0001
Revises:
Create Date: 2026-05-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260512_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    difficulty = postgresql.ENUM("EASY", "MEDIUM", "HARD", name="difficulty", create_type=False)
    submissionstatus = postgresql.ENUM("PENDING", "JUDGING", "FINISHED", name="submissionstatus", create_type=False)
    submissionresult = postgresql.ENUM("AC", "WA", "TLE", "MLE", "CE", "RE", "SE", name="submissionresult", create_type=False)
    difficulty.create(op.get_bind(), checkfirst=True)
    submissionstatus.create(op.get_bind(), checkfirst=True)
    submissionresult.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500)),
        sa.Column("role", sa.String(length=20)),
        sa.Column("is_active", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "problems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", difficulty, nullable=False),
        sa.Column("time_limit", sa.Integer()),
        sa.Column("memory_limit", sa.Integer()),
        sa.Column("total_submissions", sa.Integer()),
        sa.Column("accepted_submissions", sa.Integer()),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=50))),
        sa.Column("hint", sa.Text()),
        sa.Column("source", sa.String(length=200)),
        sa.Column("is_public", sa.Boolean()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("idx_problems_created_at", "problems", ["created_at"])
    op.create_index("idx_problems_difficulty", "problems", ["difficulty"])
    op.create_index("idx_problems_slug", "problems", ["slug"])
    op.create_index("ix_problems_slug", "problems", ["slug"], unique=True)

    op.create_table(
        "testcases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean()),
        sa.Column("is_sample", sa.Boolean()),
        sa.Column("score", sa.Integer()),
        sa.Column("order", sa.Integer()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_testcases_problem_id", "testcases", ["problem_id"])

    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("status", submissionstatus),
        sa.Column("result", submissionresult),
        sa.Column("error_message", sa.Text()),
        sa.Column("execute_time", sa.Integer()),
        sa.Column("memory_used", sa.Integer()),
        sa.Column("score", sa.Integer()),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("judge_version", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
    )
    op.create_index("idx_submissions_user_problem", "submissions", ["user_id", "problem_id"])
    op.create_index("idx_submissions_created_at", "submissions", ["created_at"])
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
    op.create_index("ix_submissions_problem_id", "submissions", ["problem_id"])
    op.create_index("ix_submissions_status", "submissions", ["status"])

    op.create_table(
        "testcase_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("testcase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("testcases.id"), nullable=False),
        sa.Column("status", submissionresult, nullable=False),
        sa.Column("input", sa.Text()),
        sa.Column("expected_output", sa.Text()),
        sa.Column("actual_output", sa.Text()),
        sa.Column("execute_time", sa.Integer()),
        sa.Column("memory_used", sa.Integer()),
        sa.Column("is_hidden", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_testcase_results_submission_id", "testcase_results", ["submission_id"])

    op.create_table(
        "solutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("time_complexity", sa.String(length=50)),
        sa.Column("space_complexity", sa.String(length=50)),
        sa.Column("is_official", sa.Boolean()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("idx_solutions_problem_language", "solutions", ["problem_id", "language"], unique=True)


def downgrade() -> None:
    op.drop_table("solutions")
    op.drop_table("testcase_results")
    op.drop_table("submissions")
    op.drop_table("testcases")
    op.drop_table("problems")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS submissionresult")
    op.execute("DROP TYPE IF EXISTS submissionstatus")
    op.execute("DROP TYPE IF EXISTS difficulty")
