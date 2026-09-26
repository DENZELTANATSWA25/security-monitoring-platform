from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.incident_evidence import EvidenceType
from app.models.user import UserRole

class IncidentEvidenceCreate(BaseModel):
    # Payload used when adding evidence to an incident.

    evidence_type: EvidenceType

    value: str = Field(
        min_length=1,
        max_length=10_000,
    )

    description: str | None = Field(
        default=None,
        max_length=10_000,
    )

    source: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator(
        "value",
        "description",
        "source",
        mode="before",
    )
    @classmethod
    def strip_strings(
        cls,
        value: str | None,
    ) -> str | None:
        # Normalise user-provided evidence text.

        if value is None:
            return None

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator(
        "description",
        "source",
    )
    @classmethod
    def normalize_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        #  Convert blank optional fields to null.

        if value == "":
            return None

        return value


class IncidentEvidenceAuthor(BaseModel):
    # Minimal user information for the evidence author.

    id: int
    full_name: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class IncidentEvidenceResponse(BaseModel):
    # Evidence representation returned to the API.

    id: int
    incident_id: int
    evidence_type: EvidenceType
    value: str
    description: str | None
    source: str | None
    added_by_user_id: int | None
    added_by: IncidentEvidenceAuthor | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
