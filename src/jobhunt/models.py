"""Pydantic models for jobhunt."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class Job(BaseModel):
    """A normalized job posting from any source."""

    # Source provenance
    source: str
    source_id: str
    fingerprint: str

    # Posting details
    title: str
    company: str
    location: str
    remote: bool = False
    posted_at: datetime
    fetched_at: datetime
    url: HttpUrl
    description: str

    # Compensation (often missing)
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None

    # Classification
    employment_type: str | None = None
    language_required: list[str] = Field(default_factory=list)
