"""Convert users.roles to JSONB

Revision ID: 004_convert_roles_to_jsonb
Revises: 003_add_auth_columns
Create Date: 2025-09-26 17:58:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "004_convert_roles_to_jsonb"
down_revision = "003_add_auth_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN roles DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN roles TYPE JSONB
        USING COALESCE(to_jsonb(roles), '[]'::jsonb)
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN roles SET DEFAULT '[]'::jsonb")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN roles DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN roles TYPE TEXT[]
        USING COALESCE(
            ARRAY(SELECT jsonb_array_elements_text(COALESCE(roles, '[]'::jsonb))),
            ARRAY[]::TEXT[]
        )
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN roles SET DEFAULT ARRAY['borrower']::TEXT[]")
