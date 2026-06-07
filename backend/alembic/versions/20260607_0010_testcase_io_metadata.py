"""Add testcase mode-specific IO metadata."""

import sqlalchemy as sa
from alembic import op

revision = "20260607_0010"
down_revision = "20260607_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("testcases", sa.Column("io_metadata_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("testcases", "io_metadata_json")
