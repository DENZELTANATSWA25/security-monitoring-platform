from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.incident_resolution import ResolutionClassification


class IncidentResolutionUpsert(BaseModel):
    """Data required to create or update an incident resolution."""

    classification: ResolutionClassification

    summary: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    root_cause: str | None = Field(
        default=None,
        max_length=10000,
    )

    remediation: str | None = Field(
        default=None,
        max_length=10000,
    )

    @field_validator("summary", mode="before")
    @classmethod
    def strip_summary(cls, value: str) -> str:
        """Strip surrounding whitespace from the required summary."""

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("root_cause", "remediation", mode="before")
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        """Strip optional text and convert blank values to None."""

        if not isinstance(value, str):
            return value

        value = value.strip()

        return value or None


class IncidentResolutionAuthor(BaseModel):
    """Minimal user information returned with a resolution."""

    id: int
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class IncidentResolutionResponse(BaseModel):
    """Resolution representation returned by the API."""

    id: int
    incident_id: int
    classification: ResolutionClassification
    summary: str
    root_cause: str | None
    remediation: str | None
    resolved_by_user_id: int | None
    resolved_by: IncidentResolutionAuthor | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)