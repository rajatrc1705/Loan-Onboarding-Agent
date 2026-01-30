"""create customer_profiles table

Revision ID: 20260128_2300
Revises: 
Create Date: 2026-01-28 23:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260128_2300"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("bank_account_number", sa.Text(), nullable=False),
        sa.Column("customer_id", sa.String(length=5), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "EXISTING_CUSTOMER",
                "LEAD",
                "APPLICATION_PENDING",
                name="customerstage",
            ),
            nullable=False,
        ),
        sa.Column("business_type", sa.Text(), nullable=True),
        sa.Column("company_type", sa.Text(), nullable=True),
        sa.Column("company_url", sa.Text(), nullable=True),
        sa.Column("google_drive_link", sa.Text(), nullable=True),
    )
    op.create_index(
        "customer_profiles_customer_id_idx",
        "customer_profiles",
        ["customer_id"],
    )


def downgrade() -> None:
    op.drop_index("customer_profiles_customer_id_idx", table_name="customer_profiles")
    op.drop_table("customer_profiles")
    op.execute("DROP TYPE IF EXISTS customerstage")
