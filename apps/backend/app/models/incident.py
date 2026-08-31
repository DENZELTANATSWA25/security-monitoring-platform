from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
)

from app.db.base import Base


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    severity = Column(
        String(50),
        nullable=False,
    )

    status = Column(
        Enum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
    )

    # Temporary legacy field.
    # Existing incidents may still contain a human-readable assignee here.
    assigned_to = Column(
        String(255),
        nullable=True,
    )

    # Real assignment to a User record.
    assigned_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    event_id = Column(
        Integer,
        ForeignKey("security_events.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(),
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime(),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )