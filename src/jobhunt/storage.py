"""DuckDB-backed storage for normalized Job records."""

from __future__ import annotations

from collections.abc import Iterable

import duckdb

from jobhunt.config import settings
from jobhunt.models import Job

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    fingerprint       TEXT PRIMARY KEY,
    source            TEXT NOT NULL,
    source_id         TEXT NOT NULL,
    title             TEXT NOT NULL,
    company           TEXT NOT NULL,
    location          TEXT NOT NULL,
    remote            BOOLEAN NOT NULL,
    posted_at         TIMESTAMP NOT NULL,
    fetched_at        TIMESTAMP NOT NULL,
    url               TEXT NOT NULL,
    description       TEXT NOT NULL,
    salary_min        DOUBLE,
    salary_max        DOUBLE,
    salary_currency   TEXT,
    employment_type   TEXT,
    language_required TEXT[],
    score             DOUBLE
);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at);
"""


def _connect() -> duckdb.DuckDBPyConnection:
    """Open a connection. Ensures the parent folder exists first."""
    settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(settings.duckdb_path))


def init_db() -> None:
    """Create tables and indexes if they don't exist. Idempotent."""
    with _connect() as con:
        con.execute(SCHEMA_SQL)


def upsert_jobs(jobs: Iterable[Job]) -> int:
    """Insert or replace jobs keyed on fingerprint. Returns count written."""
    rows = [
        (
            job.fingerprint,
            job.source,
            job.source_id,
            job.title,
            job.company,
            job.location,
            job.remote,
            job.posted_at,
            job.fetched_at,
            str(job.url),
            job.description,
            job.salary_min,
            job.salary_max,
            job.salary_currency,
            job.employment_type,
            job.language_required,
        )
        for job in jobs
    ]
    if not rows:
        return 0

    with _connect() as con:
        con.executemany(
            """
            INSERT OR REPLACE INTO jobs (
                fingerprint, source, source_id, title, company, location,
                remote, posted_at, fetched_at, url, description,
                salary_min, salary_max, salary_currency,
                employment_type, language_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    return len(rows)


def count_jobs() -> int:
    """Total number of rows in the jobs table."""
    with _connect() as con:
        result = con.execute("SELECT COUNT(*) FROM jobs").fetchone()
    return int(result[0]) if result else 0
