"""add unique constraint to customer_profiles.customer_id

Revision ID: 20260131_0100
Revises: 20260130_2355
Create Date: 2026-01-31 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260131_0100"
down_revision = "20260130_2355"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    if bind.dialect.name == "postgresql":
        exists = bind.execute(
            sa.text(
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'customer_profiles_customer_id_key'
                """
            )
        ).scalar()
        if exists:
            return
    with op.batch_alter_table("customer_profiles") as batch_op:
        batch_op.create_unique_constraint(
            "customer_profiles_customer_id_key", ["customer_id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    if bind.dialect.name == "postgresql":
        exists = bind.execute(
            sa.text(
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'customer_profiles_customer_id_key'
                """
            )
        ).scalar()
        if not exists:
            return
    with op.batch_alter_table("customer_profiles") as batch_op:
        batch_op.drop_constraint(
            "customer_profiles_customer_id_key", type_="unique"
        )
