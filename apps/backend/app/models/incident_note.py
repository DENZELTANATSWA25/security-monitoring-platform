from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.db.base import Base

class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    incident_id = Column(
        Integer,
        ForeignKey(
            "incidents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True
    )

    author_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime(),
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime(),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ORM relationship only
    # This does not create or modify a database column
    author = relationship(
        "User",
        foreign_keys=[author_user_id],
    )