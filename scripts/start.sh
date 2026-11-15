#!/usr/bin/env bash
set -e

# Change to repository root
cd "$(dirname "$0")/.."

echo "================================================================="
echo " 📰 Starting VeriNews AI News & Verification Platform"
echo "================================================================="

# 1. Start Docker Containers
echo "▶ [1/4] Starting Docker containers (PostgreSQL, Redis, FastAPI)..."
docker compose up -d

# 2. Wait for Database to become healthy
echo "▶ [2/4] Waiting for database & Redis readiness..."
until docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done
echo "✔ PostgreSQL 16 is ready."

until docker compose exec -T redis redis-cli ping | grep -q PONG; do
  sleep 1
done
echo "✔ Redis 7 is ready."

# 3. Apply database migrations
echo "▶ [3/4] Running Alembic database migrations..."
docker compose exec -T backend alembic upgrade head

# 4. Ingest news from verified feeds
echo "▶ [4/4] Ingesting initial news articles from verified sources..."
docker compose exec -T backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.seed import seed_default_sources
from app.services.ingestion import IngestionService

async def init():
    async with AsyncSessionLocal() as db:
        await seed_default_sources(db)
        await IngestionService.run_ingestion(db, limit_per_source=3)

asyncio.run(init())
"

echo "================================================================="
echo " 🎉 VeriNews is successfully running!"
echo "================================================================="
echo " 🌐 FastAPI Backend & Docs:    http://localhost:8000/docs"
echo " 🛡️  Fact-Checker Admin Portal: http://localhost:8000/admin"
echo " 🔍 Health Endpoint:           http://localhost:8000/api/v1/health"
echo " 📱 Mobile App:                cd mobile && flutter run"
echo "================================================================="
