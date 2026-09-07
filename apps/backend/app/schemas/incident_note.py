from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import UserRole

class IncidentNoteCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10_000,
    )

class IncidentNoteAuthor(BaseModel):
    id: int
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True

class IncidentNoteResponse(BaseModel):
    id: int
    incident_id: int
    author_user_id: int | None

    # The related use may be None if the original user has been subsequently been deleted
    author: IncidentNoteAuthor | None
    
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

        