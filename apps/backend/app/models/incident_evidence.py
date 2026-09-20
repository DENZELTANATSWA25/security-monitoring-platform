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
from sqlalchemy.orm import relationship

from app.db.base import Base


class EvidenceType(str, enum.Enum):
    """Supported investigation evidence categories."""

    IP_ADDRESS = "IP_ADDRESS"
    DOMAIN = "DOMAIN"
    URL = "URL"
    FILE_HASH = "FILE_HASH"
    USERNAME = "USERNAME"
    HOSTNAME = "HOSTNAME"
    PROCESS = "PROCESS"
    OTHER = "OTHER"


class IncidentEvidence(Base):
    """Analyst-provided evidence associated with an incident."""

    __tablename__ = "incident_evidence"

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

    evidence_type = Column(
        Enum(EvidenceType),
        nullable=False,
        index=True,
    )

    value = Column(
        Text,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    source = Column(
        String(255),
        nullable=True,
    )

    added_by_user_id = Column(
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
        index=True,
    )

    # Preserve evidence even if the user who added it is later deleted.
    added_by = relationship(
        "User",
        foreign_keys=[added_by_user_id],
    )