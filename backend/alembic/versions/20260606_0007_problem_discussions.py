"""Add persisted problem discussions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260606_0007"
down_revision = "20260529_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "problem_discussions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_problem_discussions_problem_id", "problem_discussions", ["problem_id"])
    op.create_index("ix_problem_discussions_user_id", "problem_discussions", ["user_id"])
    op.create_index(
        "idx_problem_discussions_problem_created",
        "problem_discussions",
        ["problem_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_problem_discussions_problem_created", table_name="problem_discussions")
    op.drop_index("ix_problem_discussions_user_id", table_name="problem_discussions")
    op.drop_index("ix_problem_discussions_problem_id", table_name="problem_discussions")
    op.drop_table("problem_discussions")
