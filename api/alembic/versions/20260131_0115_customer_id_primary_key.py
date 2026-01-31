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
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            ALTER TABLE applications
            DROP CONSTRAINT IF EXISTS applications_customer_id_fkey;
            """
        )
        op.execute(
            """
            ALTER TABLE customer_profiles
            DROP CONSTRAINT IF EXISTS customer_profiles_customer_id_key;
            """
        )
        op.execute(
            """
            ALTER TABLE customer_profiles
            DROP CONSTRAINT IF EXISTS customer_profiles_pkey;
            """
        )
        op.execute(
            """
            ALTER TABLE customer_profiles
            ADD CONSTRAINT customer_profiles_pkey PRIMARY KEY (customer_id);
            """
        )
        op.execute(
            """
            ALTER TABLE applications
            ADD CONSTRAINT applications_customer_id_fkey
            FOREIGN KEY (customer_id)
            REFERENCES customer_profiles (customer_id);
            """
        )
        return
    with op.batch_alter_table("customer_profiles") as batch_op:
        batch_op.drop_constraint("customer_profiles_customer_id_key", type_="unique")
        batch_op.drop_constraint(None, type_="primary")
        batch_op.create_primary_key("customer_profiles_pkey", ["customer_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            ALTER TABLE applications
            DROP CONSTRAINT IF EXISTS applications_customer_id_fkey;
            """
        )
        op.execute(
            """
            ALTER TABLE customer_profiles
            DROP CONSTRAINT IF EXISTS customer_profiles_pkey;
            """
        )
        op.execute(
            """
            ALTER TABLE customer_profiles
            ADD CONSTRAINT customer_profiles_pkey PRIMARY KEY (id);
            """
        )
        op.execute(
            """
            ALTER TABLE customer_profiles
            ADD CONSTRAINT customer_profiles_customer_id_key UNIQUE (customer_id);
            """
        )
        op.execute(
            """
            ALTER TABLE applications
            ADD CONSTRAINT applications_customer_id_fkey
            FOREIGN KEY (customer_id)
            REFERENCES customer_profiles (customer_id);
            """
        )
        return
    with op.batch_alter_table("customer_profiles") as batch_op:
        batch_op.drop_constraint(None, type_="primary")
        batch_op.create_primary_key("customer_profiles_pkey", ["id"])
        batch_op.create_unique_constraint(
            "customer_profiles_customer_id_key", ["customer_id"]
        )
