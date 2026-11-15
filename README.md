# VeriNews

AI-Powered Trusted News Feed & Real-Time Misinformation Verification Platform.

---

## 🏛️ Project Architecture
```
VeriNews/
├── backend/                  # FastAPI service (Python 3.11)
│   ├── alembic/              # PostgreSQL schema migrations
│   └── app/
│       ├── api/v1/           # API Endpoints (Health, News, Sources, Verify)
│       ├── core/             # Configuration, Database engine, Redis client
│       ├── models/           # SQLAlchemy 2.0 ORM models
│       └── schemas/          # Pydantic v2 validation schemas
├── mobile/                   # Flutter cross-platform mobile client
├── infra/                    # Docker Compose & deployment configuration
└── tests/                    # Integration and unit test suite
```

---

## 🚀 Quick Start (Docker Compose)

### 1. Start all services
From the `VeriNews/` root directory:
```bash
docker compose up -d --build
```
This boots:
* **PostgreSQL 16**: Port `5432`
* **Redis 7**: Port `6379`
* **FastAPI Backend**: Port `8000`

### 2. Run Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

### 3. Verify Endpoints
* **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
* **News Feed (India):** [http://localhost:8000/api/v1/news/feed?scope=national](http://localhost:8000/api/v1/news/feed?scope=national)
* **News Feed (City):** [http://localhost:8000/api/v1/news/feed?scope=city&city=mumbai](http://localhost:8000/api/v1/news/feed?scope=city&city=mumbai)
* **Supported Cities:** [http://localhost:8000/api/v1/news/cities](http://localhost:8000/api/v1/news/cities)

---

## 🧪 Running Automated Tests
```bash
docker compose exec backend pytest /app/../tests -v
```
*(or run locally using Python 3.11 virtual environment)*
