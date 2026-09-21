from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base

class ResolutionClassification(str, enum.Enum):
    # Supported conclusions for an incident investigation.

    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    BENIGN = "BENIGN"
    DUPLICATE = "DUPLICATE"
    INCONCLUSIVE = "INCONCLUSIVE"

class IncidentResolution(Base):
    """
    Investigation conclusion associated with an incident.

    Each incident may have at most one resolution record. The record is retained independently from the incident's operational status so the investigation conclusion remains explicit and auditable.
    """

    __tablename__ = "incident_resolutions"

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
        unique=True,
        index=True,
    )

    classification = Column(
        Enum(ResolutionClassification),
        nullable=False,
        index=True,
    )

    summary = Column(
        Text,
        nullable=False,
    )

    root_cause = Column(
        Text,
        nullable=True,
    )

    remediation = Column(
        Text,
        nullable=True,
    )

    resolved_by_user_id = Column(
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
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at = Column(
        DateTime(),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    resolved_by = relationship(
        "User",
        foreign_keys=[resolved_by_user_id],
    )