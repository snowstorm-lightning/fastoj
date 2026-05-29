"""add user locale preference

Revision ID: 20260529_0005
Revises: 20260529_0004
Create Date: 2026-05-29
"""

import sqlalchemy as sa
from alembic import op

revision = "20260529_0005"
down_revision = "20260529_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="zh"),
    )
    op.alter_column("users", "locale", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "locale")
