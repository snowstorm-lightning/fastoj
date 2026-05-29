"""Add target languages to problem drafts."""

import sqlalchemy as sa
from alembic import op

revision = "20260529_0006"
down_revision = "20260529_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "problem_drafts",
        sa.Column("target_languages_json", sa.Text(), nullable=False, server_default="[]"),
    )
    op.alter_column("problem_drafts", "target_languages_json", server_default=None)


def downgrade() -> None:
    op.drop_column("problem_drafts", "target_languages_json")
