"""Add source metadata to problem drafts."""

import sqlalchemy as sa
from alembic import op

revision = "20260606_0008"
down_revision = "20260606_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "problem_drafts",
        sa.Column("source_metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.alter_column("problem_drafts", "source_metadata_json", server_default=None)


def downgrade() -> None:
    op.drop_column("problem_drafts", "source_metadata_json")
