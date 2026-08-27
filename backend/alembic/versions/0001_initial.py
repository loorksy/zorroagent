"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Tables are created via SQLAlchemy metadata on startup as well.
    # This revision documents the intended schema for production deploys.
    op.create_table(
        "operators",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("language", sa.String(8), server_default="en"),
        sa.Column("theme", sa.String(8), server_default="dark"),
        sa.Column("quick_model", sa.String(64), server_default="claude-sonnet-5"),
        sa.Column("deep_model", sa.String(64), server_default="claude-fable-5"),
        sa.Column("pin_hash", sa.String(255), nullable=True),
        sa.Column("exposure_cap_r", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "instruments",
        sa.Column("canonical_id", sa.String(64), primary_key=True),
        sa.Column("display_symbol", sa.String(64)),
        sa.Column("asset_class", sa.String(32)),
        sa.Column("tradable", sa.Boolean(), server_default=sa.true()),
        sa.Column("pip_location", sa.Integer(), nullable=True),
        sa.Column("display_precision", sa.Integer(), nullable=True),
        sa.Column("extra", sa.JSON()),
        sa.Column("refreshed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "kill_switch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engaged", sa.Boolean(), server_default=sa.false()),
        sa.Column("reason", sa.Text()),
        sa.Column("engaged_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("kill_switch")
    op.drop_table("instruments")
    op.drop_table("operators")
