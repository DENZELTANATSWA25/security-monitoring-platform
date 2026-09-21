"""add incident resolution

Revision ID: ad0bbea92b63
Revises: c952bee8090c
Create Date: 2026-09-20 23:33:10.781116
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ad0bbea92b63"
down_revision: Union[str, Sequence[str], None] = "c952bee8090c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add incident resolution storage and resolution activity types."""

    # PostgreSQL ENUM values must be added explicitly because Alembic
    # autogenerate does not detect additions to an existing ENUM type.
    op.execute(
        "ALTER TYPE incidentactivitytype "
        "ADD VALUE IF NOT EXISTS 'RESOLUTION_ADDED'"
    )
    op.execute(
        "ALTER TYPE incidentactivitytype "
        "ADD VALUE IF NOT EXISTS 'RESOLUTION_UPDATED'"
    )

    op.create_table(
        "incident_resolutions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "incident_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "classification",
            sa.Enum(
                "TRUE_POSITIVE",
                "FALSE_POSITIVE",
                "BENIGN",
                "DUPLICATE",
                "INCONCLUSIVE",
                name="resolutionclassification",
            ),
            nullable=False,
        ),
        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "root_cause",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "remediation",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "resolved_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_incident_resolutions_classification"),
        "incident_resolutions",
        ["classification"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_resolutions_created_at"),
        "incident_resolutions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_resolutions_id"),
        "incident_resolutions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_resolutions_incident_id"),
        "incident_resolutions",
        ["incident_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_incident_resolutions_resolved_by_user_id"),
        "incident_resolutions",
        ["resolved_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove incident resolution storage.

    PostgreSQL cannot directly remove individual values from an ENUM. We
    therefore rebuild incidentactivitytype without the resolution values.

    The downgrade deliberately fails if resolution activity records still
    exist, preventing investigation history from being silently destroyed.
    """

    op.drop_index(
        op.f("ix_incident_resolutions_resolved_by_user_id"),
        table_name="incident_resolutions",
    )
    op.drop_index(
        op.f("ix_incident_resolutions_incident_id"),
        table_name="incident_resolutions",
    )
    op.drop_index(
        op.f("ix_incident_resolutions_id"),
        table_name="incident_resolutions",
    )
    op.drop_index(
        op.f("ix_incident_resolutions_created_at"),
        table_name="incident_resolutions",
    )
    op.drop_index(
        op.f("ix_incident_resolutions_classification"),
        table_name="incident_resolutions",
    )

    op.drop_table("incident_resolutions")

    # Remove the PostgreSQL ENUM created for the resolution classification.
    sa.Enum(
        name="resolutionclassification",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )

    # PostgreSQL does not support DROP VALUE for ENUM types. Rebuild the
    # activity ENUM without the two values introduced by this migration.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM incident_activities
                WHERE activity_type::text IN (
                    'RESOLUTION_ADDED',
                    'RESOLUTION_UPDATED'
                )
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: resolution activity records exist';
            END IF;
        END
        $$;
        """
    )

    op.execute(
        "ALTER TYPE incidentactivitytype "
        "RENAME TO incidentactivitytype_old"
    )

    op.execute(
        """
        CREATE TYPE incidentactivitytype AS ENUM (
            'INCIDENT_CREATED',
            'ASSIGNED',
            'STATUS_CHANGED',
            'NOTE_ADDED',
            'EVENT_LINKED',
            'ALERT_LINKED',
            'EVIDENCE_ADDED'
        )
        """
    )

    op.execute(
        """
        ALTER TABLE incident_activities
        ALTER COLUMN activity_type
        TYPE incidentactivitytype
        USING activity_type::text::incidentactivitytype
        """
    )

    op.execute(
        "DROP TYPE incidentactivitytype_old"
    )