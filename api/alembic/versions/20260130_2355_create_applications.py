"""create applications table

Revision ID: 20260130_2355
Revises: 20260128_2300
Create Date: 2026-01-30 23:55:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260130_2355"
down_revision = "20260128_2300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("applications"):
        return

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM customer_profiles
                    GROUP BY customer_id
                    HAVING COUNT(*) > 1
                ) THEN
                    RAISE EXCEPTION 'Duplicate customer_id values found in customer_profiles; cannot add FK.';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'customer_profiles_customer_id_key'
                ) THEN
                    ALTER TABLE customer_profiles
                    ADD CONSTRAINT customer_profiles_customer_id_key UNIQUE (customer_id);
                END IF;
            END $$;
            """
        )

    op.create_table(
        "applications",
        sa.Column("application_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.String(length=5), nullable=False),
        sa.Column("requested_loan_amount", sa.Float(), nullable=False),
        sa.Column("requested_tenure_amount", sa.Integer(), nullable=False),
        sa.Column("issue_status", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customer_profiles.customer_id"]),
    )
    op.create_index(
        "applications_customer_id_idx", "applications", ["customer_id"]
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO customer_profiles "
            "(id, customer_name, bank_account_number, customer_id, stage) "
            "SELECT :id, :name, :bank, :customer_id, :stage "
            "WHERE NOT EXISTS "
            "(SELECT 1 FROM customer_profiles WHERE customer_id = :customer_id)"
        ),
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Test Customer",
            "bank": "TEST-ACC-0001",
            "customer_id": "CUST1",
            "stage": "LEAD",
        },
    )
    connection.execute(
        sa.text(
            "INSERT INTO applications "
            "(application_id, customer_id, requested_loan_amount, requested_tenure_amount, issue_status) "
            "SELECT :app_id, :customer_id, :loan, :tenure, :issue "
            "WHERE NOT EXISTS "
            "(SELECT 1 FROM applications WHERE application_id = :app_id)"
        ),
        {
            "app_id": "CUST1-APP-001",
            "customer_id": "CUST1",
            "loan": 250000.0,
            "tenure": 24,
            "issue": None,
        },
    )


def downgrade() -> None:
    op.drop_index("applications_customer_id_idx", table_name="applications")
    op.drop_table("applications")
