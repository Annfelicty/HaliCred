"""Add auth columns to users table

Revision ID: 003_add_auth_columns
Revises: 002_add_email_to_users
Create Date: 2025-09-26 17:53:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_add_auth_columns"
down_revision = "002_add_email_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_otp_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_otp_verified_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "password_hash")
