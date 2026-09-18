"""Add incident event and alert links.

Revision ID: ae86fa14dd38
Revises: aa8302afe75b
Create Date: 2026-09-16 15:06:35.041540
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ae86fa14dd38"
down_revision: Union[str, Sequence[str], None] = "aa8302afe75b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add incident linkage tables and timeline activity types."""

    # Extend the PostgreSQL enum used by IncidentActivity.activity_type.
    #
    # SQLAlchemy/Alembic autogeneration does not reliably detect additions
    # to an existing PostgreSQL ENUM, so these values are added explicitly.
    op.execute(
        "ALTER TYPE incidentactivitytype "
        "ADD VALUE IF NOT EXISTS 'EVENT_LINKED'"
    )
    op.execute(
        "ALTER TYPE incidentactivitytype "
        "ADD VALUE IF NOT EXISTS 'ALERT_LINKED'"
    )

    op.create_table(
        "incident_alert_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("linked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["linked_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "incident_id",
            "alert_id",
            name="uq_incident_alert_link",
        ),
    )

    op.create_index(
        op.f("ix_incident_alert_links_alert_id"),
        "incident_alert_links",
        ["alert_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_alert_links_id"),
        "incident_alert_links",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_alert_links_incident_id"),
        "incident_alert_links",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_alert_links_linked_by_user_id"),
        "incident_alert_links",
        ["linked_by_user_id"],
        unique=False,
    )

    op.create_table(
        "incident_event_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("linked_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["security_events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["linked_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "incident_id",
            "event_id",
            name="uq_incident_event_link",
        ),
    )

    op.create_index(
        op.f("ix_incident_event_links_event_id"),
        "incident_event_links",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_event_links_id"),
        "incident_event_links",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_event_links_incident_id"),
        "incident_event_links",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_event_links_linked_by_user_id"),
        "incident_event_links",
        ["linked_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove incident linkage tables and restore the previous activity enum."""

    op.drop_index(
        op.f("ix_incident_event_links_linked_by_user_id"),
        table_name="incident_event_links",
    )
    op.drop_index(
        op.f("ix_incident_event_links_incident_id"),
        table_name="incident_event_links",
    )
    op.drop_index(
        op.f("ix_incident_event_links_id"),
        table_name="incident_event_links",
    )
    op.drop_index(
        op.f("ix_incident_event_links_event_id"),
        table_name="incident_event_links",
    )
    op.drop_table("incident_event_links")

    op.drop_index(
        op.f("ix_incident_alert_links_linked_by_user_id"),
        table_name="incident_alert_links",
    )
    op.drop_index(
        op.f("ix_incident_alert_links_incident_id"),
        table_name="incident_alert_links",
    )
    op.drop_index(
        op.f("ix_incident_alert_links_id"),
        table_name="incident_alert_links",
    )
    op.drop_index(
        op.f("ix_incident_alert_links_alert_id"),
        table_name="incident_alert_links",
    )
    op.drop_table("incident_alert_links")

    # PostgreSQL cannot directly remove values from an ENUM.
    #
    # Rebuild the previous enum. PostgreSQL will reject the cast if rows
    # still contain EVENT_LINKED or ALERT_LINKED, preventing silent loss
    # of incident-history data.
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
            'NOTE_ADDED'
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