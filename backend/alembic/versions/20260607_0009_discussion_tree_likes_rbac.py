"""Add discussion trees, likes, and content admin permissions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260607_0009"
down_revision = "20260606_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "content_admin_permissions",
            postgresql.ARRAY(sa.String(length=80)),
            nullable=False,
            server_default=sa.text("'{}'::character varying[]"),
        ),
    )
    op.alter_column("users", "content_admin_permissions", server_default=None)

    op.add_column("problem_discussions", sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("problem_discussions", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("problem_discussions", sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_problem_discussions_parent_id",
        "problem_discussions",
        "problem_discussions",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_problem_discussions_deleted_by_users",
        "problem_discussions",
        "users",
        ["deleted_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_problem_discussions_parent_id", "problem_discussions", ["parent_id"])
    op.create_index("ix_problem_discussions_deleted_by", "problem_discussions", ["deleted_by"])

    op.create_table(
        "problem_discussion_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("discussion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["discussion_id"], ["problem_discussions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "discussion_id", name="uq_problem_discussion_likes_user_discussion"),
    )
    op.create_index(
        "idx_problem_discussion_likes_discussion",
        "problem_discussion_likes",
        ["discussion_id"],
    )
    op.create_index("idx_problem_discussion_likes_user", "problem_discussion_likes", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_problem_discussion_likes_user", table_name="problem_discussion_likes")
    op.drop_index("idx_problem_discussion_likes_discussion", table_name="problem_discussion_likes")
    op.drop_table("problem_discussion_likes")

    op.drop_index("ix_problem_discussions_deleted_by", table_name="problem_discussions")
    op.drop_index("ix_problem_discussions_parent_id", table_name="problem_discussions")
    op.drop_constraint("fk_problem_discussions_deleted_by_users", "problem_discussions", type_="foreignkey")
    op.drop_constraint("fk_problem_discussions_parent_id", "problem_discussions", type_="foreignkey")
    op.drop_column("problem_discussions", "deleted_by")
    op.drop_column("problem_discussions", "deleted_at")
    op.drop_column("problem_discussions", "parent_id")

    op.drop_column("users", "content_admin_permissions")
