"""JSearch source adapter (RapidAPI)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from jobhunt.config import settings
from jobhunt.models import Job, compute_fingerprint

logger = logging.getLogger(__name__)

JSEARCH_BASE = "https://jsearch.p.rapidapi.com"
JSEARCH_HOST = "jsearch.p.rapidapi.com"


def fetch_jobs(
    query: str,
    location: str = "Amsterdam, Netherlands",
    num_pages: int = 1,
    date_posted: str = "week",
) -> list[Job]:
    """Fetch jobs from JSearch. Returns [] if key missing or API unavailable."""
    if not settings.jsearch_api_key:
        logger.info("JSearch key not configured, skipping")
        return []

    headers = {
        "X-RapidAPI-Key": settings.jsearch_api_key,
        "X-RapidAPI-Host": JSEARCH_HOST,
    }
    full_query = f"{query} in {location}"
    all_jobs: list[Job] = []

    with httpx.Client(timeout=10.0, headers=headers) as client:
        try:
            page_jobs = _fetch_page(client, full_query, num_pages, date_posted)
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 429:
                logger.warning("JSearch quota exhausted")
            elif status in (401, 403):
                logger.warning("JSearch auth failed (%d) — check key", status)
            else:
                logger.warning("JSearch HTTP %d: %s", status, e)
            return []
        except httpx.HTTPError as e:
            logger.warning("JSearch network error: %s", e)
            return []
        all_jobs.extend(page_jobs)
        logger.info("JSearch: %d jobs", len(page_jobs))

    return all_jobs


def _fetch_page(
    client: httpx.Client,
    query: str,
    num_pages: int,
    date_posted: str,
) -> list[Job]:
    url = f"{JSEARCH_BASE}/search"
    params: dict[str, str | int] = {
        "query": query,
        "page": 1,
        "num_pages": num_pages,
        "date_posted": date_posted,
    }
    response = client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    fetched_at = datetime.now(UTC)
    return [_to_job(item, fetched_at) for item in data.get("data", [])]


def _to_job(item: dict[str, Any], fetched_at: datetime) -> Job:
    title = item["job_title"]
    company = item["employer_name"]
    city = item.get("job_city") or ""
    country = item.get("job_country") or ""
    location = ", ".join(part for part in (city, country) if part) or "Unknown"
    description = item.get("job_description", "") or ""
    remote = bool(item.get("job_is_remote", False))

    posted_ts = item.get("job_posted_at_timestamp")
    posted_at = datetime.fromtimestamp(posted_ts, tz=UTC) if posted_ts else fetched_at

    return Job(
        source="jsearch",
        source_id=str(item["job_id"]),
        fingerprint=compute_fingerprint(company, title, location),
        title=title,
        company=company,
        location=location,
        remote=remote,
        posted_at=posted_at,
        fetched_at=fetched_at,
        url=item["job_apply_link"],
        description=description,
        salary_min=item.get("job_min_salary"),
        salary_max=item.get("job_max_salary"),
        salary_currency=item.get("job_salary_currency"),
        employment_type=item.get("job_employment_type"),
        language_required=[],
    )
