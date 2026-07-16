#!/usr/bin/env bash
#
# One-shot local setup for the backend.
# Run from the backend/ directory:  ./scripts/setup.sh
#
set -euo pipefail

# Move to the backend/ root regardless of where the script is called from.
cd "$(dirname "$0")/.."

echo "==> Starting Postgres and Redis"
docker compose -f ../docker-compose.yml up -d postgres redis

if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example (edit it to add your OPENAI_API_KEY)"
  cp .env.example .env
fi

if [ ! -d .venv ]; then
  echo "==> Creating virtualenv"
  python3 -m venv .venv
fi

echo "==> Installing dependencies"
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt

echo "==> Waiting for Postgres to accept connections"
until docker exec durable-ai-postgres pg_isready -U durable_ai -d durable_ai >/dev/null 2>&1; do
  sleep 1
done

echo "==> Applying database migrations"
./.venv/bin/alembic upgrade head

echo "==> Done. Start the API with:"
echo "    .venv/bin/uvicorn app.main:app --reload"
