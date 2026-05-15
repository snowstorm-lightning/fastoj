"""problem authoring agent drafts

Revision ID: 20260515_0002
Revises: 20260512_0001
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260515_0002"
down_revision = "20260512_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("mode", sa.String(length=20), nullable=False, server_default="acm"))
    op.add_column("problems", sa.Column("input_format", sa.Text()))
    op.add_column("problems", sa.Column("output_format", sa.Text()))
    op.add_column("problems", sa.Column("function_signature", sa.String(length=500)))

    op.create_table(
        "problem_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("input_format", sa.Text()),
        sa.Column("output_format", sa.Text()),
        sa.Column("function_signature", sa.String(length=500)),
        sa.Column("time_limit", sa.Integer()),
        sa.Column("memory_limit", sa.Integer()),
        sa.Column("hint", sa.Text()),
        sa.Column("official_solution_language", sa.String(length=20), nullable=False),
        sa.Column("official_solution_code", sa.Text(), nullable=False),
        sa.Column("official_solution_explanation", sa.Text(), nullable=False),
        sa.Column("time_complexity", sa.String(length=50)),
        sa.Column("space_complexity", sa.String(length=50)),
        sa.Column("testcases_json", sa.Text(), nullable=False),
        sa.Column("validation_report_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id")),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("idx_problem_drafts_created_at", "problem_drafts", ["created_at"])
    op.create_index("idx_problem_drafts_status", "problem_drafts", ["status"])
    op.create_index("idx_problem_drafts_slug", "problem_drafts", ["slug"])
    op.create_index("ix_problem_drafts_slug", "problem_drafts", ["slug"])
    op.create_index("ix_problem_drafts_created_by", "problem_drafts", ["created_by"])

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("model_profile", sa.String(length=30), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("draft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_drafts.id")),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
    )
    op.create_index("idx_agent_runs_created_at", "agent_runs", ["created_at"])
    op.create_index("idx_agent_runs_type_status", "agent_runs", ["run_type", "status"])
    op.create_index("ix_agent_runs_created_by", "agent_runs", ["created_by"])
    op.create_index("ix_agent_runs_draft_id", "agent_runs", ["draft_id"])

    op.create_table(
        "agent_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=30), nullable=False),
        sa.Column("tool_name", sa.String(length=100)),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("idx_agent_steps_run_index", "agent_steps", ["run_id", "step_index"])
    op.create_index("ix_agent_steps_run_id", "agent_steps", ["run_id"])


def downgrade() -> None:
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")
    op.drop_table("problem_drafts")
    op.drop_column("problems", "function_signature")
    op.drop_column("problems", "output_format")
    op.drop_column("problems", "input_format")
    op.drop_column("problems", "mode")
