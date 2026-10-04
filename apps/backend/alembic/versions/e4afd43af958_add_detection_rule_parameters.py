"""add detection rule parameters

Revision ID: e4afd43af958
Revises: ba6e931c1ee5
Create Date: 2026-10-03 23:54:56.912757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e4afd43af958'
down_revision: Union[str, Sequence[str], None] = 'ba6e931c1ee5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add configurable parameters to persisted detection rules."""

    op.add_column(
        "detection_rule_configs",
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.execute(
        """
        UPDATE detection_rule_configs
        SET parameters = CASE rule_name
            WHEN 'BRUTE_FORCE_ATTACK' THEN
                '{"failed_attempts_threshold": 5}'::jsonb

            WHEN 'EVENT_BURST' THEN
                '{"event_threshold": 5, "window_minutes": 5}'::jsonb

            WHEN 'IMPOSSIBLE_TRAVEL' THEN
                '{
                    "max_travel_speed_kmh": 1000.0,
                    "min_distance_km": 100.0
                }'::jsonb

            ELSE '{}'::jsonb
        END
        """
    )

    op.alter_column(
        "detection_rule_configs",
        "parameters",
        server_default=None,
    )


def downgrade() -> None:
    """Remove configurable detection rule parameters."""

    op.drop_column(
        "detection_rule_configs",
        "parameters",
    )
