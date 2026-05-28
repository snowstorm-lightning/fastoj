"""Allow custom run results without persisted testcases.

Revision ID: 20260529_0003
Revises: 20260515_0002
Create Date: 2026-05-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260529_0003"
down_revision: str | None = "20260515_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("testcase_results", "testcase_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.alter_column("testcase_results", "testcase_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
