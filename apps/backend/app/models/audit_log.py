from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(100)
    )
    resource: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )