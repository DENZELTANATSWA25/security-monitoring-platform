"""add login attempt history index

Revision ID: ae09bee04d97
Revises: e4afd43af958
Create Date: 2026-11-23 11:54:29.011772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae09bee04d97'
down_revision: Union[str, Sequence[str], None] = 'e4afd43af958'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the chronological login-history index."""
    op.create_index(
        "ix_login_attempts_timestamp_id",
        "login_attempts",
        ["timestamp", "id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the chronological login-history index."""
    op.drop_index(
        "ix_login_attempts_timestamp_id",
        table_name="login_attempts",
    )