from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


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

    telemetry_source_id = Column(
        Integer,
        ForeignKey(
            "telemetry_sources.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    telemetry_source = relationship(
        "TelemetrySource",
        back_populates="security_events",
    )
    
    event_metadata = Column(
        JSON,
        nullable=True
    )

    occurred_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )