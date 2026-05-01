"""Pydantic models for jobhunt."""

import hashlib
import re
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


def compute_fingerprint(company: str, title: str, location: str) -> str:
    """Generate a stable, normalized fingerprint for cross-source deduplication.

    Produces the same hash for the same posting regardless of which board
    surfaced it, by lowercasing and normalizing whitespace before hashing.
    """
    parts = [_normalize(company), _normalize(title), _normalize(location)]
    payload = "|".join(parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _normalize(value: str) -> str:
    """Lowercase, strip, collapse whitespace runs."""
    return re.sub(r"\s+", " ", value.lower().strip())
