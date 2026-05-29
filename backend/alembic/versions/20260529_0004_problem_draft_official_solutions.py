"""Store multi-language problem draft solutions.

Revision ID: 20260529_0004
Revises: 20260529_0003
Create Date: 2026-05-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0004"
down_revision: str | None = "20260529_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "problem_drafts",
        sa.Column("official_solutions_json", sa.Text(), nullable=False, server_default="[]"),
    )
    op.alter_column("problem_drafts", "official_solutions_json", server_default=None)


def downgrade() -> None:
    op.drop_column("problem_drafts", "official_solutions_json")
