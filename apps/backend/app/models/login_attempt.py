from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from app.db.base import Base

class LoginAttempt(Base):
    __tablename__ = "login_attempts"

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