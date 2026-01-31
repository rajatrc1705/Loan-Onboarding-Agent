"""make customer_id primary key

Revision ID: 20260131_0115
Revises: 20260131_0100
Create Date: 2026-01-31 01:15:00.000000
"""
from alembic import op

revision = "20260131_0115"
down_revision = "20260131_0100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "customer_profiles_customer_id_key",
        "customer_profiles",
        type_="unique",
    )
    op.drop_constraint("customer_profiles_pkey", "customer_profiles", type_="primary")
    op.create_primary_key("customer_profiles_pkey", "customer_profiles", ["customer_id"])


def downgrade() -> None:
    op.drop_constraint("customer_profiles_pkey", "customer_profiles", type_="primary")
    op.create_primary_key("customer_profiles_pkey", "customer_profiles", ["id"])
    op.create_unique_constraint(
        "customer_profiles_customer_id_key", "customer_profiles", ["customer_id"]
    )
