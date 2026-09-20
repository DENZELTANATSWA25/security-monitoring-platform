"""Add incident evidence.

Revision ID: c952bee8090c
Revises: ae86fa14dd38
Create Date: 2026-09-18 08:54:52.423689
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c952bee8090c"
down_revision: Union[str, Sequence[str], None] = "ae86fa14dd38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add incident evidence storage and evidence timeline activity."""

    # PostgreSQL ENUM additions are not reliably detected by Alembic
    # autogeneration, so the new timeline activity is added explicitly.
    op.execute(
        "ALTER TYPE incidentactivitytype "
        "ADD VALUE IF NOT EXISTS 'EVIDENCE_ADDED'"
    )

    op.create_table(
        "incident_evidence",
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
            "evidence_type",
            sa.Enum(
                "IP_ADDRESS",
                "DOMAIN",
                "URL",
                "FILE_HASH",
                "USERNAME",
                "HOSTNAME",
                "PROCESS",
                "OTHER",
                name="evidencetype",
            ),
            nullable=False,
        ),
        sa.Column(
            "value",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "added_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["added_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_incident_evidence_added_by_user_id"),
        "incident_evidence",
        ["added_by_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_incident_evidence_created_at"),
        "incident_evidence",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_incident_evidence_evidence_type"),
        "incident_evidence",
        ["evidence_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_incident_evidence_id"),
        "incident_evidence",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_incident_evidence_incident_id"),
        "incident_evidence",
        ["incident_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove incident evidence and restore the previous activity enum."""

    op.drop_index(
        op.f("ix_incident_evidence_incident_id"),
        table_name="incident_evidence",
    )

    op.drop_index(
        op.f("ix_incident_evidence_id"),
        table_name="incident_evidence",
    )

    op.drop_index(
        op.f("ix_incident_evidence_evidence_type"),
        table_name="incident_evidence",
    )

    op.drop_index(
        op.f("ix_incident_evidence_created_at"),
        table_name="incident_evidence",
    )

    op.drop_index(
        op.f("ix_incident_evidence_added_by_user_id"),
        table_name="incident_evidence",
    )

    op.drop_table("incident_evidence")

    # PostgreSQL cannot remove an individual ENUM value directly.
    # Rebuild the previous activity enum instead.
    #
    # The cast intentionally fails if EVIDENCE_ADDED activity rows still
    # exist, preventing incident-history data from being silently lost.
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
            'ALERT_LINKED'
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