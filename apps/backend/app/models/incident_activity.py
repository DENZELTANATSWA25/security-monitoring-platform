from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.db.base import Base
from sqlalchemy.orm import relationship

class IncidentActivityType(str, enum.Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    ASSIGNED= "ASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    NOTE_ADDED = "NOTE_ADDED"

class IncidentActivity(Base):
    __tablename__ = "incident_activities"

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

    actor_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    activity_type = Column(
        Enum(IncidentActivityType),
        nullable=False,
        index=True,
    )

    description = Column(
        Text,
        nullable=False
    )
    
    old_value = Column(
        String(255),
        nullable=True,
    )

    new_value = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime(),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    actor = relationship(
        "User",
        foreign_keys=[actor_user_id],
    )
    