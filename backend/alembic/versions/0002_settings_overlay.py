"""operator settings overlay tables

Revision ID: 0002_settings_overlay
Revises: 0001_initial
Create Date: 2026-08-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_settings_overlay"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    if "encrypted_secrets" not in tables:
        op.create_table(
            "encrypted_secrets",
            sa.Column("name", sa.String(64), primary_key=True),
            sa.Column("ciphertext", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
    if "settings_audit" not in tables:
        op.create_table(
            "settings_audit",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("key_name", sa.String(64), nullable=False),
            sa.Column("action", sa.String(16), nullable=False),
            sa.Column("operator_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True)),
        )


def downgrade() -> None:
    op.drop_table("settings_audit")
    op.drop_table("encrypted_secrets")
