# Durable AI Job Platform

A durable execution platform for long-running AI workflows. FastAPI + Celery
backend backed by Postgres (state) and Redis (broker/results).

## Prerequisites

- Docker (for Postgres + Redis)
- Python 3.12+

## Quick start

```bash
# 1. Start infrastructure
docker compose up -d postgres redis

# 2. Set up the backend
cd backend
cp .env.example .env          # then edit .env to add your OPENAI_API_KEY
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Create the database schema
.venv/bin/alembic upgrade head

# 4. Run the API
.venv/bin/uvicorn app.main:app --reload

# 5. In a separate terminal, run the Celery worker
.venv/bin/celery -A app.workers.celery_app worker --loglevel=info
```

Steps 1–3 are automated by [`backend/scripts/setup.sh`](backend/scripts/setup.sh):

```bash
cd backend && ./scripts/setup.sh
```

The API is served at http://localhost:8000 (docs at `/docs`, health at `/health`).

## Database migrations

Schema is managed with [Alembic](https://alembic.sqlalchemy.org/). Migrations
live in [`backend/alembic/versions/`](backend/alembic/versions/) and **must be
committed** — a fresh environment builds its schema by running them.

```bash
cd backend

# Apply all pending migrations (run this on any fresh checkout)
.venv/bin/alembic upgrade head

# After changing a SQLAlchemy model, generate a new migration
.venv/bin/alembic revision --autogenerate -m "describe change"
# then review the generated file before committing it
```

> **Note:** `alembic upgrade head` on a project with no migration files creates
> only the bookkeeping `alembic_version` table — no application tables. If you
> hit `relation "jobs" does not exist`, confirm a migration exists under
> `alembic/versions/` and has been applied.

## Configuration

Backend config is read from `backend/.env` (see
[`backend/.env.example`](backend/.env.example)). `.env` is gitignored.

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis URL (Celery broker + result backend) |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | Model name (default `gpt-4.1-mini`) |
| `MAX_JOB_ATTEMPTS` | Max retry attempts per job (default `3`) |
| `DEFAULT_MAX_COST_USD` | Default per-job cost cap (default `1.00`) |
