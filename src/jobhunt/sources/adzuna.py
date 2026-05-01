"""Adzuna source adapter."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from jobhunt.config import settings
from jobhunt.models import Job, compute_fingerprint

logger = logging.getLogger(__name__)

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"
DEFAULT_COUNTRY = "nl"
DEFAULT_RESULTS_PER_PAGE = 50
DEFAULT_MAX_DAYS_OLD = 7
COUNTRY_CURRENCY = {"nl": "EUR", "gb": "GBP", "de": "EUR", "fr": "EUR"}


def fetch_jobs(
    query: str,
    location: str = "amsterdam",
    country: str = DEFAULT_COUNTRY,
    max_pages: int = 5,
    max_days_old: int = DEFAULT_MAX_DAYS_OLD,
) -> list[Job]:
    """Fetch jobs from Adzuna across multiple pages.

    Returns validated Job records. Stops early on HTTP errors or empty pages.
    """
    all_jobs: list[Job] = []

    with httpx.Client(timeout=10.0) as client:
        for page in range(1, max_pages + 1):
            try:
                page_jobs = _fetch_page(client, query, location, country, page, max_days_old)
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "Adzuna HTTP %d on page %d: %s",
                    e.response.status_code,
                    page,
                    e,
                )
                break
            except httpx.HTTPError as e:
                logger.warning("Adzuna network error on page %d: %s", page, e)
                break

            if not page_jobs:
                break  # no more results

            all_jobs.extend(page_jobs)
            logger.info("Adzuna page %d: %d jobs", page, len(page_jobs))

    return all_jobs


def _fetch_page(
    client: httpx.Client,
    query: str,
    location: str,
    country: str,
    page: int,
    max_days_old: int,
) -> list[Job]:
    """Fetch a single page of Adzuna results and parse them into Jobs."""
    url = f"{ADZUNA_BASE}/{country}/search/{page}"
    params: dict[str, str | int] = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "what": query,
        "where": location,
        "results_per_page": DEFAULT_RESULTS_PER_PAGE,
        "max_days_old": max_days_old,
        "sort_by": "date",
    }

    response = client.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    fetched_at = datetime.now(UTC)
    return [_to_job(item, country, fetched_at) for item in data.get("results", [])]


def _to_job(item: dict[str, Any], country: str, fetched_at: datetime) -> Job:
    """Map a single Adzuna result into our Job model."""
    title = item["title"]
    company = item["company"]["display_name"]
    location = item["location"]["display_name"]
    description = item.get("description", "")

    # Adzuna doesn't expose remote as a flag — heuristic from text
    text = f"{title} {description}".lower()
    remote = "remote" in text or "thuiswerken" in text

    return Job(
        source="adzuna",
        source_id=str(item["id"]),
        fingerprint=compute_fingerprint(company, title, location),
        title=title,
        company=company,
        location=location,
        remote=remote,
        posted_at=item["created"],
        fetched_at=fetched_at,
        url=item["redirect_url"],
        description=description,
        salary_min=item.get("salary_min"),
        salary_max=item.get("salary_max"),
        salary_currency=COUNTRY_CURRENCY.get(country),
        employment_type=item.get("contract_time"),
        language_required=[],
    )
