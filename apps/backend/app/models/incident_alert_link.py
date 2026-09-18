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


class IncidentAlertLink(Base):
    """Associate an alert with an incident investigation."""

    __tablename__ = "incident_alert_links"

    __table_args__ = (
        UniqueConstraint(
            "incident_id",
            "alert_id",
            name="uq_incident_alert_link",
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

    alert_id = Column(
        Integer,
        ForeignKey(
            "alerts.id",
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

    alert = relationship(
        "Alert",
        foreign_keys=[alert_id],
    )

    linked_by = relationship(
        "User",
        foreign_keys=[linked_by_user_id],
    )