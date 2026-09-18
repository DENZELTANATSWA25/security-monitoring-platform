from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class IncidentEventLink(Base):
    """
    Associate an additional security event with an incident investigation.

    The Incident.event_id field remains the originating event for the
    incident. Records in this table represent additional events linked
    during the investigation.
    """

    __tablename__ = "incident_event_links"

    __table_args__ = (
        UniqueConstraint(
            "incident_id",
            "event_id",
            name="uq_incident_event_link",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    incident_id = Column(
        Integer,
        ForeignKey(
            "incidents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    event_id = Column(
        Integer,
        ForeignKey(
            "security_events.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    linked_by_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(),
        default=datetime.utcnow,
        nullable=False,
    )

    event = relationship(
        "SecurityEvent",
        foreign_keys=[event_id],
    )

    linked_by = relationship(
        "User",
        foreign_keys=[linked_by_user_id],
    )