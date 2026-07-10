from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)

from sqlalchemy.sql import func

from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    alert_type = Column(
        String,
        nullable=False
    )

    severity = Column(
        String,
        nullable=False
    )

    message = Column(
        String,
        nullable=True
    )

    resolved = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    