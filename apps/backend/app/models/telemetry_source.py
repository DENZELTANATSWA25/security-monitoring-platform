# Database model for registered external telemetry producers.

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.security_event import SecurityEvent

class TelemetrySource(Base):
    """
    Registered external system permitted to submit telemetry.

    API key secrets are never stored in plaintext. The key identifier is used for efficient database lookup while the secret has is used for authentication.
    """

    __tablename__ = "telemetry_sources"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    security_events: Mapped[list["SecurityEvent"]] = relationship(
        "SecurityEvent",
        back_populates="telemetry_source",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    key_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    api_key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )