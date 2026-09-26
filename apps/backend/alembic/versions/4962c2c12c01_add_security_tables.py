"""add security tables

Revision ID: 4962c2c12c01
Revises: 28df6a038087
Create Date: 2026-07-08 20:35:35.064589

This migration establishes the original security-domain tables that existed
before later migrations modified them.

The original generated migration was empty, which meant a fresh database
could not be reconstructed from Alembic history alone.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic revision identifiers.
revision: str = "4962c2c12c01"
down_revision: Union[str, Sequence[str], None] = "28df6a038087"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the original baseline security tables."""

    # Login attempts existed before migration 978af9ce493f.
    #
    # ip_address is intentionally nullable here because the later migration
    # changes it to NOT NULL. This preserves the historical schema sequence.
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "successful",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "ip_address",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Alerts are required by later incident-alert linkage migrations.
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_alerts_id"),
        "alerts",
        ["id"],
        unique=False,
    )

    # This is the historical SecurityEvent structure.
    #
    # Migration 004070fe37ae later removes timestamp and adds
    # event_metadata + created_at.
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO",
                "WARNING",
                "ERROR",
                "CRITICAL",
                name="eventseverity",
            ),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_security_events_id"),
        "security_events",
        ["id"],
        unique=False,
    )

    # Incidents require security_events to exist first because event_id is
    # a foreign key referencing security_events.id.
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "IN_PROGRESS",
                "RESOLVED",
                "CLOSED",
                name="incidentstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "assigned_to",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "event_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["security_events.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_incidents_id"),
        "incidents",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the baseline security tables in dependency-safe order."""

    # Incidents reference security_events, so incidents must be removed first.
    op.drop_index(
        op.f("ix_incidents_id"),
        table_name="incidents",
    )
    op.drop_table("incidents")

    op.drop_index(
        op.f("ix_security_events_id"),
        table_name="security_events",
    )
    op.drop_table("security_events")

    # PostgreSQL ENUM types are independent schema objects and must be
    # removed explicitly after the tables using them are gone.
    sa.Enum(name="incidentstatus").drop(
        op.get_bind(),
        checkfirst=True,
    )
    sa.Enum(name="eventseverity").drop(
        op.get_bind(),
        checkfirst=True,
    )

    op.drop_index(
        op.f("ix_alerts_id"),
        table_name="alerts",
    )
    op.drop_table("alerts")

    op.drop_table("login_attempts")
