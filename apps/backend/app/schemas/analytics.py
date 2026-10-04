"""Schemas for security analytics."""


from pydantic import BaseModel


class EventTrendItem(BaseModel):
    """Number of security events recorded on one calendar date."""

    date: str
    count: int