from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum
)

from app.db.base import Base

import enum


class EventSeverity(str, enum.Enum):

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"



class SecurityEvent(Base):

    __tablename__ = "security_events"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    event_type = Column(
        String(100),
        nullable=False
    )


    severity = Column(
        Enum(EventSeverity),
        nullable=False,
        default=EventSeverity.INFO
    )


    source = Column(
        String(100),
        nullable=False
    )


    message = Column(
        Text,
        nullable=False
    )


    user_id = Column(
        Integer,
        nullable=True
    )


    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )