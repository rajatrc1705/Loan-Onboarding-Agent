"""add voice agent review data

Revision ID: 20260201_0100
Revises: 20260131_0115
Create Date: 2026-02-01 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20260201_0100"
down_revision = "20260131_0115"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _uuid_column(name: str, *, primary_key: bool = False, nullable: bool = False):
    return sa.Column(
        name,
        postgresql.UUID(as_uuid=True),
        primary_key=primary_key,
        nullable=nullable,
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rfistatus') THEN
                    ALTER TYPE rfistatus ADD VALUE IF NOT EXISTS 'NEEDS_REVIEW';
                END IF;
            END $$;
            """
        )

    if inspector.has_table("rfi_cases"):
        with op.batch_alter_table("rfi_cases") as batch_op:
            if not _has_column(inspector, "rfi_cases", "needs_review"):
                batch_op.add_column(
                    sa.Column(
                        "needs_review",
                        sa.Boolean(),
                        nullable=False,
                        server_default=sa.false(),
                    )
                )
            if not _has_column(inspector, "rfi_cases", "review_reason"):
                batch_op.add_column(sa.Column("review_reason", sa.Text(), nullable=True))

    if inspector.has_table("rfi_answers"):
        with op.batch_alter_table("rfi_answers") as batch_op:
            if not _has_column(inspector, "rfi_answers", "answer_status"):
                batch_op.add_column(
                    sa.Column(
                        "answer_status",
                        sa.String(length=32),
                        nullable=False,
                        server_default="answered",
                    )
                )
            if not _has_column(inspector, "rfi_answers", "evidence_quote"):
                batch_op.add_column(sa.Column("evidence_quote", sa.Text(), nullable=True))
            if not _has_column(inspector, "rfi_answers", "follow_up_asked"):
                batch_op.add_column(
                    sa.Column(
                        "follow_up_asked",
                        sa.Boolean(),
                        nullable=False,
                        server_default=sa.false(),
                    )
                )
            if not _has_column(inspector, "rfi_answers", "evaluator_notes"):
                batch_op.add_column(sa.Column("evaluator_notes", sa.Text(), nullable=True))

    if inspector.has_table("rfi_cases") and not inspector.has_table("rfi_customer_questions"):
        op.create_table(
            "rfi_customer_questions",
            _uuid_column("id", primary_key=True),
            _uuid_column("rfi_id"),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("agent_response", sa.Text(), nullable=True),
            sa.Column(
                "needs_human_followup",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["rfi_id"], ["rfi_cases.id"]),
        )

    if inspector.has_table("rfi_cases") and not inspector.has_table("rfi_transcript_turns"):
        op.create_table(
            "rfi_transcript_turns",
            _uuid_column("id", primary_key=True),
            _uuid_column("rfi_id"),
            sa.Column("speaker", sa.String(length=32), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["rfi_id"], ["rfi_cases.id"]),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("rfi_transcript_turns"):
        op.drop_table("rfi_transcript_turns")
    if inspector.has_table("rfi_customer_questions"):
        op.drop_table("rfi_customer_questions")
    if inspector.has_table("rfi_answers"):
        with op.batch_alter_table("rfi_answers") as batch_op:
            for column_name in (
                "evaluator_notes",
                "follow_up_asked",
                "evidence_quote",
                "answer_status",
            ):
                if _has_column(inspector, "rfi_answers", column_name):
                    batch_op.drop_column(column_name)
    if inspector.has_table("rfi_cases"):
        with op.batch_alter_table("rfi_cases") as batch_op:
            for column_name in ("review_reason", "needs_review"):
                if _has_column(inspector, "rfi_cases", column_name):
                    batch_op.drop_column(column_name)
