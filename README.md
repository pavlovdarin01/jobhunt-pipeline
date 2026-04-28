# jobhunt-pipeline

A multi-source job aggregator with deduplication, scoring, and a Streamlit dashboard.

> **Status:** v0.1 — scaffold. In active development.

## Problem

Manually checking job boards every morning is slow and repetitive. Aggregator UIs surface stale results, fail to deduplicate across sources, and don't rank by personal fit. This project automates the discovery loop so my attention is reserved for the high-value step — deciding which roles to pursue.

## How it works

The pipeline pulls postings from two sources (Adzuna and JSearch via RapidAPI), normalizes them into a common typed schema, deduplicates across sources via fingerprint hashing, scores each posting using a hybrid of rule-based heuristics and TF-IDF cosine similarity to a target resume, and persists results in DuckDB. A Streamlit dashboard surfaces today's top results, supports status filtering (interested / applied / interviewing / rejected), and explains the score per row.

```
Adzuna API ─┐
            ├─→ Normalizer ─→ Dedup ─→ Scorer ─→ DuckDB ─→ Streamlit
JSearch API ┘
```

## Tech stack

- **Python 3.11+** with strict type checking (mypy)
- **httpx** for HTTP calls
- **Pydantic v2** for typed schemas at the source boundary
- **DuckDB** for analytical storage
- **scikit-learn** for TF-IDF resume similarity
- **Streamlit** for the dashboard
- **uv** for dependency management
- **ruff + mypy + pytest + pre-commit** for code quality
- **GitHub Actions** for CI and scheduled runs

See [`docs/PROJECT_SPEC_v1.md`](docs/PROJECT_SPEC_v1.md) for the full design rationale, and [`docs/decisions/`](docs/decisions/) for ADRs covering individual technology choices.

## Setup

You'll need:
- Python 3.11+ (or let `uv` install it for you)
- Free API keys: [Adzuna](https://developer.adzuna.com/) and [JSearch on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)

```bash
git clone https://github.com/<your-username>/jobhunt-pipeline
cd jobhunt-pipeline
uv sync --all-extras
cp .env.example .env
# then edit .env with your API keys
```

## Usage

```bash
# Run the daily pipeline
uv run jobhunt run

# View results in the dashboard
uv run streamlit run dashboard/app.py
```

## Roadmap

**v1 (in progress):** Two sources (Adzuna, JSearch), DuckDB storage, hybrid scoring (rules + TF-IDF), Streamlit dashboard, application-status tracking, GitHub Actions cron.

**v2:** Sentence-transformer embeddings replacing TF-IDF, additional sources (Arbeitnow, Reed), application-conversion analytics, LLM-generated cover letters.

**Out of scope:** Multi-user support, real-time updates, mobile app.

## License

MIT — see [LICENSE](LICENSE).
