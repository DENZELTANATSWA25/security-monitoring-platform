from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)

from app.db.base import Base

class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    # Supports the 24-hour behavioural history query and ordering.
    __table_args__ = (
        Index(
            "ix_login_attempts_timestamp_id",
            "timestamp",
            "id",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String(255),
        nullable=False
    )

    successful = Column(
        Boolean,
        default=False
    )

    ip_address = Column(
        String(50),
        nullable=False
    )

    latitude = Column(
        Float,
        nullable=True
    )

    longitude = Column(
        Float,
        nullable=True
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )